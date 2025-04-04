import datetime as dt
import os
import sys
from pathlib import Path

import ops
from fluxrun_engine import FluxRunEngine


# -f F:\Sync\luhk_work\CURRENT\FRU_rECord_test\1.1-eddypro_fluxrun_calcs -d 1

class FluxRunCli:
    """
    Run FLUXRUN in specified folder without GUI

    This starts FluxRunEngine.
    """

    def __init__(self, folder: str, days: int = None):
        self.folder = Path(folder)
        self.days = days

        self.settings_dict = {}

    def _update_settings_from_args(self, settings_dict: dict) -> dict:
        """Update settings according to given args"""
        if self.days:
            settings_dict = self._days_from_arg(settings_dict=settings_dict)
        return settings_dict

    def _days_from_arg(self, settings_dict: dict) -> dict:
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
        settings_dict['rawdata_start_date'] = _newstartdatetime
        settings_dict['rawdata_end_date'] = _newenddatetime

        return settings_dict

    def run(self):
        settingsfilefound = self.search_settingsfile()

        if not settingsfilefound:
            print(f"(!)ERROR: No 'FluxRun.settings' file found. Please make sure it is in folder '{self.folder}'")
            sys.exit()

        # Read Settings: File --> Dict
        self.settings_dict = \
            ops.setup_fr.read_settings_file_to_dict(dir_settings=self.folder,
                                                    file='FluxRun.settings',
                                                    reset_paths=False)

        self.settings_dict = self._update_settings_from_args(settings_dict=self.settings_dict)

        self.execute_in_folder()

    def search_settingsfile(self):
        files = os.listdir(self.folder)
        settingsfilefound = True if 'FluxRun.settings' in files else False
        return settingsfilefound

    def execute_in_folder(self):
        bicoengine = FluxRunEngine(settings_dict=self.settings_dict)
        bicoengine.run()
