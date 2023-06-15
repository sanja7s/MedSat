
from utils import *
import argparse
import pandas as pd
import sys
from sources.downloader import Downloader
from tqdm import tqdm
from matching.commonFunc import writeResultFiles, calculateTemporalMetrics_LSOA
import json 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l' , '--list' ,nargs="+" ,help="json file in a correct format")
    parser.add_argument('-s', "--start" , help="start year and month, format YYYYMM")
    parser.add_argument('-e', "--end" , help="end year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir" , help="Directory for output files, default ../data_prep/")

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    args = parser.parse_args()

    drug_list_json = args.list[0]

    start = str(args.start)
    end = str(args.end)

    odir = args.output_dir

    if odir:
        print('overriding output dir')
        output_dir = odir

    downloader = Downloader(sourcesFile="sources/serialized_file_paths.json" , download_dir=input_dir)
    selected_files = []
    try:
        selected_files = downloader.download_range(start , end)
    except:
        print("Failed download")
        exit(-1)


    files_sub = selected_files

    print (f'Running for suplied drugs between months {start} and {end}. The following files were selected \n\n\n')
    for f in files_sub:
        print(f)

    drugMap = {}

    try: 
        drugMap = json.load(open(drug_list_json , 'r'))
    except:
        print(f"Failed to open {drug_list_json}")
        exit(-1)

    print(drugMap)

    monthly_borough_dosage_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}


    #Compute prevalence over selected files

    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print("Working with month  " + month)
        old = False
        
        monthly_borough_dosage_new[month] = {}
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}

        pdp = pd.read_csv(f,compression='gzip')
        for drugname in tqdm(drugMap):
            print("Working with drug  " + drugname)
            monthly_borough_dosage_new[month][drugname] = {}
            monthly_borough_costs_new[month][drugname] = {}
            monthly_borough_quantity_new[month][drugname] = {}
            monthly_borough_items_new[month][drugname] = {}


            drugs = drugMap[drugname]
            
            drug_prescriptions = pdp.loc[pdp['16'].isin(drugs)] #Subset of prescriptions from drugs
            print(f"found {len(drug_prescriptions)} rows for {len(drugs)} variants of {drugname}")

            monthly_borough_quantity_new[month][drugname] , monthly_borough_costs_new[month][drugname], monthly_borough_dosage_new[month][drugname]  , monthly_borough_items_new[month][drugname] = calculateTemporalMetrics_LSOA(drug_prescriptions, mappings_dir='./mappings/', old=old)


    print("Done computing LSOA level prescription prevalences, writing files")


    writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new , list(drugMap.keys()) ,output_dir , mappings_dir='./mappings/')
    print("Finished processing !!!!! ")
