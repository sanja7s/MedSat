
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


def func_ome(df,drugBNF,ome_map,quantity_field):
    df['presc_ome'] = df[quantity_field] *df['15']*ome_map[drugBNF]
    return df

def calculateOME(pdp,ome_map,code_field, quantity_field):
    pdp['presc_ome'] = 0.0
    print(code_field  , quantity_field)
    return pdp.groupby(code_field ,as_index=False).apply(lambda df: func_ome(df , df.name, ome_map ,quantity_field))

def makeOMEmap():
    ome = pd.read_csv('../mappings/ome_rossano.csv')
    ome_map = {}
    for index,  row in ome.iterrows():
        ome_map[row['bnf']] = row['ome_multiplier']
    return ome_map

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


def calculateTemporalMetrics_LSOA_opioids(all_presc , old = True):
    LSOA_costs = {}
    LSOA_items = {}
    LSOA_quantity = {}
    LSOA_ome = {}


    LSOA_patient_count = {}
    fail = 0.0
    LSOA_map = {}
    [LSOA_dist_old , LSOA_dist_2021] = loadLSOA_mappings()

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


def writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new ,diseases,output_dir):
    LSOA_patient_pop = prepare_lsoa_GP_population()
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
