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

def prepare_lsoa_GP_population(mappings_dir, isOld=None, year=None):
    """
    Load the LSOA patient population mapping.
    
    Args:
        mappings_dir: Directory containing mapping files
        isOld: Legacy parameter for backward compatibility (if True, uses old format)
        year: Year of the data (if None, uses the most recent available)
    
    Returns:
        Dictionary mapping LSOA codes to patient counts
    """
    # Handle backward compatibility
    if isOld is not None:
        if isOld:
            LSOA_patients_map = json.load(open(mappings_dir + 'GPs_2013.json','r'))
        else:
            LSOA_patients_map = json.load(open(mappings_dir + 'GPs.json','r'))
        
        LSOA_patient_pop = {}
        for GP in tqdm(LSOA_patients_map):
            for lsoa in LSOA_patients_map[GP]['Patient_registry_LSOA']:
                if lsoa not in LSOA_patient_pop:
                    LSOA_patient_pop[lsoa] = LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
                else:
                    LSOA_patient_pop[lsoa] += LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
        return LSOA_patient_pop
    
    # New improved logic
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
            return prepare_lsoa_GP_population(mappings_dir)
    
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
    
    Args:
        mappings_dir: Directory containing mapping files
        year: Year of the data (if None, returns mappings for all available years)
    
    Returns:
        Dictionary mapping years to LSOA distribution mappings or legacy list format
    """
    # For backward compatibility, if no year specified, return original format
    if year is None:
        LSOA_dist_old = json.load(open(mappings_dir + 'GP_LSOA_PATIENTSDIST.json', 'rb'))
        LSOA_dist_2021 = json.load(open(mappings_dir + 'GP_LSOA_PATIENTSDIST_2021.json', 'rb'))
        return [LSOA_dist_old, LSOA_dist_2021]
    
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


def detect_file_format(dataframe):
    """
    Detect the format of the prescription dataframe.
    
    Args:
        dataframe: Pandas DataFrame containing prescription data
    
    Returns:
        Dictionary of field mappings
    """
    fields = {}
    
    # Check for old format (numeric column names)
    if '2' in dataframe.columns and '5' in dataframe.columns and '7' in dataframe.columns and '8' in dataframe.columns:
        fields['quantityField'] = '8'
        fields['dosageField'] = '19'
        fields['costField'] = '7'
        fields['practiceField'] = '2'
        fields['itemField'] = '5'
        fields['bnfField'] = '16'
        fields['format'] = 'old'
    
    # Check for new format (named columns)
    elif 'PRACTICE_CODE' in dataframe.columns:
        fields['practiceField'] = 'PRACTICE_CODE'
        fields['format'] = 'new'
        
        # Map other fields based on available columns
        if 'TOTAL_QUANTITY' in dataframe.columns:
            fields['quantityField'] = 'TOTAL_QUANTITY'
        elif 'QUANTITY' in dataframe.columns:
            fields['quantityField'] = 'QUANTITY'
        
        if 'ACTUAL_COST' in dataframe.columns:
            fields['costField'] = 'ACTUAL_COST'
        elif 'COST' in dataframe.columns:
            fields['costField'] = 'COST'
        
        if 'ITEMS' in dataframe.columns:
            fields['itemField'] = 'ITEMS'
        
        if 'BNF_CODE' in dataframe.columns:
            fields['bnfField'] = 'BNF_CODE'
        
        # For dosage, use '19' if it exists, otherwise initialize to 0
        if '19' in dataframe.columns:
            fields['dosageField'] = '19'
        else:
            # We'll need to add this column later
            fields['dosageField'] = None
    
    else:
        print("Warning: Unknown dataframe format. Attempting to continue with best guess.")
        # Make a best guess based on column names
        fields['format'] = 'unknown'
        
        for col in dataframe.columns:
            col_lower = col.lower()
            if 'quantity' in col_lower:
                fields['quantityField'] = col
            elif 'cost' in col_lower:
                fields['costField'] = col
            elif 'practice' in col_lower:
                fields['practiceField'] = col
            elif 'item' in col_lower:
                fields['itemField'] = col
            elif 'bnf' in col_lower and 'code' in col_lower:
                fields['bnfField'] = col
    
    return fields


def prepare_dataframe(dataframe, fields):
    """
    Prepare the dataframe for processing by ensuring all required fields are present.
    
    Args:
        dataframe: Pandas DataFrame containing prescription data
        fields: Dictionary of field mappings
    
    Returns:
        Prepared DataFrame
    """
    # Make a copy to avoid modifying the original
    df = dataframe.copy()
    
    # Add dosage field if it doesn't exist
    if fields['dosageField'] is None:
        df['19'] = 0  # Initialize dosage to 0
        fields['dosageField'] = '19'
    
    return df, fields


def calculateTemporalMetrics_LSOA(all_presc, mappings_dir, old=True, year=None):
    """
    Calculate temporal metrics at LSOA level.
    
    Args:
        all_presc: DataFrame containing prescription data
        mappings_dir: Directory containing mapping files
        old: Legacy parameter for backward compatibility (if True, uses old format logic)
        year: Year of the data (for selecting appropriate LSOA mapping, overrides 'old' parameter)
    
    Returns:
        Tuple of (quantity, costs, dosage, items) dictionaries by LSOA
    """
    LSOA_dosage = {}
    LSOA_costs = {}
    LSOA_items = {}
    LSOA_quantity = {}
    
    # If year is specified, use new enhanced logic
    if year is not None:
        # Detect the format of the dataframe
        fields = detect_file_format(all_presc)
        
        # Prepare the dataframe
        prepared_df, fields = prepare_dataframe(all_presc, fields)
        
        # Load appropriate LSOA mapping based on year
        LSOA_map = load_lsoa_mappings(mappings_dir, year)
        
        # Extract field names
        quantityField = fields['quantityField']
        dosageField = fields['dosageField']
        costField = fields['costField']
        practiceField = fields['practiceField']
        itemField = fields['itemField']
        
        # Process prescriptions by practice
        for name, group in prepared_df.groupby(practiceField):
            total_dosage = np.sum(group[dosageField]) if dosageField in group.columns else 0
            total_cost = np.sum(group[costField])
            total_quantity = np.sum(group[quantityField])
            total_items = np.sum(group[itemField])
            
            if name in LSOA_map:        
                for k in LSOA_map[name]:
                    if k not in LSOA_dosage:
                        LSOA_dosage[k] = 0.0
                        LSOA_costs[k] = 0.0
                        LSOA_quantity[k] = 0.0
                        LSOA_items[k] = 0.0
                    LSOA_dosage[k] += float(total_dosage) * float(LSOA_map[name][k])
                    LSOA_quantity[k] += float(total_quantity) * float(LSOA_map[name][k])
                    LSOA_items[k] += float(total_items) * float(LSOA_map[name][k])
                    LSOA_costs[k] += float(total_cost) * float(LSOA_map[name][k])
    
    else:
        # Legacy logic for backward compatibility
        [LSOA_dist_old, LSOA_dist_2021] = load_lsoa_mappings(mappings_dir=mappings_dir)

        # At this time we are using the same map for all files. Ideally, every year needs to have a different map.
        if old:
            quantityField = '8'
            dosageField = '19'
            costField = '7'
            practiceField = '2'
            itemField = '5'
            LSOA_map = LSOA_dist_old
        else:
            quantityField = 'TOTAL_QUANTITY'
            dosageField = '19'
            costField = 'ACTUAL_COST'
            practiceField = 'PRACTICE_CODE'
            itemField = 'ITEMS'
            LSOA_map = LSOA_dist_2021

        for name, group in all_presc.groupby(practiceField):
            total_dosage = np.sum(group[dosageField])
            total_cost = np.sum(group[costField])
            total_quantity = np.sum(group[quantityField])
            total_items = np.sum(group[itemField])

            if name in LSOA_map:        
                for k in LSOA_map[name]:
                    if k not in LSOA_dosage:
                        LSOA_dosage[k] = 0.0
                        LSOA_costs[k] = 0.0
                        LSOA_quantity[k] = 0.0
                        LSOA_items[k] = 0.0
                    LSOA_dosage[k] += float(total_dosage) * float(LSOA_map[name][k])
                    LSOA_quantity[k] += float(total_quantity) * float(LSOA_map[name][k])
                    LSOA_items[k] += float(total_items) * float(LSOA_map[name][k])
                    LSOA_costs[k] += float(total_cost) * float(LSOA_map[name][k])
    
    return LSOA_quantity, LSOA_costs, LSOA_dosage, LSOA_items

def writeResultFiles(monthly_borough_quantity_new, monthly_borough_dosage_new, monthly_borough_costs_new, monthly_borough_items_new, diseases, output_dir, mappings_dir, isOld=False, year=None):
    """
    Write result files for each disease.
    
    Args:
        monthly_borough_quantity_new: Dictionary of quantities by month, disease, and LSOA
        monthly_borough_dosage_new: Dictionary of dosages by month, disease, and LSOA
        monthly_borough_costs_new: Dictionary of costs by month, disease, and LSOA
        monthly_borough_items_new: Dictionary of items by month, disease, and LSOA
        diseases: List of diseases to process
        output_dir: Directory to write output files
        mappings_dir: Directory containing mapping files
        isOld: Legacy parameter for backward compatibility
        year: Year of the data (for selecting appropriate patient population)
    """
    # Get LSOA patient population with enhanced functionality
    if year is not None:
        LSOA_patient_pop = prepare_lsoa_GP_population(mappings_dir, year=year)
    else:
        LSOA_patient_pop = prepare_lsoa_GP_population(mappings_dir, isOld=isOld)
    
    for disease in tqdm(diseases):
        disease_dict = {'YYYYMM': [], 'LSOA_CODE': [], 'Total_quantity': [], 'Dosage_ratio': [], 
                        'Total_cost': [], 'Total_items': [], 'Patient_count': []}
        
        for yyyymm in monthly_borough_dosage_new:
            for LSOA_CODE in monthly_borough_dosage_new[yyyymm][disease]:
                if LSOA_CODE[0] == 'E':  # England LSOAs start with 'E'
                    disease_dict['YYYYMM'].append(yyyymm)
                    disease_dict['LSOA_CODE'].append(LSOA_CODE)
                    disease_dict['Total_quantity'].append(monthly_borough_quantity_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Dosage_ratio'].append(monthly_borough_dosage_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_cost'].append(monthly_borough_costs_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_items'].append(monthly_borough_items_new[yyyymm][disease][LSOA_CODE])
                    
                    # Add patient count if available, otherwise use 0
                    if LSOA_CODE in LSOA_patient_pop:
                        disease_dict['Patient_count'].append(LSOA_patient_pop[LSOA_CODE])
                    else:
                        print(f"Warning: No patient count for LSOA {LSOA_CODE}")
                        disease_dict['Patient_count'].append(0)
        
        disease_df = pd.DataFrame.from_dict(disease_dict)
        filename = os.path.join(output_dir, f"{disease}_V4.csv.gz")
        disease_df.to_csv(filename, index=False, compression='gzip')

def calculateTemporalMetrics_LSOA_opioids(all_presc, mappings_dir, old=True, year=None):
    """
    Calculate temporal metrics at LSOA level for opioids.
    
    Args:
        all_presc: DataFrame containing prescription data
        mappings_dir: Directory containing mapping files
        old: Legacy parameter for backward compatibility (if True, uses old format logic)
        year: Year of the data (for selecting appropriate LSOA mapping, overrides 'old' parameter)
    
    Returns:
        Tuple of (quantity, costs, ome, items) dictionaries by LSOA
    """
    LSOA_costs = {}
    LSOA_items = {}
    LSOA_quantity = {}
    LSOA_ome = {}
    
    # If year is specified, use new enhanced logic
    if year is not None:
        # Detect the format of the dataframe
        fields = detect_file_format(all_presc)
        
        # Prepare the dataframe
        prepared_df, fields = prepare_dataframe(all_presc, fields)
        
        # Load appropriate LSOA mapping based on year
        LSOA_map = load_lsoa_mappings(mappings_dir, year)
        
        # Extract field names
        quantityField = fields['quantityField']
        costField = fields['costField']
        practiceField = fields['practiceField']
        itemField = fields['itemField']
        omeField = 'presc_ome'
        
        # Process prescriptions by practice
        for name, group in prepared_df.groupby(practiceField):
            total_ome = np.sum(group[omeField]) if omeField in group.columns else 0
            total_cost = np.sum(group[costField])
            total_quantity = np.sum(group[quantityField])
            total_items = np.sum(group[itemField])
            
            if name in LSOA_map:        
                for k in LSOA_map[name]:
                    if k not in LSOA_ome:
                        LSOA_ome[k] = 0.0
                        LSOA_costs[k] = 0.0
                        LSOA_quantity[k] = 0.0
                        LSOA_items[k] = 0.0
                    LSOA_ome[k] += float(total_ome) * float(LSOA_map[name][k])
                    LSOA_costs[k] += float(total_cost) * float(LSOA_map[name][k])
                    LSOA_quantity[k] += float(total_quantity) * float(LSOA_map[name][k])
                    LSOA_items[k] += float(total_items) * float(LSOA_map[name][k])
    
    else:
        # Legacy logic for backward compatibility
        [LSOA_dist_old, LSOA_dist_2021] = load_lsoa_mappings(mappings_dir=mappings_dir)

        # At this time we are using the same map for all files. Ideally, every year needs to have a different map.
        if old:
            quantityField = '8'
            costField = '7'
            omeField = 'presc_ome'
            itemField = '5'
            practiceField = '2'
            LSOA_map = LSOA_dist_old  # Fixed: was using 2021 map for old data
        else:
            quantityField = 'TOTAL_QUANTITY'
            costField = 'ACTUAL_COST'
            omeField = 'presc_ome'
            itemField = 'ITEMS'
            practiceField = 'PRACTICE_CODE'
            LSOA_map = LSOA_dist_2021

        for name, group in all_presc.groupby(practiceField):
            total_ome = np.sum(group[omeField])
            total_cost = np.sum(group[costField])
            total_quantity = np.sum(group[quantityField])
            total_items = np.sum(group[itemField])
            if name in LSOA_map:        
                for k in LSOA_map[name]:
                    if k not in LSOA_ome:
                        LSOA_ome[k] = 0.0
                        LSOA_costs[k] = 0.0
                        LSOA_quantity[k] = 0.0
                        LSOA_items[k] = 0.0
                    LSOA_ome[k] += float(total_ome) * float(LSOA_map[name][k])
                    LSOA_costs[k] += float(total_cost) * float(LSOA_map[name][k])
                    LSOA_quantity[k] += float(total_quantity) * float(LSOA_map[name][k])
                    LSOA_items[k] += float(total_items) * float(LSOA_map[name][k])
    
    return LSOA_quantity, LSOA_costs, LSOA_ome, LSOA_items


def writeResultFiles_opioid(monthly_borough_quantity_new, monthly_borough_dosage_new, monthly_borough_costs_new, monthly_borough_items_new, diseases, output_dir, mappings_dir, year=None):
    """
    Write result files for opioids.
    
    Args:
        monthly_borough_quantity_new: Dictionary of quantities by month, disease, and LSOA
        monthly_borough_dosage_new: Dictionary of OME values by month, disease, and LSOA
        monthly_borough_costs_new: Dictionary of costs by month, disease, and LSOA
        monthly_borough_items_new: Dictionary of items by month, disease, and LSOA
        diseases: List of diseases to process
        output_dir: Directory to write output files
        mappings_dir: Directory containing mapping files
        year: Year of the data (for selecting appropriate patient population)
    """
    # Get LSOA patient population for the specified year
    LSOA_patient_pop = prepare_lsoa_GP_population(mappings_dir, year=year)
    
    for disease in tqdm(diseases):
        disease_dict = {'YYYYMM': [], 'LSOA_CODE': [], 'Total_quantity': [], 'OME': [], 
                        'Total_cost': [], 'Total_items': [], 'Patient_count': []}
        
        for yyyymm in monthly_borough_dosage_new:
            for LSOA_CODE in monthly_borough_dosage_new[yyyymm][disease]:
                if LSOA_CODE[0] == 'E':  # England LSOAs start with 'E'
                    disease_dict['YYYYMM'].append(yyyymm)
                    disease_dict['LSOA_CODE'].append(LSOA_CODE)
                    disease_dict['Total_quantity'].append(monthly_borough_quantity_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['OME'].append(monthly_borough_dosage_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_cost'].append(monthly_borough_costs_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_items'].append(monthly_borough_items_new[yyyymm][disease][LSOA_CODE])
                    
                    # Add patient count if available, otherwise use 0
                    if LSOA_CODE in LSOA_patient_pop:
                        disease_dict['Patient_count'].append(LSOA_patient_pop[LSOA_CODE])
                    else:
                        print(f"Warning: No patient count for LSOA {LSOA_CODE}")
                        disease_dict['Patient_count'].append(0)
        
        disease_df = pd.DataFrame.from_dict(disease_dict)
        filename = os.path.join(output_dir, f"{disease}_V4.csv.gz")
        disease_df.to_csv(filename, index=False, compression='gzip')