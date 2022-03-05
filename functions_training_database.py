__author__ = 'silviazieger'
__project__ = 'SCHeMA_ALPACA'

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math
import os

from glob import glob
from time import gmtime, strftime
from termcolor import cprint
from tabulate import tabulate


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
                  "593 nm": '#FFD500',
                  "640 nm": '#FF2100',
                  "652 nm": '#FF0000'}


def rearrange_datamatrix(data):
    d1 = data.iloc[:, 0:2]
    d2 = data.iloc[:, 2:4]
    d3 = data.iloc[:, 4:6]
    d4 = data.iloc[:, 6:8]
    d5 = data.iloc[:, 8:10]
    d6 = data.iloc[:, 10:12]
    d7 = data.iloc[:, 12:14]
    d8 = data.iloc[:, 14:16]
    ld = [d1, d2, d3, d4, d5, d6, d7, d8]

    return ld


def LED_Filter(name):
    """

    :param name:
    :return:
    """

    diodeI = pd.DataFrame(name[0:2], index=['PD1', 'PD1'])
    diodeII = pd.DataFrame(name[2:4], index=['PD2', 'PD2'])
    diodeIII = pd.DataFrame(name[4:6], index=['PD3', 'PD3'])
    diodeIV = pd.DataFrame(name[6:], index=['PD4', 'PD4'])
    photodiode = pd.concat([diodeI, diodeII, diodeIII, diodeIV])
    i = 0
    for el, i in enumerate(photodiode[0]):
        if i == '640 nm':
            rg9 = photodiode.index[el]
    RG9 = photodiode.ix[rg9, 0].tolist()
    RG665 = photodiode[0].tolist()
    RG665.remove(RG9[0])
    RG665.remove(RG9[1])

    return RG9, RG665


def info_about_file(filename):
    """

    :param filename:
    :return:
    """
    dd = os.path.basename(filename).split('.')[0]
    name = dd.split('_')[1]
    date = dd.split('_')[0]

    return dd, name, date


def info_about_file_extend(filename, header, blank_mean_ex, blank_std_ex, pumprate=None, unit_blank=None):
    """

    :param filename:
    :param header:
    :param blank_mean_ex:
    :param blank_std_ex:
    :param pumprate:
    :param MAZeT:       internal signal amplification in Ohm
    :return:
    """
    dd = os.path.basename(filename).split('.')[0]
    name = dd.split('_')[1]
    date = dd.split('_')[0]

    gen_info = pd.read_csv(filename, sep='\t', header=None, nrows=1, converters={0: lambda x: x[2:]})
    amplif = int(gen_info.ix[0, 0].split('=')[1][:-1])            # Ohm
    amplif_unit = gen_info.ix[0, 0].split('=')[1][-1]
    # multipling MAZeT amplification in order to obtain amplification in Ohm
    if amplif_unit == 'M':
        amplif = int(amplif * 1E6)
    elif amplif_unit == 'k':
        amplif = int(amplif * 1E3)

    if not pumprate:
        pumprate = float(gen_info.ix[0, 2].split('=')[1])  # mL/min

    current = []  # mA
    for i in header.ix[2, :]:
        current.append(int(float(i.split('=')[1].split('mA')[0])))
    ADC = []  # V
    for l in header.ix[3, :]:
        ADC.append(l.split(' ')[-1])

    blank_mean_header = []
    blank_std_header = []
    unit_blank_header = []
    # Extract the blank calculated and stored in the header
    for k in header.ix[4, :]:
        blank_mean_header.append(float(k.split('=')[1].split('+/-')[0]))
        blank_std_header.append(float(k.split('=')[1].split('+/-')[1][:-2]))
        unit_blank_header.append(k.split('=')[1][-2:])

    if unit_blank_header[0] == 'pA' or unit_blank_header[0] == 'pW':
        for p, q in enumerate(blank_mean_header):
            blank_mean_header[p] = (q / 1000)
            unit_blank_header = 'nW'
        for p, q in enumerate(blank_std_header):
            blank_std_header[p] = (q / 1000)
            unit_blank_header = 'nW'

    # combine blank from external file and from header if both are necessary
    if blank_mean_ex:
        blank_mean = [sum(x) for x in zip(blank_mean_header, blank_mean_ex)]
        blank_std = [sum(x) for x in zip(blank_std_header, blank_std_ex)]
    else:
        blank_mean = blank_mean_header
        blank_std = blank_std_header

    LED_wl = []
    LEDs = []
    for e in header.ix[1, :]:
        LED_wl.append(int(e.split(' ')[-2]))
        LEDs.append(e.split(' ')[-2] + ' nm')

    if unit_blank is None:
        unit_blank = unit_blank_header

    return dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, amplif, pumprate


