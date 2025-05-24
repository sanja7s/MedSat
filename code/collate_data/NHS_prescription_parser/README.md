# NHS Prescription Parser

**A unified system for computing drug and condition prevalences at the LSOA level in England from NHS prescription data.**

This module is part of the MedSat research project, integrating medical prescription data with satellite imagery for public health research. The system now supports both historical and current NHS data formats with automatic detection and processing.

## 🆕 **What's New in the Unified Version**

- **Single command interface** for all prescription analysis types
- **Automatic format detection** for old (2014-2021) and new (2021+) data formats
- **Extended date range support** from 201401 to 202112
- **Multi-year LSOA mapping** with automatic year detection
- **Improved error handling** and comprehensive logging
- **Unified architecture** eliminating code duplication

## 📋 **Quick Start**

### 1. Environment Setup

```bash
# Clone/navigate to the repository
cd NHS_prescription_parser

# Set Python version (if using asdf)
echo "python 3.8.12" > .tool-versions

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install pandas jupyter "networkx==2.8.4" tqdm requests pytest
```

### 2. Quick Test

```bash
cd code
python unified_prevalence.py --help
```

You should see the unified interface help message.

## 🚀 **Usage Guide**

The new unified system provides a single entry point for all prescription analysis:

```bash
python unified_prevalence.py <command> [options]
```

### **Available Commands:**
- `drug` - Calculate prevalence for specific drugs
- `custom` - Calculate prevalence from custom drug lists
- `condition` - Calculate prevalence for medical conditions

---

## 📊 **1. Drug Prevalence Analysis**

Calculate prescription prevalence for specific drug names.

### Basic Usage
```bash
python unified_prevalence.py drug \
  -d <drug_names> \
  -s <start_date> \
  -e <end_date>
```

### Examples

**Single drug:**
```bash
python unified_prevalence.py drug \
  -d metformin \
  -s 202001 -e 202012
```

**Multiple drugs:**
```bash
python unified_prevalence.py drug \
  -d metformin ibuprofen aspirin \
  -s 202001 -e 202012
```

**With specific LSOA year:**
```bash
python unified_prevalence.py drug \
  -d metformin \
  -s 202101 -e 202103 \
  -y 2021
```

**Custom output directory:**
```bash
python unified_prevalence.py drug \
  -d metformin \
  -s 202001 -e 202012 \
  -odir /path/to/custom/output
```

### Options
- `-d, --drugs` - List of drug names (space-separated)
- `-s, --start` - Start date (YYYYMM format)
- `-e, --end` - End date (YYYYMM format)
- `-y, --year` - Year for LSOA mapping (optional, auto-detected)
- `-odir, --output_dir` - Custom output directory (optional)

---

## 📝 **2. Custom List Analysis**

Calculate prevalence using predefined JSON files containing drug names and BNF codes.

### Basic Usage
```bash
python unified_prevalence.py custom \
  -l <json_file> \
  -s <start_date> \
  -e <end_date>
```

### Examples

**Using sample antidepressants list:**
```bash
python unified_prevalence.py custom \
  -l sample_list_antidepressants.json \
  -s 202001 -e 202012
```

**Using custom anxiety list:**
```bash
python unified_prevalence.py custom \
  -l sample_list_anxiety.json \
  -s 202101 -e 202103 \
  -y 2021
```

### JSON File Format
Your JSON file should contain drug names mapped to BNF codes:
```json
{
  "drug_category_name": ["BNF_CODE1", "BNF_CODE2", "BNF_CODE3"],
  "antidepressants": ["0403010A0", "0403020A0", "0403030A0"]
}
```

### Options
- `-l, --list` - Path to JSON file with drug mappings
- `-s, --start` - Start date (YYYYMM format)
- `-e, --end` - End date (YYYYMM format)
- `-y, --year` - Year for LSOA mapping (optional)

---

## 🏥 **3. Medical Condition Analysis**

Calculate prevalence for medical conditions using DrugBank disease-drug mappings.

### Basic Usage
```bash
python unified_prevalence.py condition \
  -c <conditions> \
  -s <start_date> \
  -e <end_date>
```

### Examples

**Single condition:**
```bash
python unified_prevalence.py condition \
  -c diabetes \
  -s 202001 -e 202012
```

**Multiple conditions:**
```bash
python unified_prevalence.py condition \
  -c diabetes hypertension depression \
  -s 202001 -e 202012
```

**Using custom drug lists for conditions:**
```bash
python unified_prevalence.py condition \
  -c depression anxiety \
  -s 202001 -e 202012 \
  --custom_drug_list sample_list_antidepressants.json sample_list_anxiety.json
```

**Treating inputs as drug categories:**
```bash
python unified_prevalence.py condition \
  -c "cardiovascular drugs" "respiratory drugs" \
  -s 202001 -e 202012 \
  --is_category
```

