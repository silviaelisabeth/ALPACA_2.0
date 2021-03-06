__author__ = 'silviaelisabeth'
__project__ = 'SCHeMA_algorithm_LDA'


import matplotlib.pyplot as plt
import numpy as np
from numpy import *
import pandas as pd
from glob import glob
import os.path
from pylab import *
from scipy.stats import *
import math
from time import time
import seaborn as sns
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import warnings
warnings.filterwarnings("ignore")

sns.set_context("paper", font_scale=2.5, rc={"lines.linewidth": 2})
sns.set_palette("colorblind", 10)
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
            "2b4": '593 nm',
            "3c1": '640 nm',
            "3c2": '652 nm'}

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

filters = ['RG665 - darkred', 'RG665 - darkred', 'RG665 - 2darkred', 'RG665 - 2darkred',
           'RG9 - darkred', 'RG9 - darkred', '2RG665 - darkred', '2RG665 - darkred']

filters_color_dict = {"ch01": 'darkred',
                      "ch02": 'Forestgreen',
                      "ch03": 'Steelblue',
                      "ch04": 'Goldenrod'}


#####################################################################################################################
# Loading of relevant files and parameters
#####################################################################################################################
def read_rawdata(filename, led_used, additional=False, co=None, factor=1., blank_corr=True, blank_mean_ex=None,
                 blank_std_ex=None, plot_raw=False):
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
                             usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]) * factor
    data_dark = pd.read_csv(filename, sep='\t', skiprows=6, usecols=[0, 16, 17, 18, 19, 20, 21, 22, 23],
                            encoding="latin-1") * factor
    header_ = pd.read_csv(filename, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]},
                          encoding="latin-1")
    header = header_.ix[:, :7]

    # extracting LED information and signal unit from header
    unit = data_light.columns[1].split(' ')[1][1:3]

    [dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, MAZeT,
     pumprate] = info_about_file_extend(filename, header, led_used, blank_mean_ex=blank_mean_ex,
                                        blank_std_ex=blank_std_ex, pumprate=None, MAZeT=None)

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


def read_peak(filename, volume, kappa_spec, correction, led_used, device=1., additional=False, blank=None,
              blank_corr=True, blank_mean_ex=None, blank_std_ex=None, normalize=False, full_calibration=False):
    """ Detects the data points over the detection limit (=peak) from a raw data file and calculates the mean values
    for each LED
    :param:     filename:   path to the raw data file
                volume:
                blank_corr: optional blank correction. Default is True
                blank_mean: optionally definition of the mean value of the blank,'cause the calculated value is not
                            valid at the moment
                blank_std:  optionally definition of the deviation of the blank,'cause the calculated value is not
                            valid at the moment
                normalize:  optional normalisation of averaged signal intensities. Default is True
    :return:    pd.Series:  calculated mean values for each LED for one given sample
    """

    # load time drive data of a certain file
    [df, header, unit] = read_rawdata(filename, led_used=led_used, additional=additional, blank_corr=blank_corr,
                                      blank_mean_ex=blank_mean_ex, blank_std_ex=blank_std_ex, plot_raw=False)
    [dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, MAZeT,
     pumprate] = info_about_file_extend(filename, header, led_used,  blank_mean_ex=blank_mean_ex,
                                        blank_std_ex=blank_std_ex, pumprate=None, MAZeT=None)

    # Plotting of training objects to select sample range
    f, ax = plt.subplots(figsize=(7, 5))
    for i in df.columns:
        alg = df[i].dropna()
        ax.plot(alg.index, alg, color=led_color_dict[i], label=i)
    plt.tick_params(labelsize=12)
    plt.xlabel('Time [s]', fontsize=12)
    plt.ylabel('Fluorescence intensity', fontsize=12)
    plt.title('{} \n Select sample range (first) and then baseline for correction!'.format(name), fontsize=11)

    coords = []
    def onclick(event):
        global ix, iy
        ix, iy = event.xdata, event.ydata
        coords.append(ix)
        if len(coords) == 4:
            f.canvas.mpl_disconnect(cid)
        return coords

    cid = f.canvas.mpl_connect('button_press_event', onclick)
    plt.show()

    # control of coords
    for el in range(len(coords)):
        if coords[el] == None:
            coords[el] = 0
    while 1 < len(coords) < 4:
        coords.append(0)

    [rg9, rg665] = LED_Filter(LEDs)

    # extract the detection limit depending if there's a blank correction or not
    LoD = detection(header=header, rg665=rg665, rg9=rg9, kappa_spec=kappa_spec, date=date, led_used=led_used,
                    current=current, unit_blank=unit_blank, full_calibration=full_calibration, blank_corr=blank_corr,
                    blank_mean=blank_mean, blank_std=blank_std, correction=correction, device=int(device))
    print('227')
    print(df.columns)
    # extract the peaks in the raw data file
    [c, peak, mean] = counter(df, LoD=LoD.values[0], xcoords=coords, volume=volume, division=None, warn=False)
    print('230')
    # calculate the mean values for each LED from detected peaks
    mean_ = peak.mean().fillna(0)

    # normalize the data for one sample over the whole row
    if normalize is True:
        mean_ = mean_/mean_.max()
    mean_.set_index = df.name
    mean_.name = df.name
    print('239')
    return mean_


