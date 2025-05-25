# NHS Prescription Parser - Complete Bootstrap Guide

## 🎯 **One-Command Setup**

```bash
git clone <your-repo-url>
cd NHS_prescription_parser
./bootstrap.sh
```

That's it! The script automatically:
- ✅ Creates isolated Python environment
- ✅ Installs all dependencies  
- ✅ Sets up directory structure
- ✅ Configures Git LFS for large files
- ✅ Creates easy-to-use wrapper scripts
- ✅ Verifies setup completeness

## 🚀 **Quick Start After Bootstrap**

```bash
# 1. Activate environment
source activate_env.sh

# 2. Verify everything works
./verify_setup.sh

# 3. Run your first analysis
./run_analysis.sh drug metformin 2021
```

## 📊 **Easy Analysis Commands**

### Drug Prevalence Analysis
```bash
# Single drug, full year
./run_analysis.sh drug metformin 2021

# Multiple drugs
./run_analysis.sh drug "metformin insulin glipizide" 2021

# Specific months (Jan-Jun 2021)
./run_analysis.sh drug metformin 2021-01:06

# Single month (January 2021)
./run_analysis.sh drug metformin 2021-01
```

### Condition-Based Analysis
```bash
# Condition analysis (finds relevant drugs automatically)
./run_analysis.sh condition depression 2021
./run_analysis.sh condition diabetes 2021
./run_analysis.sh condition asthma 2021
```

### Custom Drug Lists
```bash
# Use predefined drug lists
./run_analysis.sh custom code/sample_list_antidepressants.json 2021
./run_analysis.sh custom code/sample_list_anxiety.json 2021
./run_analysis.sh custom code/sample_list_painkiller.json 2021
```

### Advanced Options
```bash
# Custom output directory
./run_analysis.sh drug metformin 2021 --output /path/to/output

# Get help for any command
./run_analysis.sh --help
python code/drug_prevalence.py --help
python code/condition_prevalence.py --help
```

## 📁 **Output Structure**

All results go to `data_prep/`:
```
data_prep/
├── metformin_V4.csv.gz          # Monthly prescription data
├── depression_V4.csv.gz         # Condition-based results
└── antidepressants_V4.csv.gz    # Custom list results
```

### Output File Format
Each CSV contains:
- `YYYYMM` - Year and month
- `LSOA_CODE` - Geographic area code
- `Total_quantity` - Total medication quantity
- `Total_cost` - Total medication cost
- `Total_items` - Number of prescription items
- `Dosage_ratio` - Normalized dosage
- `Patient_count` - Population denominator

## 🔧 **System Requirements**

- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows (with bash)
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space
- **Internet**: Required for initial setup and data downloads

## 📚 **What Gets Installed**

### Core Dependencies
- `pandas` - Data processing
- `numpy` - Numerical operations  
- `tqdm` - Progress bars
- `networkx` - Drug relationship graphs
- `requests` - Data downloading

### Analysis Dependencies  
- `matplotlib` - Plotting
- `seaborn` - Statistical visualizations
- `scipy` - Statistical tests
- `openpyxl` - Excel file support

### Optional Components
- `jupyter` - For interactive notebooks
- `pytest` - For running tests

## 🗂 **Directory Structure After Bootstrap**

```
NHS_prescription_parser/
├── bootstrap.sh                 # 🔧 Setup script
├── activate_env.sh             # 🟢 Environment activation
├── run_analysis.sh             # 🚀 Easy analysis runner
├── verify_setup.sh             # ✅ Setup verification
├── requirements.txt            # 📦 Dependencies
├── GETTING_STARTED.md          # 📖 Quick guide
├── venv/                       # 🐍 Python environment
├── code/                       # 💻 Source code
│   ├── drug_prevalence.py      # Drug analysis
│   ├── condition_prevalence.py # Condition analysis
│   ├── custom_list_prevalence.py # Custom list analysis
│   ├── mappings/               # Data mappings
│   ├── sources/                # Data downloaders
│   └── claude_experiments/     # Advanced analysis tools
├── data_prep/                  # 📊 Output directory
└── prescriptionfiles/          # 💾 Downloaded data cache
```

## 🔍 **Troubleshooting**

### Common Issues

**1. Python version too old**
```bash
# Check version
python3 --version

# Upgrade Python (macOS)
brew install python@3.9

# Upgrade Python (Ubuntu)
sudo apt update && sudo apt install python3.9
```

**2. Virtual environment issues**
```bash
# Remove and recreate
rm -rf venv
./bootstrap.sh
```

**3. Missing large files**
```bash
# Check file status
python code/claude_experiments/handle_missing_files.py

# Set up Git LFS
brew install git-lfs  # macOS
git lfs install
git lfs pull
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

## 🧪 **Testing Your Setup**

### Quick Tests
```bash
# 1. Verify environment
./verify_setup.sh

# 2. Test analysis (small dataset)
./run_analysis.sh drug metformin 2019-01

# 3. Check output
ls data_prep/metformin_V4.csv.gz
```

### Advanced Testing
```bash
source activate_env.sh
cd code

# Run unit tests
python -m pytest tests/ -v

# Test data download
python sources/test_downloader_config.py

# Test drug matching
python -c "from matching.drugMatching import DrugMatcher; print('✅ DrugMatcher works')"
```

## 📈 **Next Steps**

### 1. Extract Yearly Data
After generating monthly data, extract yearly prevalence:
```bash
# Use Jupyter notebook for yearly aggregation
jupyter notebook extract_yearly_prevalence.ipynb
```

### 2. Advanced Analysis
Explore statistical tools:
```bash
cd code/claude_experiments
python statistical_validation_analysis.py
python updated_mapping_integration.py
```

### 3. Custom Drug Lists
Create your own drug lists in JSON format:
```json
{
    "drug_name": ["BNF_CODE1", "BNF_CODE2"],
    "metformin": ["0406020A0"],
    "insulin": ["0601010D0", "0601010E0"]
}
```

## 🔒 **Data Security & Privacy**

- **No patient-level data**: All analysis uses aggregate statistics
- **LSOA-level only**: Geographic data at population level (1,500 people avg)
- **NHS compliance**: Follows NHS Digital data usage guidelines
- **Local processing**: All computation happens on your machine

## 📞 **Support & Contributing**

- **Issues**: Check existing documentation first
- **Missing files**: Use the provided detection and download tools
- **New features**: Follow existing code patterns
- **Statistical validation**: All tools include proper testing

## 🎉 **Success Indicators**

You'll know the setup worked when:
- ✅ `./verify_setup.sh` passes all checks
- ✅ `./run_analysis.sh drug metformin 2021` completes successfully  
- ✅ Files appear in `data_prep/` directory
- ✅ No error messages during bootstrap

**Ready to analyze NHS prescription data!** 🏥📊