#!/usr/bin/env python3
"""
Script to create LSOA patient distribution mappings for 2021 and later.
This script processes the new GP patient registry files and creates the necessary
JSON mapping files for use with the prescription prevalence code.
"""

import pandas as pd
import json
import os
import argparse
from tqdm import tqdm


def process_gp_registry_file(file_path, year):
    """
    Process a GP registry file to create a mapping of GP practices to LSOA codes
    with patient counts.
    
    Args:
        file_path: Path to the GP registry CSV file
        year: Year of the data (used for naming the output file)
        
    Returns:
        A dictionary mapping GP practice codes to LSOA patient distributions
    """
    print(f"Processing GP registry file: {file_path}")
    
    # Read the GP registry data
    df = pd.read_csv(file_path)
    
    # Filter for 'ALL' sex records to avoid double-counting
    df = df[df['SEX'] == 'ALL']
    
    # Create a dictionary to store the GP to LSOA patient distribution
    gp_lsoa_map = {}
    
    # Group by practice code
    for practice_code, group in tqdm(df.groupby('PRACTICE_CODE')):
        if practice_code not in gp_lsoa_map:
            gp_lsoa_map[practice_code] = {
                'Practice_name': group['PRACTICE_NAME'].iloc[0],
                'Patient_registry_LSOA': {}
            }
        
        # Add LSOA patient counts to the practice
        for _, row in group.iterrows():
            lsoa_code = row['LSOA_CODE']
            patient_count = row['Number of Patients']
            gp_lsoa_map[practice_code]['Patient_registry_LSOA'][lsoa_code] = patient_count
    
    return gp_lsoa_map


def process_census_lsoa_mapping(file_path):
    """
    Process the LSOA mapping file to create a mapping between 2011 and 2021 LSOA codes.
    
    Args:
        file_path: Path to the LSOA mapping CSV file
        
    Returns:
        A dictionary mapping 2021 LSOA codes to 2011 LSOA codes
    """
    print(f"Processing LSOA mapping file: {file_path}")
    
    # Read the LSOA mapping data - this will depend on the actual format of the file
    # For now, we assume a simple CSV with LSOA11CD and LSOA21CD columns
    try:
        df = pd.read_csv(file_path)
        # Adapt column names to the actual data
        mapping = {}
        if 'LSOA11CD' in df.columns and 'LSOA21CD' in df.columns:
            for _, row in df.iterrows():
                mapping[row['LSOA21CD']] = row['LSOA11CD']
        else:
            print("Warning: Expected columns 'LSOA11CD' and 'LSOA21CD' not found.")
            print(f"Available columns: {df.columns.tolist()}")
        return mapping
    except Exception as e:
        print(f"Error processing LSOA mapping file: {e}")
        return {}


def create_patient_distribution(gp_lsoa_map, lsoa_mapping=None):
    """
    Create a patient distribution across LSOAs.
    
    Args:
        gp_lsoa_map: Mapping of GP practices to LSOA patient distributions
        lsoa_mapping: Optional mapping from 2021 to 2011 LSOA codes
        
    Returns:
        A dictionary mapping LSOA codes to total patient counts
    """
    print("Creating LSOA patient population mapping")
    
    lsoa_patient_pop = {}
    
    for gp in tqdm(gp_lsoa_map):
        for lsoa in gp_lsoa_map[gp]['Patient_registry_LSOA']:
            # Map LSOA code if a mapping is provided
            mapped_lsoa = lsoa_mapping.get(lsoa, lsoa) if lsoa_mapping else lsoa
            
            if mapped_lsoa not in lsoa_patient_pop:
                lsoa_patient_pop[mapped_lsoa] = gp_lsoa_map[gp]['Patient_registry_LSOA'][lsoa]
            else:
                lsoa_patient_pop[mapped_lsoa] += gp_lsoa_map[gp]['Patient_registry_LSOA'][lsoa]
    
    return lsoa_patient_pop


