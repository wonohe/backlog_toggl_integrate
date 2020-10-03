"""
Repository modules.

define persistence logic.
"""
from chalice import Chalice
from chalicelib.models import BacklogIssue
from chalicelib.models import TogglReportDetail
from chalicelib.models import TogglReportSummary
from chalicelib.error import TogglAPIError
from chalicelib.error import TogglDBError
from chalicelib.error import BacklogAPIError
from typing import List, Tuple, Dict, Optional
import os
import datetime
import logging
import requests
import json
import re
import psycopg2
import psycopg2.extras

app = Chalice(app_name='nulabExamApp')
# productionでもcloudwatchにlog出力する
app.debug = True

# 定数（config.json）
TOGGL_API_TOKEN = os.environ['TOGGL_API_TOKEN']
TOGGL_BASE_URL = os.environ['TOGGL_BASE_URL']
TOGGL_PAST_DAYS = int(os.environ['TOGGL_PAST_DAYS'])
BACKLOG_PRJ_KEY = os.environ['BACKLOG_PRJ_KEY']
BACKLOG_BASE_URL = os.environ['BACKLOG_BASE_URL']
BACKLOG_APIKEY = os.environ['BACKLOG_APIKEY']
BACKLOG_COMMENT = os.environ['BACKLOG_COMMENT']
BACKLOG_COMMENT_COUNT = os.environ['BACKLOG_COMMENT_COUNT']


class TogglReportSummaryRepository():
    """Toggl Summary Data Repository
    TogglのDetailed Report APIを利用
    """

    def __init__(self):
        """Initialize.
        Togglのworkspace idとemailを取得（API利用時に必要なため）
        """

        self.workspace_id = self._get_workspace_id()
        self.email = self._get_email()
        pass

    def get_data(self, past_days: int = TOGGL_PAST_DAYS) \
            -> List[TogglReportDetail]:
        """get toggl report data

        Args:
            past_days:int
                何日前のデータまで取得するか。初期値6日

        Return:
            data:List[TogglReportDetail]
                取得結果。TogglReportDetail型配列
        """

        # Togglデータ取得
        _since: str = (datetime.datetime.now() - datetime.timedelta(days=TOGGL_PAST_DAYS)).strftime('%Y-%m-%d')
        _until: str = datetime.datetime.now().strftime('%Y-%m-%d')
        _params = {
            'user_agent': self.email,
            'description': f'{BACKLOG_PRJ_KEY}-',
            'since': _since,
            'until': _until,
            'workspace_id': self.workspace_id
        }
        app.log.info(f'[toggl get data:_params]{_params}')
        # 50件ずつ取得
        _page = 0
        _total_data = {}
        while True:
            _page += 1
            _params['page'] = _page
            _req = requests.get(f'{TOGGL_BASE_URL}/reports/api/v2/details',
                                auth=(TOGGL_API_TOKEN, 'api_token'),
                                params=_params)
            _res = _req.json()
            app.log.info(f'[toggl get data:_res]{_res}')
            if 'data' not in _total_data.keys():
                _total_data = _res
            else:
                _total_data['data'] += _res['data']
            if len(_res['data']) == 0:
                # dataがなければ取得完了
                break

        # BacklogissueKeyは先頭の１つ目のみ取得
        _data = [TogglReportDetail(
            id=dict['id'],
            pid=dict['pid'],
            tid=dict['tid'],
            uid=dict['uid'],
            user=dict['user'],
            description=dict['description'],
            start=dict['start'],
            end=dict['end'],
            updated=dict['updated'],
            dur=dict['dur'],
            backlog_issue_key=re.findall(rf'{BACKLOG_PRJ_KEY}-\d+', dict['description'], flags=re.I)[0].upper()
            ) for dict in _total_data['data']]

        return _data

    def _get_workspace_id(self) -> int:
        """get toggl workspace id

        Args:
            None

        Return:
            workspace_id:int
                togglのworkspace id

        """
        _req = requests.get(f'{TOGGL_BASE_URL}/api/v8/workspaces',
                            auth=(TOGGL_API_TOKEN, 'api_token'))
        _data = _req.json()
        app.log.info(f'[toggl workspaces data]{_data}')
        if _data[0]['id']:
            return _data[0]['id']
        else:
            raise TogglAPIError('workspace id not found')

    def _get_email(self) -> str:
        """get toggl email

        Args:
            None

        Return:
            email:str
                toggl apiに紐づくemail
        """
        _req = requests.get(f'{TOGGL_BASE_URL}/api/v8/me',
                            auth=(TOGGL_API_TOKEN, 'api_token'))
        _data = _req.json()
        app.log.info(f'[toggl email data]{_data}')
        if _data['data']['email']:
            return _data['data']['email']
        else:
            raise TogglAPIError('email not found')