def read_rawdata(filename, blank_corr=True, blank_mean_ex=None, blank_std_ex=None, plot_raw=False):
    """ Reads one data file and loads data within this file. Optionally the data could be corrected by the mean value
    of the blank.
    :param filename:        path to the file and name of file
    :param additional:      additional offset-compensation
    :param co:              path to the offset-compensation optimisation measurement
    :param factor:          float; can be used to amplify the light-measurement, when the offset_compensation is not
                            working properly
    :param: blank:          if the separate blank calculation based on an external file if preferred. Please refer the
                            path.
    :param blank_corr:      optional blank correction of data
    :param blank_mean_ex:
    :param blank_std_ex:    optionally definition of the deviation of the blank,'cause the calculated value is not valid
                            at the moment
    :param plot_raw:        time drive plot of this file
    :return: pandas.DataFrame:  containing the processed data for one algal sample at each LED
    """

    # load name of the file and slide it into subsections to extract the file information.
    [dd, algae, date] = info_about_file(filename)

    # current version of the data file
    # read file with the light-data and the dark-data and the header as well in a separate file.
    # for the signal processing, subtract the dark-offset from the light value
    data_light = pd.read_csv(filename, sep='\t', skiprows=6, encoding="latin-1",
                             usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
    data_dark = pd.read_csv(filename, sep='\t', skiprows=6, usecols=[0, 16, 17, 18, 19, 20, 21, 22, 23],
                            encoding="latin-1")
    header_ = pd.read_csv(filename, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]},
                          encoding="latin-1")
    header = header_.ix[:, :7]

    # extracting LED information and signal unit from header
    unit = data_light.columns[1].split(' ')[1][1:3]

    [dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, MAZeT,
     pumprate] = info_about_file_extend(filename, header, blank_mean_ex=blank_mean_ex, blank_std_ex=blank_std_ex,
                                        pumprate=None)

    # off-set compensation of the recorded data
    data = data_light.copy()
    i = 0
    for li, j in enumerate(data_light.columns):
        if li % 2 != 0:
            data.ix[:, li] = pd.DataFrame(data_light.ix[:, li] - data_dark.ix[:, (i + 1)])
            i += 1

    # extracting each time and LED pair, recombinant and concatenate them afterwards
    # blank correction of the raw data selecting the LED (odd columns) and subtract the blank
    ld = rearrange_datamatrix(data)

    data_corr = pd.concat([i.set_index(i.columns[0]) for i in ld], axis=1)
    data_corr.columns = LEDs

    # Warning if one channel is saturated
    for i, c in enumerate(data):
        if i < 16:
            if 0.5 in data[c].values and data[c].value_counts(normalize=True)[0.5] > 0.01:
                print("Warning! Photodiode {} is saturated for {} {}/{}/{}".format(
                    data_corr.columns[math.trunc(i/2)], algae, date[4:6], date[6:8], date[:4]))
            elif 0.25 in data[c].values and data[c].value_counts(normalize=True)[0.25] > 0.01:
                print("Warning! Photodiode {} might be saturated {} {}/{}/{}".format(
                    data_corr.columns[math.trunc(i/2)], algae, date[4:6], date[6:8], date[:4]))

    if blank_corr:
        # first use blank stored in header (blank_mean_header) and, additionally, use the blank from external blank file
        # (blank_mean_ex; optional)!
        data_corr = data_corr - blank_mean
    data_corr.name = algae

    # plotting raw data
    if plot_raw:
        color_LED = []
        for i in data_corr.columns:
            color_LED.append(led_color_dict[i])

        f, ax = plt.subplots()
        mngr = plt.get_current_fig_manager()
        # to put the screen into a defined position: (x,y, width, height)
        mngr.resize(650, 400)
        # plotting spectra
        for c, l in zip(color_LED, data_corr):
            data_corr[l].dropna().plot(ax=ax, color=c, linewidth=1.75, fontsize=12)
            plt.xlabel('Time [s]', fontsize=13)
            plt.ylabel('Intensity [{}]'.format(unit), fontsize=13)
            plt.legend(loc=0, ncol=1, frameon=True, fontsize=12)     # bbox_to_anchor=(1.05, 0.8) loc='upper center'

        if blank_corr:
            plt.title("Blank corrected data of {} {}/{}/{} {}:{}h".format(algae, date[6:8], date[4:6], date[:4],
                                                                          date[8:10], date[10:12]), fontsize=13)
        else:
            plt.title("Raw data of {} without blank correction".format(algae), fontsize=13)
        plt.tight_layout()

    return data_corr, header, unit


