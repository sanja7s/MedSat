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
cd code && source activate_env.sh

# Verify everything works
./verify_setup.sh

# Start analyzing
./run_analysis.sh drug metformin 2021

# Or for multi-year precise control
./run_analysis.sh condition asthma 201801:202409
```

## 🆕 **What's New in the Unified Version**

- **Single command interface** for all prescription analysis types
- **🚀 Parallel processing support** with 4-8x performance improvements
- **Automatic format detection** for old (2014-2021) and new (2021+) data formats
- **Extended date range support** from 201401 to 202503
- **Multi-year LSOA mapping** with automatic year detection
- **Configurable CPU cores** via `--cores` flag
- **Built-in benchmarking** with `--benchmark` flag
- **Git LFS integration** for 47 mapping files (35MB-29MB large files)
- **Comprehensive bootstrap system** with automatic file management
- **Improved error handling** and comprehensive logging
- **Unified architecture** eliminating code duplication

## 📊 **Easy Mode Analysis (Recommended)**

The bootstrap creates an easy-to-use analysis runner with **parallel processing support**:

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

# Multi-year analysis
./run_analysis.sh drug metformin 2018:2021  # 2018-2021, all months

# Precise month control (exact start/end)
./run_analysis.sh condition asthma 201801:202409  # Jan 2018 - Sep 2024

# Parallel processing (NEW - 5-10x faster for multi-year)
./run_analysis.sh condition asthma 201801:202409 --cores 8  # Use 8 CPU cores
```

## 📋 **Advanced Usage**

### 1. **Drug Prevalence Analysis**

Calculate prescription prevalence for specific drug names.

```bash
cd code
python drug_prevalence.py -d metformin ibuprofen aspirin -s 202001 -e 202012
```

**Options:**
- `-d, --drugs` - List of drug names (space-separated)
- `-s, --start` - Start date (YYYYMM format)
- `-e, --end` - End date (YYYYMM format)  
- `-odir, --output_dir` - Custom output directory (optional)

### 2. **Custom List Analysis**

Using predefined JSON files containing drug names and BNF codes:

```bash
python custom_list_prevalence.py -l sample_list_antidepressants.json -s 202001 -e 202012
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
python condition_prevalence.py -c depression anxiety -s 202001 -e 202012
```

**With custom drug lists:**
```bash
python condition_prevalence.py -c depression anxiety -s 202001 -e 202012 --custom_drug_list_file_names sample_list_antidepressants.json
```

## 🗂️ **Large File Management (Git LFS)**

This repository uses Git LFS to manage 47 large mapping files:

### **Large Files Tracked (>25MB):**
- `GP_LSOA_weights_2013.csv` (35MB)
- `GP_LSOA_PATIENTSDIST_2021.json` (29MB)
- `GP_LSOA_PATIENTSDIST.json` (26MB)

### **All Mapping Files (21 total):**
- Drug association graphs, GP registries, LSOA mappings, chemical master maps

### **Setting up LFS:**
```bash
# Install Git LFS (if not installed)
brew install git-lfs          # macOS
sudo apt-get install git-lfs  # Ubuntu

# Initialize and pull files
git lfs install
git lfs pull
```

### **If LFS Files Are Missing:**

Check if files are LFS pointers vs actual data:
```bash
# This should show CSV headers, NOT "version https://git-lfs.github.com/spec/v1"
head -3 code/mappings/CHEM_MASTER_MAP.csv

# Check file sizes - should be MB, not just a few KB
ls -lh code/mappings/ | head -5
```

**Solution 1: Use Dedicated LFS Downloader (Recommended)**
```bash
./download_lfs_files.sh
```

**Solution 2: Manual LFS Commands**
```bash
git lfs install
git lfs fetch --all
git lfs pull
git lfs checkout
```

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
- **Current data (new format)**: 202101 to 202503
- **Overlap period**: 202101-202102 (both formats available)

### LSOA Boundaries
- **2011 boundaries**: Used for 2014-2020 data
- **2021 boundaries**: Used for 2021+ data with automatic detection
- **Multi-year support**: Automatic LSOA mapping year detection

## 🚀 **Parallel Processing (NEW)**

Dramatically speed up multi-year analyses with parallel processing:

```bash
# Automatic parallelization (uses all CPU cores)
./run_analysis.sh condition asthma 201801:202409

# Manual core specification
./run_analysis.sh condition asthma 201801:202409 --cores 8

# Check system resources
./run_analysis.sh --info

# Force serial processing (disable parallelization)  
./run_analysis.sh condition asthma 201801:202409 --serial

# Performance benchmark
./run_analysis.sh condition asthma 201801:202003 --benchmark
```

### **Performance Improvements:**
- **Single month**: No improvement (same ~30-60 seconds)
- **3+ months**: 2-4x faster 
- **Multi-year**: 4-8x faster (e.g., 30 minutes → 6 minutes)

### **System Requirements:**
- **CPU cores**: More cores = better performance (auto-detected)
- **RAM**: ~3GB per core (automatically managed)
- **Optimal**: 8-12 cores for best performance

## 🧪 **Testing & Validation**

```bash
# Run verification script
./verify_setup.sh

# Run unit tests (recommended)
cd code
./run_tests.sh

# Alternative: Run tests manually
cd code
source ../venv/bin/activate
python -m unittest discover tests -v

# Test download system
python -c "
from sources.downloader import Downloader
downloader = Downloader(sourcesFile='sources/serialized_file_paths.json')
print(f'Available sources: {len(downloader.sources)}')
"
```

## 🔧 **System Requirements**

- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows (with bash)
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space
- **Internet**: Required for initial setup and data downloads

## 📚 **Core Dependencies**

- `pandas` - Data processing
- `numpy` - Numerical operations  
- `tqdm` - Progress bars
- `networkx` - Drug relationship graphs
- `requests` - Data downloading
- `matplotlib` - Plotting
- `seaborn` - Statistical visualizations
- `scipy` - Statistical tests

## 🔧 **Troubleshooting**

### Common Issues

**1. Missing Files After Bootstrap**
```bash
# Download essential files manually
./download_lfs_files.sh

# Or generate sample data for testing
python code/claude_experiments/download_essential_files.py --sample
```

**2. Git LFS Issues**
```bash
# Check LFS status
git lfs ls-files | wc -l  # Should show 47 files

# Reinstall LFS if needed
git lfs install
git lfs pull
```

**3. Python/Environment Issues**
```bash
# Check version
python3 --version

# Remove and recreate environment
rm -rf venv
./bootstrap.sh
```

**4. Permission denied on scripts**
```bash
chmod +x bootstrap.sh activate_env.sh run_analysis.sh verify_setup.sh
```

### Getting Help

**Script-specific help:**
```bash
./run_analysis.sh --help
python code/drug_prevalence.py --help
```

**File availability check:**
```bash
source activate_env.sh
python code/claude_experiments/handle_missing_files.py
```

**Full system verification:**
```bash
./verify_setup.sh
```

## 🎯 **Example Workflows**

### Complete Diabetes Analysis
```bash
# 1. One-command analysis
./run_analysis.sh condition diabetes 2020

# 2. Or advanced usage
python code/condition_prevalence.py -c diabetes -s 202001 -e 202012

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

### Testing Your Setup
```bash
# 1. Verify environment
./verify_setup.sh

# 2. Test analysis (small dataset)
./run_analysis.sh drug metformin 2019-01

# 3. Check output
ls data_prep/metformin_V4.csv.gz
```

## 📝 **Success Indicators**

You'll know the setup worked when:
- ✅ `./verify_setup.sh` passes all checks
- ✅ `./run_analysis.sh drug metformin 2021` completes successfully  
- ✅ Files appear in `data_prep/` directory
- ✅ No error messages during bootstrap
- ✅ Mapping files show actual data (CSV headers, JSON content)
- ✅ Large files show correct sizes (35MB, 29MB, etc.)

## 🔒 **Data Security & Privacy**

- **No patient-level data**: All analysis uses aggregate statistics
- **LSOA-level only**: Geographic data at population level (1,500 people avg)
- **NHS compliance**: Follows NHS Digital data usage guidelines
- **Local processing**: All computation happens on your machine

## 🔧 **Extended Features (2021+ Data)**

For newer NHS data formats with 2021 LSOA boundaries, use the extended interface:

```bash
cd code
# Drug analysis with extended features
python run_extended.py drug -d metformin -s 202110 -e 202110 -y 2021

# Condition analysis with extended features  
python run_extended.py condition -c asthma -s 201801 -e 202409 -y 2021

