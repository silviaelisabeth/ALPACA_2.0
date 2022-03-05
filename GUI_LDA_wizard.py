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
sns.set_context('paper', font_scale=.5, rc={"lines.linewidth": .25, "axes.linewidth": 0.25, "grid.linewidth": 0.25})
sns.set_style('ticks', {"xtick.direction": "in", "ytick.direction": "in"})


# global layout parameters
fs = 5          # font size in plot figures
fs_font = 11    # font size for buttons, etc. in window layout
led_color_dict = {"380 nm": '#610061', "403 nm": '#8300BC', "438 nm": '#0A00FF', "453 nm": '#0057FF',
                  "472 nm": '#00AEFF', "526 nm": '#00FF17', "544 nm": '#8CFF00', "593 nm": '#FFD500',
                  "640 nm": '#FF2100'}

# global parameters
led_selected = ['526', '438', '593', '453', '380', '472', '403', '640']
ls_LDAset = ['blank correction', 'optical correction', 'LED linear ampl', 'peak detection', 'dinophyta', '3D']

#!!!TODO: resize pages
# !!!TODO: switch 3D vs 2D
#!!! TODO: requirements to allow nextID


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
        self.initUI()

        # connect button with function
        self.load_sample_button.clicked.connect(self.open_sample)
        self.load_blank_button.clicked.connect(self.open_blank)
        self.load_database_button.clicked.connect(self.open_database)
        self.load_ex_correction_button.clicked.connect(self.open_ex_calibration)
        self.load_em_correction_button.clicked.connect(self.open_em_calibration)
        self.reset_button.clicked.connect(self.reset_lineEdit)

        # registered field for mandatory input
        self.fname_blank, self.fname_sample, self.fname_ex = QLineEdit(), QLineEdit(), QLineEdit()
        self.fname_em = QLineEdit()
        self.registerField("Data*", self.fname_sample)
        self.registerField("Blank", self.fname_blank)
        self.registerField("Database", self.database)
        self.registerField('ex calibration', self.fname_ex)
        self.registerField('em calibration', self.fname_em)

    def initUI(self):
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
        self.reset_button = QPushButton('Reset', self)
        self.reset_button.setMaximumWidth(150)
        self.reset_button.setFont(QFont('Helvetica Neue', fs_font))

        # Text-box displaying chosen files
        self.sample_edit = QTextEdit(self)
        self.sample_edit.setReadOnly(True), self.sample_edit.setMaximumSize(200, 20)
        self.sample_edit.setFont(QFont('Helvetica Neue', fs_font))

        self.blank_edit = QTextEdit(self)
        self.blank_edit.setReadOnly(True), self.blank_edit.setMaximumSize(200, 20)
        self.blank_edit.setFont(QFont('Helvetica Neue', fs_font))

        self.database_edit, self.database = QTextEdit(self), QLineEdit()
        self.database_edit.setReadOnly(True), self.database_edit.setMaximumSize(200, 20)
        self.fname_database = 'supplementary/trainingdatabase/20170829_trainignsmatrix_corrected_norm-to-max.txt'
        self.database_edit.append('trainingsmatrix_corrected'), self.database.setText(self.fname_database)
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
        path_group.setFixedSize(500, 275)
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
        grid_load.addWidget(self.reset_button, 6, 0)

        path_group.setContentsMargins(50, 20, 10, 10)
        self.setLayout(mlayout)

    def reset_lineEdit(self):
        self.sample_edit.clear()
        self.blank_edit.clear()
        self.ex_correction_edit.clear()
        self.em_correction_edit.clear()

        self.fname_sample = QLineEdit()
        self.registerField("Data*", self.fname_sample)

    def open_sample(self):
        self.fname = QFileDialog.getOpenFileName(self, "Select a measurement file", 'measurement/')[0]
        if not self.fname:
            return
        self.read_sample_name(self.fname)
        self.sample_edit.setAlignment(Qt.AlignRight)

    def read_sample_name(self, fname):
        try:
            self.date = fname.split('/')[-1].split('.')[0].split('_')[0]
            self.name = fname.split('/')[-1].split('.')[0].split('_')[1]
        except:
            sample_load_failed = QMessageBox()
            sample_load_failed.setIcon(QMessageBox.Information)
            sample_load_failed.setText("Invalid sample file!")
            sample_load_failed.setInformativeText("Choose another file from path...")
            sample_load_failed.setWindowTitle("Error!")
            sample_load_failed.buttonClicked.connect(self.open_sample)
            sample_load_failed.exec_()
            return

        self.fname_sample.setText(fname)
        self.sample_edit.setText(str(self.date + '_' + self.name))

    def open_blank(self):
        fname_blank = QFileDialog.getOpenFileName(self, "Select a blank file", "measurement/blank/")[0]
        if not fname_blank:
            return

        self.read_blank_name(fname_blank)
        self.blank_edit.setAlignment(Qt.AlignRight)

    def read_blank_name(self, fname_blank):
        try:
            self.date_blank = fname_blank.split('/')[-1].split('.')[0].split('_')[0]
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

        self.fname_blank.setText(fname_blank)
        self.blank_edit.setText(str(self.date_blank + '_' + name_blank))

    def open_database(self):
        self.fname_database = None
        self.fname_database = QFileDialog.getOpenFileName(self, "Select Training database",
                                                          "supplementary/trainingdatabase")[0]
        if not self.fname_database:
            return

        self.read_database_name(self.fname_database)
        self.database_edit.setAlignment(Qt.AlignRight)
        self.database.setText(self.fname_database)

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
            self.fname_ex.setText(self.fname_ex_)
            self.led_file = fname_ex_.split('/')[-1].split('.')[0].split('_')
        except:
            correction_ex_load_failed = QMessageBox()
            correction_ex_load_failed.setIcon(QMessageBox.Information)
            correction_ex_load_failed.setText("Invalid file for excitation correction!")
            correction_ex_load_failed.setInformativeText("Choose another file from path...")
            correction_ex_load_failed.setWindowTitle("Error!")
            correction_ex_load_failed.buttonClicked.connect(self.open_ex_calibration)
            correction_ex_load_failed.exec_()
            return

        self.device = self.led_file[5] if len(self.led_file) > 5 else 0
        self.led_setup = self.led_file[6] if len(self.led_file) > 6 else 1
        self.date_ex, self.name_ex = self.led_file[0], self.led_file[3]
        self.ex_correction_edit.setText(str(self.date_ex + '_' + self.name_ex))

    def open_em_calibration(self):
        fname_em_ = QFileDialog.getOpenFileName(self, "Select specific correction file for emission side",
                                                "supplementary/calibration/emission-site/")[0]
        if not fname_em_:
            return

        self.read_correction_em(fname_em_)
        self.em_correction_edit.setAlignment(Qt.AlignRight)

    def read_correction_em(self, fname_em):
        self.em_correction_edit.clear()
        try:
            self.fname_em.setText(fname_em)
            self.em_file = fname_em.split('/')[-1].split('.')[0].split('_')
            self.number_em = self.em_file[2]
        except:
            correction_em_load_failed = QMessageBox()
            correction_em_load_failed.setIcon(QMessageBox.Information)
            correction_em_load_failed.setText("Invalid file for emission correction!")
            correction_em_load_failed.setInformativeText("Choose another file from path...")
            correction_em_load_failed.setWindowTitle("Error!")
            correction_em_load_failed.buttonClicked.connect(self.open_em_calibration)
            correction_em_load_failed.exec_()
            return

        self.em_correction_edit.insertPlainText(str('emission_' + self.number_em))


class SamplePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Time-drive selection")
        self.setSubTitle("... to be written")

        # creating the layout / grid of the wizard page
        self.initUI()

        # connect checkbox and load file button with a function
        self.setting_button.clicked.connect(self.LDA_settings)
        self.plot_button.clicked.connect(self.TimeDrive)

        self.led_selected = QLineEdit()
        self.led_selected.setText(','.join(led_selected))
        self.LED526_checkbox.stateChanged.connect(self.led2list)
        self.LED438_checkbox.stateChanged.connect(self.led2list)
        self.LED593_checkbox.stateChanged.connect(self.led2list)
        self.LED453_checkbox.stateChanged.connect(self.led2list)
        self.LED380_checkbox.stateChanged.connect(self.led2list)
        self.LED472_checkbox.stateChanged.connect(self.led2list)
        self.LED403_checkbox.stateChanged.connect(self.led2list)
        self.LED640_checkbox.stateChanged.connect(self.led2list)

        #!!!TODO: what is the default list?
        # define default lda settings
        self.ls_LDAset = QLineEdit()
        self.ls_LDAset.setText(','.join(ls_LDAset))

        # registered field for mandatory input
        self.xcoords = QLineEdit()
        self.registerField('LDA settings', self.ls_LDAset)
        self.registerField('LED selected', self.led_selected)
        self.registerField('xcoords*', self.xcoords)

    def initUI(self):
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

        # plot button to plot sample time drive
        self.plot_button = QPushButton('Plot', self)
        self.plot_button.setMaximumWidth(150)
        self.plot_button.setFont(QFont('Helvetica Neue', fs_font))

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

        # create GroupBox to structure the layout
        settings_group = QGroupBox("Navigation panel")
        grid_set = QGridLayout()
        settings_group.setFixedHeight(75)
        settings_group.setFont(QFont('Helvetica Neue', fs_font))
        vbox_left.addWidget(settings_group)
        settings_group.setLayout(grid_set)

        grid_set.addWidget(self.setting_button, 0, 1)
        grid_set.addWidget(self.plot_button, 0, 2)

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

    def LDA_settings(self):
        # open a pop up window with options to select what shall be saved
        global wSet
        wSet = SettingWindow(self.ls_LDAset)
        if wSet.isVisible():
            pass
        else:
            wSet.show()

    def led2list(self):
        ls_led = list()
        if self.LED526_checkbox.isChecked() is True:
            ls_led.append('526')
        if self.LED438_checkbox.isChecked() is True:
            ls_led.append('438')
        if self.LED593_checkbox.isChecked() is True:
            ls_led.append('593')
        if self.LED453_checkbox.isChecked() is True:
            ls_led.append('453')
        if self.LED380_checkbox.isChecked() is True:
            ls_led.append('380')
        if self.LED472_checkbox.isChecked() is True:
            ls_led.append('472')
        if self.LED403_checkbox.isChecked() is True:
            ls_led.append('403')
        if self.LED640_checkbox.isChecked() is True:
            ls_led.append('640')
        self.led_selected.setText(','.join(ls_led))

    def TimeDrive(self):
        # clear xcoords whenever user presses "plot"
        self.ls_xcoords = []

        # execute pre-parameter check and check settings
        [kappa_spec, pumprate, device, correction, full_calibration, blank_corr, blank_mean_ex,
         blank_std_ex] = self.para_prep()

        # Load data and correct them with prescan_load_file function.
        [l, l_corr, header, firstline, current, date, sample_name, blank_mean, blank_std, blank_corrected,
         rg9_sample, rg665_sample, volume, pumprate, unit, unit_corr, unit_bl,
         path] = algae.prescan_load_file(filename=self.field("Data"), kappa_spec=kappa_spec, pumprate=pumprate,
                                         correction=correction, blank_corr=blank_corr, blank_std_ex=blank_std_ex,
                                         full_calibration=full_calibration, blank_mean_ex=blank_mean_ex, device=device)

        l_red = pd.DataFrame(np.zeros(shape=(len(l.index), 0)), index=l.index)
        l_corr_red = pd.DataFrame(np.zeros(shape=(len(l_corr.index), 0)), index=l_corr.index)
        for i in l.columns:
            if i.split(' ')[0] in self.led_selected.text():
                l_red[i] = l[i]
        for i in l_corr.columns:
            if i.split(' ')[0] in self.led_selected.text():
                l_corr_red[i] = l_corr[i]

        # sample data sorted
        self.l_corr_red = l_corr_red.sort_index(axis=1)

        # actual plot data in figure
        self.plotTimeDrive(df=l_corr_red, name=sample_name, date=date, fig=self.figS, ax=self.axS)

        # connect onclick event with function
        self.figS.canvas.mpl_connect('button_press_event', self.onclick_timedrive)

        # !!!TODO: something mandatory for self.registeredField to enable NEXT button only, when plot has been pressed

    def para_prep(self):
        # pump rate
        pumprate = float(self.pump_edit.text())

        # get parameter settings for LDA
        para_lda = self.field('LDA settings').split(',')
        print(525, para_lda)
        # optical correction such as ex/em correction, linear LED amplification
        if self.field('ex calibration'):
            # correction and kappa_spec
            correction, kappa_spec = True, self.field('ex calibration')

            # device
            fname_ex = self.field('ex calibration').split('/')[-1]
            device = fname_ex.split('_')[-2][-1]
            #!!!TODO: double check whether em-calibration has the same device number and whether both exist
            device_em = self.field('em calibration').split('/')[-1].split('-')[-1].split('.')[0]
            if device != device_em:
                print('WARNING ex/em calibration are not selected for the same device. Choose ex-device')

            # full_calibration
            full_calibration = False if 'linear ampl' in para_lda else True
        else:
            correction, full_calibration = False, False
            kappa_spec, fname_ex, device = None, None, None

        # blank / background correction
        blank_corr = True if 'blank correction' in para_lda else False

        # !!!TODO: update blank mean and std from external file in case selected
        if 'external blank' in para_lda and blank_corr is True:
            if self.field('Blank'):
                # blank is not (ex- or em-)corrected so far
                [self.blank, header_bl,
                 self.unit_bl] = algae.read_rawdata(filename=self.field("Blank"), additional=False, blank_mean_ex=None,
                                                    blank_std_ex=None, co=None, factor=1, blank_corr=blank_corr,
                                                    plot_raw=False)
                # convert blank to nW
                blank_mean_ex, blank_std_ex = self.blank2nW()
            else:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setText("Blank file missing for external blank correction. Please, provide file or deselect "
                               "external blank correction in settings.")
                msgBox.setFont(QFont('Helvetica Neue', 11))
                msgBox.setWindowTitle("Error")
                msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msgBox.exec()
                return
        else:
            blank_mean_ex, blank_std_ex = None, None

        return kappa_spec, pumprate, device, correction, full_calibration, blank_corr, blank_mean_ex, blank_std_ex

    def blank2nW(self):
        if self.unit_bl == 'nW':
            blank_mean_ex, blank_std_ex = self.blank.mean().tolist(), self.blank.std().tolist()
        elif self.unit_bl == 'pW':
            blank_mean_ex, blank_std_ex = self.blank.mean().tolist() / 1000, self.blank.std().tolist() / 1000
            self.unit_bl = 'nW'
        elif self.unit_bl == 'µW':
            blank_mean_ex, blank_std_ex = self.blank.mean().tolist() * 1000, self.blank.std().tolist() * 1000
            self.unit_bl = 'nW'
        else:
            self.message.append('The blank is unusually high! Please check the blank ....')
            return
        return blank_mean_ex, blank_std_ex

    def plotTimeDrive(self, df, name, date, fig, ax):
        ax.cla()
        ax.set_title("{} {}/{}/{} {}:{}h - \nSelect time range for sample and"
                     " blank.".format(name, date[6:8], date[4:6], date[:4], date[8:10], date[10:12]), fontsize=fs * 0.9)
        ax.set_xlabel('Time (s)', fontsize=fs)
        ax.set_ylabel('Rel. Fluorescence intensity (rfu)', fontsize=fs)

        # which colors shall be used
        color_LED = []
        for i in df.columns:
            color_LED.append(led_color_dict[i])

        # plotting spectra
        ylim_max = pd.DataFrame(np.zeros(shape=(len(df.columns), 1)), index=df.columns).T
        ylim_min = pd.DataFrame(np.zeros(shape=(len(df.columns), 1)), index=df.columns).T

        for c, p in zip(color_LED, df):
            if df[p].dropna().empty is True:
                df[p][np.isnan(df[p])] = 0
                df[p].plot(ax=ax, color=c, linewidth=1)
            else:
                df[p].dropna().plot(ax=ax, color=c, label=p, linewidth=0.75)
                ylim_max[p] = df[p].dropna().max()
                ylim_min[p] = df[p].dropna().min()
        ax.legend(loc=0, ncol=1, frameon=True, fancybox=True, framealpha=0.25, fontsize=fs * 0.8)

        # Define plotting area. Default is 2 but if max value is higher it has to be rearranged
        y_max = ylim_max.max(axis=1).values[0] * 1.05
        y_min = ylim_min.min(axis=1).values[0] * 1.05
        ax.set_ylim(y_min, y_max)

        fig.tight_layout()
        fig.canvas.draw()

    def onclick_timedrive(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers != Qt.ControlModifier:  # change selected range
            return
        if len(self.ls_xcoords) >= 4:
            return

        if event.xdata is None:
            if len(self.ls_xcoords) < 2:
                event.xdata = self.l_corr_red.index.max()
            else:
                event.xdata = 0

        self.ls_xcoords.append(event.xdata)
        self.axS.vlines(x=self.ls_xcoords, ymin=self.l_corr_red.min().min(), ymax=self.l_corr_red.max().max(),
                        color='k', lw=0.15)
        if len(self.ls_xcoords) == 2:
            self.axS.axvspan(self.ls_xcoords[0], self.ls_xcoords[1], color='grey', alpha=0.3)
        elif len(self.ls_xcoords) == 4:
            self.axS.axvspan(self.ls_xcoords[0], self.ls_xcoords[1], color='grey', alpha=0.3)
            self.axS.axvspan(self.ls_xcoords[2], self.ls_xcoords[3], color='grey', alpha=0.3)
        # update figure plot
        self.figS.canvas.draw()

        # add selected xdata to self.xcoords as str list
        if len(self.ls_xcoords) in (2, 4):
            self.xcoords.setText(str(self.ls_xcoords))


class SettingWindow(QDialog):
    def __init__(self, ls_LDAset):
        super().__init__()
        self.ls_LDAset = ls_LDAset
        self.initUI()

        # when checkbox selected, save information in registered field
        self.close_button.clicked.connect(self.close_window)

        self.blank_box.stateChanged.connect(self.lda_set2field)
        self.eblank_box.stateChanged.connect(self.lda_set2field)
        self.emex_box.stateChanged.connect(self.lda_set2field)
        self.linEx_box.stateChanged.connect(self.lda_set2field)
        self.peakLoD_box.stateChanged.connect(self.lda_set2field)
        self.dinophyta_box.stateChanged.connect(self.lda_set2field)

    def initUI(self):
        self.setWindowTitle("LDA options")
        self.setGeometry(650, 180, 300, 200)

        # close window button
        self.close_button = QPushButton('OK', self)
        self.close_button.setFixedWidth(100), self.close_button.setFont(QFont('Helvetica Neue', fs_font))

        # checkboxes for possible data tables and figures to save
        self.blank_box = QCheckBox('blank correction', self)
        if 'blank correction' in ls_LDAset:
            self.blank_box.setChecked(True)
        else:
            self.blank_box.setChecked(False)
        self.eblank_box = QCheckBox('external blank', self)
        if 'external blank' in ls_LDAset:
            self.eblank_box.setChecked(True)
        else:
            self.eblank_box.setChecked(False)
        self.emex_box = QCheckBox('Em-/Ex correction', self)
        if 'optical correction' in ls_LDAset:
            self.emex_box.setChecked(True)
        else:
            self.emex_box.setChecked(False)
        self.linEx_box = QCheckBox('linear LED calibration (30-50mA)', self)
        if 'LED linear ampl' in ls_LDAset:
            self.linEx_box.setChecked(True)
        else:
            self.linEx_box.setChecked(False)
        self.peakLoD_box = QCheckBox('Peak detection (LoD)', self)
        if 'peak detection' in ls_LDAset:
            self.peakLoD_box.setChecked(True)
        else:
            self.peakLoD_box.setChecked(False)
        self.dinophyta_box = QCheckBox('Dinophyta prioritised', self)
        if 'dinophyta' in ls_LDAset:
            self.dinophyta_box.setChecked(True)
        else:
            self.dinophyta_box.setChecked(False)

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

        ok_settings = QGroupBox("")
        grid_ok = QGridLayout()
        ok_settings.setFont(QFont('Helvetica Neue', 12))
        vbox2_bottom.addWidget(ok_settings)
        ok_settings.setLayout(grid_ok)

        # include widgets in the layout
        grid_ok.addWidget(self.close_button, 0, 0)

        # add everything to the window layout
        self.setLayout(mlayout2)

    def lda_set2field(self):
        ls_lda = list()
        # internal or external blank correction
        if self.blank_box.isChecked() is True:
            ls_lda.append('blank correction')
        if self.eblank_box.isChecked() is True:
            ls_lda.append('external blank')

        # optical correction
        if self.emex_box.isChecked() is True:
            ls_lda.append('optical correction')
        if self.linEx_box.isChecked() is True:
            ls_lda.append('LED linear ampl')
        if self.peakLoD_box.isChecked() is True:
            ls_lda.append('peak detection')
        if self.dinophyta_box.isChecked() is True:
            ls_lda.append('dinophyta')

        # update register field of lda settings
        self.ls_LDAset.setText(','.join(ls_lda))

        # update global LDA setting list
        global ls_LDAset
        ls_LDAset = ls_lda

    def close_window(self):
        self.hide()


class LDAPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("LDA analysis")
        self.setSubTitle("... to be written")

        # load layout
        self.initUI()

        # connect button and checkbox with functions
        self.plot3D_box1.stateChanged.connect(self.mpl_3Dplot)
        self.plot2D_box1.stateChanged.connect(self.mpl_2Dplot)
        self.run_button.clicked.connect(self.run_LDA)

    def initUI(self):
        # buttons to control the analysis
        self.histo_button = QPushButton('Check histogram', self)
        self.histo_button.setMaximumWidth(150)
        self.histo_button.setFont(QFont('Helvetica Neue', fs_font))
        self.run_button = QPushButton('Run analysis', self)
        self.run_button.setMaximumWidth(150)
        self.run_button.setFont(QFont('Helvetica Neue', fs_font))
        self.saveAll_button = QPushButton('Save all', self)
        self.saveAll_button.setMaximumWidth(150)
        self.saveAll_button.setFont(QFont('Helvetica Neue', fs_font))
        self.save_button = QPushButton('Save report', self)
        self.save_button.setMaximumWidth(150)
        self.save_button.setFont(QFont('Helvetica Neue', fs_font))

        # again as already in the settings; but for ease of use
        self.plot3D_box1 = QCheckBox('3D score plot', self)
        self.plot2D_box1 = QCheckBox('2D score plot', self)
        if '3D' in ls_LDAset:
            self.plot3D_box1.setChecked(True)
            self.plot2D_box1.setChecked(False)
        else:
            self.plot3D_box1.setChecked(False)
            self.plot2D_box1.setChecked(True)

        # ---------------------------------------------------------
        # creating window layout
        w1 = QWidget()
        mlayout1 = QVBoxLayout(w1)
        vbox_bottom, vbox_middle, vbox_top = QHBoxLayout(), QHBoxLayout(), QHBoxLayout()
        mlayout1.addLayout(vbox_top), mlayout1.addLayout(vbox_middle), mlayout1.addLayout(vbox_bottom)

        # ------------------------------------------------------------
        # divide top panel in left and right
        tbox_left, tbox_middle, tbox_right = QVBoxLayout(), QVBoxLayout(), QVBoxLayout()
        vbox_top.addLayout(tbox_left), vbox_top.addLayout(tbox_middle), vbox_top.addLayout(tbox_right)

        # report table
        self.report = QTableWidget(self)
        # !!!TODO: has to be updated
        self.report.setColumnCount(3), self.report.setRowCount(10)
        self.report.setHorizontalHeaderLabels([' ', 'identified class', 'probability [%]'])
        self.report.resizeColumnsToContents()
        self.report.resizeRowsToContents()

        # create GroupBox to structure the layout
        class_grp = QGroupBox("Classification results")
        class_grp.setFixedSize(300, 450)
        grid_class = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        tbox_left.addWidget(class_grp)
        class_grp.setLayout(grid_class)

        grid_class.addWidget(self.report)
        self.report.adjustSize()

        # ------------------------------------------------------------
        # draw additional "line" to separate navigation/control buttons from plot
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine | QFrame.Raised)
        vline.setLineWidth(2)
        tbox_middle.addWidget(vline)

        # ------------------------------------------------------------
        # score plot (3D or 2D) - depending on what is selected
        self.figScore = plt.figure(figsize=(7, 4))
        self.canvasScore = FigureCanvasQTAgg(self.figScore)
        if self.plot3D_box1.isChecked():
            self.axScore = self.figScore.add_subplot(111, projection='3d')
            print(861, '3D score plot')
            plot_3DScore_empty(fig=self.figScore, ax=self.axScore)
        else:
            print(864, '2D score plot')
            plot_2DScore_empty(fig=self.figScore, ax=self.axScore)

        # create GroupBox to structure the layout
        score_grp = QGroupBox("Score plot")
        score_grp.setFixedSize(600, 400)
        grid_score = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        tbox_right.addWidget(score_grp)
        score_grp.setLayout(grid_score)

        grid_score.addWidget(self.canvasScore)

        # create GroupBox to structure the layout
        scoreOp_grp = QGroupBox("")
        scoreOp_grp.setFixedSize(600, 45)
        grid_scoreOp = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        tbox_right.addWidget(scoreOp_grp)
        scoreOp_grp.setLayout(grid_scoreOp)

        grid_scoreOp.addWidget(self.plot3D_box1, 0, 0)
        grid_scoreOp.addWidget(self.plot2D_box1, 0, 1)

        scoreOp_grp.setContentsMargins(100, 5, 5, 5)

        # ------------------------------------------------------------
        # draw additional "line" to separate navigation/control buttons from plot
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine | QFrame.Raised)
        hline.setLineWidth(2)
        vbox_middle.addWidget(hline)

        # ------------------------------------------------------------
        # create GroupBox to structure the layout
        control_grp = QGroupBox("Navigation panel")
        grid_crtl = QGridLayout()
        control_grp.setMinimumWidth(800)
        control_grp.setFont(QFont('Helvetica Neue', fs_font))
        vbox_bottom.addWidget(control_grp)
        control_grp.setLayout(grid_crtl)

        grid_crtl.addWidget(self.histo_button, 0, 1)
        grid_crtl.addWidget(self.run_button, 0, 2)
        grid_crtl.addWidget(self.save_button, 0, 3)
        grid_crtl.addWidget(self.saveAll_button, 0, 4)

        # add grid(s) to main layout of wizard page
        self.setLayout(mlayout1)

    def mpl_3Dplot(self):
        self.figScore.clear()
        if self.plot3D_box1.isChecked() is False and self.plot2D_box1.isChecked() is False:
            self.plot2D_box1.setChecked(True)
            print(950, 'plot 2D')
        elif self.plot3D_box1.isChecked() is True and self.plot2D_box1.isChecked() is True:
            self.plot2D_box1.setChecked(False)
            print(953, 'plot 3D')
        else:
            pass

    def mpl_2Dplot(self):
        self.figScore.clear()
        if self.plot3D_box1.isChecked() is False and self.plot2D_box1.isChecked() is False:
            self.plot3D_box1.setChecked(True), self.plot2D_box1.setChecked(False)
            print(961, 'plot 2D')
        elif self.plot3D_box1.isChecked() is True and self.plot2D_box1.isChecked() is True:
            self.plot3D_box1.setChecked(False), self.plot2D_box1.setChecked(True)
            print(964, 'plot 2D')
            # self.plot_2DScore_empty()
            self.figScore.canvas.draw()
        else:
            pass

    def run_LDA(self):
        print(877, 'do something')
        print(878, self.field('LDA settings'))


