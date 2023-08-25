from matching.utils import *
import argparse
import glob 
import networkx as nx
import pandas as pd
import sys

def getMonthList(files):
    monthListAll = []
    for f in files: 
        weight = re.findall(r'[0-9]*\.?[0-9]+', f)
        monthListAll.append(weight[-1])
    #     print(weight)
    monthListAll = list(set(monthListAll))
    monthListAll.sort()
    return monthListAll

def getOpenGPs():
    GP_META = pd.read_csv('../mappings/epraccur_2021.csv',header=None)
    GP_META.rename(columns={0:'BP_code',
                        1:'Name',
                        2:'Grouping',
                        3:'National_geo',
                        4:'Addr1',
                        5:'Addr2',
                        6:'Addr3',
                        7: 'Addr4',
                        8:'Addr5',
                        9:'Postcode',
                        10:'Open',
                        11:'Closed',
                        12:'Status',
                        13:'Org type code',
                        14:'Commissioner',
                        15:'Join provider',
                        16:'Left provider',
                        17:'Contact',
                        18:'Null1',
                        19:'Null2',
                        20:'Null3',
                        21:'Amended',
                        22:'Null4',
                        23:'Provider',
                        24:'Null5',
                        25:'Setting',
                        26:'Null6'}, 
                 inplace=True)
    Open_filtered_GPs = {}
    for index,row in GP_META.iterrows():
        if row ['Setting'] == 4 and row['Status'] =='A':
            Open_filtered_GPs[row['BP_code']] = row['Postcode'].strip()
    return Open_filtered_GPs


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--start" , help="start year and month, format YYYYMM")
    parser.add_argument('-e', "--end" , help="end year and month, format YYYYMM")
    parser.add_argument('-odir', "--output_dir" , help="Directory for output files, default /10TBDrive_2/sagar/NHS_data/serialized/")
    parser.add_argument('-idir', "--input_dir" , help="Directory for input nhs files, default: /10TBDrive_2/sagar/NHS_data/. Make sure that you have NHS files downloaded here. There is no sanity check here.")

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


    files = glob.glob(input_dir + '/*.zip')
    
    monthList = getMonthList(files)
    start_i = 0
    end_i = len(monthList)

    
    if start:
        for i in range(len(monthList)):
            if monthList[i] == start:
                start_i = i
    if end:
        for i in range(len(monthList)):
            if monthList[i] == end:
                end_i = i

    files_sub = monthList[start_i:end_i+1]

    print (f'Serializating between months {start} and {end}. The following files were selected \n\n\n')



    #Compute prevalence over selected files
    Open_filtered_GPs = getOpenGPs()
    for month in tqdm(files_sub):
        filename = odir + month + '.gz'
        print("Generating file: "+str(filename))
        pdp = pd.read_csv( idir +'EPD_'+str(month) +'.zip')
        pdp = pdp.dropna()
        pdp_filtered = pdp[pdp['PRACTICE_CODE'].isin(Open_filtered_GPs.keys())].copy(deep=True)
    #         pdp_filtered = pdp[~pdp['BNF_CHAPTER_PLUS_CODE'].isin(cat_filters)]
        pdp_filtered = doImportantMappings_new(pdp_filtered)
        pdp_filtered.to_csv(filename,compression='gzip')
        del pdp_filtered
        del pdp