# Custom list with extended features
python run_extended.py list -l sample_list_antidepressants.json -s 202101 -e 202112 -y 2021

# Opioid analysis with OME calculations
python run_extended.py opioid -d tramadol -s 202101 -e 202112 -y 2021
```

**Available extended commands:**
- `drug` - Drug prevalence with 2021+ mappings
- `list` - Custom list analysis with new format
- `condition` - Condition analysis with updated boundaries
- `opioid` - Specialized opioid OME calculations

**Note**: `run_extended.py` is recommended for:
- Data spanning 2021+ (newer NHS format)
- Multi-year analysis requiring 2021 LSOA boundaries
- Specialized opioid OME calculations

## 📊 **Testing & Validation Framework**

The system includes comprehensive testing for data quality assurance:

### Statistical Validation
```bash
cd code/claude_experiments
python statistical_validation_analysis.py
```

**Provides:**
- Correlation tests (Pearson and Spearman)
- Normality assessment (Shapiro-Wilk, Q-Q plots)
- Effect size calculations (Cohen's d)
- Multiple testing corrections

### Unit Tests
```bash
cd code
./run_tests.sh
```

**Alternative manual testing:**
```bash
cd code
source ../venv/bin/activate
python -m unittest discover tests -v
```

**Test Coverage:**
- ✅ Download system (both .gz and .ZIP formats)
- ✅ Format detection (old/new data formats)
- ✅ Data processing pipeline
- ✅ LSOA mapping (multi-year support)
- ✅ Integration tests (end-to-end workflows)

## 🎯 **Research Applications**

### London Prescription Analysis
```bash
cd code/claude_experiments
python london_correlation_analysis.py
```

**Generates:**
- Correlation analysis between time periods
- Geographic trend visualizations
- Statistical significance testing
- COVID-19 impact assessment

### System Analysis
```bash
cd code/analysis
python system_analysis.py
```

**Provides:**
- Code quality assessment
- Performance optimization recommendations
- Architecture analysis

## 📚 **Documentation Structure**

### Core Files
- `README.md` (this file) - Complete system documentation
- `CLAUDE.md` - Claude Code integration instructions
- `config.json` - System configuration

### Legacy Files (Still Valid)
- Original analysis scripts: `drug_prevalence.py`, `custom_list_prevalence.py`, `condition_prevalence.py`
- Processing guides: Manual processing instructions available if needed
- Testing reports: Comprehensive improvement documentation

## 🏗️ **Architecture Overview**

### Unified System (`code/unified/`)
- **DataFrameAdapter**: Automatic format detection and field mapping
- **LSPOAMappingManager**: Multi-year LSOA boundary support
- **MetricsCalculator**: Format-agnostic prevalence calculations
- **UnifiedProcessor**: Single entry point for all operations

### Key Benefits
- **100% backward compatibility** with existing workflows
- **Automatic format detection** eliminates manual configuration
- **Centralized configuration** reduces scattered settings
- **Comprehensive testing** ensures reliability

## 💡 **Quick Help**

```bash
# General help
./run_analysis.sh --help
python code/drug_prevalence.py --help

# Extended functionality help
python code/run_extended.py --help

# Check setup
./verify_setup.sh

# Activate environment
source activate_env.sh
```

## 🤝 **Contributing**

1. Use the virtual environment: `cd code && source activate_env.sh`
2. Run tests before submitting: `cd code && ./run_tests.sh`
3. Verify setup: `./verify_setup.sh`
4. Follow unified architecture patterns in `code/unified/`
5. Add tests for new features in `code/tests/`
6. Update documentation for new features
7. Ensure Git LFS files are properly tracked

## 📄 **License & Citation**

This code is part of the MedSat research project. If you use this code in your research, please cite the MedSat paper.

---

### **🚀 Quick Command Reference**

```bash
# Setup
./bootstrap.sh
cd code && source activate_env.sh

# Basic analysis
./run_analysis.sh drug metformin 2021

# Multi-year with exact month control
./run_analysis.sh condition depression 201801:202409

# Parallel processing (NEW - much faster for multi-year)
./run_analysis.sh condition asthma 201801:202409 --cores 8

# Check system resources
./run_analysis.sh --info

# Extended features (2021+ data)
python run_extended.py condition -c asthma -s 201801 -e 202409 -y 2021
```

**🎉 Ready to use? Run `./bootstrap.sh` and start analyzing!**