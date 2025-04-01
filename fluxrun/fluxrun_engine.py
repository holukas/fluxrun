import os
from pathlib import Path
import ops.setup

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
        # Convert given parsing string to a string containing datetime characters that Python understands, e.g. %Y
        self.settings_dict['_sitefiles_parse_str_python'] = self.make_datetime_parsing_string()
        make_outdirs(settings_dict=self.settings_dict)
        self.set_dir_eddypro_rawdata()

    def run(self):

        # Logger
        self.logger = ops.logger.setup_logger(settings_dict=self.settings_dict)
        self.logger.info(f"\n\nRun ID: {self.settings_dict['_run_id']}")
        self.logger.info(f"FluxRun Version: {_version.__version__} / {_version.__date__}\n\n")

        self.settings_dict = ops.file.PrepareEddyProFiles(settings_dict=self.settings_dict, logger=self.logger).get()
        ops.file.set.save_settings_to_file(settings_dict=self.settings_dict, copy_to_outdir=True)

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

    def make_datetime_parsing_string(self):
        """Parse filename for datetime info"""
        _parsing_string = self.settings_dict['sitefiles_parse_str']
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