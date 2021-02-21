import os
import time
from pathlib import Path


def read_settings_file_to_dict(dir_settings, file, reset_paths):
    """Read start values from settings file as strings into dict, with same variable names as in file"""

    settings_dict = {}
    settings_file_fullpath = os.path.join(dir_settings, file)

    with open(settings_file_fullpath) as input_file:
        for line in input_file:  # cycle through all lines in settings file
            if ('=' in line) and (not line.startswith('#')):  # identify lines that contain setting
                line_id, line_setting = line.strip().split('=')

                # reset all file paths, folder paths and instr info, will be filled during run
                if reset_paths:
                    if line_id.startswith('f_') or line_id.startswith('dir_') or line_id.startswith('instr_'):
                        line_setting = ''

                settings_dict[line_id] = line_setting  # store setting from file in dict

    return settings_dict


def make_run_outdirs(settings_dict):
    """Set output paths and create output folders"""

    # Run output folder
    # settings_dict['dir_out_run'] = Path(settings_dict['dir_out']) / "FLUXRUN_TEST_OUT"
    _dirname = f"{settings_dict['site']}_{settings_dict['run_id']}"
    settings_dict['dir_out_run'] = Path(settings_dict['dir_out']) / _dirname  # todo act
    if not Path.is_dir(settings_dict['dir_out_run']):
        print(f"Creating folder {settings_dict['dir_out_run']} ...")
        os.makedirs(settings_dict['dir_out_run'])

    # Logfile
    settings_dict['dir_out_run_log'] = settings_dict['dir_out_run'] / '0_log'

    # # Plots general
    # settings_dict['dir_out_run_plots'] = settings_dict['dir_out_run'] / 'plots'

    # Raw data files
    settings_dict['dir_out_run_rawdata_ascii_files'] = \
        settings_dict['dir_out_run'] / '1-0_rawdata_files_ascii'
    settings_dict['dir_out_run_plots_availability_rawdata'] = \
        settings_dict['dir_out_run'] / '1-1_rawdata_plots_availability'
    settings_dict['dir_out_run_plots_aggregates_rawdata'] = \
        settings_dict['dir_out_run'] / '1-2_rawdata_plots_aggregates'

    # EddyPro
    settings_dict['dir_out_run_eddypro'] = settings_dict['dir_out_run'] / '2-0_eddypro_flux_calculations'
    settings_dict['dir_out_run_eddypro_ini'] = settings_dict['dir_out_run_eddypro'] / 'ini'
    settings_dict['dir_out_run_eddypro_bin'] = settings_dict['dir_out_run_eddypro'] / 'bin'
    settings_dict['dir_out_run_eddypro_results'] = settings_dict['dir_out_run_eddypro'] / 'results'
    settings_dict['dir_out_run_plots_summary'] = \
        settings_dict['dir_out_run'] / '2-1_eddypro_flux_calculations_summary_plots'

    # Make dirs
    create_dirs = ['dir_out_run_log',
                   'dir_out_run_rawdata_ascii_files', 'dir_out_run_plots_availability_rawdata',
                   'dir_out_run_plots_aggregates_rawdata',
                   'dir_out_run_eddypro', 'dir_out_run_eddypro_bin', 'dir_out_run_eddypro_ini',
                   'dir_out_run_eddypro_results', 'dir_out_run_plots_summary']
    for d in create_dirs:
        if not Path.is_dir(settings_dict[d]):
            print(f"Creating folder {settings_dict[d]} ...")
            os.makedirs(settings_dict[d])

    return settings_dict


def generate_run_id():
    """Generate unique id for this run"""
    # script_start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    run_id = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"FR-{run_id}"
    return run_id