def read_directory(dirname, volume, kappa_spec, led_used, device=1., correction=False, additional=False,
                   blank_corr=True, blank_mean_ex=None, blank_std_ex=None, normalize=True, standardize=False,
                   full_calibration=False):
    """ Reads a directory and loads all data files. Returns a normalized data frame.
    Data could be standardized (combined with the normalization or without) if it is preferred

    :param: dirname:        path to data directory
            volume:
            blank_corr:     blank correction of the raw data desired?
            blank_mean:     give an external calculated average of the blank measurement
            blank_std:      give an external calculated deviation of the blank measurement
            normalize:      processing of the raw data, default is True
            standardize:    additional processing of (normalized) data, default is False
    :return: pandas.DataFrame:  containing the processed mean values for each algae sample at each LED
    """
    print('258')
    # load data by the mean of the function read_file. The data could be normalized over the row.
    l1 = [read_peak(i, led_used=led_used, volume=volume, kappa_spec=kappa_spec, correction=correction, device=device,
                    additional=additional, blank_corr=blank_corr, blank_mean_ex=blank_mean_ex,
                    blank_std_ex=blank_std_ex, normalize=normalize, full_calibration=full_calibration)
          for i in glob(dirname + '/*_*.txt')]
    print('264')
    current_extract = [current_extraction(p) for p in glob(dirname + '/*_*.txt')]
    date_extract = [date_extration(q) for q in glob(dirname + '/*_*.txt')]
    rg9 = [filter_extraction_rg9(q) for q in glob(dirname + '/*_*.txt')]
    rg665 = [filter_extraction_rg665(q, rg9) for q in glob(dirname + '/*_*.txt')]

    # combining mean values of trainings matrix
    df = pd.concat(l1, axis=1).T
    # set negative values to quasi-zero!
    df[df < 0] = 1E-9
    # combine current of different samples
    df_current = pd.concat(current_extract, axis=0)
    df_date = pd.DataFrame(date_extract)
    print('277')
    # execute standardization, if preferred for the algae sample. Transformation is necessary to calculate
    # the mean of the row (algae) instead of the columns (LEDs). Re-transformation is used afterwards to
    # obtain the common matrix.
    if standardize is True:
        df = ((df.T - df.T.mean())/df.T.std()).T
    print('283')
    return df, df_current, rg9[0], rg665[0], df_date


def filter_extraction_rg9(filename):

    header_ = pd.read_csv(filename, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]})
    header = header_.ix[:, :7]
    q1 = pd.DataFrame(header.ix[1, :][:2])
    q1.index = ['PD1', 'PD1']
    q2 = pd.DataFrame(header.ix[1, :][2:4])
    q2.index = ['PD2', 'PD2']
    q3 = pd.DataFrame(header.ix[1, :][4:6])
    q3.index = ['PD3', 'PD3']
    q4 = pd.DataFrame(header.ix[1, :][6:8])
    q4.index = ['PD4', 'PD4']
    photo = pd.concat([q1, q2, q3, q4])
    photo.columns = [0]
    photodiode = []
    for k in range(len(photo.index)):
        photodiode.append(photo.ix[k, 0].split(' ')[2] + ' nm')
    photodiode = pd.DataFrame(photodiode, index=photo.index)

    rg9 = []
    rg9_list = []
    rg9_list = []
    i = 0
    for el, i in enumerate(photodiode[0]):
        if i == '640 nm':
            rg9 = photodiode.index[el]
    rg9_list = photodiode.ix[rg9, 0].tolist()

    return rg9_list


def filter_extraction_rg665(filename, rg9):

    header_ = pd.read_csv(filename, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]})
    header = header_.ix[:, :7]
    q1 = pd.DataFrame(header.ix[1, :][:2])
    q1.index = ['PD1', 'PD1']
    q2 = pd.DataFrame(header.ix[1, :][2:4])
    q2.index = ['PD2', 'PD2']
    q3 = pd.DataFrame(header.ix[1, :][4:6])
    q3.index = ['PD3', 'PD3']
    q4 = pd.DataFrame(header.ix[1, :][6:8])
    q4.index = ['PD4', 'PD4']
    photo = pd.concat([q1, q2, q3, q4])
    photo.columns = [0]
    photodiode = []
    for k in range(len(photo.index)):
        photodiode.append(photo.ix[k, 0].split(' ')[2] + ' nm')
    photodiode = pd.DataFrame(photodiode, index=photo.index)

    rg665 = photodiode[0].tolist()
    rg665.remove(rg9[0][0])
    rg665.remove(rg9[0][1])

    return rg665


def date_extration(filename):
    """

    :param filename:
    :return:
    """
    dd_ = os.path.basename(filename).split('.')[0]
    dd = dd_.split('_')[0]

    return dd


def current_extraction(filename):
    """

    :param      filename:
    :return:    current_:
    """
    dd = os.path.basename(filename).split('.')[0]
    name = dd.split('_')[1]

    header_ = pd.read_csv(filename, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]})
    header = header_.ix[:, :7]

    LEDs = []
    for e in header.ix[1, :]:
        LEDs.append(e.split(' ')[-2] + ' nm')

    current = []  # mA
    for i in header.ix[2, :]:
        current.append(int(i.split('=')[1].split('mA')[0]))
    current_ = pd.DataFrame(current, index=LEDs, columns=[name]).T
    current_.set_index = name
    current_.name = name

    return current_


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


def info_about_file(filename):
    """

    :param filename:
    :return:
    """
    dd = os.path.basename(filename).split('.')[0]
    name = dd.split('_')[1]
    date = dd.split('_')[0]

    return dd, name, date


def info_about_file_extend(filename, header, led_used, blank_mean_ex, blank_std_ex, pumprate=None, MAZeT=None,
                           unit_blank=None):
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

    # reduce to channels which are used for evaluation
    current.pop(LEDs.index(list(set(LEDs) - set(led_used))[0]))
    blank_mean.pop(LEDs.index(list(set(LEDs) - set(led_used))[0]))
    blank_std.pop(LEDs.index(list(set(LEDs) - set(led_used))[0]))

    return dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, amplif, pumprate


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