### Options
- `-c, --conditions` - List of medical conditions (space-separated)
- `-s, --start` - Start date (YYYYMM format)
- `-e, --end` - End date (YYYYMM format)
- `--custom_drug_list` - Paths to custom drug list files (optional)
- `--is_category` - Treat conditions as drug categories instead of diseases
- `-y, --year` - Year for LSOA mapping (optional)

---

## ⚙️ **Advanced Configuration**

### Global Options
All commands support these global options:

```bash
python unified_prevalence.py <command> [options] \
  --config config.json \     # Custom configuration file
  --verbose \                # Enable detailed logging
  -odir /custom/output       # Custom output directory
```

### Configuration File
Create a `config.json` file for custom settings:

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

---

## 📁 **Output Files**

### File Structure
Results are saved as compressed CSV files:
```
data_prep/
├── <condition_name>_V4.csv.gz
├── Drugs.csv                    # Drug mapping details
└── <custom_name>_V4.csv.gz
```

### Output Format
Each result file contains:
- `YYYYMM` - Year and month
- `LSOA_CODE` - LSOA geographic code
- `Total_quantity` - Total medication quantity
- `Dosage_ratio` - Normalized dosage measurement
- `Total_cost` - Total medication cost
- `Total_items` - Number of prescription items
- `Patient_count` - Patient population in LSOA

### Per Capita Calculations
Use the Jupyter notebooks for post-processing:
1. `extract_yearly_prevalence.ipynb` - Aggregate monthly to yearly data
2. `outcomes-master.ipynb` - Create outcome datasets

---

## 🧪 **Testing & Validation**

### Run Unit Tests
```bash
cd code
source ../venv/bin/activate
python -m unittest discover tests -v
```

### Run System Analysis
```bash
cd code/analysis
python system_analysis.py
python basic_analysis.py
```

### Test Download System
```bash
cd code
python -c "
from sources.downloader import Downloader
downloader = Downloader()
print(f'Available sources: {len(downloader.sources)}')
print('System ready!')
"
```

---

## 🔧 **Troubleshooting**

### Common Issues

**1. Module Import Errors**
```bash
# Ensure you're in the code directory
cd code
source ../venv/bin/activate
```

**2. Missing Dependencies**
```bash
pip install pandas jupyter "networkx==2.8.4" tqdm requests
```

**3. Date Range Errors**
- Check date format is YYYYMM
- Ensure dates are within 201401-202112 range
- Verify start date is before end date

**4. Missing Mapping Files**
```bash
# Check required files exist
ls mappings/
# Should contain: drug_association_graph.gexf, category_association_graph.gexf, CHEM_MASTER_MAP.csv
```

**5. Download Failures**
- Check internet connection
- Verify Dropbox links are accessible
- Use `--verbose` flag for detailed error messages

### Getting Help
```bash
# General help
python unified_prevalence.py --help

# Command-specific help
python unified_prevalence.py drug --help
python unified_prevalence.py custom --help
python unified_prevalence.py condition --help
```

---

## 📚 **Legacy Compatibility**

The original scripts are still available:
- `drug_prevalence.py`
- `custom_list_prevalence.py`
- `condition_prevalence.py`

However, we recommend using the new unified interface for:
- Better error handling
- Automatic format detection
- Consistent behavior
- Enhanced logging

---

## 🎯 **Example Workflows**

### Complete Diabetes Analysis
```bash
# 1. Calculate diabetes prevalence for 2020
python unified_prevalence.py condition \
  -c diabetes \
  -s 202001 -e 202012 \
  -y 2020 \
  --verbose

# 2. Post-process with Jupyter notebooks
jupyter notebook extract_yearly_prevalence.ipynb
```

### Multi-Drug Comparison
```bash
# Compare multiple cardiovascular drugs
python unified_prevalence.py drug \
  -d "metoprolol" "atenolol" "bisoprolol" \
  -s 202001 -e 202012 \
  -odir cardiovascular_analysis
```

### Custom Research Study
```bash
# 1. Create custom drug list (my_drugs.json)
# 2. Run analysis
python unified_prevalence.py custom \
  -l my_drugs.json \
  -s 202101 -e 202103 \
  -y 2021

# 3. Analyze results
python -c "
import pandas as pd
df = pd.read_csv('../data_prep/my_category_V4.csv.gz')
print(df.groupby('YYYYMM')['Total_quantity'].sum())
"
```

---

## 📖 **Additional Resources**

- **Detailed Implementation**: See `COMPREHENSIVE_TESTING_REPORT.md`
- **Architecture Details**: See `code/unified/unified_processor.py`
- **Research Paper**: `NeurIPS-2023-medsat-a-public-health-dataset-for-england.pdf`
- **Manual Processing**: See `code/MANUAL_PROCESSING_GUIDE.md`

---

## 🤝 **Contributing**

When contributing to this project:
1. Use the virtual environment
2. Run tests before submitting
3. Follow the unified architecture patterns
4. Update documentation for new features

---

## 📄 **License & Citation**

This code is part of the MedSat research project. If you use this code in your research, please cite the MedSat paper.

---

*For technical support or questions about the unified system, please refer to the comprehensive testing report or create an issue.*