import os
import time
from pathlib import Path

import yaml


def read_settings_file_to_dict(dir_settings, file, reset_paths):
    """Read start values from settings file as strings into dict, with same variable names as in file"""

    settings_file_fullpath = os.path.join(dir_settings, file)
    with open(settings_file_fullpath, 'r', encoding='utf-8') as f:
        settings_dict = yaml.safe_load(f)

    # settings_dict = {}
    # settings_file_fullpath = os.path.join(dir_settings, file)
    #
    # with open(settings_file_fullpath) as input_file:
    #     for line in input_file:  # cycle through all lines in settings file
    #         if ('=' in line) and (not line.startswith('#')):  # identify lines that contain setting
    #             line_id, line_setting = line.strip().split('=')
    #
    #             # reset all file paths, folder paths and instr info, will be filled during run
    #             if reset_paths:
    #                 if line_id.startswith('f_') or line_id.startswith('dir_') or line_id.startswith('instr_'):
    #                     line_setting = ''
    #
    #             settings_dict[line_id] = line_setting  # store setting from file in dict

    return settings_dict


def set_outdirs(settings_dict: dict) -> dict:
    """Set paths for output files"""

    # Output folder
    _dirname = f"{settings_dict['site']}_{settings_dict['_run_id']}"
    settings_dict['_dir_out_run'] = \
        Path(settings_dict['dir_out']) / _dirname

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
    if not Path.is_dir(settings_dict['_dir_out_run']):
        print(f"Creating folder {settings_dict['_dir_out_run']} ...")
        os.makedirs(settings_dict['_dir_out_run'])

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
