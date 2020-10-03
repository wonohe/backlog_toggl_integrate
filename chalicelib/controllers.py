"""
Controller modules.

define contollers.
"""
from chalice import Chalice
from chalicelib.usecases import ImportFromTogglUsecase


app = Chalice(app_name='nulabExamApp')
# productionでもcloudwatchにlog出力する
app.debug = True


class WorkTimeController:
    """WorkTime contoroller
    """

    def __init__(
            self,
            import_from_toggl_usecase: ImportFromTogglUsecase):

        self.import_from_toggl_usecase = import_from_toggl_usecase
        pass

    def import_from_toggl(self):
        """ import from toggl data

        Args:
            None

        Return:
            Boolean

        """
        return self.import_from_toggl_usecase.handle()
