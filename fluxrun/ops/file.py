import datetime as dt
import fileinput
import fnmatch
import gzip
import os
import shutil
import sys
import time
from pathlib import Path
from shutil import copyfile

import numpy as np
import pandas as pd
import yaml


def check_if_file_in_folder(search_str: str, folder: str):
    """Check if filename exists in a folder"""
    file_is_in_folder = False
    filepath = None
    files_in_folder = os.listdir(folder)
    for found_file in files_in_folder:
        if fnmatch.fnmatch(found_file, search_str):
            file_is_in_folder = True
            filepath = Path(folder) / found_file
            break
    return file_is_in_folder, filepath


def uncompress_gz(settings_dict, found_gz_files_dict, logger):
    """Unzip compressed .gz files to output folder of current run"""
    for compr_filename, compr_filepath in found_gz_files_dict.items():
        try:
            compr_filepath = str(compr_filepath)
            uncompr_filename = Path(compr_filename).stem
            uncompr_filepath = Path(settings_dict['_dir_out_run_rawdata_ascii_files']) / uncompr_filename
            tic = time.time()
            with gzip.open(compr_filepath, 'rb') as f_in:
                logger.info(f"Trying to unzip file {compr_filepath} ...")
                with open(uncompr_filepath, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    time_needed = time.time() - tic
                    logger.info(f"[UNZIPPING GZ RAW DATA (ASCII) FILES] {compr_filepath} --> {uncompr_filepath} "
                                f"(done in {time_needed:.3f}s)")
        except Exception as e:
            logger.info("")
            logger.info(f"{'!'* 50}")
            logger.info(f"(!)WARNING for file {compr_filepath}")
            logger.info(f"(!)File skipped during uncompression.")
            logger.info(f"(!)Reason for skipping: {e}")
            logger.info(f"(!)File will not be used in processing.")
            logger.info(f"{'!'* 50}")
            logger.info("")


def copy_rawdata_files(settings_dict, found_csv_files_dict, logger):
    """Copy csv files to output folder of current run"""
    for filename, filepath in found_csv_files_dict.items():
        destination = Path(settings_dict['_dir_out_run_rawdata_ascii_files']) / filename
        shutil.copy(filepath, destination)
        logger.info(f"[GETTING CSV RAW DATA FILES] {filepath} --> {destination}")


class SearchAll:
    def __init__(self, logger, search_in_dir, settings, search_uncompressed=False):
        self.logger = logger
        self.valid_files_dict = {}
        self.search_in_dir = search_in_dir
        self.rawdata_start_date = settings['RAWDATA']['START_DATE']
        self.rawdata_end_date = settings['RAWDATA']['END_DATE']

        if search_uncompressed:
            self.site_parse_str_py = settings['_sitefiles_parse_str_python_uncompr']  # Parsing string in Python format
        else:
            self.site_parse_str_py = settings['_sitefiles_parse_str_python']  # Parsing string in Python format

    def keep_valid_files(self):
        """Search all files that can be parsed with the parsing string,
        but then keep only those that fulfil selected requirements."""

        # Search files for current site
        self.valid_files_dict = self.search_all(dir=self.search_in_dir,
                                                site_parse_str_py=self.site_parse_str_py,
                                                logger=self.logger)

        # Parse filedates and keep files in specified date range
        self.valid_files_dict = self.keep_files_within_timerange(site_parse_str_py=self.site_parse_str_py)
        return self.valid_files_dict

    def search_all(self, dir, site_parse_str_py, logger):
        """Search all files that can be parsed with the parsing string."""
        logger.info(f"Searching for files that fit the pattern {self.site_parse_str_py} ...")
        valid_files_dict = {}
        for root, dirs, found_files in os.walk(dir):
            for idx, file in enumerate(found_files):
                try:
                    rawdata_filedate = dt.datetime.strptime(file, self.site_parse_str_py)
                    filepath = Path(root) / file
                    valid_files_dict[file] = filepath
                except ValueError:
                    continue
        logger.info(f"Found {len(valid_files_dict)} files matching {site_parse_str_py} in {dir}")
        return valid_files_dict

    @staticmethod
    def make_parsing_string(settings_dict, file_ext):
        """Add site id and extension to parsing string"""
        parsing_string = f"{settings_dict['site']}_" \
                         f"{settings_dict['filename_datetime_parsing_string']}{file_ext}"
        return parsing_string

    def keep_files_within_timerange(self, site_parse_str_py):
        """Check if file date is within selected time range"""

        # site_parse_str = self.make_parsing_string(settings_dict=self.settings_dict)

        suffix = "[FILE TIME RANGE CHECK]"
        run_start_date = dt.datetime.strptime(self.rawdata_start_date, '%Y-%m-%d %H:%M')
        run_end_date = dt.datetime.strptime(self.rawdata_end_date, '%Y-%m-%d %H:%M')
        _invalid_files_dict = {}
        valid_files_dict = {}
        for filename, filepath in self.valid_files_dict.items():
            rawdata_filedate = dt.datetime.strptime(filename, site_parse_str_py)
            if (rawdata_filedate < run_start_date) | (rawdata_filedate > run_end_date):
                self.logger.info(
                    f"{suffix} Date of file ({filename}, date: {rawdata_filedate}) is outside the selected time range"
                    f" (between {run_start_date} and {run_end_date}), skipping file.")
                _invalid_files_dict[filename] = filepath
            else:
                self.logger.info(
                    f"{suffix} + Found file {filename} ({rawdata_filedate}), is within the selected time range"
                    f" (between {run_start_date} and {run_end_date}), keeping file.")
                valid_files_dict[filename] = filepath

        self.logger.info(f"{suffix} ============================")
        self.logger.info(f"{suffix} Results of time range check:")
        self.logger.info(f"{suffix} +++ {len(valid_files_dict)} files were within the selected time range between"
                         f" {run_start_date} and {run_end_date}, keeping files: {list(valid_files_dict.keys())}")
        self.logger.info(f"{suffix} --- {len(_invalid_files_dict)} files were outside the selected time range between"
                         f" {run_start_date} and {run_end_date} and will not be used: {list(_invalid_files_dict.keys())}")
        self.logger.info(f"{suffix} ============================")
        return valid_files_dict


class PrepareEddyProFiles:
    """Copy EddyPro *.processing and *.metadata file to run folder"""

    def __init__(self, logger, settings_dict):
        self.logger = logger
        self.settings_dict = settings_dict
        self.section_txt = "[EDDYPRO PROCESSING SETTINGS]"

        self.dir_out_run_eddypro_ini = Path(self.settings_dict['_dir_out_run_eddypro_ini'])
        self.dir_out_run_eddypro_bin = Path(self.settings_dict['_dir_out_run_eddypro_bin'])
        self.path_selected_processing_file = Path(settings_dict['FLUX_PROCESSING']['EDDYPRO_PROCESSING_FILE'])

        self.run()

    def get(self):
        return self.settings_dict

    def run(self):
        self.prepare_processing_file()
        self.prepare_metadata_file()
        self.update_processing_file()
        self.update_metadata_file()
        self.prepare_app()

    def update_metadata_file(self):
        """Update metadata settings"""

        section_id = '[UPDATING EDDYPRO METADATA FILE]'

        # fill in CORRECT PATHS
        # remove backslash of path because eddypro does not like it
        with open(self.settings_dict['_path_used_eddypro_metadata_file']) as input_file:
            for line in input_file:
                if line.startswith('file_name='):  # Output folder for EddyPro results
                    file_name_old = line

        file_name_new = f"file_name={Path(self.settings_dict['_path_used_eddypro_metadata_file'])}\n".replace('\\', '/')
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_metadata_file'],
                            old=file_name_old, new=file_name_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {file_name_old}"
                         f"    NEW:  {file_name_new}")

    def update_processing_file(self):
        """Update processing settings"""
        section_id = '[UPDATING EDDYPRO PROCESSING FILE]'

        self.logger.info(f"{section_id}  Updating file:  {self.settings_dict['_path_used_eddypro_processing_file']}")

        # fill in CORRECT PATHS in processing.eddypro
        # remove backslash of path w/ .replace because eddypro does not like it
        with open(self.settings_dict['_path_used_eddypro_processing_file']) as input_file:
            for line in input_file:
                if line.startswith('out_path='):  # Output folder for EddyPro results
                    out_path_old = line
                elif line.startswith('proj_file='):  # .metadata file
                    proj_file_old = line
                elif line.startswith('file_name='):  # processing.eddypro file
                    file_name_old = line
                elif line.startswith('data_path='):  # Folder w/ raw data ascii
                    data_path_old = line
                elif line.startswith('file_prototype='):  # For raw data file search
                    file_prototype_old = line
                elif line.startswith('project_id='):  # For raw data file search
                    project_id_old = line

        out_path_new = f"out_path={Path(self.settings_dict['_dir_out_run_eddypro_results'])}\n".replace('\\', '/')
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_processing_file'],
                            old=out_path_old, new=out_path_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {out_path_old}"
                         f"    NEW:  {out_path_new}")

        proj_file_new = f"proj_file={Path(self.settings_dict['_path_used_eddypro_metadata_file'])}\n".replace('\\', '/')
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_processing_file'],
                            old=proj_file_old, new=proj_file_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {proj_file_old}"
                         f"    NEW:  {proj_file_new}")

        file_name_new = f"file_name={Path(self.settings_dict['_path_used_eddypro_processing_file'])}\n".replace('\\',
                                                                                                                '/')
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_processing_file'],
                            old=file_name_old, new=file_name_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {file_name_old}"
                         f"    NEW:  {file_name_new}")

        data_path_new = f"data_path={Path(self.settings_dict['_dir_used_rawdata_ascii_files_eddypro_data_path'])}\n".replace(
            '\\', '/')
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_processing_file'],
                            old=data_path_old, new=data_path_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {data_path_old}"
                         f"    NEW:  {data_path_new}")

        # Remove .gzip file extension, EddyPro uses the unzipped files
        prototype_str = self.settings_dict['RAWDATA']['FILENAME_ID']
        file_ext = Path(self.settings_dict['RAWDATA']['FILENAME_ID']).suffix
        prototype_str = prototype_str.replace('.gz', '') if file_ext == '.gz' else prototype_str
        file_prototype_new = f"file_prototype={prototype_str}\n".replace('\\', '/')
        # file_prototype_new = f"file_prototype={prototype_str}\n".replace('\\', '/')
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_processing_file'],
                            old=file_prototype_old, new=file_prototype_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {file_prototype_old}"
                         f"    NEW:  {file_prototype_new}")

        project_id_new = f"project_id={self.settings_dict['OUTPUT']['OUTDIR_PREFIX']}_{Path(self.settings_dict['_run_id'])}\n"
        self.update_setting(filepath=self.settings_dict['_path_used_eddypro_processing_file'],
                            old=project_id_old, new=project_id_new)
        self.logger.info(f"{section_id}"
                         f"\n    Updated line:"
                         f"\n    OLD:  {project_id_old}"
                         f"    NEW:  {project_id_new}")

    def update_setting(self, filepath: str, old: str, new: str):
        for line in fileinput.input(filepath, inplace=True):
            print(line.replace(old, new), end='')

    def prepare_app(self):
        """Copy app files to run folder, e.g. Windows exe"""

        # Operating system
        dir_app = Path(self.settings_dict['_dir_script']) / 'eddypro_app'
        if os.name == 'nt':
            os_subdir = 'windows'
        else:
            self.logger(f"(!)ERROR Operating system {os.name} not implemented")
            sys.exit(-1)
        dir_app = dir_app / os_subdir

        # Copy all files to bin folder
        for root, dirs, found_files in os.walk(dir_app):
            for idx, file in enumerate(found_files):
                filepath = Path(root) / file
                shutil.copy(filepath, self.settings_dict['_dir_out_run_eddypro_bin'])

        # Set path to executables
        self.settings_dict['_path_used_eddypro_app_rp'] = \
            Path(self.settings_dict['_dir_out_run_eddypro_bin']) / 'eddypro_rp.exe'
        self.settings_dict['_path_used_eddypro_app_fcc'] = \
            Path(self.settings_dict['_dir_out_run_eddypro_bin']) / 'eddypro_fcc.exe'

        # Check if files available
        if not Path(self.settings_dict['_path_used_eddypro_app_rp']).is_file():
            self.logger.info(f"(!)ERROR eddypro_rp.exe was not found "
                             f"in folder {self.settings_dict['_dir_out_run_eddypro_bin']}")
            sys.exit(-1)

        if not Path(self.settings_dict['_path_used_eddypro_app_fcc']).is_file():
            self.logger.info(f"(!)ERROR eddypro_fcc was not found "
                             f"in folder {self.settings_dict['_dir_out_run_eddypro_bin']}")
            sys.exit(-1)

    def prepare_processing_file(self):
        """Copy processing file to run folder"""
        self.logger.info(f"{self.section_txt} [PROCESSING FILE] "
                         f"Selected file is {self.path_selected_processing_file}")
        path_used_processing_file = self.dir_out_run_eddypro_ini / 'processing.eddypro'  # Needs static name
        shutil.copy(self.path_selected_processing_file, path_used_processing_file)
        self.logger.info(f"{self.section_txt} [PROCESSING FILE] "
                         f"Copied file to {path_used_processing_file} ...")
        self.logger.info(f"{self.section_txt} [PROCESSING FILE] "
                         f"Used in this run: {path_used_processing_file} ...")
        self.settings_dict['_path_used_eddypro_processing_file'] = path_used_processing_file
        self.settings_dict['_path_found_eddypro_metadata_file'] = self.path_selected_processing_file

    def prepare_metadata_file(self):
        """Search metadata file and copy to run folder"""
        path_found_metadata_file, required_metadata_filename = self.search_required_metadata_file()

        if path_found_metadata_file:
            # Copy to run folder
            self.logger.info(f"{self.section_txt} [METADATA FILE] Found {path_found_metadata_file}")
            path_used_metadata_file = self.dir_out_run_eddypro_ini / path_found_metadata_file.name
            shutil.copy(path_found_metadata_file, path_used_metadata_file)
            self.logger.info(f"{self.section_txt} [METADATA FILE] Copied file to {path_used_metadata_file}")
            self.logger.info(f"{self.section_txt} [METADATA FILE] Used in this run: {path_used_metadata_file}")
            self.settings_dict['_path_used_eddypro_metadata_file'] = path_used_metadata_file

        else:
            self.logger.info(f"{self.section_txt} [METADATA FILE] "
                             f"(!)ERROR: No *.metadata file with name {required_metadata_filename} was found.")
            self.logger.info(f"{self.section_txt} [METADATA FILE] "
                             f"(!)ERROR: Stopping fluxrun.")
            sys.exit()

    def search_required_metadata_file(self):
        """
        Search for metadata file in same dir (same location, no subdirs considered)
        as the selected processing file
        """
        dir_selected_eddypro_processing_file = self.path_selected_processing_file.parent
        required_metadata_filename = self.path_selected_processing_file.stem + ".metadata"
        path_found_metadata_file = None

        self.logger.info(f"{self.section_txt} [METADATA FILE] "
                         f"Searching for file {required_metadata_filename} "
                         f"in {dir_selected_eddypro_processing_file} ...")

        for found_file in os.listdir(dir_selected_eddypro_processing_file):
            if found_file == required_metadata_filename:
                path_found_metadata_file = Path(dir_selected_eddypro_processing_file) / found_file
                break

        return path_found_metadata_file, required_metadata_filename


