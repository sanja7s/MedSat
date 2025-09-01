
from matching.utils import *
import argparse
import glob 
import pandas as pd
import sys
from matching.drugMatching import DrugMatcher
from sources.downloader import Downloader
from tqdm import tqdm
from matching.commonFunc import writeResultFiles, calculateTemporalMetrics_LSOA
from matching.commonFunc import detect_file_format
from matching.parallel_handler import try_parallel_processing, handle_info_request

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d' , '--drugs' ,nargs="+" ,help="list of drug names you need prescription prevalence for. Can be a list of single item e.g ['ibuprofen'] ")
    parser.add_argument('-s', "--start" , help="start year and month, format YYYYMM")
    parser.add_argument('-e', "--end" , help="end year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir" , help="Directory for output files, default ../data_prep/")
    
    # Parallel processing arguments (backward compatible)
    parser.add_argument('--cores', type=int, default=None, help='Number of CPU cores to use (default: auto)')
    parser.add_argument('--serial', action='store_true', help='Force serial processing')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark comparing serial vs parallel')
    parser.add_argument('--info', action='store_true', help='Show system resources and processing recommendations')

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    args = parser.parse_args()
    
    # Handle info request
    if handle_info_request(args):
        sys.exit(0)

    drug_list = args.drugs
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

    print (f'Running for {drug_list} between months {start} and {end}. The following files were selected \n\n\n')
    for f in files_sub:
        print(f)

    # Try parallel processing
    if try_parallel_processing('drug', args, files_sub, 
                              drug_list=drug_list, 
                              mappings_dir='./mappings/', 
                              output_dir=output_dir):
        sys.exit(0)

    drugMatcher = DrugMatcher(mappings_dir='./mappings/', output_dir=output_dir)
    DiseaseDrugs, drugMap = drugMatcher.DrugMatching(drug_list)
    print(drugMap)

    monthly_borough_dosage_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}


    #Compute prevalence over selected files

    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print("Working with month  " + month)
        
        monthly_borough_dosage_new[month] = {}
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}

        pdp = pd.read_csv(f,compression='gzip')
        
        # Detect file format and get appropriate field mappings
        fields = detect_file_format(pdp)
        bnf_field = fields['bnfField']
        old = (fields['format'] == 'old')
        
        for drugname in tqdm(drugMap):
            print("Working with drug  " + drugname)
            monthly_borough_dosage_new[month][drugname] = {}
            monthly_borough_costs_new[month][drugname] = {}
            monthly_borough_quantity_new[month][drugname] = {}
            monthly_borough_items_new[month][drugname] = {}


            drugs = drugMap[drugname]
            
            drug_prescriptions = pdp.loc[pdp[bnf_field].isin(drugs)] #Subset of prescriptions from drugs
            print(f"found {len(drug_prescriptions)} rows for {len(drugs)} variants of {drugname}")

            monthly_borough_quantity_new[month][drugname] , monthly_borough_costs_new[month][drugname], monthly_borough_dosage_new[month][drugname]  , monthly_borough_items_new[month][drugname] = calculateTemporalMetrics_LSOA(drug_prescriptions, mappings_dir='./mappings/', old=old)


    print("Done computing LSOA level prescription prevalences, writing files")


    writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new , list(drugMap.keys()) ,output_dir , mappings_dir='./mappings/')
    drugMatcher.dumpDrugs(DiseaseDrugs)

    print("Finished processing !!!!! ")
