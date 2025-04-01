import os
import subprocess
import sys
from pathlib import Path

import ops.file as file
import ops.logger as logger
import ops.setup as setup
import ops.vis as vis
from settings import version


class FluxRunEngine:

    def __init__(
            self,
            settings: dict):
        self.settings = settings

        self.logger = None

        self.update_settings()

    def update_settings(self):
        """Update automatically derived settings"""
        self.settings['_run_id'] = setup.generate_run_id()
        _script = os.path.abspath(__file__)  # Dir of this file
        self.settings['_dir_script'] = os.path.dirname(_script)
        self.settings['_dir_settings'] = \
            Path(os.path.join(self.settings['_dir_script'])) / 'settings'
        self.settings['_dir_fluxrun'] = Path(self.settings['_dir_script']).parents[0]
        self.settings['_dir_root'] = Path(self.settings['_dir_script']).parents[1]
        self.settings = setup.set_outdirs(settings_dict=self.settings)
        # Convert given parsing string to a string containing datetime characters that Python understands, e.g. %Y
        self.settings['_sitefiles_parse_str_python'] = self.make_datetime_parsing_string()
        setup.make_outdirs(settings_dict=self.settings)
        self.set_dir_eddypro_rawdata()

    def run(self):

        # Logger
        self.logger = logger.setup_logger(settings_dict=self.settings)
        self.logger.info(f"\n\nRun ID: {self.settings['_run_id']}")
        self.logger.info(f"fluxrun version: {version.__version__} / {version.__date__}\n\n")

        self.settings = file.PrepareEddyProFiles(settings_dict=self.settings, logger=self.logger).get()
        file.save_settings_to_file(settings_dict=self.settings, copy_to_outdir=True)

        # Search valid raw ASCII files, depending on settings
        self.rawdata_found_files_dict = file.SearchAll(
            settings_dict=self.settings,
            logger=self.logger,
            search_in_dir=self.settings['rawdata_indir']) \
            .keep_valid_files()

        if not self.rawdata_found_files_dict:
            self.logger.info("(!)ERROR No raw data files found. Please check settings.")
            sys.exit(-1)

        # Get raw data files for processing, uncompress if needed
        if self.settings['rawdata_file_compression'] == 'gzip':
            file.uncompress_gzip(settings_dict=self.settings,
                                 found_gzip_files_dict=self.rawdata_found_files_dict,
                                 logger=self.logger)
            # Files were uncompressed, search those files
            self.rawdata_found_files_dict = file.SearchAll(
                settings_dict=self.settings,
                logger=self.logger,
                search_in_dir=self.settings['_dir_used_rawdata_ascii_files_eddypro_data_path'],
                search_uncompressed=True) \
                .keep_valid_files()
        elif self.settings['rawdata_file_compression'] == 'None':
            # In this case files are already uncompressed
            pass
            # file.copy_rawdata_files(...)

        # Availability heatmap for *uncompressed* raw data files
        if self.settings['plot_availability_rawdata'] == '1':
            vis.availability_rawdata(rawdata_found_files_dict=self.rawdata_found_files_dict,
                                     rawdata_file_datefrmt=self.settings['_sitefiles_parse_str'].rstrip('.gz'),
                                     outdir=self.settings['_dir_out_run_plots_availability_rawdata'],
                                     logger=self.logger)

        # Plot stats for *uncompressed* raw data files
        if self.settings['plot_aggregates_rawdata'] == '1':
            vis.PlotRawDataFilesAggregates(
                rawdata_found_files_dict=self.rawdata_found_files_dict,
                settings_dict=self.settings,
                logger=self.logger,
                rawdata_file_datefrmt=self.settings['_sitefiles_parse_str'].rstrip('.gz'))

        # Call EddyPro processing
        rp_process_status = self.run_eddypro_cmd(cmd='eddypro_rp.exe')  # execute exe todo for linux and osx

        # Check if EddyPro full_output file was already generated
        found_full_output, _ = file.check_if_file_in_folder(search_str='*_full_output_*.csv',
                                                            folder=self.settings[
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
            file.check_if_file_in_folder(search_str='*_full_output_*.csv',
                                         folder=self.settings['_dir_out_run_eddypro_results'])
        if found_full_output and int(self.settings['plot_summary']) == 1:
            vis.PlotEddyProFullOutputFile(
                file_to_plot=filepath_full_output,
                destination_folder=self.settings['_dir_out_run_plots_summary'],
                logger=self.logger).run()
        else:
            self.logger.info("(!)WARNING No *_full_output_* file was found. Skipping summary plots.")

    def _delete_uncompressed_ascii_files(self):
        """Delete uncompressed (unzipped) ASCII files that were used for flux processing"""
        if int(self.settings['delete_uncompressed_ascii_after_processing']) == 1:
            uncompressed_ascii_files = file.SearchAll(
                settings_dict=self.settings,
                logger=self.logger,
                search_in_dir=self.settings['_dir_out_run_rawdata_ascii_files'],
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

        os.chdir(self.settings['_dir_out_run_eddypro_bin'])  # go to eddypro bin folder
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

    def make_datetime_parsing_string(self):
        """Parse filename for datetime info"""
        _parsing_string = self.settings['RAWDATA']['PARSING_STRING']
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
        if self.settings['RAWDATA']['COMPRESSION'] == 'gzip':
            self.settings['_dir_used_rawdata_ascii_files_eddypro_data_path'] = \
                self.settings['_dir_out_run_rawdata_ascii_files']

        elif self.settings['RAWDATA']['COMPRESSION'] == 'None':
            outpath = Path(self.settings['_dir_out_run_rawdata_ascii_files']) / 'readme.txt'
            readme_txt = open(str(outpath), "w+")
            readme_txt.write(f"This folder is empty because uncompressed ASCII raw data files from the "
                             f"following folder were used for flux calculations:\n\n"
                             f"{self.settings['rawdata_indir']}")
            self.settings['_dir_used_rawdata_ascii_files_eddypro_data_path'] = \
                self.settings['rawdata_indir']
