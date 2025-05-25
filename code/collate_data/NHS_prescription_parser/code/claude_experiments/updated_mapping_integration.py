#!/usr/bin/env python3
"""
Updated Mapping Integration for NHS Prescription Parser

This script provides updated functions to handle the new mapping files:
- gp-reg-pat-prac-lsoa-all_YYYY.csv (direct GP registry data)
- LSOA_DEC_2021.csv (LSOA codes and names)
- census2021_lsoa_level.xlsx (census data)

Integrates with existing code while prioritizing newer data sources.
"""

import pandas as pd
import numpy as np
import json
import os
import glob
import re
from pathlib import Path
from tqdm import tqdm

def load_gp_registry_csv(mappings_dir, year=None):
    """
    Load GP registry data from the new CSV format files.
    
    Args:
        mappings_dir: Directory containing mapping files
        year: Specific year to load (if None, finds most recent)
    
    Returns:
        DataFrame with columns: PRACTICE_CODE, LSOA_CODE, Number of Patients
    """
    # Find available GP registry CSV files
    csv_pattern = os.path.join(mappings_dir, 'gp-reg-pat-prac-lsoa-all_*.csv')
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"No GP registry CSV files found in {mappings_dir}")
        return None
    
    # Extract years from filenames
    year_pattern = re.compile(r'gp-reg-pat-prac-lsoa-all_(\d{4})\.csv')
    available_years = []
    for f in csv_files:
        match = year_pattern.search(f)
        if match:
            available_years.append(int(match.group(1)))
    
    if not available_years:
        print("No valid year found in GP registry CSV files")
        return None
    
    # Select appropriate year
    if year is None:
        target_year = max(available_years)
        print(f"No year specified, using most recent: {target_year}")
    else:
        if year in available_years:
            target_year = year
        else:
            target_year = min(available_years, key=lambda x: abs(x - year))
            print(f"Year {year} not available, using closest: {target_year}")
    
    # Load the CSV file
    csv_file = os.path.join(mappings_dir, f'gp-reg-pat-prac-lsoa-all_{target_year}.csv')
    print(f"Loading GP registry data from: {csv_file}")
    
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
            print(f"Warning: Missing required columns. Available: {list(df.columns)}")
            return df
        
        df = df[required_cols].copy()
        
        # Clean and validate data
        df['NUMBER_OF_PATIENTS'] = pd.to_numeric(df['NUMBER_OF_PATIENTS'], errors='coerce')
        df = df.dropna(subset=['NUMBER_OF_PATIENTS'])
        df = df[df['NUMBER_OF_PATIENTS'] > 0]  # Remove zero/negative patient counts
        
        print(f"Loaded {len(df):,} GP-LSOA registrations for {target_year}")
        print(f"Unique practices: {df['PRACTICE_CODE'].nunique():,}")
        print(f"Unique LSOAs: {df['LSOA_CODE'].nunique():,}")
        print(f"Total patients: {df['NUMBER_OF_PATIENTS'].sum():,.0f}")
        
        return df
        
    except Exception as e:
        print(f"Error loading {csv_file}: {e}")
        return None

