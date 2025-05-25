"""
Patched version of commonFunc_updated.py to use new CSV mapping files.

This version integrates the new gp-reg-pat-prac-lsoa-all_YYYY.csv files
while maintaining backward compatibility with existing JSON files.
"""

import json
import argparse
from tqdm import tqdm
import numpy as np
import pandas as pd
import os
import glob
import re


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    
def func_ome(df, drugBNF, ome_map, quantity_field):
    df['presc_ome'] = df[quantity_field] * df['15'] * ome_map[drugBNF]
    return df

def calculateOME(pdp, ome_map, code_field, quantity_field):
    pdp['presc_ome'] = 0.0
    print(code_field, quantity_field)
    return pdp.groupby(code_field, as_index=False).apply(lambda df: func_ome(df, df.name, ome_map, quantity_field))

def makeOMEmap(mappings_dir):
    ome = pd.read_csv(mappings_dir + 'ome_rossano.csv')
    ome_map = {}
    for index, row in ome.iterrows():
        ome_map[row['bnf']] = row['ome_multiplier']
    return ome_map

def load_gp_registry_csv(mappings_dir, year=None):
    """
    Load GP registry data from the new CSV format files.
    
    Args:
        mappings_dir: Directory containing mapping files
        year: Specific year to load (if None, finds most recent)
    
    Returns:
        DataFrame with columns: PRACTICE_CODE, LSOA_CODE, NUMBER_OF_PATIENTS
    """
    # Find available GP registry CSV files
    csv_pattern = os.path.join(mappings_dir, 'gp-reg-pat-prac-lsoa-all_*.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        return None
    
    # Extract years from filenames
    year_pattern = re.compile(r'gp-reg-pat-prac-lsoa-all_(\d{4})\.csv')
    available_years = []
    for f in csv_files:
        match = year_pattern.search(f)
        if match:
            available_years.append(int(match.group(1)))
    
    if not available_years:
        return None
    
    # Select appropriate year
    if year is None:
        target_year = max(available_years)
    else:
        if year in available_years:
            target_year = year
        else:
            target_year = min(available_years, key=lambda x: abs(x - year))
            print(f"Year {year} not available, using closest: {target_year}")
    
    # Load the CSV file
    csv_file = os.path.join(mappings_dir, f'gp-reg-pat-prac-lsoa-all_{target_year}.csv')
    
    try:
        # Read CSV with appropriate column names
        df = pd.read_csv(csv_file)
        
        # Standardize column names (handle variations)
        if 'Number of Patients' in df.columns:
            df = df.rename(columns={'Number of Patients': 'NUMBER_OF_PATIENTS'})
        elif 'NUMBER_OF_PATIENTS' not in df.columns:
            # Try to find the patient count column
            patient_cols = [col for col in df.columns if 'patient' in col.lower() or 'number' in col.lower()]
            if patient_cols:
                df = df.rename(columns={patient_cols[0]: 'NUMBER_OF_PATIENTS'})
        
        # Filter for relevant columns and clean data
        required_cols = ['PRACTICE_CODE', 'LSOA_CODE', 'NUMBER_OF_PATIENTS']
        if not all(col in df.columns for col in required_cols):
            return None
        
        df = df[required_cols].copy()
        
        # Clean and validate data
        df['NUMBER_OF_PATIENTS'] = pd.to_numeric(df['NUMBER_OF_PATIENTS'], errors='coerce')
        df = df.dropna(subset=['NUMBER_OF_PATIENTS'])
        df = df[df['NUMBER_OF_PATIENTS'] > 0]  # Remove zero/negative patient counts
        
        return df
        
    except Exception as e:
        print(f"Error loading {csv_file}: {e}")
        return None

def prepare_lsoa_GP_population(mappings_dir, year=None):
    """
    Enhanced version that uses CSV files when available, with JSON fallback.
    
    Priority order:
    1. gp-reg-pat-prac-lsoa-all_YYYY.csv (newest format)
    2. GP_LSOA_PATIENTSDIST_YYYY.json (existing format)  
    3. GPs.json (fallback)
    
    Args:
        mappings_dir: Directory containing mapping files
        year: Year of the data (if None, uses the most recent available)
    
    Returns:
        Dictionary mapping LSOA codes to patient counts
    """
    # Try CSV format first (newest and most accurate)
    gp_df = load_gp_registry_csv(mappings_dir, year)
    
    if gp_df is not None:
        # Aggregate by LSOA (sum patients across all practices in each LSOA)
        lsoa_population = gp_df.groupby('LSOA_CODE')['NUMBER_OF_PATIENTS'].sum().to_dict()
        
        # Convert to int for consistency
        lsoa_population = {lsoa: int(pop) for lsoa, pop in lsoa_population.items()}
        
        return lsoa_population
    
    # Fall back to existing JSON format
    return prepare_lsoa_GP_population_legacy(mappings_dir, year)

def prepare_lsoa_GP_population_legacy(mappings_dir, year=None):
    """
    Legacy function using JSON format files (kept for backward compatibility).
    """
    LSOA_patient_pop = {}
    
    # Determine which file to use based on year
    if year is None:
        # Find the most recent GP_LSOA_PATIENTSDIST file
        dist_files = glob.glob(os.path.join(mappings_dir, 'GP_LSOA_PATIENTSDIST_*.json'))
        if not dist_files:
            # Fall back to original files
            if os.path.exists(os.path.join(mappings_dir, 'GPs.json')):
                LSOA_patients_map = json.load(open(os.path.join(mappings_dir, 'GPs.json'), 'r'))
            else:
                LSOA_patients_map = json.load(open(os.path.join(mappings_dir, 'GPs_2013.json'), 'r'))
        else:
            # Extract years from filenames and find the most recent
            year_pattern = re.compile(r'GP_LSOA_PATIENTSDIST_(\d{4})\.json')
            years = [int(year_pattern.search(f).group(1)) for f in dist_files if year_pattern.search(f)]
            latest_year = max(years)
            latest_file = os.path.join(mappings_dir, f'GP_LSOA_PATIENTSDIST_{latest_year}.json')
            return json.load(open(latest_file, 'r'))
    else:
        # Use the specified year
        year_file = os.path.join(mappings_dir, f'GP_LSOA_PATIENTSDIST_{year}.json')
        if os.path.exists(year_file):
            return json.load(open(year_file, 'r'))
        else:
            print(f"Warning: No patient distribution file found for year {year}. Using the most recent available.")
            return prepare_lsoa_GP_population_legacy(mappings_dir)
    
    # Process the GP to LSOA mapping
    for GP in tqdm(LSOA_patients_map):
        for lsoa in LSOA_patients_map[GP]['Patient_registry_LSOA']:
            if lsoa not in LSOA_patient_pop:
                LSOA_patient_pop[lsoa] = LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
            else:
                LSOA_patient_pop[lsoa] += LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
    
    return LSOA_patient_pop


def load_lsoa_mappings(mappings_dir, year=None):
    """
    Load LSOA distribution mappings for a specific year.
    Enhanced to work with new CSV format when available.
    
    Args:
        mappings_dir: Directory containing mapping files
        year: Year of the data (if None, returns mappings for all available years)
    
    Returns:
        Dictionary mapping GP practices to LSOA distributions
    """
    # Try to use CSV format data first
    gp_df = load_gp_registry_csv(mappings_dir, year)
    
    if gp_df is not None:
        # Convert CSV format to the expected mapping format
        # Group by practice and create LSOA distribution
        practice_mappings = {}
        
        for practice, group in gp_df.groupby('PRACTICE_CODE'):
            # Calculate total patients for this practice
            total_patients = group['NUMBER_OF_PATIENTS'].sum()
            
            # Create LSOA distribution (proportion of patients in each LSOA)
            lsoa_dist = {}
            for _, row in group.iterrows():
                lsoa_code = row['LSOA_CODE']
                patients = row['NUMBER_OF_PATIENTS']
                # Store as proportion for consistency with existing format
                lsoa_dist[lsoa_code] = patients / total_patients if total_patients > 0 else 0
                
            practice_mappings[practice] = lsoa_dist
        
        return practice_mappings
    
    # Fall back to existing JSON format
    return load_lsoa_mappings_legacy(mappings_dir, year)

def load_lsoa_mappings_legacy(mappings_dir, year=None):
    """
    Legacy function for loading LSOA mappings from JSON files.
    """
    # Initialize with the original mappings
    mappings = {}
    
    # Load the original mappings if they exist
    if os.path.exists(os.path.join(mappings_dir, 'GP_LSOA_PATIENTSDIST.json')):
        mappings['old'] = json.load(open(os.path.join(mappings_dir, 'GP_LSOA_PATIENTSDIST.json'), 'rb'))
    
    if os.path.exists(os.path.join(mappings_dir, 'GP_LSOA_PATIENTSDIST_2021.json')):
        mappings['2021'] = json.load(open(os.path.join(mappings_dir, 'GP_LSOA_PATIENTSDIST_2021.json'), 'rb'))
    
    # Find and load additional year-specific mappings
    dist_files = glob.glob(os.path.join(mappings_dir, 'GP_LSOA_PATIENTSDIST_*.json'))
    year_pattern = re.compile(r'GP_LSOA_PATIENTSDIST_(\d{4})\.json')
    
    for file in dist_files:
        match = year_pattern.search(file)
        if match:
            file_year = match.group(1)
            if file_year not in mappings:
                mappings[file_year] = json.load(open(file, 'rb'))
    
    # If a specific year is requested, return only that mapping
    if year is not None:
        if str(year) in mappings:
            return mappings[str(year)]
        else:
            # Find the closest year
            available_years = [int(y) for y in mappings.keys() if y.isdigit()]
            if not available_years:
                print(f"Warning: No year-specific mappings found. Using default mapping.")
                return mappings.get('2021', mappings.get('old', {}))
            
            closest_year = min(available_years, key=lambda x: abs(int(x) - int(year)))
            print(f"Warning: No mapping for year {year}. Using closest available year: {closest_year}")
            return mappings[str(closest_year)]
    
    # Return the original expected format for backward compatibility
    return [mappings.get('old', {}), mappings.get('2021', {})]


# Continue with rest of the functions from commonFunc_updated.py...
# (The remaining functions would be copied as-is since they don't need changes)

def detect_file_format(dataframe):
    """
    Detect the format of the prescription dataframe.
    
    Args:
        dataframe: Pandas DataFrame containing prescription data
    
    Returns:
        Dictionary of field mappings
    """
    fields = {}
    
    # Check for new format columns
    if 'BNF_CODE' in dataframe.columns:
        fields['format'] = 'new'
        fields['quantityField'] = 'TOTAL_QUANTITY'
        fields['costField'] = 'ACTUAL_COST'
        fields['practiceField'] = 'PRACTICE_CODE'
        fields['itemField'] = 'ITEMS'
        fields['bnfField'] = 'BNF_CODE'
        
        # Check if dosage field exists in new format
        if '19' in dataframe.columns:
            fields['dosageField'] = '19'
        else:
            fields['dosageField'] = None
    else:
        # Old format
        fields['format'] = 'old'
        fields['quantityField'] = '8'
        fields['costField'] = '7'
        fields['practiceField'] = '2'
        fields['itemField'] = '5'
        fields['bnfField'] = '16'
        fields['dosageField'] = '19'
    
    return fields

def prepare_dataframe(dataframe, fields):
    """
    Prepare the dataframe for processing by standardizing column types.
    
    Args:
        dataframe: Raw prescription dataframe
        fields: Field mapping from detect_file_format
    
    Returns:
        Tuple of (prepared_dataframe, updated_fields)
    """
    df = dataframe.copy()
    
    # Convert numeric fields to appropriate types
    numeric_fields = [fields['quantityField'], fields['costField'], fields['itemField']]
    if fields['dosageField']:
        numeric_fields.append(fields['dosageField'])
    
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')
            # Fill NaN values with 0 for calculations
            df[field] = df[field].fillna(0)
    
    return df, fields