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

sns.set_context('paper', font_scale=.5, rc={"lines.linewidth": .25, "axes.linewidth": 0.25, "grid.linewidth": 0.25})
sns.set_style('ticks', {"xtick.direction": "in", "ytick.direction": "in"})

#sns.set_palette("colorblind", 10)

# global parameters
fs = 5          # font size in plot figures
fs_font = 11    # font size for buttons, etc. in window layout
led_color_dict = {"380 nm": '#610061', "403 nm": '#8300BC', "438 nm": '#0A00FF', "453 nm": '#0057FF',
                  "472 nm": '#00AEFF', "526 nm": '#00FF17', "544 nm": '#8CFF00', "593 nm": '#FFD500',
                  "640 nm": '#FF2100'}


class Gui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.xcoords = []

    def initUI(self):
        # creating main window
        w = QWidget()
        self.setCentralWidget(w)
        # main window layout - x-loc on screen, y-loc on  screen, width, height
        self.setGeometry(50, 50, 300, 100)

        # self.setMinimumSize(1500, 750)
        self.setWindowTitle('LDA for algae classification')
        self.setWindowIcon(QtGui.QIcon('ALPACA_icon.jpg'))

        # invisible structure of main window (=grid) - box with horizontal alignment
        hbox = QHBoxLayout(w)

        # box with vertical alignment
        vbox_left, vbox_middle, vbox_right = QVBoxLayout(), QVBoxLayout(), QVBoxLayout()
        hbox.addLayout(vbox_left), hbox.addLayout(vbox_middle), hbox.addLayout(vbox_right)

        hbox_top, hbox_bottom = QHBoxLayout(), QHBoxLayout()

    # -----------------------------------------------------------------------------------------------------------------
        # left side of main window (-> data treatment)
        vbox_left.addWidget(w)
        vbox_left.setContentsMargins(5, 10, 10, 10)

    # ----------------------------------------------------------------------
        # INPUT load files
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

        # connect button with function (read_csv and do stuff)
        self.load_sample_button.clicked.connect(self.open_sample)
        self.load_blank_button.clicked.connect(self.open_blank)
        self.load_database_button.clicked.connect(self.open_database)
        self.load_ex_correction_button.clicked.connect(self.open_ex_calibration)
        self.load_em_correction_button.clicked.connect(self.open_em_calibration)

        # Text-box displaying chosen files
        self.sample_edit = QTextEdit(self)
        self.sample_edit.setReadOnly(True), self.sample_edit.setMaximumSize(200, 20)
        self.sample_edit.setFont(QFont('Helvetica Neue', fs_font)), self.sample_edit.setAlignment(Qt.AlignRight)
        self.blank_edit = QTextEdit(self)
        self.blank_edit.setReadOnly(True), self.blank_edit.setMaximumSize(200, 20)
        self.blank_edit.setFont(QFont('Helvetica Neue', fs_font)), self.blank_edit.setAlignment(Qt.AlignRight)
        self.database_edit = QTextEdit(self)
        self.database_edit.setReadOnly(True), self.database_edit.setMaximumSize(200, 20)
        self.fname_database = 'supplementary/trainingdatabase/20170829_trainignsmatrix_corrected_norm-to-max.txt'
        self.database_edit.append('trainingsmatrix_corrected')
        self.database_edit.setFont(QFont('Helvetica Neue', fs_font)), self.database_edit.setAlignment(Qt.AlignRight)
        self.ex_correction_edit = QTextEdit(self)
        self.ex_correction_edit.setReadOnly(True), self.ex_correction_edit.setMaximumSize(200, 20)
        self.ex_correction_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.ex_correction_edit.setAlignment(Qt.AlignRight)
        self.em_correction_edit = QTextEdit(self)
        self.em_correction_edit.setReadOnly(True), self.em_correction_edit.setFixedSize(200, 20)
        self.em_correction_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.em_correction_edit.setAlignment(Qt.AlignRight)

        # create buttons to clear data
        self.clear_all_button = QPushButton('Clear all', self)
        self.clear_all_button.setFont(QFont('Helvetica Neue', fs_font))

        # connect button with function (read_csv and do stuff)
        self.clear_all_button.clicked.connect(self.clear_all)

        # create GroupBox to structure the layout
        load_data_group = QGroupBox("Load data")
        load_data_group.setMaximumWidth(400), load_data_group.setMaximumHeight(280)
        grid_load = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_left.addWidget(load_data_group)
        load_data_group.setLayout(grid_load)

        grid_load.addWidget(self.load_sample_button, 0, 0)
        grid_load.addWidget(self.load_blank_button, 1, 0)
        grid_load.addWidget(self.load_database_button, 2, 0)
        grid_load.addWidget(self.load_ex_correction_button, 3, 0)
        grid_load.addWidget(self.load_em_correction_button, 4, 0)

        grid_load.addWidget(self.sample_edit, 0, 1)
        grid_load.addWidget(self.blank_edit, 1, 1)
        grid_load.addWidget(self.database_edit, 2, 1)
        grid_load.addWidget(self.ex_correction_edit, 3, 1)
        grid_load.addWidget(self.em_correction_edit, 4, 1)
        grid_load.addWidget(self.clear_all_button, 5, 0)

        load_data_group.setContentsMargins(5, 5, 5, 5)
        vbox_left.addSpacing(1)

    # -----------------------------------------------------------------------------------------------------------------
        # Choice of LEDs used for evaluation
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

        # create GroupBox to structure the layout
        led_selection_group = QGroupBox("LED selection for analysis")
        led_selection_group.setMaximumHeight(100)
        grid_led = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_left.addWidget(led_selection_group)
        led_selection_group.setLayout(grid_led)

        grid_led.addWidget(self.LED526_checkbox, 0, 0)
        grid_led.addWidget(self.LED438_checkbox, 1, 0)
        grid_led.addWidget(self.LED593_checkbox, 0, 1)
        grid_led.addWidget(self.LED453_checkbox, 1, 1)
        grid_led.addWidget(self.LED380_checkbox, 0, 2)
        grid_led.addWidget(self.LED472_checkbox, 1, 2)
        grid_led.addWidget(self.LED403_checkbox, 0, 3)
        grid_led.addWidget(self.LED640_checkbox, 1, 3)

        led_selection_group.setContentsMargins(5, 20, 5, 7)
        vbox_left.addSpacing(1)

    # -----------------------------------------------------------------------------------------------------------------
        # Parameter of choice for analysis
        # create Checkbox and LineEdit for parameter of choice
        self.blank_cor_checkbox = QCheckBox('Blank correction', self)
        self.blank_cor_checkbox.toggle(), self.blank_cor_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.blank_externalfile_checkbox = QCheckBox('External blank', self)
        self.blank_externalfile_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.correction_checkbox = QCheckBox('Em-/Ex correction', self)
        self.correction_checkbox.toggle(), self.correction_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.calibration_linearfit_checkbox = QCheckBox('LED-calib. 30-50mA', self)
        self.calibration_linearfit_checkbox.toggle()
        self.calibration_linearfit_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.peak_detect_checkbox = QCheckBox('Peak detection (LoD)', self)
        self.peak_detect_checkbox.toggle(), self.peak_detect_checkbox.setFont(QFont('Helvetica Neue', fs_font))

        self.priority_checkbox = QCheckBox('Dinophyta priority', self)
        self.priority_checkbox.toggle(), self.priority_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.normalize_checkbox = QCheckBox('Normalize data', self)
        self.normalize_checkbox.toggle(), self.normalize_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.standardize_checkbox = QCheckBox('Standardize data', self)
        self.standardize_checkbox.toggle(), self.standardize_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.threedimensional_plot_checkbox = QCheckBox('3D score plot', self)
        self.threedimensional_plot_checkbox.toggle()
        self.threedimensional_plot_checkbox.setFont(QFont('Helvetica Neue', fs_font))
        self.twodimensional_plot_checkbox = QCheckBox('2D score plot', self)
        self.twodimensional_plot_checkbox.setFont(QFont('Helvetica Neue', fs_font))

        if self.threedimensional_plot_checkbox.checkState() != 2:
            self.twodimensional_plot_checkbox.toggle()

        # connect button with function (read_csv and do stuff)
        self.blank_cor_checkbox.stateChanged.connect(self.reportInput_blank_correction)
        self.blank_externalfile_checkbox.stateChanged.connect(self.reportInput_external_blank)
        self.correction_checkbox.stateChanged.connect(self.reportInput_correction)
        self.calibration_linearfit_checkbox.stateChanged.connect(self.reportInput_led_calibration_fit)
        self.peak_detect_checkbox.stateChanged.connect(self.reportInput_LoD)
        self.priority_checkbox.stateChanged.connect(self.reportInput_priority)
        self.normalize_checkbox.stateChanged.connect(self.reportInput_normalize)
        self.standardize_checkbox.stateChanged.connect(self.reportInput_standardize)
        self.threedimensional_plot_checkbox.stateChanged.connect(self.reportInput_threedimensional)
        self.twodimensional_plot_checkbox.stateChanged.connect(self.reportInput_twodimensional)

        # Input parameter for analysis
        grid_input_para = QGridLayout()
        vbox_left.addLayout(grid_input_para)

        pumprate_label, pumprate_unit_label = QLabel(self), QLabel(self)
        pumprate_label.setText('Pump rate'), pumprate_unit_label.setText('mL/min')
        pumprate_label.setFont(QFont('Helvetica Neue', fs_font))
        pumprate_unit_label.setFont(QFont('Helvetica Neue', fs_font))
        self.pumprate_edit = QLineEdit(self)
        self.pumprate_edit.setValidator(QtGui.QDoubleValidator())
        self.pumprate_edit.setAlignment(Qt.AlignRight)
        self.pumprate_edit.setText('1.5'), self.pumprate_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.pumprate_edit.setMaximumWidth(75)

        separation_label = QLabel(self)
        separation_label.setText('Separation level'), separation_label.setFont(QFont('Helvetica Neue', fs_font))
        self.separation_edit = QLineEdit(self)
        self.separation_edit.setText('order'), self.separation_edit.setFont(QFont('Helvetica Neue', fs_font))
        self.separation_edit.setAlignment(Qt.AlignRight)
        self.separation_edit.setMaximumWidth(75)

        # connect LineEdit with function (read_csv and do stuff)
        self.pumprate_edit.editingFinished.connect(self.print_pumprate)
        self.separation_edit.editingFinished.connect(self.print_separation)

        # create GroupBox to structure the layout
        set_parameter_group = QGroupBox("Parameter of choice")
        set_parameter_group.setMaximumWidth(400), set_parameter_group.setMaximumHeight(250)
        grid_parameter = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_left.addWidget(set_parameter_group)
        set_parameter_group.setLayout(grid_parameter)

        grid_parameter.addWidget(self.blank_cor_checkbox, 0, 0)
        grid_parameter.addWidget(self.blank_externalfile_checkbox, 0, 2)
        grid_parameter.addWidget(self.correction_checkbox, 1, 0)
        grid_parameter.addWidget(self.calibration_linearfit_checkbox, 1, 2)
        grid_parameter.addWidget(self.peak_detect_checkbox, 2, 0)
        grid_parameter.addWidget(self.priority_checkbox, 2, 2)
        grid_parameter.addWidget(self.normalize_checkbox, 3, 0)
        grid_parameter.addWidget(self.standardize_checkbox, 3, 2)
        grid_parameter.addWidget(self.threedimensional_plot_checkbox, 4, 0)
        grid_parameter.addWidget(self.twodimensional_plot_checkbox, 4, 2)

        grid_parameter.addWidget(pumprate_label, 6, 0)
        grid_parameter.addWidget(pumprate_unit_label, 6, 2)
        grid_parameter.addWidget(self.pumprate_edit, 6, 1)
        grid_parameter.addWidget(separation_label, 14, 0)
        grid_parameter.addWidget(self.separation_edit, 14, 1)

        set_parameter_group.setContentsMargins(5, 20, 5, 7)
        vbox_left.addSpacing(1)

        # -----------------------------------------------------------------------------------------------------------------
        # vertical line to visualise the different sections
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine | QFrame.Raised)
        vline.setLineWidth(2)
        vbox_middle.addWidget(vline)

    # -----------------------------------------------------------------------------------------------------------------
        # OUTPUT save stuff and information box for evaluation
        # create Buttons
        self.load_timedrive_button = QPushButton('Display sample file', self)
        self.load_timedrive_button.setFont(QFont('Helvetica Neue', fs_font))
        self.run_button = QPushButton('Run analysis', self)
        self.run_button.setEnabled(False), self.run_button.setFont(QFont('Helvetica Neue', fs_font))
        self.save_report_button = QPushButton('Save report', self)
        self.save_report_button.setEnabled(False), self.save_report_button.setFont(QFont('Helvetica Neue', fs_font))
        self.save_all_button = QPushButton('Save all', self)
        self.save_all_button.setEnabled(False), self.save_all_button.setFont(QFont('Helvetica Neue', fs_font))

        # connect button with function (read_csv and do stuff)
        self.load_timedrive_button.clicked.connect(self.load_timedrive)
        self.run_button.clicked.connect(self.run_analysis)
        self.save_report_button.clicked.connect(self.save_report)
        self.save_all_button.clicked.connect(self.save_all)

        # create GroupBox to structure the layout
        run_and_save_group = QGroupBox("Evaluation")
        run_and_save_group.setFixedWidth(400), run_and_save_group.setFixedHeight(100)
        grid_run_and_save = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_left.addWidget(run_and_save_group)
        run_and_save_group.setLayout(grid_run_and_save)

        # add GroupBox to layout and load buttons in GroupBox
        grid_run_and_save.addWidget(self.load_timedrive_button, 0, 0)
        grid_run_and_save.addWidget(self.run_button, 0, 1)
        grid_run_and_save.addWidget(self.save_report_button, 1, 0)
        grid_run_and_save.addWidget(self.save_all_button, 1, 1)

        run_and_save_group.setContentsMargins(5, 10, 5, 7)
        vbox_left.addSpacing(1)

        # Message box
        self.message = QTextEdit(self)
        self.message.setReadOnly(True)

        # create GroupBox to structure the layout
        message_group = QGroupBox("Message box")
        message_group.setFixedSize(400, 100)
        grid_message = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_left.addWidget(message_group)
        message_group.setLayout(grid_message)
        grid_message.addWidget(self.message)

    # ----------------------------------------------------------------------------------------------------------------
        # full right side of main window
        # right side top
        vbox_right.addWidget(w)
        vbox_right.addLayout(hbox_top)

        # Figure | HLine | Figure
        vbox_top_left, vbox_top_right = QVBoxLayout(), QVBoxLayout()
        hbox_top.addLayout(vbox_top_left), hbox_top.addLayout(vbox_top_right)

        # Plot for time-drive plot
        self.fig_timedrive, self.ax_timedrive = plt.subplots() #figsize=(3, 4))
        self.canvas_timedrive = FigureCanvasQTAgg(self.fig_timedrive)
        # self.navi_timedrive = NavigationToolbar2QT(self.canvas_timedrive, w)
        self.ax_timedrive.set_xlim(0, 10)
        self.ax_timedrive.set_xlabel('Time [s]', fontsize=fs)
        self.ax_timedrive.set_ylabel('Rel. Intensity [pW]', fontsize=fs)
        self.fig_timedrive.subplots_adjust(left=0.15, right=0.85, bottom=0.19, top=0.85)
        sns.despine()

        # connect onclick event with function
        self.fig_timedrive.canvas.mpl_connect('button_press_event', self.onclick_timedrive)

        # Text-box for report (right side in right half of main window)
        self.report = QTableWidget(self)
        # self.report_sup = QTableWidget(self)

        # create GroupBox to structure the layout
        timedriveplot_group = QGroupBox("Time drive plot of sample")
        timedriveplot_group.setMinimumSize(300, 350)
        grid_timedriveplot = QGridLayout()
        result_report_group = QGroupBox("Report results")
        result_report_group.setMinimumSize(300, 350)
        grid_report = QGridLayout()

    #     # !!!TODO: make a tab out it between which the user can switch
    #     # result_report_sup_group = QGroupBox("Report results superordinate")
    #     # grid_report_sup = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_top_left.addWidget(timedriveplot_group)
        timedriveplot_group.setLayout(grid_timedriveplot)
        grid_timedriveplot.addWidget(self.canvas_timedrive)
        # grid_timedriveplot.addWidget(self.navi_timedrive)

        vbox_top_right.addWidget(result_report_group)
        result_report_group.setLayout(grid_report)
        grid_report.addWidget(self.report)
        # vbox_top_right.addWidget(result_report_sup_group)
        # result_report_sup_group.setLayout(grid_report_sup)
        # grid_report_sup.addWidget(self.report_sup)

        # self.canvas_timedrive.setMaximumWidth(350)
        self.report.adjustSize()
        # self.report_sup.adjustSize()

    # -----------------------------------------------------------------------------------------------------------------
        # right side bottom
        vbox_right.addLayout(hbox_bottom)

        vbox_bottom_left = QVBoxLayout()
        vbox_bottom_right = QVBoxLayout()
        hbox_bottom.addLayout(vbox_bottom_left)
        hbox_bottom.addLayout(vbox_bottom_right)

        # Plot for histogram (left side in right half of main window)
        self.fig_histogram, self.ax_histogram = plt.subplots()# figsize=(5, 3))
        self.canvas_histo = FigureCanvasQTAgg(self.fig_histogram)
        # self.navi_histo = NavigationToolbar2QT(self.canvas_histo, w)
        self.ax_histogram = plt.gca()
        self.ax_histogram.set_xlim(0, 8)
        self.ax_histogram.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
        self.led_selection = ['380 nm', '403 nm', '438 nm', '453 nm', '472 nm', '526 nm', '593 nm', '640 nm']
        self.ax_histogram.set_xticklabels(self.led_selection, rotation=15)
        self.ax_histogram.tick_params(axis='both', labelsize=fs * 0.9)
        self.ax_histogram.set_xlabel('Wavelength [nm]', fontsize=fs)
        self.ax_histogram.set_ylabel('Relative signal intensity [rfu]', fontsize=fs)
        self.fig_histogram.subplots_adjust(left=0.15, right=0.9, bottom=0.18, top=0.85)
        sns.despine()

        # Plot for score plot (right side in right half of main window)
        self.fig_scoreplot = plt.figure()# figsize=(5, 3))
        if self.threedimensional_plot_checkbox.isChecked():
            # 3D Plot
            self.ax_scoreplot = self.fig_scoreplot.gca(projection='3d')
            self.ax_scoreplot.view_init(elev=16., azim=57)
            self.canvas_score = FigureCanvasQTAgg(self.fig_scoreplot)
            # self.navi_score = NavigationToolbar2QT(self.canvas_score, w)
            self.ax_scoreplot = plt.gca()
            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=-8)
            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=-8)
            self.ax_scoreplot.set_zlabel('LDA 3', fontsize=fs, labelpad=-8)
            self.ax_scoreplot.tick_params(axis='both', pad=-2, labelsize=fs*0.9)
            self.fig_scoreplot.tight_layout() #subplots_adjust(left=0.15, right=0.9, bottom=0.18, top=0.85)
        else:
            # 2D Plot
            self.ax_scoreplot = self.fig_scoreplot.add_subplot(111)
            self.canvas_score = FigureCanvasQTAgg(self.fig_scoreplot)
            # self.navi_score = NavigationToolbar2QT(self.canvas_score, w)
            self.ax_scoreplot = plt.gca()
            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=2)
            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=2)
            self.fig_scoreplot.subplots_adjust(left=0.10, right=0.9, bottom=0.18, top=0.85)

        # create GroupBox to structure the layout
        result_histogram_group = QGroupBox("Histogram")
        result_histogram_group.setMinimumSize(400, 350)
        grid_histogram = QGridLayout()
        result_scoreplot_group = QGroupBox("Score plot")
        result_scoreplot_group.setMinimumSize(300, 350)
        grid_scoreplot = QGridLayout()

        # add GroupBox to layout and load buttons in GroupBox
        vbox_bottom_left.addWidget(result_histogram_group)
        result_histogram_group.setLayout(grid_histogram)
        grid_histogram.addWidget(self.canvas_histo)
        # grid_histogram.addWidget(self.navi_histo)

        vbox_bottom_right.addWidget(result_scoreplot_group)
        result_scoreplot_group.setLayout(grid_scoreplot)
        grid_scoreplot.addWidget(self.canvas_score)
        # grid_scoreplot.addWidget(self.navi_score)

        self.show()

