__author__ = 'szieger'
__project__ = 'SCHeMA_algorithm_LDA'

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os.path
from pylab import *
from scipy.stats import *
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import math

sns.set_context("paper", font_scale=2.5, rc={"lines.linewidth": 2})
sns.set_palette("colorblind", 10)
sns.set_style("ticks", {"xtick.direction": "in", "ytick.direction": "in"})

# global parameters and variables
loc_path = os.getcwd()
file_group = loc_path + '/supplementary/phytoplankton/170427_algae.txt'
file_phylum = loc_path + '/supplementary/phytoplankton/170427_algalphylum.txt'

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


# ---------------------------------------------------------------------------------------------------------------------
def prescan_load_file(filename, file_em, device=1, kappa_spec=None, pumprate=None, correction=True, blank_corr=True,
                      full_calibration=True, blank_mean_ex=None, blank_std_ex=None, factor=1, unit_blank=None):
    # ---------------------------------------------------------------------------------------------------------
    # Load data file, which is optionally blank corrected.
    # signal (optionally blank corrected), header and unit of measurement signal (nW or pW)
    [l, header, unit] = read_rawdata(filename=filename, factor=factor, plot_raw=False, blank_corr=blank_corr,
                                     blank_mean_ex=blank_mean_ex)

    # ensure that everything is calculated in nW
    if unit == 'pW':
        l_ = l.copy()
        for i in l.columns:
            for k in l.index:
                l_.loc[k, i] = l.loc[k, i] / 1000
        unit = 'nW'
    elif unit == 'µW':
        l_ = l.copy()
        for i in l.columns:
            for k in l.index:
                l_.loc[k, i] = l.loc[k, i] * 1000
        unit = 'nW'
    else:
        # unit should then be nW
        l_ = l

    # general information about the file. The blank value is a combination of header and external file or just extracted
    # from file, respectively
    path = os.path.dirname(filename)
    [name, date, current, blank_mean, blank_std, unit_blank, LEDs,
     pumprate] = file_info_extend(filename, header, blank_mean_ex=blank_mean_ex, blank_std_ex=blank_std_ex,
                                  pumprate=pumprate, unit_blank=unit_blank)
    firstline = pd.read_csv(filename, sep='\t', header=None, nrows=1, converters={0: lambda x: x[2:]})

    # defining measurement time and volume based on pump speed
    t = l_.index[-1] / 60  # time in minutes
    volume = round(pumprate * t, 2)  # volume in mL

    # ------------------------------------------------------------------------------------------------------------
    # Correct all measured data along the time-drive, i.e. emission-site with defined values and on the excitation-site
    # with correction factors from rhodamine101 12mM.
    [rg9_sample, rg665_sample] = LED_Filter(l_.columns)

    if correction is True:
        # Emission-site correction: Balance different transmission properties of the emission filters if correction is
        # True. Dimension of correction factor is [1] or [%]
        l_em_balanced = em_corr_table(file_em=file_em, df=l_, device=device, led_order=LEDs, RG9=rg9_sample,
                                      RG665=rg665_sample)
        blank_mean_ = pd.DataFrame(blank_mean, index=LEDs)
        blank_em_bal = em_corr_table(file_em=file_em, df=blank_mean_.T, device=device, led_order=LEDs, RG9=rg9_sample,
                                     RG665=rg665_sample)

        # Excitation-site correction: Correction of the LED intensities for standardizing the measurement and
        # inter-comparability. Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum
        # counter) and multiply the factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
        # Dimension of correction factor is []
        l_corr = correction_led_table(l_em_balanced, kappa_spec, date, current, peakcolumns=l_.columns,
                                      full_calibration=full_calibration)
        blank_corrected = correction_led_table(blank_em_bal, kappa_spec, date, current, peakcolumns=l_.columns,
                                               full_calibration=full_calibration).values[0]
        unit_corr = 'rfu'
    else:
        l_corr, unit_corr = l_, unit
        blank_corrected = blank_mean if isinstance(blank_mean, list) else blank_mean.tolist()
    return l_, l_corr, header, firstline, current, date, name, blank_mean, blank_std, blank_corrected, rg9_sample, \
           rg665_sample, volume, pumprate, unit, unit_corr, unit_blank, path


def read_rawdata(filename, factor=1., blank_corr=True, blank_mean_ex=None, plot_raw=False):
    """ Reads one data file and loads data within this file. Optionally the data could be corrected by the mean value
    of the blank.
    :param filename:        path to the file and name of file
    :param factor:          float; can be used to amplify the light-measurement, when the offset_compensation is not
                            working properly
    :param blank_corr:      optional blank correction of data
    :param blank_mean_ex:
    :param plot_raw:        time drive plot of this file
    :return: pandas.DataFrame:  containing the processed data for one algal sample at each LED
    """
    # load name of the file and slide it into subsections to extract the file information.
    algae = os.path.basename(filename).split('.')[0]

    # current version of the data file
    # read file with the light-data and the dark-data and the header as well in a separate file.
    # for the signal processing, subtract the dark-offset from the light value
    data_light = pd.read_csv(filename, sep='\t', skiprows=6, encoding="latin-1",
                             usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]) * factor
    data_dark = pd.read_csv(filename, sep='\t', skiprows=6, usecols=[0, 16, 17, 18, 19, 20, 21, 22, 23],
                            encoding="latin-1") * factor
    header = pd.read_csv(filename, sep='\t', header=None, skiprows=1, nrows=5, converters={0: lambda x: x[2:]},
                         encoding="latin-1")[:7]

    # extracting LED information and signal unit from header
    unit = data_light.columns[1].split(' ')[1][1:3]
    [date, blank_mean, LEDs] = file_info_sort(filename=filename, header=header, blank_mean_ex=blank_mean_ex)

    data = data_light.copy()
    i = 0
    for li, j in enumerate(data_light.columns):
        if li % 2 != 0:
            data.loc[:, li] = pd.DataFrame(data_light[j] - data_dark[data_dark.columns[i+1]])
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