def algae_dictionary(filename):
    """

    :param filename:
    :return:
    classes_dict:   dictionary containing genus names as keys and taxonomic level (phylum, class, order, family) as
                    value
    color_dict:     dictionary containing genus names as keys and colors as values
    genus_names:  list with the genus names
    """

    # load excel file with all information about algae genus
    qqt = pd.read_csv(filename, sep='\t', header=None, encoding="latin-1")

    # splitting table
    classes_dict = {}
    color_dict = {}
    colorclass_dict = {}

    re = qqt[0]
    key_list = re.values.tolist()
    re = qqt[1]
    values_list = re.values.tolist()
    re = qqt[2]
    color_list = re.values.tolist()
    genus_names = key_list

    # creating dictionary
    for key, value in zip(key_list, values_list):
        classes_dict[key] = value

    for key, value in zip(genus_names, color_list):
        color_dict[key] = value

    for key, value in zip(values_list, color_list):
        colorclass_dict[key] = value

    return classes_dict, color_dict, colorclass_dict, genus_names


def separation_level(separation, path):
    """ Loads the taxonomic and the color information as well of all algae samples. It returns dictioonarys which are
    needed for further analysis.
    :param separation:
    :return:
    classes_dict:       dictionary containing genus as keys and groups as information/values
    color_dict:         dictionary containing genus as keys and colors as information/values
    colorclass_dict:    dictionary containing groups as keys and colors as information/values
    genus_names:      list of all names used in the analysis
    """
    if separation == 'phylum':
        name = path + '170427_algalphylum.txt'
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(name)
    elif separation == 'class':
        name = path + '170427_algalclass.txt'
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(name)
    elif separation == 'order':
        name = path + '170427_algalorder.txt'
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(name)
    elif separation == 'family':
        name = path + '170427_algalfamily.txt'
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(name)

    return classes_dict, color_dict, colorclass_dict, genus_names


def led_reduction(LED380_checkbox, LED403_checkbox, LED438_checkbox, LED453_checkbox, LED472_checkbox,
                  LED526_checkbox, LED593_checkbox, LED640_checkbox):
    # reduce number of LEDs used for LDA
    led_used = pd.DataFrame(np.zeros(shape=(8, 1)),
                            index=['380 nm', '403 nm', '438 nm', '453 nm', '472 nm', '526 nm', '593 nm', '640 nm']).T

    if LED380_checkbox is True:
        led_used.ix[0, '380 nm'] = True
    else:
        led_used.ix[0, '380 nm'] = False
    if LED403_checkbox is True:
        led_used.ix[0, '403 nm'] = True
    else:
        led_used.ix[0, '403 nm'] = False
    if LED438_checkbox is True:
        led_used.ix[0, '438 nm'] = True
    else:
        led_used.ix[0, '438 nm'] = False
    if LED453_checkbox is True:
        led_used.ix[0, '453 nm'] = True
    else:
        led_used.ix[0, '453 nm'] = False
    if LED472_checkbox is True:
        led_used.ix[0, '472 nm'] = True
    else:
        led_used.ix[0, '472 nm'] = False
    if LED526_checkbox is True:
        led_used.ix[0, '526 nm'] = True
    else:
        led_used.ix[0, '526 nm'] = False
    if LED593_checkbox is True:
        led_used.ix[0, '593 nm'] = True
    else:
        led_used.ix[0, '593 nm'] = False
    if LED640_checkbox is True:
        led_used.ix[0, '640 nm'] = True
    else:
        led_used.ix[0, '640 nm'] = False

    return led_used


# #####################################################################################################################
# # Preparation of measurement and training database
# #####################################################################################################################
def pre_process(df, normalize=True, standardize=True):
    """ Normalisation and standardisation of sample data if necessary.
    :param: df:             raw data of the peaks detected in a sample combined in a pandas.DataFrame
            normalize:      normalisation of given samples along one row
            standardize:    standardisation of a given sample along one row
    :return:df = pandas.DataFrame of preprocessed data
    """
    # Same pre-processing for the sample as for the training data (normalized/standardized)
    if normalize is True:
        df = df / df.max()

    if standardize is True:
        df = ((df - df.mean())/df.std(axis=0))

    return df


def detection(header, rg665, rg9, kappa_spec, date, current, unit_blank, led_used, full_calibration=False,
              blank_corr=True, blank_mean=None, blank_std=None, correction=True, device=1):

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
        nm = led.split(' ')[2] + ' nm'
        if nm in led_used:
            led_order.append(nm)

    [mean_ex_corr, std_ex_corr, unit_blank] = mean_conversion(led_order=led_order, rg665=rg665, rg9=rg9,
                                                              kappa_spec=kappa_spec, date=date, current=current,
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
    print('699')
    if not division:
        division = [453, 593]
    if xcoords is None:
        # assume only sample is measured in the file. Blank is separate.
        xcoords = [l.index[0], l.index[-1], 0, 0]
    print('705')
    # extracting the peaks
    peak = l.copy()
    print('708')
    print(LoD)
    print(peak.columns)
    for i, k in enumerate(peak.columns):    # i = numbers, k = wavelengths
        peak[k][peak[k] < LoD[i]] = np.nan
    print('711')
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
                    print('Cell density at LED {} ??? {} cells/{}mL!'.format(c.index[i], len(cnm)/2, volume))
    print('725')
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
        mean_blank = pd.Series([0]*len(l.columns), index=mean_sample.index)
    print('737')
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
    print('749')
    return c, peak, mean


def mean_conversion(led_order, rg665, rg9, kappa_spec, date, current, unit_blank, full_calibration=False,
                    blank_mean=None, blank_std=None, correction=True, device=1):
    # convert depending  on unit into nW:
    if unit_blank == 'nW':
        pass
    elif unit_blank == 'pW':
        # from 1pW into 1nW
        blank_mean = [i / 1000 for i in blank_mean]
        blank_std = [i / 1000 for i in blank_std]
        unit_blank = 'nW'
    elif unit_blank == '??W':
        # from 1??W into 1nW
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
        blank_em_bal = emission_correction_table(blank_std, device, rg9, rg665, led_order=led_order)

        # Excitation-site correction: Correction of the LED intensities for standardizing the measurement and
        # inter-comparability. Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum
        # counter) and multiply the factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
        # Dimension of correction factor is []
        blank_std = correction_led_table(blank_em_bal, kappa_spec, date, current, peakcolumns=led_order,
                                         full_calibration=full_calibration)
        unit_blank = 'rfu'

    return blank_mean, blank_std, unit_blank


def emission_correction(mean, device, RG9_sample, RG665_sample, led_order):
    """
    :param      mean:           mean values of the LEDs in the right order (not sorted by wavelengths) as it was
                                measured
    :param      RG9_sample:     list of LEDs which are placed at the RG9 emission filter
    :param      RG665_sample:   list of LEDs which are placed at the RG665 emission filter
    :return:
    """
    # Load emission factors from file
    em_path = 'supplementary/calibration/emission-site/' + '20170505_emission_device-' + str(device) + '.txt'
    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = led_order

    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9)
    for i in RG9_sample:
        if i in mean.index:
            mean.ix[i, :] = mean.ix[i, :].values[0] / balance_factor.ix[int(device), i]
    for i in RG665_sample:
        if i in mean.index:
            mean.ix[i, :] = mean.ix[i, :].values[0] / balance_factor.ix[int(device), i]

    return mean