class DbTogglReportRepository():
    """Toggl report repository interface with db."""

    def __init__(self):
        """Initialize db connection."""
        try:
            _conn = psycopg2.connect(
                host=os.environ['DB_HOST'],
                database=os.environ['DB_NAME'],
                port=os.environ['DB_PORT'],
                user=os.environ['DB_USER'],
                password=os.environ['DB_PASSWORD']
            )
            _conn.autocommit = False
            _conn.set_client_encoding('utf-8')
            _conn.cursor_factory = psycopg2.extras.DictCursor
            self.conn = _conn
        except Exception as e:
            raise TogglDBError('db connection error:{}'.format(e))

    def __del__(self):
        """Close db connection."""
        try:
            self.conn.close()
        except Exception as e:
            raise TogglDBError('db connection close error:{}'.format(e))

    def find_summary_data(self) -> List[TogglReportSummary]:
        """find summary data.
        Args:
            None

        Return:
            data:[TogglReportSummary]
                DBから取得したBacklogIssue毎のTogglReportデータ。TogglReportSummary型配列
        """
        with self.conn.cursor() as _cur:
            # SQLでgroup byしたものを抽出
            _statement = ('SELECT backlog_issue_key,sum(dur) as sum_dur FROM '
                          'toggl_report tr WHERE backlog_issue_key IS NOT NULL '
                          'GROUP BY backlog_issue_key')
            app.log.info(f'[SQL]{_statement}')
            _cur.execute(_statement)
            recset = _cur.fetchall()

        data = [TogglReportSummary(
            backlog_issue_key=dict['backlog_issue_key'],
            sum_dur=dict['sum_dur'],
            sum_dur_hours=round(dict['sum_dur']/(60*60*1000), 2)
            ) for dict in recset]
        return data

    def delete(self, past_days: int = TOGGL_PAST_DAYS) -> bool:
        """delete past data
        Args:
            past_days:int
                DB上で何日前までのtoggl report dataを削除するか。初期値6日

        Return:
            bool
                成功していればTrue
        """
        try:
            with self.conn.cursor() as _cur:
                _statement = (f'DELETE FROM toggl_report WHERE start_time > '
                              f'date_trunc(\'day\',now() + \'-{past_days} days\')')
                app.log.info(f'[SQL]{_statement}')
                _cur.execute(_statement)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise TogglDBError('toggl data delete error:{}'.format(e))

    def insert(self, toggl_data: List[TogglReportDetail]) -> bool:
        """insert toggl report data
        Args:
            toggl_data:List[TogglReportDetail]
                DBに登録するtoggl data. toggl detailed report api で取得したもの

        Return:
            bool
                成功していればTrue
        """
        try:
            with self.conn.cursor() as _cur:
                for dict in toggl_data:
                    # 6日以上前のデータが6日以内に変更されていた場合は過去レコードを削除
                    _statement = (f'SELECT count(*) cnt FROM toggl_report '
                                  f'WHERE toggl_id = {dict.id}')
                    _cur.execute(_statement)
                    if(int(_cur.fetchone()["cnt"]) > 0):
                        _statement = (f'DELETE FROM toggl_report '
                                      f'WHERE toggl_id = {dict.id}')
                        _cur.execute(_statement)

                    # 登録
                    _statement = ('INSERT INTO toggl_report (toggl_id,'
                                  'pid,tid,uid,user_name,description,'
                                  'start_time,end_time,updated,dur,'
                                  'backlog_issue_key) VALUES ('
                                  '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
                    _variables = [
                        dict.id,
                        dict.pid,
                        dict.tid,
                        dict.uid,
                        dict.user,
                        dict.description,
                        dict.start,
                        dict.end,
                        dict.updated,
                        dict.dur,
                        dict.backlog_issue_key
                    ]
                    app.log.info(f'{_statement}\n{_variables}')
                    _cur.execute(_statement, _variables)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise TogglDBError('toggl data insert error:{}'.format(e))


class BacklogIssueRepository():
    """Backlog issue repository interface"""

    def __init__(self):
        """Initialize
        API用の共通ヘッダー設定
            Args:
                None
        """
        self.api_headers = {
            'Content-Type': 'application/json'
        }
        pass

    def get_issue_data(self, toggl_summary: TogglReportSummary) -> BacklogIssue:
        """get backlog issue data
        Args:
            toggl_data:TogglReportSummary
                Backlogのissue情報取得のためのTogglデータ。togglで登録されているBacklog issueを取得する

        Return:
            backlog_issue:BacklogIssue
                Backlog issue modelを返す
        """
        _url = (f'{BACKLOG_BASE_URL}/api/v2/issues/{toggl_summary.backlog_issue_key}'
                f'?apiKey={BACKLOG_APIKEY}')
        _req = requests.get(_url, headers=self.api_headers)
        app.log.info(f'[backlog issue url]{_url}')

        if _req.status_code == 200:
            _res = json.loads(_req.text)
            app.log.info(f'[backlog issue result]{_res}')
            _comments = self._get_comments_data(_res["issueKey"], _res["actualHours"])
            _manual_actual_hours = self._get_manual_actual_hours(_comments)
            _backlog_issue = BacklogIssue(
                issue_key=_res["issueKey"],
                actual_hours=_res["actualHours"],
                manual_actual_hours=_manual_actual_hours,
                comments=_comments
                )
        else:
            app.log.info(f'[backlog issue not found')
            _backlog_issue = BacklogIssue()

        return _backlog_issue

    def _get_comments_data(self, issue_key: str, actual_hours: float) -> List:
        """get backlog comment data
        issueに紐づくすべてのコメントデータを取得

        Args:
            issue_key:str
                backlog issueのkey
            actual_hours:float
                backlog issueに登録されている実績時間

        Return:
            data:[]
                Backlog issueに紐づくcomment dataの配列
                実績時間が登録ない場合、取得の必要がないのでNone
        """
        if not actual_hours:
            # 実績時間登録なしの場合
            # commentデータを取る必要はないのでNoneのまま
            return None
        else:
            # 実績時間登録ありの場合
            # commentデータを取得
            _total_data = []
            _min_id = 1
            while True:
                _url = (f'{BACKLOG_BASE_URL}/api/v2/issues/{issue_key}/comments?'
                        f'apiKey={BACKLOG_APIKEY}&count={BACKLOG_COMMENT_COUNT}'
                        f'&order=asc&minId={_min_id}')
                _req = requests.get(_url, headers=self.api_headers)
                app.log.info(f'[backlog comment url]{_url}')
                if _req.status_code == 200:
                    _res = json.loads(_req.text)
                    app.log.info(f'[backlog comment data]{_res}')
                    _total_data += _res
                    if len(_res) == int(BACKLOG_COMMENT_COUNT):
                        _min_id = _res[len(_res)-1]['id']
                    else:
                        break
                else:
                    raise BacklogAPIError('failed to get comment data')

            return _total_data

    def _get_manual_actual_hours(self, comments: List) -> float:
        """get manual actual hours
        issueに登録されている実績時間の内、手動で実績登録している時間を計算

        Args:
            comments:[]
                backlog issueに紐づくcommentデータの配列

        Return:
            manual_actual_hours:float
                Backlog issueに登録されている実績時間から手動で登録した時間のみを計算したもの
        """
        _manual_actual_hours: float = 0.0
        for dict in comments:
            _content = dict.get('content') or ''
            app.log.info(f'[comment content]{_content}')
            if not _content or (_content and not _content.startswith(BACKLOG_COMMENT)):
                # コメントがない or toggl定型文でない場合のみ処理
                for change_log in dict['changeLog']:
                    if change_log['field'] == 'actualHours':
                        # 実績時間更新がない履歴は無視
                        _original_value = float(change_log['originalValue'] or 0)
                        _new_value = float(change_log['newValue'] or 0)
                        _manual_actual_hours = _manual_actual_hours + _new_value - _original_value
                        app.log.info(f'[_manual_actual_hours]{_manual_actual_hours}')
                        app.log.info(f'[_new_value]{_new_value}')
                        app.log.info(f'[_original_value]{_original_value}')
        _manual_actual_hours = round(_manual_actual_hours, 2)
        return _manual_actual_hours

    def update(self, toggl_summary: TogglReportSummary, backlog_issue: str, comment: List) -> bool:
        """update backlog issue
        Backlog issueを更新。実績時間とToggl連携のコメントを登録する

        Args:
            toggl_summary:TogglReportSummary
                Toggl Report Summary.Togglで登録された合計時間を使う（sum_dur_hours）
            backlog_issue:str
                Backlog issue model.手動実績時間を使う（manual_actual_hours）
            comment:str
                登録用コメント

        Return:
            bool
                成功したらTrue
        """

        app.log.info('backlog update start')
        _url = (f'{BACKLOG_BASE_URL}/api/v2/issues/{backlog_issue.issue_key}'
                f'?apiKey={BACKLOG_APIKEY}')
        data = {
            'actualHours': backlog_issue.manual_actual_hours + toggl_summary.sum_dur_hours,
            'comment': comment
        }
        app.log.info(f'[backlog update url]{_url}')
        app.log.info(f'[backlog update data]{data}')
        _req = requests.patch(_url, json=data, headers=self.api_headers)
        if _req.status_code == 200:
            app.log.info(f'backlog update success')
            return True
        else:
            raise BacklogAPIError('update failed')
