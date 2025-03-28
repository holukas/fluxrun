import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg
from PyQt6 import QtWidgets as qtw

import ops
from gui.gui import Ui_MainWindow
from ops import cli, file
from ops.setup_fr import generate_run_id, set_outdirs, make_outdirs
from settings import _version


# TODO displacement height file?
# TODO LATER parallelize, multiprocessing?

class FluxRunEngine:

    def __init__(
            self,
            settings_dict: dict):
        self.settings_dict = settings_dict

        self.logger = None

        self.update_settings()

    def update_settings(self):
        """Update automatically derived settings"""
        self.settings_dict['_run_id'] = generate_run_id()
        _script = os.path.abspath(__file__)  # Dir of this file
        self.settings_dict['_dir_script'] = os.path.dirname(_script)
        self.settings_dict['_dir_settings'] = \
            Path(os.path.join(self.settings_dict['_dir_script'])) / 'settings'
        self.settings_dict['_dir_fluxrun'] = Path(self.settings_dict['_dir_script']).parents[0]
        self.settings_dict['_dir_root'] = Path(self.settings_dict['_dir_script']).parents[1]
        self.settings_dict = set_outdirs(settings_dict=self.settings_dict)
        self.make_parsing_strings()
        make_outdirs(settings_dict=self.settings_dict)
        self.set_dir_eddypro_rawdata()

    def run(self):

        # Logger
        self.logger = ops.logger.setup_logger(settings_dict=self.settings_dict)
        self.logger.info(f"\n\nRun ID: {self.settings_dict['_run_id']}")
        self.logger.info(f"FluxRun Version: {_version.__version__} / {_version.__date__}\n\n")

        self.settings_dict = ops.file.PrepareEddyProFiles(settings_dict=self.settings_dict, logger=self.logger).get()
        file.save_settings_to_file(settings_dict=self.settings_dict, copy_to_outdir=True)

        # Search valid raw ASCII files, depending on settings
        self.rawdata_found_files_dict = ops.file.SearchAll(
            settings_dict=self.settings_dict,
            logger=self.logger,
            search_in_dir=self.settings_dict['rawdata_indir']) \
            .keep_valid_files()

        if not self.rawdata_found_files_dict:
            self.logger.info("(!)ERROR No raw data files found. Please check settings.")
            sys.exit(-1)

        # Get raw data files for processing, uncompress if needed
        if self.settings_dict['rawdata_file_compression'] == 'gzip':
            ops.file.uncompress_gzip(settings_dict=self.settings_dict,
                                     found_gzip_files_dict=self.rawdata_found_files_dict,
                                     logger=self.logger)
            # Files were uncompressed, search those files
            self.rawdata_found_files_dict = ops.file.SearchAll(
                settings_dict=self.settings_dict,
                logger=self.logger,
                search_in_dir=self.settings_dict['_dir_used_rawdata_ascii_files_eddypro_data_path'],
                search_uncompressed=True) \
                .keep_valid_files()
        elif self.settings_dict['rawdata_file_compression'] == 'None':
            # In this case files are already uncompressed
            pass
            # file.copy_rawdata_files(...)

        # Availability heatmap for *uncompressed* raw data files
        if self.settings_dict['plot_availability_rawdata'] == '1':
            ops.vis.availability_rawdata(rawdata_found_files_dict=self.rawdata_found_files_dict,
                                         rawdata_file_datefrmt=self.settings_dict['_sitefiles_parse_str'].rstrip('.gz'),
                                         outdir=self.settings_dict['_dir_out_run_plots_availability_rawdata'],
                                         logger=self.logger)

        # Plot stats for *uncompressed* raw data files
        if self.settings_dict['plot_aggregates_rawdata'] == '1':
            ops.vis.PlotRawDataFilesAggregates(
                rawdata_found_files_dict=self.rawdata_found_files_dict,
                settings_dict=self.settings_dict,
                logger=self.logger,
                rawdata_file_datefrmt=self.settings_dict['_sitefiles_parse_str'].rstrip('.gz'))

        # Call EddyPro processing
        rp_process_status = self.run_eddypro_cmd(cmd='eddypro_rp.exe')  # execute exe todo for linux and osx

        # Check if EddyPro full_output file was already generated
        found_full_output, _ = ops.file.check_if_file_in_folder(search_str='*_full_output_*.csv',
                                                                folder=self.settings_dict[
                                                                    '_dir_out_run_eddypro_results'])
        if found_full_output:
            self.logger.info("(!)WARNING EddyPro RP already generated a full_output file. FCC will be skipped. "
                             "This is not necessarily bad.")

        if rp_process_status == 0 and found_full_output is False:
            fcc_process_status = self.run_eddypro_cmd(cmd='eddypro_fcc.exe')  # execute exe todo for linux and osx

        self._plot_summary()
        self._delete_uncompressed_ascii_files()

        self.logger.info("\n\n\n")
        self.logger.info("=" * 60)
        self.logger.info("FluxRun finished.")
        self.logger.info("=" * 60)

    def _plot_summary(self):
        """Generate summary plots"""
        found_full_output, filepath_full_output = \
            ops.file.check_if_file_in_folder(search_str='*_full_output_*.csv',
                                             folder=self.settings_dict['_dir_out_run_eddypro_results'])
        if found_full_output and int(self.settings_dict['plot_summary']) == 1:
            ops.vis.PlotEddyProFullOutputFile(
                file_to_plot=filepath_full_output,
                destination_folder=self.settings_dict['_dir_out_run_plots_summary'],
                logger=self.logger).run()
        else:
            self.logger.info("(!)WARNING No *_full_output_* file was found. Skipping summary plots.")

    def _delete_uncompressed_ascii_files(self):
        """Delete uncompressed (unzipped) ASCII files that were used for flux processing"""
        if int(self.settings_dict['delete_uncompressed_ascii_after_processing']) == 1:
            uncompressed_ascii_files = ops.file.SearchAll(
                settings_dict=self.settings_dict,
                logger=self.logger,
                search_in_dir=self.settings_dict['_dir_out_run_rawdata_ascii_files'],
                search_uncompressed=True) \
                .keep_valid_files()

            # Convert to list
            deletepaths = []
            for filename, filepath in uncompressed_ascii_files.items():
                deletepaths.append(filepath)

            # Keep the last file
            deletepaths = list(deletepaths)[:-1]

            # Make sure there are CSVs only
            deletelist = []
            [deletelist.append(x) for x in deletepaths if x.suffix == '.csv']

            # Delete files
            for filepath in deletelist:
                self.logger.info(f"Deleting uncompressed (unzipped) ASCII file: {filepath}) ...")
                os.remove(filepath)

    def run_eddypro_cmd(self, cmd: str):
        """Run eddypro_rp.exe or eddypro_fcc.exe"""

        os.chdir(self.settings_dict['_dir_out_run_eddypro_bin'])  # go to eddypro bin folder
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)  # call cmd command
        while process.poll() is None:
            # This blocks until it receives a newline.
            line = process.stdout.readline().decode('utf-8').replace('\r\n', '')
            if 'processing new flux averaging period' in line:
                self.logger.info("-" * 60)  # to better see the different days in the output
            else:
                self.logger.info(f"[EDDYPRO LOG] [{cmd}] {line}")
        # When the subprocess terminates there might be unconsumed output that still needs to be processed.
        self.logger.info(process.stdout.read().decode('utf-8').replace('\r\n', ''))
        process_status = process.wait()  # Wait for cmd to terminate. Get return returncode

        # CHECK IF FINISHED SUCCESSFULLY
        self.logger.info("*" * 30)
        self.logger.info(f"[EDDYPRO LOG] {cmd} return code: {process_status}")
        if process_status == 0:
            self.logger.info(f"[EDDYPRO LOG] {cmd} finished successfully.")
        else:
            self.logger.info(f"[EDDYPRO LOG] (!)ERROR {cmd} encountered a problem.")
        self.logger.info("*" * 30)
        return process_status

    def make_parsing_strings(self):
        """Make parsing strings to parse info from raw data filenames"""

        # Assemble search strings

        file_ext = Path(self.settings_dict['rawdata_filename_datetime_format']).suffix

        if not file_ext:
            # If no file extension given in setting 'rawdata_filename_datetime_format',
            # the by default '.csv' is used
            if self.settings_dict['rawdata_file_compression'] == 'gzip':
                file_ext_search = '.csv.gz'
                file_ext_parsing = '.csv.gz'
            else:
                file_ext_search = '.csv'
                file_ext_parsing = '.csv'

        else:
            if self.settings_dict['rawdata_file_compression'] == 'gzip':
                file_ext_search = f'{file_ext}.gz'
                file_ext_parsing = '.gz'
            else:
                # File extension already given in setting 'rawdata_filename_datetime_format'
                file_ext_search = file_ext
                file_ext_parsing = ''

        self.settings_dict['_sitefiles_search_str'] = f"{self.settings_dict['site']}_*{file_ext_search}"
        # print(self.settings_dict['_sitefiles_search_str'])

        # Convert given parsing string to a string containing datetime characters that Python understands, e.g. %Y
        self.settings_dict['filename_datetime_parsing_string'] = self.make_datetime_parsing_string()

        # Construct exact parsing string
        self.settings_dict['_sitefiles_parse_str'] = f"{self.settings_dict['site']}_" \
                                                     f"{self.settings_dict['filename_datetime_parsing_string']}" \
                                                     f"{file_ext_parsing}"
        # print(self.settings_dict['_sitefiles_parse_str'])
        # print(self.settings_dict['_sitefiles_parse_str'])

    def make_datetime_parsing_string(self):
        """Parse filename for datetime info"""
        _parsing_string = self.settings_dict['rawdata_filename_datetime_format']
        _parsing_string = _parsing_string.replace('yyyy', '%Y')
        _parsing_string = _parsing_string.replace('mm', '%m')
        _parsing_string = _parsing_string.replace('dd', '%d')
        _parsing_string = _parsing_string.replace('HH', '%H')
        _parsing_string = _parsing_string.replace('MM', '%M')
        # _parsing_string = f"{self.settings_dict['site']}_{_parsing_string}"  # Add site id
        return _parsing_string

    def set_dir_eddypro_rawdata(self):
        """
        Set raw data folder for EddyPro flux calculations

        Compressed files will be uncompressed and saved to the current run output folder.
        Uncompressed files will be directly used from where they are stored.
        """
        if self.settings_dict['rawdata_file_compression'] == 'gzip':
            self.settings_dict['_dir_used_rawdata_ascii_files_eddypro_data_path'] = \
                self.settings_dict['_dir_out_run_rawdata_ascii_files']

        elif self.settings_dict['rawdata_file_compression'] == 'None':
            outpath = Path(self.settings_dict['_dir_out_run_rawdata_ascii_files']) / 'readme.txt'
            readme_txt = open(str(outpath), "w+")
            readme_txt.write(f"This folder is empty because uncompressed ASCII raw data files from the "
                             f"following folder were used for flux calculations:\n\n"
                             f"{self.settings_dict['rawdata_indir']}")
            self.settings_dict['_dir_used_rawdata_ascii_files_eddypro_data_path'] = \
                self.settings_dict['rawdata_indir']


