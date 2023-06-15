
from utils import *
import argparse
import glob 
import networkx as nx
import pandas as pd



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c' , '--conditions' ,nargs="+" ,help="list of a conditions you need prescription prevalence for. Can be a list of single item ['item'] ")
    parser.add_argument('--isCat' , type=str2bool , default=False, help=" Boolean flag to notify if the list is a set of conditions or categories. Default is False, implying conditions ")
    parser.add_argument('-s', "--start" , help="start year and month, format YYYYMM")
    parser.add_argument('-e', "--end" , help="end year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir" , help="Directory for output files, default ../data_prep/")
    parser.add_argument('-idir', "--input_dir" , help="Directory for input nhs files, default: ../../BL_Work/openPrescribe/serialized/. Make sure that you have NHS files downloaded here. There is no sanity check here.")

    args = parser.parse_args()

    conditions = args.conditions
    print("Running for : ",conditions)
    
    start = str(args.start)
    end = str(args.end)

    idir = args.input_dir
    odir = args.output_dir

    if idir:
        print('overriding input dir')
        input_dir = idir
    if odir:
        print('overriding output dir')
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

    print (f'Running for {conditions} between months {start} and {end}. The following files were selected \n\n\n')
    for f in files_sub:
        print(f)

    

    DiseaseDrugs, drugMap = DrugMatching(conditions , args.isCat)
    
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
        if int(month) > 201312:
            old = False
        else:
            old = True
        
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

            monthly_borough_quantity_new[month][disease] , monthly_borough_costs_new[month][disease], monthly_borough_dosage_new[month][disease]  , monthly_borough_items_new[month][disease] = calculateTemporalMetrics_LSOA(opioids, old)


    print("Done computing LSOA level prescription prevalences, writing files")


    writeResultFiles(monthly_borough_quantity_new ,monthly_borough_dosage_new , monthly_borough_costs_new , monthly_borough_items_new , conditions , output_dir, old)
    dumpDrugs(DiseaseDrugs)

    print("Finished processing !!!!! ")
