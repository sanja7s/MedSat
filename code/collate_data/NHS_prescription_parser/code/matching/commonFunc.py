import json
import argparse
from tqdm import tqdm
import numpy as np
import pandas as pd



def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    
def func_ome(df,drugBNF,ome_map,quantity_field):
    df['presc_ome'] = df[quantity_field] *df['15']*ome_map[drugBNF]
    return df

def calculateOME(pdp,ome_map,code_field, quantity_field):
    pdp['presc_ome'] = 0.0
    print(code_field  , quantity_field)
    return pdp.groupby(code_field ,as_index=False).apply(lambda df: func_ome(df , df.name, ome_map ,quantity_field))

def makeOMEmap():
    ome = pd.read_csv(mappings_dir + 'ome_rossano.csv')
    ome_map = {}
    for index,  row in ome.iterrows():
        ome_map[row['bnf']] = row['ome_multiplier']
    return ome_map

def prepare_lsoa_GP_population(mappings_dir , isOld):
    LSOA_patient_pop = {}
    if isOld:
        LSOA_patients_map = json.load(open(mappings_dir + 'GPs_2013.json','r'))
    else:
        LSOA_patients_map = json.load(open(mappings_dir + 'GPs.json','r'))
    for GP in tqdm(LSOA_patients_map):
        for lsoa in LSOA_patients_map[GP]['Patient_registry_LSOA']:
            if lsoa not in LSOA_patient_pop:
                LSOA_patient_pop[lsoa] = LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
            else:
                LSOA_patient_pop[lsoa] += LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
    return LSOA_patient_pop


def load_lsoa_mappings(mappings_dir):
    LSOA_dist_old = json.load(open(mappings_dir + 'GP_LSOA_PATIENTSDIST.json', 'rb'))
    LSOA_dist_2021 = json.load(open(mappings_dir + 'GP_LSOA_PATIENTSDIST_2021.json', 'rb'))
    return [LSOA_dist_old, LSOA_dist_2021]


def calculateTemporalMetrics_LSOA( all_presc , mappings_dir , old = True):
    LSOA_dosage = {}
    LSOA_costs = {}
    LSOA_items = {}
    LSOA_quantity = {}

    LSOA_patient_count = {}
    fail = 0.0
    LSOA_map = {}
    [LSOA_dist_old , LSOA_dist_2021] = load_lsoa_mappings(mappings_dir=mappings_dir)

    #At this time we are using the same map for all files. Ideally, every year needs to have a different map.
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
                LSOA_dosage[k]+= float(total_dosage)*float(LSOA_map[name][k])
                LSOA_quantity[k]+= float(total_quantity)*float(LSOA_map[name][k])
                LSOA_items[k]+= float(total_items)*float(LSOA_map[name][k])
                LSOA_costs[k]+= float(total_cost)*float(LSOA_map[name][k])
    
    return  LSOA_quantity , LSOA_costs, LSOA_dosage , LSOA_items

def writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new ,diseases, output_dir, mappings_dir ,isOld=False):
    LSOA_patient_pop = prepare_lsoa_GP_population(mappings_dir,isOld)
    for disease in tqdm(diseases):
        disease_dict = {'YYYYMM':[] , 'LSOA_CODE' : [] , 'Total_quantity' : [] ,'Dosage_ratio' :[] , 'Total_cost' : [] ,'Total_items': [] , 'Patient_count' : []}
        for yyyymm in monthly_borough_dosage_new:
            for LSOA_CODE in monthly_borough_dosage_new[yyyymm][disease]:
                if LSOA_CODE[0] == 'E':
                    disease_dict['YYYYMM'].append(yyyymm)
                    disease_dict['LSOA_CODE'].append(LSOA_CODE)
                    disease_dict['Total_quantity'].append(monthly_borough_quantity_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Dosage_ratio'].append(monthly_borough_dosage_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_cost'].append(monthly_borough_costs_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_items'].append(monthly_borough_items_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Patient_count'].append(LSOA_patient_pop[LSOA_CODE])
        disease_df = pd.DataFrame.from_dict(disease_dict)
        filename = output_dir + disease+'_V4.csv.gz'
        disease_df.to_csv(filename,index=False,compression='gzip')

def calculateTemporalMetrics_LSOA_opioids(all_presc , mappings_dir ,old = True):
    LSOA_costs = {}
    LSOA_items = {}
    LSOA_quantity = {}
    LSOA_ome = {}


    LSOA_patient_count = {}
    fail = 0.0
    LSOA_map = {}
    [LSOA_dist_old , LSOA_dist_2021] = load_lsoa_mappings(mappings_dir=mappings_dir)

    #At this time we are using the same map for all files. Ideally, every year needs to have a different map.
    if old:
        quantityField = '8'
        costField = '7'
        omeField = 'presc_ome'
        itemField = '5'
        practiceField = '2'
        LSOA_map = LSOA_dist_2021
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
                LSOA_ome[k]+= float(total_ome)*float(LSOA_map[name][k])
                LSOA_costs[k]+= float(total_cost)*float(LSOA_map[name][k])
                LSOA_quantity[k]+= float(total_quantity)*float(LSOA_map[name][k])
                LSOA_items[k]+= float(total_items)*float(LSOA_map[name][k])
    
    return  LSOA_quantity  , LSOA_costs,  LSOA_ome , LSOA_items


def writeResultFiles_opioid(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new ,diseases,output_dir , mappings_dir):
    LSOA_patient_pop = prepare_lsoa_GP_population(mappings_dir=mappings_dir)
    for disease in tqdm(diseases):
        disease_dict = {'YYYYMM':[] , 'LSOA_CODE' : [] , 'Total_quantity' : [] ,'OME' :[] , 'Total_cost' : [] ,'Total_items': [] , 'Patient_count' : []}
        for yyyymm in monthly_borough_dosage_new:
            for LSOA_CODE in monthly_borough_dosage_new[yyyymm][disease]:
                if LSOA_CODE[0] == 'E':
                    disease_dict['YYYYMM'].append(yyyymm)
                    disease_dict['LSOA_CODE'].append(LSOA_CODE)
                    disease_dict['Total_quantity'].append(monthly_borough_quantity_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['OME'].append(monthly_borough_dosage_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_cost'].append(monthly_borough_costs_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Total_items'].append(monthly_borough_items_new[yyyymm][disease][LSOA_CODE])
                    disease_dict['Patient_count'].append(LSOA_patient_pop[LSOA_CODE])
        disease_df = pd.DataFrame.from_dict(disease_dict)
        filename = output_dir + disease+'_V4.csv.gz'
        disease_df.to_csv(filename,index=False,compression='gzip')