###################################################################################################################
# Functions for analysis
###################################################################################################################
    # Load or define input parameter
    def open_sample(self):
        self.fname = QFileDialog.getOpenFileName(self, "Select a measurement file", 'measurement/')[0]
        if not self.fname:
            return
        self.read_sample_name(self.fname)

    def read_sample_name(self, fname):
        try:
            sample_file = fname.split('/')[-1]
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
        if self.blank_edit.toPlainText():
            self.blank_externalfile_checkbox.toggle()

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

    def open_prescan(self):
        self.fname_prescan = QFileDialog.getOpenFileName(self, "Select a blank file", "measurement/")[0]
        if not self.fname_prescan:
            return
        self.read_prescan_name(self.fname_prescan)
        if self.prescan_edit.toPlainText():
            print(self.prescan_edit.toPlainText())

    def read_prescan_name(self, fname_prescan):
        try:
            name_sample = fname_prescan.split('/')[-1].split('.')[0].split('_')[1]
            date_sample = fname_prescan.split('/')[-1].split('.')[0].split('_')[0]
            xcoords_sample = fname_prescan.split('/')[-1].split('.')[0].split('_')[2]
        except:
            blank_load_failed = QMessageBox()
            blank_load_failed.setIcon(QMessageBox.Information)
            blank_load_failed.setText("Invalid sample file!")
            blank_load_failed.setInformativeText("Choose another file from path...")
            blank_load_failed.setWindowTitle("Error!")
            blank_load_failed.buttonClicked.connect(self.open_prescan)
            blank_load_failed.exec_()
            return

        self.name_sample = name_sample
        self.date_sample = date_sample
        self.xcoords_prescan = xcoords_sample
        self.prescan_edit.setText(str(self.date_sample + '_' + self.name_sample + '_' + self.xcoords_prescan))

    def open_database(self):
        self.fname_database = None
        self.fname_database = QFileDialog.getOpenFileName(self, "Select Training database",
                                                          "supplementary/trainingdatabase")[0]

        if not self.fname_database:
            return
        self.read_database_name(self.fname_database)
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

    def clear_data_sample(self):
        self.sample_edit.clear()
        self.fname_sample = None

    def clear_data_blank(self):
        self.blank_edit.clear()
        self.blank_externalfile_checkbox.setCheckState(False)
        self.fname_blank = None

    def clear_data_prescan(self):
        self.prescan_edit.clear()
        self.fname_prescan = None
        self.xcoords_prescan = None

    def clear_database(self):
        self.database_edit.clear()
        self.fname_database = None

    def clear_ex_correction(self):
        self.ex_correction_edit.clear()
        self.fname_ex = None

    def clear_em_correction(self):
        self.em_correction_edit.clear()
        self.fname_em = None

    def clear_all(self):
        self.sample_edit.clear()
        self.blank_edit.clear()
        self.database_edit.clear()
        self.ex_correction_edit.clear()
        self.em_correction_edit.clear()
        if self.xcoords:
            self.xcoords.clear()

    def reportInput_blank_correction(self):
        print('blank correction: ', self.blank_cor_checkbox.isChecked())
        return self.blank_cor_checkbox.isChecked()

    def reportInput_external_blank(self):
        print('external blank: ', self.blank_externalfile_checkbox.isChecked())
        return self.blank_externalfile_checkbox.isChecked()

    def reportInput_correction(self):
        print('em-/ex-correction: ', self.correction_checkbox.isChecked())

    def reportInput_led_calibration_fit(self):
        print('led-calibration fit linear:', self.calibration_linearfit_checkbox.isChecked())
        return self.calibration_linearfit_checkbox.isChecked()

    def reportInput_priority(self):
        print('Priority for dinophyta: ', self.priority_checkbox.isChecked())
        return self.priority_checkbox.isChecked()

    def reportInput_normalize(self):
        print('data normalization: ', self.normalize_checkbox.isChecked())
        return self.normalize_checkbox.isChecked()

    def reportInput_standardize(self):
        print('data standardization: ', self.standardize_checkbox.isChecked())
        return self.standardize_checkbox.isChecked()

    def reportInput_threedimensional(self):
        print('3D plot for score plot: ', self.threedimensional_plot_checkbox.isChecked())
        if self.threedimensional_plot_checkbox.isChecked() == True:
            self.twodimensional_plot_checkbox.setCheckState(False)
        return self.threedimensional_plot_checkbox.isChecked()

    def reportInput_twodimensional(self):
        print('2D plot for score plot: ', self.twodimensional_plot_checkbox.isChecked())
        if self.twodimensional_plot_checkbox.isChecked() == True:
            self.threedimensional_plot_checkbox.setCheckState(False)
        return self.twodimensional_plot_checkbox.isChecked()

    def reportInput_LoD(self):
        print('peak detection with LoD ', self.peak_detect_checkbox.isChecked())
        return self.peak_detect_checkbox.isChecked()

    def print_pumprate(self):
        print('Pumprate: ', self.pumprate_edit.text(), 'mL/min')
        return self.pumprate_edit.text()

    def print_separation(self):
        if self.separation_edit.text() == 'phylum' or self.separation_edit.text() == 'order':
            print('Separation level: ', self.separation_edit.text())
            return self.separation_edit.text()
        elif self.separation_edit.text() == 'family' or self.separation_edit.text() == 'class':
            print('Separation level: ', self.separation_edit.text())
            return self.separation_edit.text()
        else:
            separation_level_failed = QMessageBox()
            separation_level_failed.setIcon(QMessageBox.Information)
            separation_level_failed.setText("Invalid separation level!")
            separation_level_failed.setInformativeText("Choose either 'phylum', 'class', 'order' or 'family' ... ")
            separation_level_failed.setWindowTitle("Error!")
            separation_level_failed.exec_()
            return

    def print_limit(self):
        print('Limit for score plot: ', self.limit_edit.text())
        return self.limit_edit.text()

    def onclick_timedrive(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers != Qt.ControlModifier:  # change selected range
            return
        if len(self.xcoords) >= 4:
            return
        if event.xdata == None:
            if len(self.xcoords) < 2:
                event.xdata = self.loaded_data['l_corr'].index.max()
            else:
                event.xdata = 0
        self.xcoords.append(event.xdata)
        self.ax_timedrive.vlines(x=self.xcoords, ymin=self.loaded_data['l_corr'].min().min(),
                                 ymax=self.loaded_data['l_corr'].max().max(), lw=0.5)
        if len(self.xcoords) == 2:
            self.ax_timedrive.axvspan(self.xcoords[0], self.xcoords[1], color='grey', alpha=0.3)
        elif len(self.xcoords) == 4:
            self.ax_timedrive.axvspan(self.xcoords[0], self.xcoords[1], color='grey', alpha=0.3)
            self.ax_timedrive.axvspan(self.xcoords[2], self.xcoords[3], color='grey', alpha=0.3)
        self.fig_timedrive.canvas.draw()

    def plot_timedrive(self, df, name, date, ax, f, unit):
        color_LED = []
        for i in df.columns:
            color_LED.append(led_color_dict[i])

        # plotting spectra
        ylim_max = pd.DataFrame(np.zeros(shape=(len(df.columns), 1)), index=df.columns).T
        ylim_min = pd.DataFrame(np.zeros(shape=(len(df.columns), 1)), index=df.columns).T

        for c, p in zip(color_LED, df):
            if df[p].dropna().empty is True:
                df[p][np.isnan(df[p])] = 0
                df[p].plot(ax=ax, color=c, linewidth=1.5)
            else:
                df[p].dropna().plot(ax=ax, color=c, label=p, linewidth=1.5)
                ylim_max[p] = df[p].dropna().max()
                ylim_min[p] = df[p].dropna().min()

        # General layout-stuff
        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Rel. Fluorescence intensity [rfu]')
        ax.legend(loc=0, ncol=1, frameon=True, fancybox=True, framealpha=0.5, fontsize=fs*0.4)

        # Define plotting area. Default is 2 but if max value is higher it has to be rearranged
        y_max = ylim_max.max(axis=1).values[0] * 1.05
        y_min = ylim_min.min(axis=1).values[0] * 1.05
        ax.set_ylim(y_min, y_max)
        ax.set_title("{} {}/{}/{} {}:{}h - \n Select time range for sample and "
                     "blank.".format(name, date[6:8], date[4:6], date[:4], date[8:10], date[10:12]),
                     fontsize=fs*0.9)

        f.tight_layout()
        f.canvas.draw()

    def plot_histogram(self, mean, ax, f):
        # plot histogram: Relative intensity @ different excitation LEDs.
        mean = mean.sort_index()

       # prepare general information about the sample and the setup
        LED_color, LED_wl = [], []
        for i in mean.index:
            if type(i) == str:
                if len(i.split(' ')) == 1:
                    # led as string without 'nm'
                    j = i + ' nm'
                else:
                    # led with 'nm'
                    j = i
            else:
                j = str(i) + ' nm'
            LED_wl.append(j)
            LED_color.append(led_color_dict[j])

        mean.index = LED_wl

        # normalize mean
        means = mean / mean.max()
        for i in means.index:
            if (means.loc[i, :].values[0]) < 0:
                means.loc[i, :].values[0] = 0

        self.led_total = pd.DataFrame(self.led_selection)
        x = []
        for i in mean.index:
            x.append(self.led_total[self.led_total[0] == i].index[0])

        for k, l in enumerate(mean.index):
            ax.bar(x[k]+0.5, means.loc[l, :], width=0.9, color=LED_color[k])
        ax = plt.gca()
        ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
        ax.set_xticklabels(mean.index)
        ax.xaxis.grid(False)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='center')

        ax.set_xlabel('Wavelength [nm]')
        ax.set_ylabel('Relative signal intensity [rfu]')
        f.tight_layout()

        f.canvas.draw()

    def plot_distribution_2d(self, f, ax, d, df_score, color, alg_group, alg_phylum, phyl_group, separation):
        ax.cla()
        # preparation of figure plot
        if ax is None:
            f, ax = plt.subplots()

        # plotting the centers of each algal class
        for el in d.index:
            ax.scatter(d.loc[el, 0], d.loc[el, 1], facecolor=color[el], edgecolor='k', s=60)

        # calculate the standard deviation within one class to built up a solid (sphere with 3 different radii)
        # around the centroid using spherical coordinates
        for i in d.index:
            # replace sample name (phyl_group.index) with phylum name (in phyl_group['phylum_label'])
            phyl = alg_group[alg_group[separation] == i]['phylum'].values[0]
            if phyl in phyl_group['phylum_label'].values:
                pass
            else:
                phyl_group.loc[i, 'phylum_label'] = phyl
                phyl_group.loc[i, 'color'] = alg_phylum.loc[phyl, :].values

            rx = np.sqrt(d['LDA1var'].loc[i])
            ry = np.sqrt(d['LDA2var'].loc[i])
            c_x = d.loc[i]['LDA1']
            c_y = d.loc[i]['LDA2']
            ells = Ellipse(xy=[c_x, c_y], width=rx, height=ry, angle=0, edgecolor=color[i], lw=1, facecolor=color[i],
                           alpha=0.6, label=i)
            ax.add_artist(ells)

            ells2 = Ellipse(xy=[c_x, c_y], width=2*rx, height=2*ry, angle=0, edgecolor=color[i], lw=1,
                            facecolor=color[i], alpha=0.4)
            ax.add_artist(ells2)

            ells3 = Ellipse(xy=[c_x, c_y], width=3*rx, height=3*ry, angle=0, edgecolor=color[i], lw=0.5,
                            facecolor=color[i], alpha=0.1)
            ax.add_artist(ells3)

        # patch = pd.DataFrame(np.zeros(shape=(len(phyl_group), 2)), index=phyl_group.index)
        patch = []
        for i in phyl_group.index:
            patch.append(mpatches.Patch(color=phyl_group.loc[i, 'color'][0], label=phyl_group.loc[i, 'phylum_label']))
            ax.legend(handles=patch, loc="upper center", bbox_to_anchor=(1.2, 0.9), frameon=True, fontsize=11)

        plt.setp(ax.get_xticklabels(), fontsize=fs*0.5)
        plt.setp(ax.get_yticklabels(), fontsize=fs*0.5)
        ax.set_xlabel('LDA1', fontsize=fs, labelpad=5)
        ax.set_ylabel('LDA2', fontsize=fs, labelpad=5)
        plt.title('')

        # plotting the sample scores
        for i in range(len(df_score.T)):
            ax.plot(df_score.loc[0, 0], df_score.loc[1, 0], marker='^', markersize=14, color='orangered', label='')
        f.subplots_adjust(left=0.1, right=0.75, bottom=0.18, top=0.85)

        f.canvas.draw()

    def plot_distribution_3d(self, f, ax, d, df_score, color, alg_group, alg_phylum, phyl_group, separation):
        ax.cla()
        # preparation of figure plot
        if ax is None:
            f = plt.figure()
            ax = f.gca(projection='3d')
            ax.set_aspect('auto')
        # initial view of score plot to enhance the separation of algae and cyanos
        ax.view_init(elev=19., azim=-67)

        # plotting the centers of each algal class
        for el in d.index:
            ax.scatter(d.loc[el, 0], d.loc[el, 1], d.loc[el, 2], marker='.', color='k', s=60)

        # calculate the standard deviation within one class to built up a solid (sphere with 3 different radii)
        # around the centroid using spherical coordinates
        for i in d.index:

            # replace sample name (phyl_group.index) with phylum name (in phyl_group['phylum_label'])
            phyl = alg_group[alg_group[separation] == i]['phylum'].values[0]
            if phyl in phyl_group['phylum_label'].values:
                pass
            else:
                phyl_group.loc[i, 'phylum_label'] = phyl

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
            ax.plot_wireframe(x, y, z, color=color[i], alpha=0.5, linewidth=1, label=phyl)

            x1 = 2 * rx * np.cos(u) * np.sin(v) + c_x
            y1 = 2 * ry * np.sin(u) * np.sin(v) + c_y
            z1 = 2 * rz * np.cos(v) + c_z
            ax.plot_wireframe(x1, y1, z1, color=color[i], alpha=0.2, linewidth=1)

            x2 = 3 * rx * np.cos(u) * np.sin(v) + c_x
            y2 = 3 * ry * np.sin(u) * np.sin(v) + c_y
            z2 = 3 * rz * np.cos(v) + c_z
            ax.plot_wireframe(x2, y2, z2, color=color[i], alpha=0.15, linewidth=0.5)

        patch = []
        for i in phyl_group.index:
            patch.append(mpatches.Patch(color=phyl_group.loc[i, 'color'][0], label=phyl_group.loc[i, 'phylum_label']))
            ax.legend(handles=patch, loc="upper center", bbox_to_anchor=(0., 0.9), frameon=True, fancybox=True,
                      fontsize=fs*0.6)

        plt.setp(ax.get_xticklabels(), va='center', ha='left', fontsize=fs*0.8)
        plt.setp(ax.get_yticklabels(), va='center', ha='left', fontsize=fs*0.8)
        plt.setp(ax.get_zticklabels(), va='center', fontsize=fs*0.8)

        ax.set_xlabel('LDA1', fontsize=fs, labelpad=16, rotation=-2)
        ax.set_ylabel('LDA2', fontsize=fs, labelpad=14, rotation=18)
        ax.set_zlabel('LDA3', fontsize=fs, labelpad=10, rotation=90)
        plt.title(' ')

        # plotting the sample scores
        for i in range(len(df_score.T)):
            ax.scatter(df_score.loc[0, 0], df_score.loc[1, 0], df_score.loc[2, 0], marker='^', s=300,
                       color='orangered', label='')

        f.subplots_adjust(left=0.1, right=0.9, bottom=0.06, top=0.99)

        f.canvas.draw()


