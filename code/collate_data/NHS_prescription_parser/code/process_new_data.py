#!/usr/bin/env python3
"""
Process new NHS prescription data with updated LSOA mappings.

This script processes the new EPD file and GP registry files to create
updated LSOA mappings and prepare the data for prevalence calculation.
"""

import argparse
import os
import pandas as pd
import subprocess
import sys
from tqdm import tqdm
import shutil
import gzip
import json


def process_gp_registry_file(file_path, output_dir, year):
    """
    Process a GP registry file to create the necessary mapping files.
    
    Args:
        file_path: Path to the GP registry CSV file
        output_dir: Directory to save the mapping files
        year: Year of the data
    """
    print(f"Processing GP registry file: {file_path}")
    
    # Read the GP registry data
    df = pd.read_csv(file_path)
    print(f"Loaded GP registry data with {len(df)} rows")
    
    # Filter for 'ALL' sex records to avoid double-counting
    df = df[df['SEX'] == 'ALL']
    
    # Create a dictionary to store the GP to LSOA patient distribution
    gp_lsoa_map = {}
    lsoa_patient_dist = {}
    
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
            
            # Also create the LSOA patient distribution
            if lsoa_code not in lsoa_patient_dist:
                lsoa_patient_dist[lsoa_code] = patient_count
            else:
                lsoa_patient_dist[lsoa_code] += patient_count
    
    # Save the GP to LSOA mapping
    gps_file = os.path.join(output_dir, f"GPs_{year}.json")
    with open(gps_file, 'w') as f:
        json.dump(gp_lsoa_map, f)
    print(f"Saved GP to LSOA mapping to {gps_file}")
    
    # Save the LSOA patient distribution
    dist_file = os.path.join(output_dir, f"GP_LSOA_PATIENTSDIST_{year}.json")
    with open(dist_file, 'w') as f:
        json.dump(lsoa_patient_dist, f)
    print(f"Saved LSOA patient distribution to {dist_file}")


def process_lsoa_mapping(file_path, output_dir):
    """
    Process the LSOA mapping file (2011 to 2021 codes).
    
    Args:
        file_path: Path to the LSOA mapping CSV file
        output_dir: Directory to save the mapping file
    """
    print(f"Processing LSOA mapping file: {file_path}")
    
    try:
        # Read the LSOA mapping data
        df = pd.read_csv(file_path)
        print(f"LSOA mapping columns: {df.columns.tolist()}")
        
        # Create a mapping dictionary
        lsoa_mapping = {}
        if 'LSOA11CD' in df.columns and 'LSOA21CD' in df.columns:
            # Direct mapping from 2011 to 2021 codes
            for _, row in df.iterrows():
                lsoa_mapping[row['LSOA21CD']] = row['LSOA11CD']
        elif 'LSOA21CD' in df.columns:
            # Only 2021 codes are available
            for _, row in df.iterrows():
                lsoa_mapping[row['LSOA21CD']] = row['LSOA21CD']
        
        # Save the mapping
        mapping_file = os.path.join(output_dir, "LSOA_2021_to_2011_mapping.json")
        with open(mapping_file, 'w') as f:
            json.dump(lsoa_mapping, f)
        print(f"Saved LSOA mapping to {mapping_file}")
        
    except Exception as e:
        print(f"Error processing LSOA mapping file: {e}")


