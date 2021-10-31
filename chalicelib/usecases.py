"""
Usecase modules.

define buisiness logic.
"""
from chalice import Chalice
from chalicelib.repositories import TogglReportSummaryRepository
from chalicelib.repositories import DbTogglReportRepository
from chalicelib.repositories import BacklogIssueRepository
import os
import math

app = Chalice(app_name='ExamApp')
# productionでもcloudwatchにlog出力する
app.debug = True


class ImportFromTogglUsecase():
    """toggl data import usecase
    """
    def __init__(
            self,
            toggl_report_summary_repository: TogglReportSummaryRepository,
            db_toggl_report_repository: DbTogglReportRepository,
            backlog_issue_repository: BacklogIssueRepository):
        """Initialize.
        インスタンス変数にrepository設定

        Args:
            toggl_report_summary_repository : TogglReportSummaryRepository
                APIで取得したToggl report data格納
            db_toggl_report_repository : DbTogglReportRepository
                DBから取得したらToggl data（集計済み）格納
            backlog_issue_repository : BacklogIssueRepository
                backlog issueのデータ格納

        Return:
            None
        """
        self.toggl_report_summary_repository = toggl_report_summary_repository
        self.db_toggl_report_repository = db_toggl_report_repository
        self.backlog_issue_repository = backlog_issue_repository
        pass

    def handle(self):
        """usecase handle.

        Args:
            None

        Return:
            boolean

        """
        # get toggl data from 6 days ago to today
        app.log.info('get toggl data')
        toggl_data: list = self.toggl_report_summary_repository.get_data()
        # regist toggl data to database.
        app.log.info('delete/insert toggl data to database')
        self.db_toggl_report_repository.delete()
        self.db_toggl_report_repository.insert(toggl_data)
        # get toggl summary data from database.
        app.log.info('get toggl data from database')
        toggl_summary_data: list = self.db_toggl_report_repository.find_summary_data()
        app.log.info('calc toggl data.')
        for toggl_summary in toggl_summary_data:
            backlog_issue = self.backlog_issue_repository.get_issue_data(toggl_summary)
            if not backlog_issue.issue_key:
                continue
            app.log.info(f'[issue_key]{backlog_issue.issue_key}')
            app.log.info(f'[sum_dur_hours]{toggl_summary.sum_dur_hours}')
            app.log.info(f'[actual_hours]{backlog_issue.actual_hours}')
            app.log.info(f'[manual_actual_hours]{backlog_issue.manual_actual_hours}')
            if (backlog_issue.actual_hours
                    and not math.isclose(toggl_summary.sum_dur_hours, (backlog_issue.actual_hours - backlog_issue.manual_actual_hours))):
                app.log.info(f'update backlog data')
                comment = f'{os.environ["BACKLOG_COMMENT"]}　手動登録時間：{backlog_issue.manual_actual_hours}h　toggl登録時間：{toggl_summary.sum_dur_hours}h'
                self.backlog_issue_repository.update(toggl_summary, backlog_issue,comment)

        return True

