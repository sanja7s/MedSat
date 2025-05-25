# NHS Prescription Parser

**A unified system for computing drug and condition prevalences at the LSOA level in England from NHS prescription data.**

This module is part of the MedSat research project, integrating medical prescription data with satellite imagery for public health research. The system supports both historical and current NHS data formats with automatic detection and processing.

## 🚀 **One-Command Setup**

```bash
git clone <repository-url>
cd MedSat/code/collate_data/NHS_prescription_parser
./bootstrap.sh
```

The bootstrap script will:
- ✅ Set up Python environment and dependencies
- ✅ Check for missing essential files and offer downloads
- ✅ Configure Git LFS for large mapping files (47 files tracked)
- ✅ Create utility scripts for easy analysis
- ✅ Guide you through setup if needed

### After Bootstrap

```bash
# Activate environment
source activate_env.sh

# Verify everything works
./verify_setup.sh

# Start analyzing
./run_analysis.sh drug metformin 2021
```

## 🆕 **What's New in the Unified Version**

- **Single command interface** for all prescription analysis types
- **Automatic format detection** for old (2014-2021) and new (2021+) data formats
- **Extended date range support** from 201401 to 202112
- **Multi-year LSOA mapping** with automatic year detection
- **Git LFS integration** for 47 mapping files (35MB-29MB large files)
- **Comprehensive bootstrap system** with automatic file management
- **Improved error handling** and comprehensive logging
- **Unified architecture** eliminating code duplication

## 📊 **Easy Mode Analysis (Recommended)**

The bootstrap creates an easy-to-use analysis runner:

```bash
# Analyze a drug for full year
./run_analysis.sh drug metformin 2021

# Analyze multiple drugs
./run_analysis.sh drug "metformin insulin" 2021

# Analyze a condition
./run_analysis.sh condition depression 2021

# Use custom drug list
./run_analysis.sh custom code/sample_list_antidepressants.json 2021

# Analyze specific months
./run_analysis.sh drug metformin 2021-01:06  # Jan-Jun 2021
```

## 📋 **Advanced Usage**

### 1. **Drug Prevalence Analysis**

Calculate prescription prevalence for specific drug names.

```bash
cd code
python unified_prevalence.py drug \
  -d metformin ibuprofen aspirin \
  -s 202001 -e 202012
```

**Options:**
- `-d, --drugs` - List of drug names (space-separated)
- `-s, --start` - Start date (YYYYMM format)
- `-e, --end` - End date (YYYYMM format)  
- `-y, --year` - Year for LSOA mapping (optional, auto-detected)
- `-odir, --output_dir` - Custom output directory (optional)

### 2. **Custom List Analysis**

Using predefined JSON files containing drug names and BNF codes:

```bash
python unified_prevalence.py custom \
  -l sample_list_antidepressants.json \
  -s 202001 -e 202012
```

**JSON Format:**
```json
{
  "antidepressants": ["0403010A0", "0403020A0", "0403030A0"],
  "diabetes_drugs": ["0601021M0", "0601022B0"]
}
```

### 3. **Medical Condition Analysis**

Using DrugBank disease-drug mappings:

```bash
python unified_prevalence.py condition \
  -c diabetes hypertension depression \
  -s 202001 -e 202012
```

**With custom drug lists:**
```bash
python unified_prevalence.py condition \
  -c depression anxiety \
  -s 202001 -e 202012 \
  --custom_drug_list sample_list_antidepressants.json
```

### 4. **Extended Format Support (2021+ Data)**

For newer NHS data formats with 2021 LSOA boundaries:

```bash
python run_extended.py drug \
  -d metformin \
  -s 202110 -e 202110 \
  -y 2021
```

**Available commands:**
- `drug` - Drug prevalence with 2021+ mappings
- `list` - Custom list analysis with new format
- `condition` - Condition analysis with updated boundaries
- `opioid` - Specialized opioid OME calculations

## 🗂️ **Large File Management (Git LFS)**

This repository uses Git LFS to manage 47 large mapping files:

**Large Files Tracked (>25MB):**
- `GP_LSOA_weights_2013.csv` (35MB)
- `GP_LSOA_PATIENTSDIST_2021.json` (29MB)
- `GP_LSOA_PATIENTSDIST.json` (26MB)

**All Mapping Files (21 total):**
- Drug association graphs, GP registries, LSOA mappings, chemical master maps

**Setting up LFS:**
```bash
# Install Git LFS (if not installed)
brew install git-lfs          # macOS
sudo apt-get install git-lfs  # Ubuntu

# Initialize and pull files
git lfs install
git lfs pull
```

The bootstrap script handles this automatically and provides guidance if LFS is missing.

## 📁 **Output Structure**

Results are saved as compressed CSV files:
```
data_prep/
├── <condition_name>_V4.csv.gz    # Main results
├── Drugs.csv                     # Drug mapping details
└── <custom_name>_V4.csv.gz      # Custom analysis results
```