def file_info_sort(filename, header, blank_mean_ex):
    """
    :param filename:
    :param header:
    :param blank_mean_ex:
    :return:
    """
    date = os.path.basename(filename).split('.')[0].split('_')[0]

    # Extract the blank calculated and stored in the header
    blank_mean_header, unit_blank_header = [], []
    for k in header.loc[4, :]:
        if isinstance(k, np.float) is False:
            blank_mean_header.append(float(k.split('=')[1].split('+/-')[0]))
            unit_blank_header.append(k.split('=')[1][-2:])

    if unit_blank_header[0] == 'pA' or unit_blank_header[0] == 'pW':
        for p, q in enumerate(blank_mean_header):
            blank_mean_header[p] = (q / 1000)

    # combine blank from external file and from header if both are necessary
    blank_mean = [sum(x) for x in zip(blank_mean_header, blank_mean_ex)] if blank_mean_ex else blank_mean_header
    LEDs = [e.split(' ')[-2] + ' nm' for e in header.loc[1, :] if isinstance(e, np.float) is False]

    return date, blank_mean, LEDs


def file_info_extend(filename, header, blank_mean_ex, blank_std_ex, pumprate=None, unit_blank=None):
    """
    :param filename:
    :param header:
    :param blank_mean_ex:
    :param blank_std_ex:
    :param pumprate:
    :param unit_blank:
    :return:
    """
    name = os.path.basename(filename).split('.')[0].split('_')[1]
    gen_info = pd.read_csv(filename, sep='\t', header=None, nrows=1, converters={0: lambda x: x[2:]})
    [date, blank_mean, LEDs] = file_info_sort(filename=filename, header=header, blank_mean_ex=blank_mean_ex)

    if not pumprate:
        pumprate = float(gen_info.loc[0, 2].split('=')[1])  # mL/min

    current = []  # mA
    for i in header.loc[2, :]:
        if isinstance(i, np.float) is False:
            current.append(int(float(i.split('=')[1].split('mA')[0].strip())))

    blank_std_header, unit_blank_header = [], []
    # Extract the blank calculated and stored in the header
    for k in header.loc[4, :]:
        if isinstance(k, np.float) is False:
            blank_std_header.append(float(k.split('=')[1].split('+/-')[1][:-2]))
            unit_blank_header.append(k.split('=')[1][-2:])

    if unit_blank_header[0] == 'pA' or unit_blank_header[0] == 'pW':
        for p, q in enumerate(blank_std_header):
            blank_std_header[p] = (q / 1000)
            unit_blank_header = 'nW'

    # combine blank from external file and from header if both are necessary
    blank_std = [sum(x) for x in zip(blank_std_header, blank_std_ex)] if blank_mean_ex else blank_std_header
    if unit_blank is None:
        unit_blank = unit_blank_header

    return name, date, current, blank_mean, blank_std, unit_blank, LEDs, pumprate


def find_label(label, ls):
    if isinstance(label, str):
        if type(label) == type(ls[0]):
            return label
        else:
            return int(label.split(' ')[0])
    else:
        if type(label) == type(ls[0]):
            return label
        else:
            return str(label) + ' nm'


def LED_Filter(name):
    """
    :param name:
    :return:
    """
    # original order: '526 nm', '438 nm', '593 nm', '453 nm', '380 nm', '472 nm', '403 nm', '640 nm'
    diodeI = pd.DataFrame(name[0:2], index=['PD1', 'PD1'])
    diodeII = pd.DataFrame(name[2:4], index=['PD2', 'PD2'])
    diodeIII = pd.DataFrame(name[4:6], index=['PD3', 'PD3'])
    diodeIV = pd.DataFrame(name[6:], index=['PD4', 'PD4'])
    photodiode = pd.concat([diodeI, diodeII, diodeIII, diodeIV])

    # Search for 640nm-LED (only one that has to be with filter RG665). This photodiode shall be collected in RG665.
    rg9 = None
    for el, i in enumerate(photodiode[0]):
        if i == 640.0 or i == '640 nm':
            rg9 = photodiode.index[el]
    if rg9:
        RG9 = photodiode.loc[rg9, 0].tolist()
        RG665 = photodiode[0].tolist()
        RG665.remove(RG9[0])
        RG665.remove(RG9[1])
    else:
        RG9, RG665 = photodiode[0].tolist(), None

    # convert to expected format of 'XY nm' for each LED
    if isinstance(RG9[0], float):
        RG9 = [str(int(i)) + ' nm' for i in RG9]
        if RG665:
            RG665 = [str(int(i)) + ' nm' if i != 0. else i for i in RG665]
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

    key_list = qqt[0].values.tolist()
    values_list = qqt[1].values.tolist()
    color_list = qqt[2].values.tolist()
    genus_names = key_list

    # creating dictionary
    for key, value in zip(key_list, values_list):
        classes_dict[key] = value

    for key, value in zip(genus_names, color_list):
        color_dict[key] = value

    for key, value in zip(values_list, color_list):
        colorclass_dict[key] = value

    return classes_dict, color_dict, colorclass_dict, genus_names


def training_database(trainings_path, led_used):
    # load trainings data from a txt-file
    training = pd.read_csv(trainings_path, sep='\t', index_col=0)
    ynew = [int(c.split(' ')[0]) for c in training.columns]
    training.columns = ynew

    # trainings data bank reduction according to selected LEDs
    training_red = pd.DataFrame(np.zeros(shape=(len(training.index), 0)), index=training.index)
    for i in led_used:
        if i in training.columns:
            training_red.loc[:, i] = training.loc[:, i]
    training_red_sort = training_red.sort_index(axis=1)

    return training_red_sort, training, training_red


