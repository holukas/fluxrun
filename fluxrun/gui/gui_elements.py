from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5.QtGui import QIntValidator


def add_label_combobox_to_grid(label, grid, row, items: list):
    lbl = qtw.QLabel(label)
    cmb = qtw.QComboBox()
    cmb.addItems(items)
    grid.addWidget(lbl, row, 0)
    grid.addWidget(cmb, row, 1)
    return cmb


def add_label_datetimepicker_to_grid(label, grid, row):
    lbl = qtw.QLabel(label)
    datetimepicker = qtw.QDateTimeEdit()
    grid.addWidget(lbl, row, 0)
    grid.addWidget(datetimepicker, row, 1)
    return datetimepicker


def add_label_lineedit_to_grid(label, grid, row, value, only_int=False):
    lbl = qtw.QLabel(label)
    lineedit = qtw.QLineEdit(value)
    lineedit.setProperty('labelClass', 'section_bg_raw_bin')
    lineedit.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)
    if only_int:
        onlyIntegers = QIntValidator()
        lineedit.setValidator(onlyIntegers)
    grid.addWidget(lbl, row, 0)
    grid.addWidget(lineedit, row, 1, 1, 1)
    return lineedit


def add_checkbox_to_grid(label, grid, row):
    checkbox = qtw.QCheckBox(label)
    grid.addWidget(checkbox, row, 0)
    return checkbox


def add_button_to_grid(label, grid, row, colspan=1):
    button = qtw.QPushButton(label)
    grid.addWidget(button, row, 0, 1, colspan)
    return button


def add_label_link_to_grid(link_txt, link_str, grid, row, colspan=1):
    label_link = qtw.QLabel(f"<a href='{link_str}'>{link_txt}</a>\n")
    label_link.setProperty('labelClass', 'label_link')
    label_link.setAlignment(qtc.Qt.AlignCenter | qtc.Qt.AlignVCenter)
    grid.addWidget(label_link, row, 0, 1, colspan)
    return label_link
