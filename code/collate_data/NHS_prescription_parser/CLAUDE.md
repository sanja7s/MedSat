# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NHS_prescription_parser is a Python module that computes drug and condition prevalences at the LSOA (Lower Super Output Area) level in England from NHS prescription data. It is part of the MedSat research project, which integrates medical prescription data with satellite imagery for public health research in England.

The module can generate prevalence values from:
1. Drug names
2. Drug names with BNF (British National Formulary) codes 
3. Medical conditions (by finding associated drugs)
4. Opioid OME (Oral Morphine Equivalent) prevalence

### Research Context

This prescription prevalence calculation is a key component in the MedSat dataset, allowing researchers to:
- Calculate yearly drug consumption per capita at the LSOA level
- Aggregate monthly prescription data into yearly metrics
- Link medication usage to specific medical conditions
- Generate health outcome variables for various conditions including diabetes, asthma, hypertension, depression, and anxiety
- Study the relationship between geographic areas and medication patterns

## Environment Setup

```bash
# Create and activate the conda environment
conda env create -f environment.yml
conda activate nhsrefactor
```

## Command Execution

The codebase offers three main entry points for computing prevalences:

### 1. Drug Prevalence

Computes prevalence based on specific drug names:

```bash
cd code
python drug_prevalence.py -d metformin -s 201901 -e 201912
```

Parameters:
- `-d` or `--drugs`: List of drug names
- `-s` or `--start`: Start year and month (format: YYYYMM)
- `-e` or `--end`: End year and month (format: YYYYMM)
- `-odir` or `--output_dir`: Optional output directory (default: ../data_prep/)

### 2. Custom List Prevalence

Computes prevalence based on a JSON file containing drug names and their BNF codes:

```bash
cd code
python custom_list_prevalence.py -l ./sample_list_antidepressants.json -s 201901 -e 201912
```

Parameters:
- `-l` or `--list`: Path to JSON file with drug names and BNF codes
- `-s` or `--start`: Start year and month (format: YYYYMM)
- `-e` or `--end`: End year and month (format: YYYYMM)
- `-odir` or `--output_dir`: Optional output directory (default: ../data_prep/)

### 3. Condition Prevalence

Computes prevalence based on medical conditions:

```bash
cd code
# Using drugbank to find drugs:
python condition_prevalence.py -s 201901 -e 201912 -c depression

# Using a custom drug list:
python condition_prevalence.py -s 201901 -e 201912 -c depression -custDLFN sample_list_antidepressants.json
```

Parameters:
- `-c` or `--conditions`: List of conditions
- `-s` or `--start`: Start year and month (format: YYYYMM)
- `-e` or `--end`: End year and month (format: YYYYMM)
- `-custDLFN` or `--custom_drug_list_file_names`: Optional custom drug list file
- `--isCat`: Boolean flag to indicate if the list is a set of conditions or categories (default: False)
- `-odir` or `--output_dir`: Optional output directory (default: ../data_prep/)

## Post-Processing Workflow

After generating monthly prevalence data with the scripts above, you can use the Jupyter notebooks to:

1. **Extract yearly prevalence** (`extract_yearly_prevalence.ipynb`):
   - Aggregates monthly data into yearly statistics
   - Normalizes by patient population to generate per capita metrics
   - Creates yearly prevalence CSV files for each condition

2. **Generate outcome datasets** (`outcomes-master.ipynb`):
   - Combines prevalence data for multiple conditions into a unified dataset
   - Creates outcome variables for research analysis
   - Formats data for integration with other MedSat components

## Architecture

### Core Components

1. **Downloader (`sources/downloader.py`)**
   - Downloads NHS prescription data files for specified date ranges
   - Uses a cached mapping of dates to URLs in `sources/serialized_file_paths.json`
   - Maintains a local cache to avoid re-downloading existing files

2. **Drug Matcher (`matching/drugMatching.py`)**
   - Maps drug names to BNF codes using networkx graphs
   - Supports matching by disease, category, or direct drug name
   - Uses bipartite graphs to link conditions to their associated medications

3. **Common Functions (`matching/commonFunc.py`)**
   - Functions for calculating prevalence metrics at LSOA level
   - Maps prescriptions to LSOA patient populations
   - Writes result files with calculated metrics

4. **Utils (`matching/utils.py`)**
   - Helper functions for string manipulation, drug mapping, and normalization
   - Functions to query and process the bipartite drug-disease and drug-category graphs

### Data Flow

1. User specifies drug names, conditions, or a custom list along with a date range
2. System downloads relevant prescription data files if not already cached
3. Drug matcher identifies relevant BNF codes for the requested drugs/conditions
4. System processes prescription files to calculate metrics (quantity, dosage, cost, items)
5. Results are normalized by patient population and written to CSV files
6. Post-processing aggregates monthly data into yearly statistics and prepares outcome datasets

### Key Metrics Calculated

1. **Total_quantity_per_capita**: Total amount of medication dispensed per person
2. **Dosage_ratio**: Normalized dosage measurement
3. **Total_cost_per_capita**: Medication cost per person
4. **Total_items_per_capita**: Number of prescription items per person
5. **OME_per_capita**: Oral Morphine Equivalent per capita (for opioids only)

## Important Files

- **Prescription Files**: Downloaded to `./code/prescriptionfiles/`
- **Output Files**: Generated in `../data_prep/` by default
- **Mapping Files**: Located in `./code/mappings/` 
  - `drug_association_graph.gexf`: Bipartite graph connecting drugs to conditions
  - `category_association_graph.gexf`: Graph connecting drugs to categories
  - `CHEM_MASTER_MAP.csv`: Mapping of drug codes to names
  - `GP_LSOA_PATIENTSDIST*.json`: Patient distribution across LSOAs

## Date Range and Download System

### Supported Date Range
The system now supports dates from **201401 to 202112**, with automatic download capabilities for both old and new data formats:
- **201401-202102**: Original .gz format files
- **202101-202112**: New EPD .ZIP format files (with overlap for 202101-202102)

### Automatic Download System
The enhanced download system in `sources/downloader.py` automatically:
1. **Detects file format**: Handles both .gz and .ZIP files
2. **Processes ZIP files**: Extracts and converts EPD ZIP files to the expected .gz format
3. **Maintains compatibility**: All files are stored in the same .gz format for consistent processing
4. **Caches downloads**: Avoids re-downloading existing files

### Usage Example
```python
from sources.downloader import Downloader

# Initialize downloader
downloader = Downloader()

# Download range spanning both old and new formats
files = downloader.download_range("202001", "202106")
```

### File Format Handling
- **Old format (.gz)**: Used directly
- **New format (.ZIP)**: Automatically extracted and converted to .gz format
- **Output**: All files standardized to YYYYMM.gz format in `prescriptionfiles/` directory

## LSOA Geography

The prescription data is mapped to 2011 LSOA boundaries, which is important to note when integrating with other geographic datasets.