def emission_correction_table(df, device, RG9, RG665, led_order):
    """
    :param      mean:           mean values of the LEDs in the right order (not sorted by wavelengths) as it was
                                measured
    :param      RG9:            list of LEDs which are placed at the RG9 emission filter
    :param      RG665:          list of LEDs which are placed at the RG665 emission filter
    :return:
    """
    # Load emission factors from file
    em_path = 'supplementary/calibration/emission-site/' + '20170505_emission_device-' + str(device) + '.txt'
    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = led_order

    df_em = df.copy()
    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9). Dimension = 1
    for i in RG9:
        if i in df_em:
            df_em[i] = df[i].values / balance_factor.ix[int(device), i]
    for i in RG665:
        if i in df_em:
            df_em[i] = df[i].values / balance_factor.ix[int(device), i]

    return df_em


def correction_led(mean, kappa_spec, date, current, peakcolumns, full_calibration=True, print_info=True):
    """ Balance the LED-intensity based on the correction factors (kappa) calculated by the mean of the internal quantum
    counter. It returns an Data Frame containing the corrected mean values for each LED.
    :param mean:
    :param kappa:
    :param current:
    :param peakcolumns:
    :param full_calibration:
    :return: mean_corr
    """

    # Correction of the LED intensities for standardizing the measurement and inter-comparability.
    # Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum counter) and multiply the
    # factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
    if kappa_spec is None:
        # no specified correction factor. load the factor according to the date of the measurement file.
        if full_calibration is False:
            kappa_ = 'supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            if os.path.exists(kap) is True:
                kappa = pd.read_csv(kap, sep='\t', index_col=0)
            else:
                print("ERROR! No such file in directory!")
                return
        else:
            kappa_ = 'supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            kappa = pd.read_csv(kap, sep='\t', index_col=0)
    else:
        kappa = pd.read_csv(kappa_spec, sep='\t', index_col=0)

    corr_factor = kappa.ix[:-1, :].astype(float)
    corr_factor = corr_factor.set_index(corr_factor.index.astype(int))
    mean_corr = mean.copy()
    mean = pd.DataFrame(mean_corr)

    if not current:
        if full_calibration is True:
            current = [97]*8
        else:
            current = [50]*8

    if current[0] not in corr_factor.index:
        print("WARNING! Correction not processed! No correction factor for {}mA in calibrationfile!".format(current[0]))
        pass
    else:
        print('876')
        print(peakcolumns)
        print(current)
        if type(current) == float or type(current) == int:
            current = [int(current)] * len(peakcolumns)
            current = pd.DataFrame(current, index=peakcolumns).T
        elif type(current) == list:
            current = pd.DataFrame(current, index=peakcolumns).T
        print('881')
        for k in current.columns:                           # k: LED_wl
            if k not in corr_factor.columns:
                print('\n', 'Warning! No correction factor for LED {}'.format(k))
                for r in range(len(mean.columns)):                  # if there are more than one column in the matrix
                    mean_corr.ix[k, r] = mean.ix[k, r] * 1.0E-3
            else:
                for r in mean.columns:                              # if there are more than one column in the matrix
                    mean_corr.ix[k, r] = mean.ix[k, r] * corr_factor.ix[current.ix[0, k], k]

    return mean_corr


def correction_led_table(df, kappa_spec, date, current, peakcolumns, full_calibration=True):
    """ Balance the LED-intensity based on the correction factors (kappa) calculated by the mean of the internal quantum
    counter.
    :param df:
    :param kappa:
    :param current:
    :param peakcolumns:
    :param full_calibration:
    :return: mean_corr
    """
    if kappa_spec is None: # automatically chosen excitation-correction file
        # no specified correction factor. load the factor according to the date of the measurement file.
        if full_calibration is False: # linear fit between 30-50mA
            kappa_ = 'supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            if os.path.exists(kap) is True:
                kappa = pd.read_csv(kap, sep='\t', index_col=0)
            else:
                print("ERROR! No such file in directory!")
                return
        else:
            kappa_ = 'supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            kappa = pd.read_csv(kap, sep='\t', index_col=0)
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