def emission_correction_table(df, device, RG9, RG665, led_order, em_path=None):
    """

    :param df:
    :param device:
    :param RG9:                 list of LEDs which are placed at the RG9 emission filter
    :param RG665:               list of LEDs which are placed at the RG665 emission filter
    :param led_order:
    :param em_path:             path to a specific file containing (emission) correction factors of the device.
                                The form of the file name is typically: '201705_device_emission_device-1.txt'
    :return:
    """
    # Load emission factors from file
    if em_path is None:
        raise ValueError('Specific filename for emission correction is required!')

    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = led_order

    df_em = df.copy()
    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9). Dimension = 1
    for i in RG9:

        df_em[i] = df[i].values / balance_factor.ix[int(device), i]
    for i in RG665:
        df_em[i] = df[i].values / balance_factor.ix[int(device), i]

    return df_em


def correction_led_table(df, kappa_spec, current, peakcolumns, full_calibration=True):
    """ Balance the LED-intensity based on the correction factors (kappa) calculated by the mean of the internal quantum
    counter.
    :param df:
    :param kappa_spec:
    :param current:
    :param peakcolumns:
    :param kappa_file:
    :param full_calibration:
    :return:
    """
    if kappa_spec is None:
        raise ValueError('Specific file for excitation correction is required! The typical filename is '
                         '20171001_LED_correction_rhodamine101_spectrum.txt')

        # automatically chosen excitation-correction file
        # no specified correction factor. load the factor according to the date of the measurement file.
        #if full_calibration is False:
        #    # linear fit between 30-50mA
        #   if os.path.exists(kappa_file) is True:
        #       kappa = pd.read_csv(kappa_file, sep='\t', index_col=0)
        #    else:
        #        print("ERROR! No such file in directory!")
        #       return
        #else:
        #    kappa = pd.read_csv(kappa_file, sep='\t', index_col=0)
    else:
        # specific file for excitation
        kappa = pd.read_csv(kappa_spec, sep='\t', index_col=0)

    # Preparation of data frames so you won't overwrite anything
    corr_factor = kappa.ix[:-1, :].astype(float)
    corr_factor = corr_factor.set_index(corr_factor.index.astype(int))
    df_led_corr = df.copy()
    df = pd.DataFrame(df)

    if not current:
        if full_calibration is True:
            current = [97]*8
        else:
            current = [50]*8

    # Correction of the LED intensities for standardizing the measurement and inter-comparability.
    # Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum counter) and multiply the
    # factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
    if current[0] not in corr_factor.index:
        print("WARNING! Correction not processed! No correction factor for {}mA in calibration file!".format(current[0]))
        pass
    else:
        # preparation of LED current; default type is list but for manual input it might be just one integer
        if type(current) == float or type(current) == int:
            current = [int(current)] * 8
            current = pd.DataFrame(current, index=peakcolumns).T
        elif type(current) == list:
            current = pd.DataFrame(current, index=peakcolumns).T

        # multiplication of LED correction factor and LED value
        for k in current.columns:                           # k: LED_wl
            if k not in corr_factor.columns:
                print('\n', 'Warning! No correction factor for LED {}'.format(k))
                df_led_corr[k] = df[k] * 1.0E-3
            else:
                df_led_corr[k] = df[k] * corr_factor.ix[current.ix[0, k], k]

    return df_led_corr


def plot_timedrive(df, name, date, unit, blank_corr, fontsize_=12):
    xcoords = []

    fig, ax = plt.subplots(figsize=(5, 3))
    color_LED = []
    for i in df.columns:
        color_LED.append(led_color_dict[i])

    # plotting spectra
    ylim_max = pd.DataFrame(np.zeros(shape=(len(df.columns), 1)), index=df.columns).T
    ylim_min = pd.DataFrame(np.zeros(shape=(len(df.columns), 1)), index=df.columns).T

    for c, p in zip(color_LED, df):
        if df[p].dropna().empty is True:
            df[p][np.isnan(df[p])] = 0
            df[p].plot(ax=ax, color=c, linewidth=1.75)
        else:
            df[p].dropna().plot(ax=ax, color=c, label=p, linewidth=1.75)
            ylim_max[p] = df[p].dropna().max()
            ylim_min[p] = df[p].dropna().min()

    # General layout-stuff
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Rel. Fluorescence intensity [{}]'.format(unit))
    ax.legend(loc=0, ncol=1, frameon=True, fancybox=True, framealpha=0.5,
              fontsize=9)  # 'upper center', bbox_to_anchor=(1.08, 1.)

    # Define plotting area. Default is 2 but if max value is higher it has to be rearranged
    x_max = df.index[-1] * 1.05
    x_min = np.abs(df.index[0]) - np.abs(df.index[-1]) * 0.05
    ax.set_xlim(x_min, x_max)
    ax.tick_params(direction='in', labelsize=fontsize_ * 0.8, top=True, right=True)

    y_max = ylim_max.max(axis=1).values[0] * 1.05
    y_min = ylim_min.min(axis=1).values[0] * 1.05
    ax.set_ylim(y_min, y_max)
    ax.set_title("{} {}/{}/{} {}:{}h - \n Select time range for sample and "
                 "blank.".format(name, date[6:8], date[4:6], date[:4], date[8:10], date[10:12]),
                 fontsize=11)

    fig.tight_layout()
    fig.canvas.draw()
    plt.show(block=False)

    def onclick(event):
        xcoords.append(event.xdata)

    if blank_corr is True:
        limit = 4
    else:
        limit = 2
    while len(xcoords) < limit:
        fig.canvas.mpl_connect('button_press_event', onclick)
        fig.canvas.flush_events()

    for i in xcoords:
        ax.axvline(x=i, color='k', lw=.5)

    ax.axvspan(xcoords[0], xcoords[1], color='grey', alpha=0.5)
    ax.axvspan(xcoords[2], xcoords[3], color='grey', alpha=0.5)

    fig.tight_layout()
    plt.show()

    return fig, ax, xcoords


