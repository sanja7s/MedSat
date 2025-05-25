#!/usr/bin/env python3
"""
Extended runner script for NHS prescription prevalence calculation.

This script uses the updated commonFunc_updated.py module to calculate
prevalence metrics for conditions or drugs, supporting the newer data formats
and LSOA mappings for 2021 and beyond.
"""

import argparse
import sys
import pandas as pd
import json
import os
from tqdm import tqdm
from sources.downloader import Downloader
from matching.drugMatching import DrugMatcher
from matching.commonFunc_updated import (
    calculateTemporalMetrics_LSOA,
    writeResultFiles,
    calculateTemporalMetrics_LSOA_opioids,
    writeResultFiles_opioid,
    str2bool
)


def run_drug_prevalence(args):
    """
    Run drug prevalence calculation with the specified parameters.
    """
    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    
    drug_list = args.drugs
    start = str(args.start)
    end = str(args.end)
    year = args.year
    
    # Override output directory if specified
    if args.output_dir:
        print('Overriding output dir')
        output_dir = args.output_dir
    
    # Download or locate prescription files
    downloader = Downloader(sourcesFile="sources/serialized_file_paths.json", download_dir=input_dir)
    selected_files = []
    try:
        selected_files = downloader.download_range(start, end)
    except Exception as e:
        print(f"Failed download: {e}")
        exit(-1)
    
    files_sub = selected_files
    
    print(f'Running for {drug_list} between months {start} and {end}. The following files were selected:')
    for f in files_sub:
        print(f)
    
    # Match drugs to BNF codes
    drugMatcher = DrugMatcher(mappings_dir='./mappings/', output_dir=output_dir)
    DiseaseDrugs, drugMap = drugMatcher.DrugMatching(drug_list)
    print(drugMap)
    
    # Initialize dictionaries to store results
    monthly_borough_dosage_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}
    
    # Compute prevalence over selected files
    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print(f"Working with month {month}")
        
        monthly_borough_dosage_new[month] = {}
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}
        
        # Read prescription data
        pdp = pd.read_csv(f, compression='gzip')
        
        # Determine file format based on columns
        if 'BNF_CODE' in pdp.columns:
            bnf_code_field = 'BNF_CODE'
        else:
            bnf_code_field = '16'  # Default for old format
        
        for drugname in tqdm(drugMap):
            print(f"Working with drug {drugname}")
            monthly_borough_dosage_new[month][drugname] = {}
            monthly_borough_costs_new[month][drugname] = {}
            monthly_borough_quantity_new[month][drugname] = {}
            monthly_borough_items_new[month][drugname] = {}
            
            drugs = drugMap[drugname]
            
            # Subset of prescriptions for the drug
            drug_prescriptions = pdp.loc[pdp[bnf_code_field].isin(drugs)]
            print(f"Found {len(drug_prescriptions)} rows for {len(drugs)} variants of {drugname}")
            
            # Calculate metrics for this drug and month
            monthly_borough_quantity_new[month][drugname], \
            monthly_borough_costs_new[month][drugname], \
            monthly_borough_dosage_new[month][drugname], \
            monthly_borough_items_new[month][drugname] = calculateTemporalMetrics_LSOA(
                drug_prescriptions, mappings_dir='./mappings/', year=year
            )
    
    print("Done computing LSOA level prescription prevalences, writing files")
    
    # Write result files
    writeResultFiles(
        monthly_borough_quantity_new,
        monthly_borough_dosage_new,
        monthly_borough_costs_new,
        monthly_borough_items_new,
        list(drugMap.keys()),
        output_dir,
        mappings_dir='./mappings/',
        year=year
    )
    
    # Dump drugs used for this analysis
    drugMatcher.dumpDrugs(DiseaseDrugs)
    
    print("Finished processing!")