**Output Format:**
- `YYYYMM` - Year and month
- `LSOA_CODE` - LSOA geographic code  
- `Total_quantity` - Total medication quantity
- `Dosage_ratio` - Normalized dosage measurement
- `Total_cost` - Total medication cost
- `Total_items` - Number of prescription items
- `Patient_count` - Patient population in LSOA

## 📊 **Post-Processing**

Use Jupyter notebooks for analysis:

1. **`extract_yearly_prevalence.ipynb`** - Aggregate monthly to yearly data
2. **`outcomes-master.ipynb`** - Create outcome datasets for research

```bash
# After running prevalence analysis
jupyter notebook extract_yearly_prevalence.ipynb
```

## ⚙️ **Configuration & Data Ranges**

### Configuration File (`config.json`)
```json
{
  "mappings_dir": "./mappings/",
  "output_dir": "../data_prep/",
  "input_dir": "./prescriptionfiles/", 
  "sources_file": "./sources/serialized_file_paths.json",
  "logging_level": "INFO",
  "default_year": 2021
}
```

### Supported Date Ranges
- **Historical data (old format)**: 201401 to 202102
- **Current data (new format)**: 202101 to 202112
- **Overlap period**: 202101-202102 (both formats available)

### LSOA Boundaries
- **2011 boundaries**: Used for 2014-2020 data
- **2021 boundaries**: Used for 2021+ data with automatic detection
- **Multi-year support**: Automatic LSOA mapping year detection

## 🧪 **Testing & Validation**

```bash
# Run verification script
./verify_setup.sh

# Run unit tests
cd code
python -m unittest discover tests -v

# Test download system
python -c "
from sources.downloader import Downloader
downloader = Downloader()
print(f'Available sources: {len(downloader.sources)}')
"
```

## 🔧 **Troubleshooting**

### Missing Files After Bootstrap
```bash
# Download essential files manually
./download_files.sh

# Or generate sample data for testing
python code/claude_experiments/download_essential_files.py --sample
```

### Git LFS Issues
```bash
# Check LFS status
git lfs ls-files | wc -l  # Should show 47 files

# Reinstall LFS if needed
git lfs install
git lfs pull
```

### Common Issues
- **Module Import Errors**: Ensure you're in `code/` directory with environment activated
- **Date Range Errors**: Use YYYYMM format, check dates are in 201401-202112 range
- **Missing Dependencies**: Run `pip install -r requirements.txt`

## 🎯 **Example Workflows**

### Complete Diabetes Analysis
```bash
# 1. One-command analysis
./run_analysis.sh condition diabetes 2020

# 2. Or advanced usage
python unified_prevalence.py condition -c diabetes -s 202001 -e 202012 --verbose

# 3. Post-process
jupyter notebook extract_yearly_prevalence.ipynb
```

### Multi-Drug Research Study
```bash
# 1. Create custom drug list (my_drugs.json)
# 2. Run analysis
./run_analysis.sh custom my_drugs.json 2021

# 3. Analyze results  
python -c "
import pandas as pd
df = pd.read_csv('data_prep/my_category_V4.csv.gz')
print(df.groupby('YYYYMM')['Total_quantity'].sum())
"
```

### Extended Format Analysis (2021+ Data)
```bash
# Process new data files first
python process_new_data.py \
  --gp-registry data_prep/gp-reg-pat-prac-lsoa-all_2021.csv \
  --years 2021 \
  --lsoa-mapping data_prep/LSOA_DEC_2021.csv \
  --epd-file data_prep/EPD_202110.ZIP

# Run analysis with 2021 boundaries
python run_extended.py drug -d metformin -s 202110 -e 202110 -y 2021
```

## 📚 **Legacy Compatibility**

Original scripts remain available:
- `drug_prevalence.py`
- `custom_list_prevalence.py`  
- `condition_prevalence.py`

However, the unified interface is recommended for better error handling and automatic format detection.

## 📖 **Additional Resources**

- **Detailed Implementation**: `COMPREHENSIVE_TESTING_REPORT.md`
- **Architecture Details**: `code/unified/unified_processor.py`
- **Research Paper**: `NeurIPS-2023-medsat-a-public-health-dataset-for-england.pdf`
- **Manual Processing**: `MANUAL_PROCESSING_GUIDE.md`
- **Bootstrap Details**: `GETTING_STARTED.md`

## 💡 **Quick Help**

```bash
# General help
./run_analysis.sh --help
python unified_prevalence.py --help

# Command-specific help
python unified_prevalence.py drug --help
python unified_prevalence.py condition --help

# Check setup
./verify_setup.sh
```

## 🤝 **Contributing**

1. Use the virtual environment: `source activate_env.sh`
2. Run tests before submitting: `./verify_setup.sh`
3. Follow unified architecture patterns
4. Update documentation for new features
5. Ensure Git LFS files are properly tracked

## 📄 **License & Citation**

This code is part of the MedSat research project. If you use this code in your research, please cite the MedSat paper.

---

**🎉 Ready to use? Run `./bootstrap.sh` and start analyzing!**