class ReadEddyProFullOutputFile:
    DATA_SKIP_ROWS = [0]
    DATA_HEADER_ROWS = [0, 1]
    DATA_HEADER_SECTION_ROWS = [0, 1, 2]
    DATA_NA_VALUES = -9999
    DATA_DELIMITER = ','
    TIMESTAMP_INDEX_COLUMN = [('date', '[yyyy-mm-dd]'), ('time', '[HH:MM]')]
    TIMESTAMP_DATETIME_FORMAT = '%Y-%m-%d %H:%M'
    TIMESTAMP_SHOWS_START_MIDDLE_OR_END_OF_RECORD = 'end'

    TIMESTAMP_OUT_NAME = ('TIMESTAMP', '[yyyy-mm-dd HH:MM:SS]')
    PARSED_INDEX_COL = ('index', '[parsed]')

    def __init__(self, filepath):
        self.filepath = filepath
        self.data_df = pd.DataFrame()
        self.run()

    def run(self):
        # Check header vs data
        more_data_cols_than_header_cols, num_missing_header_cols, \
            header_cols_list, generated_missing_header_cols_list = \
            self.compare_len_header_vs_data(filepath=self.filepath,
                                            skip_rows_list=self.DATA_SKIP_ROWS,
                                            header_rows_list=self.DATA_HEADER_ROWS)

        # Read data file
        parse_dates, date_parser = self.dateparser_settings()
        self.data_df = self.read_file(header_cols_list=header_cols_list,
                                      parse_dates=parse_dates,
                                      date_parser=date_parser)

        self.data_df = self.sanitize(df=self.data_df)
        self.data_df = self.standardize_index(df=self.data_df)

    def get(self):
        return self.data_df

    def sanitize(self, df):
        # There exist certain instances where the float64 data column can contain
        # non-numeric values that are interpreted as a float64 inf, which is basically
        # a NaN value. To harmonize missing values inf is also set to NaN.
        df = df.replace(float('inf'), np.nan)
        df = df.replace(float('-inf'), np.nan)
        return df

    def standardize_index(self, df):
        # Index name is now the same for all filetypes w/ timestamp in data
        df.set_index([self.PARSED_INDEX_COL], inplace=True)
        df.index.name = self.TIMESTAMP_OUT_NAME
        # Make sure the index is datetime
        df.index = pd.to_datetime(df.index)
        return df

    def read_file(self, header_cols_list, parse_dates, date_parser):
        data_df = pd.read_csv(self.filepath,
                              skiprows=self.DATA_HEADER_SECTION_ROWS,
                              header=None,
                              names=header_cols_list,
                              na_values=self.DATA_NA_VALUES,
                              encoding='utf-8',
                              delimiter=self.DATA_DELIMITER,
                              # mangle_dupe_cols=True,
                              keep_date_col=False,
                              parse_dates=parse_dates,
                              date_parser=date_parser,
                              index_col=None,
                              dtype=None,
                              skip_blank_lines=True,
                              engine='python')
        return data_df

    def dateparser_settings(self):
        """Column settings for parsing dates / times correctly"""
        parsed_index_col = self.PARSED_INDEX_COL
        parse_dates = self.TIMESTAMP_INDEX_COLUMN
        parse_dates = {parsed_index_col: parse_dates}
        date_parser = lambda x: dt.datetime.strptime(x, self.TIMESTAMP_DATETIME_FORMAT)
        return parse_dates, date_parser

    def compare_len_header_vs_data(self, filepath, skip_rows_list, header_rows_list):
        """
        Check whether there are more data columns than given in the header.

        If not checked, this would results in an error when reading the csv file
        with .read_csv, because the method expects an equal number of header and
        data columns. If this check is True, then the difference between the length
        of the first data row and the length of the header row(s) can be used to
        automatically generate names for the missing header columns.
        """
        # Check number of columns of the first data row after the header part
        skip_num_lines = len(header_rows_list) + len(skip_rows_list)
        first_data_row_df = pd.read_csv(filepath, skiprows=skip_num_lines,
                                        header=None, nrows=1)
        len_data_cols = first_data_row_df.columns.size

        # Check number of columns of the header part
        header_cols_df = pd.read_csv(filepath, skiprows=skip_rows_list,
                                     header=header_rows_list, nrows=0)
        len_header_cols = header_cols_df.columns.size

        # Check if there are more data columns than header columns
        if len_data_cols > len_header_cols:
            more_data_cols_than_header_cols = True
            num_missing_header_cols = len_data_cols - len_header_cols
        else:
            more_data_cols_than_header_cols = False
            num_missing_header_cols = 0

        # Generate missing header columns if necessary
        header_cols_list = header_cols_df.columns.to_list()
        generated_missing_header_cols_list = []
        sfx = self.make_timestamp_microsec_suffix()
        if more_data_cols_than_header_cols:
            for m in list(range(1, num_missing_header_cols + 1)):
                missing_col = (f'unknown_{m}-{sfx}', '[-unknown-]')
                generated_missing_header_cols_list.append(missing_col)
                header_cols_list.append(missing_col)

        return more_data_cols_than_header_cols, num_missing_header_cols, \
            header_cols_list, generated_missing_header_cols_list

    def make_timestamp_microsec_suffix(self):
        now_time_dt = dt.datetime.now()
        now_time_str = now_time_dt.strftime("%H%M%S%f")
        run_id = f'{now_time_str}'
        return run_id


