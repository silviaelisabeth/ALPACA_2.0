__author__ = 'szieger'
__project__ = 'SCHeMA_calibration_standard'

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import seaborn as sns
import numpy as np
import math
import os
from os import listdir
from os.path import isfile, join
from tabulate import tabulate
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

sns.set_context("paper", font_scale=2.5, rc={"lines.linewidth": 2})
sns.set_palette("colorblind")
sns.set_style("ticks", {"xtick.direction": "in","ytick.direction": "in"})
#################################################################################################
# GLOBAL VARIABLES
#################################################################################################

led_dict = {"1a1": '380 nm',
            "1a2": '403 nm',
            "1a3": '438 nm',
            "1a4": '453 nm',
            "2a1": '472 nm',
            "2b1": '507 nm',
            "2b2": '526 nm',
            "1b1": '544 nm',
            "2b3": '572 nm',
            "2b3+": '588 nm',
            "2b4": '593 nm',
            "3c1": '640 nm',
            "3c2": '652 nm',
            "3c3": '615 nm'}

led_color_dict = {"380 nm": '#610061',
                  "403 nm": '#8300BC',
                  "428 nm": '#0A00FF',
                  "438 nm": '#0A00FF',
                  "453 nm": '#0057FF',
                  "472 nm": '#00AEFF',
                  "508 nm": '#00FF17',
                  "526 nm": '#00FF17',
                  "518 nm": '#4AFF00',
                  "544 nm": '#8CFF00',
                  "572 nm": '#E7FF00',
                  "588 nm": '#ffe600',
                  "593 nm": '#FFD500',
                  "615 nm": '#ff8900',
                  "640 nm": '#FF2100',
                  "652 nm": '#FF0000'}


#################################################################################################
# Polynomial Regression
#################################################################################################
def polyfit_correlation(x, y, degree):
    """
    :param x:           x-values of the data set that should be fitted
    :param y:           y-values of the data set to be fitted
    :param degree:      order of the regression curve. 1st order = linear regression, 2nd order = quadratic polynom, ...
    :return: results    dictionary containing the polynomial coefficients as results['correlation'] as well as the
                        r-square value as results['determination'].
    """

    results = {}
    coeffs = np.polyfit(x, y, degree)

    # Polynomial Coefficients
    results['polynomial'] = coeffs.tolist() # first slope than increment
    correlation = np.corrcoef(x, y)[0, 1]

    # r
    results['correlation'] = correlation
    # r-squared
    results['determination'] = correlation**2

    return results


#################################################################################################
# Information from file
#################################################################################################
def meas_file(path):
    """ Reading all txt-files in the current folder and sort if the file is a sample- or a calibration-file
    :param  path:       path to the current folder that should be analysed
    :return:
            calib_:     pd.DataFrame containing the ID of the file ('calibration'), the measurement time and the full
                        txt-file name of all calibration-files
            sample_:    pd.DataFrame containing the sample-name, the measurement time, the LED current, the MAZeT
                        amplification and the full txt-file-name
    """
    filename = [f for f in listdir(path) if isfile(join(path, f))]
    sample = pd.DataFrame(np.zeros(3), index=['Name', 'Time', 'basename'])

    for k in range(len(filename)):
        # depending on the system, the date is interpreted in different ways ('_' or ':')
        fn = filename[k].split('.')[0].split('_')[1]

        # storage of data in sample and calibration dataFrame
        if fn == 'rhodamine101' or fn == 'rhodamin101' or fn == 'Rhodamine101' or fn == 'Rhodamin101':
            sample.ix['Name', k] = filename[k].split('.')[0].split('_')[1]
            sample.ix['Time', k] = filename[k].split('.')[0].split('_')[0][8:]
            sample.ix['basename', k] = path + filename[k]
        else:
            raise ValueError('Unknown standard: \'{}\'! Please change standard or algorithm'.format(fn))

    sample = sample.drop(sample.ix[:, (sample == 0).all()], axis=1)
    sample_ = sample.T

    return sample_