def run_custom_list_prevalence(args):
    """
    Run prevalence calculation with a custom list of drugs and BNF codes.
    """
    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    
    drug_list_json = args.list[0]
    start = str(args.start)
    end = str(args.end)
    year = args.year
    
    # Override output directory if specified
    if args.output_dir:
        print('Overriding output dir')
        output_dir = args.output_dir
    
    # Download or locate prescription files
    downloader = Downloader(sourcesFile="sources/serialized_file_paths.json", download_dir=input_dir)
    selected_files = []
    try:
        selected_files = downloader.download_range(start, end)
    except Exception as e:
        print(f"Failed download: {e}")
        exit(-1)
    
    files_sub = selected_files
    
    print(f'Running for supplied drugs between months {start} and {end}. The following files were selected:')
    for f in files_sub:
        print(f)
    
    # Load drug list from JSON
    drugMap = {}
    try:
        drugMap = json.load(open(drug_list_json, 'r'))
    except Exception as e:
        print(f"Failed to open {drug_list_json}: {e}")
        exit(-1)
    
    print(drugMap)
    
    # Initialize dictionaries to store results
    monthly_borough_dosage_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}
    
    # Compute prevalence over selected files
    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print(f"Working with month {month}")
        
        monthly_borough_dosage_new[month] = {}
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}
        
        # Read prescription data
        pdp = pd.read_csv(f, compression='gzip')
        
        # Determine file format based on columns
        if 'BNF_CODE' in pdp.columns:
            bnf_code_field = 'BNF_CODE'
        else:
            bnf_code_field = '16'  # Default for old format
        
        for drugname in tqdm(drugMap):
            print(f"Working with drug {drugname}")
            monthly_borough_dosage_new[month][drugname] = {}
            monthly_borough_costs_new[month][drugname] = {}
            monthly_borough_quantity_new[month][drugname] = {}
            monthly_borough_items_new[month][drugname] = {}
            
            drugs = drugMap[drugname]
            
            # Subset of prescriptions for the drug
            drug_prescriptions = pdp.loc[pdp[bnf_code_field].isin(drugs)]
            print(f"Found {len(drug_prescriptions)} rows for {len(drugs)} variants of {drugname}")
            
            # Calculate metrics for this drug and month
            monthly_borough_quantity_new[month][drugname], \
            monthly_borough_costs_new[month][drugname], \
            monthly_borough_dosage_new[month][drugname], \
            monthly_borough_items_new[month][drugname] = calculateTemporalMetrics_LSOA(
                drug_prescriptions, mappings_dir='./mappings/', year=year
            )
    
    print("Done computing LSOA level prescription prevalences, writing files")
    
    # Write result files
    writeResultFiles(
        monthly_borough_quantity_new,
        monthly_borough_dosage_new,
        monthly_borough_costs_new,
        monthly_borough_items_new,
        list(drugMap.keys()),
        output_dir,
        mappings_dir='./mappings/',
        year=year
    )
    
    print("Finished processing!")