def plot_3DScore_empty(fig=None, ax=None):
    if fig is None:
        fig = plt.figure(figsize=(7, 4))
    if ax is None:
        ax = fig.add_subplot(111, projection='3d')

    ax = plt.gca()
    ax.set_xlabel('LDA 1', fontsize=fs, labelpad=-7.5)
    ax.set_ylabel('LDA 2', fontsize=fs, labelpad=-7.5)
    ax.set_zlabel('LDA 3', fontsize=fs, labelpad=-5)
    ax.tick_params(axis='x', which='both', labelsize=fs, width=.3, length=2.5, pad=-3.)
    ax.tick_params(axis='y', which='both', labelsize=fs, width=.3, length=2.5, pad=-2.5)
    ax.tick_params(axis='z', which='both', labelsize=fs, width=.3, length=2.5, pad=0)
    ax.view_init(elev=20., azim=-30)
    fig.tight_layout()
    sns.despine()


def plot_2DScore_empty(fig=None, ax=None):
    if fig is None:
        fig = plt.figure(figsize=(7, 4))
    if ax is None:
        ax = fig.add_subplot(111)
    ax = plt.gca()
    ax.set_xlabel('LDA 1', fontsize=fs, labelpad=-7.5)
    ax.set_ylabel('LDA 2', fontsize=fs, labelpad=-7.5)
    ax.tick_params(axis='x', which='both', labelsize=fs, width=.3, length=2.5, pad=-3.)
    ax.tick_params(axis='y', which='both', labelsize=fs, width=.3, length=2.5, pad=-2.5)
    fig.tight_layout()
    sns.despine()


# -----------------------------------------------------------------------------------------------------------------
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