def info_file(d):
    """
    Collects information about the input-file
    :param d: path to the sample file
    :return:
            info_dict ... dictionary containing the following parameters:
            LED:                LED-ID,
            LED_color:          color of the LEDs,
            fluor_standard:     fluorescence standard,
            measurement_day:    yyyymmdd of the measurement
            name:               file name of the sample,
            path:               path to the sample file,
            wavelength:         of the LEDs in the right order in the style: '380 nm'
    """
    # path and filename
    path = os.path.dirname(d)
    name = os.path.basename(d)

    # load header of a specific file and information about amplification and pump speed (gen_info)
    header_ = pd.read_csv(d, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]})
    header = header_.ix[:, :7]
    gen_info = pd.read_csv(d, sep='\t', header=None, nrows=1, converters={0: lambda x: x[2:]})
    amplif = gen_info.ix[0, 0].split('=')[1]            # Ohm
    pumpspeed = float(gen_info.ix[0, 2].split('=')[1])  # mL/min

    # LED used in right order
    LED = []
    LEDs = []
    for i in header.ix[1, :]:
        LEDs.append(int(i.split(' ')[-2]))   # LED without nm
        LED.append(i.split(' ')[-2] + ' nm')
    color = []
    for j in LED:
        color.append(led_color_dict[j])  # define color for LED

    # current and blank of the sample file
    blank = []
    for w in header.ix[4, :]:
        blank.append(float(w.split('=')[1].split('+')[0]) / 1000)  # mean value in nW
    current = []
    for i in header.ix[2, :]:
        current.append(int(i.split(' ')[-2]))

    # measurement date and standard name
    date = name.split('.')[0].split('_')[0]
    standard = name.split('.')[0].split('_')[1]

    info_dict = {'path':            path,
                 'name':            name,
                 'LED':             LED,
                 'wavelength':      LEDs,
                 'LED_color':       color,
                 'current':         current,
                 'amplification':   amplif,
                 'pump_speed':      pumpspeed,
                 'blank':           blank,
                 'measurement_day': date,
                 'fluor_standard':  standard}

    return info_dict


def signal_calculation(d, blank, LED, curr):
    """
    Calculation of light - dark signal
    :param d:
    :param blank:
    :param LED:
    :param curr:
    :return:
    """

    # load light and dark signals and the header as well
    s_light = pd.read_csv(d, sep='\t', usecols=[0, 1, 3, 5, 7, 9, 11, 13, 15], skiprows=6, index_col=0)
    s_dark = pd.read_csv(d, sep='\t', usecols=[0, 16, 17, 18, 19, 20, 21, 22, 23], skiprows=6, index_col=0)
    s_light.columns = LED
    s_dark.columns = LED

    # offset-compensation of each LED, averaging and blank correction generating the LED signal
    signal_comp = s_light - s_dark
    signal = pd.DataFrame(signal_comp.mean() - blank).T

    # merge signal and current for each LED
    current = pd.DataFrame(curr, index=LED).T  # current in mA
    signal = signal.append(current)
    signal.index = ['mean', 'current']

    return signal


