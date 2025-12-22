# ALPACA (v2.0)

<table>
<tr>
<td width="70%">

**Multi-Channel Flow-Through Fluorometer for Harmful Algal Bloom Detection**

A graphical user interface for ALPACA – an ultra low-cost (<400 USD) fluorometer system for real-time identification and classification of phytoplankton groups based on their spectral characteristics. The software implements supervised pattern recognition (Fisher's Linear Discriminant Analysis) and cluster algorithms (Euclidean distance) for chemotaxonomic classification with detection limits down to 10 cells per liter.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://img.shields.io/badge/DOI-10.1021%2Facs.est.8b04528-blue)](https://doi.org/10.1021/acs.est.8b04528)

</td>
<td width="30%">
  
<img height="300" alt="logo_ALPACA4" src="https://github.com/user-attachments/assets/ccc502a9-b124-40f4-9e64-5f0698a6c0cd" />

</td>
</tr>
</table>


## Overview

Climate change and environmental shifts have increased the frequency and intensity of harmful algal blooms (HABs) worldwide. ALPACA addresses the critical need for affordable, real-time monitoring solutions by combining:

- **Low-Cost Hardware**: Multi-wavelength fluorometer built for <400 USD using readily available components
- **Intelligent Software**: Machine learning algorithms for automated species identification
- **Field-Ready Design**: Modular system suitable for laboratory benchtop or submersible in situ deployment
- **High Sensitivity**: Detection limit of 10 cells per liter


## Scientific Background

### Pigment-Based Chemotaxonomy

ALPACA uses spectral fingerprinting of photosynthetic pigments to identify algal groups. Different phytoplankton classes contain unique combinations of pigments (chlorophylls, carotenoids, phycobilins) that produce characteristic fluorescence patterns when excited at specific wavelengths.

### Supported Phytoplankton Groups

The system has been trained and validated on **8 major phytoplankton phyla**:

| Phylum | Common Name | HAB Relevance |
|--------|-------------|---------------|
| **Cyanobacteria** | Blue-green algae | Toxin producers (microcystins, nodularins) |
| **Dinophyta** | Dinoflagellates | Toxin producers (saxitoxins, brevetoxins) |
| **Bacillariophyta** | Diatoms | Dominant primary producers |
| **Haptophyta** | Coccolithophores, etc. | Bloom formers |
| **Chlorophyta** | Green algae | Freshwater/marine |
| **Ochrophyta** | Brown algae | Coastal ecosystems |
| **Cryptophyta** | Cryptophytes | Diverse environments |
| **Euglenophyta** | Euglenoids | Freshwater indicators |



## Key Features

### Software Capabilities
- **Supervised Classification**: Fisher's Linear Discriminant Analysis (LDA) for species identification
- **Unsupervised Clustering**: Euclidean distance-based grouping for unknown samples
- **Probability Assessment**: Quantified confidence scores for taxonomic assignments
- **Cross-Validation**: Leave-one-out validation with 53 unialgal cultures
- **Mixed Population Analysis**: Capability to analyze multi-species samples
- **Growth Stage Compensation**: Accounts for physiological variations

### Hardware Advantages
- **Ultra Low-Cost**: <400 USD using off-the-shelf components
- **Modular Design**: Flexible configuration for different applications
- **Dual Deployment**: Benchtop laboratory use or submersible housing for in situ monitoring
- **Multi-Wavelength**: Captures comprehensive spectral information
- **Real-Time Analysis**: Continuous monitoring and immediate classification



## Prerequisites

### System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.7 or higher
- **Memory**: 4 GB RAM minimum (8 GB recommended)
- **Storage**: 500 MB available space

### Knowledge Requirements
- Basic understanding of phytoplankton ecology
- Familiarity with fluorescence spectroscopy (recommended)
- No programming knowledge required for GUI operation



## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/alpaca-2.0.git
cd alpaca-2.0
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

Or if you're using a virtual environment (recommended):

```bash
# Create virtual environment
python3 -m venv alpaca-env

# Activate virtual environment
# On macOS/Linux:
source alpaca-env/bin/activate
# On Windows:
alpaca-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Required packages typically include:
- numpy
- pandas
- matplotlib
- scikit-learn
- scipy
- tkinter (usually included with Python)

### 3. Verify Directory Structure

Ensure the following structure is maintained:

```
alpaca-2.0/
│
├── GUI_LDA_wizard.py          # Main application script
├── GUI_LDA_functions.py       # LDA algorithm functions
├── requirements.txt           # Python dependencies
│
├── logo/                      # Application graphics
├── measurement/               # Sample data and measurement files
└── supplementary/             # Additional resources and documentation
```

### 4. Run the Application

```bash
python3 GUI_LDA_wizard.py
```

**Note**: On some systems, you may need to use `python` instead of `python3`:
```bash
python GUI_LDA_wizard.py
```


## Quick Start Guide

### 1. Launch ALPACA GUI
Execute the main script from your terminal:
```bash
python3 GUI_LDA_wizard.py
```

**Alternative commands** depending on your system:
```bash
# If python3 is not recognized
python GUI_LDA_wizard.py

# Or with full path
python3 /path/to/alpaca-2.0/GUI_LDA_wizard.py
```

### 2. Load Measurement Data
- Import fluorescence spectra from the ALPACA fluorometer
- Supported formats: CSV, TXT (tab-delimited)
- Load calibration data if using a new instrument

### 3. Configure Analysis
- **Training Mode**: Build or update LDA models with known cultures
- **Classification Mode**: Identify unknown samples
- **Mixed Population Mode**: Analyze multi-species blooms

### 4. Run Classification
- Execute LDA analysis
- Review probability scores for each identified group
- Examine spectral plots and diagnostic information

### 5. Export Results
- Save classification reports (CSV, PDF)
- Export spectral plots
- Generate summary statistics


## Validation & Performance

### Classification Accuracy
- **Validation Method**: Leave-one-out cross-validation (LOOCV)
- **Training Set**: 53 unialgal cultures across 8 phyla
- **Performance Metrics**: Sensitivity, specificity, precision, recall
- **Mixed Cultures**: Successfully discriminates cyanobacteria and dinoflagellates

### Field Testing
**First in situ deployment**: Port of Genoa, Italy
- Real-time monitoring of coastal waters
- Successful discrimination of toxin-producing classes
- Validated against HPLC pigment analysis


## Workflow Example

### Typical Use Case: HAB Early Warning System

1. **Continuous Monitoring**
   - ALPACA deployed in submersible housing
   - Autonomous sampling every 30-60 minutes
   
2. **Real-Time Classification**
   - Spectral data transmitted to shore station
   - GUI processes spectra using pre-trained LDA model
   
3. **Alert Generation**
   - High probability detection of toxin-producing groups triggers alert
   - Notification sent to monitoring authorities
   
4. **Validation & Response**
   - Water samples collected for confirmatory analysis
   - Management decisions based on verified HAB composition

---

## Advanced Configuration

### Training Custom LDA Models

To create classification models for your specific region or target species:

1. Collect monoculture reference samples
2. Measure fluorescence excitation spectra
3. Load spectra into training mode
4. Generate and validate LDA model
5. Export model for field deployment

### Integrating HPLC Data

For enhanced validation, integrate High-Performance Liquid Chromatography (HPLC) pigment analysis:

1. Collect parallel water samples during ALPACA measurements
2. Analyze marker pigments via HPLC
3. Compare chemotaxonomic assignments
4. Refine LDA model based on discrepancies


## Publications & Citations

### Primary References

```bibtex
@article{Zieger2018Hardware,
  title={Compact and Low-Cost Fluorescence Based Flow-Through Analyzer for Early-Stage Classification of Potentially Toxic Algae and in Situ Semiquantification},
  journal={Environmental Science & Technology},
  year={2018},
  doi={10.1021/acs.est.8b00578}
}
```

```bibtex
@article{Zieger2018LDA,
  title={Pigment-Based Chemotaxonomy of Phytoplankton using Linear Discriminant Analysis},
  journal={Environmental Science & Technology},
  year={2018},
  doi={10.1021/acs.est.8b04528}
}
```

```bibtex
@article{Zieger2018Chemotaxonomy,
  title={Spectral Characterization of Eight Marine Phytoplankton Phyla and Assessing a Pigment-Based Taxonomic Discriminant Analysis for the in Situ Classification of Phytoplankton Blooms},
  journal={Environmental Science & Technology},
  year={2018},
  doi={10.1021/acs.est.8b04528}
}
```

### Related Publications
- DOI: [10.1021/acs.est.8b04528](https://doi.org/10.1021/acs.est.8b04528)
- DOI: [10.1021/acs.est.8b00578](https://doi.org/10.1021/acs.est.8b00578)


## Troubleshooting

### Common Issues

**Issue**: GUI doesn't launch
```bash
# Check Python version
python3 --version  # Should be 3.7+

# Try running with verbose error messages
python3 -v GUI_LDA_wizard.py
```

**Issue**: Module not found errors
```bash
# Reinstall all requirements
pip3 install -r requirements.txt --upgrade

# Or install specific missing package
pip3 install package-name
```

**Issue**: Permission denied
```bash
# Make the script executable (macOS/Linux)
chmod +x GUI_LDA_wizard.py

# Then run directly
./GUI_LDA_wizard.py
```

**Issue**: Classification errors or low confidence
- Verify spectral data quality (no saturation, proper baseline)
- Check that excitation wavelengths match training data
- Ensure instrument calibration is current
- Consider growth stage variations in samples

**Issue**: Logo/images not displaying
- Confirm `logo/` folder is in the same directory as `GUI_LDA_wizard.py`
- Check file paths in the GUI script
- Verify image file formats are supported

**Issue**: Slow performance or crashes
- Check available system memory
- Reduce dataset size for initial testing
- Close other memory-intensive applications
- Consider using a virtual environment


## Contributing

We welcome contributions from the community!

### How to Contribute
1. **Report Bugs**: Open an issue with detailed description and error messages
2. **Suggest Features**: Describe new capabilities or improvements
3. **Add Training Data**: Share validated spectra from new species/regions
4. **Improve Documentation**: Help make ALPACA more accessible
5. **Submit Code**: Fork the repository and create a pull request

### Development Priorities
- Expanding training database with more species
- Regional model optimization
- Integration with other sensor platforms
- Mobile/web-based interface
- Automated quality control algorithms


## Real-World Applications

### Current Use Cases
- **Coastal Monitoring**: Early detection of HAB events in harbors and bays
- **Aquaculture**: Water quality monitoring for fish/shellfish farms
- **Drinking Water**: Source water protection for municipal systems
- **Research**: Ecological studies of phytoplankton dynamics
- **Education**: Teaching tool for marine biology and oceanography

### Potential Expansions
- Autonomous underwater vehicles (AUVs)
- Buoy-based monitoring networks
- Citizen science programs
- Climate change impact studies


## License

Copyright © 2020 Silvia R. E. Zieger. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND**, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## Contact & Support

**Developer**: Silvia R. E. Zieger  
**Email**: [info@silviazieger.com](mailto:info@silviazieger.com)  
**Issues**: [GitHub Issues](../../issues)

For hardware inquiries, collaboration opportunities, or technical support, please reach out via email.


## Acknowledgments

This work was supported by:
- Research institutions and funding agencies
- Marine monitoring organizations who tested ALPACA in the field
- The phytoplankton ecology community for providing reference cultures
- Open-source software contributors

Special thanks to colleagues at the Port of Genoa for hosting the first in situ deployment.


## Research Opportunities
- Long-term deployment studies
- Climate change impact assessment
- Toxin prediction models
- Ecosystem modeling integration

---

<p align="center">
  <sub>Protecting marine ecosystems through affordable, accessible technology 🌊</sub>
</p>