def process_epd_file(file_path, output_dir):
    """
    Process the EPD file and convert it to the format expected by the codebase.
    
    Args:
        file_path: Path to the EPD CSV file
        output_dir: Directory to save the processed file
        
    Returns:
        Path to the processed file
    """
    print(f"Processing EPD file: {file_path}")
    
    # Extract the year and month from the filename
    filename = os.path.basename(file_path)
    yyyymm = filename.split('.')[0].split('_')[-1]  # Assuming format like EPD_202110
    
    # Create output filename
    output_filename = f"{yyyymm}.gz"
    output_path = os.path.join(output_dir, output_filename)
    
    # Process in chunks to handle large files
    chunk_size = 1000000  # Adjust based on your system's memory
    
    # First read a small sample to get column names
    sample = pd.read_csv(file_path, nrows=5)
    print(f"EPD file columns: {sample.columns.tolist()}")
    
    # Map columns to the expected format
    # The actual mapping will depend on the EPD file structure
    # This is a placeholder based on common NHS prescription data structure
    column_mapping = {
        'PRACTICE_CODE': 'PRACTICE_CODE',  # Map to column 2 in older format
        'BNF_CODE': 'BNF_CODE',           # Map to column 16 in older format
        'ITEMS': 'ITEMS',                 # Map to column 5 in older format
        'ACTUAL_COST': 'ACTUAL_COST',     # Map to column 7 in older format
        'QUANTITY': 'TOTAL_QUANTITY'      # Map to column 8 in older format
    }
    
    # Process file in chunks
    print(f"Converting EPD file to format expected by codebase...")
    
    try:
        # Read and process the file in chunks
        reader = pd.read_csv(file_path, chunksize=chunk_size)
        first_chunk = True
        
        for chunk in tqdm(reader):
            # Select and rename columns
            # The actual transformation will depend on the specific format differences
            processed_chunk = chunk[list(column_mapping.keys())].rename(columns=column_mapping)
            
            # Save chunk to gzipped file
            mode = 'w' if first_chunk else 'a'
            processed_chunk.to_csv(output_path, compression='gzip', index=False, mode=mode, header=first_chunk)
            first_chunk = False
        
        print(f"Processed EPD file saved to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error processing EPD file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Process new NHS data for prescription prevalence analysis')
    parser.add_argument('--gp-registry', required=True, help='Path to GP registry file (CSV)')
    parser.add_argument('--lsoa-mapping', help='Path to LSOA mapping file (CSV)')
    parser.add_argument('--epd-file', help='Path to EPD file (CSV)')
    parser.add_argument('--year', required=True, help='Year of the data (YYYY)')
    parser.add_argument('--output-dir', default='../mappings', help='Output directory for mapping files')
    parser.add_argument('--prescriptions-dir', default='./prescriptionfiles', help='Output directory for processed prescription files')
    
    args = parser.parse_args()
    
    # Create output directories if they don't exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.prescriptions_dir, exist_ok=True)
    
    # Process GP registry file
    gp_lsoa_map = process_gp_registry_file(args.gp_registry, args.year)
    
    # Save GP to LSOA mapping
    gp_map_output = os.path.join(args.output_dir, f"GPs_{args.year}.json")
    with open(gp_map_output, 'w') as f:
        json.dump(gp_lsoa_map, f)
    print(f"GP to LSOA mapping saved to: {gp_map_output}")
    
    # Process LSOA mapping file if provided
    lsoa_mapping = None
    if args.lsoa_mapping:
        lsoa_mapping = process_census_lsoa_mapping(args.lsoa_mapping)
    
    # Create patient distribution
    lsoa_patient_pop = create_patient_distribution(gp_lsoa_map, lsoa_mapping)
    
    # Save patient distribution
    patientdist_output = os.path.join(args.output_dir, f"GP_LSOA_PATIENTSDIST_{args.year}.json")
    with open(patientdist_output, 'w') as f:
        json.dump(lsoa_patient_pop, f)
    print(f"LSOA patient distribution saved to: {patientdist_output}")
    
    # Process EPD file if provided
    if args.epd_file:
        process_epd_file(args.epd_file, args.prescriptions_dir)
    
    print("Data processing complete.")


if __name__ == "__main__":
    main()