#################################################################################################
#   Load data and select range for sample and blank
#################################################################################################
    def load_timedrive(self):
        self.message.clear()
        self.message.setText(' ')
        self.report.clear()
        # self.report_sup.clear()
        self.ax_timedrive.cla()
        self.ax_timedrive.set_xlim(0, 10)
        self.ax_timedrive.set_xlabel('Time [s]')
        self.ax_timedrive.set_ylabel('Rel. intensity [pW]')
        self.fig_timedrive.canvas.draw()
        self.ax_histogram.cla()
        self.ax_histogram.set_xlim(0, 8)
        self.ax_histogram.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
        self.ax_histogram.set_xticklabels(self.led_selection, rotation=15)
        self.ax_histogram.set_xlabel('Wavelength [nm]')
        self.ax_histogram.set_ylabel('Relative signal intensity [rfu]')
        self.fig_histogram.canvas.draw()

        if self.threedimensional_plot_checkbox.isChecked():
            # 3D Plot redrawing
            self.ax_scoreplot.cla()
            self.fig_scoreplot.clear()
            self.ax_scoreplot = self.fig_scoreplot.gca(projection='3d')
            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=10)
            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=10)
            self.ax_scoreplot.set_zlabel('LDA 3', fontsize=fs, labelpad=10)
            self.fig_scoreplot.subplots_adjust(left=0.1, right=0.9, bottom=0.18, top=0.85)
            self.fig_scoreplot.canvas.draw()
        else:
            # 2D Plot activated
            self.ax_scoreplot.cla()
            self.fig_scoreplot.clear()
            self.ax_scoreplot = self.fig_scoreplot.add_subplot(111)
            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=10)
            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=10)
            self.fig_scoreplot.subplots_adjust(left=0.12, right=0.9, bottom=0.18, top=0.85)
            self.fig_scoreplot.canvas.draw()

        self.fname_prescan = None
        self.xcoords_prescan = None

        # find sample filename
        try:
            self.fname
        except:
            try:
                # if pre-scanned data are analysed
                self.fname_prescan
            except:
                run_sample_load_failed = QMessageBox()
                run_sample_load_failed.setIcon(QMessageBox.Information)
                run_sample_load_failed.setText("Sample file is missing!")
                run_sample_load_failed.setInformativeText("Choose a specific sample file for analysis")
                run_sample_load_failed.setWindowTitle("Error!")
                run_sample_load_failed.exec_()
                return

        # if data should be corrected
        if self.correction_checkbox.isChecked() is True:
            correction = True
            # if correction is chosen, you need the em- and ex- correction files!
            # device for emission correction
            try:
                self.number_em  # number 0, 1, 2, 3
            except:
                run_correction_em_failed = QMessageBox()
                run_correction_em_failed.setIcon(QMessageBox.Information)
                run_correction_em_failed.setText("File for emission correction is missing!")
                run_correction_em_failed.setInformativeText("Choose a correction file for analysis.")
                run_correction_em_failed.setWindowTitle("Error!")
                run_correction_em_failed.exec_()
                return

            # excitation correction
            # linear fit between 30-50mA or whole current between 9-97mA
            if self.calibration_linearfit_checkbox.isChecked() is True:
                full_calibration = False
            else:
                full_calibration = True

            if self.ex_correction_edit.toPlainText():
                # manual choice of correction file!
                # check if the correct file was chosen (spectrum; not reference)
                if self.fname_ex.split('/')[-1].split('_')[4].split('.')[0] == 'reference':
                    self.message.append('Wrong file for LED correction was chosen! '
                                         ' Using spectrum correction instead of reference correction ...')
                    fname_ex_corr = self.fname_ex.split('reference')[0] + 'spectrum' + \
                                    self.fname_ex.split('reference')[1]
                    kappa_spec = fname_ex_corr
                else:
                    kappa_spec = self.fname_ex

            else:
                # automatic choice of correction file
                self.message.append('No specific file for excitation correction is chosen. Choose automatically ...')
                kappa_spec = None
        else:
            # No excitation correction
            correction = False
            device = None
            kappa_spec = None
            self.number_em = 'device-1'
            full_calibration = False

        # pumprate either from file or from GUI
        if not self.pumprate_edit.text():
            self.message.append("No external pump rate defined. Take information from header!")
            pumprate = None
        else:
            pumprate = float(self.pumprate_edit.text())

        # no additional offset compensation when database is updated
        additional = False

        # single event evaluation
        single_events = False

        # peak_detection means LoD is used
        if self.peak_detect_checkbox.isChecked() is True:
            peak_detection = True
        else:
            peak_detection = False

        # other parameter not used in the normal analysis
        ampli = None
        factor = 1

        # blank_corr of data
        if self.blank_cor_checkbox.isChecked() is True:
            blank_correction = True
        else:
            blank_correction = False

        # use external file instead of blank stored in the header
        if self.blank_externalfile_checkbox.isChecked() is True:
            try:
                self.fname_blank
            except:
                run_blank_external_failed = QMessageBox()
                run_blank_external_failed.setIcon(QMessageBox.Information)
                run_blank_external_failed.setText("File for external blank correction is missing!")
                run_blank_external_failed.setInformativeText("Choose an external blank file for analysis.")
                run_blank_external_failed.setWindowTitle("Error!")
                run_blank_external_failed.exec_()
                return
            # blank is not (ex- or em-)corrected so far
            [blank, header_bl, unit_bl] = algae.read_rawdata(filename=self.fname_blank, additional=additional, co=None,
                                                           factor=factor, blank_corr=blank_correction,
                                                           blank_mean_ex=None, blank_std_ex=None, plot_raw=False)
            # convert the blank in nW
            if unit_bl == 'nW':
                blank_mean_ex =blank.mean().tolist()
                blank_std_ex = blank.std().tolist()
            elif unit_bl == 'pW':
                blank_mean_ex =blank.mean().tolist() / 1000
                blank_std_ex = blank.std().tolist() / 1000
                unit_bl = 'nW'
            elif unit_bl == 'µW':
                blank_mean_ex =blank.mean().tolist() * 1000
                blank_std_ex = blank.std().tolist() * 1000
                unit_bl = 'nW'
            else:
                self.message.append('The blank is unusually high! Please check the blank ....')
                return
        else:
            blank_mean_ex = None
            blank_std_ex = None

        # selection of xcoords depending on sample type
        if self.sample_edit.toPlainText():
            # raw data do not have a x-coord selection. the xcoord prescan should be empty
            if self.xcoords_prescan:
                self.xcoords_prescan = None
            if self.xcoords:
                self.xcoords.clear()

            # Load data and correct them with prescan_load_file function.
            [l, l_corr, header, firstline, current, date, self.sample_name, blank_mean, blank_std, blank_corrected,
             rg9_sample, rg665_sample, volume, pumprate, unit, unit_corr, unit_bl,
             path] = algae.prescan_load_file(filename=self.fname, device=self.number_em.split('-')[1],
                                             kappa_spec=kappa_spec, pumprate=pumprate, ampli=ampli,
                                             correction=correction, full_calibration=full_calibration,
                                             blank_corr=blank_correction, factor=factor, blank_mean_ex=blank_mean_ex,
                                             blank_std_ex=blank_std_ex, additional=additional)

            self.led_total = l.columns
            # Dataframe reduction for analysis according to selected LEDs
            self.led_used = algae.led_reduction(LED380_checkbox=self.LED380_checkbox.isChecked(),
                                                LED403_checkbox=self.LED403_checkbox.isChecked(),
                                                LED438_checkbox=self.LED438_checkbox.isChecked(),
                                                LED453_checkbox=self.LED453_checkbox.isChecked(),
                                                LED472_checkbox=self.LED472_checkbox.isChecked(),
                                                LED526_checkbox=self.LED526_checkbox.isChecked(),
                                                LED593_checkbox=self.LED593_checkbox.isChecked(),
                                                LED640_checkbox=self.LED640_checkbox.isChecked())

            l_red = pd.DataFrame(np.zeros(shape=(len(l.index), 0)), index=l.index)
            l_corr_red = pd.DataFrame(np.zeros(shape=(len(l_corr.index), 0)), index=l_corr.index)
            for i in l.columns:
                if self.led_used.loc[0, i] == True:
                    l_red.loc[:, i] = l.loc[:, i]
            for i in l_corr.columns:
                if self.led_used.loc[0, i] == True:
                    l_corr_red.loc[:, i] = l_corr.loc[:, i]

            # sample data are sorted
            l_corr_red = l_corr_red.sort_index(axis=1)

            # Store parameter for further evaluation
            self.loaded_data = {'l': l_red, 'l_corr': l_corr_red, 'header': header, 'firstline': firstline,
                                'current': current, 'date': date, 'name': self.sample_name, 'blank_mean': blank_mean,
                                'blank_std': blank_std, 'rg9_sample': rg9_sample, 'rg665_sample': rg665_sample,
                                'volume': volume, 'path': path, 'full_calibration': full_calibration,
                                'kappa_spec': kappa_spec, 'correction': correction, 'pumprate': pumprate,
                                'device': self.number_em.split('-')[1], 'blank_corr': blank_correction,
                                'peak_detection': peak_detection, 'additional': additional, 'unit': unit_corr,
                                'unit_blank': unit_bl}

            # Plotting corrected data to select the time-range for sample and blank. Time-range stored in xcoords.
            self.plot_timedrive(df=self.loaded_data['l_corr'], name=self.loaded_data['name'],
                                date=self.loaded_data['date'], f=self.fig_timedrive, ax=self.ax_timedrive, unit=unit)


        else:
            run_missing_sample_failed = QMessageBox()
            run_missing_sample_failed.setIcon(QMessageBox.Information)
            run_missing_sample_failed.setText("Choose sample file!")
            run_missing_sample_failed.setInformativeText("Either raw data or already processed sample file")
            run_missing_sample_failed.setWindowTitle("Missing input!")
            run_missing_sample_failed.exec_()
            return
        self.run_button.setEnabled(True)