##################################################################################################
# Calibration
#################################################################################################
def calibration_basis(reference_path, device_ref, full_calibration=False):
    """
    Defines the basis which is used as reference for the inter-comparability of the device. The function returns a
    value table for the reference sample so we could calculate the corrections factors for all LED intensities in the
    range between 9-97 mA. The polynomial fit is of 2.order.
    :param reference_path:              path to the folder with all reference measurements and calibration files
    :param device_ref:                  integer; which device was used for the reference measurement
    :param full_calibration:            polynomial fit between 10 - 97mA if True, otherwise linear fit between 15-50 mA
    :return:
    """
    # load measurement files of the reference
    reference = meas_file(reference_path)

    # info about sample file
    info = info_file(reference['basename'][0])

    # merge current and signal for each LED of all sample files. Signals are offset compensated and blank corrected
    data_reference = pd.DataFrame(np.zeros(shape=(8, 1)), index=info['LED'])
    for u in range(len(reference['basename'])):
        info = info_file(reference['basename'][u])
        w = (signal_calculation(reference['basename'][u], info['blank'], info['LED'], info['current']))
        w.index = ['mean {}'.format(u), 'current {}'.format(u)]
        data_reference = data_reference.join(w.T)
    reference_tab = data_reference.loc[:, (data_reference != 0).any(axis=0)]

    # sort LEDs by emission filter RG665 or RG9
    RG665_basis = info['LED'][0:-2]
    RG9_basis = info['LED'][-2:]

    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9)
    reference_table = reference_tab.copy()
    # Load emission factors from file

    em_path = 'D:/01_data_processing/algae_module\/01_calibration/correction_emissionfilter/'  + \
             '201705_device_emission_device-' + str(device_ref) + '.txt'
    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = data_reference.index

    for i in RG9_basis:
        for j in range(int(len(reference_tab.columns)/2)):
            reference_table.ix[i, j+j] = reference_tab.ix[i, j+j] / balance_factor.ix[int(device_ref), i]
    for i in RG665_basis:
        for j in range(int(len(reference_tab.columns)/2)):
            reference_table.ix[i, j+j] = reference_tab.ix[i, j+j] / balance_factor.ix[int(device_ref), i]

    # split reference table into value table for each LED for the regression analysis
    table_y = pd.DataFrame(np.zeros(shape=(3, 8)), columns=reference_table.index, index=[0, 2, 4])
    table_x = pd.DataFrame(np.zeros(shape=(3, 8)), columns=reference_table.index, index=[1, 3, 5])
    for x in range(len(reference_table.columns)):
        for e in reference_table.index:
            if x % 2 == 0:  # no residual, even number := y-value
                table_y.ix[x, e] = reference_table.ix[e, x]
            else:           # residual, odd number := x-value
                table_x.ix[x, e] = reference_table.ix[e, x]
    table_y = table_y.sort_values(['380 nm'])
    table_y.index = [0, 2, 4]
    table_x = table_x.sort_values(['380 nm'])
    table_x.index = [1, 3, 5]

    if full_calibration is True:
        # regression curve (2nd order) for each LED with r-square value - full range
        reg = np.zeros((8, 4))
        regression = pd.DataFrame(reg, index=info['LED'], columns=['a', 'b', 'c', 'r-square']).T

        for k in table_y.columns:
            a = polyfit_correlation(table_x[k], table_y[k], 2)
            regression[k]['a':'c'] = a['polynomial']
            regression[k]['r-square'] = round(a['determination'] * 100, 2)

        # value table for polynomial fit
        x = np.arange(9, 98, 1)
        valuetable_basis = pd.DataFrame(np.zeros(len(x)).T, index=x)
        for k in regression.columns:
            valuetable_basis[k] = pd.DataFrame([regression[k]['a'] * x ** 2 + regression[k]['b'] * x +
                                                regression[k]['c']], index=[k], columns=x).T
        valuetable_basis = valuetable_basis.drop(0, axis=1).round(2)
    else:
        # regression curve (1st order) for each LED with r-square value - 15-50 mA
        reg = np.zeros((8, 3))
        regression = pd.DataFrame(reg, index=info['LED'], columns=['a', 'b', 'r-square']).T
        for k in table_y.columns:
            a = polyfit_correlation(table_x[k], table_y[k], 1)
            regression[k]['a':'b'] = a['polynomial']
            regression[k]['r-square'] = round(a['determination'] * 100, 2)

        # value table for linear fit
        x = np.arange(15, 51, 1)
        valuetable_basis = pd.DataFrame(np.zeros(len(x)).T, index=x)
        for k in regression.columns:
            valuetable_basis[k] = pd.DataFrame([regression[k]['a'] * x + regression[k]['b']], index=[k], columns=x).T
        valuetable_basis = valuetable_basis.drop(0, axis=1).round(2)

    return valuetable_basis, table_y, RG665_basis, RG9_basis, info['fluor_standard'], info, regression


