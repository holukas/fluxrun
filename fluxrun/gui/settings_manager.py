# -*- coding: utf-8 -*-
"""Settings configuration and management for FluxRun GUI.

This module provides centralized constants for all settings dictionary keys,
eliminating magic strings throughout the codebase and providing a single
source of truth for the settings structure.
"""

from typing import Dict, List, Tuple, Any


class SettingsKeys:
    """Central registry of all settings dictionary keys.

    Organizes settings keys by their YAML section for clarity and
    to prevent errors from typos in string literals.
    """

    # RAWDATA section
    RAWDATA = 'RAWDATA'
    RAWDATA_INDIR = 'INDIR'
    RAWDATA_FILENAME_ID = 'FILENAME_ID'
    RAWDATA_HEADER_FORMAT = 'HEADER_FORMAT'
    RAWDATA_START_DATE = 'START_DATE'
    RAWDATA_END_DATE = 'END_DATE'
    RAWDATA_PLOT_AVAILABILITY = 'PLOT_RAWDATA_AVAILABILITY'
    RAWDATA_PLOT_AGGREGATES = 'PLOT_RAWDATA_AGGREGATES'

    # FLUX_PROCESSING section
    FLUX_PROCESSING = 'FLUX_PROCESSING'
    FLUX_RUN_CALCS = 'RUN_FLUX_CALCS'
    FLUX_EDDYPRO_FILE = 'EDDYPRO_PROCESSING_FILE'

    # OUTPUT section
    OUTPUT = 'OUTPUT'
    OUTPUT_OUTDIR = 'OUTDIR'
    OUTPUT_PREFIX = 'OUTDIR_PREFIX'
    OUTPUT_PLOT_SUMMARY = 'PLOT_SUMMARY'

    # AFTER PROCESSING section
    AFTER_PROCESSING = 'AFTER PROCESSING'
    AFTER_PROCESSING_DELETE_ASCII = 'DELETE_UNCOMPRESSED_ASCII_AFTER_PROCESSING'


class SettingsDefaults:
    """Default values and configuration for settings."""

    DATETIME_FORMAT = 'yyyy-MM-dd hh:mm'
    CHECKBOX_UNCHECKED = 0
    CHECKBOX_CHECKED = 1


class SettingsSectionMapping:
    """Mapping of settings keys to widget names for metadata-driven GUI updates.

    This mapping eliminates code duplication between show_settings_in_gui()
    and get_settings_from_gui() by providing a single source of truth for
    which settings keys correspond to which GUI widgets.

    Each entry is a tuple of (settings_key, widget_name).
    """

    SECTIONS: Dict[str, List[Tuple[str, str]]] = {
        SettingsKeys.RAWDATA: [
            (SettingsKeys.RAWDATA_INDIR, 'lbl_proc_rawdata_source_dir_selected'),
            (SettingsKeys.RAWDATA_FILENAME_ID, 'lne_filename_id'),
            (SettingsKeys.RAWDATA_HEADER_FORMAT, 'cmb_rawdata_header_format'),
            (SettingsKeys.RAWDATA_START_DATE, 'dtp_rawdata_time_range_start'),
            (SettingsKeys.RAWDATA_END_DATE, 'dtp_rawdata_time_range_end'),
            (SettingsKeys.RAWDATA_PLOT_AVAILABILITY, 'chk_output_plots_availability_rawdata'),
            (SettingsKeys.RAWDATA_PLOT_AGGREGATES, 'chk_output_plots_aggregates_rawdata'),
        ],
        SettingsKeys.FLUX_PROCESSING: [
            (SettingsKeys.FLUX_RUN_CALCS, 'chk_proc_run_fluxcalcs'),
            (SettingsKeys.FLUX_EDDYPRO_FILE, 'lbl_proc_ep_procfile_selected'),
        ],
        SettingsKeys.OUTPUT: [
            (SettingsKeys.OUTPUT_OUTDIR, 'lbl_output_folder'),
            (SettingsKeys.OUTPUT_PREFIX, 'lne_outdir_prefix'),
            (SettingsKeys.OUTPUT_PLOT_SUMMARY, 'chk_output_plots_summary'),
        ],
        SettingsKeys.AFTER_PROCESSING: [
            (SettingsKeys.AFTER_PROCESSING_DELETE_ASCII, 'chk_output_afterprocessing_delete_ascii_rawdata'),
        ],
    }

    @staticmethod
    def get_all_mappings() -> Dict[str, Tuple[str, str]]:
        """Return a flat dictionary of all setting_key -> widget_name mappings.

        Returns:
            Dictionary mapping each settings key to its widget name.
        """
        all_mappings: Dict[str, Tuple[str, str]] = {}
        for section_key, field_mappings in SettingsSectionMapping.SECTIONS.items():
            for settings_key, widget_name in field_mappings:
                all_mappings[settings_key] = (section_key, widget_name)
        return all_mappings


class WidgetTypeIdentifiers:
    """Type identifiers for widget classification during settings sync."""

    # Widget type detection helpers
    @staticmethod
    def is_checkbox(widget_name: str) -> bool:
        """Check if widget is a checkbox by name pattern."""
        return widget_name.startswith('chk_')

    @staticmethod
    def is_label(widget_name: str) -> bool:
        """Check if widget is a display label (not editable)."""
        return widget_name.startswith('lbl_')

    @staticmethod
    def is_lineedit(widget_name: str) -> bool:
        """Check if widget is a line edit."""
        return widget_name.startswith('lne_')

    @staticmethod
    def is_datetimeedit(widget_name: str) -> bool:
        """Check if widget is a datetime picker."""
        return widget_name.startswith('dtp_')

    @staticmethod
    def is_combobox(widget_name: str) -> bool:
        """Check if widget is a combobox."""
        return widget_name.startswith('cmb_')
