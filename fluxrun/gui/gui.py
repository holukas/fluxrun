# -*- coding: utf-8 -*-
import sys

from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg
from PyQt6 import QtWidgets as qtw
from PyQt6.QtGui import QPixmap

import settings._version as info
from gui import gui_elements
# import gui_elements
from help import tooltips


class Ui_MainWindow(object):
    """
        Prepares the raw GUI, i.e. the canvas that is filled with content later.
    """

    def setupUi(self, mainwindow):
        # Main window
        mainwindow.setWindowTitle(f"FluxRun")
        mainwindow.setWindowIcon(qtg.QIcon('images/logo_FLUXRUN1.png'))
        # mainwindow.resize(250, 150)

        # # todo Center mainwindow on screen
        # qr = mainwindow.frameGeometry()  # geometry of the main window, yields: int x, int y, int width, int height
        # cp = qtw.QDesktopWidget().availableGeometry().center()  # center point of screen
        # qr.moveCenter(cp)  # move rectangle's center point to screen's center point
        # mainwindow.move(qr.topLeft())  # top left of rectangle becomes top left of window centering it
        # print(qr)
        mainwindow.move(100, 100)

        # mainwindow.resize(600, 800)
        centralwidget = qtw.QWidget(mainwindow)
        centralwidget.setObjectName("centralwidget")
        centralwidget.setAccessibleName('mainwindow')
        mainwindow.setCentralWidget(centralwidget)

        # Statusbar
        self.statusbar = qtw.QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.showMessage('No processing running.')
        mainwindow.setStatusBar(self.statusbar)

        # CSS
        with open('gui/gui.css', "r") as fh:
            mainwindow.setStyleSheet(fh.read())

        # ADD SECTIONS to LAYOUT CONTAINER
        container = qtw.QHBoxLayout()
        container.addWidget(self.add_section_logo())
        container.addWidget(self.add_section_instruments())
        container.addWidget(self.add_section_processing())
        container.addWidget(self.add_section_output())
        # container.addWidget(self.add_section_flux_processing())
        container.addWidget(self.add_section_controls())
        container.setContentsMargins(0, 0, 0, 0)
        centralwidget.setLayout(container)

    def add_section_logo(self):
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_output')
        grid = qtw.QGridLayout()
        label_image = qtw.QLabel()
        label_image.setPixmap(QPixmap('images/logo_FLUXRUN1_256px.png'))

        label_txt = qtw.QLabel("FluxRun")
        label_txt.setProperty('labelClass', 'header_3')
        label_txt.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)

        label_txt2 = qtw.QLabel("Wrapper for EddyPro flux calculations")
        label_txt2.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)

        label_txt3 = qtw.QLabel(f"v{info.__version__} / {info.__date__}")
        label_txt3.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)

        label_txt4 = qtw.QLabel(f"using EddyPro v{info.__ep_version__}")
        label_txt4.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)

        # Links
        # self.lbl_link_releases = qtw.QLabel(f"<a href='{info.__link_releases__}'>Releases</a>\n")
        # self.lbl_link_releases.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)
        # grid.addWidget(self.lbl_link_releases, 5, 0)

        self.lbl_link_releases = gui_elements.add_label_link_to_grid(
            link_txt='Releases', link_str=info.__link_releases__, grid=grid, row=6)
        self.lbl_link_source_code = gui_elements.add_label_link_to_grid(
            link_txt='Source Code', link_str=info.__link_source_code__, grid=grid, row=7)
        # self.lbl_link_license = gui_elements.add_label_link_to_grid(
        #     link_txt='License', link_str=info.__license__, grid=grid, row=8)
        self.lbl_link_changelog = gui_elements.add_label_link_to_grid(
            link_txt='Changelog', link_str=info.__link_changelog__, grid=grid, row=8)
        self.lbl_link_ep_changelog = gui_elements.add_label_link_to_grid(
            link_txt='EddyPro Changelog', link_str=info.__link_ep_changelog__, grid=grid, row=9)

        grid.addWidget(label_image, 0, 0)
        grid.addWidget(qtw.QLabel(), 1, 0)
        grid.addWidget(label_txt, 2, 0)
        grid.addWidget(label_txt2, 3, 0)
        grid.addWidget(label_txt3, 4, 0)
        grid.addWidget(label_txt4, 5, 0)

        grid.setRowStretch(10, 1)
        section.setLayout(grid)
        return section

    def add_section_output(self):
        # Instruments (instr)
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_output')
        grid = qtw.QGridLayout()

        # Main Header
        header_output_output = qtw.QLabel('Output')
        header_output_output.setProperty('labelClass', 'header_1')
        grid.addWidget(header_output_output, 0, 0)

        # Output folder
        header_output_plots = qtw.QLabel('Output Folder')
        header_output_plots.setProperty('labelClass', 'header_2')
        grid.addWidget(header_output_plots, 1, 0, 1, 1)
        self.btn_output_folder = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=2)
        self.btn_output_folder.setToolTip(tooltips.btn_output_folder)
        self.lbl_output_folder = qtw.QLabel("***Please select output folder...***")
        grid.addWidget(self.lbl_output_folder, 3, 0, 1, 2)

        # Plots
        header_output_plots = qtw.QLabel('Plots')
        header_output_plots.setProperty('labelClass', 'header_2')
        grid.addWidget(header_output_plots, 4, 0, 1, 1)
        self.chk_output_plots_availability_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Availability (Raw Data)', grid=grid, row=5)
        self.chk_output_plots_aggregates_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Aggregates (Raw Data)', grid=grid, row=6)
        self.chk_output_plots_summary = \
            gui_elements.add_checkbox_to_grid(label='Summary (Flux Processing)', grid=grid, row=7)

        # After processing
        header_output_plots = qtw.QLabel('After Processing')
        header_output_plots.setProperty('labelClass', 'header_2')
        grid.addWidget(header_output_plots, 8, 0, 1, 1)
        self.chk_output_afterprocessing_delete_ascii_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Delete uncompressed raw data ASCII', grid=grid, row=9)

        grid.setRowStretch(10, 1)
        section.setLayout(grid)
        return section

    def add_section_instruments(self):
        # Instruments (instr)
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_instruments')
        grid = qtw.QGridLayout()

        # Main Header
        header_instr_instruments = qtw.QLabel('Instruments')
        header_instr_instruments.setProperty('labelClass', 'header_1')
        grid.addWidget(header_instr_instruments, 0, 0)

        # Site Selection
        header_instr_time_range = qtw.QLabel('Site')
        header_instr_time_range.setProperty('labelClass', 'header_2')
        grid.addWidget(header_instr_time_range, 1, 0)
        self.cmb_instr_site_selection = \
            gui_elements.add_label_combobox_to_grid(label='Select Site', grid=grid, row=2,
                                                    items=['CH-AES', 'CH-AWS', 'CH-CHA', 'CH-DAE',
                                                           'CH-DAV', 'CH-DAS', 'CH-FOR', 'CH-FRU',
                                                           'CH-HON', 'CH-INO', 'CH-LAE', 'CH-LAS',
                                                           'CH-OE2', 'CH-TAN'])
        self.cmb_instr_site_selection.setMaxVisibleItems(99)

        grid.setRowStretch(3, 1)
        section.setLayout(grid)

        return section

    def add_section_processing(self):
        """Add raw data section"""
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_processing')
        grid = qtw.QGridLayout()

        # Main Header
        header_proc = qtw.QLabel('Processing')
        header_proc.setProperty('labelClass', 'header_1')
        grid.addWidget(header_proc, 0, 0)

        # Raw Data

        # Source Folder
        header_proc_rawdata_source_dir = qtw.QLabel('Raw Data: Source Folder (ASCII)')
        header_proc_rawdata_source_dir.setProperty('labelClass', 'header_2')
        grid.addWidget(header_proc_rawdata_source_dir, 1, 0)
        self.btn_proc_rawdata_source_dir = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=2)
        self.lbl_proc_rawdata_source_dir_selected = qtw.QLabel("***Please select source folder***")
        grid.addWidget(self.lbl_proc_rawdata_source_dir_selected, 3, 0, 1, 2)

        # File Compression
        self.cmb_proc_rawdata_compr = \
            gui_elements.add_label_combobox_to_grid(label='ASCII File Compression', grid=grid, row=4,
                                                    items=['gzip', 'None'])
        self.cmb_proc_rawdata_compr.setToolTip(tooltips.cmb_output_compression)

        # File Settings
        header_proc_rawdata_file_settings = qtw.QLabel('Raw Data: File Settings')
        header_proc_rawdata_file_settings.setProperty('labelClass', 'header_2')
        grid.addWidget(header_proc_rawdata_file_settings, 5, 0, 1, 1)
        self.lne_proc_filedt_format = \
            gui_elements.add_label_lineedit_to_grid(label='Date/Time Format In File Name '
                                                          '(default: yyyymmddHHMM)', grid=grid,
                                                    row=6, value='*.X*')

        # Time Range
        header_processing_time_range = qtw.QLabel('Raw Data: Time Range')
        header_processing_time_range.setProperty('labelClass', 'header_2')
        grid.addWidget(header_processing_time_range, 7, 0)
        self.dtp_processing_time_range_start = \
            gui_elements.add_label_datetimepicker_to_grid(label='Start', grid=grid, row=8)
        self.dtp_processing_time_range_end = \
            gui_elements.add_label_datetimepicker_to_grid(label='End', grid=grid, row=9)

        # EddyPro Processing File
        header_proc_rawdata_source_dir = qtw.QLabel('EddyPro: Processing File')
        header_proc_rawdata_source_dir.setProperty('labelClass', 'header_2')
        grid.addWidget(header_proc_rawdata_source_dir, 10, 0)
        self.btn_proc_ep_procfile = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=11)
        self.lbl_proc_ep_procfile_selected = qtw.QLabel("***Please select EddyPro *.processing file***")
        grid.addWidget(self.lbl_proc_ep_procfile_selected, 12, 0, 1, 2)

        grid.setRowStretch(13, 1)
        section.setLayout(grid)
        return section

    def add_section_controls(self):
        # ----------------------------------------------------------
        # CONTROLS (ctr)
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_controls')
        grid = qtw.QGridLayout()

        # Main Header
        header_ctr_controls = qtw.QLabel('Controls')
        header_ctr_controls.setProperty('labelClass', 'header_1')
        grid.addWidget(header_ctr_controls, 0, 0)

        # Buttons
        self.btn_ctr_run = \
            gui_elements.add_button_to_grid(label='Run', grid=grid, row=1)

        grid.setRowStretch(3, 1)
        section.setLayout(grid)

        return section


class TesGui(qtw.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(TesGui, self).__init__(parent)
        self.setupUi(self)


def main():
    appp = qtw.QApplication(sys.argv)
    testgui = TesGui()
    testgui.show()
    appp.exec_()


if __name__ == '__main__':
    main()
