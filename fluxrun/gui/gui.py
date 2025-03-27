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

    def __init__(self):
        self.dtp_processing_time_range_start = None
        self.dtp_processing_time_range_end = None
        self.btn_proc_ep_procfile = None
        self.lbl_proc_ep_procfile_selected = None
        self.btn_output_folder = None
        self.lbl_output_folder = None
        self.statusbar = None
        self.lbl_link_releases = None
        self.lbl_link_source_code = None
        self.lbl_link_changelog = None
        self.lbl_link_ep_changelog = None
        self.cmb_instr_site_selection = None
        self.btn_proc_rawdata_source_dir = None
        self.lbl_proc_rawdata_source_dir_selected = None
        self.cmb_proc_rawdata_compr = None
        self.lne_proc_filedt_format = None
        self.chk_output_plots_availability_rawdata = None
        self.chk_output_plots_aggregates_rawdata = None
        self.chk_output_plots_summary = None
        self.chk_output_afterprocessing_delete_ascii_rawdata = None
        self.btn_ctr_run = None

    def setupUi(self, mainwindow):
        # Main window
        mainwindow.setWindowTitle(f"FluxRun")
        mainwindow.setWindowIcon(qtg.QIcon('images/logo_FLUXRUN1.png'))
        mainwindow.move(100, 100)

        # Central widget
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
        container.addWidget(self.add_section_funcs())
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
        label_txt.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        label_txt2 = qtw.QLabel("Wrapper for EddyPro flux calculations")
        label_txt2.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        label_txt3 = qtw.QLabel(f"v{info.__version__} / {info.__date__}")
        label_txt3.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        label_txt4 = qtw.QLabel(f"using EddyPro v{info.__ep_version__}")
        label_txt4.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        # Links
        self.lbl_link_releases = gui_elements.add_label_link_to_grid(
            link_txt='Releases', link_str=info.__link_releases__, grid=grid, row=6)
        self.lbl_link_source_code = gui_elements.add_label_link_to_grid(
            link_txt='Source Code', link_str=info.__link_source_code__, grid=grid, row=7)
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

    def add_section_funcs(self):
        # Settings
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_instruments')
        layout = qtw.QVBoxLayout()
        layout.addWidget(self.add_section_settings())
        section.setLayout(layout)
        return section

    def add_section_settings(self):
        # Start section
        section = qtw.QFrame()
        section.setProperty('labelClass', 'section_bg_instruments')
        grid = qtw.QGridLayout()

        # SITE
        header_instr_instruments = qtw.QLabel('Site')
        header_instr_instruments.setProperty('labelClass', 'header_1')
        grid.addWidget(header_instr_instruments, 0, 0)
        self.cmb_instr_site_selection = \
            gui_elements.add_label_combobox_to_grid(
                label='Select Site', grid=grid, row=2,
                items=['CH-AES', 'CH-AWS', 'CH-CHA', 'CH-DAE',
                       'CH-DAV', 'CH-DAS', 'CH-FOR', 'CH-FRU',
                       'CH-HON', 'CH-INO', 'CH-LAE', 'CH-LAS',
                       'CH-OE2', 'CH-TAN'])
        self.cmb_instr_site_selection.setMaxVisibleItems(99)
        # grid.setRowStretch(3, 1)

        # RAW DATA
        header_proc = qtw.QLabel('Raw Data')
        header_proc.setProperty('labelClass', 'header_1')
        grid.addWidget(header_proc, 3, 0)

        # RAW DATA: Source folder for raw data
        header_proc_rawdata_source_dir = qtw.QLabel('Select raw data source folder (ASCII)')
        grid.addWidget(header_proc_rawdata_source_dir, 4, 0)
        self.btn_proc_rawdata_source_dir = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=4, col=1)
        self.lbl_proc_rawdata_source_dir_selected = qtw.QLabel("***Please select source folder***")
        grid.addWidget(self.lbl_proc_rawdata_source_dir_selected, 4, 2, 1, 1)

        # RAW DATA: File compression
        self.cmb_proc_rawdata_compr = \
            gui_elements.add_label_combobox_to_grid(label='ASCII File Compression', grid=grid, row=5,
                                                    items=['gzip', 'None'])
        self.cmb_proc_rawdata_compr.setToolTip(tooltips.cmb_output_compression)

        # File Settings
        self.lne_proc_filedt_format = \
            gui_elements.add_label_lineedit_to_grid(label='Date/Time Format In File Name '
                                                          '(default: yyyymmddHHMM)', grid=grid,
                                                    row=6, value='*.X*')

        # RAW DATA: Time Range
        self.dtp_processing_time_range_start = \
            gui_elements.add_label_datetimepicker_to_grid(label='Start', grid=grid, row=7)
        self.dtp_processing_time_range_end = \
            gui_elements.add_label_datetimepicker_to_grid(label='End', grid=grid, row=8)

        # PROCESSING SETTINGS: EddyPro Processing File
        header_proc = qtw.QLabel('Processing')
        header_proc.setProperty('labelClass', 'header_1')
        grid.addWidget(header_proc, 9, 0)

        header_proc_rawdata_source_dir = qtw.QLabel('Select EddyPro processing file (*.eddypro)')
        grid.addWidget(header_proc_rawdata_source_dir, 10, 0)
        self.btn_proc_ep_procfile = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=10, col=1)
        self.lbl_proc_ep_procfile_selected = qtw.QLabel("***Please select EddyPro *.processing file***")
        grid.addWidget(self.lbl_proc_ep_procfile_selected, 10, 2, 1, 2)

        # Main Header
        header_output_output = qtw.QLabel('Output')
        header_output_output.setProperty('labelClass', 'header_1')
        grid.addWidget(header_output_output, 11, 0)

        # Output folder
        header_output_plots = qtw.QLabel('Select output folder')
        grid.addWidget(header_output_plots, 12, 0, 1, 1)
        self.btn_output_folder = gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=12, col=1)
        self.btn_output_folder.setToolTip(tooltips.btn_output_folder)
        self.lbl_output_folder = qtw.QLabel("***Please select output folder...***")
        grid.addWidget(self.lbl_output_folder, 12, 2, 1, 1)

        # Plots
        self.chk_output_plots_availability_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Availability (Raw Data)', grid=grid, row=14)
        self.chk_output_plots_aggregates_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Aggregates (Raw Data)', grid=grid, row=15)
        self.chk_output_plots_summary = \
            gui_elements.add_checkbox_to_grid(label='Summary (Flux Processing)', grid=grid, row=16)

        # After processing
        self.chk_output_afterprocessing_delete_ascii_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Delete uncompressed raw data ASCII after processing', grid=grid,
                                              row=18)

        # Buttons
        self.btn_ctr_run = \
            gui_elements.add_button_to_grid(label='Run', grid=grid, row=20, col=0, colspan=3)

        # End section
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
    appp.exec()


if __name__ == '__main__':
    main()
