# -*- coding: utf-8 -*-


import os
from pathlib import Path

from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg
from PyQt6 import QtWidgets as qtw

from . import fluxrun_engine
from .gui import gui_elements as ele
from .gui.mainwindow import BuildGui
from .ops import file
from .ops.setup import read_settings_file
from .settings import version

# todo testing
print(f"{__file__}")


class FluxRunGUI(qtw.QMainWindow, BuildGui):
    def __init__(self, parent=None):
        super(FluxRunGUI, self).__init__(parent)
        self.setupUi(self)

        # Set filepath to setting YAML
        # TODO bug: script always loads settings from original script folder
        # todo I think this is an issue with the __init__.py (no, maybe not...)
        dir_script = os.path.abspath(__file__)  # Dir of this file
        dir_settings = Path(
            os.path.join(os.path.dirname(dir_script))) / 'settings'  # Preload settings dir to load settings file
        self.filepath_settings = Path(dir_settings) / 'fluxrunsettings.yaml'

        # Read settings from YAML file
        self.settings = read_settings_file(filepath_settings=self.filepath_settings)

        # Show settings in GUI
        self.show_settings_in_gui(settings=self.settings)

        # Connect GUI elements
        self._connections()

    def run(self):
        """Call FluxRunEngine for calculations"""
        self.settings = self.get_settings_from_gui()

        fluxrunengine = fluxrun_engine.FluxRunEngine(settings=self.settings)
        fluxrunengine.run()

    def update_dict_key(self, key, new_val):
        """ Updates key in Dict with new_val """
        self.settings[key] = new_val

    def show_settings_in_gui(self, settings: dict):
        """Update GUI with settings from fluxrunsettings.yaml file."""

        # RAW DATA
        _settings = settings['RAWDATA']
        self.lbl_proc_rawdata_source_dir_selected.setText(_settings['INDIR'])
        self.lne_filename_id.setText(_settings['FILENAME_ID'])
        ele.set_gui_combobox(combobox=self.cmb_rawdata_header_format, find_text=_settings['HEADER_FORMAT'])
        ele.set_gui_datetimepicker(datetimepicker=self.dtp_rawdata_time_range_start, date_str=_settings['START_DATE'])
        ele.set_gui_datetimepicker(datetimepicker=self.dtp_rawdata_time_range_end, date_str=_settings['END_DATE'])
        ele.set_gui_checkbox(checkbox=self.chk_output_plots_availability_rawdata,
                             state=_settings['PLOT_RAWDATA_AVAILABILITY'])
        ele.set_gui_checkbox(checkbox=self.chk_output_plots_aggregates_rawdata,
                             state=_settings['PLOT_RAWDATA_AGGREGATES'])

        # FLUX PROCESSING
        _settings = settings['FLUX_PROCESSING']
        ele.set_gui_checkbox(checkbox=self.chk_proc_run_fluxcalcs,
                             state=_settings['RUN_FLUX_CALCS'])
        self.lbl_proc_ep_procfile_selected.setText(_settings['EDDYPRO_PROCESSING_FILE'])

        # OUTPUT
        _settings = settings['OUTPUT']
        self.lbl_output_folder.setText(_settings['OUTDIR'])
        self.lne_outdir_prefix.setText(_settings['OUTDIR_PREFIX'])
        ele.set_gui_checkbox(checkbox=self.chk_output_plots_summary, state=_settings['PLOT_SUMMARY'])

        # AFTER PROCESSING
        _settings = settings['AFTER PROCESSING']
        ele.set_gui_checkbox(checkbox=self.chk_output_afterprocessing_delete_ascii_rawdata,
                             state=_settings['DELETE_UNCOMPRESSED_ASCII_AFTER_PROCESSING'])

    def get_settings_from_gui(self) -> dict:
        """Read settings from GUI and store in dict"""

        # Reset
        settings = self.settings.copy()

        # RAW DATA
        settings['RAWDATA']['INDIR'] = self.lbl_proc_rawdata_source_dir_selected.text()
        settings['RAWDATA']['FILENAME_ID'] = self.lne_filename_id.text()
        settings['RAWDATA']['HEADER_FORMAT'] = self.cmb_rawdata_header_format.currentText()
        settings['RAWDATA']['START_DATE'] = self.dtp_rawdata_time_range_start.dateTime().toString(
            'yyyy-MM-dd hh:mm')
        settings['RAWDATA']['END_DATE'] = self.dtp_rawdata_time_range_end.dateTime().toString('yyyy-MM-dd hh:mm')
        settings['RAWDATA']['PLOT_RAWDATA_AVAILABILITY'] = \
            1 if self.chk_output_plots_availability_rawdata.isChecked() else 0
        settings['RAWDATA']['PLOT_RAWDATA_AGGREGATES'] = \
            1 if self.chk_output_plots_aggregates_rawdata.isChecked() else 0

        # FLUX PROCESSING
        settings['FLUX_PROCESSING']['RUN_FLUX_CALCS'] = \
            1 if self.chk_proc_run_fluxcalcs.isChecked() else 0
        settings['FLUX_PROCESSING']['EDDYPRO_PROCESSING_FILE'] = self.lbl_proc_ep_procfile_selected.text()

        # OUTPUT
        settings['OUTPUT']['OUTDIR'] = self.lbl_output_folder.text()
        settings['OUTPUT']['OUTDIR_PREFIX'] = self.lne_outdir_prefix.text()
        settings['OUTPUT']['PLOT_SUMMARY'] = \
            1 if self.chk_output_plots_summary.isChecked() else 0

        # AFTER PROCESSING
        settings['AFTER PROCESSING']['DELETE_UNCOMPRESSED_ASCII_AFTER_PROCESSING'] = \
            1 if self.chk_output_afterprocessing_delete_ascii_rawdata.isChecked() else 0

        return settings

    @staticmethod
    def link(link_str):
        """Call hyperlink from label, opens in browser"""
        qtg.QDesktopServices.openUrl(qtc.QUrl(link_str))

    # def _update_text_field(self):
    #     _site = self.cmb_site_selection.currentText()
    #     _compression = self.cmb_rawdata_compr.currentText()
    #     _datetimeformat = self.lne_filedt_format.text()
    #     _ext = '<select compression>'
    #     if _compression == '.gz':
    #         _ext = '.csv.gz'
    #     elif _compression == 'None':
    #         _ext = '.csv'
    #     self.lbl_rawdata_sitefiles_parse_str.setText(f"{_site}_{_datetimeformat}{_ext}")

    def _checkbox_changed(self, state):

        if state == qtc.Qt.CheckState.Checked.value:
            self.chk_output_plots_summary.setEnabled(True)
            # self.chk_output_plots_summary.setChecked(True)
        elif state == qtc.Qt.CheckState.Unchecked.value:
            self.chk_output_plots_summary.setDisabled(True)
            self.chk_output_plots_summary.setChecked(False)

    def _connections(self):
        """Connect GUI elements to functions"""
        # SIDEBAR
        self.lbl_link_releases.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_releases__)))
        self.lbl_link_source_code.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_source_code__)))
        # self.lbl_link_license.clicked.connect(self.link)
        self.lbl_link_changelog.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_changelog__)))
        self.lbl_link_ep_changelog.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_ep_changelog__)))

        # self.cmb_site_selection.currentIndexChanged.connect(self._update_text_field)
        # self.cmb_rawdata_compr.currentIndexChanged.connect(self._update_text_field)
        # self.lne_filedt_format.textChanged.connect(self._update_text_field)
        self.chk_proc_run_fluxcalcs.stateChanged.connect(self._checkbox_changed)

        # RAW DATA
        self.btn_rawdata_source_dir.clicked.connect(lambda: self.select_dir(
            start_dir=self.settings['RAWDATA']['INDIR'],
            dir_setting=('RAWDATA', 'INDIR'),
            update_label=self.lbl_proc_rawdata_source_dir_selected,
            dialog_txt='Select Source Folder For Raw Data Files'))
        self.btn_proc_ep_procfile.clicked.connect(lambda: self.select_file(
            start_dir=self.settings['RAWDATA']['INDIR'],
            filesetting=('FLUX_PROCESSING', 'EDDYPRO_PROCESSING_FILE'),
            update_label=self.lbl_proc_ep_procfile_selected, dialog_txt='Select EddyPro *.processing file',
            ext='*.eddypro'))

        # Output
        self.btn_output_folder.clicked.connect(lambda: self.select_dir(
            start_dir=self.settings['OUTPUT']['OUTDIR'],
            dir_setting=('OUTPUT', 'OUTDIR'),
            update_label=self.lbl_output_folder, dialog_txt='Select Output Folder'))

        # Controls
        self.btn_save.clicked.connect(lambda: self.save_settings_to_file())
        self.btn_run.clicked.connect(lambda: self.run())

    def save_settings_to_file(self):
        """Save settings from the GUI to settings file."""
        self.settings = self.get_settings_from_gui()
        file.save_settings_to_file(filepath_settings=self.filepath_settings,
                                   settings=self.settings,
                                   copy_to_outdir=False)

    def select_dir(self, start_dir, dir_setting, update_label, dialog_txt):
        """ Select directory, update dict and label"""
        selected_dir = qtw.QFileDialog.getExistingDirectory(None, dialog_txt, str(start_dir))  # Open dialog
        self.settings[dir_setting[0]][dir_setting[1]] = selected_dir  # Update settings dict
        # self.settings[dir_setting] = selected_dir
        update_label.setText(self.settings[dir_setting[0]][dir_setting[1]])  # Update gui

    def select_file(self, start_dir, filesetting, update_label, dialog_txt, ext):
        """ Select file, update dict (with Path) and label (with str)"""
        selected_file = qtw.QFileDialog.getOpenFileName(None, dialog_txt, str(start_dir), ext)  # Open dialog
        self.settings[filesetting[0]][filesetting[1]] = selected_file  # Update settings dict
        txt = self.settings[filesetting[0]][filesetting[1]]
        txt = txt[0]
        update_label.setText(txt)  # Update gui
