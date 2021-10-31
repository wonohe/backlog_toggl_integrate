# Name
Sample App

# Features
本アプリは個人の作業時間を登録する[toggl](https://toggl.com/)というサービスとBacklogとの連携アプリです。
togglで登録された時間をBacklogの稼働時間として取り込みます。
例えば、toggl登録の際、「WONOHE-2 開発」といった形で作業内容を
登録しておくと、課題IDが「WONOHE-2」の実績時間として登録がされるアプリです。
togglのTeamに含まれている人のすべての登録を取得します。

# Requirement
- python 3.7~
- Postgres 12.3

# Setup
1. chaliceを使用していますので、まずchaliceをインストールください。
```
pip install chalice
```

2. requirements.txtの関連モジュールをインストール
```
pip install -r requirements.txt
```

3. `config.json.sample`を`config.json`にリネーム

4. `config.json`を編集
下記パラメータを参考ください。

| key | 内容 | 例 |
|:--|:--|:--|
| TOGGL_API_TOKEN | toggl API用トークン | abcdefghijklmnopqrstuvwxyz |
| TOGGL_BASE_URL|toggl APIのURL| https://www.toggl.com |
| TOGGL_PAST_DAYS | N日前までのtogglデータを取り込み | 6 |
| BACKLOG_PRJ_KEY | Backlogのプロジェクトキー | ONOUE |
| BACKLOG_BASE_URL | Backlog APIのURL | https://hoge.backlog.jp |
| BACKLOG_APIKEY | toggl API用Key | zyxwvutsrqponmlkjihgfedcba |
| BACKLOG_COMMENT | Backlogを更新するときのコメント接頭辞 | [togglより連携] |
| BACKLOG_COMMENT_COUNT | Backlog APIで一回に取得するコメント数（上限100） | 100 |
| DB_HOST | togglデータ格納用DBのHOST | hoge-dev.hogefugafoo.ap-northeast-1.rds.amazonaws.co |
| DB_NAME | togglデータ格納用DBのDB名 | hoge |
| DB_PORT | togglデータ格納用DBのPORT | 5432 |
| DB_USER | togglデータ格納用DBのUSER名 | hoge_exam_dev
| DB_PASSWORD | togglデータ格納用DBのPASSWORD | aaaaabbbbcccc |

5.chalice実行

```bash:bash
# local実行
chalice local

# dev環境としてdeploy
chalice deploy --stage=dev

# production環境としてdeploy
# config.jsonにproductionの設定が必要
chalice deploy --stage=production
```

# Note
## DBについて
togglデータを格納するためにRDB（Postgres）を使用しています
ddl.sqlの内容にてテーブル作成ください

## 取り込みロジックについて
下記ロジックにて取り込んでいます

1. 直近１週間のtogglデータを取得（※）
2. １週間以上前のtogglデータと合わせて、toggl稼働時間を算出
3. Backlog issueに登録されている実績時間を取得
4. 3のうち、手動で登録されたもののみ抽出
5. 4と2の時間を合わせて、Backlog issueを更新

※togglの過去データは1年前まで取得可能ですが、データが大量になると処理が重くなってしまうことを考慮し、処理上では1週間前までしか取得しません。
1週間以上前のデータは、作業時間として確定しているものとみなしています。
（1週間以上前の作業を覚えている人も少ないと思いますので）

## Lint
pycodestyleで行っています。
`E501 line too long`が残ったままですが、視認性が落ちるため対応していません。

```
pycodestyle <file name>
```

## 既知の問題について
Backlog上で課題作成時に「実績時間」を登録した場合、その時間が計算されずに連携されています。
「課題作成時に登録した実績時間」を取得する方法がないため、既知の問題として置いてあります。

# TODO
下記項目については未対応です。

- テストコード
- 監視
- AWS SAMでRDSを管理
- その他便利ツール導入
https://www.slideshare.net/aodag/python-172432039

随時対応します


