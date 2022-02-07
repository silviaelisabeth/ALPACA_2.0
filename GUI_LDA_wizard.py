__author__ = 'szieger'
__project__ = 'SCHeMA_GUI_LDA'

import matplotlib
matplotlib.use('Qt5Agg')
import GUI_LDA_functions as algae
import sys
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QFrame, QWidget, QVBoxLayout, QHBoxLayout, QMainWindow, QPushButton,
                             QFileDialog, QAction, qApp, QGridLayout, QLabel, QLineEdit, QCheckBox, QTextEdit,
                             QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT, FigureCanvasQTAgg
import pandas as pd
import numpy as np
import seaborn as sns
import os
from matplotlib.patches import Ellipse
import matplotlib.patches as mpatches

# global parameter
sns.set_context('paper', font_scale=.5, rc={"lines.linewidth": .25, "axes.linewidth": 0.25})
sns.set_style('ticks', {"xtick.direction": "in", "ytick.direction": "in"})


# global parameters
fs = 5          # font size in plot figures
fs_font = 11    # font size for buttons, etc. in window layout
led_color_dict = {"380 nm": '#610061', "403 nm": '#8300BC', "438 nm": '#0A00FF', "453 nm": '#0057FF',
                  "472 nm": '#00AEFF', "526 nm": '#00FF17', "544 nm": '#8CFF00', "593 nm": '#FFD500',
                  "640 nm": '#FF2100'}


class QIComboBox(QComboBox):
    def __init__(self):
        super(QIComboBox, self).__init__()


class MagicWizard(QWizard):
    def __init__(self):
        super(MagicWizard, self).__init__()
        self.introPage = IntroPage()
        self.setPage(1, self.introPage)
        self.sample_project = SamplePage()
        self.setPage(2, self.sample_project)
        self.LDA_project = LDAPage()
        self.setPage(3, self.LDA_project)

        # set start page
        self.setStartId(1)

        # GUI layout
        self.setWindowTitle("ALPACA - LDA4algae")
        self.setGeometry(50, 50, 500, 300)

        # define Wizard style and certain options
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOptions(QtWidgets.QWizard.NoCancelButtonOnLastPage | QtWidgets.QWizard.HaveFinishButtonOnEarlyPages)


class IntroPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTitle("InfoPage")
        self.setSubTitle("Please provide the path to your measurement file as well as the path to additional files for "
                         "device calibration.")
        self.setMaximumSize(500, 300)

        # create buttons to load data
        self.load_sample_button = QPushButton('Load sample', self)
        self.load_sample_button.setMaximumWidth(150), self.load_sample_button.setFont(QFont('Helvetica Neue', fs_font))
        self.load_blank_button = QPushButton('Load blank', self)
        self.load_blank_button.setMaximumWidth(150), self.load_blank_button.setFont(QFont('Helvetica Neue', fs_font))
        self.load_database_button = QPushButton('Load database', self)
        self.load_database_button.setMaximumWidth(150)
        self.load_database_button.setFont(QFont('Helvetica Neue', fs_font))
        self.load_ex_correction_button = QPushButton('Ex-correction sample', self)
        self.load_ex_correction_button.setMaximumWidth(150)
        self.load_ex_correction_button.setFont(QFont('Helvetica Neue', fs_font))
        self.load_em_correction_button = QPushButton('Em-correction sample', self)
        self.load_em_correction_button.setMaximumWidth(150)
        self.load_em_correction_button.setFont(QFont('Helvetica Neue', fs_font))

        # Text-box displaying chosen files
        self.sample_edit = QTextEdit(self)
        self.sample_edit.setReadOnly(True), self.sample_edit.setMaximumSize(200, 20)
        self.sample_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.blank_edit = QTextEdit(self)
        self.blank_edit.setReadOnly(True), self.blank_edit.setMaximumSize(200, 20)
        self.blank_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.database_edit = QTextEdit(self)
        self.database_edit.setReadOnly(True), self.database_edit.setMaximumSize(200, 20)
        self.fname_database = 'supplementary/trainingdatabase/20170829_trainignsmatrix_corrected_norm-to-max.txt'
        self.database_edit.append('trainingsmatrix_corrected')
        self.database_edit.setFont(QFont('Helvetica Neue', fs_font)), self.database_edit.setAlignment(Qt.AlignRight)
        self.ex_correction_edit = QTextEdit(self)
        self.ex_correction_edit.setReadOnly(True), self.ex_correction_edit.setMaximumSize(200, 20)
        self.ex_correction_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.em_correction_edit = QTextEdit(self)
        self.em_correction_edit.setReadOnly(True), self.em_correction_edit.setFixedSize(200, 20)
        self.em_correction_edit.setFont(QFont('Helvetica Neue', fs_font))

        # ----------------------------------------------------------------------------------
        # creating main window (GUI)
        w = QWidget()
        # create layout grid
        mlayout = QVBoxLayout(w)
        vbox_top = QHBoxLayout()
        mlayout.addLayout(vbox_top)

        path_group = QGroupBox("File paths")
        grid_load = QGridLayout()
        path_group.setFixedSize(500, 250)
        path_group.setFont(QFont('Helvetica Neue', 12))
        vbox_top.addWidget(path_group)
        path_group.setLayout(grid_load)

        # include widgets in the layout
        grid_load.addWidget(self.load_sample_button, 0, 0)
        grid_load.addWidget(self.sample_edit, 0, 1)
        grid_load.addWidget(self.load_blank_button, 1, 0)
        grid_load.addWidget(self.blank_edit, 1, 1)
        grid_load.addWidget(self.load_database_button, 2, 0)
        grid_load.addWidget(self.database_edit, 2, 1)
        grid_load.addWidget(self.load_ex_correction_button, 3,0)
        grid_load.addWidget(self.ex_correction_edit, 3, 1)
        grid_load.addWidget(self.load_em_correction_button, 4, 0)
        grid_load.addWidget(self.em_correction_edit, 4, 1)

        path_group.setContentsMargins(50, 20, 10, 10)
        self.setLayout(mlayout)

        # connect button with function
        self.load_sample_button.clicked.connect(self.open_sample)
        self.load_blank_button.clicked.connect(self.open_blank)
        self.load_database_button.clicked.connect(self.open_database)
        self.load_ex_correction_button.clicked.connect(self.open_ex_calibration)
        self.load_em_correction_button.clicked.connect(self.open_em_calibration)

        # registered field for mandatory input
        self.fname_blank, self.fname_sample = QLineEdit(), QLineEdit()
        #self.registerField("Data", self.fname_sample)
        #self.registerField("Blank", self.fname_blank)
        #self.registerField("Database*", self.database_edit)
        #self.registerField('ex calibration*', self.fname_ex)
        #self.registerField('em calibration*', self.fname_em)

    def open_sample(self):
        self.fname = QFileDialog.getOpenFileName(self, "Select a measurement file", 'measurement/')[0]
        if not self.fname:
            return
        self.read_sample_name(self.fname)
        self.sample_edit.setAlignment(Qt.AlignRight)

    def read_sample_name(self, fname):
        try:
            date = fname.split('/')[-1].split('.')[0].split('_')[0]
            name = fname.split('/')[-1].split('.')[0].split('_')[1]
        except:
            sample_load_failed = QMessageBox()
            sample_load_failed.setIcon(QMessageBox.Information)
            sample_load_failed.setText("Invalid sample file!")
            sample_load_failed.setInformativeText("Choose another file from path...")
            sample_load_failed.setWindowTitle("Error!")
            sample_load_failed.buttonClicked.connect(self.open_sample)
            sample_load_failed.exec_()
            return
        self.fname_sample = fname
        self.date = date
        self.name = name
        self.sample_edit.setText(str(self.date + '_' + self.name))

    def open_blank(self):
        self.fname_blank = QFileDialog.getOpenFileName(self, "Select a blank file", "measurement/blank/")[0]
        if not self.fname_blank:
            return
        self.read_blank_name(self.fname_blank)
        self.blank_edit.setAlignment(Qt.AlignRight)

    def read_blank_name(self, fname_blank):
        try:
            blank_file = fname_blank.split('/')[-1]
            date_blank = fname_blank.split('/')[-1].split('.')[0].split('_')[0]
            name_blank = fname_blank.split('/')[-1].split('.')[0].split('_')[1]
        except:
            blank_load_failed = QMessageBox()
            blank_load_failed.setIcon(QMessageBox.Information)
            blank_load_failed.setText("Invalid blank file!")
            blank_load_failed.setInformativeText("Choose another file from path...")
            blank_load_failed.setWindowTitle("Error!")
            blank_load_failed.buttonClicked.connect(self.open_blank)
            blank_load_failed.exec_()
            return

        self.name_blank = name_blank
        self.date_blank = date_blank
        self.blank_edit.setText(str(self.date_blank + '_' + self.name_blank))

    def open_database(self):
        self.fname_database = None
        self.fname_database = QFileDialog.getOpenFileName(self, "Select Training database",
                                                          "supplementary/trainingdatabase")[0]

        if not self.fname_database:
            return
        self.read_database_name(self.fname_database)
        self.database_edit.setAlignment(Qt.AlignRight)
        if self.database_edit.toPlainText():
            print('database: ', self.database_edit.toPlainText())

    def read_database_name(self, fname_database):
        try:
            database_folder = fname_database.split('/')[-1]
        except:
            blank_load_failed = QMessageBox()
            blank_load_failed.setIcon(QMessageBox.Information)
            blank_load_failed.setText("Invalid path for database!")
            blank_load_failed.setInformativeText("Choose another folder from path...")
            blank_load_failed.setWindowTitle("Error!")
            blank_load_failed.buttonClicked.connect(self.open_database)
            blank_load_failed.exec_()
            return
        self.database_edit.setText(str(database_folder))

    def open_ex_calibration(self):
        self.fname_ex_ = QFileDialog.getOpenFileName(self, "Select specific correction file for LEDs",
                                                    "supplementary/calibration/excitation-site/")[0]
        if not self.fname_ex_:
            return
        self.read_correction_ex(self.fname_ex_)
        self.ex_correction_edit.setAlignment(Qt.AlignRight)

    def read_correction_ex(self, fname_ex_):
        try:
            self.fname_ex = self.fname_ex_
            self.led_file = fname_ex_.split('/')[-1].split('.')[0].split('_')
            date_ex = self.led_file[0]
            name_ex = self.led_file[3]
        except:
            correction_ex_load_failed = QMessageBox()
            correction_ex_load_failed.setIcon(QMessageBox.Information)
            correction_ex_load_failed.setText("Invalid file for excitation correction!")
            correction_ex_load_failed.setInformativeText("Choose another file from path...")
            correction_ex_load_failed.setWindowTitle("Error!")
            correction_ex_load_failed.buttonClicked.connect(self.open_ex_calibration)
            correction_ex_load_failed.exec_()
            return

        if len(self.led_file) > 5:
            self.device = self.led_file[5]
        else:
            self.device = 0
        if len(self.led_file) > 6:
            self.led_setup = self.led_file[6]
        else:
            self.led_setup = 1
        self.date_ex = self.led_file[0]
        self.name_ex = self.led_file[3]
        self.ex_correction_edit.setText(str(self.date_ex + '_' + self.name_ex))

    def open_em_calibration(self):
        self.fname_em = QFileDialog.getOpenFileName(self, "Select specific correction file for emission side",
                                                    "supplementary/calibration/emission-site/")[0]
        if not self.fname_em:
            return
        self.read_correction_em(self.fname_em)
        self.em_correction_edit.setAlignment(Qt.AlignRight)

    def read_correction_em(self, fname_em):
        self.em_correction_edit.clear()
        try:

            self.em_file = fname_em.split('/')[-1].split('.')[0].split('_')
            number_em = self.em_file[2]
        except:
            correction_em_load_failed = QMessageBox()
            correction_em_load_failed.setIcon(QMessageBox.Information)
            correction_em_load_failed.setText("Invalid file for emission correction!")
            correction_em_load_failed.setInformativeText("Choose another file from path...")
            correction_em_load_failed.setWindowTitle("Error!")
            correction_em_load_failed.buttonClicked.connect(self.open_em_calibration)
            correction_em_load_failed.exec_()
            return
        self.em_file = self.fname_em.split('/')[-1].split('.')[0].split('_')
        self.number_em = number_em
        self.em_correction_edit.insertPlainText(str('emission_' + self.number_em))


class SamplePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Time-drive selection")
        self.setSubTitle("... to be written")

        # LED checkboxes used for evaluation
        self.LED526_checkbox = QCheckBox('526 nm', self)
        self.LED526_checkbox.toggle(), self.LED526_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED438_checkbox = QCheckBox('438 nm', self)
        self.LED438_checkbox.toggle(), self.LED438_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED593_checkbox = QCheckBox('593 nm', self)
        self.LED593_checkbox.toggle(), self.LED593_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED453_checkbox = QCheckBox('453 nm', self)
        self.LED453_checkbox.toggle(), self.LED453_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED380_checkbox = QCheckBox('380 nm', self)
        self.LED380_checkbox.toggle(), self.LED380_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED472_checkbox = QCheckBox('472 nm', self)
        self.LED472_checkbox.toggle(), self.LED472_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED403_checkbox = QCheckBox('403 nm', self)
        self.LED403_checkbox.toggle(), self.LED403_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.LED640_checkbox = QCheckBox('640 nm', self)
        self.LED640_checkbox.toggle(), self.LED640_checkbox.setFont(QFont('Helvetica Neue', fs_font))

        # setting button to specify analysis
        self.setting_button = QPushButton('Settings', self)
        self.setting_button.setMaximumWidth(150)
        self.setting_button.setFont(QFont('Helvetica Neue', fs_font))

        # LineEdit for pump rate and separation level

        pump_label, pump_unit = QLabel(self), QLabel(self)
        pump_label.setFont(QFont('Helvetica Neue', fs_font)), pump_unit.setFont(QFont('Helvetica Neue', fs_font))
        pump_label.setText('Pump rate')
        pump_unit.setText('mL/min')
        self.pump_edit = QLineEdit(self)
        self.pump_edit.setValidator(QtGui.QDoubleValidator()), self.pump_edit.setAlignment(Qt.AlignRight)
        self.pump_edit.setText('1.5')

        separation_label = QLabel(self)
        separation_label.setFont(QFont('Helvetica Neue', fs_font))
        separation_label.setText('Separation level')
        self.separation_edit = QLineEdit(self)
        self.separation_edit.setValidator(QtGui.QDoubleValidator()), self.separation_edit.setAlignment(Qt.AlignRight)
        self.separation_edit.setText('order')

        # ---------------------------------------------------------
        # creating window layout
        w1 = QWidget()
        mlayout1 = QHBoxLayout(w1)
        vbox_left, vbox_middle, vbox_right = QVBoxLayout(), QVBoxLayout(), QVBoxLayout()
        mlayout1.addLayout(vbox_left), mlayout1.addLayout(vbox_middle), mlayout1.addLayout(vbox_right)

        # create GroupBox to structure the layout
        led_selection = QGroupBox("LED selection for analysis")
        grid_led = QGridLayout()
        led_selection.setFixedSize(250, 150)
        led_selection.setFont(QFont('Helvetica Neue', fs_font))
        vbox_left.addWidget(led_selection)
        led_selection.setLayout(grid_led)

        grid_led.addWidget(self.LED526_checkbox, 0, 0)
        grid_led.addWidget(self.LED438_checkbox, 1, 0)
        grid_led.addWidget(self.LED593_checkbox, 2, 0)
        grid_led.addWidget(self.LED453_checkbox, 3, 0)
        grid_led.addWidget(self.LED380_checkbox, 0, 1)
        grid_led.addWidget(self.LED472_checkbox, 1, 1)
        grid_led.addWidget(self.LED403_checkbox, 2, 1)
        grid_led.addWidget(self.LED640_checkbox, 3, 1)

        # create GroupBox to structure the layout
        settings_group = QGroupBox("")
        grid_set = QGridLayout()
        settings_group.setFixedHeight(50)
        settings_group.setFont(QFont('Helvetica Neue', fs_font))
        vbox_left.addWidget(settings_group)
        settings_group.setLayout(grid_set)

        grid_set.addWidget(self.setting_button, 5, 1)

        para_group = QGroupBox("Parameter of choice")
        grid_para = QGridLayout()
        para_group.setFixedSize(250, 100)
        para_group.setFont(QFont('Helvetica Neue', fs_font))
        vbox_left.addWidget(para_group)
        para_group.setLayout(grid_para)

        grid_para.addWidget(pump_label, 0, 0)
        grid_para.addWidget(self.pump_edit, 0, 1)
        grid_para.addWidget(pump_unit, 0, 2)
        grid_para.addWidget(separation_label, 1, 0)
        grid_para.addWidget(self.separation_edit, 1, 1)

        # ------------------------------------------------------------
        # draw additional "line" to separate parameters from plots and to separate navigation from rest
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine | QFrame.Raised)
        vline.setLineWidth(2)
        vbox_middle.addWidget(vline)

        # figure plot - sample loaded for selection of time-drive signal
        self.figS, self.axS = plt.subplots(figsize=(3, 4))
        self.canvasS = FigureCanvasQTAgg(self.figS)
        self.axS.set_xlabel('Time / s', fontsize=fs), self.axS.set_ylabel('Rel. Intensity / pW', fontsize=fs)
        self.axS.invert_yaxis()
        self.axS.tick_params(labelsize=fs, width=.3, length=2.5)
        self.figS.subplots_adjust(bottom=0.2, right=0.95, top=0.9, left=0.15)
        sns.despine()

        # create GroupBox to structure the layout
        timedriveplot_group = QGroupBox("Time drive plot of the sample")
        timedriveplot_group.setFixedSize(600, 400) # width, height
        grid_timedriveplot = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_right.addWidget(timedriveplot_group)
        timedriveplot_group.setLayout(grid_timedriveplot)
        grid_timedriveplot.addWidget(self.canvasS)

        self.setLayout(mlayout1)

        # connect checkbox and load file button with a function
        self.setting_button.clicked.connect(self.LDA_settings)

        self.ls_LDAset = QLineEdit()
        self.registerField('LDA settings', self.ls_LDAset)

    def LDA_settings(self):
        # open a pop up window with options to select what shall be saved
        global wSet
        wSet = SettingWindow(self.ls_LDAset)
        if wSet.isVisible():
            pass
        else:
            wSet.show()


