__author__ = 'szieger'
__project__ = 'SCHeMA_GUI_LDA'

import matplotlib
matplotlib.use('Qt5Agg')
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
from matplotlib.patches import Ellipse
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime
import pandas as pd
import numpy as np
import os

import GUI_LDA_functions as algae

# global parameter
sns.set_context('paper', font_scale=.5, rc={"lines.linewidth": .25, "axes.linewidth": 0.25, "grid.linewidth": 0.25})
sns.set_style('ticks', {"xtick.direction": "in", "ytick.direction": "in"})


# global layout parameters
fs, fs_font, fs_grp = 5, 11, 10        # font size in plot figures | buttons and text | group labels
font_button, font_bod = 'Helvetica Neue', 'Arimo'
led_color_dict = {"380 nm": '#610061', "403 nm": '#8300BC', "438 nm": '#0A00FF', "453 nm": '#0057FF',
                  "472 nm": '#00AEFF', "526 nm": '#00FF17', "544 nm": '#8CFF00', "593 nm": '#FFD500',
                  "640 nm": '#FF2100'}

# global parameters
led_selected = ['526', '438', '593', '453', '380', '472', '403', '640']
ls_LDAset = ['blank correction', 'optical correction', 'LED linear ampl', 'peak detection', 'dinophyta', '3D']
loaded_data, xcoords, results = dict(), list(), dict()

