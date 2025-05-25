# Extended NHS Prescription Parser

This directory contains extended scripts to support the newer NHS prescription data formats and 2021 LSOA boundaries.

## New Files

1. **lsoa_mapper_2021.py**: Processes GP registry files to create LSOA patient distribution mappings for 2021 and later.
2. **update_sources.py**: Updates the serialized_file_paths.json file to include local EPD files.
3. **process_new_data.py**: Processes new NHS data files (EPD, GP registry, LSOA mapping) and updates the necessary mappings.
4. **commonFunc_updated.py**: Extended version of commonFunc.py with support for 2021+ LSOA mappings.
5. **run_extended.py**: Command-line interface for running prevalence calculations with the new data formats.

## Usage Guide

### Step 1: Process New Data Files

Process the new data files to create the necessary mappings:

```bash
python process_new_data.py \
  --gp-registry ../data_prep/gp-reg-pat-prac-lsoa-all_2021.csv ../data_prep/gp-reg-pat-prac-lsoa-all_2022.csv \
  --years 2021 2022 \
  --lsoa-mapping ../data_prep/LSOA_DEC_2021.csv \
  --epd-file ../data_prep/EPD_202110.ZIP \
  --mappings-dir ./mappings \
  --prescriptions-dir ./prescriptionfiles \
  --sources-file ./sources/serialized_file_paths.json
```

This script will:
1. Process the GP registry files to create LSOA patient distribution mappings
2. Process the LSOA mapping file to create a mapping between 2011 and 2021 LSOA codes
3. Extract and process the EPD file to make it compatible with the existing code
4. Update the serialized_file_paths.json file to include the new EPD file

### Step 2: Run Prevalence Calculations

Use the extended runner script to calculate prevalence metrics:

#### Drug Prevalence

```bash
python run_extended.py drug \
  -d metformin \
  -s 202110 \
  -e 202110 \
  -y 2021
```

#### Custom List Prevalence

```bash
python run_extended.py list \
  -l ./sample_list_antidepressants.json \
  -s 202110 \
  -e 202110 \
  -y 2021
```

#### Condition Prevalence

```bash
python run_extended.py condition \
  -c depression \
  -s 202110 \
  -e 202110 \
  -y 2021
```

#### Opioid Prevalence

```bash
python run_extended.py opioid \
  -s 202110 \
  -e 202110 \
  -y 2021
```

### Step 3: Post-processing

The existing Jupyter notebooks (`extract_yearly_prevalence.ipynb` and `outcomes-master.ipynb`) can be used to process the output files as before.

## LSOA 2021 Boundaries

The script `lsoa_mapper_2021.py` processes the new GP registry files and census data to create LSOA patient distribution mappings for 2021 boundaries. These mappings are used by the extended functions to correctly distribute prescriptions to LSOAs based on the new boundaries.

## Command Line Arguments

### process_new_data.py

- `--gp-registry`: Paths to GP registry files (CSV)
- `--years`: Years corresponding to the GP registry files
- `--lsoa-mapping`: Path to LSOA mapping file (CSV)
- `--epd-file`: Path to EPD file (ZIP)
- `--mappings-dir`: Output directory for mapping files (default: ./mappings)
- `--prescriptions-dir`: Output directory for processed prescription files (default: ./prescriptionfiles)
- `--sources-file`: Path to serialized_file_paths.json (default: ./sources/serialized_file_paths.json)

### run_extended.py

#### Common arguments for all commands:

- `-s`, `--start`: Start year and month, format YYYYMM (required)
- `-e`, `--end`: End year and month, format YYYYMM (required)
- `-y`, `--year`: Year for LSOA mapping, e.g., 2021 (optional)
- `-odir`, `--output_dir`: Directory for output files (default: ../data_prep/)

#### Command-specific arguments:

- `drug`: `-d`, `--drugs`: List of drug names (required)
- `list`: `-l`, `--list`: JSON file with drug names and BNF codes (required)
- `condition`: 
  - `-c`, `--conditions`: List of conditions (required)
  - `-custDLFN`, `--custom_drug_list_file_names`: List of custom drug list files
  - `--isCat`: Boolean flag to indicate if the list is a set of conditions or categories (default: False)
- `opioid`: No additional arguments required

## Notes

1. The extended scripts are designed to be backward compatible with the existing codebase.
2. The scripts automatically detect the format of the prescription data and adapt accordingly.
3. When specifying a year with the `-y` option, the scripts will use the appropriate LSOA mappings for that year.
4. If multiple years of GP registry data are available, the scripts will use the most appropriate one based on the specified year.