# #####################################################################################################################
# # Linear discriminant analysis (LDA)
# #####################################################################################################################
def priority_lda(training_data_list, separation, training_corr):

    # trainingdata used
    tr = training_data_list.tolist()

    # principle possible algae samples analysed
    qqt = pd.read_csv('supplementary/phytoplankton/170427_algae.txt', sep='\t', header=0, encoding="latin-1")

    con = pd.DataFrame(qqt[separation])
    con.index = qqt['genus']
    # table of algae analysed and taxonomic level according to separation level
    con_ = con.ix[:(len(con) - 1)]

    # reduce principle possible groups to the amount of effectively used groups
    group = []

    for i in range(len(tr)):
        if tr[i] in con_.index:
            group.append(con_.ix[tr[i], separation])
        else:
            print('Warning! Sample {} not found in training matrix...'.format(tr[i]))
            training_corr = training_corr.drop(tr[i])

    groups = pd.DataFrame(group).drop_duplicates()
    groups.index = np.arange(len(groups))
    groups.columns = ['groups']
    groups['emphasis'] = np.zeros(shape=(len(groups), 1))

    # dinoflagellate potentially for analysis
    if separation == 'order' or separation == 'family':
        b = 'class'
        c = 'Dinophyceae'
    elif separation == 'class':
        b = 'phylum'
        c = 'Miozoa'
    elif separation == 'phylum':
        b = 'phylum'
        c = 'Miozoa'

    a = pd.DataFrame(qqt[b])
    a.index = qqt['genus']
    if separation == 'phylum':
        a_con = a
    else:
        a_con = pd.concat([con, a], axis=1).ix[:len(a) - 1]

    dino = a_con[a_con[b] == c].drop_duplicates()
    dinos_in_group = []
    for d in range(len(dino[separation])):
        if dino[separation][d] in groups['groups'].values:
            dinos_in_group.append(int(groups[groups['groups'] == dino[separation].values[d]]['emphasis'].index[0]))
        else:
            pass
    for t in range(len(dinos_in_group)):
        groups.ix[dinos_in_group[t], 'emphasis'] = len(groups) / len(dinos_in_group)
    priority = groups['emphasis'].tolist()

    return groups, priority, training_corr


def lda_sep(data, classes_dict, priors=None, number_components=3):
    """ running linear discriminant analysis for a given data set (mean values for different LEDs).
    The analysis bases on the Singular value decomposition (as default). It does not compute the
    covariance matrix, therefore this solver is recommended for data with a large number of features.
    Least square solution or eigenvalue decomposition are also possible.
    :param:     data:                       mean values of the sample at different LEDs
    :return:    LinearDiscriminantAnalysis: describe the analysis' quality
    """
    # data analysis
    classes = np.array([classes_dict[l] for l in data.index])

    lda = LinearDiscriminantAnalysis(n_components=number_components, store_covariance=True, priors=priors, solver='svd')
    # shrinkage doesn't work with singular value decomposition (svd), which might be interesting for classification and
    # tranfsormation

    # data set for training - fitting and transformation in one step
    lda.fit(data, classes)

    return lda


def lda_analysis(df, training, classes_dict, color_dict, priors=None, number_components=3, plot_score=False, type_=3):
    """Apply the linear discriminant analysis on an unknown sample and compare the scores with a training matrix.
    If desired, the results can be visualised in a 2D or 3D plot.
    :param: df:         pandas.DataFrame with pre-processed data for one unknown sample
            training:   pandas.DataFrame with pre-processed data for all algal samples from the data bank.
            plot_score: visualize the score values of each algal sample in a 2D or 3D plot. Default is True
            type:       which kind of plot is used for the visualisation: 2D (2) or 3D (3)? Default is 3.
    :return:lda = sklear.discriminant_analysis.LinearDiscriminantAnalysis
            training_score = pandas.DataFrame of the score values (returned from LDA) of the algal samples
            df_score = pandas.DataFrame of the calculated score values (from LDA) of the sample
    """
    # linear discriminant analysis with training data to calibrate the algorithm; saving scores
    lda = lda_sep(training, classes_dict, priors=priors, number_components=number_components)

    # (Coordinates) transformation in (sub)space for enhances class separation
    training_score = lda.transform(training)
    df_score = lda.transform(df)

    # linear discriminant analysis with sample data and plot training and sample data in one plot
    if plot_score is True:
        if number_components <= 2:
            type_ = 2
        ax = lda_plot(training, lda, classes_dict, color_dict, type_=type_)
        ax = lda_plot(df, lda, classes_dict, color_dict, type_=type_, ax=ax, marker='^')

    col_name = []
    for i in np.arange(df_score.size):
        col_name.append('LDA' + str(i + 1))
    df_score = pd.DataFrame(df_score, columns=[col_name], index=['sample'] * len(df_score))
    training_score = pd.DataFrame(training_score, columns=[col_name], index=training.index)

    return lda, training_score, df_score


# #####################################################################################################################
# # Converting Mahalanobis distance into probability of group membership and plotting
# #####################################################################################################################
def lda_plot(data, lda, classesdict, colordict, type_=3, ax=None, marker='H'):
    """ Calculates the scores of the sample and plots them together with the training samples.
    :param: data:   data matrix of the sample that has to be plotted
            lda:    sklear.discriminat_analysis.LineardiscriminantAnalysis
            type:   2dim or 3dim plot of the results
            ax:     standard process to add further data
            marker: sample data marked as hexagon2
    return: ax
    """

    scores_lda = lda.transform(data)
    ax = plot_scores(scores_lda, data.index, classesdict, colordict, type_=type_, figsize=(14, 8), marker=marker, ax=ax)

    return ax