def prescan_load_file(filename, kappa_spec=None, pumprate=None, correction=True, em_path=None,
                      full_calibration=False, blank_corr=True, blank_mean_ex=None, blank_std_ex=None, unit_blank=None):
    """

    :param filename:
    :param kappa_spec:
    :param pumprate:
    :param correction:
    :param em_path:             the specific path to an txt-file containing the emission corrections for a specific
                                ALPACA device. The filename must include the device-number as the following:
                                201705_device_emission_device-1.txt
    :param full_calibration:
    :param blank_corr:
    :param blank_mean_ex:
    :param blank_std_ex:
    :param unit_blank:
    :return:
    """
    # ---------------------------------------------------------------------------------------------------------
    # Load data file, which is optionally blank corrected.
    # signal (optionally blank corrected), header and unit of measurement signal (nW or pW)
    [l, header, unit] = read_rawdata(filename=filename, plot_raw=False, blank_corr=blank_corr,
                                     blank_mean_ex=blank_mean_ex, blank_std_ex=blank_std_ex)

    # ensure that everything is calculated in nW
    if unit == 'nW':
        l_ = l
    elif unit == 'pW':
        l_ = l.copy()
        for i in l.columns:
            for k in l.index:
                l_.ix[k, i] = l.ix[k, i] / 1000
        unit = 'nW'
    elif unit == 'µW':
        l_ = l.copy()
        for i in l.columns:
            for k in l.index:
                l_.ix[k, i] = l.ix[k, i] * 1000
        unit = 'nW'

    # general information about the file. The blank value is a combination of header and external file or just extracted
    # from file, respectively
    path = os.path.dirname(filename)
    [dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, amplif,
     pumprate] = info_about_file_extend(filename=filename, header=header, blank_mean_ex=blank_mean_ex,
                                        blank_std_ex=blank_std_ex, pumprate=pumprate, unit_blank=unit_blank)
    firstline = pd.read_csv(filename, sep='\t', header=None, nrows=1, converters={0: lambda x: x[2:]})

    # defining measurement time and volume based on pump speed
    t = l_.index[-1] / 60  # time in minutes
    volume = round(pumprate * t, 2)  # volume in mL

    # ------------------------------------------------------------------------------------------------------------
    # Correct all measured data along the time-drive, i.e. emission-site with defined values and on the excitation-site
    # with correction factors from rhodamine101 12mM.
    [rg9_sample, rg665_sample] = LED_Filter(l_.columns)

    if correction is True:
        device = np.int(em_path.split('device-')[-1].split('.')[0])

        # Emission-site correction: Balance different transmission properties of the emission filters if correction is
        # True. Dimension of correction factor is [1] or [%]
        l_em_balanced = emission_correction_table(l_, device, rg9_sample, rg665_sample, led_order=LEDs, em_path=em_path)
        blank_mean_ = pd.DataFrame(blank_mean, index=LEDs)
        blank_em_bal = emission_correction_table(blank_mean_.T, device, rg9_sample, rg665_sample, led_order=LEDs,
                                                 em_path=em_path)
        # Excitation-site correction: Correction of the LED intensities for standardizing the measurement and
        # inter-comparability. Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum
        # counter) and multiply the factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
        # Dimension of correction factor is []
        l_corr = correction_led_table(df=l_em_balanced, kappa_spec=kappa_spec, current=current, peakcolumns=l_.columns,
                                      full_calibration=full_calibration)
        blank_corrected = correction_led_table(df=blank_em_bal, kappa_spec=kappa_spec, current=current,
                                               peakcolumns=l_.columns, full_calibration=full_calibration).values[0]
    else:
        l_corr = l_
        if type(blank_mean) == list:
            blank_corrected = blank_mean
        else:
            blank_corrected = blank_mean.tolist()
    unit_corr = unit

    return l_, l_corr, header, firstline, current, date, name, blank_mean, blank_std, blank_corrected, rg9_sample, \
           rg665_sample, volume, pumprate, unit, unit_corr, unit_blank, path