def process_epd_file(file_path, output_dir):
    """
    Process the EPD file and convert it to gzipped CSV format.
    
    Args:
        file_path: Path to the EPD ZIP file
        output_dir: Directory to save the processed file
    """
    print(f"Processing EPD file: {file_path}")
    
    # Extract the year and month from the filename
    filename = os.path.basename(file_path)
    yyyymm = filename.split('_')[-1].split('.')[0]  # Assuming format like EPD_202110.ZIP
    
    # Create output filename
    output_filename = f"{yyyymm}.gz"
    output_path = os.path.join(output_dir, output_filename)
    
    # Check if output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a temporary directory for extraction
    temp_dir = os.path.join(output_dir, "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    try:
        # Extract the ZIP file
        print(f"Extracting {file_path} to {temp_dir}...")
        extract_cmd = f"unzip -o '{file_path}' -d '{temp_dir}'"
        subprocess.run(extract_cmd, shell=True, check=True)
        
        # Find the extracted CSV file
        csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
        if not csv_files:
            print("No CSV files found in the extracted archive")
            return None
        
        csv_file = os.path.join(temp_dir, csv_files[0])
        print(f"Found CSV file: {csv_file}")
        
        # Read a sample to get column names
        sample = pd.read_csv(csv_file, nrows=5)
        print(f"EPD file columns: {sample.columns.tolist()}")
        
        # Process the file in chunks and compress
        chunk_size = 1000000  # Adjust based on available memory
        reader = pd.read_csv(csv_file, chunksize=chunk_size)
        
        print(f"Converting to gzipped format...")
        with gzip.open(output_path, 'wt') as f_out:
            # Write header
            header = ','.join(sample.columns) + '\n'
            f_out.write(header)
            
            # Process chunks
            for chunk in tqdm(reader):
                chunk_str = chunk.to_csv(index=False, header=False)
                f_out.write(chunk_str)
        
        print(f"Processed EPD file saved to: {output_path}")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        return output_path
    
    except Exception as e:
        print(f"Error processing EPD file: {e}")
        # Clean up temporary directory if it exists
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None


def update_sources_file(sources_file, epd_path, yyyymm):
    """
    Update the serialized_file_paths.json file to include the new EPD file.
    
    Args:
        sources_file: Path to the serialized_file_paths.json file
        epd_path: Path to the processed EPD file
        yyyymm: Year and month (YYYYMM) of the EPD data
    """
    print(f"Updating {sources_file} with new EPD file...")
    
    try:
        # Load existing sources file
        with open(sources_file, 'r') as f:
            sources = json.load(f)
        
        # Add new entry
        key = f"{yyyymm}.gz"
        sources[key] = f"file://{os.path.abspath(epd_path)}"
        
        # Write updated sources back to file
        with open(sources_file, 'w') as f:
            json.dump(sources, f, indent=4)
        
        print(f"Updated {sources_file} with new entry for {yyyymm}")
    
    except Exception as e:
        print(f"Error updating sources file: {e}")


def update_mappings(gp_registry_files, lsoa_mapping_file, epd_file, years, mappings_dir, prescriptions_dir, sources_file):
    """
    Process all input files and update the necessary mappings.
    
    Args:
        gp_registry_files: List of GP registry files
        lsoa_mapping_file: Path to the LSOA mapping file
        epd_file: Path to the EPD file
        years: List of years corresponding to the GP registry files
        mappings_dir: Directory to save mapping files
        prescriptions_dir: Directory to save processed prescription files
        sources_file: Path to the serialized_file_paths.json file
    """
    # Create output directories if they don't exist
    if not os.path.exists(mappings_dir):
        os.makedirs(mappings_dir)
    if not os.path.exists(prescriptions_dir):
        os.makedirs(prescriptions_dir)
    
    # Process LSOA mapping file
    if lsoa_mapping_file:
        process_lsoa_mapping(lsoa_mapping_file, mappings_dir)
    
    # Process GP registry files
    for i, file_path in enumerate(gp_registry_files):
        if i < len(years):
            year = years[i]
            process_gp_registry_file(file_path, mappings_dir, year)
    
    # Process EPD file
    if epd_file:
        yyyymm = os.path.basename(epd_file).split('_')[-1].split('.')[0]
        processed_path = process_epd_file(epd_file, prescriptions_dir)
        if processed_path and sources_file:
            update_sources_file(sources_file, processed_path, yyyymm)


def main():
    parser = argparse.ArgumentParser(description='Process new NHS data files and update mappings')
    parser.add_argument('--gp-registry', nargs='+', help='Paths to GP registry files (CSV)')
    parser.add_argument('--years', nargs='+', help='Years corresponding to the GP registry files')
    parser.add_argument('--lsoa-mapping', help='Path to LSOA mapping file (CSV)')
    parser.add_argument('--epd-file', help='Path to EPD file (ZIP)')
    parser.add_argument('--mappings-dir', default='./mappings', help='Output directory for mapping files')
    parser.add_argument('--prescriptions-dir', default='./prescriptionfiles', help='Output directory for processed prescription files')
    parser.add_argument('--sources-file', default='./sources/serialized_file_paths.json', help='Path to serialized_file_paths.json')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.gp_registry and args.years and len(args.gp_registry) != len(args.years):
        print("Error: Number of GP registry files must match number of years")
        sys.exit(1)
    
    # Process files and update mappings
    update_mappings(
        args.gp_registry,
        args.lsoa_mapping,
        args.epd_file,
        args.years,
        args.mappings_dir,
        args.prescriptions_dir,
        args.sources_file
    )
    
    print("All data processing complete.")


if __name__ == "__main__":
    main()