def separation_level(separation):
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
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(loc_path + '/supplementary/phytoplankton/170427_algalphylum.txt')
    elif separation == 'class':
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(loc_path + '/supplementary/phytoplankton/170427_algalclass.txt')
    elif separation == 'order':
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(loc_path + '/supplementary/phytoplankton/170427_algalorder.txt')
    else:
        # separation is family
        [classes_dict, color_dict, colorclass_dict,
         genus_names] = algae_dictionary(loc_path + '/supplementary/phytoplankton/170427_algalfamily.txt')

    return classes_dict, color_dict, colorclass_dict, genus_names


def taxonomic_level_reduction(prob, separation='phylum', likelyhood=False):
    # load general taxonomic information about algae
    alg_group = pd.read_csv(file_group, sep='\t', encoding="latin-1")

    # prepare data matrices for data reduction
    probability = pd.DataFrame(prob[0])  # for all identified groups

    # last point is "sample" not needed in this DF
    alg_phylum = alg_group['phylum'].drop_duplicates().tolist()[:-1]
    prob_group_all = pd.DataFrame(np.zeros(shape=(1, len(alg_phylum))), columns=alg_phylum)

    # classify the identified algal group in the DataFrame according to their phylum
    for i in range(len(probability.index)):
        phylum = alg_group[alg_group[separation] == probability.index[i]]['phylum'].values[0]
        prob_group_all.loc[i, phylum] = probability.loc[probability.index[i], 'gaussian prob.']

    # reduce too detailed information of algal separation level to the higher - more general / more secure level phylum
    prob_red, prob_red_gauss_ = [], []
    for i in range(len(probability.index)):
        phyl = alg_group[alg_group[separation] == probability.index[i]]['phylum'].values[0]
        if likelyhood is True:
            phyl_prob = probability['gaussian prob.'][i]
        else:
            phyl_prob = 0

        if phyl not in prob_red:
            prob_red.append(phyl)
            if likelyhood is True:
                prob_red_gauss_.append(phyl_prob.round(2))

    prob_red_gauss = []
    for t in prob_red_gauss_:
        a = t / sum(prob_red_gauss_) * 100
        prob_red_gauss.append(a.round(2))

    return prob_red, prob_red_gauss


# ---------------------------------------------------------------------------------------------------------------------
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


def detection(header, rg665, rg9, kappa_spec, date, current, unit_blank, device=1, file_em=None, full_calibration=False,
              blank_corr=True, blank_mean=None, blank_std=None, correction=True):
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
    # get the specific order of the LEDs in the device
    led_order = [led.split(' ')[2] + ' nm' for led in header.loc[1, :] if isinstance(led, str)]
    [mean_ex_corr, std_ex_corr] = mean_conversion(led_order=led_order, rg665=rg665, rg9=rg9, date=date, file_em=file_em,
                                                  kappa_spec=kappa_spec, current=current, unit_blank=unit_blank,
                                                  full_calibration=full_calibration, blank_mean=blank_mean,
                                                  blank_std=blank_std, device=device, correction=correction)

    # calculation of LoD depending whether the data are raw or blank corrected data
    ls_mean = mean_ex_corr.loc[mean_ex_corr.index[0], :].tolist()
    ls_std = std_ex_corr.loc[std_ex_corr.index[0], :].tolist()
    if blank_corr:
        # the mean value of the blank was subtracted before
        LoD = [3*ls_std[i] for i in range(len(ls_mean))]
    else:
        # the mean value of the blank has to be taken into account
        LoD = [ls_mean[i] + 3*ls_std[i] for i in range(len(ls_mean))]
    LoD = pd.DataFrame(LoD, index=mean_ex_corr.columns, columns=[int(device)]).T
    return LoD


