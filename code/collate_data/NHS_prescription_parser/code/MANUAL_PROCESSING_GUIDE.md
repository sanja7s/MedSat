# Manual Processing Guide for NHS Prescription Data

This guide provides step-by-step instructions for processing the new NHS prescription data without relying on automatic execution.

## Prerequisites

1. Ensure you have the following files in the `data_prep` directory:
   - `EPD_202110.ZIP` - The new NHS prescription data
   - `gp-reg-pat-prac-lsoa-all_2021.csv` (and other years if available) - GP registry data
   - `LSOA_DEC_2021.csv` - LSOA mapping file
   - `census2021_lsoa_level.xlsx` - Census data at LSOA level

2. Make sure you have the correct Python environment with required dependencies:
   - pandas
   - networkx
   - tqdm

## Step 1: Manual Processing of GP Registry Data

If you're having trouble running the `process_new_data.py` script, you can perform the steps manually:

1. **Create the mappings directory if it doesn't exist**:
   ```
   mkdir -p ./mappings
   ```

2. **Process the GP registry file**:
   - Open the `gp-reg-pat-prac-lsoa-all_2021.csv` file
   - Filter for records with SEX = 'ALL'
   - Group by PRACTICE_CODE
   - For each practice, create a mapping from LSOA_CODE to patient count
   - Save the resulting mapping to `./mappings/GPs_2021.json`

3. **Create LSOA patient distribution**:
   - For each LSOA, sum the patient counts across all practices
   - Save the resulting mapping to `./mappings/GP_LSOA_PATIENTSDIST_2021.json`

## Step 2: Manual Processing of EPD File

1. **Create prescriptionfiles directory if it doesn't exist**:
   ```
   mkdir -p ./prescriptionfiles
   ```

2. **Extract and process the EPD file**:
   - Extract the ZIP file to a temporary location
   - Create a new gzipped CSV file with the format `202110.gz` in the `./prescriptionfiles` directory
   - Ensure the columns match what the code expects (or update `commonFunc_updated.py` to handle the new format)

3. **Update sources file**:
   - Open `./sources/serialized_file_paths.json`
   - Add a new entry for the processed file:
     ```json
     "202110.gz": "file:///absolute/path/to/prescriptionfiles/202110.gz"
     ```

## Step 3: Calculate Diabetes Prevalence

Once the data is prepared, you can calculate diabetes prevalence using the extended scripts.

### Using run_extended.py

With a working Python environment, run:

```
python run_extended.py condition -c diabetes -s 202110 -e 202110 -y 2021
```

### Manual Alternative

If you're still having issues with Python execution:

1. **Match diabetes condition to drugs**:
   - Use the drug association graph in `./mappings/drug_association_graph.gexf` to find drugs related to diabetes
   - Create a mapping from drug names to BNF codes

2. **Process prescription data**:
   - Read the prescription data file for 202110
   - Filter for prescriptions with BNF codes matching diabetes drugs
   - Calculate metrics (quantity, cost, dosage, items) per LSOA

3. **Write results**:
   - Normalize metrics by patient population from `GP_LSOA_PATIENTSDIST_2021.json`
   - Save results to `../data_prep/diabetes_V4.csv.gz`

## Post-Processing

After generating the prevalence data, you would typically use the Jupyter notebooks:

1. `extract_yearly_prevalence.ipynb` - Aggregates monthly data into yearly statistics
2. `outcomes-master.ipynb` - Combines prevalence data for multiple conditions

If you're having issues running these notebooks, you can perform the aggregation manually:

1. Read the monthly data from `diabetes_V4.csv.gz`
2. Group by year and LSOA_CODE
3. Calculate sum of metrics and normalize by patient count
4. Save results to yearly files

## Troubleshooting

If you encounter issues with Python environment or execution:

1. **Check Python installation**:
   ```
   which python
   python --version
   ```

2. **Check conda environment**:
   ```
   conda env list
   conda activate nhsrefactor
   ```

3. **Verify dependencies**:
   ```
   pip list | grep pandas
   pip list | grep networkx
   pip list | grep tqdm
   ```

4. **Consider Docker**:
   - If environment issues persist, consider using Docker to create an isolated environment with all dependencies
   - The Dockerfile would be based on Python 3.8 and include all required packages