def plot_scores(data, names, classes_dict, color_dict, type_=3, figsize=None, ax=None, marker="o"):
    """ Plotting at a 2 dimensional plane the score values of the linear discriminant analysis
     :param:    data:       data matrix that has to be plotted
                names:      labels or names of the samples
                type:       2dim or 3dim plot of the results
                figsize:    size of the plot
                ax:         standard process to add further data
                marker:     training data marked as points
     :return:   ax:         plotted axis
    """

    # plotting 2D scores
    if type_ == 2:
        if ax is None:
            f, ax = plt.subplots(figsize=figsize)
        plotted = set()

        for coords, name in zip(data, names):
            color = color_dict[name]
            group = classes_dict[name]
            if group in plotted:
                group = "_nolegend_"
            plotted.add(group)
            ax.plot(coords[0], coords[1], marker=marker, color=color, label=group, markersize=22)
        plt.tight_layout()
    elif type_ == 3:
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.set_aspect('normal')
        plotted = set()

        for coords, name in zip(data, names):
            color = color_dict[name]
            group = classes_dict[name]
            if group in plotted:
                group = "_nolegend_"
            plotted.add(group)
            ax.scatter(coords[0], coords[1], coords[2], marker=marker, color=color, label=group, s=180)

            plt.setp(ax.get_zticklabels(), fontsize=20)
            ax.set_zlabel('LDA3', fontsize=20)
        plt.tight_layout()
    else:
        raise ValueError("Choose plot dimension! (2D -> type=2 or 3D -> type=3)")

    ax.legend(loc=0, bbox_to_anchor=(0.5, 1.12), ncol=6, frameon=True, fancybox=True, shadow=True,
              fontsize=14)      # loc='upper center'
    plt.setp(ax.get_xticklabels(), fontsize=20)
    plt.setp(ax.get_yticklabels(), fontsize=20)

    ax.set_xlabel('LDA1', fontsize=20)
    ax.set_ylabel('LDA2', fontsize=20)

    return ax


#####################################################################################################################
# Construction of training database
#####################################################################################################################
def construction_training_database(data, trainingsdata, phytoplankton, xcoords, led_used_, device=1, device_training=0.,
                                   kappa_spec=None, separation='class', priority=False, pumprate=None, MAZeT=None,
                                   correction=True,  additional=False, peak_detection=True, current_training=None,
                                   blank_corr=True, blank_mean_ex=None, blank_std_ex=None, limit=None, plot_raw=False,
                                   plot_distance=True, type_=2, full_calibration=True, normalize=True,
                                   additional_training=False, standardize=True, save=False):
    """ Complete analysis by the mean of the linear discriminant analysis of a measured sample. The raw data are
    optionally blank corrected and peaks > LoD (3*std(blank)) are extracted. The signal intensity of the same
    biomass at different LEDs is clustered together.
    :param:     data:               path to the data file
                trainingsdata:      path to the trainings data for the LDA
                kappa_spec:          correction factors of the device for inter-comparability
                kappa_training:     correction factors of the device for inter-comparability. Just for trainings data
                seperation:         defines the taxonomic level at which the separation should take place
                priority:           If yes, the dinophyta is emphasised to be separated. Otherwise all groups have the
                                    same priority
                number_components:  define number of degrees of freedom for LDA separation
                pumprate:           definition of the pump speed [ml/min] to define the analysed sample volume
                correction:         correction of LED intensity for inter-comparability and correction of differences
                                    in emission filter properties
                blank_corr:         optionally correction of the raw data-file. The trainings data will be blank
                                    corrected anyway
                blank_std_ex:       give an external calculated deviation of the blank measurement
                blank_mean_ex:      give an external calculated mean value of the blank measurement
                plot_data:          time-drive plot of the sample. Default is False
                plot_score:         resulting score plot for trainings data and sample data. Default is True
                plot_distance:      plots the scores of the sample and the spheres of the algae classes to visualize
                                    the sample affiliations
                type_:              2dim or 3dim plot of the results
                normalize:          normalisation of the trainings and sample data. Same option for both data to
                                    ensure an equivalent analysis. Default = True
                standardize:        standardisation, i.e. centering and auto-scaling of trainings and sample data
                                    for the algorithm. Default = True
                save:               store the results of the analysis. When individual peaks are analysed only a
                                    summary (which algal classes could be found + their probability) is exported.
                                    Standard txt file for english application (sep = '\t', decimal = '.')
    :return:    lda = sklearn.discriminant_analysis.LinearDiscriminantAnalysis
                df_score = pd.DataFrame:        resulting score values (from LDA) for the analyzed sample
                training_score = pd.DataFrame:  resulting score values (from LDA) for each algal sample in the
                                                training matrix
                d_ = list/pd.DataFrame:         mean values for each algal class, their spatial distribution and the
                                                distance between the sample and each class center
                prob = list/pd.DataFrame:       probability of belonging to a certain algal class
    """

# ------------------------------------------------------------------------------------
    # Load data and prepare analysis
    t0 = time()
    led_used = []
    for i in led_used_.columns:
        if led_used_.ix[0, i] == True:
            led_used.append(i)

    # load the raw data of one! measurement file for the LDA
    [l_, header, unit] = read_rawdata(filename=data, led_used=led_used, additional=additional, co=None,
                                      blank_corr=blank_corr, blank_mean_ex=blank_mean_ex, blank_std_ex=blank_std_ex,
                                      plot_raw=plot_raw)

    # reduce sample to the number of LEDs used
    l = pd.DataFrame(np.zeros(shape=(len(l_.index), 0)), index=l_.index)
    for i in l_.columns:
        if led_used_.ix[0, i] == True:
            l.ix[:, i] = l_.ix[:, i]

    print('separation level: ', 'algal', separation)

    # general information about file. If one use an externally calculated blank, the values are transferred here!
    path = os.path.dirname(data)
    [dd, name, date, current, blank_mean, blank_std, unit_blank, LED_wl, LEDs, MAZeT,
     pumprate] = info_about_file_extend(data, header, led_used=led_used, blank_mean_ex=blank_mean_ex,
                                        blank_std_ex=blank_std_ex, pumprate=pumprate, MAZeT=MAZeT)

    # return the pump rate in mL/min
    print('Pump rate for this measurement: {:.2f} mL/min'.format(pumprate), '\n')

    # defining measurement time and volume based on pump speed
    t = l_.index[-1] / 60  # time in minutes
    volume = round(pumprate * t, 2)  # volume in mL

    # information for trainings data. Which separation level is chosen?
    [classes_dict, color_dict, colorclass_dict, genus_names] = separation_level(separation, path=phytoplankton)
