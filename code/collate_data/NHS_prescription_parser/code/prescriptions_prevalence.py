
from matching.utils import *
import argparse
import glob 
import pandas as pd
import sys
from matching.commonFunc import writeResultFiles

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

    print (f'Computing Opioid OMEs between months {start} and {end}. The following files were selected \n\n\n')
    
    for f in files_sub:
        print(f)

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
        
        monthly_borough_costs_new[month] = {}
        monthly_borough_quantity_new[month] = {}
        monthly_borough_items_new[month] = {}

        pdp = pd.read_csv(f,compression='gzip')

        monthly_borough_costs_new[month]['total_prescriptions'] = {}
        monthly_borough_quantity_new[month]['total_prescriptions'] = {}
        monthly_borough_items_new[month]['total_prescriptions'] = {}
        
        monthly_borough_quantity_new[month]['total_prescriptions'] , monthly_borough_costs_new[month]['total_prescriptions'], monthly_borough_items_new[month]['total_prescriptions'] = calculateTemporalMetrics_LSOA_all(pdp, old)


    print("Done computing LSOA level prescription prevalences, writing files")


    writeResultFiles(monthly_borough_quantity_new , monthly_borough_costs_new , monthly_borough_items_new , ['total_prescriptions'],output_dir)

    print("Finished processing !!!!! ")