def save_settings_to_file(filepath_settings: Path, settings: dict, copy_to_outdir: bool = False):
    """Save settings from the GUI to settings file."""
    essential_settings = {key: value for key, value in settings.items() if not key.startswith('_')}
    with open(filepath_settings, "w") as f:
        cfg = yaml.dump(essential_settings, stream=f, default_flow_style=False, sort_keys=False)
    if copy_to_outdir:
        # Save a copy of the settings file also in the output dir
        run_settings_file_path = Path(settings['_dir_out_run']) / 'fluxrunsettings.yaml'
        copyfile(filepath_settings, run_settings_file_path)

# def save_settings_to_file(settings_dict: dict, copy_to_outdir=False):
#     """Save settings dict to settings file """
#
#     # for key, val in settings_dict.items():
#     #     print(key, val)
#
#     with open("config.yaml", "w") as f:
#         cfg = yaml.dump(
#             cfg, stream=f, default_flow_style=False, sort_keys=False
#         )
#
#     print(yaml.dump(settings_dict, default_flow_style=True))
#
#     old_settings_file = os.path.join(settings_dict['_dir_settings'], 'FluxRun.settings')
#     new_settings_file = os.path.join(settings_dict['_dir_settings'], 'FluxRun.settingsTemp')
#     with open(old_settings_file) as infile, open(new_settings_file, 'w') as outfile:
#         for line in infile:  # cycle through all lines in settings file
#             if ('=' in line) and (not line.startswith('#')):  # identify lines that contain setting
#                 line_id, line_setting = line.strip().split('=')
#                 line = '{}={}\n'.format(line_id, settings_dict[line_id])  # insert setting from dict
#             outfile.write(line)
#     try:
#         os.remove(old_settings_file + 'Old')
#     except:
#         pass
#     os.rename(old_settings_file, old_settings_file + 'Old')
#     os.rename(new_settings_file, old_settings_file)
#
#     if copy_to_outdir:
#         # Save a copy of the settings file also in the output dir
#         run_settings_file_path = Path(settings_dict['_dir_out_run']) / 'FluxRun.settings'
#         copyfile(old_settings_file, run_settings_file_path)
#         pass
#
#     # return settings_dict