def mean_conversion(led_order, rg665, rg9, kappa_spec, current, unit_blank, em_path, full_calibration=False,
                    blank_mean=None, blank_std=None, correction=True, device=1):
    # convert depending  on unit into nW:
    if unit_blank == 'nW':
        pass
    elif unit_blank == 'pW':
        # from 1pW into 1nW
        blank_mean = [i / 1000 for i in blank_mean]
        blank_std = [i / 1000 for i in blank_std]
        unit_blank = 'nW'
    elif unit_blank == 'µW':
        # from 1µW into 1nW
        blank_mean = [i * 1000 for i in blank_mean]
        blank_std = [i * 1000 for i in blank_std]
        unit_blank = 'nW'

    # first correction then addition ("punkt vor strich"). Blank mean was (in case) corrected previously
    blank_mean = pd.DataFrame(blank_mean, index=led_order, columns=[int(device)]).T
    blank_std = pd.DataFrame(blank_std, index=led_order, columns=[int(device)]).T

    # correction of blank_std
    if correction is True:
        # Emission-site correction: Balance different transmission properties of the emission filters if correction is
        # True. Dimension of correction factor is [1] or [%]
        blank_em_bal = emission_correction_table(blank_std, device, rg9, rg665, led_order=led_order, em_path=em_path)

        # Excitation-site correction: Correction of the LED intensities for standardizing the measurement and
        # inter-comparability. Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum
        # counter) and multiply the factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
        # Dimension of correction factor is []
        blank_std = correction_led_table(df=blank_em_bal, kappa_spec=kappa_spec, current=current, peakcolumns=led_order,
                                         full_calibration=full_calibration)

        unit_blank = 'nW'

    return blank_mean, blank_std, unit_blank


def detection(header, rg665, rg9, kappa_spec, current, unit_blank, em_path, full_calibration=False, blank_corr=True,
              blank_mean=None, blank_std=None, correction=True, device=1):

    """ Define the LoD from the raw data file depending if there's a blank correction or not. When the data are blank
    corrected you only need the standard deviation of the blank for the LoD. The mean values and the standard deviation
    of the blank measurement for each LED will be extracted to define the LoD (for a qualitative approach).
    If desired an externally calculated deviation of the blank could be included.
    :param:     filename:   path to the raw data
                blank_corr: if the data are blank corrected the LoD = 3*std(blank),
                            otherwise LoD includes the mean(blank)
                blank_std:  optionally definition of the deviation of the blank,'cause the calculated value is not
                            valid at the moment
                blank_mean:  optionally definition of the mean value of the blank,'cause the calculated value is not
                            valid at the moment
    :return:    list:       detection limits for each LED
    """
    led_order = []
    for led in header.ix[1, :]:
        led_order.append(led.split(' ')[2] + ' nm')

    [mean_ex_corr, std_ex_corr, unit_blank] = mean_conversion(led_order=led_order, rg665=rg665, rg9=rg9,
                                                              kappa_spec=kappa_spec, current=current, em_path=em_path,
                                                              unit_blank=unit_blank, full_calibration=full_calibration,
                                                              blank_mean=blank_mean, blank_std=blank_std,
                                                              correction=correction, device=device)

    # calculation of LoD depending whether the data are raw or blank corrected data
    LoD = []
    if blank_corr:
        # the mean value of the blank was subtracted before
        for i in range(len(mean_ex_corr.ix[mean_ex_corr.index[0], :].tolist())):
            LoD.append(3*std_ex_corr.ix[std_ex_corr.index[0], :].tolist()[i])
    else:
        # the mean value of the blank has to be taken into account
        for i in range(len(mean_ex_corr.ix[mean_ex_corr.index[0], :].tolist())):
            LoD.append(mean_ex_corr.ix[mean_ex_corr.index[0], :].tolist()[i] +
                       3*std_ex_corr.ix[std_ex_corr.index[0], :].tolist()[i])
    LoD = pd.DataFrame(LoD, index=led_order, columns=[int(device)]).T

    return LoD


