import datetime as dt
import os
from pathlib import Path

from fluxrun.ops.setup import read_settings_file
from fluxrun_engine import FluxRunEngine


# -f F:\Sync\luhk_work\CURRENT\FRU_rECord_test\with_cli -d 9999

class FluxRunCli:
    """
    Run FLUXRUN in specified folder without GUI

    This starts FluxRunEngine.
    """

    def __init__(self, folder: str, days: int = None):
        self.folder = Path(folder)
        self.days = days

        self.settings = {}

    def _update_settings_from_args(self, settings: dict) -> dict:
        """Update settings according to given args"""
        if self.days:
            settings = self._days_from_arg(settings=settings)
        return settings

    def _days_from_arg(self, settings: dict) -> dict:
        """Set new start and end date according to DAYS arg"""
        # Get current time, subtract number of days
        _currentdate = dt.datetime.now().date()
        _newstartdate = _currentdate - dt.timedelta(days=self.days)

        # Define new start date
        _newstartdatetime = dt.datetime(year=_newstartdate.year, month=_newstartdate.month,
                                        day=_newstartdate.day, hour=0, minute=0)
        _newstartdatetime = _newstartdatetime.strftime('%Y-%m-%d %H:%M')  # As string

        # Define new end date (now)
        _newenddatetime = dt.datetime.now()
        _newenddatetime = _newenddatetime.strftime('%Y-%m-%d %H:%M')

        # Update dict
        settings['_rawdata_start_date'] = _newstartdatetime
        settings['_rawdata_end_date'] = _newenddatetime

        return settings

    def run(self):
        filepath_settings = self.search_settingsfile()
        self.settings = read_settings_file(filepath_settings=filepath_settings)
        self.settings = self._update_settings_from_args(settings=self.settings)
        self.execute_in_folder()

    def search_settingsfile(self):
        files = os.listdir(self.folder)
        settingsfilefound = True if 'fluxrunsettings.yaml' in files else False
        if settingsfilefound:
            filepath_settings = Path(self.folder) / 'fluxrunsettings.yaml'
        else:
            raise FileNotFoundError(f'No fluxrunsettings.yaml file found in folder {self.folder}.')
        return filepath_settings

    def execute_in_folder(self):
        _fluxrunengine = FluxRunEngine(settings=self.settings)
        _fluxrunengine.run()