#################################################################################################
#   Run analysis
#################################################################################################
    def run_analysis(self):
        self.message.clear()
        self.report.clear()
        # self.report_sup.clear()
        if self.xcoords:
            # xcoords from time drive selected -> currently no histogram
            self.ax_histogram.clear()
            self.ax_histogram.set_xlim(0, 8)
            self.ax_histogram.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5])
            self.ax_histogram.set_xticklabels(self.led_selection, rotation=15)
            self.ax_histogram.set_xlabel('Wavelength [nm]')
            self.ax_histogram.set_ylabel('Relative signal intensity [rfu]')
        if self.threedimensional_plot_checkbox.isChecked():
            # 3D Plot redrawing
            self.ax_scoreplot.cla()
            self.fig_scoreplot.clear()
            self.ax_scoreplot = self.fig_scoreplot.gca(projection='3d')
            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=10)
            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=10)
            self.ax_scoreplot.set_zlabel('LDA 3', fontsize=fs, labelpad=10)
            self.fig_scoreplot.subplots_adjust(left=0.1, right=0.9, bottom=0.18, top=0.85)
            self.fig_scoreplot.canvas.draw()
        else:
            # 2D Plot activated
            self.ax_scoreplot.cla()
            self.fig_scoreplot.clear()
            self.ax_scoreplot = self.fig_scoreplot.add_subplot(111)
            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=10)
            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=10)
            self.fig_scoreplot.subplots_adjust(left=0.12, right=0.9, bottom=0.18, top=0.85)
            self.fig_scoreplot.canvas.draw()

        if not self.xcoords and not self.xcoords_prescan:
            self.message.append('No time range selected - use whole timeline as sample')
            self.xcoords = [self.loaded_data['l_corr'].index[0], self.loaded_data['l_corr'].index[-1], 0, 0]
        if len(self.xcoords) == 2:
            self.message.append('Only the sample range was selected - use blank which is stored in header')
            self.xcoords = [self.xcoords[0], self.xcoords[1], 0, 0]

        self.mean_corr = self.loaded_data['l_corr'].mean()

        try:
            self.fname_database
        except:
            run_missing_database = QMessageBox()
            run_missing_database.setIcon(QMessageBox.Information)
            run_missing_database.setText("Database is missing!")
            run_missing_database.setInformativeText("Select a folder for database!")
            run_missing_database.setWindowTitle("Missing input!")
            run_missing_database.exec_()
            return

        trainingdata = self.fname_database
        device_training = 1

        # Load training data
        self.message.append('Start loading reference database... ')

        [self.training_corr_red_sort, training,
         self.training_red] = algae.training_database(trainings_path=trainingdata, led_used=self.led_used)

        # message that training matrix is loaded
        self.message.append('Reference data base is loaded: check ✓')

        # Load additional information, e.g. color classes and genus names
        if self.threedimensional_plot_checkbox.isChecked() is True:
            self.score_type = 3
        elif self.twodimensional_plot_checkbox.isChecked() is True:
            self.score_type = 2
        else:
            self.message.append('Error! Choose a distinct plot dimension')
            return

        # information for training data. Which separation level is chosen?
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae.separation_level(separation=self.separation_edit.text())

        # raw data or already pre-scanned data are analysed?
        if self.sample_edit.toPlainText():
            # raw data are analysed -> check if an overall or an individual peak analysis might be possible
            # correction of sample time drive mean is corrected and peak extracted but peak is a DataFrame of raw data.
            [c, peak, self.mean_corr,
             LoD] = algae.correction_sample(l=self.loaded_data['l'], header=self.loaded_data['header'],
                                            date=self.loaded_data['date'], current=self.loaded_data['current'],
                                            volume=self.loaded_data['volume'], device=self.loaded_data['device'],
                                            unit_blank=self.loaded_data['unit_blank'], led_total=self.led_total,
                                            kappa_spec=self.loaded_data['kappa_spec'],
                                            correction=self.loaded_data['correction'],
                                            peak_detection=self.loaded_data['peak_detection'], xcoords=self.xcoords,
                                            full_calibration=self.loaded_data['full_calibration'],
                                            blank_corr=self.loaded_data['blank_corr'],
                                            blank_mean=self.loaded_data['blank_mean'],
                                            blank_std=self.loaded_data['blank_std'])

            # calculate average fluorescence intensity at different excitation wavelengths of sample.
            # standardize and normalize the values if it is done with the training-data
            [mean_fluoro, training_corr,
             pigment_pattern] = algae.average_fluorescence(mean_corr=self.mean_corr,
                                                           training_corr_sort=self.training_corr_red_sort,
                                                           normalize=self.normalize_checkbox.isChecked(),
                                                           standardize=self.standardize_checkbox.isChecked())

            # evaluation of mean values or individual spike evaluation
            if ['--'] in c.unique():
                self.message.append('We will do the analysis with mean values ... \n')
                [self.lda, training_score, df_score,
                 number_components] = algae.lda_process_mean(mean_fluoro=mean_fluoro, training_corr=training_corr,
                                                             unit=self.loaded_data['unit'], classes_dict=classes_dict,
                                                             colorclass_dict=colorclass_dict,
                                                             separation=self.separation_edit.text(),
                                                             priority=self.priority_checkbox.isChecked(),
                                                             type_=self.score_type)
            else:
                self.message.append('We will do the analysis with individual peaks ... \n')
                [self.lda, df_score, training_score,
                 number_components] = algae.lda_process_individual(l=self.loaded_data['l_corr'],
                                                                   training_corr=training_corr, LoD=LoD,
                                                                   classes_dict=classes_dict,
                                                                   colorclass_dict=colorclass_dict, volume=None,
                                                                   separation=self.separation_edit.text(),
                                                                   pumprate=self.loaded_data['pumprate'],
                                                                   normalize=self.normalize_checkbox.isChecked(),
                                                                   priority=self.priority_checkbox.isChecked(),
                                                                   type_=self.score_type)

            ax = self.plot_histogram(mean=self.mean_corr, f=self.fig_histogram, ax=self.ax_histogram)

        else:
            # Already pre-scanned data are analysed. No peak detection necessary
            self.message.append('Pre-scanned data will be analysed. \n')

            # calculate average fluorescence intensity at different excitation wavelengths of sample.
            # standardize and normalize the values if it is done with the training-data
            [mean_fluoro, training_corr,
             pigment_pattern] = algae.average_fluorescence(mean_corr=self.mean_corr,
                                                           training_corr_sort=self.training_corr,
                                                           normalize=self.normalize_checkbox.isChecked(),
                                                           standardize=self.standardize_checkbox.isChecked())

            # counted cells preparation. If '--' in counted cells list -> analysis with mean values
            c = self.loaded_data['counted_cells'].loc[self.loaded_data['counted_cells'].index[0], :]

            self.message.append('We will do the analysis with mean values ... \n')
            [self.lda, training_score, df_score,
             number_components] = algae.lda_process_mean(mean_fluoro=mean_fluoro, training_corr=training_corr,
                                                         unit=self.loaded_data['unit'], classes_dict=classes_dict,
                                                         colorclass_dict=colorclass_dict,
                                                         separation=self.separation_edit.text(),
                                                         priority=self.priority_checkbox.isChecked(),
                                                         type_=self.score_type)

        if number_components <= 2:
            type_ = 2
        else:
            type_ = self.score_type

        # decision function calculating the distance between sample and centroid of each class. prob_
        # calculates the 3D gaussian probability that a sample belongs to a certain algal class
        limit = 1E-6

        d = algae.reference_scores(self.lda, training_score, classes_dict)
        d_ = []
        prob = []

        for el in range(len(df_score)):
            d_.append(algae.sample_distance(d, df_score))
            prob.append(algae.prob_(d_[el]))

        # preparing the output-file
        summary = []
        summary_ = []
        sample = []
        sample_plot = []

        # load overview file for algal groups and group colors
        df_phylum = 'supplementary/phytoplankton/170427_algae.txt'
        phylum = 'supplementary/phytoplankton/170427_algalphylum.txt'
        alg_group = pd.read_csv(df_phylum, sep='\t', encoding="latin-1")
        alg_phylum = pd.read_csv(phylum, sep='\t', header=None, encoding="latin-1", usecols=[1, 2],
                                 index_col=0).drop_duplicates()
        phyl_group = pd.DataFrame(np.zeros(shape=(0, 2)), columns=['phylum_label', 'color'])

        for el in range(len(prob)):
            for k in range(len(prob[0])):
                if prob[el].values[k][0] > limit:
                    sample.append(el)
                    summary.append(prob[el].index[k])
                    summary_.append(float(prob[el].values[k]))

                    if el not in sample_plot:
                        sample_plot.append(el)
                        color = d['LDA1'].copy()

                        for coords in d.index:
                            color[coords] = colorclass_dict[coords]

                        if type_ == 2:
                            # 2D Plot activated
                            self.ax_scoreplot.cla()
                            self.fig_scoreplot.clear()
                            self.ax_scoreplot = self.fig_scoreplot.add_subplot(111)
                            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=10)
                            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=10)
                            self.fig_scoreplot.subplots_adjust(left=0.12, right=0.9, bottom=0.18, top=0.85)
                            self.fig_scoreplot.canvas.draw()

                            self.plot_distribution_2d(f=self.fig_scoreplot, ax=self.ax_scoreplot, d=d,
                                                      df_score=df_score.loc[el, :], color=color, alg_group=alg_group,
                                                      alg_phylum=alg_phylum, phyl_group=phyl_group,
                                                      separation=self.separation_edit.text())
                        elif type_ == 3:
                            self.ax_scoreplot.cla()
                            self.fig_scoreplot.clear()
                            self.ax_scoreplot = self.fig_scoreplot.gca(projection='3d')
                            self.ax_scoreplot.set_xlabel('LDA 1', fontsize=fs, labelpad=10)
                            self.ax_scoreplot.set_ylabel('LDA 2', fontsize=fs, labelpad=10)
                            self.ax_scoreplot.set_zlabel('LDA 3', fontsize=fs, labelpad=10)
                            self.fig_scoreplot.subplots_adjust(left=0.1, right=0.9, bottom=0.18, top=0.85)
                            self.fig_scoreplot.canvas.draw()
                            self.plot_distribution_3d(f=self.fig_scoreplot, ax=self.ax_scoreplot, d=d,
                                                      df_score=df_score.loc[el, :], color=color, alg_group=alg_group,
                                                      alg_phylum=alg_phylum, phyl_group=phyl_group,
                                                      separation=self.separation_edit.text())
                        else:
                            self.message.append('No score plot possible! Choose 3D or 2D.')
                    else:
                        color = d['LDA1'].copy()
                        for coords in d.index:
                            color[coords] = colorclass_dict[coords]
                else:
                    self.message.append('nothing to print for {}'.format(prob[el].index[k]))


        self.algae = {'alg_group': alg_group, 'alg_phylum': alg_phylum, 'phyl_group': phyl_group}
        self.results_lda = {'data': d, 'df_score': df_score, 'mean': self.mean_corr, 'color_scores': color}

        [self.res, self.prob_phylum] = algae.output(sample, sample_plot, summary, summary_,
                                                    path=self.loaded_data['path'], date=self.loaded_data['date'],
                                                    name=self.sample_name, prob=prob,
                                                    separation=self.separation_edit.text(), save=False)

        # Report results
        self.report.setColumnCount(3)
        self.report.setRowCount(len(self.res.index))
        # self.report_sup.setColumnCount(2)
        # self.report_sup.setRowCount(len(self.prob_phylum.index))

        self.report.setHorizontalHeaderLabels([' ', 'identified class', 'probability [%]'])
        # self.report_sup.setHorizontalHeaderLabels([' ', 'identified phylum', 'probability [%]'])

        for i in range(len(self.res.index)):
            self.report.setItem(i, 0, QTableWidgetItem(str(self.res.loc[self.res.index[i], 0])))
            self.report.setItem(i, 1, QTableWidgetItem(str(self.res.loc[self.res.index[i], 1])))
            self.report.setItem(i, 2, QTableWidgetItem(str(self.res.loc[self.res.index[i], 2])))
            self.report.item(i, 0).setTextAlignment(Qt.AlignBottom | Qt.AlignRight)
            self.report.item(i, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.report.item(i, 1).setTextAlignment(Qt.AlignBottom | Qt.AlignRight)
            self.report.item(i, 1).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.report.item(i, 2).setTextAlignment(Qt.AlignBottom | Qt.AlignRight)
            self.report.item(i, 2).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.report.resizeColumnsToContents()
        self.report.resizeRowsToContents()
        # for i in range(len(self.prob_phylum.index)):
            # self.report_sup.setItem(i, 0, QTableWidgetItem(str(self.prob_phylum.loc[self.prob_phylum.index[i], 0])))
            # self.report_sup.setItem(i, 1, QTableWidgetItem(str(self.prob_phylum.loc[self.prob_phylum.index[i], 1])))
            # self.report_sup.item(i, 0).setTextAlignment(Qt.AlignBottom | Qt.AlignRight)
            # self.report_sup.item(i, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            # self.report_sup.item(i, 1).setTextAlignment(Qt.AlignBottom | Qt.AlignRight)
            # self.report_sup.item(i, 1).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        # self.report_sup.resizeColumnsToContents()
        # self.report_sup.resizeRowsToContents()

        self.save_report_button.setEnabled(True)
        self.save_all_button.setEnabled(True)


#################################################################################################
#   Save data
#################################################################################################
    def save_report(self):

        a = self.sample_name
        b = self.fname.split('.')[0].split('/')

        path = ''
        for i in range(len(b)-1):
            path = path + str(b[i]) + '/'

        info = ''
        if self.xcoords_prescan != None:
            part = self.xcoords_prescan[:-3].split('-')
            xcoords = []
            for i in part:
                xcoords.append(int(i))
        elif self.xcoords != []:
            xcoords = self.xcoords

        info = str(xcoords[0]) + '-' + str(xcoords[1])

        folder_scores = path + 'scores/'
        if self.priority_checkbox.isChecked() is True:
            scores_trainig = folder_scores + 'training-scores_' + 'dinophyta-priority.txt'
            scores_sample = folder_scores + 'scores-' + self.sample_name + '-' + b[-1].split('_')[2] + \
                            '_dinophyta-priority.txt'
            name = self.sample_name + '_dinophyta-priority'
        else:
            scores_trainig = folder_scores + 'training-scores.txt'
            scores_sample = folder_scores + 'scores-' + self.sample_name + '-' + b[-1].split('_')[2] + '.txt'
            name = self.sample_name

        # check if results-folder already exists. if not, create one
        if not os.path.exists(folder_scores):
            os.makedirs(folder_scores)

        self.results_lda['data'].to_csv(scores_trainig, sep='\t', decimal='.')
        self.results_lda['df_score'].to_csv(scores_sample, sep='\t', decimal='.')


        res = algae.linear_discriminant_save(res=self.res, prob_phylum=self.prob_phylum, info=info,
                                             date=self.loaded_data["date"], name=name, path=path[:-1],
                                             blank_corr=self.loaded_data['blank_corr'],
                                             correction=self.loaded_data['correction'],
                                             additional=self.loaded_data['additional'],
                                             peak_detection=self.loaded_data['peak_detection'])

        self.message.append('Save report done')

    def save_all(self):
        a = self.sample_name
        b = self.fname.split('.')[0].split('/')
        pre_scanned = False

        path = ''
        for i in range(len(b)-1):
            path = path + str(b[i]) + '/'

        info = ''
        if self.xcoords_prescan != None:
            part = self.xcoords_prescan[:-3].split('-')
            xcoords = []
            for i in part:
                xcoords.append(int(i))
        elif self.xcoords != []:
            xcoords = self.xcoords

        info = str(xcoords[0]) + '-' + str(xcoords[1])

        res = algae.linear_discriminant_save_all(res=self.res, prob_phylum=self.prob_phylum, d=self.results_lda['data'],
                                                 df_score=self.results_lda['df_score'], mean=self.results_lda['mean'],
                                                 info=info, date=self.loaded_data["date"],
                                                 name=a, alg_group=self.algae['alg_group'],
                                                 alg_phylum=self.algae['alg_phylum'],
                                                 phyl_group=self.algae['phyl_group'],
                                                 color=self.results_lda['color_scores'],
                                                 blank_corr=self.loaded_data['blank_corr'],
                                                 correction=self.loaded_data['correction'],
                                                 additional=self.loaded_data['additional'],
                                                 peak_detection=self.loaded_data['peak_detection'],
                                                 separation=self.separation_edit.text(),
                                                 path=path[:-1], ax=None, format='pdf', dpi=600, type_=3)

        self.message.append('Save report and figures done')


#################################################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Breeze')
    alpaca = Gui()

    # screen Size adjustment
    screen = app.primaryScreen()
    rect = screen.availableGeometry()

    alpaca.setFixedHeight(int(rect.height() * 0.9))
    alpaca.setFixedWidth(int(rect.width() * 0.95))

    # show wizard
    alpaca.show()
    app.exec_()