def calibration_actual(sample_path, basis, table_basis, basis_name, RG9_basis, device, full_calibration=False):
    """
    Calculates the regression curve for the standard on a specific day and compares the found regression curve to
    the basis. The polynomial fit is of 2.order.
    :param sample_path:
    :param basis:                       value table of the reference standard
    :param table_basis:
    :param basis_name:                  which standard is used as reference
    :param RG9_basis:
    :param device:                      which device was used for the actual measurement
    :param full_calibration:            polynomial fit between 10 - 97mA if True, otherwise linear fit between 10-50 mA
    :return:
            valuetable:                 value table for the fluorescence standard for the actual day
            info['fluor_standard']:     which standard is used for the measurement
            RG665_sample
            RG9_sample
    """
    # load measurement files of the reference
    d = meas_file(sample_path)

    # warning, if a different standard is used for sample or reference
    if d['Name'][0] != basis_name:
        print('Warning! You used another sample for the calibration than for the reference')

    #  additional info over file
    info = info_file(d['basename'][0])

    # merge current and signal for each LED of all sample files
    data_sample = pd.DataFrame(np.zeros(shape=(8, 1)), index=info['LED'])
    for u in range(len(d['basename'])):
        info = info_file(d['basename'][u])
        w = (signal_calculation(d['basename'][u], info['blank'], info['LED'], info['current']))
        w.index = ['mean {}'.format(u), 'current {}'.format(u)]
        data_sample = data_sample.join(w.T)
    sample_tab = data_sample.loc[:, (data_sample != 0).any(axis=0)]

    # sort LEDs by emission filter RG665 or RG9
    RG665_sample = info['LED'][0:-2]
    RG9_sample = info['LED'][-2:]

    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9)
    # Load emission factors from file
    em_path = 'D:/01_data_processing/algae_module\/01_calibration/correction_emissionfilter/' \
              '201705_device_emission_device-' + str(device) + '.txt'
    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = ['526 nm', '438 nm', '593 nm', '453 nm', '380 nm', '472 nm', '403 nm', '640 nm']
    # balance_factor = pd.DataFrame([6.59, 6.85, 6.57, 4.09, 6.90, 6.43, 1.83, 1.00], index=sample_tab.index).T

    sample_table = sample_tab.copy()
    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9)
    for i in RG9_sample:
        for j in range(int(len(sample_tab.columns)/2)):
            sample_table.ix[i, j+j] = sample_tab.ix[i, j+j] / balance_factor.ix[int(device), i]
    for i in RG665_sample:
        for j in range(int(len(sample_tab.columns)/2)):
            sample_table.ix[i, j+j] = sample_tab.ix[i, j+j] / balance_factor.ix[int(device), i]

    # split reference table into value table for each LED for the regression analysis
    table_y = pd.DataFrame(np.zeros(shape=(3, 8)), columns=sample_table.index, index=[0, 2, 4])
    table_x = pd.DataFrame(np.zeros(shape=(3, 8)), columns=sample_table.index, index=[1, 3, 5])
    for x in range(len(sample_table.columns)):
        for e in sample_table.index:
            if x % 2 == 0:  # no residual, even number := y-value
                table_y.ix[x, e] = sample_table.ix[e, x]
            else:  # residual, odd number := x-value
                table_x.ix[x, e] = sample_table.ix[e, x]
    table_y = table_y.sort_values(['380 nm'])
    table_y.index = [0, 2, 4]
    table_x = table_x.sort_values(['380 nm'])
    table_x.index = [1, 3, 5]

    # variation between fitted basis data and measured sample data
    variation = table_y.copy()
    var = pd.DataFrame(np.zeros(shape=(3, 8)), columns=variation.columns)
    print('Sample-Reference variation higher than 10%:')
    for i in table_basis.columns:
        for k in range(len(sample_table.columns)):
            if k % 2 == 0:  # k := mean0, mean1, mean2 (0,2,4)
                variation.ix[k, i] = (table_y.ix[k, i] - table_basis.ix[k, i]) / table_basis.ix[k, i] * 100
        variation = variation.sort_index()

    # return warning if variation is higher than 10%!
    LED_var = []
    for j in variation.columns:
        for i in variation.index:
            if abs(variation.ix[i, j]) > 10 and j not in LED_var:
                LED_var.append(j)
    if not LED_var:
        print('-- none of the LEDs -- ')
    else:
        for k, e in enumerate(LED_var):
            print(variation.ix[:, e].round(1))
    print('\n')

    if full_calibration is True:
        print('Polynomial regression of 2nd order between 10-97 mA for the sample', '\n')
        # regression curve (2nd order) for each LED with r-square value - full range
        reg = np.zeros((8, 4))
        regression = pd.DataFrame(reg, index=info['LED'], columns=['a', 'b', 'c', 'r-square']).T

        for k in table_y.columns:
            a = polyfit_correlation(table_x[k], table_y[k], 2)
            regression[k]['a':'c'] = a['polynomial']
            regression[k]['r-square'] = round(a['determination'] * 100, 2)

            # value table for polynomial fit
            x = np.arange(9, 98, 1)
            valuetable_sample = pd.DataFrame(np.zeros(len(x)).T, index=x)
            for m in regression.columns:
                valuetable_sample[m] = pd.DataFrame([regression[m]['a'] * x ** 2 + regression[m]['b'] * x +
                                                    regression[m]['c']], index=[m], columns=x).T
            valuetable_sample = valuetable_sample.drop(0, axis=1).round(2)
    else:
        print('Linear fit between 15-50 mA for the sample', '\n')
        # regression curve (1st order) for each LED with r-square value - 15-50 mA
        reg = np.zeros((8, 3))
        regression = pd.DataFrame(reg, index=info['LED'], columns=['a', 'b', 'r-square']).T

        for k in table_y.columns:
            a = polyfit_correlation(table_x[k], table_y[k], 1)
            regression[k]['a':'b'] = a['polynomial']
            regression[k]['r-square'] = round(a['determination'] * 100, 2)

        # value table for linear fit
        x = np.arange(15, 51, 1)
        valuetable_sample = pd.DataFrame(np.zeros(len(x)).T, index=x)
        for k in regression.columns:
            valuetable_sample[k] = pd.DataFrame([regression[k]['a'] * x + regression[k]['b']], index=[k], columns=x).T
        valuetable_sample = valuetable_sample.drop(0, axis=1).round(2)

    # plot calibration data
    f, ax = plt.subplots(figsize=(7.5, 5))
    for i, k in enumerate(table_y.columns):
        ax.plot(table_x[k], table_y[k], color=info['LED_color'][i], lw=0, marker='^',
                markersize=9, label=k)
    for i, k in enumerate(valuetable_sample.columns):
        ax.plot(x, valuetable_sample[k], color=info['LED_color'][i], lw=1.75, label='sample')      # actual LED fit
        ax.plot(basis.index, basis[k], color=info['LED_color'][i], lw=1.75, ls='-.', label='refernce')  # basis LED fit

    xmin = math.ceil(basis.index[0]*70/100)
    xmax = (basis.index[-1]*105/100).round(0)
    if basis.max().max() > valuetable_sample.max().max():
        ymin = math.ceil(basis.min().min())*0.95
        ymax = (basis.max().max()).round(0)*1.05
    else:
        ymin = math.ceil(valuetable_sample.min().min())*0.95
        ymax = (valuetable_sample.max().max()).round(0)*1.05

    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    majorLocator_x = MultipleLocator(5)
    majorLocator_y = MultipleLocator(500)
    minorLocator_x = MultipleLocator(1)
    minorLocator_y = MultipleLocator(100)
    ax.xaxis.set_major_locator(majorLocator_x)
    ax.xaxis.set_minor_locator(minorLocator_x)
    ax.yaxis.set_major_locator(majorLocator_y)
    ax.yaxis.set_minor_locator(minorLocator_y)
    ax.tick_params(axis='both', which='major', direction='in', labelsize=15)
    ax.tick_params(axis='both', which='minor', direction='in')
    ax.xaxis.set_ticks_position('both')
    ax.yaxis.set_ticks_position('both')

    plt.title('Actual LED fit with {} at {}/{}/{}'.format(info['fluor_standard'], info['measurement_day'][6: 8],
                                                          info['measurement_day'][4: 6], info['measurement_day'][0: 4],
                                                          basis_name), fontsize=13)
    plt.xlabel('LED intensity [mA]', fontsize=14)
    plt.ylabel('Light intensity [nW]', fontsize=14)

    legend = []
    for i in info['wavelength']:
        legend.append(str(i) + ' nm')
    plt.legend(legend, loc='upper center', bbox_to_anchor=(1.15, 1.), frameon=True, fontsize=13)
    plt.subplots_adjust(left=0.15, right=0.8, top=0.9, bottom=0.15)# plt.tight_layout()

    return valuetable_sample, RG665_sample, RG9_sample


