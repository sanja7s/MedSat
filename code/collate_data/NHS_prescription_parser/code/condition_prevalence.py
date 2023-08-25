
from matching.utils import *
import argparse
import glob 
import pandas as pd
from matching.commonFunc import str2bool
from matching.commonFunc import writeResultFiles, calculateTemporalMetrics_LSOA
from matching.drugMatching import DrugMatcher
from sources.downloader import Downloader
from tqdm import tqdm



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c' , '--conditions' ,nargs="+" ,help="list of a conditions you need prescription prevalence for. Can be a list of single item ['item'] ")
    parser.add_argument('--isCat' , type=str2bool , default=False, help=" Boolean flag to notify if the list is a set of conditions or categories. Default is False, implying conditions ")
    parser.add_argument('-s', "--start" , help="start year and month, format YYYYMM")
    parser.add_argument('-e', "--end" , help="end year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir" , help="Directory for output files, default ../data_prep/")

    input_dir = "./prescriptionfiles/"
    output_dir = "../data_prep/"
    args = parser.parse_args()

    conditions = args.conditions
    print("Running for : ",conditions)
    
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

    print (f'Running for {conditions} between months {start} and {end}. The following files were selected \n\n\n')
    for f in files_sub:
        print(f)

    
    matcher = DrugMatcher(mappings_dir = './mappings/')

    DiseaseDrugs, drugMap = matcher.DrugMatching(conditions)
    
    print(DiseaseDrugs)
    
    for k in drugMap:
        print(k , drugMap[k])

    monthly_borough_dosage_new = {}
    monthly_borough_costs_new = {}
    monthly_borough_quantity_new = {}
    monthly_borough_items_new = {}


    #Compute prevalence over selected files

    for f in tqdm(files_sub):
        month = f.split('/')[-1].split('.')[0]
        print("Working with file  " + f)
        old = False
        
        monthly_borough_dosage_new[month] = {}
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}

        pdp = pd.read_csv(f,compression='gzip')
        for disease in tqdm(drugMap):
            print("Working with disease  " + disease)
            monthly_borough_dosage_new[month][disease] = {}
            monthly_borough_costs_new[month][disease] = {}
            monthly_borough_quantity_new[month][disease] = {}
            monthly_borough_items_new[month][disease] = {}


            drugs = drugMap[disease]
            opioids = pdp.loc[pdp['16'].isin(drugs)] #Original opioids

            monthly_borough_quantity_new[month][disease] , monthly_borough_costs_new[month][disease], monthly_borough_dosage_new[month][disease]  , monthly_borough_items_new[month][disease] = calculateTemporalMetrics_LSOA(opioids, mappings_dir='./mappings/', old = old)


    print("Done computing LSOA level prescription prevalences, writing files")


    writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new , conditions , output_dir,  mappings_dir='./mappings/' , isOld = old)
    print("Finished processing !!!!! ")
