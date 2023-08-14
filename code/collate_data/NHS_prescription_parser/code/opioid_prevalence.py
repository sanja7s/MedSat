
from utils import *
import argparse
import glob 
import networkx as nx
import pandas as pd
import sys

mappings_dir = '../mappings/'
input_dir = '/10TBDrive_2/sagar/NHS_data/serialized/'
output_dir = '../data_prep/'


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')




def DrugMatching(conditions, isCat=False):
    drug_association_graph = nx.read_gexf(mappings_dir + 'drug_association_graph.gexf')
    drug_cat_association_graph = nx.read_gexf(mappings_dir + 'category_association_graph.gexf')
    chem = pd.read_csv(mappings_dir + 'CHEM_MASTER_MAP.csv')

    DiseaseDrugs = {}
    for d in tqdm(conditions):
        drugs = findDrugsForDisease(drug_association_graph,d ,chem)
    #     drugs = findDrugsByName(drug_association_graph,d ,chem)
        for drug in drugs:
            DiseaseDrugs[drug] = {}
            DiseaseDrugs[drug]['chemName'] = drugs[drug]['name']
            DiseaseDrugs[drug]['drugName'] = d
    
    disease_drug_map = {}
    for k in DiseaseDrugs:
        if DiseaseDrugs[k]['drugName'] not in disease_drug_map:
            disease_drug_map[DiseaseDrugs[k]['drugName']] = []
        disease_drug_map[DiseaseDrugs[k]['drugName']].append(k)
    return DiseaseDrugs , disease_drug_map

def dumpDrugs(DiseaseDrugs):
    drug_map_dict = {'BNF_code':[], 'Drug_name':[] , 'Mapped_Drug': []}
    for k in DiseaseDrugs:
        drug_map_dict['BNF_code'].append(k)
        drug_map_dict['Drug_name'].append(DiseaseDrugs[k]['chemName'])
        drug_map_dict['Mapped_Drug'].append(DiseaseDrugs[k]['drugName'])
    drug_map_df = pd.DataFrame.from_dict(drug_map_dict)    
    drug_map_df.to_csv(output_dir + 'Drug_map.csv',index=False)

def loadLSOA_mappings():
    LSOA_dist_old = json.load(open(mappings_dir + 'GP_LSOA_PATIENTSDIST.json','rb'))
    LSOA_dist_2021 = json.load(open(mappings_dir + 'GP_LSOA_PATIENTSDIST_2021.json','rb'))
    return [LSOA_dist_old , LSOA_dist_2021]

def prepare_lsoa_GP_population():
    LSOA_patient_pop = {}
    LSOA_patients_map = json.load(open(mappings_dir + 'GPs.json','r'))
    for GP in tqdm(LSOA_patients_map):
        for lsoa in LSOA_patients_map[GP]['Patient_registry_LSOA']:
            if lsoa not in LSOA_patient_pop:
                LSOA_patient_pop[lsoa] = LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
            else:
                LSOA_patient_pop[lsoa] += LSOA_patients_map[GP]['Patient_registry_LSOA'][lsoa]
    return LSOA_patient_pop




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--start" , help="start year and month, format YYYYMM")
    parser.add_argument('-e', "--end" , help="end year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir" , help="Directory for output files, default ../data_prep/")
    parser.add_argument('-idir', "--input_dir" , help="Directory for input nhs files, default: ../../BL_Work/openPrescribe/serialized/. Make sure that you have NHS files downloaded here. There is no sanity check here.")

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    start = str(args.start)
    end = str(args.end)

    idir = args.input_dir
    odir = args.output_dir

    if idir:
        print('overriding input dir')
        input_dir = idir
    if odir:
        print('overriding input dir')
        output_dir = odir


    files = glob.glob(input_dir + '/*.gz')
    files.sort()
    start_i = 0
    end_i = len(files)
    
    if start:
        for i in range(len(files)):
            year = files[i].split('/')[-1].split('.')[0].strip()
            if year == start:
                start_i = i
    if end:
        for i in range(len(files)):
            year = files[i].split('/')[-1].split('.')[0].strip()
            if year == end:
                end_i = i

    files_sub = files[start_i:end_i+1]
    
    ome_map = makeOMEmap()

    print (f'Computing Opioid OMEs between months {start} and {end}. The following files were selected \n\n\n')
    for f in files_sub:
        print(f)

    monthly_borough_dosage_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}



    #Compute prevalence over selected files

    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print("Working with month  " + month)
        if int(month) > 201312:
            old = False
            code_field = 'BNF_CODE'
            dosageField = 'TOTAL_QUANTITY'
        else:
            old = True
            code_field = '3'
            dosageField = '8'
        
        monthly_borough_dosage_new[month] = {}
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}

        pdp = pd.read_csv(f,compression='gzip')
        opioids = pdp[pdp[code_field].isin(ome_map.keys())]
        opioids = calculateOME(opioids , ome_map ,code_field , dosageField) 

        monthly_borough_dosage_new[month]['opioids'] = {}
        monthly_borough_costs_new[month]['opioids'] = {}
        monthly_borough_quantity_new[month]['opioids'] = {}
        monthly_borough_items_new[month]['opioids'] = {}
        
        monthly_borough_quantity_new[month]['opioids'] , monthly_borough_costs_new[month]['opioids'], monthly_borough_dosage_new[month]['opioids']  , monthly_borough_items_new[month]['opioids'] = calculateTemporalMetrics_LSOA_opioids(opioids, old)


    print("Done computing LSOA level prescription prevalences, writing files")


    writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new , ['opioids'],output_dir)

    print("Finished processing !!!!! ")