def corr_factor_deviation(kappa_basis, kappa_day):
    """

    :param kappa_basis: correction factors calculated for the reference to balance the different LED light intensity
    :param kappa_day:   correction factors calculated for the actual measurement day
    :return:
    """
    return kappa_basis / kappa_day


def corr_factor(standard, valuetable, info, info_basis, spectra_path, reference_correction, path_saving,
                full_calibration=True, plot=True, save=True):
    """
    Correction factors calculated against the internal quantum counter (rhodamine 101). The measurement data are
    normalized against the results of LED 453 nm.
    :param standard:            which fluorescence standard is used for the calibration
    :param valuetable:          value table of the standard calculated before
    :param info:                global information about the sample
    :param info_basis:
    :param spectra_path:
    :param reference_correction:
    :param full_calibration     if the whole range is calibrated -> use another saving path
    :param plot:                plotting of the reference vs. measured data
    :param save:                option to save the correction factors
    :return:
            ex_standard_norm:   value table of the normalized excitation spectrum of the chosen reference
            index_value:        index values of the LEDs according to reference excitation spectrum
            kappa:              calculated correction factors of the actual standard measurement to the excitation
                                spectrum
    """

    # load normalized spectrum of standard and correction factors for the reference as basis
    if standard == 'rhodamin101' or standard == 'rhodamine101' or standard == 'Rhodamin101' or standard == 'Rhodamine101':
        standard_exp = 'rhodamine'
        standard_name = spectra_path + '160902_Rhodamine101_12mM_absorbed_light.txt'
        ex_standard = pd.read_csv(standard_name, index_col=0)
        ref1 = reference_correction
        kappa_basis = pd.read_csv(ref1, sep='\t', index_col=0)
    else:
        raise ValueError('The standard you choose was not in the dictionary')
    index_ = []
    for i in ex_standard.index:
        index_.append(i.round(0))
    ex_standard.index = index_
    # dimension of normalized absorption spectrum is [1]
    ex_standard_norm = ex_standard / ex_standard.max()

    # find index value (dimension [% or 1]) for the LEDs in the normalized absorption spectrum
    # wavelength of LED used in the set up
    wl = info['wavelength']
    # index value for normalized standard; dimension [1 or %]
    index_value = pd.DataFrame(np.zeros(8), index=info['LED']).T
    for p in range(len(wl)):
        if wl[p] in ex_standard_norm.index:
            index_value.ix[0, p] = ex_standard_norm.ix[wl[p], 0]
        else:
            index_value[info['wavelength'][p]] = 0

    # Normalize value table to compare the data with the absorption spectra. For inter-comparability choose the maximum.
    # Dimension [1 or %]
    valuetable_norm = (valuetable.T / valuetable.max(axis=1)).T

    if plot is True:
        f, ax1 = plt.subplots(figsize=(7.5, 4))

        # plotting amount of absorbed light and measurement data of the fluorescence standard
        ax1.plot(ex_standard_norm.index, ex_standard_norm, lw=1.5, color='black', alpha=0.8)
        for x in range(len(valuetable_norm.columns)):
            ax1.plot(wl[x], valuetable_norm.ix[50, x], lw=0, color=info['LED_color'][x], marker='h', markersize=13)

        plt.xlim(300, 750)
        y_max = valuetable_norm.max().max() * 1.05
        plt.ylim(0, y_max)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        minorLocatorx = MultipleLocator(20)
        minorLocatory = MultipleLocator(0.1)
        ax1.xaxis.set_minor_locator(minorLocatorx)
        ax1.yaxis.set_minor_locator(minorLocatory)
        ax1.tick_params(axis='both', which='major', labelsize=15, pad=8, right='on')
        ax1.tick_params(axis='both', which='minor', direction='in', pad=8, right='on')
        ax1.xaxis.set_ticks_position('both')
        plt.xlabel('Wavelength [nm]', fontsize=14)
        plt.ylabel('Fluorescence intensity [a.u.]', fontsize=14)

        plt.title('Absorbed light of {} at 50mA vs. measured intensity'.format(info['fluor_standard']), fontsize=13)
        plt.legend(['absorbed light', valuetable.columns[0], valuetable.columns[1],
                    valuetable.columns[2], valuetable.columns[3], valuetable.columns[4], valuetable.columns[5],
                    valuetable.columns[6], valuetable.columns[7]], frameon=True, loc='upper center',
                   bbox_to_anchor=(1.05, 1.), fontsize=11)
        plt.subplots_adjust(left=0.12, right=0.8, top=0.9, bottom=0.15)

    # calculate LED-correction-factors (kappa, k) for inter-comparability based on the amount of absorbed light and
    # the measurement results of the sample
    kappa = valuetable_norm.copy()
    for e, t in enumerate(kappa.columns):
        # index_value (soll-wert; [1 or %]) / normalized and measured value (ist-wert; [1 or %]) = correction [rfu]
        kappa.ix[:, e] = index_value.ix[0, e] / valuetable_norm.ix[:, e]
    kappa.columns = wl
    kappa = kappa.sort_index(axis=1)
    kappa_norm = (kappa.T / kappa.max(axis=1)).T

    # sort wavelength and combine with 'nm'
    wl_nm = []
    for p in range(len(kappa.columns)):
        wl_nm.append(str(kappa.columns[p]) + ' nm')
    kappa.columns = wl_nm
    kappa_norm.columns = wl_nm
    kappa = kappa.round(5)
    kappa_norm = kappa_norm.round(5)
    reference_day = info_basis['measurement_day'][0:4] + '-' + info_basis['measurement_day'][4:6] + '-' + \
                    info_basis['measurement_day'][6:8]

    # calculate LED-correction-factors (kappa, k') based on the reference sample (basis)
    unit = 'nW'
    correction_day = corr_factor_deviation(kappa_basis, kappa)
    correction_day = correction_day.round(5)
    correction_day.ix['Basis', :] = [standard, reference_day, unit, 'NaN', 'NaN', 'NaN', 'NaN', 'NaN']
    kappa.ix['Basis', :] = [standard, reference_day, unit, 'NaN', 'NaN', 'NaN', 'NaN', 'NaN']
    kappa_norm.ix['Basis', :] = [standard, reference_day, unit, 'NaN', 'NaN', 'NaN', 'NaN', 'NaN']
    correction_day = correction_day.dropna()

    # save correction factors of the day
    if save is True:
        path = path_saving + 'correctionfactor/'
        save_name = path + info['measurement_day'][0:-4] + '_' + 'LED_correction' + '_' + standard + '_spectrum.txt'
        kappa.to_csv(save_name, sep='\t')


    # direct output in the notebook
    print('Daily measurement deviation compared to the reference for {} at {}'.format(info['fluor_standard'],
                                                                                      reference_day))
    a = np.arange(correction_day.index[0], correction_day.index[-2], math.ceil((len(correction_day) + 1 +
                                                                           correction_day.index[0]) / 5))
    aa = []
    aa.append(a[0])
    for i in range(len(a)):
        if i > 0:
            aa.append(math.ceil(a[i] / 10) * 10)
    print(tabulate(correction_day.ix[aa, :], headers=[correction_day.columns[0], correction_day.columns[1],
                                            correction_day.columns[2], correction_day.columns[3],
                                            correction_day.columns[4], correction_day.columns[5],
                                            correction_day.columns[6], correction_day.columns[7]],
                   tablefmt="rst", numalign='right', stralign='right'), '\n')

    return ex_standard_norm, index_value, kappa, kappa_norm


