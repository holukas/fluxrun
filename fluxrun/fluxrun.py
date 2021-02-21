import os
import subprocess
import sys
from pathlib import Path
from shutil import copyfile

from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from PyQt5 import QtWidgets as qtw

import ops.logger
import ops.setup
from gui.gui import Ui_MainWindow
from ops import vis, file
from settings import _version


# TODO displacement height file?

# TODO LATER parallelize, multiprocessing?
# import multiprocessing as mp
# print("Number of processors: ", mp.cpu_count())


class FluxRun(qtw.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(FluxRun, self).__init__(parent)
        self.setupUi(self)

        self.run_id = ops.setup.generate_run_id()

        # Detect Folders
        dir_script = os.path.abspath(__file__)  # Dir of this file
        dir_settings = Path(
            os.path.join(os.path.dirname(dir_script))) / 'settings'  # Preload settings dir to load settings file

        # Read Settings: File --> Dict
        self.settings_dict = \
            ops.setup.read_settings_file_to_dict(dir_settings=dir_settings,
                                                 file='FluxRun.settings',
                                                 reset_paths=False)

        # Update dir settings in dict, for current run
        self.update_dict_dir_settings(dir_script=dir_script, dir_settings=dir_settings)

        # Fill-In Settings: Dict --> GUI
        self.show_settings_in_gui()

        # Connect GUI elements
        self.connections()

    def run(self):

        # Outdirs and logger
        self.settings_dict = ops.setup.make_run_outdirs(settings_dict=self.settings_dict)
        self.logger = ops.logger.setup_logger(settings_dict=self.settings_dict)
        self.logger.info(f"Run ID: {self.run_id}")
        self.logger.info(f"FluxRun Version: {_version.__version__} / {_version.__date__}")

        # Settings
        self.get_settings_from_gui()
        self.set_dir_eddypro_rawdata()
        self.settings_dict = file.PrepareEddyProFiles(settings_dict=self.settings_dict,
                                                      logger=self.logger).get()
        self.save_settings_to_file(copy_to_outdir=True)

        # # todo act test
        # vis.PlotEddyProFullOutputFile(
        #     file_to_plot=r"C:\Users\holukas\Desktop\eddypro_CH-AES_FR-20210216-150657_full_output_2021-02-17T212711_adv.csv",
        #     destination_folder=r"C:\Users\holukas\Desktop\_test",
        #     logger=self.logger).run()

        # Search valid raw ASCII files, depending on settings
        self.settings_dict['filename_datetime_parsing_string'] = self.make_datetime_parsing_string()
        self.rawdata_found_files_dict = file.SearchAll(settings_dict=self.settings_dict,
                                                       logger=self.logger).keep_valid_files()

        if not self.rawdata_found_files_dict:
            self.logger.info("(!)ERROR No raw data files found. Please check settings.")
            sys.exit(-1)

        # Availability heatmap for raw data files
        if self.settings_dict['plot_availability_rawdata'] == '1':
            parsing_string = file.SearchAll.make_parsing_string(settings_dict=self.settings_dict)
            vis.availability_rawdata(rawdata_found_files_dict=self.rawdata_found_files_dict,
                                     rawdata_file_datefrmt=parsing_string,
                                     outdir=self.settings_dict['dir_out_run_plots_availability_rawdata'],
                                     logger=self.logger)

        # Plot stats collection from file
        if self.settings_dict['plot_aggregates_rawdata'] == '1':
            vis.PlotRawDataFilesAggregates(rawdata_found_files_dict=self.rawdata_found_files_dict,
                                           settings_dict=self.settings_dict,
                                           logger=self.logger)

        # Get raw data files for processing, uncompress
        if self.settings_dict['rawdata_file_compression'] == 'gzip':
            file.uncompress_gzip(settings_dict=self.settings_dict,
                                 found_gzip_files_dict=self.rawdata_found_files_dict,
                                 logger=self.logger)
        elif self.settings_dict['rawdata_file_compression'] == 'None':
            pass
            # file.copy_rawdata_files(settings_dict=self.settings_dict,
            #                         found_csv_files_dict=self.rawdata_found_files_dict,
            #                         logger=self.logger)

        # Call EddyPro processing
        rp_process_status = self.run_eddypro_cmd(cmd='eddypro_rp.exe')  # execute exe todo for linux and osx

        # Check if EddyPro full_output file was already generated
        found_full_output, _ = file.check_if_file_in_folder(search_str='*_full_output_*.csv',
                                                            folder=self.settings_dict['dir_out_run_eddypro_results'])
        if found_full_output:
            self.logger.info("(!)WARNING EddyPro RP already generated a full_output file. FCC will be skipped. "
                             "This is not necessarily bad.")

        if rp_process_status == 0 and found_full_output == False:
            fcc_process_status = self.run_eddypro_cmd(cmd='eddypro_fcc.exe')  # execute exe todo for linux and osx

        # Plot summary
        found_full_output, filepath_full_output = \
            file.check_if_file_in_folder(search_str='*_full_output_*.csv',
                                         folder=self.settings_dict['dir_out_run_eddypro_results'])
        if found_full_output and int(self.settings_dict['plot_summary']) == 1:
            vis.PlotEddyProFullOutputFile(
                file_to_plot=filepath_full_output,
                destination_folder=self.settings_dict['dir_out_run_plots_summary'],
                logger=self.logger).run()

        else:
            self.logger.info("(!)WARNING No *_full_output_* file was found. Skipping summary plots.")

        self.logger.info("\n\n\n")
        self.logger.info("=" * 60)
        self.logger.info("FluxRun finished.")
        self.logger.info("=" * 60)

    def set_dir_eddypro_rawdata(self):
        """
        Set raw data folder for EddyPro flux calculations

        Compressed files will be uncompressed and saved to the current run output folder.
        Uncompressed files will be directly used from where they are stored.
        """
        if self.settings_dict['rawdata_file_compression'] == 'gzip':
            self.settings_dict['dir_used_rawdata_ascii_files_eddypro_data_path'] = \
                self.settings_dict['dir_out_run_rawdata_ascii_files']

        elif self.settings_dict['rawdata_file_compression'] == 'None':
            outpath = Path(self.settings_dict['dir_out_run_rawdata_ascii_files']) / 'readme.txt'
            readme_txt = open(str(outpath), "w+")
            readme_txt.write(f"This folder is empty because uncompressed ASCII raw data files from the "
                             f"following folder were used for flux calculations:\n\n"
                             f"{self.settings_dict['rawdata_indir']}")
            self.settings_dict['dir_used_rawdata_ascii_files_eddypro_data_path'] = \
                self.settings_dict['rawdata_indir']

    def run_eddypro_cmd(self, cmd: str):
        """Run eddypro_rp.exe or eddypro_fcc.exe"""

        os.chdir(self.settings_dict['dir_out_run_eddypro_bin'])  # go to eddypro bin folder
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
        _parsing_string = self.settings_dict['filename_datetime_format']
        _parsing_string = _parsing_string.replace('yyyy', '%Y')
        _parsing_string = _parsing_string.replace('mm', '%m')
        _parsing_string = _parsing_string.replace('dd', '%d')
        _parsing_string = _parsing_string.replace('HH', '%H')
        _parsing_string = _parsing_string.replace('MM', '%M')
        # _parsing_string = f"{self.settings_dict['site']}_{_parsing_string}"  # Add site id
        return _parsing_string

    def update_dict_key(self, key, new_val):
        """ Updates key in Dict with new_val """
        self.settings_dict[key] = new_val
        ('{}: {}'.format(key, self.settings_dict[key]))

    def get_settings_from_gui(self):
        """Read settings from GUI and store in dict"""
        # Instruments
        self.update_dict_key(key='site', new_val=self.cmb_instr_site_selection.currentText())
        # self.update_dict_key(key='header', new_val=self.cmb_instr_header.currentText())

        # Processing
        self.update_dict_key(key='rawdata_indir', new_val=self.lbl_proc_rawdata_source_dir_selected.text())
        self.update_dict_key(key='rawdata_start_date',
                             new_val=self.dtp_processing_time_range_start.dateTime().toString('yyyy-MM-dd hh:mm'))
        self.update_dict_key(key='rawdata_end_date',
                             new_val=self.dtp_processing_time_range_end.dateTime().toString('yyyy-MM-dd hh:mm'))
        self.update_dict_key(key='filename_datetime_format',
                             new_val=self.lne_proc_filedt_format.text())
        self.update_dict_key(key='rawdata_file_compression', new_val=self.cmb_proc_rawdata_compr.currentText())
        self.update_dict_key(key='path_selected_eddypro_processing_file',
                             new_val=self.lbl_proc_ep_procfile_selected.text())

        # Output
        self.update_dict_key(key='dir_out', new_val=self.lbl_output_folder.text())

        self.update_dict_key(key='plot_availability_rawdata',
                             new_val='1' if self.chk_output_plots_availability_rawdata.isChecked() else '0')
        self.update_dict_key(key='plot_aggregates_rawdata',
                             new_val='1' if self.chk_output_plots_aggregates_rawdata.isChecked() else '0')
        self.update_dict_key(key='plot_summary',
                             new_val='1' if self.chk_output_plots_summary.isChecked() else '0')

    def update_dict_dir_settings(self, dir_script, dir_settings):
        """Update dir info for current run"""
        self.settings_dict['run_id'] = self.run_id
        self.settings_dict['dir_script'] = os.path.join(os.path.dirname(dir_script))
        self.settings_dict['dir_settings'] = dir_settings
        self.settings_dict['dir_fluxrun'] = Path(self.settings_dict['dir_script']).parents[0]
        self.settings_dict['dir_root'] = Path(self.settings_dict['dir_script']).parents[1]

        # Update dirs that can be changed in the gui
        self.settings_dict['rawdata_indir'] = \
            self.dir_fluxrun if not self.settings_dict['rawdata_indir'] else self.settings_dict['rawdata_indir']
        self.settings_dict['dir_out'] = \
            self.dir_fluxrun if not self.settings_dict['dir_out'] else self.settings_dict['dir_out']

    def set_gui_combobox(self, combobox, find_text):
        idx = combobox.findText(find_text, qtc.Qt.MatchContains)
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
        self.set_gui_combobox(combobox=self.cmb_instr_site_selection, find_text=self.settings_dict['site'])
        # self.set_gui_combobox(combobox=self.cmb_instr_header, find_text=self.settings_dict['header'])

        # Processing
        self.lbl_proc_rawdata_source_dir_selected.setText(str(self.settings_dict['rawdata_indir']))
        self.set_gui_datetimepicker(datetimepicker=self.dtp_processing_time_range_start,
                                    date_str=self.settings_dict['rawdata_start_date'])
        self.set_gui_datetimepicker(datetimepicker=self.dtp_processing_time_range_end,
                                    date_str=self.settings_dict['rawdata_end_date'])
        self.set_gui_lineedit(lineedit=self.lne_proc_filedt_format,
                              string=self.settings_dict['rawdata_filename_datetime_format'])
        self.set_gui_combobox(combobox=self.cmb_proc_rawdata_compr,
                              find_text=self.settings_dict['rawdata_file_compression'])
        self.lbl_proc_ep_procfile_selected.setText(str(self.settings_dict['path_selected_eddypro_processing_file']))

        # Output
        self.lbl_output_folder.setText(str(self.settings_dict['dir_out']))

        self.set_gui_checkbox(checkbox=self.chk_output_plots_availability_rawdata,
                              state=self.settings_dict['plot_availability_rawdata'])
        self.set_gui_checkbox(checkbox=self.chk_output_plots_aggregates_rawdata,
                              state=self.settings_dict['plot_aggregates_rawdata'])
        self.set_gui_checkbox(checkbox=self.chk_output_plots_summary,
                              state=self.settings_dict['plot_summary'])

    def link(self, link_str):
        """Call hyperlink from label, opens in browser"""
        qtg.QDesktopServices.openUrl(qtc.QUrl(link_str))

    def connections(self):
        """Connect GUI elements to functions"""
        # Logo
        self.lbl_link_releases.linkActivated.connect(self.link)
        self.lbl_link_source_code.linkActivated.connect(self.link)
        self.lbl_link_license.linkActivated.connect(self.link)
        self.lbl_link_help.linkActivated.connect(self.link)

        # Processing
        self.btn_proc_rawdata_source_dir.clicked.connect(lambda: self.select_dir(
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
        self.btn_ctr_save.clicked.connect(lambda: self.save_settings())
        self.btn_ctr_run.clicked.connect(lambda: self.run())

    def save_settings(self):
        """Get selected settings from GUI elements, store in dict and save to file"""
        self.get_settings_from_gui()
        self.save_settings_to_file()

    def save_settings_to_file(self, copy_to_outdir=False):
        """Save settings dict to settings file """
        old_settings_file = os.path.join(self.settings_dict['dir_settings'], 'FluxRun.settings')
        new_settings_file = os.path.join(self.settings_dict['dir_settings'], 'FluxRun.settingsTemp')
        with open(old_settings_file) as infile, open(new_settings_file, 'w') as outfile:
            for line in infile:  # cycle through all lines in settings file
                if ('=' in line) and (not line.startswith('#')):  # identify lines that contain setting
                    line_id, line_setting = line.strip().split('=')
                    line = '{}={}\n'.format(line_id, self.settings_dict[line_id])  # insert setting from dict
                outfile.write(line)
        try:
            os.remove(old_settings_file + 'Old')
        except:
            pass
        os.rename(old_settings_file, old_settings_file + 'Old')
        os.rename(new_settings_file, old_settings_file)

        if copy_to_outdir:
            # Save a copy of the settings file also in the output dir
            run_settings_file_path = Path(self.settings_dict['dir_out_run']) / 'FluxRun.settings'
            copyfile(old_settings_file, run_settings_file_path)
            pass

        # return settings_dict

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


def main():
    app = qtw.QApplication(sys.argv)
    fluxrun = FluxRun()
    fluxrun.show()
    app.exec_()


if __name__ == '__main__':
    main()