# ----------------------------------------------------------------------------------------------------

    # Balance device and correct measurement data
    # sort LEDs by emission filter RG665 or RG9 for the sample as well as for the trainings data
    [RG9_sample, RG665_sample] = LED_Filter(l_.columns)
    print('1256')

    # load trainings data from a folder
    [training, training_current, RG9_training, RG665_training,
     training_date] = read_directory(trainingsdata, volume, led_used=led_used, kappa_spec=None, device=device_training,
                                     additional=additional_training, blank_corr=blank_corr, blank_mean_ex=None,
                                     blank_std_ex=None, normalize=False, standardize=False,
                                     full_calibration=full_calibration)
    print('1263')
    # reduce training matrix to the number of LEDs used
    training_red = pd.DataFrame(np.zeros(shape=(len(training.index), 0)), index=training.index)
    for i in training.columns:
        if led_used.ix[0, i] == True:
            training_red.ix[:, i] = training.ix[:, i]
    print('1269')
    # define LoD (depending whether the data are blank corrected or not) and sample peaks (= data > LoD)
    # count the number of detected peaks(c), extract the peak values(peak), calculate mean values for the LEDs(mean)
    LoD = detection(header=header, rg665=RG665_sample, rg9=RG9_sample, kappa_spec=kappa_spec, led_used=led_used,
                    date=date, current=current, unit_blank=unit_blank, full_calibration=full_calibration,
                    blank_corr=blank_corr, blank_mean=blank_mean, blank_std=blank_std, correction=correction,
                    device=int(device))
    print('1276')
    if peak_detection is True:
        # peak detection (Int. > LoD (peak)) and count number of peaks (c) as well as the mean value of the peaks (mean)
        [c, peak, mean_raw] = counter(l, volume=volume, LoD=LoD.values[0], xcoords=xcoords, division=None,
                                            warn=False)
    else:
        mean_raw = l.copy()
        mean_raw = mean_raw.mean()
        c = mean_raw.copy()
        for r in c.index:
            c[r] = '--'
        peak = l.copy()
    print('1288')
    mean = pd.DataFrame(mean_raw, columns=['sample'])

    if correction is True:
        # Balance different transmission properties of the emission filters
        mean_balanced = emission_correction(mean, device, RG9_sample, RG665_sample, led_order=LEDs)
        training_balanced = emission_correction_table(training_red, device, RG9_training, RG665_training,
                                                      led_order=LEDs)

        # Correction of the LED intensities for standardizing the measurement and inter-comparability. Load correction
        # factors for rhodamine 101 12mM in ethylene glycol(internal quantum counter) and multiply the factors with the
        # LED intensity to get the inter-comparability / ist-LED-intensity. LED correction for the sample
        mean_corr = correction_led(mean_balanced, kappa_spec, date, current, peak.columns,
                                   full_calibration=full_calibration, print_info=True)
        mean_corr = mean_corr.sort_index(axis=0)

        # LED correction for trainings matrix individually in order to get rid of sample-names as index in order to
        # deal with multiple sample measurements
        training_trans = training_balanced.set_index(np.arange(len(training_balanced.index)))
        trans_current = training_current.set_index(np.arange(len(training_current.index)))

        # correct each trainings sample individually and append corrected sample to the trainings matrix
        [a, b] = training_balanced.shape
        training_corr1 = pd.DataFrame(zeros((a, b)), columns=training_balanced.columns)

        for s in range(len(training_balanced.index)):
            cur_training = trans_current.ix[s, :].values.tolist()
            mean_tra = pd.DataFrame(training_trans.T[s])
            training_corr_trans = correction_led(mean_tra, kappa_spec, training_date.ix[s, :].values[0],
                                                       cur_training, training_current.columns,
                                                       full_calibration=full_calibration, print_info=False).T
            training_corr1.T[s] = training_corr_trans.T
        training_corr_sort = training_corr1.sort_index(axis=1)
        training_corr_sort.index = training_balanced.index
    else:
        mean_corr = mean.sort_index(axis=0)
        training_corr_sort = training_red.sort_index(axis=1)

# ------------------------------------------------------------------------------------

    # calculate average fluorescence intensity at different excitation wavelengths
    # pigment pattern just with normalised, but not with standardised sample data
    pigment_pattern = mean_corr.copy()
    pigment_pattern = pre_process(pigment_pattern, normalize=True, standardize=False)
    pigment_pattern.columns = ['mean value [pW]']

    # pre-processing of the sample data at the same level as for the trainings matrix
    mean_corr = pre_process(mean_corr, normalize=normalize, standardize=standardize)
    mean_corr = pd.DataFrame(mean_corr, columns=['sample'])
    training_corr_ = pre_process(training_corr_sort.T, normalize=normalize, standardize=standardize).T
    training_corr = pd.DataFrame(training_corr_)