def counter(l, LoD, volume, xcoords=None, division=None, warn=True):
    """ Counting measurement data which are higher than the LoD for each LED. The number of detected peaks will be
    stored as well as the intensities of the peaks. Finally the mean values for all LEDs will be calculated after
    the peak detection.
    :param:     l:          peak extracted data that should be counted
                LoD:        detection limit to define what is a peak
                division:   which LEDs are important
                warn:       warning can be hidden optionally. Default there's a warning
    :return:    c = pandas.Series:      counted peaks for a LED
                peak = pandas.DataFrame:detected peaks for each LED
                mean = pandas.Series:   mean values of all LEDs after the peak identification
    """

    if not division:
        division = [453, 593]
    if xcoords is None:
        # assume only sample is measured in the file. Blank is separate.
        xcoords = [l.index[0], l.index[-1], 0, 0]

    # extracting the peaks
    peak = l.copy()

    for i, k in enumerate(peak.columns):    # i = numbers, k = wavelengths
        peak[k][peak[k] < LoD[i]] = np.nan

    # counting peaks - when the pump rate is too slow, there are more measurement points for the same biomass
    # which has to be taken into account
    c = pd.Series([0]*len(peak.columns), index=peak.columns)
    for i in range(len(c)):                                         # number of rows in c (= number of LEDs, i = 0-7)
        cnm = l[c.index[i]].dropna()                                # copy of l but without NaN-entries
        for k in range(len(cnm) - 1):
            if cnm.iloc[k] < LoD[i] and cnm.iloc[k + 1] >= LoD[i]:  # single peaks found in the file
                c[c.index[i]] += 1
        if len(peak[c.index[i]].dropna()) >= len(cnm)/2:    # only signals > LOD found in the file -> high cell density
            c[c.index[i]] = '--'
            if warn is True:
                if c.index[i].split(' ')[0] == str(division[0]) or c.index[i].split(' ')[0] == str(division[1]):
                    print('Cell density at LED {} ≥ {} cells/{}mL!'.format(c.index[i], len(cnm)/2, volume))

    # calculate the mean value for each LED from the detected peaks and set negative values to zero
    if xcoords[0] >= xcoords[1]:
        mean_sample = peak.ix[xcoords[1]:xcoords[0], :].mean()
    elif xcoords[1] > xcoords[0]:
        mean_sample = peak.ix[xcoords[0]:xcoords[1], :].mean()
    if xcoords[2] > xcoords[3]:
        mean_blank = peak.ix[xcoords[3]:xcoords[2], :].mean()
    elif xcoords[3] > xcoords[2]:
        mean_blank = peak.ix[xcoords[2]:xcoords[3], :].mean()
    elif xcoords[2] == xcoords[3]:
        mean_blank = pd.Series([0]*len(mean_sample.index), index=mean_sample.index)

    for val in mean_blank.index:
        if math.isnan(mean_blank[val]) is True:
            mean_blank[val] = 0.
    mean = mean_sample - mean_blank

    mean[mean < 0] = 0
    for el in range(len(peak.columns)):
        if np.isnan(mean.ix[el, :]):
            if warn is True:
                print('No peaks found for LED {}'.format(mean.index[el]))
            mean.ix[el] = 0

    return c, peak, mean


def signal_precision(mean):
    """
    :param mean:    One column-DataFrame containing the average light intenisties for each LED
    :return unit:
    :return mean:
    """
    c1 = []
    c2 = []

    # basic unit nW
    for el in mean.index:
        for k in mean.columns:
            # store the wavelengths, for which the value is <0.1 in the list c1 to convert from nW to pW
            if mean.ix[el, k] < 0.1:
                c1.append(el)
            # store the wavelengths, for which the value is >100.0 in the list c2 to convert from nW to µW
            if mean.ix[el, k] > 100.0:
                c2.append(el)

    if not c1:  # signal intensity remain at 1nW
        unit = 'nW'
        if not c2:  # signal intensity remain at 1nW
            unit = 'nW'
        else:  # conversion 1nW-> µW, since signal intensity is to high
            mean = mean / 1000
            unit = 'µW'
    else:  # conversion 1nW-> pW, since signal intensity is to low
        mean = mean * 1000
        unit = 'pW'

    return unit, mean