# global parameter for saving
save_type = ['tiff', 'eps', 'jpg']


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
        self.final = FinalPage()
        self.setPage(4, self.final)

        # set start page
        self.setStartId(1)

        # GUI layout
        self.setWindowTitle("ALPACA - LDA4algae")
        self.setGeometry(50, 50, 500, 300)

        # define Wizard style and certain options
        self.setWizardStyle(QWizard.MacStyle)
        self.setOptions(QtWidgets.QWizard.NoCancelButtonOnLastPage | QtWidgets.QWizard.HaveFinishButtonOnEarlyPages)

        # add a background image
        path = os.path.join('/Users/au652733/Python/ALPACA/logo/', 'logo_ALPACA1.png')
        pixmap = QtGui.QPixmap(path)
        pixmap = pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.setPixmap(QWizard.BackgroundPixmap, pixmap)


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
        self.load_sample_button.setMaximumWidth(150)
        self.load_sample_button.setFont(QFont(font_button, fs_font))
        self.load_blank_button = QPushButton('Load blank', self)
        self.load_blank_button.setMaximumWidth(150)
        self.load_blank_button.setFont(QFont(font_button, fs_font))
        self.load_database_button = QPushButton('Load database', self)
        self.load_database_button.setMaximumWidth(150)
        self.load_database_button.setFont(QFont(font_button, fs_font))
        self.load_ex_correction_button = QPushButton('Ex-correction sample', self)
        self.load_ex_correction_button.setMaximumWidth(150)
        self.load_ex_correction_button.setFont(QFont(font_button, fs_font))
        self.load_em_correction_button = QPushButton('Em-correction sample', self)
        self.load_em_correction_button.setMaximumWidth(150)
        self.load_em_correction_button.setFont(QFont(font_button, fs_font))
        self.reset_button = QPushButton('Reset', self)
        self.reset_button.setMaximumWidth(150)
        self.reset_button.setFont(QFont(font_button, fs_font))

        # Text-box displaying chosen files
        self.sample_edit = QTextEdit(self)
        self.sample_edit.setReadOnly(True), self.sample_edit.setMaximumSize(200, 20)
        self.sample_edit.setFont(QFont(font_button, fs_font))

        self.blank_edit = QTextEdit(self)
        self.blank_edit.setReadOnly(True), self.blank_edit.setMaximumSize(200, 20)
        self.blank_edit.setFont(QFont(font_button, fs_font))

        self.database_edit, self.database = QTextEdit(self), QLineEdit()
        self.database_edit.setReadOnly(True), self.database_edit.setMaximumSize(200, 20)

        self.fname_database = os.getcwd() + '/supplementary/trainingdatabase/20170810_trainingsmatrix_corrected.txt'
        self.database_edit.append('trainingsmatrix_corrected'), self.database.setText(self.fname_database)
        self.database_edit.setFont(QFont(font_button, fs_font)), self.database_edit.setAlignment(Qt.AlignRight)

        self.ex_correction_edit = QTextEdit(self)
        self.ex_correction_edit.setReadOnly(True), self.ex_correction_edit.setMaximumSize(200, 20)
        self.ex_correction_edit.setFont(QFont(font_button, fs_font))

        self.em_correction_edit = QTextEdit(self)
        self.em_correction_edit.setReadOnly(True), self.em_correction_edit.setFixedSize(200, 20)
        self.em_correction_edit.setFont(QFont(font_button, fs_font))

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
        path_group.setFont(QFont(font_button, fs_grp))
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
        fname = QFileDialog.getOpenFileName(parent=self, caption='Select a measurement file', directory='measurement/',
                                            filter='csv(*.csv *.txt)', initialFilter='csv(*.csv, *.txt)')[0]
        if not fname:
            return
        self.read_sample_name(fname)
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
        self.setSubTitle("Before we get to the actual analysis,  you need to select the time interval in which you "
                         "want to analyze the relative phytoplankton composition.  While pressing the COMMAND key,  "
                         "click in the time-drive plot and first select the start/end point of the phytoplankton "
                         "signal.  Then you can additionally select the start/end point of the background signal if "
                         "you want to account for it as well. \nUnder SETTINGS,  you may adjust parameters for the "
                         "analysis.")

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

        self.separation_edit.textEdited.connect(self.updateInfo)

        #!!!TODO: what is the default list?
        # define default lda settings
        self.ls_LDAset, self.separation = QLineEdit(), QLineEdit()
        self.ls_LDAset.setText(','.join(ls_LDAset)), self.separation.setText(self.separation_edit.text())

        # registered field for mandatory input
        self.xcoords = QLineEdit()
        self.registerField('LDA settings', self.ls_LDAset)
        self.registerField('LED selected', self.led_selected)
        self.registerField('xcoords*', self.xcoords)
        self.registerField('separation', self.separation)

    def initUI(self):
        # LED checkboxes used for evaluation
        self.LED526_checkbox = QCheckBox('526 nm', self)
        self.LED526_checkbox.toggle(), self.LED526_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED438_checkbox = QCheckBox('438 nm', self)
        self.LED438_checkbox.toggle(), self.LED438_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED593_checkbox = QCheckBox('593 nm', self)
        self.LED593_checkbox.toggle(), self.LED593_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED453_checkbox = QCheckBox('453 nm', self)
        self.LED453_checkbox.toggle(), self.LED453_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED380_checkbox = QCheckBox('380 nm', self)
        self.LED380_checkbox.toggle(), self.LED380_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED472_checkbox = QCheckBox('472 nm', self)
        self.LED472_checkbox.toggle(), self.LED472_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED403_checkbox = QCheckBox('403 nm', self)
        self.LED403_checkbox.toggle(), self.LED403_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))
        self.LED640_checkbox = QCheckBox('640 nm', self)
        self.LED640_checkbox.toggle(), self.LED640_checkbox.setFont(QFont(font_button, int(fs_font*0.8)))

        # setting button to specify analysis
        self.setting_button = QPushButton('Settings', self)
        self.setting_button.setMaximumWidth(150)
        self.setting_button.setFont(QFont(font_button, fs_grp))

        # plot button to plot sample time drive
        self.plot_button = QPushButton('Plot', self)
        self.plot_button.setMaximumWidth(150)
        self.plot_button.setFont(QFont(font_button, fs_grp))

        # LineEdit for pump rate and separation level
        pump_label, pump_unit = QLabel(self), QLabel(self)
        pump_label.setFont(QFont(font_button, fs_font)), pump_unit.setFont(QFont(font_button, fs_font))
        pump_label.setText('Pump rate')
        pump_unit.setText('mL/min')
        self.pump_edit = QLineEdit(self)
        self.pump_edit.setValidator(QtGui.QDoubleValidator()), self.pump_edit.setAlignment(Qt.AlignRight)
        self.pump_edit.setText('1.5')

        separation_label = QLabel(self)
        separation_label.setFont(QFont(font_button, fs_font))
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
        led_selection.setFont(QFont(font_button, fs_grp))
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
        para_group.setFont(QFont(font_button, fs_grp))
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
        settings_group.setFont(QFont(font_button, fs_grp))
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

        # Load data and correct them
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
        
        # collect relevant parameter to transfer between pages
        global loaded_data, ls_xcoords
        loaded_data = {'l': l_red, 'l_corr': l_corr_red, 'header': header, 'firstline': firstline, 'path': path,
                            'current': current, 'volume': volume, 'name': sample_name, 'date': date, 'unit': unit_corr,
                            'blank_mean': blank_mean, 'blank_std': blank_std, 'unit_blank': unit_bl,
                            'blank_corr': blank_corr, 'pumprate': pumprate, 'correction': correction,
                            'rg9_sample': rg9_sample, 'rg665_sample': rg665_sample, 'full_calibration': full_calibration,
                            'device': device, 'kappa_spec': kappa_spec, 'sep': self.separation_edit.text()}

    def para_prep(self):
        # pump rate
        pumprate = float(self.pump_edit.text())

        # get parameter settings for LDA
        para_lda = self.field('LDA settings').split(',')

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
                text = "Blank file missing for external blank correction. Please, provide file or deselect external " \
                       "blank correction in settings."
                feedback_user(text=text, icon=QMessageBox.Warning, title='Error')
        else:
            blank_mean_ex, blank_std_ex = None, None

        return kappa_spec, pumprate, device, correction, full_calibration, blank_corr, blank_mean_ex, blank_std_ex

    def updateInfo(self):
        self.separation.setText(self.separation_edit.text())

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
        global xcoords
        if len(self.ls_xcoords) in (2, 4):
            self.xcoords.setText(str(self.ls_xcoords))
            xcoords = list(self.ls_xcoords)


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
        self.close_button.setFixedWidth(100), self.close_button.setFont(QFont(font_button, fs_font))

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
        data_settings.setFont(QFont(font_button, fs_grp))
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
        ok_settings.setFont(QFont(font_button, fs_grp))
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
        self.setSubTitle("Now we start with the analysis!  Click on RUN ANALYSIS,  to see the results of the "
                         "classification.  If you want to see more results on the specific pigment pattern recorded "
                         "with the ALPACA,  click CHECK HISTOGRAM.")

        # load layout
        self.initUI()

        # connect button and checkbox with functions
        self.plot3D_box1.stateChanged.connect(self.mpl_decision)
        self.plot2D_box1.stateChanged.connect(self.mpl_decision)
        self.histo_button.clicked.connect(self.plot_histo)
        self.run_button.clicked.connect(self.run_LDA)
        self.save_button.clicked.connect(self.save_report)
        self.saveAll_button.clicked.connect(self.save_all)

    def initUI(self):
        # buttons to control the analysis
        self.histo_button = QPushButton('Check histogram', self)
        self.histo_button.setMaximumWidth(150)
        self.histo_button.setEnabled(False)
        self.histo_button.setFont(QFont(font_button, fs_font))
        self.run_button = QPushButton('Run analysis', self)
        self.run_button.setMaximumWidth(150)
        self.run_button.setFont(QFont(font_button, fs_font))
        self.saveAll_button = QPushButton('Save all', self)
        self.saveAll_button.setMaximumWidth(150)
        self.saveAll_button.setFont(QFont(font_button, fs_font))
        self.save_button = QPushButton('Save report', self)
        self.save_button.setMaximumWidth(150)
        self.save_button.setFont(QFont(font_button, fs_font))

        # again as already in the settings; but for ease of use
        self.plot3D_box1 = QCheckBox('3D score plot', self)
        self.plot2D_box1 = QCheckBox('2D score plot', self)
        if '3D' in ls_LDAset:
            self.plot3D_box1.setChecked(True), self.plot2D_box1.setChecked(False)
        else:
            self.plot3D_box1.setChecked(False), self.plot2D_box1.setChecked(True)

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
        self.report.setColumnCount(3), self.report.setRowCount(1)
        self.report.setHorizontalHeaderLabels([' ', 'identified class', 'probability [%]'])
        self.report.resizeColumnsToContents(), self.report.resizeRowsToContents()
        self.report.adjustSize()

        # create GroupBox to structure the layout
        class_grp = QGroupBox("Classification results")
        class_grp.setFixedSize(350, 450)
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
            self.figScore, self.axScore = plot_3DScore_empty(fig=self.figScore)
        else:
            self.figScore, self.axScore = plot_2DScore_empty(fig=self.figScore)
        self.figScore.canvas.draw()

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
        control_grp.setFont(QFont(font_button, fs_grp))
        vbox_bottom.addWidget(control_grp)
        control_grp.setLayout(grid_crtl)

        grid_crtl.addWidget(self.histo_button, 0, 1)
        grid_crtl.addWidget(self.run_button, 0, 0)
        grid_crtl.addWidget(self.save_button, 0, 3)
        grid_crtl.addWidget(self.saveAll_button, 0, 4)

        # add grid(s) to main layout of wizard page
        self.setLayout(mlayout1)

    def mpl_decision(self, state):
        if state == Qt.Checked:

            # if 3D check box is selected
            if self.sender() == self.plot3D_box1:
                # making other check box to uncheck
                self.plot2D_box1.setChecked(False)
                self.figScore.clear()
                self.figScore, self.axScore = plot_3DScore_empty(fig=self.figScore)

            # if 2D check box is selected
            elif self.sender() == self.plot2D_box1:
                # making other check box to uncheck
                self.plot3D_box1.setChecked(False)
                self.figScore.clear()
                self.figScore, self.axScore = plot_2DScore_empty(fig=self.figScore)
            sns.despine()
            self.figScore.canvas.draw()

    def plot_histo(self):
        global wHisto
        wHisto = HistoWindow(self.mean_corr)
        if wHisto.isVisible():
            pass
        else:
            wHisto.show()

    def run_LDA(self):
        # load relevant data and prepare, e.g. correct them
        self.get_data()
        self.prep_data()

        # preparing classification and output-file
        [self.alg_group, self.alg_phylum, self.phyl_group, _, self.d,
         self.prob] = algae.prep_lda_classify(lda=self.lda, classes_dict=self.classes_dict, df_score=self.df_score,
                                              training_score=self.training_score)
        # determine the probability of belonging for each phytoplankton group, plot scores, and fill results table
        self.process_results()
        self.fillTable()

    def get_data(self):
        led_str = self.field('LED selected')
        ls_led = [int(i) for i in led_str.split(',')]

        # get training data base
        [self.training_corr_red_sort, training,
         self.training_red] = algae.training_database(trainings_path=self.field("Database"), led_used=ls_led)

        # information for training data. Which separation level is chosen?
        [self.classes_dict, _, self.colorclass_dict, _] = algae.separation_level(separation=self.field('separation'))

    def prep_data(self):
        # data correction        
        global loaded_data, xcoords, ls_LDAset
        peak_dt = True if 'peak detection' in ls_LDAset else False
        
        [c, _, self.mean_corr,
         LoD] = algae.correction_sample(l=loaded_data['l'], header=loaded_data['header'], date=loaded_data['date'],
                                        current=loaded_data['current'], volume=loaded_data['volume'],
                                        device=loaded_data['device'], unit_blank=loaded_data['unit_blank'],
                                        led_total=loaded_data['l'].columns, kappa_spec=loaded_data['kappa_spec'],
                                        correction=loaded_data['correction'], blank_corr=loaded_data['blank_corr'],
                                        xcoords=xcoords, full_calibration=loaded_data['full_calibration'],
                                        peak_detection=peak_dt, blank_std=loaded_data['blank_std'],
                                        blank_mean=loaded_data['blank_mean'])

        # calculate average fluorescence intensity at different excitation wavelengths of sample.
        # standardize and normalize the values if it is done with the training-data
        [mean_fluoro, training_corr,
         _] = algae.average_fluorescence(mean_corr=self.mean_corr, normalize=True, standardize=True,
                                         training_corr_sort=self.training_corr_red_sort)

        # evaluation of mean values or individual spike evaluation
        priority = True if 'dinophyta' in ls_LDAset else False
        self.score_type = 3 if self.plot3D_box1.isChecked() is True else 2
        if ['--'] in c.unique():
            [self.lda, self.training_score,
             self.df_score] = algae.lda_process_mean(mean_fluoro=mean_fluoro, training_corr=training_corr,
                                                     unit=loaded_data['unit'], classes_dict=self.classes_dict,
                                                     priority=priority, colorclass_dict=self.colorclass_dict,
                                                     separation=loaded_data['sep'], type_=self.score_type)
        else:
            [self.lda, self.training_score,
             self.df_score] = algae.lda_process_individual(l=loaded_data['l_corr'], training_corr=training_corr,
                                                           priority=priority, classes_dict=self.classes_dict, LoD=LoD,
                                                           normalize=True, separation=loaded_data['sep'], volume=None,
                                                           pumprate=loaded_data['pumprate'], type_=self.score_type,
                                                           colorclass_dict=self.colorclass_dict)

    def fillTable(self):
        #!!!TODO: allow tabs to show classification on different levels
        global loaded_data
        [self.res, self.prob_phylum] = algae.output(self.sample, self.summary, self.summary_, date=loaded_data['date'],
                                                    prob=self.prob, separation=loaded_data['sep'], save=False,
                                                    path=loaded_data['path'])

        # get number of rows in table
        new_row = self.report.rowCount()
        x0 = new_row - 1
        # check whether this (last) row is empty
        item = self.report.item(x0, 0)
        x = x0 if not item or not item.text() else x0 + 1

        # add the number of rows according to index in self.res
        self.report.setRowCount(len(self.res.index))

        # fill in the results into the table
        for k in range(len(self.res.index)):
            itemGrp = QTableWidgetItem(str(k))
            itemGrp.setTextAlignment(Qt.AlignRight)

            item = QTableWidgetItem(str(self.res.loc[self.res.index[k]][0].split(' ')[-1]))
            item.setTextAlignment(Qt.AlignRight)
            item1 = QTableWidgetItem(str(self.res.loc[self.res.index[k]][1]))
            item1.setTextAlignment(Qt.AlignRight)
            item2 = QTableWidgetItem(str(self.res.loc[self.res.index[k]][2]))
            item2.setTextAlignment(Qt.AlignRight)

            # item structure: row, table, content
            self.report.setItem(x, 0, item)
            self.report.setItem(x, 1, item1)
            self.report.setItem(x, 2, item2)

            # go to the next row
            x += 1

        # adjust table header to its content
        header = self.report.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        # size policy
        self.report.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.report.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)  # +++

        # adjust table to its content
        self.report.resizeRowsToContents(), self.report.adjustSize()

    def process_results(self):
        global results
        limit, self.summary, self.summary_, self.sample, self.sample_plot = 1E-6, [], [], [], []
        for el in range(len(self.prob)):
            for k in range(len(self.prob[0])):
                if self.prob[el].values[k][0] > limit:
                    self.sample.append(el)
                    self.summary.append(self.prob[el].index[k])
                    self.summary_.append(float(self.prob[el].values[k]))

                    if el not in self.sample_plot:
                        self.sample_plot.append(el)
                        self.color = self.d['LDA1'].copy()
                        for coords in self.d.index:
                            self.color[coords] = self.colorclass_dict[coords]

                        if self.score_type == 2:
                            self.plot_distribution_2d(f=self.figScore, ax=self.axScore, alg_group=self.alg_group,
                                                      df_score=self.df_score.loc[self.df_score.index[el], :], d=self.d,
                                                      alg_phylum=self.alg_phylum, phyl_group=self.phyl_group,
                                                      separation=loaded_data['sep'])
                        else:
                            self.plot_distribution_3d(f=self.figScore, ax=self.axScore, separation=loaded_data['sep'],
                                                      df_score=self.df_score.loc[self.df_score.index[el], :], d=self.d,
                                                      alg_group=self.alg_group, alg_phylum=self.alg_phylum,
                                                      phyl_group=self.phyl_group)
                        self.figScore.canvas.draw()

                    else:
                        self.color = self.d['LDA1'].copy()
                        for coords in self.d.index:
                            self.color[coords] = self.colorclass_dict[coords]

        # allow histogram button now as we have the pigment pattern
        self.histo_button.setEnabled(True)
        results['score plot'] = self.figScore

    def plot_distribution_2d(self, f, ax, d, df_score, alg_group, alg_phylum, phyl_group, separation):
        ax.cla()
        # preparation of figure plot
        if ax is None:
            f, ax = plt.subplots()

        # plotting the centers of each algal class
        for el in d.index:
            ax.scatter(d.loc[el, d.columns[0]], d.loc[el, d.columns[1]], facecolor=self.color[el], edgecolor='k', s=6,
                       lw=0.25)

        # calculate the standard deviation within one class to built up a solid (sphere with 3 different radii)
        # around the centroid using spherical coordinates
        ls_xrange, ls_yrange = list(), list()
        for i in d.index:
            # replace sample name (phyl_group.index) with phylum name (in phyl_group['phylum_label'])
            phyl = alg_group[alg_group[separation] == i]['phylum'].values[0]
            if phyl in phyl_group['phylum_label'].values:
                pass
            else:
                phyl_group.loc[i, 'phylum_label'] = phyl
                if isinstance(alg_phylum.loc[phyl, :].values, np.ndarray):
                    phyl_group.loc[i, 'color'] = alg_phylum.loc[phyl, :].values[0]
                else:
                    phyl_group.loc[i, 'color'] = alg_phylum.loc[phyl, :].values

            rx = np.sqrt(d['LDA1var'].loc[i])
            ry = np.sqrt(d['LDA2var'].loc[i])
            c_x = d.loc[i]['LDA1']
            c_y = d.loc[i]['LDA2']
            ells = Ellipse(xy=[c_x, c_y], width=rx, height=ry, angle=0, edgecolor=self.color[i], lw=1,
                           facecolor=self.color[i], alpha=0.6, label=i)
            ax.add_artist(ells)
            ells2 = Ellipse(xy=[c_x, c_y], width=2 * rx, height=2 * ry, angle=0, edgecolor=self.color[i], lw=0.25,
                            facecolor=self.color[i], alpha=0.4)
            ax.add_artist(ells2)

            ells3 = Ellipse(xy=[c_x, c_y], width=3 * rx, height=3 * ry, angle=0, edgecolor=self.color[i], lw=0.15,
                            facecolor=self.color[i], alpha=0.1)
            ax.add_artist(ells3)
            # store for x/y scale adjustment
            ls_xrange.append([c_x - rx, c_x + rx]), ls_yrange.append([c_y - ry, c_y + ry])

        # patch = pd.DataFrame(np.zeros(shape=(len(phyl_group), 2)), index=phyl_group.index)
        patch = []
        for i in phyl_group.index:
            patch.append(mpatches.Patch(color=phyl_group.loc[i, 'color'], label=phyl_group.loc[i, 'phylum_label']))
            leg = ax.legend(handles=patch, loc="upper center", bbox_to_anchor=(1.2,.75), frameon=True, fontsize=fs*.75)
        frame = leg.get_frame()
        frame.set_linewidth(0.25)
        ax.set_xlabel('LDA1', fontsize=fs, labelpad=5)
        ax.set_ylabel('LDA2', fontsize=fs, labelpad=5)

        # plotting the sample scores
        df_score = pd.DataFrame(df_score)
        for i in range(len(df_score.columns)):
            ax.plot(df_score.loc['LDA1', df_score.columns[i]], df_score.loc['LDA2', df_score.columns[i]], marker='^',
                    markersize=2, color='orangered', label='')
            # store for x/y scale adjustment
            ls_xrange.append([df_score.loc['LDA1', df_score.columns[i]], df_score.loc['LDA1', df_score.columns[i]]])
            ls_yrange.append([df_score.loc['LDA2', df_score.columns[i]], df_score.loc['LDA2', df_score.columns[i]]])

        # adjust x/y scale
        if np.nanmin(pd.DataFrame(ls_xrange)) < 0:
            min_ = -1*np.abs(np.nanmin(pd.DataFrame(ls_xrange))) * 1.25
        else:
            min_ = np.abs(np.nanmin(pd.DataFrame(ls_xrange))) * 0.85
        ax.set_xlim(min_, np.nanmax(pd.DataFrame(ls_xrange)) * 1.25)

        if np.nanmin(pd.DataFrame(ls_yrange)) < 0:
            min_ = -1*np.abs(np.nanmin(pd.DataFrame(ls_yrange))) * 1.25
        else:
            min_ = np.abs(np.nanmin(pd.DataFrame(ls_yrange))) * 0.85
        ax.set_ylim(min_, np.nanmax(pd.DataFrame(ls_yrange)) * 1.25)
        sns.despine()
        f.subplots_adjust(left=0.15, right=0.75, bottom=0.2, top=0.9)
    
    def plot_distribution_3d(self, f, ax, d, df_score, alg_group, alg_phylum, phyl_group, separation):
        ax.cla()
        # preparation of figure plot
        if ax is None:
            f = plt.figure()
            ax = f.gca(projection='3d')
            ax.set_aspect('auto')
        # initial view of score plot to enhance the separation of algae and cyanos
        ax.view_init(elev=19., azim=-60) # elev=19., azim=-67

        # plotting the centers of each algal class
        for el in d.index:
            ax.scatter(d.loc[el, d.columns[0]], d.loc[el, d.columns[1]], d.loc[el, d.columns[2]], marker='.', color='k',
                       s=6)

        # calculate the standard deviation within one class to built up a solid (sphere with 3 different radii)
        # around the centroid using spherical coordinates
        for i in d.index:
            # replace sample name (phyl_group.index) with phylum name (in phyl_group['phylum_label'])
            phyl = alg_group[alg_group[separation] == i]['phylum'].values[0]
            if phyl in phyl_group['phylum_label'].values:
                pass
            else:
                phyl_group.loc[i, 'phylum_label'] = phyl
                if isinstance(alg_phylum.loc[phyl, :].values, np.ndarray):
                    phyl_group.loc[i, 'color'] = alg_phylum.loc[phyl, :].values[0]
                else:
                    phyl_group.loc[i, 'color'] = alg_phylum.loc[phyl, :].values

            rx = np.sqrt(d['LDA1var'].loc[i])
            ry = np.sqrt(d['LDA2var'].loc[i])
            rz = np.sqrt(d['LDA3var'].loc[i])
            c_x = d.loc[i]['LDA1']
            c_y = d.loc[i]['LDA2']
            c_z = d.loc[i]['LDA3']

            u, v = np.mgrid[0:2 * np.pi:10j, 0:np.pi:20j]
            x = rx * np.cos(u) * np.sin(v) + c_x
            y = ry * np.sin(u) * np.sin(v) + c_y
            z = rz * np.cos(v) + c_z
            ax.plot_wireframe(x, y, z, color=self.color[i], alpha=0.5, linewidth=1, label=phyl)

            x1 = 2 * rx * np.cos(u) * np.sin(v) + c_x
            y1 = 2 * ry * np.sin(u) * np.sin(v) + c_y
            z1 = 2 * rz * np.cos(v) + c_z
            ax.plot_wireframe(x1, y1, z1, color=self.color[i], alpha=0.2, linewidth=1)

            x2 = 3 * rx * np.cos(u) * np.sin(v) + c_x
            y2 = 3 * ry * np.sin(u) * np.sin(v) + c_y
            z2 = 3 * rz * np.cos(v) + c_z
            ax.plot_wireframe(x2, y2, z2, color=self.color[i], alpha=0.15, linewidth=0.5)

        patch = []
        for i in phyl_group.index:
            patch.append(mpatches.Patch(color=phyl_group.loc[i, 'color'], label=phyl_group.loc[i, 'phylum_label']))
            leg = ax.legend(handles=patch, loc="upper center", bbox_to_anchor=(-0.2, 0.9), frameon=True, fancybox=True,
                            fontsize=fs*0.75)
        frame = leg.get_frame()
        frame.set_linewidth(0.25)
        plt.setp(ax.get_xticklabels(), va='center', ha='center', fontsize=fs*0.9)
        plt.setp(ax.get_yticklabels(), va='center', ha='center', fontsize=fs*0.8)
        plt.setp(ax.get_zticklabels(), va='center', ha='center', fontsize=fs*0.8)
        ax.tick_params(axis='z', which='major', pad=-2.5)
        ax.set_xlabel('LDA1', fontsize=fs, labelpad=-10, rotation=-2)
        ax.set_ylabel('LDA2', fontsize=fs, labelpad=-10, rotation=33)
        ax.set_zlabel('LDA3', fontsize=fs, labelpad=-10, rotation=90)

        # plotting the sample scores
        df_score = pd.DataFrame(df_score)
        for i in range(len(df_score.columns)):
            ax.scatter(df_score.loc['LDA1', df_score.columns[i]], df_score.loc['LDA2', df_score.columns[i]],
                       df_score.loc['LDA3', df_score.columns[i]], marker='^', s=2, color='orangered', label='')

        # adjust layout
        f.tight_layout()

    def gather_saving_info(self, path_folder):
        global results, xcoords

        # collect individual information about analysis and sample to be part of the save_name and save in dictionary
        # date / time
        if 'time' not in results.keys():
            results['time'] = datetime.now().strftime("%Y%m%d-%H%M%S")
        # time frame selected
        results['info'] = str(round(xcoords[0], 2)) + '-' + str(round(xcoords[1], 2)) + 'sec'
        # LDA with dinoflagellata prioritized
        results['priority'] = 'Dino-priority' if 'dinophyta' in ls_LDAset else ''
        # peak detection selected
        results['peak'] = True if 'peak detection' in ls_LDAset else False
        # sample name
        results['name'] = loaded_data['name']

        # combine information for save_name
        save_start = path_folder + results['time']
        save_end = results['priority'] + '_split-' + results['info'] + '.txt'
        save_name_sample = save_start + '_scores-' + results['name'] + '_' + save_end
        save_name_training = save_start + '_training-scores_' + save_end
        return save_name_training, save_name_sample

    def save_report(self, feedback=True):
        global loaded_data, xcoords, ls_LDAset, results

        if 'fsave' not in results.keys():
            # open directory to save the image
            results['fsave'] = str(QtWidgets.QFileDialog.getExistingDirectory(parent=self, directory=os.getcwd(),
                                                                              caption='Select Folder for saving'))

        # create report folder in selected directory
        path_folder = results['fsave'] + '/results_scores/'
        if not os.path.exists(path_folder):
            os.makedirs(path_folder)
        save_name_training, save_name_sample = self.gather_saving_info(path_folder)

        # save scores and LDA information
        self.d.to_csv(save_name_training, sep='\t', decimal='.')
        self.df_score.to_csv(save_name_sample, sep='\t', decimal='.')
        _ = algae.linear_discriminant_save(res=self.res, prob_phylum=self.prob_phylum, date=loaded_data['date'],
                                           info=results['info'], name=results['name'], path=results['fsave'],
                                           blank_corr=loaded_data['blank_corr'], peak_detection=results['peak'],
                                           correction=loaded_data['correction'])

        # feedback to user - saving is done
        if feedback is True:
            feedback_user(text="Report successfully saved to folder.", icon=QMessageBox.Information,
                          title='Good Job')
        return

    def save_all(self):
        global loaded_data, xcoords, ls_LDAset, save_type, results

        # saving the report
        self.save_report(feedback=False)

        # prep folder for score plot
        path_folder = results['fsave'] + '/plots/'
        if not os.path.exists(path_folder):
            os.makedirs(path_folder)
        # save score plot
        for t in save_type:
            save_name = path_folder + results['time'] + '_Sample-scores_{}.'.format(loaded_data['name'])
            results['score plot'].savefig(save_name + t, dpi=300, transparent=False)

        # prep folder for pigment pattern
        path_folder2 = results['fsave'] + '/plots/pigmentPattern/'
        if not os.path.exists(path_folder2):
            os.makedirs(path_folder2)

        # generate pigment pattern in case it does not exist yet
        generate_pigment_pattern(mean_pattern=self.mean_corr, ax=None, fig=None)
        # save pigment pattern
        for t in save_type:
            save_name2 = path_folder2 + results['time'] + '_pigmentPattern_{}.'.format(loaded_data['name'])
            results['pigment pattern'].savefig(save_name2 + t, dpi=300, transparent=False)

        # feedback to user - saving is done
        feedback_user(text="Everything successfully saved to the folders.", icon=QMessageBox.Information,
                      title='Successful')