def run_condition_prevalence(args):
    """
    Run prevalence calculation for medical conditions.
    """
    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    
    conditions = args.conditions
    print(f"Running for: {conditions}")
    
    start = str(args.start)
    end = str(args.end)
    custDLFN = args.custom_drug_list_file_names
    year = args.year
    
    # Override output directory if specified
    if args.output_dir:
        print('Overriding output dir')
        output_dir = args.output_dir
    
    # If no custom drug list is provided, use drug matching
    if custDLFN is None:
        # Download or locate prescription files
        downloader = Downloader(sourcesFile="sources/serialized_file_paths.json", download_dir=input_dir)
        selected_files = []
        try:
            selected_files = downloader.download_range(start, end)
        except Exception as e:
            print(f"Failed download: {e}")
            exit(-1)
        
        files_sub = selected_files
        
        print(f'Running for supplied drugs between months {start} and {end}. The following files were selected:')
        for f in files_sub:
            print(f)
        
        # Match conditions to drugs
        matcher = DrugMatcher(mappings_dir='./mappings/', output_dir=output_dir)
        DiseaseDrugs, drugMap = matcher.DrugMatching(conditions, isCat=args.isCat)
        
        matcher.dumpDrugs(DiseaseDrugs)
        
        print(DiseaseDrugs)
        
        for k in drugMap:
            print(k, drugMap[k])
        
        # Initialize dictionaries to store results
        monthly_borough_dosage_new = {}
        monthly_borough_costs_new = {}
        monthly_borough_quantity_new = {}
        monthly_borough_items_new = {}
        
        # Compute prevalence over selected files
        for f in tqdm(files_sub):
            month = f.split('/')[-1].split('.')[0]
            print(f"Working with file {f}")
            
            monthly_borough_dosage_new[month] = {}
            monthly_borough_costs_new[month] = {}
            monthly_borough_quantity_new[month] = {}
            monthly_borough_items_new[month] = {}
            
            # Read prescription data
            pdp = pd.read_csv(f, compression='gzip')
            
            # Determine file format based on columns
            if 'BNF_CODE' in pdp.columns:
                bnf_code_field = 'BNF_CODE'
            else:
                bnf_code_field = '16'  # Default for old format
            
            for disease in tqdm(drugMap):
                print(f"Working with disease {disease}")
                monthly_borough_dosage_new[month][disease] = {}
                monthly_borough_costs_new[month][disease] = {}
                monthly_borough_quantity_new[month][disease] = {}
                monthly_borough_items_new[month][disease] = {}
                
                drugs = drugMap[disease]
                
                # Subset of prescriptions for the condition
                disease_prescriptions = pdp.loc[pdp[bnf_code_field].isin(drugs)]
                
                # Calculate metrics for this condition and month
                monthly_borough_quantity_new[month][disease], \
                monthly_borough_costs_new[month][disease], \
                monthly_borough_dosage_new[month][disease], \
                monthly_borough_items_new[month][disease] = calculateTemporalMetrics_LSOA(
                    disease_prescriptions, mappings_dir='./mappings/', year=year
                )
            
            print("Done computing LSOA level prescription prevalences, writing files")
            
            # Write result files
            writeResultFiles(
                monthly_borough_quantity_new,
                monthly_borough_dosage_new,
                monthly_borough_costs_new,
                monthly_borough_items_new,
                conditions,
                output_dir,
                mappings_dir='./mappings/',
                year=year
            )
            print("Finished processing!")
    
    # If custom drug list is provided, aggregate existing drug files
    else:
        directory_path = output_dir
        
        i = 0
        for cond in conditions:
            print(f"Parsing condition {i+1} of {len(conditions)}: {cond}")
            all_files = []
            
            # Load custom drug list
            with open(custDLFN[i], 'r') as drug_file:
                custom_drug_list = json.load(drug_file)
            
            # Collect drug files
            for drug_name in custom_drug_list:
                file_name = f"{drug_name}_V4.csv.gz"
                all_files.append(os.path.join(directory_path, file_name))
            
            # List to hold dataframes from each file
            dfs = []
            
            # Read all CSV files into dataframes
            for file_name in all_files:
                try:
                    dfs.append(pd.read_csv(file_name, compression='gzip'))
                except Exception as e:
                    print(f"Error reading {file_name}: {e}")
            
            if not dfs:
                print(f"No valid drug files found for condition {cond}")
                i += 1
                continue
            
            # Concatenate all the dataframes
            df = pd.concat(dfs, ignore_index=True)
            
            # Check that 'Patient_count' is the same across the same 'LSOA_CODE's
            try:
                assert df.groupby('LSOA_CODE')['Patient_count'].nunique().max() == 1
            except AssertionError:
                print("Warning: Patient counts vary for the same LSOA. Using the first value.")
            
            # Aggregate the required columns
            agg_funcs = {
                'Total_quantity': 'sum',
                'Dosage_ratio': 'sum',
                'Total_cost': 'sum',
                'Total_items': 'sum',
                'Patient_count': 'first'
            }
            disease_df = df.groupby(['YYYYMM', 'LSOA_CODE']).agg(agg_funcs).reset_index()
            
            # Save to a new CSV file
            out_file_name = f"{cond}_V4.csv.gz"
            
            print("Done computing LSOA level prescription prevalences, writing files")
            disease_df.to_csv(os.path.join(directory_path, out_file_name), index=False, compression='gzip')
            print("Finished processing!")
            
            i += 1


def run_opioid_prevalence(args):
    """
    Run prevalence calculation for opioids with OME values.
    """
    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    
    start = str(args.start)
    end = str(args.end)
    year = args.year
    
    # Override output directory if specified
    if args.output_dir:
        print('Overriding output dir')
        output_dir = args.output_dir
    
    # Download or locate prescription files
    downloader = Downloader(sourcesFile="sources/serialized_file_paths.json", download_dir=input_dir)
    selected_files = []
    try:
        selected_files = downloader.download_range(start, end)
    except Exception as e:
        print(f"Failed download: {e}")
        exit(-1)
    
    files_sub = selected_files
    
    print(f'Running for opioids between months {start} and {end}. The following files were selected:')
    for f in files_sub:
        print(f)
    
    # Load OME mappings
    ome_df = pd.read_csv(os.path.join('./mappings', 'ome_rossano_opioids.csv'))
    ome_map = dict(zip(ome_df['bnf'], ome_df['ome_multiplier']))
    
    # Initialize dictionaries to store results
    monthly_borough_ome_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}
    
    # Compute prevalence over selected files
    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print(f"Working with month {month}")
        
        monthly_borough_ome_new[month] = {'opioids': {}}
        monthly_borough_costs_new[month] = {'opioids': {}}
        monthly_borough_quantity_new[month] = {'opioids': {}}
        monthly_borough_items_new[month] = {'opioids': {}}
        
        # Read prescription data
        pdp = pd.read_csv(f, compression='gzip')
        
        # Determine file format based on columns
        if 'BNF_CODE' in pdp.columns:
            bnf_code_field = 'BNF_CODE'
            quantity_field = 'TOTAL_QUANTITY'
        else:
            bnf_code_field = '16'  # Default for old format
            quantity_field = '8'
        
        # Filter for opioids and calculate OME
        opioids_prescriptions = pdp[pdp[bnf_code_field].isin(ome_map.keys())]
        
        # Add OME column
        opioids_prescriptions['presc_ome'] = 0.0
        for bnf_code, ome_value in ome_map.items():
            mask = opioids_prescriptions[bnf_code_field] == bnf_code
            opioids_prescriptions.loc[mask, 'presc_ome'] = opioids_prescriptions.loc[mask, quantity_field] * ome_value
        
        # Calculate metrics for opioids
        monthly_borough_quantity_new[month]['opioids'], \
        monthly_borough_costs_new[month]['opioids'], \
        monthly_borough_ome_new[month]['opioids'], \
        monthly_borough_items_new[month]['opioids'] = calculateTemporalMetrics_LSOA_opioids(
            opioids_prescriptions, mappings_dir='./mappings/', year=year
        )
    
    print("Done computing LSOA level prescription prevalences, writing files")
    
    # Write result files for opioids
    writeResultFiles_opioid(
        monthly_borough_quantity_new,
        monthly_borough_ome_new,
        monthly_borough_costs_new,
        monthly_borough_items_new,
        ['opioids'],
        output_dir,
        mappings_dir='./mappings/',
        year=year
    )
    
    print("Finished processing!")