def quotation(x, y, mean, name, threshold=None):
    """ Divide two values x, y and decide depending on the chosen threshold-pair.
    :param: x,y:        values that should be divided in the way: x/y
            mean:       DataFrame containing average fluorescence intensity at different excitation wavelengths
            threshold:  array f two thresholds for rhe decision if there are bacteria / algae present.
                        Thresholds depend on the chosen LED-filter setup
    :return: tuple:     containing the decision for cyanobacteria and algae as a string ('yes', or 'no')
    """
    cyano = '--'
    algae = '--'

    # set any mean value below zero as zero; negative intensity is senseless.
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    for i in mean.index:
        if mean.ix[i, 0] < 0:
            mean.ix[i, 0] = 0

    quot = x / y

    # basic decision if there's a photosynthetic active organism present in the sample
    result_txt = None
    print('\n')
    print('Results for {}'.format(name))

    if (mean.ix[453, 0] < 1.0E-5) or (mean.ix[438, 0] < 1.0E-5):
        cprint('--> No photosynthetic active organisms found', 'cyan')
        result_txt = '--> No photosynthetic active organisms found'
        cyano = 'no'
        algae = 'no'
        pass
    else:
        # case discrimination depending on q = x/y according to the given threshold
        # 1st case: no algae, but cyanobacteria little likelihood (contains chlorophyll-a which is excited at 435 nm)
        if quot == 0.0:
            if x == 0.0 and y > 0.0:
                cprint('--> No algae found. The likelihood for cyanobacteria is quite low', 'cyan')
                result_txt = '--> No algae found. The likelihood for cyanobacteria is quite low'
                cyano = 'might be'
                algae = 'no'
        # 2nd case: no cyanobacteria
        elif math.isinf(quot) or math.isnan(quot):
            if x == 0.0 and y == 0.0:
                cprint('--> Neither algae nor cyanobacteria identified', 'cyan')
                result_txt = '--> Neither algae nor cyanobacteria identified'
                cyano = 'no'
                algae = 'no'
            elif x > 0.0 and y == 0.0:
                cprint('--> No cyanobacteria, but algae identified', 'cyan')
                result_txt = '--> No cyanobacteria, but algae identified'
                cyano = 'no'
                algae = 'yes'
        # 3th case: no algae, but cyanobacteria
        elif quot < threshold[0]:
            cprint('--> Cyanobacteria, but no algae identified', 'cyan')
            result_txt = '--> Cyanobacteria, but no algae identified'
            cyano = 'yes'
            algae = 'no'
        # 4th case: algae but no cyanobacteria
        elif quot > threshold[1]:
            cprint('--> Algae (also Cryptophyta), but no cyanobacteria identified', 'cyan')
            result_txt = '--> Algae (also Cryptophyta), but no cyanobacteria identified'
            cyano = 'no'
            algae = 'yes'
        # 5th case: mixture of both is possible
        elif threshold[0] <= quot <= threshold[1]:
            cprint('--> Cyanobacteria and Cryptophyta potentially identified', 'cyan')
            result_txt = '--> Cyanobacteria and Cryptophyta potentially identified'
            cyano = 'yes'
            algae = 'yes'
        else:
            cprint('anything else...', 'cyan')
            result_txt = 'anything else...'
            cyano = '-'
            algae = '-'
            pass

    return cyano, algae, result_txt