class HistoWindow(QDialog):
    def __init__(self, mean_pattern):
        super().__init__()
        self.initUI()

        # get the transmitted data
        global loaded_data
        self.mean_pattern, led_total = mean_pattern, list(loaded_data['l'].columns)

        # generate pigment pattern plot
        generate_pigment_pattern(mean_pattern=self.mean_pattern, ax=self.ax_histo, fig=self.fig_histo)

        # when checkbox selected, save information in registered field
        self.close_button.clicked.connect(self.close_window)
        self.saveH_button.clicked.connect(self.save_histogram)

    def initUI(self):
        self.setWindowTitle("Histogram - pigment pattern")
        self.setGeometry(650, 180, 600, 500) # x,y position | width , height

        # close window button
        self.close_button = QPushButton('OK', self)
        self.close_button.setFixedWidth(100), self.close_button.setFont(QFont(font_button, fs_font))
        self.saveH_button = QPushButton('Save', self)
        self.saveH_button.setFixedWidth(100), self.saveH_button.setFont(QFont(font_button, fs_font))

        # histogram figure plot
        self.fig_histo, self.ax_histo = plt.subplots()
        self.canvas_histo = FigureCanvasQTAgg(self.fig_histo)
        self.ax_histo.set_xlim(0, 8)
        self.ax_histo.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
        self.led_selection = ['380 nm', '403 nm', '438 nm', '453 nm', '472 nm', '526 nm', '593 nm', '640 nm']
        self.ax_histo.set_xticklabels(self.led_selection, rotation=15)
        self.ax_histo.tick_params(axis='x', which='both', labelsize=fs, width=.3, length=2.5)
        self.ax_histo.tick_params(axis='y', which='both', labelsize=fs, width=.3, length=2.5)
        self.ax_histo.set_xlabel('Wavelength / nm', fontsize=fs)
        self.ax_histo.set_ylabel('Relative signal intensity / rfu', fontsize=fs)
        self.fig_histo.subplots_adjust(left=0.15, right=0.95, bottom=0.2, top=0.9)
        sns.despine()
        self.fig_histo.canvas.draw()

        # creating window layout
        mlayout2 = QVBoxLayout()
        vbox2_top, vbox2_middle, vbox2_bottom = QHBoxLayout(), QHBoxLayout(), QHBoxLayout()
        mlayout2.addLayout(vbox2_top), mlayout2.addLayout(vbox2_middle), mlayout2.addLayout(vbox2_bottom)

        histo_grp = QGroupBox("Pigment pattern")
        grid_plot = QGridLayout()
        histo_grp.setFont(QFont(font_button, fs_grp))
        vbox2_top.addWidget(histo_grp)
        histo_grp.setLayout(grid_plot)

        # include widgets in the layout
        grid_plot.addWidget(self.canvas_histo, 0, 0)

        # ------------------------------------------------------------
        # draw additional "line" to separate navigation/control buttons from plot
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine | QFrame.Raised)
        hline.setLineWidth(2)
        vbox2_middle.addWidget(hline)

        # ------------------------------------------------------------
        # create GroupBox to structure the layout
        button_grp = QGroupBox("")
        grid_button = QGridLayout()
        button_grp.setFont(QFont(font_button, fs_grp))
        vbox2_bottom.addWidget(button_grp)
        button_grp.setLayout(grid_button)

        # include widgets in the layout
        grid_button.addWidget(self.saveH_button, 0, 1)
        grid_button.addWidget(self.close_button, 0, 0)

        # add everything to the window layout
        self.setLayout(mlayout2)

    def save_histogram(self):
        global loaded_data, results
        # actual time to avoid overwriting
        if 'time' not in results.keys():
            results['time'] = datetime.now().strftime("%Y%m%d-%H%M%S")

        # open directory to save the image
        if 'fsave' not in results.keys():
            results['fsave'] = str(QtWidgets.QFileDialog.getExistingDirectory(parent=self, directory=os.getcwd(),
                                                                              caption='Select Folder for saving'))

        if results['fsave']:
            # create report folder in selected directory
            path_save = results['fsave'] + '/plots/pigmentPattern/'
            if not os.path.exists(path_save):
                os.makedirs(path_save)

            for t in save_type:
                save_name = path_save + results['time'] + '_pigmentPattern_{}.'.format(loaded_data['name'])
                results['pigment pattern'].savefig(save_name + t, dpi=300, transparent=False)

            # feedback to user - saving is done
            feedback_user(text="Pigment pattern successfully saved to folder.", icon=QMessageBox.Information,
                          title='Successful')

    def close_window(self):
        self.hide()


