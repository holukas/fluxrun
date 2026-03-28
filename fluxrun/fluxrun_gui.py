# -*- coding: utf-8 -*-
"""FluxRun GUI application using PyQt6.

This module provides the main GUI interface for FluxRun, allowing users to
configure raw data processing settings, EddyPro flux calculations, and output
options through an intuitive PyQt6 interface.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg
from PyQt6 import QtWidgets as qtw

from . import fluxrun_engine
from .gui import gui_elements as ele
from .gui.mainwindow import BuildGui
from .gui.settings_manager import SettingsKeys, SettingsDefaults, SettingsSectionMapping
from .ops import file
from .ops.setup import read_settings_file
from .settings import version


class FluxRunGUI(qtw.QMainWindow, BuildGui):
    """Main GUI application for FluxRun flux calculations and data processing.

    Provides a PyQt6-based interface for configuring raw data files, flux
    processing settings, output options, and triggering calculation runs.

    Attributes:
        settings: Dictionary containing current application settings from YAML file.
        filepath_settings: Path to the fluxrunsettings.yaml configuration file.
    """

    def __init__(self, parent: Optional[qtw.QWidget] = None) -> None:
        """Initialize the FluxRun GUI application.

        Args:
            parent: Parent widget (default: None).
        """
        super(FluxRunGUI, self).__init__(parent)
        self.setupUi(self)

        # Resolve settings file path using pathlib for clarity and reliability
        self.filepath_settings: Path = Path(__file__).parent / 'settings' / 'fluxrunsettings.yaml'

        # Read settings from YAML file
        self.settings: Dict[str, Any] = read_settings_file(filepath_settings=self.filepath_settings)

        # Show settings in GUI
        self.show_settings_in_gui(settings=self.settings)

        # Connect GUI elements to their respective handlers
        self._connections()

    def run(self) -> None:
        """Execute the FluxRun processing pipeline.

        Collects all settings from GUI widgets, saves them, and passes them
        to the FluxRunEngine for processing calculations.
        """
        self.settings = self.get_settings_from_gui()

        fluxrunengine = fluxrun_engine.FluxRunEngine(settings=self.settings)
        fluxrunengine.run()

    def update_dict_key(self, key: str, new_val: Any) -> None:
        """Update a single key in the settings dictionary.

        Args:
            key: Dictionary key to update.
            new_val: New value for the key.
        """
        self.settings[key] = new_val

    def show_settings_in_gui(self, settings: Dict[str, Any]) -> None:
        """Populate GUI widgets with values from settings dictionary.

        Uses metadata-driven approach via SettingsSectionMapping to eliminate
        code duplication between show and get methods.

        Args:
            settings: Dictionary containing settings loaded from YAML file.
        """
        for section_key, field_mappings in SettingsSectionMapping.SECTIONS.items():
            section_settings = settings.get(section_key, {})
            for settings_key, widget_name in field_mappings:
                widget = getattr(self, widget_name, None)
                if widget is None:
                    continue
                value = section_settings.get(settings_key)
                self._set_widget_value(widget, value, settings_key)

    def get_settings_from_gui(self) -> Dict[str, Any]:
        """Collect all settings from GUI widgets into dictionary.

        Uses metadata-driven approach via SettingsSectionMapping to eliminate
        code duplication between show and get methods.

        Returns:
            Dictionary with all settings from GUI widgets in YAML structure.
        """
        settings = self.settings.copy()

        for section_key, field_mappings in SettingsSectionMapping.SECTIONS.items():
            for settings_key, widget_name in field_mappings:
                widget = getattr(self, widget_name, None)
                if widget is None:
                    continue
                value = self._get_widget_value(widget, settings_key)
                settings[section_key][settings_key] = value

        return settings

    def _set_widget_value(self, widget: qtw.QWidget, value: Any, settings_key: str) -> None:
        """Set widget value from settings value.

        Dispatches to appropriate setter based on widget type.

        Args:
            widget: PyQt6 widget to update.
            value: Value to set in the widget.
            settings_key: Settings key (used for context).
        """
        if isinstance(widget, qtw.QLineEdit):
            widget.setText(str(value or ''))
        elif isinstance(widget, qtw.QLabel):
            widget.setText(str(value or ''))
        elif isinstance(widget, qtw.QComboBox):
            ele.set_gui_combobox(combobox=widget, find_text=str(value or ''))
        elif isinstance(widget, qtw.QCheckBox):
            checkbox_value = int(value) if value is not None else SettingsDefaults.CHECKBOX_UNCHECKED
            widget.setChecked(bool(checkbox_value))
        elif isinstance(widget, qtw.QDateTimeEdit):
            ele.set_gui_datetimepicker(datetimepicker=widget, date_str=str(value or ''))

    def _get_widget_value(self, widget: qtw.QWidget, settings_key: str) -> Any:
        """Get widget value and convert to settings format.

        Dispatches to appropriate getter based on widget type.

        Args:
            widget: PyQt6 widget to read from.
            settings_key: Settings key (used for context).

        Returns:
            Value in appropriate format for settings dictionary.
        """
        if isinstance(widget, qtw.QLineEdit):
            return widget.text()
        elif isinstance(widget, qtw.QLabel):
            return widget.text()
        elif isinstance(widget, qtw.QComboBox):
            return widget.currentText()
        elif isinstance(widget, qtw.QCheckBox):
            return SettingsDefaults.CHECKBOX_CHECKED if widget.isChecked() else SettingsDefaults.CHECKBOX_UNCHECKED
        elif isinstance(widget, qtw.QDateTimeEdit):
            return widget.dateTime().toString(SettingsDefaults.DATETIME_FORMAT)
        return None

    @staticmethod
    def link(link_str: str) -> None:
        """Open a hyperlink in the default web browser.

        Args:
            link_str: URL to open.
        """
        qtg.QDesktopServices.openUrl(qtc.QUrl(link_str))

    def _checkbox_changed(self, state: int) -> None:
        """Handle checkbox state changes for dependencies.

        When 'Run flux calculations' checkbox changes, enable/disable and
        update the 'Summary plots' checkbox accordingly.

        Args:
            state: Qt checkbox state value.
        """
        if state == qtc.Qt.CheckState.Checked.value:
            self.chk_output_plots_summary.setEnabled(True)
        elif state == qtc.Qt.CheckState.Unchecked.value:
            self.chk_output_plots_summary.setDisabled(True)
            self.chk_output_plots_summary.setChecked(False)

    def _connections(self) -> None:
        """Connect all GUI widget signals to their respective handler methods.

        Sets up event connections for buttons, checkboxes, and links that
        drive the application's interactive behavior.
        """
        # SIDEBAR - External links
        self.lbl_link_releases.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_releases__)))
        self.lbl_link_source_code.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_source_code__)))
        self.lbl_link_changelog.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_changelog__)))
        self.lbl_link_ep_changelog.clicked.connect(
            lambda: qtg.QDesktopServices.openUrl(qtc.QUrl(version.__link_ep_changelog__)))

        # Checkbox state change handler
        self.chk_proc_run_fluxcalcs.stateChanged.connect(self._checkbox_changed)

        # RAW DATA - File/folder selection
        self.btn_rawdata_source_dir.clicked.connect(lambda: self.select_dir(
            start_dir=self.settings[SettingsKeys.RAWDATA][SettingsKeys.RAWDATA_INDIR],
            dir_setting=(SettingsKeys.RAWDATA, SettingsKeys.RAWDATA_INDIR),
            update_label=self.lbl_proc_rawdata_source_dir_selected,
            dialog_txt='Select Source Folder For Raw Data Files'))
        self.btn_proc_ep_procfile.clicked.connect(lambda: self.select_file(
            start_dir=self.settings[SettingsKeys.RAWDATA][SettingsKeys.RAWDATA_INDIR],
            filesetting=(SettingsKeys.FLUX_PROCESSING, SettingsKeys.FLUX_EDDYPRO_FILE),
            update_label=self.lbl_proc_ep_procfile_selected,
            dialog_txt='Select EddyPro *.processing file',
            ext='*.eddypro'))

        # OUTPUT - Output folder selection
        self.btn_output_folder.clicked.connect(lambda: self.select_dir(
            start_dir=self.settings[SettingsKeys.OUTPUT][SettingsKeys.OUTPUT_OUTDIR],
            dir_setting=(SettingsKeys.OUTPUT, SettingsKeys.OUTPUT_OUTDIR),
            update_label=self.lbl_output_folder,
            dialog_txt='Select Output Folder'))

        # ACTION BUTTONS - Save and Run
        self.btn_save.clicked.connect(lambda: self.save_settings_to_file())
        self.btn_run.clicked.connect(lambda: self.run())

    def save_settings_to_file(self) -> None:
        """Save all current GUI settings to the YAML configuration file.

        Collects settings from all widgets and writes them back to the
        fluxrunsettings.yaml file for persistence.
        """
        self.settings = self.get_settings_from_gui()
        file.save_settings_to_file(filepath_settings=self.filepath_settings,
                                   settings=self.settings,
                                   copy_to_outdir=False)

    def select_dir(self, start_dir: str, dir_setting: Tuple[str, str],
                   update_label: qtw.QLabel, dialog_txt: str) -> None:
        """Open directory selection dialog and update settings and GUI.

        Args:
            start_dir: Starting directory path for the dialog.
            dir_setting: Tuple of (section_key, setting_key) for storing the result.
            update_label: Label widget to update with selected path.
            dialog_txt: Dialog title text.
        """
        selected_dir = qtw.QFileDialog.getExistingDirectory(None, dialog_txt, str(start_dir))

        # Handle dialog cancellation
        if not selected_dir:
            return

        # Update settings dictionary and GUI label
        self.settings[dir_setting[0]][dir_setting[1]] = selected_dir
        update_label.setText(selected_dir)

    def select_file(self, start_dir: str, filesetting: Tuple[str, str],
                    update_label: qtw.QLabel, dialog_txt: str, ext: str) -> None:
        """Open file selection dialog and update settings and GUI.

        Args:
            start_dir: Starting directory path for the dialog.
            filesetting: Tuple of (section_key, setting_key) for storing the result.
            update_label: Label widget to update with selected file path.
            dialog_txt: Dialog title text.
            ext: File extension filter (e.g., '*.eddypro').
        """
        selected_file_tuple = qtw.QFileDialog.getOpenFileName(None, dialog_txt, str(start_dir), ext)

        # getOpenFileName returns tuple (filename, filter); extract filename
        selected_file = selected_file_tuple[0] if selected_file_tuple else ''

        # Handle dialog cancellation
        if not selected_file:
            return

        # Update settings dictionary and GUI label
        self.settings[filesetting[0]][filesetting[1]] = selected_file
        update_label.setText(selected_file)