class FluxRunGUI(qtw.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(FluxRunGUI, self).__init__(parent)
        self.setupUi(self)

        # Detect Folders
        dir_script = os.path.abspath(__file__)  # Dir of this file
        dir_settings = Path(
            os.path.join(os.path.dirname(dir_script))) / 'settings'  # Preload settings dir to load settings file

        # Read previous settings: File --> Dict
        self.settings_dict = \
            ops.setup_fr.read_settings_file_to_dict(dir_settings=dir_settings,
                                                    file='FluxRun.settings',
                                                    reset_paths=False)
        self.reset_derived_settings()

        # Fill-In Settings: Dict --> GUI
        self.show_settings_in_gui()

        # Connect GUI elements
        self.connections()

    def run(self):
        """Call FluxRunEngine for calculations"""
        self.get_settings_from_gui()

        fluxrunengine = FluxRunEngine(settings_dict=self.settings_dict)
        fluxrunengine.run()

    def reset_derived_settings(self):
        """
        Reset all settings that are constructed from GUI settings
        """
        for key, val in self.settings_dict.items():
            if str(key).startswith('_'):
                self.settings_dict[key] = ""

    def update_dict_key(self, key, new_val):
        """ Updates key in Dict with new_val """
        self.settings_dict[key] = new_val
        # ('{}: {}'.format(key, self.settings_dict[key]))

    def get_settings_from_gui(self):
        """Read settings from GUI and store in dict"""
        # Instruments
        self.update_dict_key(key='site', new_val=self.cmb_site_selection.currentText())
        # self.update_dict_key(key='header', new_val=self.cmb_instr_header.currentText())

        # Processing
        self.update_dict_key(key='rawdata_indir', new_val=self.lbl_proc_rawdata_source_dir_selected.text())
        self.update_dict_key(key='rawdata_start_date',
                             new_val=self.dtp_rawdata_time_range_start.dateTime().toString('yyyy-MM-dd hh:mm'))
        self.update_dict_key(key='rawdata_end_date',
                             new_val=self.dtp_rawdata_time_range_end.dateTime().toString('yyyy-MM-dd hh:mm'))
        self.update_dict_key(key='rawdata_filename_datetime_format',
                             new_val=self.lne_filedt_format.text())
        self.update_dict_key(key='rawdata_file_compression', new_val=self.cmb_rawdata_compr.currentText())
        self.update_dict_key(key='rawdata_header_format', new_val=self.cmb_rawdata_header_format.currentText())
        self.update_dict_key(key='path_selected_eddypro_processing_file',
                             new_val=Path(self.lbl_proc_ep_procfile_selected.text()))

        # Output
        self.update_dict_key(key='dir_out', new_val=Path(self.lbl_output_folder.text()))

        self.update_dict_key(key='plot_availability_rawdata',
                             new_val='1' if self.chk_output_plots_availability_rawdata.isChecked() else '0')
        self.update_dict_key(key='plot_aggregates_rawdata',
                             new_val='1' if self.chk_output_plots_aggregates_rawdata.isChecked() else '0')
        self.update_dict_key(key='plot_summary',
                             new_val='1' if self.chk_output_plots_summary.isChecked() else '0')

        self.update_dict_key(key='delete_uncompressed_ascii_after_processing',
                             new_val='1' if self.chk_output_afterprocessing_delete_ascii_rawdata.isChecked() else '0')

    def set_gui_combobox(self, combobox, find_text):
        idx = combobox.findText(find_text, qtc.Qt.MatchFlag.MatchContains)
        if idx >= 0:
            combobox.setCurrentIndex(idx)

    def set_gui_datetimepicker(self, datetimepicker, date_str):
        qtDate = qtc.QDateTime.fromString(date_str, 'yyyy-MM-dd hh:mm')
        datetimepicker.setDateTime(qtDate)

    def set_gui_lineedit(self, lineedit, string):
        lineedit.setText(string)

    def set_gui_checkbox(self, checkbox, state):
        checkbox.setChecked(True if state == '1' else False)

    def show_settings_in_gui(self):
        """Update GUI from dict"""
        # Instruments
        self.set_gui_combobox(combobox=self.cmb_site_selection, find_text=self.settings_dict['site'])
        # self.set_gui_combobox(combobox=self.cmb_instr_header, find_text=self.settings_dict['header'])

        # Processing
        self.lbl_proc_rawdata_source_dir_selected.setText(str(self.settings_dict['rawdata_indir']))
        self.set_gui_datetimepicker(datetimepicker=self.dtp_rawdata_time_range_start,
                                    date_str=self.settings_dict['rawdata_start_date'])
        self.set_gui_datetimepicker(datetimepicker=self.dtp_rawdata_time_range_end,
                                    date_str=self.settings_dict['rawdata_end_date'])
        self.set_gui_lineedit(lineedit=self.lne_filedt_format,
                              string=self.settings_dict['rawdata_filename_datetime_format'])
        self.set_gui_combobox(combobox=self.cmb_rawdata_compr,
                              find_text=self.settings_dict['rawdata_file_compression'])
        self.set_gui_combobox(combobox=self.cmb_rawdata_header_format,
                              find_text=self.settings_dict['rawdata_header_format'])
        self.lbl_proc_ep_procfile_selected.setText(str(self.settings_dict['path_selected_eddypro_processing_file']))

        # Output
        self.lbl_output_folder.setText(str(self.settings_dict['dir_out']))

        self.set_gui_checkbox(checkbox=self.chk_output_plots_availability_rawdata,
                              state=self.settings_dict['plot_availability_rawdata'])
        self.set_gui_checkbox(checkbox=self.chk_output_plots_aggregates_rawdata,
                              state=self.settings_dict['plot_aggregates_rawdata'])
        self.set_gui_checkbox(checkbox=self.chk_output_plots_summary,
                              state=self.settings_dict['plot_summary'])

        self.set_gui_checkbox(checkbox=self.chk_output_afterprocessing_delete_ascii_rawdata,
                              state=self.settings_dict['delete_uncompressed_ascii_after_processing'])

    def link(self, link_str):
        """Call hyperlink from label, opens in browser"""
        qtg.QDesktopServices.openUrl(qtc.QUrl(link_str))

    def _update_text_field(self):
        # TODO init on start
        # TODO testing dynamic text update
        # TODO use searchfilestring directly for search
        _site = self.cmb_site_selection.currentText()
        _compression = self.cmb_rawdata_compr.currentText()
        _datetimeformat = self.lne_filedt_format.text()
        _ext = '<select compression>'
        if _compression == 'gzip':
            _ext = '.csv.gzip'
        elif _compression == 'None':
            _ext = '.csv'
        self.lbl_rawdata_searchfilestring.setText(f"{_site}_{_datetimeformat}{_ext}")

    def connections(self):
        """Connect GUI elements to functions"""
        # Logo
        self.lbl_link_releases.linkActivated.connect(self.link)
        self.lbl_link_source_code.linkActivated.connect(self.link)
        # self.lbl_link_license.linkActivated.connect(self.link)
        self.lbl_link_changelog.linkActivated.connect(self.link)
        self.lbl_link_ep_changelog.linkActivated.connect(self.link)

        # TODO testing dynamic text update
        self.cmb_site_selection.currentIndexChanged.connect(self._update_text_field)
        self.cmb_rawdata_compr.currentIndexChanged.connect(self._update_text_field)
        self.lne_filedt_format.textChanged.connect(self._update_text_field)

        # Processing
        self.btn_rawdata_source_dir.clicked.connect(lambda: self.select_dir(
            start_dir=self.settings_dict['rawdata_indir'], dir_setting='rawdata_indir',
            update_label=self.lbl_proc_rawdata_source_dir_selected,
            dialog_txt='Select Source Folder For Raw Data Files'))
        self.btn_proc_ep_procfile.clicked.connect(lambda: self.select_file(
            start_dir=self.settings_dict['rawdata_indir'], filesetting='path_selected_eddypro_processing_file',
            update_label=self.lbl_proc_ep_procfile_selected, dialog_txt='Select EddyPro *.processing file',
            ext='*.eddypro'))

        # Output
        self.btn_output_folder.clicked.connect(lambda: self.select_dir(
            start_dir=self.settings_dict['dir_out'], dir_setting='dir_out',
            update_label=self.lbl_output_folder, dialog_txt='Select Output Folder'))

        # Controls
        self.btn_run.clicked.connect(lambda: self.run())

    def select_dir(self, start_dir, dir_setting, update_label, dialog_txt):
        """ Select directory, update dict and label"""
        selected_dir = qtw.QFileDialog.getExistingDirectory(None, dialog_txt, str(start_dir))  # Open dialog
        self.settings_dict[dir_setting] = selected_dir  # Update settings dict
        update_label.setText(self.settings_dict[dir_setting])  # Update gui
        # ops.setup.settings_dict_to_file(settings_dict=self.settings_dict)  # Save to file

    def select_file(self, start_dir, filesetting, update_label, dialog_txt, ext):
        """ Select file, update dict (with Path) and label (with str)"""
        selected_file = qtw.QFileDialog.getOpenFileName(None, dialog_txt, str(start_dir), ext)  # Open dialog
        self.settings_dict[filesetting] = selected_file  # Update settings dict
        update_label.setText(self.settings_dict[filesetting][0])  # Update gui


class FluxRunFolder:
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


def main(args):
    abspath = Path(os.path.abspath(__file__)).parent  # directory of bico.py
    os.chdir(abspath)
    wd = os.getcwd()
    print(f"Working directory: {wd}")

    # Run FLUXRUN w/o GUI
    if args.folder:
        days = args.days if args.days else None
        bicofromfolder = FluxRunFolder(folder=args.folder, days=days)
        bicofromfolder.run()

    # Run FLUXRUN with GUI
    if args.gui:
        app = qtw.QApplication(sys.argv)
        fluxrunfromgui = FluxRunGUI()
        fluxrunfromgui.show()
        app.exec()

    else:
        print("Please add arg how FLUXRUN should be executed. Add '-h' for help.")


if __name__ == '__main__':
    args = cli.get_args()
    args = cli.validate_args(args)
    main(args)