class FinalPage(QWizardPage):
    def __init__(self, parent=None):
        super(FinalPage, self).__init__(parent)
        self.setTitle("Final page")
        self.setSubTitle("Thanks for visiting  ·  Tak for besøget\n\nIf you have any questions regarding the "
                         "software or have encountered a bug,  please do not hesitate to contact me at "
                         "info@envipatable.com.\n\n")


def generate_pigment_pattern(mean_pattern, ax=None, fig=None):
    global led_color_dict, results
    if fig is None or ax is None:
        fig, ax = plt.subplots()
        ax.set_xlim(0, 8)
        ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
        led_selection = ['380 nm', '403 nm', '438 nm', '453 nm', '472 nm', '526 nm', '593 nm', '640 nm']
        ax.set_xticklabels(led_selection, rotation=15)
        ax.tick_params(axis='x', which='both', labelsize=fs, width=.3, length=2.5)
        ax.tick_params(axis='y', which='both', labelsize=fs, width=.3, length=2.5)
        ax.set_xlabel('Wavelength / nm', fontsize=fs)
        ax.set_ylabel('Relative signal intensity / rfu', fontsize=fs)

    # normalize average LED intensities
    mean_norm = mean_pattern / mean_pattern.max()
    x = np.arange(len(mean_norm.index))

    # plot pattern
    for k, l in enumerate(mean_norm.index):
        ax.bar(x[k]+0.5, mean_norm.loc[l, :], width=0.9, color=led_color_dict[l])

    # adjust axes
    ax.set_xticklabels(mean_norm.index, rotation=15)
    fig.subplots_adjust(left=0.15, right=0.95, bottom=0.2, top=0.9)

    # draw figure
    sns.despine()
    fig.canvas.draw()
    results['pigment pattern'] = fig