def prescan_run_analysis(l_corr, xcoords, header, name, kappa_spec, correction, current, blank_corr, blank_mean,
                         blank_std, unit_blank, rg9_sample, rg665_sample, volume, output_result, em_path, division=None,
                         threshold=None, peak_detection=True):
    # Pre-definition of important variables
    device = np.int(em_path.split('device-')[-1].split('.')[0])
    if not division:
        division = [438, 526]
    # For LED setup 2. ration < 1 -> cyanobacteria, ratio > 5 algae. In between it could be both.
    # After Bilbao: 0.79 vs 5.31 is the exact threshold; even for just cropped files it is fine enough.
    if not threshold:
        if division == [453, 640]:
            threshold = [1, 1.16]
        elif division == [438, 526]:
            # threshold after analysing all measurements from Bilbao. When there is no air in the sample and the
            # offset compensation works properly, the threshold is 0.7 - 1.7 or 1.0 - 6.0, respectively; depending if a
            # peak detection is True or False.
            if peak_detection is True:
                threshold = [0.69, 0.83]
            else:
                threshold = [1.0, 6.0]

    # calculate mean values of (em- and ex-)corrected data according to selected sample and blank regions.
    if peak_detection is True:
        # Baseline correction relies on selected blank region (xcoords[3] and xcoords[4]). L_corr is corrected if
        # selected previously
        if xcoords[2] >= xcoords[3]:
            mean_blank_ex = l_corr.ix[xcoords[3]:xcoords[2], :].mean()
            std_blank_ex = l_corr.ix[xcoords[3]:xcoords[2], :].std()
        elif xcoords[3] > xcoords[2]:
            mean_blank_ex = l_corr.ix[xcoords[2]:xcoords[3], :].mean()
            std_blank_ex = l_corr.ix[xcoords[2]:xcoords[3], :].std()
        else:
            mean_blank_ex = None
            std_blank_ex = None

        # combine blank mean and std from header and from selected region. Blank mean must be corrected if
        # correction is chosen for the sample. Check if the unit is the same
        if mean_blank_ex.isnull().any():
            blank_mean_sum = blank_mean
            blank_std_combi = blank_std
        else:
            blank_mean_ = [sum(x) for x in zip(mean_blank_ex.tolist(), blank_mean)]
            blank_mean_sum = pd.DataFrame(blank_mean_, index=l_corr.columns)
            variance_ex = [p ** 2 for p in std_blank_ex.tolist()]
            variance = [p ** 2 for p in blank_std]
            variance_sum = [sum(x) for x in zip(variance_ex, variance)]
            blank_std_combi = [np.sqrt(y) for y in variance_sum]

        LoD = detection(header, kappa_spec=kappa_spec, current=current, em_path=em_path, device=device, rg9=rg9_sample,
                        full_calibration=False, blank_corr=blank_corr, blank_mean=blank_mean_sum, rg665=rg665_sample,
                        blank_std=blank_std_combi, unit_blank=unit_blank, correction=correction)

        # peak detection (Int. > LoD (peak)) and count number of peaks (c) and mean value of the peaks (mean)
        [c, peak, mean] = counter(l_corr, volume=volume, LoD=LoD.values[0], xcoords=xcoords, division=None, warn=True)
    else:
        LoD = pd.DataFrame([0] * 8, index=l_corr.columns).T
        # peak detection (Int. > LoD (peak)) and count number of peaks (c) and mean value of the peaks (mean)
        [c, peak, mean] = counter(l_corr, volume=volume, LoD=LoD.values[0], xcoords=xcoords, division=None, warn=True)

    mean_corr = (pd.DataFrame(mean))

    # ------------------------------------------------------------------------------------------------------------
    # Preparation of output: unit conversion from V to mV and definition of precision to maximal 5 decimals
    # (4 decimals are secure)
    wavelength = []
    mean_corr = mean_corr.sort_index(axis=0)
    wl = mean_corr.index

    # Rename the index by converting the string to an integer. Preparing step for LED-mean value division
    for el in range(len(mean_corr.index)):
        wavelength.append(int(mean_corr.index[el].split(' ')[0]))
    mean_corr.index = wavelength

    # check if the chosen LEDs are used in the measurement
    for el in range(len(division)):
        if division[el] not in mean_corr.index:
            raise ValueError("Chosen LED {} was not used in this measurement!".format(division[el]))

    # Creates the output file containing the decision if cyanobacteria and/or algae are present and also the mean
    # values of the chosen LEDs
    [unit, mean_corr] = signal_precision(mean_corr)

    # divide the chosen LEDs and act depending on the result. First entry is for the algae, second for the cyanos
    [cyano_res, algae_res,
     result_txt] = quotation(x=mean_corr.ix[division[0], 0], y=mean_corr.ix[division[1], 0], mean=mean_corr, name=name,
                             threshold=threshold)
    mean_corr = mean_corr.round(5)

    out = [['Cyano:', cyano_res, ' '], ['Algae:', algae_res, ' '],
           ['{} nm:'.format(division[0]), round(mean_corr.ix[division[0], 0], 2), c[str(division[0]) + ' nm']],
           ['{} nm:'.format(division[1]), round(mean_corr.ix[division[1], 0], 2), c[str(division[1]) + ' nm']],
           ]

    if output_result is True:
        print(tabulate(out, headers=['', 'mean value [{}]'.format(unit), 'cell density [cells/{} mL]'.format(volume)],
                       tablefmt="rst", numalign='right', stralign='right'))
    res = pd.DataFrame(out, columns=['', 'mean value [{}]'.format(unit), 'cell density [cells/{} mL]'.format(volume)])

    # combining results and mean values for the txt-file to be saved
    mean_index = pd.DataFrame(mean_corr.index.tolist())
    mean_values = pd.DataFrame(mean_corr.ix[:, 0].values)
    mean_conc = pd.concat([mean_index, mean_values], axis=1)
    mean_conc.columns = ['LED', 'mean value [{}]'.format(unit)]
    mean_corr.columns = [name]

    c_2 = pd.DataFrame(c).sort_index()
    c_ = pd.DataFrame(c_2.ix[:, 0].values, columns=["cell density [cells/{} mL".format(volume)])
    res_out = pd.concat([res, mean_conc, c_], axis=1)

    return mean_corr, peak, res_out, current, l_corr, unit, out, result_txt, c_2, LoD, mean_conc


def creating_training_objects(df, em_correction, kappa_, pumprate, correction=True, blank_corr=True, blank_mean_ex=None,
                              output_result=False):
    # loading file
    [l_, l_corr, header, firstline, current, date, name, blank_mean, blank_std, blank_corrected,
     rg9_sample, rg665_sample, volume, pumprate, unit, unit_corr, unit_blank,
     path] = prescan_load_file(filename=df, em_path=em_correction, kappa_spec=kappa_, pumprate=pumprate,
                               correction=correction, blank_corr=blank_corr, blank_mean_ex=blank_mean_ex,
                               blank_std_ex=blank_mean_ex)

    # select xdata for sample range and blank range
    fig, ax, xcoords = plot_timedrive(df=l_corr, name=name, date=date, unit=unit, blank_corr=blank_corr)

    # signal processing to determine realtive pigment pattern of the training object
    [mean_corr, peak, res_out, current, l_corr, unit, out, result_txt, c, LoD,
     mean_conc] = prescan_run_analysis(l_corr=l_corr, xcoords=xcoords, header=header, name=name, kappa_spec=kappa_,
                                       correction=correction, current=current, blank_corr=blank_corr, volume=volume,
                                       blank_mean=blank_mean, blank_std=blank_std, unit_blank=unit_blank,
                                       rg9_sample=rg9_sample, rg665_sample=rg665_sample, output_result=output_result,
                                       em_path=em_correction, peak_detection=True)

    return mean_corr