def prepare_lsoa_GP_population_updated(mappings_dir, year=None):
    """
    Enhanced version of prepare_lsoa_GP_population that uses CSV files when available.
    
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
    print(f"Loading LSOA patient populations for year: {year or 'latest'}")
    
    # Try CSV format first (newest)
    gp_df = load_gp_registry_csv(mappings_dir, year)
    
    if gp_df is not None:
        print("Using CSV format GP registry data")
        # Aggregate by LSOA (sum patients across all practices in each LSOA)
        lsoa_population = gp_df.groupby('LSOA_CODE')['NUMBER_OF_PATIENTS'].sum().to_dict()
        
        # Convert to int for consistency
        lsoa_population = {lsoa: int(pop) for lsoa, pop in lsoa_population.items()}
        
        print(f"Processed {len(lsoa_population):,} LSOAs from CSV data")
        return lsoa_population
    
    # Fall back to existing JSON format
    print("CSV format not available, falling back to JSON format")
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

def load_lsoa_lookup(mappings_dir):
    """
    Load LSOA code lookup table from LSOA_DEC_2021.csv.
    
    Args:
        mappings_dir: Directory containing mapping files
    
    Returns:
        DataFrame with LSOA codes and names
    """
    lsoa_file = os.path.join(mappings_dir, 'LSOA_DEC_2021.csv')
    
    if not os.path.exists(lsoa_file):
        print(f"LSOA lookup file not found: {lsoa_file}")
        return None
    
    try:
        # Handle potential BOM (Byte Order Mark) in CSV
        df = pd.read_csv(lsoa_file, encoding='utf-8-sig')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        print(f"Loaded LSOA lookup with {len(df):,} entries")
        
        # Show sample of London LSOAs
        london_sample = df[df['LSOA21NM'].str.contains('London|City of London', na=False)].head()
        if len(london_sample) > 0:
            print("Sample London LSOAs:")
            print(london_sample[['LSOA21CD', 'LSOA21NM']].to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"Error loading LSOA lookup: {e}")
        return None

def get_london_lsoas(mappings_dir):
    """
    Get list of London LSOA codes using multiple data sources.
    
    Args:
        mappings_dir: Directory containing mapping files
    
    Returns:
        Set of London LSOA codes
    """
    london_lsoas = set()
    
    # Method 1: Use LSOA lookup if available
    lsoa_df = load_lsoa_lookup(mappings_dir)
    if lsoa_df is not None:
        # Filter for London boroughs
        london_patterns = [
            'City of London', 'Camden', 'Greenwich', 'Hackney', 'Hammersmith', 'Fulham',
            'Haringey', 'Islington', 'Kensington', 'Chelsea', 'Lambeth', 'Lewisham',
            'Newham', 'Southwark', 'Tower Hamlets', 'Wandsworth', 'Westminster',
            'Barking', 'Dagenham', 'Barnet', 'Bexley', 'Brent', 'Bromley', 'Croydon',
            'Ealing', 'Enfield', 'Harrow', 'Havering', 'Hillingdon', 'Hounslow',
            'Kingston upon Thames', 'Merton', 'Redbridge', 'Richmond upon Thames',
            'Sutton', 'Waltham Forest'
        ]
        
        london_mask = lsoa_df['LSOA21NM'].str.contains('|'.join(london_patterns), na=False)
        london_lsoas.update(lsoa_df[london_mask]['LSOA21CD'].tolist())
        
        print(f"Found {len(london_lsoas)} London LSOAs from lookup table")
    
    # Method 2: Use GP registry data patterns (backup)
    if len(london_lsoas) == 0:
        gp_df = load_gp_registry_csv(mappings_dir)
        if gp_df is not None:
            # Use LSOA code patterns for London (E01000001-E01004999 roughly)
            london_pattern_lsoas = gp_df[
                gp_df['LSOA_CODE'].str.match(r'E0100[0-4]\d{3}')
            ]['LSOA_CODE'].unique()
            london_lsoas.update(london_pattern_lsoas)
            
            print(f"Found {len(london_lsoas)} potential London LSOAs from GP registry patterns")
    
    return london_lsoas

def load_census_data(mappings_dir):
    """
    Load census data from census2021_lsoa_level.xlsx if needed.
    
    Args:
        mappings_dir: Directory containing mapping files
    
    Returns:
        DataFrame with census data or None if not available
    """
    census_file = os.path.join(mappings_dir, 'census2021_lsoa_level.xlsx')
    
    if not os.path.exists(census_file):
        print(f"Census file not found: {census_file}")
        return None
    
    try:
        # Load Excel file - may need to specify sheet
        df = pd.read_excel(census_file)
        print(f"Loaded census data with {len(df):,} entries")
        print(f"Columns: {list(df.columns)}")
        return df
        
    except Exception as e:
        print(f"Error loading census data: {e}")
        return None

def validate_mapping_integration(mappings_dir):
    """
    Validate that all new mapping files are properly integrated.
    """
    print("VALIDATING MAPPING INTEGRATION")
    print("=" * 50)
    
    # Test GP registry CSV loading
    print("\n1. Testing GP Registry CSV loading:")
    for year in [2020, 2021, 2022, 2023, 2024, 2025]:
        gp_data = load_gp_registry_csv(mappings_dir, year)
        if gp_data is not None:
            print(f"   ✅ {year}: {len(gp_data):,} records")
        else:
            print(f"   ❌ {year}: Failed to load")
    
    # Test LSOA population preparation
    print("\n2. Testing LSOA population preparation:")
    lsoa_pop = prepare_lsoa_GP_population_updated(mappings_dir, 2021)
    if lsoa_pop:
        print(f"   ✅ Loaded {len(lsoa_pop):,} LSOAs")
        print(f"   ✅ Total patients: {sum(lsoa_pop.values()):,}")
    else:
        print("   ❌ Failed to load LSOA populations")
    
    # Test LSOA lookup
    print("\n3. Testing LSOA lookup:")
    lsoa_lookup = load_lsoa_lookup(mappings_dir)
    if lsoa_lookup is not None:
        print(f"   ✅ Loaded {len(lsoa_lookup):,} LSOA entries")
    else:
        print("   ❌ Failed to load LSOA lookup")
    
    # Test London LSOA identification
    print("\n4. Testing London LSOA identification:")
    london_lsoas = get_london_lsoas(mappings_dir)
    if london_lsoas:
        print(f"   ✅ Found {len(london_lsoas)} London LSOAs")
        
        # Check overlap with patient data
        if lsoa_pop:
            overlap = len(london_lsoas.intersection(set(lsoa_pop.keys())))
            print(f"   ✅ {overlap} London LSOAs have patient data")
    else:
        print("   ❌ Failed to identify London LSOAs")
    
    # Test census data loading
    print("\n5. Testing census data loading:")
    census_data = load_census_data(mappings_dir)
    if census_data is not None:
        print(f"   ✅ Loaded census data")
    else:
        print("   ❌ Census data not available or failed to load")
    
    print("\n" + "=" * 50)
    print("VALIDATION COMPLETE")

def main():
    """Test the updated mapping integration"""
    mappings_dir = "../mappings/"
    validate_mapping_integration(mappings_dir)

if __name__ == "__main__":
    main()