def main():
    parser = argparse.ArgumentParser(description='Extended NHS prescription prevalence calculator')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Drug prevalence parser
    drug_parser = subparsers.add_parser('drug', help='Calculate drug prevalence')
    drug_parser.add_argument('-d', '--drugs', nargs="+", required=True, 
                            help="List of drug names you need prescription prevalence for")
    drug_parser.add_argument('-s', "--start", required=True, help="Start year and month, format YYYYMM")
    drug_parser.add_argument('-e', "--end", required=True, help="End year and month, format YYYYMM")
    drug_parser.add_argument('-y', "--year", help="Year for LSOA mapping (e.g., 2021)")
    drug_parser.add_argument('-odir', "--output_dir", help="Directory for output files, default ../data_prep/")
    
    # Custom list prevalence parser
    list_parser = subparsers.add_parser('list', help='Calculate prevalence from custom drug list')
    list_parser.add_argument('-l', '--list', nargs="+", required=True, help="JSON file in a correct format")
    list_parser.add_argument('-s', "--start", required=True, help="Start year and month, format YYYYMM")
    list_parser.add_argument('-e', "--end", required=True, help="End year and month, format YYYYMM")
    list_parser.add_argument('-y', "--year", help="Year for LSOA mapping (e.g., 2021)")
    list_parser.add_argument('-odir', "--output_dir", help="Directory for output files, default ../data_prep/")
    
    # Condition prevalence parser
    condition_parser = subparsers.add_parser('condition', help='Calculate condition prevalence')
    condition_parser.add_argument('-c', '--conditions', nargs="+", required=True,
                                help="List of conditions you need prescription prevalence for")
    condition_parser.add_argument('-custDLFN', '--custom_drug_list_file_names', nargs="+", default=None,
                                help="List of custom lists for the conditions")
    condition_parser.add_argument('--isCat', type=str2bool, default=False,
                                help="Boolean flag to notify if the list is a set of conditions or categories")
    condition_parser.add_argument('-s', "--start", required=True, help="Start year and month, format YYYYMM")
    condition_parser.add_argument('-e', "--end", required=True, help="End year and month, format YYYYMM")
    condition_parser.add_argument('-y', "--year", help="Year for LSOA mapping (e.g., 2021)")
    condition_parser.add_argument('-odir', "--output_dir", help="Directory for output files, default ../data_prep/")
    
    # Opioid prevalence parser
    opioid_parser = subparsers.add_parser('opioid', help='Calculate opioid prevalence with OME')
    opioid_parser.add_argument('-s', "--start", required=True, help="Start year and month, format YYYYMM")
    opioid_parser.add_argument('-e', "--end", required=True, help="End year and month, format YYYYMM")
    opioid_parser.add_argument('-y', "--year", help="Year for LSOA mapping (e.g., 2021)")
    opioid_parser.add_argument('-odir', "--output_dir", help="Directory for output files, default ../data_prep/")
    
    args = parser.parse_args()
    
    if args.command == 'drug':
        run_drug_prevalence(args)
    elif args.command == 'list':
        run_custom_list_prevalence(args)
    elif args.command == 'condition':
        run_condition_prevalence(args)
    elif args.command == 'opioid':
        run_opioid_prevalence(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()