def counter(df, LoD, volume, xcoords=None, division=None, warn=True):
    """ Counting measurement data which are higher than the LoD for each LED. The number of detected peaks will be
    stored as well as the intensities of the peaks. Finally the mean values for all LEDs will be calculated after
    the peak detection.
    :param:     df:         peak extracted data that should be counted
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
        xcoords = [df.index[0], df.index[-1], 0, 0]

    # extracting the peaks
    peak = df.copy()
    for i, k in enumerate(peak.columns):    # i = numbers, k = wavelengths
        peak[k][peak[k] < LoD[i]] = np.nan

    # counting peaks - when the pump rate is too slow, there are more measurement points for the same biomass
    # which has to be taken into account
    c = pd.Series([0]*len(peak.columns), index=peak.columns)
    for i in range(len(c)):                                         # number of rows in c (= number of LEDs, i = 0-7)
        cnm = df[c.index[i]].dropna()                               # copy of l but without NaN-entries
        for k in range(len(cnm) - 1):
            if cnm.iloc[k] < LoD[i] and cnm.iloc[k + 1] >= LoD[i]:  # single peaks found in the file
                c[c.index[i]] += 1
        if len(peak[c.index[i]].dropna()) >= len(cnm)/2:    # only signals > LOD found in the file -> high cell density
            c[c.index[i]] = '--'
            if warn is True:
                if c.index[i].split(' ')[0] == str(division[0]) or c.index[i].split(' ')[0] == str(division[1]):
                    print('Cell density at LED {} ≥ {} cells/{}mL!'.format(c.index[i], len(cnm)/2, volume))

    # calculate the mean value for each LED from the detected peaks and set negative values to zero
    # sample
    if xcoords[0] >= xcoords[1]:
        mean_sample = pd.Series([np.nanmean(peak.loc[xcoords[1]:xcoords[0], col]) for col in peak.columns],
                                index=peak.columns)
    elif xcoords[1] > xcoords[0]:
        mean_sample = pd.Series([np.nanmean(peak.loc[xcoords[0]:xcoords[1], col]) for col in peak.columns],
                                index=peak.columns)
    else:
        mean_sample = pd.Series([0, 0, 0, 0, 0, 0, 0, 0], index=peak.columns)

    # blank
    if len(xcoords) > 2:
        if xcoords[2] > xcoords[3]:
            mean_blank = pd.Series([np.nanmean(peak.loc[xcoords[3]:xcoords[2], col]) for col in peak.columns],
                                   index=peak.columns)
        elif xcoords[3] > xcoords[2]:
            mean_blank = pd.Series([np.nanmean(peak.loc[xcoords[2]:xcoords[3], col]) for col in peak.columns],
                                   index=peak.columns)
        else:
            mean_blank = pd.Series([0, 0, 0, 0, 0, 0, 0, 0], index=peak.columns)
    else:
        mean_blank = pd.Series([0, 0, 0, 0, 0, 0, 0, 0], index=peak.columns)

    for val in mean_blank.index:
        if math.isnan(mean_blank[val]) is True:
            mean_blank[val] = 0.
    mean = pd.DataFrame(mean_sample - mean_blank.fillna(0))

    mean[mean < 0] = 0
    for el in peak.columns:
        if mean.loc[el, :].values <= 0:
            if warn is True:
                print('No peaks found for LED {}'.format(mean.index[el]))
            mean.loc[el] = 0

    return c, peak, mean


def mean_conversion(led_order, rg665, rg9, kappa_spec, date, current, unit_blank, file_em, full_calibration=False,
                    blank_mean=None, blank_std=None, correction=True, device=1):
    # convert depending  on unit into nW:
    if unit_blank == 'nW':
        pass
    elif unit_blank == 'pW':
        # from 1pW into 1nW
        blank_mean = [i / 1000 for i in blank_mean]
        blank_std = [i / 1000 for i in blank_std]
    elif unit_blank == 'µW':
        # from 1µW into 1nW
        blank_mean = [i * 1000 for i in blank_mean]
        blank_std = [i * 1000 for i in blank_std]

    # first correction then addition ("punkt vor strich"). Blank mean was (in case) corrected previously
    blank_mean = pd.DataFrame(blank_mean, index=led_order, columns=[int(device)]).T
    blank_std = pd.DataFrame(blank_std, index=led_order, columns=[int(device)]).T

    # correction of blank_std
    if correction is True:
        # Emission-site correction: Balance different transmission properties of the emission filters if correction is
        # True. Dimension of correction factor is [1] or [%]
        blank_mean = em_corr_table(file_em=file_em, df=blank_std, device=device, RG9=rg9, RG665=rg665,
                                   led_order=led_order)

        # Excitation-site correction: Correction of the LED intensities for standardizing the measurement and
        # inter-comparability. Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum
        # counter) and multiply the factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
        # Dimension of correction factor is []
        blank_std = correction_led_table(blank_mean, kappa_spec, date, current, peakcolumns=led_order,
                                         full_calibration=full_calibration)
    return blank_mean, blank_std


def correction_sample(df, header, date, current, volume, device, unit_blank, led_total, kappa_spec=None, file_em=None,
                      correction=True, peak_detection=True, xcoords=None, full_calibration=True, blank_corr=True,
                      blank_mean=None, blank_std=None,):
    # Balance device and correct measurement data
    # sort (!all not reduced!) LEDs by emission filter RG665 or RG9 for the sample as well as for the trainings data
    [RG9_sample, RG665_sample] = LED_Filter(led_total)

    # define LoD (depending whether the data are blank corrected or not) and sample peaks (= data > LoD)
    # count the number of detected peaks(c), extract the peak values(peak), calculate mean values for the LEDs(mean)
    LoD = detection(date=date, header=header, file_em=file_em, kappa_spec=kappa_spec, correction=correction,
                    rg665=RG665_sample, rg9=RG9_sample, unit_blank=unit_blank, blank_mean=blank_mean, current=current,
                    full_calibration=full_calibration, blank_corr=blank_corr, blank_std=blank_std, device=int(device))

    if peak_detection is True:
        # peak detection (Int. > LoD (peak)) and count number of peaks (c) as well as the mean value of the peaks (mean)
        [c, peak, mean_raw] = counter(df, volume=volume, LoD=LoD.values[0], xcoords=xcoords, division=None, warn=False)
    else:
        mean_raw = df.copy()
        mean_raw = mean_raw.mean()
        c = mean_raw.copy()
        for r in c.index:
            c[r] = '--'
        peak = df.copy()

    mean = pd.DataFrame(mean_raw)
    mean.columns = ['sample']

    if correction is True:
        # Balance different transmission properties of the emission filters
        mean_balanced = emission_correction(mean=mean, file_em=file_em, device=device, RG9_sample=RG9_sample,
                                            RG665_sample=RG665_sample, led_order=led_total)

        # Correction of the LED intensities for standardizing the measurement and inter-comparability. Load correction
        # factors for rhodamine 101 12mM in ethylene glycol(internal quantum counter) and multiply the factors with the
        # LED intensity to get the inter-comparability / ist-LED-intensity. LED correction for the sample
        mean_corr = correction_led(mean=mean_balanced, kappa_spec=kappa_spec, date=date, current=current,
                                   peakcolumns=peak.columns, led_total=led_total, full_calibration=full_calibration)
    else:
        mean_corr = mean
    mean_corr = mean_corr.sort_index(axis=0)

    return c, peak, mean_corr, LoD


def emission_correction(mean, file_em, device, RG9_sample, RG665_sample, led_order):
    """
    :param      mean:           mean values of the LEDs in the right order (not sorted by wavelengths) as it was
                                measured
    :param      file_em:
    :param      device:
    :param      RG9_sample:     list of LEDs which are placed at the RG9 emission filter
    :param      RG665_sample:   list of LEDs which are placed at the RG665 emission filter
    :param      led_order:
    :return:
    """
    # double-check LEDs
    if isinstance(led_order[0], int) or isinstance(led_order[0], float):
        led_order = [str(int(i)) + ' nm' if i != 0. else i for i in led_order]

    # Load emission factors from file
    em_path = loc_path + '/supplementary/calibration/emission-site/emission_device-' + str(device) + '.txt'
    if os.path.isfile(em_path) is False:
        print('Warning! File not found; hence we use the default file', file_em)
        em_path = file_em
    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = led_order

    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9)
    for i in RG9_sample:
        i = find_label(label=i, ls=mean.index)
        if i in mean.index:
            mean.loc[i, :] = mean.loc[i, :].values[0] / balance_factor.loc[int(device), i]
        else:
            print('LED', i, 'not used for analysis')
    for i in RG665_sample:
        i = find_label(label=i, ls=mean.index)
        if i in mean.index:
            mean.loc[i, :] = mean.loc[i, :].values[0] / balance_factor.loc[int(device), i]
        else:
            print('LED', i, 'not used for analysis')

    return mean


def em_corr_table(file_em, df, device, RG9, RG665, led_order):
    """
    :param  file_em:
    :param  df:
    :param  device:
    :param  RG9:
    :param  RG665:
    :param  led_order:
    :return:
    """
    # Load emission factors from file
    em_path = loc_path + '/supplementary/calibration/emission-site/emission_device-' + str(device) + '.txt'
    if os.path.isfile(em_path) is False:
        print('Warning! File not found; hence we use the default file', file_em)
        em_path = file_em

    balance_factor = pd.read_csv(em_path, sep='\t', encoding="latin-1", index_col=0, header=[0, 1])
    balance_factor.columns = led_order

    # Balance the RG665 and RG9 emission filters by LED-at-RG665 = LED-at-RG9 / balance_factor(RG665/RG9). Dimension = 1
    df_em = pd.DataFrame(np.zeros(shape=(len(df.index), 0)), index=df.index)
    for i in RG9:
        if i in balance_factor.columns:
            df_em[i] = df[i].values / balance_factor.loc[int(device), i]
        else:
            if isinstance(i, str):
                if int(i.split(' ')[0]) in balance_factor.columns:
                    df_em[i] = df[i].values / balance_factor.loc[int(device), int(i.split(' ')[0])]
            else:
                if str(i) + ' nm' in balance_factor.columns:
                    df_em[str(i) + ' nm'] = df[str(i) + ' nm'].values / balance_factor.loc[int(device), str(i) + ' nm']
    for i in RG665:
        if i in balance_factor.columns:
            df_em[i] = df[i].values / balance_factor.loc[int(device), i]
        else:
            if isinstance(i, str):
                if int(i.split(' ')[0]) in balance_factor.columns:
                    df_em[i] = df[i].values / balance_factor.loc[int(device), int(i.split(' ')[0])]
            else:
                if str(i) + ' nm' in balance_factor.columns:
                    df_em[str(i) + ' nm'] = df[str(i) + ' nm'].values / balance_factor.loc[int(device), str(i) + ' nm']
    return df_em


def correction_led(mean, kappa_spec, date, current, peakcolumns, led_total, full_calibration=True):
    """ Balance the LED-intensity based on the correction factors (kappa) calculated by the mean of the internal quantum
    counter. It returns an Data Frame containing the corrected mean values for each LED.
    :param mean:
    :param kappa_spec:
    :param date:
    :param current:
    :param peakcolumns:
    :param led_total:
    :param full_calibration:
    :return: mean_corr
    """
    # Correction of the LED intensities for standardizing the measurement and inter-comparability.
    # Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum counter) and multiply the
    # factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
    # update led_total
    if isinstance(led_total[0], int) or isinstance(led_total[0], float):
        led_total = [str(int(i)) + ' nm' if i != 0 else i for i in led_total]

    if kappa_spec is None:
        # no specified correction factor. load the factor according to the date of the measurement file.
        if full_calibration is False:
            kappa_ = loc_path + '/supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            if os.path.exists(kap) is True:
                kappa = pd.read_csv(kap, sep='\t', index_col=0)
            else:
                print("ERROR! No such file in directory!")
                return
        else:
            kappa_ = loc_path + '/supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            kappa = pd.read_csv(kap, sep='\t', index_col=0)
    else:
        kappa = pd.read_csv(kappa_spec, sep='\t', index_col=0)

    corr_factor = kappa.loc[:kappa.index[-2], :].astype(float)
    corr_factor = corr_factor.set_index(corr_factor.index.astype(int))
    mean_corr = mean.copy()
    mean = pd.DataFrame(mean_corr)

    if not current:
        if full_calibration is True:
            current = [97]*len(mean_corr.index)
        else:
            current = [50]*len(mean_corr.index)
    else:
        # reduce current-list to number of LEDs used for analysis
        current_red = []
        for i, p in enumerate(led_total):
            if p in peakcolumns:
                current_red.append(current[i])
        current = current_red

    if current[0] not in corr_factor.index:
        print("WARNING! Correction not processed! No correction factor for {}mA in calibrationfile!".format(current[0]))
        pass
    else:
        if type(current) == float or type(current) == int:
            current = [int(current)] * len(led_total)
            current = pd.DataFrame(current, index=peakcolumns).T
        elif type(current) == list:
            current = pd.DataFrame(current, index=peakcolumns).T
        for k in current.columns:                           # k: LED_wl
            if k not in corr_factor.columns:
                print('\n', 'Warning! No correction factor for LED {}'.format(k))
                for r in range(len(mean.columns)):                  # if there are more than one column in the matrix
                    mean_corr.loc[k, r] = mean.loc[k, r] * 1.0E-3
            else:
                for r in mean.columns:                              # if there are more than one column in the matrix
                    mean_corr.loc[k, r] = mean.loc[k, r] * corr_factor.loc[current.loc[0, k], k]
    return mean_corr


def correction_led_table(df, kappa_spec, date, current, peakcolumns, full_calibration=True):
    """ Balance the LED-intensity based on the correction factors (kappa) calculated by the mean of the internal quantum
    counter.
    :param df:
    :param kappa_spec:
    :param date:
    :param current:
    :param peakcolumns:
    :param full_calibration:
    :return: mean_corr
    """
    if kappa_spec is None:  # automatically chosen excitation-correction file
        # no specified correction factor. load the factor according to the date of the measurement file.
        if full_calibration is False:  # linear fit between 30-50mA
            kappa_ = loc_path + '/supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            if os.path.exists(kap) is True:
                kappa = pd.read_csv(kap, sep='\t', index_col=0)
            else:
                print("ERROR! No such file in directory!")
                return
        else:
            kappa_ = loc_path + '/supplementary/calibration/excitation-site/'
            kap = kappa_ + str(date[:-4]) + '_LED_correction_rhodamine101_spectrum.txt'
            kappa = pd.read_csv(kap, sep='\t', index_col=0)
    else:
        # specific file for excitation
        kappa = pd.read_csv(kappa_spec, sep='\t', index_col=0)

    # Preparation of data frames so you won't overwrite anything
    corr_factor = kappa.iloc[:-1].astype(float)
    corr_factor = corr_factor.set_index(corr_factor.index.astype(int))
    df_led_corr = df.copy()
    df = pd.DataFrame(df)

    if not current:
        current = [97]*8 if full_calibration is True else [50]*8

    # Correction of the LED intensities for standardizing the measurement and inter-comparability.
    # Load correction factors for rhodamine 101 12mM in ethylene glycol(internal quantum counter) and multiply the
    # factors with the LED intensity to get the inter-comparability / ist-LED-intensity.
    if current[0] not in corr_factor.index:
        print("WARNING! Correction not processed! No correction factor for {}mA in file!".format(current[0]))
        pass
    else:
        # preparation of LED current; default type is list but for manual input it might be just one integer
        if type(current) == float or type(current) == int:
            current = pd.DataFrame([int(current)] * 8, index=peakcolumns).T
        elif type(current) == list:
            current = pd.DataFrame(current, index=peakcolumns).T

        # multiplication of LED correction factor and LED value
        for k in current.columns:                           # k: LED_wl
            if k in df.columns:
                if k not in corr_factor.columns:
                    print('\n', 'Warning! No correction factor for LED {}'.format(k))
                    df_led_corr[k] = df[k] * 1.0E-3
                else:
                    df_led_corr[k] = df[k] * corr_factor.loc[current.loc[0, k], k]
    return df_led_corr


def average_fluorescence(mean_corr, training_corr_sort, normalize=True, standardize=True):
    # calculate average fluorescence intensity at different excitation wavelengths
    # pigment pattern just with normalised, but not with standardised sample data
    pigment_pattern = mean_corr.copy()
    pigment_pattern = pre_process(pigment_pattern, normalize=True, standardize=False)
    pigment_pattern.columns = ['mean value [pW]']

    # pre-processing of the sample data at the same level as for the training matrix
    mean_corr = pre_process(mean_corr, normalize=normalize, standardize=standardize)
    if type(mean_corr) == pd.DataFrame:
        pass
    else:
        mean_corr = pd.DataFrame(mean_corr, columns=['sample'])

    training_corr_ = pre_process(training_corr_sort.T, normalize=normalize, standardize=standardize).T
    training_corr = pd.DataFrame(training_corr_)

    return mean_corr, training_corr, pigment_pattern


# ---------------------------------------------------------------------------------------------------------------------
def priority_lda(training_data_list, separation, training_corr):
    # training data used
    tr = training_data_list.tolist()

    # principle possible algae samples analysed
    qqt = pd.read_csv(loc_path + '/supplementary/phytoplankton/170427_algae.txt', sep='\t', header=0,
                      encoding="latin-1")
    con = pd.DataFrame(qqt[separation])
    con.index = qqt['genus']

    # table of algae analysed and taxonomic level according to separation level
    con_ = con.loc[:con.index[-2]]

    # reduce principle possible groups to the amount of effectively used groups
    group = []
    for i in range(len(tr)):
        if tr[i] in con_.index:
            group.append(con_.loc[tr[i], separation])
        else:
            print('Warning! Sample {} not found in training matrix...'.format(tr[i]))
            training_corr = training_corr.drop(tr[i])

    groups = pd.DataFrame(group).drop_duplicates()
    groups.index, groups.columns = np.arange(len(groups)), ['groups']
    groups['emphasis'] = np.zeros(shape=(len(groups), 1))

    # dinoflagellate potentially for analysis
    if separation == 'order' or separation == 'family':
        b, c = 'class', 'Dinophyceae'
    elif separation == 'class' or separation == 'phylum':
        b, c = 'phylum', 'Miozoa'
    else:
        b, c = None, None
    a = pd.DataFrame(qqt[b])
    a.index = qqt['genus']
    a = a.loc[:a.index[-2]]
    a_con = a if separation == 'phylum' else pd.concat([con, a], axis=1)

    dino = a_con[a_con[b] == c].drop_duplicates()
    dinos_in_group = []
    for d in range(len(dino[separation])):
        if dino[separation][d] in groups['groups'].values:
            dinos_in_group.append(int(groups[groups['groups'] == dino[separation].values[d]]['emphasis'].index[0]))
        else:
            pass

    # get and normalize priority (must sum up to 1 for LDA)
    for t in range(len(dinos_in_group)):
        groups.loc[dinos_in_group[t], 'emphasis'] = len(groups) / len(dinos_in_group)
    priority = groups['emphasis'].tolist() / sum(groups['emphasis'])

    return groups, priority, training_corr


def lda_sep(data, classes_dict, priors=None):
    """ running linear discriminant analysis for a given data set (mean values for different LEDs).
    The analysis bases on the Singular value decomposition (as default). It does not compute the
    covariance matrix, therefore this solver is recommended for data with a large number of features.
    Least square solution or eigenvalue decomposition are also possible.
    :param:     data:                       mean values of the sample at different LEDs
    :return:    LinearDiscriminantAnalysis: describe the analysis' quality
    """
    # data analysis
    classes = np.array([classes_dict[l] for l in data.index])
    lda = LinearDiscriminantAnalysis(n_components=min(data.shape), store_covariance=True, priors=priors, solver='svd')

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
    lda = lda_sep(training, classes_dict, priors=priors)

    # (Coordinates) transformation in (sub)space for enhances class separation
    training_score = lda.transform(training)
    df_score = lda.transform(df)

    # linear discriminant analysis with sample data and plot training and sample data in one plot
    if plot_score is True:
        if number_components <= 2:
            type_ = 2
        ax = lda_plot(training, lda, classes_dict, color_dict, type_=type_)
        _ = lda_plot(df, lda, classes_dict, color_dict, type_=type_, ax=ax, marker='^')

    col_name = []
    for i in np.arange(df_score.size):
        col_name.append('LDA' + str(i + 1))
    df_score = pd.DataFrame(df_score, columns=[col_name], index=['sample'] * len(df_score))
    training_score = pd.DataFrame(training_score, columns=[col_name], index=training.index)
    return lda, training_score, df_score


def lda_process_mean(mean_fluoro, training_corr, unit, classes_dict, colorclass_dict, separation='class',
                     priority=False, type_=2):
    """ Complete analysis by the mean of the linear discriminant analysis of a measured sample. The raw data are
           optionally blank corrected and peaks > LoD (3*std(blank)) are extracted. The signal intensity of the same
           biomass at different LEDs is clustered together.
           :param:     data:                path to the data file
                       trainingdata:        path to the training data for the LDA
                       kappa_spec:          correction factors of the device for inter-comparability
                       kappa_training:      correction factors of the device for inter-comparability. Just for training
                                            data
                       seperation:          defines the taxonomic level at which the separation should take place
                       priority:            If yes, the dinophyta is emphasised to be separated. Otherwise all groups
                                            have the same priority
                       number_components:   define number of degrees of freedom for LDA separation
                       pumprate:            definition of the pump speed [ml/min] to define the analysed sample volume
                       correction:          correction of LED intensity for inter-comparability and correction of
                                            differences in emission filter properties
                       blank_corr:          optionally correction of the raw data-file. The training data will be blank
                                            corrected anyway
                       blank_std_ex:        give an external calculated deviation of the blank measurement
                       blank_mean_ex:       give an external calculated mean value of the blank measurement
                       plot_data:           time-drive plot of the sample. Default is False
                       plot_score:          resulting score plot for training data and sample data. Default is True
                       plot_distance:       plots the scores of the sample and the spheres of the algae classes to
                                            visualize the sample affiliations
                       type_:               2dim or 3dim plot of the results
                       normalize:           normalisation of the training and sample data. Same option for both data to
                                            ensure an equivalent analysis. Default = True
                       standardize:         standardisation, i.e. centering and auto-scaling of training and sample data
                                            for the algorithm. Default = True
                       save:                store the results of the analysis. When individual peaks are analysed only a
                                            summary (which algal classes could be found + their probability) is
                                            exported. Standard txt file for english application (sep = '\t',
                                            decimal = '.')
           :return:    lda = sklearn.discriminant_analysis.LinearDiscriminantAnalysis
                       df_score = pd.DataFrame:         resulting score values (from LDA) for the analyzed sample
                       training_score = pd.DataFrame:   resulting score values (from LDA) for each algal sample in the
                                                        training matrix
                       d_ = list/pd.DataFrame:          mean values for each algal class, their spatial distribution and
                                                        the distance between the sample and each class center
                       prob = list/pd.DataFrame:        probability of belonging to a certain algal class
           """
    # sort LEDs by wavelength
    df = mean_fluoro.sort_index().T

    # adaption for the output
    mean_fluoro.columns = [unit]

    if priority is True:
        priority = False if separation == 'phylum' or separation == 'class' else True
    if priority is True:
        [_, priors, training_corr] = priority_lda(training_corr.index, separation, training_corr)
    else:
        priors = None

    # linear discriminant analysis
    [lda, training_score,
     df_score] = lda_analysis(df, training_corr, classes_dict, colorclass_dict, priors=priors, plot_score=False,
                              number_components=len(mean_fluoro.index), type_=type_)
    return lda, training_score, df_score


# ---------------------------------------------------------------------------------------------------------------------
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


def reference_scores(lda, training_score, classes_dict):
    """ Calculating the distance between sample and centroid of each algal class.
    :param:     lda:                sklearn.discriminant_analysis.LinearDiscriminantAnalysis
                training_score:     score values of all training samples labeled with their class affiliation
    :return:    d = pd.DataFrame:   containing the centroid for each algal class, the group variances
                                    in each direction as well as the distance between centroid and sample
    """
    # classify all algal samples according to their class affiliation
    group = lda.classes_
    q = []
    training_score['label'] = [0]*len(training_score)
    for i in training_score.index:
        training_score.loc[i, 'label'] = classes_dict[i]

    for k in training_score['label']:
        if k == group[0]:
            q.append(k)

    # calculation of centroid for each class as well as their spatial distribution in each direction
    training_score.columns = training_score.columns.levels[0]
    centroid = training_score.groupby("label").median()
    d = centroid.copy()
    for v in training_score.columns[:-1]:
        col = str(v) + 'var'
        d[col] = training_score.groupby("label").var().loc[:, v]
    # replace NaN values with a small distribution
    for c in d.columns:
        if c[-3:] == 'var':
            d[c][np.isnan(d[c])] = 5E-3
    return d


def sample_distance(d, df_score):
    """ Calculating of distance between sample and the centroid to each algal class.
    :param:     d:          scores of the centers of all algal classes as well as their spatial distribution
                            (variance in each direction)
                df_score:   resulting score values of the sample after the application of the LDA
    :return:    d_:         pd.DataFrame of algal classes, their centroids, group variances in each direction
                            as well as the distance between centroid and sample
    """
    # calculation of distance between sample and centroid-median
    d['distance'] = np.zeros(len(d))
    df_score = pd.DataFrame(df_score)
    df_score.columns = df_score.columns.levels[0]

    list = pd.DataFrame(np.zeros(shape=(len(d), len(df_score.index))), index=d.index)
    for i in d.index:
        for y in range(len(df_score.columns)):
            list.loc[i, y] = (((d.loc[i, :][df_score.columns[y]] - df_score[df_score.columns[y]])**2).values[0])
    d['distance'] = (np.sqrt(sum(list, axis=1)))

    # sort distance
    d_ = d.sort_values(by='distance')
    return d_


def prob_(d):
    """ Based on the distance between sample and class centroid (median), the 3dimensional gaussian distribution is
        calculated and combined with a probability that the sample belongs to a certain algal group.
    :param:     d:      pd.DataFrame of algal classes, their centroids, group variances in each direction as
                        well as the distance between centroid and sample
    :return:    prob:   pd.DataFrame containing the probability that a sample belongs to a certain algal class
    """
    # probability if the sample belongs to the algal group
    # calculate gaussian distribution for the sample in each class (prob = exp(-0.5*distance)*100 [%])
    pro, alg = [], []

    # d['distance'] contains the distance between test point and mean/median of the group. According to Prasanta Chandra
    # Mahalanobis this distance is equal to the argument in the multivariate normal density distribution.
    # (x - µ)^T * Covariancematrix * (x - µ) Mahalanobis-Distance
    for el in d.index:
        alg.append(el)
        pro.append(np.exp(-0.5*d['distance'][el])*100)
    prob = pd.DataFrame(pro, index=alg, columns=['gaussian prob.'])

    return prob


def prep_lda_classify(lda, training_score, df_score, classes_dict):
    d = reference_scores(lda, training_score, classes_dict)
    d_, prob = [], []
    for el in range(len(df_score)):
        d_.append(sample_distance(d, df_score))
        prob.append(prob_(d_[el]))

    # load overview file for algal groups and group colors
    alg_group = pd.read_csv(file_group, sep='\t', encoding="latin-1")
    alg_phylum = pd.read_csv(file_phylum, sep='\t', header=None, encoding="latin-1", usecols=[1, 2],
                             index_col=0).drop_duplicates()
    phyl_group = pd.DataFrame(np.zeros(shape=(0, 2)), columns=['phylum_label', 'color'])

    return alg_group, alg_phylum, phyl_group, d_, d, prob


# ---------------------------------------------------------------------------------------------------------------------
def output(sample, summary, summary_, path, date, prob, separation='phylum', save=True):
    """
    :param: sample:             list; peak number which has a probability > 1E-2 of belonging to a separation group
            sample_plot:        list; shorted version of sample
            summary:            list; which algal classes were identified in the sample
            summary_:           list; probability of the class affiliation
            path:               direction to the saving place. Same folder as for the input file
            date:               to mark the relationship of the input and output files
            save:               store the results of the analysis. When individual peaks are analysed
                                only a summary (which algal classes could be found + their probability)
                                is exported. English txt file format (sep = '\t', decimal = '.')
    :return: res = pandas.DataFrame of the detected algal classes and the corresponding probability
    """
    [prob_red, prob_red_gauss] = taxonomic_level_reduction(prob, separation=separation, likelyhood=True)

    prob_phylum = pd.concat([pd.DataFrame(prob_red), pd.DataFrame(prob_red_gauss)], axis=1)
    prob_phylum.columns = ['identified phylum', 'gaussian probability [%]']

    # prepare the output file
    out = []
    for i in range(len(sample)):
        out.append(['sample peak {}'.format(sample[i]), summary[i], summary_[i]])
    if not out:
        print('-> EXIT! The sample contains no known algae classes!')
    else:
        for i in range(len(out)):
            out[i][-1] = (round(out[i][-1], 2))
    res = pd.DataFrame(out, columns=['sample peak', 'identified class', 'probability [%]'])

    # overall probability
    b = prob[0]['gaussian prob.']
    bb = b.drop([b.idxmax()])
    overall = round((b.max() - bb.max()) / b.max() * 100, 3)
    res1 = res.append(pd.DataFrame(['----', '----', '----'], index=res.columns).T)
    res1 = res1.append(pd.DataFrame(['overall security [%] for class', prob[0].index[0], overall], index=res.columns).T)

    if save is True:
        newfolder = path + '/' + 'results_LDA'
        # check if results-folder already exists. if not, create one
        if not os.path.exists(newfolder):
            os.makedirs(newfolder)

        # save file to the same directory as the raw data file
        result_LDA = newfolder + '/' + date + '_' + '_result_LDA_peak.txt'
        result_phylum = newfolder + '/' + date + '_' + '_result_LDA_superordinate.txt'

        res1.to_csv(result_LDA, sep='\t', index=False)
        prob_phylum.to_csv(result_phylum, sep='\t', index=False)

    return res, prob_phylum


def linear_discriminant_save(res, prob_phylum, info, date, name, path, blank_corr, correction, peak_detection=True,
                             additional=False):
    # define folder and name of result-file
    newfolder = path + '/' + 'results_LDA'
    if blank_corr is True:
        newfolder += '_blank'
    if correction is True:
        newfolder += '_correction'
    if additional is True:
        newfolder += '_addcomp'
    if peak_detection is True:
        newfolder += '_peak'

    # check if results-folder already exists. if not, create one
    if not os.path.exists(newfolder):
        os.makedirs(newfolder)

    # save file to the same directory as the raw data file
    result = newfolder + '/' + date + '_' + name + '_' + info + '_result_LDA.txt'

    # create output file
    firstline = [str(date), str(name), info]
    res_col = res.columns
    prob_col = prob_phylum.columns

    secondline = pd.concat([pd.DataFrame(res_col), pd.DataFrame(prob_col)], axis=0)
    second = pd.DataFrame(secondline[0].values.tolist())
    first = pd.DataFrame(firstline)
    header = pd.concat([first.T, second.T], axis=0)
    res.columns = np.arange(0, len(res.columns))
    prob_phylum.columns = np.arange(len(res.columns)+1, len(res.columns)+1+len(prob_phylum.columns))
    res_save_ = pd.concat([res, prob_phylum], axis=1)
    res_save = pd.concat([header, res_save_], axis=0)
    res_save.to_csv(result, sep='\t', index=False, header=False)

    return res_save