class SettingWindow(QDialog):
    def __init__(self, ls_LDAset):
        super().__init__()
        self.ls_LDAset = ls_LDAset
        self.initUI()

        # when checkbox selected, save information in registered field
        self.close_button.clicked.connect(self.close_window)

    def initUI(self):
        self.setWindowTitle("LDA options")
        self.setGeometry(650, 180, 300, 200)

        # close window button
        self.close_button = QPushButton('OK', self)
        self.close_button.setFixedWidth(100), self.close_button.setFont(QFont('Helvetica Neue', fs_font))

        # checkboxes for possible data tables and figures to save
        self.blank_box = QCheckBox('blank correction', self)
        self.blank_box.setChecked(True)
        self.eblank_box = QCheckBox('external blank', self)
        self.eblank_box.setChecked(False)
        self.emex_box = QCheckBox('Em-/Ex correction', self)
        self.emex_box.setChecked(True)
        self.linEx_box = QCheckBox('linear LED calibration (30-50mA)', self)
        self.linEx_box.setChecked(True)
        self.peakLoD_box = QCheckBox('peak detection (LoD)', self)
        self.peakLoD_box.setChecked(True)
        self.dinophyta_box = QCheckBox('Dinophyta prioritised', self)
        self.dinophyta_box.setChecked(True)
        self.plot3D_box = QCheckBox('3D score plot', self)
        self.plot3D_box.setChecked(True)
        self.plot2D_box = QCheckBox('2D score plot', self)
        self.plot2D_box.setChecked(False)

        # creating window layout
        mlayout2 = QVBoxLayout()
        vbox2_top, vbox2_middle, vbox2_bottom = QHBoxLayout(), QHBoxLayout(), QHBoxLayout()
        mlayout2.addLayout(vbox2_top), mlayout2.addLayout(vbox2_middle), mlayout2.addLayout(vbox2_bottom)

        data_settings = QGroupBox("Data tables")
        grid_data = QGridLayout()
        data_settings.setFont(QFont('Helvetica Neue', 12))
        vbox2_top.addWidget(data_settings)
        data_settings.setLayout(grid_data)

        # include widgets in the layout
        grid_data.addWidget(self.blank_box, 0, 0)
        grid_data.addWidget(self.eblank_box, 1, 0)
        grid_data.addWidget(self.emex_box, 3, 0)
        grid_data.addWidget(self.linEx_box, 4, 0)
        grid_data.addWidget(self.peakLoD_box, 6, 0)
        grid_data.addWidget(self.dinophyta_box, 7, 0)
        grid_data.addWidget(self.plot3D_box, 8, 0)
        grid_data.addWidget(self.plot2D_box, 9, 0)

        ok_settings = QGroupBox("")
        grid_ok = QGridLayout()
        ok_settings.setFont(QFont('Helvetica Neue', 12))
        vbox2_bottom.addWidget(ok_settings)
        ok_settings.setLayout(grid_ok)

        # include widgets in the layout
        grid_ok.addWidget(self.close_button, 0, 0)

        # add everything to the window layout
        self.setLayout(mlayout2)

    def close_window(self):
        self.hide()


# -----------------------------------------------------------------------------------------------
class LDAPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("LDA analysis")
        self.setSubTitle("... to be written")
        self.xcoords = []


#################################################################################################
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    app.setStyle('Breeze')
    app.setWindowIcon(QIcon('ALPACA_icon.jpg'))

    alpaca = MagicWizard()
    # screen Size adjustment
    screen = app.primaryScreen()
    rect = screen.availableGeometry()
    alpaca.setMaximumHeight(int(rect.height() * 0.9))
    #alpaca.setFixedWidth(int(rect.width() * 0.95))

    # show wizard
    alpaca.show()
    sys.exit(app.exec_())

