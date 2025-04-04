# -*- coding: utf-8 -*-
from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg
from PyQt6 import QtWidgets as qtw

import gui.gui_elements as gui_elements
from help import tooltips
from settings import version


class BuildGui(object):
    """
        Prepares the raw GUI, i.e. the canvas that is filled with content later.
    """

    def __init__(self):
        self.dtp_rawdata_time_range_start = None
        self.dtp_rawdata_time_range_end = None
        self.btn_proc_ep_procfile = None
        self.lbl_proc_ep_procfile_selected = None
        self.btn_output_folder = None
        self.lbl_output_folder = None
        self.lbl_link_releases = None
        self.lbl_link_source_code = None
        self.lbl_link_changelog = None
        self.lbl_link_ep_changelog = None
        self.btn_rawdata_source_dir = None
        self.lbl_proc_rawdata_source_dir_selected = None
        self.cmb_rawdata_compr = None
        self.lne_filedt_format = None
        self.chk_output_plots_availability_rawdata = None
        self.chk_output_plots_aggregates_rawdata = None
        self.chk_output_plots_summary = None
        self.chk_output_afterprocessing_delete_ascii_rawdata = None
        self.btn_run = None
        self.cmb_rawdata_header_format = None
        self.lbl_rawdata_sitefiles_parse_str = None
        self.btn_save = None
        self.chk_proc_run_fluxcalcs = None

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

        # # Statusbar
        # self.statusbar = qtw.QStatusBar(mainwindow)
        # self.statusbar.setObjectName("statusbar")
        # self.statusbar.showMessage('No processing running.')
        # mainwindow.setStatusBar(self.statusbar)

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
        label_image.setPixmap(qtg.QPixmap('images/logo_FLUXRUN1_256px.png'))

        label_txt = qtw.QLabel("fluxrun")
        label_txt.setProperty('labelClass', 'header_1')
        label_txt.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        label_txt2 = qtw.QLabel("Wrapper for EddyPro flux calculations")
        label_txt2.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        label_txt3 = qtw.QLabel(f"v{version.__version__} / {version.__date__}")
        label_txt3.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        label_txt4 = qtw.QLabel(f"using EddyPro v{version.__ep_version__}")
        label_txt4.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter | qtc.Qt.AlignmentFlag.AlignVCenter)

        # Links
        self.lbl_link_releases = gui_elements.add_button_link_to_grid(
            link_txt='Releases', grid=grid, row=6)
        self.lbl_link_source_code = gui_elements.add_button_link_to_grid(
            link_txt='Source Code', grid=grid, row=7)
        self.lbl_link_changelog = gui_elements.add_button_link_to_grid(
            link_txt='Changelog', grid=grid, row=8)
        self.lbl_link_ep_changelog = gui_elements.add_button_link_to_grid(
            link_txt='EddyPro Changelog', grid=grid, row=9)

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

        # RAW DATA FILES

        header_instr_instruments = qtw.QLabel('Raw Data Files')
        header_instr_instruments.setProperty('labelClass', 'header_2')
        grid.addWidget(header_instr_instruments, 0, 0)

        # Source folder for raw data
        row = 1
        header_proc_rawdata_source_dir = qtw.QLabel('Select raw data source folder (ASCII)')
        grid.addWidget(header_proc_rawdata_source_dir, row, 0)
        self.btn_rawdata_source_dir = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=row, col=1)
        self.lbl_proc_rawdata_source_dir_selected = qtw.QLabel("***Please select source folder***")
        self.lbl_proc_rawdata_source_dir_selected.setProperty('labelClass', 'filepath')
        grid.addWidget(self.lbl_proc_rawdata_source_dir_selected, row, 2, 1, 1)

        # Filename ID
        row = 2
        self.lne_filename_id = \
            gui_elements.add_label_lineedit_to_grid(
                label='File name ID (default: yyyymmddHHMM)',
                grid=grid, row=row, value='SITE_yyyymmddHHMM.csv.gz')

        # RAW DATA: Header format
        row = 3
        self.cmb_rawdata_header_format = \
            gui_elements.add_label_combobox_to_grid(label='Header format', grid=grid, row=row,
                                                    items=[
                                                        '3-row header (bico files)',
                                                        '4-row header (rECord files)'
                                                    ])
        self.cmb_rawdata_header_format.setToolTip(tooltips.cmb_rawdata_header_format)

        # Time Range
        row = 4
        self.dtp_rawdata_time_range_start = \
            gui_elements.add_label_datetimepicker_to_grid(label='Start', grid=grid, row=row)
        self.dtp_rawdata_time_range_end = \
            gui_elements.add_label_datetimepicker_to_grid(label='End', grid=grid, row=row + 1)

        # Plots
        row = 7
        header_instr_instruments = qtw.QLabel('Plots')
        # header_instr_instruments.setProperty('labelClass', 'header_3')
        grid.addWidget(header_instr_instruments, row, 0)

        self.chk_output_plots_availability_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Availability (raw data)', grid=grid, row=row)
        self.chk_output_plots_aggregates_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Aggregates (raw data)', grid=grid, row=row + 1)

        spacer = qtw.QLabel("")
        spacer.setProperty('labelClass', 'spacer')
        grid.addWidget(spacer, 9, 0)

        # PROCESSING SETTINGS

        # PROCESSING SETTINGS: EddyPro Processing File
        row = 10
        header_proc = qtw.QLabel('Flux Processing Settings')
        header_proc.setProperty('labelClass', 'header_2')
        grid.addWidget(header_proc, row, 0)

        header_proc = qtw.QLabel('Run flux calculations using EddyPro')
        grid.addWidget(header_proc, row + 1, 0)
        self.chk_proc_run_fluxcalcs = \
            gui_elements.add_checkbox_to_grid(label='Calculate fluxes', grid=grid, row=row + 1)

        header_proc_rawdata_source_dir = qtw.QLabel('Select EddyPro processing file (*.eddypro)')
        grid.addWidget(header_proc_rawdata_source_dir, row + 2, 0)
        self.btn_proc_ep_procfile = \
            gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=row + 2, col=1)
        self.lbl_proc_ep_procfile_selected = qtw.QLabel("***Please select EddyPro *.processing file***")
        self.lbl_proc_ep_procfile_selected.setProperty('labelClass', 'filepath')
        grid.addWidget(self.lbl_proc_ep_procfile_selected, row + 2, 2, 1, 2)

        spacer = qtw.QLabel("")
        spacer.setProperty('labelClass', 'spacer')
        grid.addWidget(spacer, row + 3, 0)

        # OUTPUT
        row = 14
        header_output_output = qtw.QLabel('Output')
        header_output_output.setProperty('labelClass', 'header_2')
        grid.addWidget(header_output_output, row, 0)

        header_output_plots = qtw.QLabel('Select output folder')
        grid.addWidget(header_output_plots, row + 1, 0, 1, 1)
        self.btn_output_folder = gui_elements.add_button_to_grid(label='Select ...', grid=grid, row=row + 1, col=1)
        self.btn_output_folder.setToolTip(tooltips.btn_output_folder)
        self.lbl_output_folder = qtw.QLabel("***Please select output folder...***")
        self.lbl_output_folder.setProperty('labelClass', 'filepath')
        grid.addWidget(self.lbl_output_folder, row + 1, 2, 1, 1)

        self.lne_outdir_prefix = \
            gui_elements.add_label_lineedit_to_grid(
                label='Output folder name prefix',
                grid=grid, row=row + 2, value='PREFIX')

        header_instr_instruments = qtw.QLabel('Plots')
        grid.addWidget(header_instr_instruments, row + 3, 0)
        self.chk_output_plots_summary = \
            gui_elements.add_checkbox_to_grid(label='Summary (flux processing)', grid=grid, row=row + 3)

        spacer = qtw.QLabel("")
        spacer.setProperty('labelClass', 'spacer')
        grid.addWidget(spacer, row + 4, 0)

        # OUTPUT: After processing
        row = 19
        header_instr_instruments = qtw.QLabel('After Processing')
        header_instr_instruments.setProperty('labelClass', 'header_2')
        grid.addWidget(header_instr_instruments, row, 0)
        self.chk_output_afterprocessing_delete_ascii_rawdata = \
            gui_elements.add_checkbox_to_grid(label='Delete uncompressed raw data ASCII after processing', grid=grid,
                                              row=row + 1)

        spacer = qtw.QLabel("")
        spacer.setProperty('labelClass', 'spacer')
        grid.addWidget(spacer, row + 2, 0)

        # RUN/SAVE
        row = 22
        self.btn_save = \
            gui_elements.add_button_to_grid(label='Save settings', grid=grid, row=row, col=1, colspan=1)
        self.btn_save.setShortcut(qtg.QKeySequence("Ctrl+S"))  # Set Ctrl+R as the shortcut
        self.btn_run = \
            gui_elements.add_button_to_grid(label='Run', grid=grid, row=row, col=2, colspan=1)
        self.btn_run.setShortcut(qtg.QKeySequence("Ctrl+R"))  # Set Ctrl+R as the shortcut

        # End section
        section.setLayout(grid)

        return section