# ------------------------------------------------------------------------------------

    # LDA with all data-points
    # If there's one LED where the cell density is too high -> LDA with mean values
    if ['--'] in c.unique():
        # sort LEDs by wavelength
        df = mean_corr.sort_index().T

        # adaption for the output
        mean_corr.columns = [unit]

        if separation == 'phylum' or separation == 'class':
            priority = False

        if priority is True:
            [groups, priors, training_corr] = priority_lda(training_corr.index, separation, training_corr)
            number_components = len(groups)
        else:
            priors = None
            number_components = 8

        # linear discriminant analysis
        [lda, training_score,
         df_score] = lda_analysis(df, training_corr, classes_dict, colorclass_dict, priors=priors,
                                  number_components=number_components, plot_score=False, type_=type_)

        if number_components <= 2:
            type_ = 2

    # ------------------------------------------------------------------------------------
    # LDA with detected peaks
    else:
        # calculate time delay to shift the channels. The volume is the sum of the measurement volume and the death
        # volume between two emission channels [m^3]. The shift is the calculated time difference to shift the columns
        # from one device-side: volume[L] / pumprate [L/s] = [s]
        volume_ = (0.5 * 1.94/1000)**2 * np.pi * 6.9 / 1000
        shift = volume_ * 1000 / (pumprate / 1000 / 60)

        # concatenate the blank-corrected data to a new DataFrame with the same time line.
        data0 = l.ix[:, 0:1].dropna()
        data7 = l.ix[:, 1:2].dropna()
        data7.index = data0.index
        data1 = l.ix[:, 2:3].dropna()
        data1.index = data0.index - 1 * shift
        data6 = l.ix[:, 3:4].dropna()
        data6.index = data1.index
        data2 = l.ix[:, 4:5].dropna()
        data2.index = data0.index - 2 * shift
        data5 = l.ix[:, 5:6].dropna()
        data5.index = data2.index
        data3 = l.ix[:, 6:7].dropna()
        data3.index = data0.index - 3 * shift
        data4 = l.ix[:, 7:8].dropna()
        data4.index = data3.index
        ld = [data0, data7, data1, data6, data2, data5, data3, data4]
        data = pd.concat(ld, axis=1)
        df_ = pd.DataFrame(data, index=data.index, columns=data.columns)

        # peak detection
        [c, peak, mean] = counter(df_, LoD=LoD, volume=volume, warn=False)

        # control if there are no peaks detected -> exit. Otherwise go on!
        if [0] in c.unique():
            sys.exit('No peak detected!')

        # delete rows where all entries are NaN and replace NaN, occurring only on few columns for one row, with LoD for
        # each columns
        peak = peak[~np.isnan(peak).all(axis=1)]
        peak.ix[:, 0:1] = peak.ix[:, 0:1].replace(to_replace=NaN, value=LoD[0])
        peak.ix[:, 1:2] = peak.ix[:, 1:2].replace(to_replace=NaN, value=LoD[1])
        peak.ix[:, 2:3] = peak.ix[:, 2:3].replace(to_replace=NaN, value=LoD[2])
        peak.ix[:, 3:4] = peak.ix[:, 3:4].replace(to_replace=NaN, value=LoD[3])
        peak.ix[:, 4:5] = peak.ix[:, 4:5].replace(to_replace=NaN, value=LoD[4])
        peak.ix[:, 5:6] = peak.ix[:, 5:6].replace(to_replace=NaN, value=LoD[5])
        peak.ix[:, 6:7] = peak.ix[:, 6:7].replace(to_replace=NaN, value=LoD[6])
        peak.ix[:, 7:8] = peak.ix[:, 7:8].replace(to_replace=NaN, value=LoD[7])

        # preparation of the detected peaks to analyse them individually
        index = ['sample'] * len(peak)
        peak.index = index

        # sort wavelength according to their size
        df = peak.reindex_axis(sorted(peak.columns), axis=1)

        # pre-processing of the data
        df = pre_process(df, normalize=normalize, standardize=standardize)

        if priority is True:
            [groups, priors, training_corr] = priority_lda(training_corr.index, separation)
        else:
            priors = None

        # linear discriminant analysis
        number_components = len(groups)

        # linear discriminant analysis
        [lda, training_score,
         df_score] = lda_analysis(df, training_corr, classes_dict, colorclass_dict, priors=priors,
                                  number_components=number_components, plot_score=False, type_=type_)

    print('Training database successfully constructed')
    if save is True:
        if priority is True:
            path_training = 'supplementary/trainingdatabase/' + date[:7] + '_trainignsmatrix_corrected_priority.txt'
        else:
            path_training = 'supplementary/trainingdatabase/' + date[:7] + '_trainignsmatrix_corrected.txt'

        training_score.to_csv(path_training, sep='\t')
        print('Training database '+ date[:7] + '_trainignsmatrix_corrected.txt is saved')

    return lda, df_score, training, training_score, peak, mean_corr, c, l, pigment_pattern


#####################################################################################################################
#
#####################################################################################################################
def gen_train_data():
    # raw data
    df_ = 'measurement/201611081019_skeletonemacostatum_50mA_20MOhm.txt'
    training_db ='supplementary/trainingdatabase/Bilbao_processed/all_50mA_100mikroE_01i_family/'
    kappa_spec = 'supplementary/calibration/excitation-site/linear_amplification/correctionfactor/' \
    '20180116_LED_correction_rhodamine101_spectrum.txt'
    phytoplankton = 'supplementary/phytoplankton/'

    # Parameter of choice for evaluation
    device = 1
    separation_ = 'order'
    priority = False
    pumprate = 1.5
    correction = True
    full_calibration = False
    blank_correction = False
    normalization = True
    standardization = True
    save = True
    xcoords_sample = [50, 100, 0, 5]

    #!!!TODO:
    # LED selection for analysis
    LED380_checkbox = False
    LED403_checkbox = True
    LED438_checkbox = True
    LED453_checkbox = True
    LED472_checkbox = True
    LED526_checkbox = True
    LED593_checkbox = True
    LED640_checkbox = True
    # which LEDs are used
    led_used_ = led_reduction(LED380_checkbox, LED403_checkbox, LED438_checkbox, LED453_checkbox, LED472_checkbox,
                             LED526_checkbox, LED593_checkbox, LED640_checkbox)

    # construction of traning database
    [lda, df_score, training, training_score, peak, mean_corr, c, l,
    pigment_pattern] = construction_training_database(df_, training_db, phytoplankton=phytoplankton, led_used_=led_used_,
                                                      xcoords=xcoords_sample, device=1, device_training=device,
                                                      kappa_spec=kappa_spec, separation=separation_, priority=priority,
                                                      pumprate=pumprate, correction=correction,
                                                      blank_corr=blank_correction, full_calibration=full_calibration,
                                                      normalize=normalization, standardize=standardization, save=save)

if __name__ == "__main__":
    gen_train_data()