##########################################################################################################
# Final and combining calibration function
##########################################################################################################
def calibration(sample_path, reference_path, reference_correction, spectra_path, device=1, device_ref=1,
                full_calibration=False, plot=False, save=False):
    """

    :param sample_path:
    :param reference_path:
    :param reference_correction:
    :param spectra_path:
    :param device:              integer; which device was used for the actual measurement.
    :param device_ref:          integer; which device was used for the reference measurement.
    :param  full_calibration:   polynomial fit between 10 - 97mA if True, otherwise linear fit between 10-50 mA
    :param lightintensity:
    :param plot:
    :param save:
    :return:
            ex_standard_norm:   value table of the normalized excitation spectrum of the chosen reference
            index_value:        index values of the LEDs according to reference excitation spectrum
            kappa:              calculated correction factors of the actual standard measurement to the excitation
                                spectrum
    """

    # load measurement files of the reference
    sample = meas_file(sample_path)

    component = sample_path.split('/')
    entry = component.index('excitation-site')
    path_saving = ''
    for i in range(entry+2):
        path_saving += component[i] + '/'

    # info about sample file
    info = info_file(sample['basename'][0])

    # device correction to which reference?
    [valuetable_basis, table_basis, RG665_basis, RG9_basis, basis_name,
     info_basis, regression_basis] = calibration_basis(reference_path, device_ref=device_ref,
                                                       full_calibration=full_calibration)

    # correction of the measurement data to a defined basis
    [valuetable_sample, RG665_sample, RG9_sample] = calibration_actual(sample_path, valuetable_basis, table_basis,
                                                                       basis_name, RG9_basis, device=device,
                                                                       full_calibration=full_calibration)

    [ex_standard_norm, index_value, kappa, kappa_norm] = corr_factor(info['fluor_standard'], valuetable_sample, info,
                                                                     info_basis, spectra_path, reference_correction,
                                                                     path_saving=path_saving,
                                                                     full_calibration=full_calibration,  plot=plot,
                                                                     save=save)

    return ex_standard_norm, index_value, kappa, kappa_norm, valuetable_sample, full_calibration


