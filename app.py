from typing import Dict
from chalice import Chalice, Cron
from chalicelib.controllers import WorkTimeController
from chalicelib.repositories import TogglReportSummaryRepository
from chalicelib.repositories import DbTogglReportRepository
from chalicelib.repositories import BacklogIssueRepository
from chalicelib.usecases import ImportFromTogglUsecase

app = Chalice(app_name='nulabExamApp')
# productionでもcloudwatchにlog出力する
app.debug = True


@app.schedule(Cron(0, 23, '*', '*', '?', '*'))
# @app.schedule(Cron('0/2', '*', '*', '*', '?', '*')) #for debug
def main(event: Dict):
    app.log.info('Exec Start')
    try:
        # Create Usecase
        toggl_usecase: ImportFromTogglUsecase = ImportFromTogglUsecase(
                                TogglReportSummaryRepository(),
                                DbTogglReportRepository(),
                                BacklogIssueRepository())

        wt_controlller: WorkTimeController = WorkTimeController(toggl_usecase)
        wt_controlller.import_from_toggl()
        app.log.info('Exec End')
        return True
    except Exception as e:
        app.log.error(e)
        return False
