import os
import time
from pathlib import Path

import yaml


def read_settings_file(filepath_settings):
    """Read start values from settings file as strings into dict, with same variable names as in file"""
    with open(filepath_settings, 'r', encoding='utf-8') as f:
        settings_dict = yaml.safe_load(f)
    return settings_dict


def set_outdirs(settings_dict: dict) -> dict:
    """Set paths for output files"""

    # Output folder
    _dirname = f"{settings_dict['OUTPUT']['OUTDIR_PREFIX']}_{settings_dict['_run_id']}"
    settings_dict['_dir_out_run'] = \
        Path(settings_dict['OUTPUT']['OUTDIR']) / _dirname

    # Logfile
    settings_dict['_dir_out_run_log'] = \
        settings_dict['_dir_out_run'] / '0_log'

    # Raw data files
    settings_dict['_dir_out_run_rawdata_ascii_files'] = \
        settings_dict['_dir_out_run'] / '1-0_rawdata_files_ascii'
    settings_dict['_dir_out_run_plots_availability_rawdata'] = \
        settings_dict['_dir_out_run'] / '1-1_rawdata_plots_availability'
    settings_dict['_dir_out_run_plots_aggregates_rawdata'] = \
        settings_dict['_dir_out_run'] / '1-2_rawdata_plots_aggregates'

    # EddyPro
    settings_dict['_dir_out_run_eddypro'] = \
        settings_dict['_dir_out_run'] / '2-0_eddypro_flux_calculations'
    settings_dict['_dir_out_run_eddypro_ini'] = \
        settings_dict['_dir_out_run_eddypro'] / 'ini'
    settings_dict['_dir_out_run_eddypro_bin'] = \
        settings_dict['_dir_out_run_eddypro'] / 'bin'
    settings_dict['_dir_out_run_eddypro_results'] = \
        settings_dict['_dir_out_run_eddypro'] / 'results'
    settings_dict['_dir_out_run_plots_summary'] = \
        settings_dict['_dir_out_run'] / '2-1_eddypro_flux_calculations_summary_plots'

    return settings_dict


def make_outdirs(settings_dict):
    """Create output folders"""

    # Create general run output folder that contains all other folders
    _dir_out_run = Path(settings_dict['_dir_out_run'])
    if not Path.is_dir(_dir_out_run):
        print(f"Creating folder {_dir_out_run} ...")
        os.makedirs(_dir_out_run)

    # Make subfolders
    for key, val in settings_dict.items():
        if str(key).startswith('_dir_out_'):
            if not Path.is_dir(settings_dict[key]):
                print(f"Creating folder {settings_dict[key]} ...")
                os.makedirs(settings_dict[key])

    return settings_dict


def generate_run_id():
    """Generate unique id for this run"""
    # script_start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"FR-{run_id}"
    return run_id