#################################################################################################
# emission calibration
#################################################################################################
def emission_calibration(path, emissionfilter, device_number=1, save=True):

    # sample information
    d = meas_file(path)
    info = info_file(d['basename'][0])

    # channel description
    channel_ = pd.read_csv(d['basename'][0], nrows=1, sep='\t', usecols=[0, 1, 2, 3, 4, 5, 6, 7]).ix[0].tolist()
    channel = []
    for p in channel_:
        channel.append('ch' + p.split(' ')[-1].split('_')[1])

    matrix = pd.DataFrame(np.zeros(shape=(2, 8)), index=['Filter', 'factor'], columns=channel)
    matrix.ix['Filter', :] = emissionfilter

    for u in d.index:
        w = signal_calculation(d['basename'][u], info['blank'], info['LED'], info['current'])
        for i in range(len(w.columns)): # i position of LED
            if w.ix['mean', i] <= 1:
                pass
            else:
                matrix.ix['factor', channel[i]] = w.ix['mean', i]

    matrix_norm = matrix.copy()
    matrix_norm.ix['factor',:] = matrix.ix['factor'] / matrix.ix['factor'].min()
    for i in range(len(matrix_norm.ix['factor'])):
        matrix_norm.ix['factor', i] = matrix_norm.ix['factor', i].round(1)

    if save is True:
        component = path.split('/')
        entry = component.index('emission-site')
        path_saving = ''
        for i in range(entry+1):
            path_saving += component[i] + '/'
        date = info_file(d['basename'][0])['name'].split('_')[0][:8]
        name_ = str(date) + '_emission_device-' + str(device_number) + '.txt'
        name = path_saving + name_
        matrix_norm.to_csv(name, sep='\t')
        print('saving done')

    return matrix, matrix_norm
