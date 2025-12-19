# ALPACA 2.0

Graphical User Interface (GUI) for ALPACA – a multi-channel flow-through fluorimeter for chemotaxonomic identification and classification of potential toxin production algae groups.
The software algorithm includes a supervised pattern recognition algorithm (linear discriminant analysis) and cluster algorithm (Euclidean distance) for identifying the probability of belonging. 

To access the software, you may download the python script (GUI_wizard.py and GUI_LDA_functions.py) as well as the accompaying folders (logo, measurement, and supplementary). Please save everything in one directory and keep the structure. The main script is GUI_wizard.py and can be executed with your terminal (command line front-end). If you encounter any issues, please reach out via mail at info@silviazieger.com

Pigment-based chemotaxonomy using Fisher's linear discriminant analysis for supervised group allocation.

For more information about the theory, please have a look at the corresponding dissertation: Zieger, SRE 2020, Multiparametric Sensing - from Development to Application in Marine Science.


Further information:
· DOI: 10.1021/acs.est.8b04528
and
· DOI: 10.1021/acs.est.8b00578


ALPACA 
The occurrence and intensity of (harmful) algal blooms (HABs) have increased through the years due to rapidly changing environmental conditions. At the same time, the demand for low-cost instrumentation has increased substantially, enabling the real-time monitoring and early-stage detection of HABs. To meet this challenge, we have developed a compact multi-wavelength fluorometer for less than 400 USD. This is possible by using readily available and low-cost optical and electronic components. Its modular design results in a highly versatile and flexible monitoring tool. The algae detection module enables a continuous identification and control of relevant algal groups based on their spectral characteristics with a detection limit of 10 cells per liter. Besides its usage as a benchtop module in the laboratory, the algae module has been integrated into submersible housings and applied in coastal environments. During its first in situ application in the Port of Genoa, seawater samples of mixed algal composition were used to demonstrate the successful discrimination of cyanobacteria and dinophytes as well-known toxin producing classes. Fabrication, operation, and performance as well as its first in situ application are addressed.

Theory on chemotaxonomy
Early stage identification of harmful algal blooms (HABs) has gained significance for marine monitoring systems over the years. Various approaches for in situ classification have been developed. Among them, pigment-based taxonomic classification is one promising technique for in situ characterization of bloom compositions, although it is yet underutilized in marine monitoring programs. To demonstrate the applicability and importance of this powerful approach for monitoring programs, we combined an ultra low-cost and miniaturized multichannel fluorometer with Fisher’s linear discriminant analysis (LDA). This enables the real-time characterization of algal blooms at order level based on their spectral properties. The classification capability of the algorithm was examined with a leave-one-out cross validation of 53 different unialgal cultures conducted in terms of standard statistical measures and independent figures of merit. The separation capability of the linear discriminant analysis was further successfully examined in mixed algal suspensions. Besides this, the impact of the growing status on the classification capability was assessed. Further, we provide a comprehensive study of spectral features of eight different phytoplankton phyla including an extensive study of fluorescence excitation spectra and marker pigments analyzed via HPLC. The analyzed phytoplankton species belong to the phyla of Cyanobacteria, Dinophyta (Dinoflagellates), Bacillariophyta (Diatoms), Haptophyta, Chlorophyta, Ochrophyta, Cryptophyta, and Euglenophyta.