def plot_3DScore_empty(fig=None, ax=None):
    if fig is None:
        fig = plt.figure(figsize=(7, 4))
    if ax is None:
        ax = fig.add_subplot(111, projection='3d')

    # ax = plt.gca()
    ax.set_xlabel('LDA 1', fontsize=fs, labelpad=-7.5)
    ax.set_ylabel('LDA 2', fontsize=fs, labelpad=-7.5)
    ax.set_zlabel('LDA 3', fontsize=fs, labelpad=-5)
    ax.tick_params(axis='x', which='both', labelsize=fs, width=.3, length=2.5, pad=-3.)
    ax.tick_params(axis='y', which='both', labelsize=fs, width=.3, length=2.5, pad=-2.5)
    ax.tick_params(axis='z', which='both', labelsize=fs, width=.3, length=2.5, pad=0)
    ax.view_init(elev=20., azim=-30)
    fig.tight_layout(pad=0.5), sns.despine()
    return fig, ax


def plot_2DScore_empty(fig=None, ax=None):
    if fig is None:
        fig = plt.figure(figsize=(7, 4))
    if ax is None:
        ax = fig.add_subplot(111)
    # ax = plt.gca()
    ax.set_xlabel('LDA 1', fontsize=fs)
    ax.set_ylabel('LDA 2', fontsize=fs)
    ax.tick_params(axis='x', which='both', labelsize=fs, width=.3, length=2.5)
    ax.tick_params(axis='y', which='both', labelsize=fs, width=.3, length=2.5)
    fig.tight_layout(pad=2), sns.despine()
    fig.canvas.draw()
    return fig, ax


def feedback_user(text, icon, title):
    msgBox = QMessageBox()
    msgBox.setIcon(icon)
    msgBox.setText(text)
    msgBox.setFont(QFont(font_button, fs_font))
    msgBox.setWindowTitle(title)
    msgBox.setStandardButtons(QMessageBox.Ok)

    returnValue = msgBox.exec()
    if returnValue == QMessageBox.Ok:
        pass


# -----------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    # application style options: 'Breeze', 'Oxygen', 'QtCurve', 'Windows', 'Fusion'
    app.setStyle('QtCurve')
    app.setWindowIcon(QIcon('ALPACA_icon.jpg'))

    alpaca = MagicWizard()
    # screen Size adjustment
    screen = app.primaryScreen()
    rect = screen.availableGeometry()
    alpaca.setMaximumHeight(int(rect.height() * 0.9))

    # show wizard
    alpaca.show()
    sys.exit(app.exec_())

