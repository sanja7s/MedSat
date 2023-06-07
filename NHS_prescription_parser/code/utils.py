import pandas as pd
import geopandas as gp 
import json
from glob import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import glob
import numpy as np
import networkx as nx 





def cleanStringofUTF(string):
    my_str_as_bytes = str.encode(string,'utf-8')
    cleaned = str(my_str_as_bytes).replace('\xe8','e').replace('\xf6','o')
    return cleaned

def enrichdrugs(chem_dict , drugs):
    diabetes_drug_words = [drugs[k]['name'].lower() for k in drugs]
    for drug in chem_dict:
        Name = chem_dict[drug]['name'].replace('(','').replace(')','')
        slot1 = Name.lower().split('/')
        slot2 = Name.lower().split(' ')
        slot3 = Name.lower().split(' & ')
        common1 = set(diabetes_drug_words).intersection(slot1)
        common2 = set(diabetes_drug_words).intersection(slot2)
        common3 = set(diabetes_drug_words).intersection(slot3)
        
        if len(common1) > 0 or len(common2) > 0 or len(common3) > 0:
#             print common1 , common2 , common3
            drugs[chem_dict[drug]['code']] = {'disease':'' , 'disease_given_drug':0.0 , 'matched_disease':'', 'name':chem_dict[drug]['name'].strip() }

            
            
def makeChemDict(BNF_Chem):
    chem_dict = {}
    for index, row in BNF_Chem.iterrows():
        chem_dict[row['UNII_drugbank']] = {}
        chem_dict[row['UNII_drugbank']]['name'] = row['NAME']
        chem_dict[row['UNII_drugbank']]['code'] = row['BNF_code']
    return chem_dict
    
def getDrugCategory(categorylist, BNF_Chem, drugbankDict):
    allMatched = []
    drugs = {}
    chem_dict = makeChemDict(BNF_Chem)
    
    for k in drugbankDict:
        if len(drugbankDict[k]['Categories']) > 0:
            for cat in drugbankDict[k]['Categories']:
                matched_memo = []
                catString = cat.values()[0]#.split('\u2014')[-1]
                t = catString.lower().strip()
                for categoryString in categorylist:
                    categoryString = categoryString.lower()
                    if t.find(categoryString) >= 0:
                        matched_memo.append(categoryString)
                if k in chem_dict:
                    if len(matched_memo) > 0:# == len(categorylist):
                        allMatched.append(k)
#                         print chem_dict[k]
                        drugs[chem_dict[k]['code']] = {}
                        drugs[chem_dict[k]['code']]['name'] = chem_dict[k]['name']
                        drugs[chem_dict[k]['code']]['matched_cat'] = categorylist
    enrichdrugs(chem_dict,drugs)               
    return list(set(allMatched)) , drugs


def getDrugforDiseaseDrugbank(categorylist, BNF_Chem, drugbankDict):
    allMatched = []
    drugs = {}
    chem_dict = makeChemDict(BNF_Chem)
    
    for k in drugbankDict:
        if len(drugbankDict[k]['Associations']) > 0:
            for cat in drugbankDict[k]['Associations']:
                matched_memo = []
                catString = cat.values()[0]
                t = catString.lower().strip()
                for categoryString in categorylist:
                    categoryString = categoryString.lower()
                    if t.find(categoryString) >= 0:
                        matched_memo.append(categoryString)
                if k in chem_dict:
                    if len(matched_memo) > 0:
                        allMatched.append(k)
#                         print chem_dict[k]
                        drugs[chem_dict[k]['code']] = {}
                        drugs[chem_dict[k]['code']]['name'] = chem_dict[k]['name']
                        drugs[chem_dict[k]['code']]['matched_cat'] = categorylist
    enrichdrugs(chem_dict,drugs)               
    return  allMatched , drugs


def findDrugsForDisease(Graph, Disease, BNF_Chem ):#,threshProb):
    chem_dict = makeChemDict(BNF_Chem)
    drugs = {}
    for e in Graph.edges(data=True):
        if (cleanStringofUTF(e[1]).lower().find(Disease.lower()) >=0) or (cleanStringofUTF(e[0]).lower().find(Disease.lower()) >= 0) :
            drugNode = ''
            matchedDisease = ''
            if Graph.node[e[0]]['type'] == 'symptom':
                drugNode = e[1]
                matchedDisease = e[0]
            else:
                drugNode = e[0]
                matchedDisease = e[1]
            drugs[Graph.node[drugNode]['Id']] = {}
            drugs[Graph.node[drugNode]['Id']]['name'] = drugNode
            drugs[Graph.node[drugNode]['Id']]['matched_disease'] = matchedDisease
            drugs[Graph.node[drugNode]['Id']]['disease'] = Disease
    enrichdrugs(chem_dict,drugs)
    return drugs


def generateConfidence(drugs,Graph):
    shared = []
    All = []
    denom = max(Graph.degree().values())
    for d in drugs:
        name = drugs[d]['name']
        for e in Graph.edges(data=True):
            if Graph.node[e[0]]['type'] == 'symptom':
                if e[1] == name:
                    shared.append(Graph.degree()[e[1]]-1)
                else:
                    continue
            else:
                
                if e[0] == name:
                    shared.append(Graph.degree()[e[0]]-1)
                else:
                    continue
#     shared = [float(k) for k in shared]
    num = [k for k in shared if k > 1]

    return float(len(num)+1.0)/float(len(shared)+1.0)
#     return float(len(num))/float(len(shared)) * 10.0
#     return len(num)
                
                
def findDrugsForCategory(Graph, Cat, BNF_Chem ):#,threshProb):
    chem_dict = makeChemDict(BNF_Chem)
    drugs = {}
    for e in Graph.edges(data=True):
        if (cleanStringofUTF(e[1]).lower().find(Cat.lower()) >=0) or (cleanStringofUTF(e[0]).lower().find(Cat.lower()) >= 0) :
            drugNode = ''
            matchedDisease = ''
            if Graph.node[e[0]]['type'] == 'category':
                drugNode = e[1]
                matchedDisease = e[0]
            else:
                drugNode = e[0]
                matchedDisease = e[1]
#             print Graph.node[drugNode]['Id']
            drugs[Graph.node[drugNode]['Id']] = {}
            drugs[Graph.node[drugNode]['Id']]['name'] = drugNode
            drugs[Graph.node[drugNode]['Id']]['matched_cat'] = matchedDisease
            drugs[Graph.node[drugNode]['Id']]['category'] = Cat
    enrichdrugs(chem_dict,drugs)
    return drugs



def enrichdrugsByNames(chem_dict , drugs , drugname):
    drug_words = [drugs[k]['name'].lower() for k in drugs]
    for drug in chem_dict:
        Name = chem_dict[drug]['name'].replace('(','').replace(')','')
        slot1 = Name.lower().split('/')
        slot2 = Name.lower().split(' ')
        slot3 = Name.lower().split(' & ')
        common1 = set(drug_words).intersection(slot1)
        common2 = set(drug_words).intersection(slot2)
        common3 = set(drug_words).intersection(slot3)
        
        if len(common1) > 0 or len(common2) > 0 or len(common3) > 0:
#             print common1 , common2 , common3
            drugs[chem_dict[drug]['code']] = { 'matched_drug':drugname, 'name':chem_dict[drug]['name'].strip() }

def findDrugsByName(Graph, drugname, BNF_Chem ):#,threshProb):
    chem_dict = makeChemDict(BNF_Chem)
    drugs = {}
    for n in tqdm(Graph.nodes(data=True)):
        if n[1]['type'] == 'drug':
            if (cleanStringofUTF(n[1]['label']).lower().find(drugname.lower()) >=0) or (cleanStringofUTF(n[1]['label']).lower().find(drugname.lower()) >= 0) :
                drugs[n[1]['Id']] = {}
                drugs[n[1]['Id']]['name'] = n[1]['label']
                drugs[n[1]['Id']]['matched_drug'] = drugname
        enrichdrugsByNames(chem_dict,drugs,drugname)
    return drugs





    ### serialization methods ##### 

#Different functions to extract different data form the prescription 

import inspect
import re

def extractPostCodesDict(addrDf):
    postcodeDict = {}
    for index,row in addrDf.iterrows():
        try:
            postcodeDict[row[1]] = row[7].strip()
        except:
            print("Found invalid entry")
    return postcodeDict

def checkIndex(index):
    if index%100 == 0:
        return True
    else:
        return False

def getPC(key , postcodeDict):
    codes = []
    for k in key:
        if k in postcodeDict:
            codes.append(postcodeDict[k])
        else:
            codes.append('')
    return pd.Series(codes,index=key.index)

def getPostcode(df,postcodeDict):
    df[10] = ''
    df[10] = df.groupby(2)[2].apply(getPC,postcodeDict)   
    return df

def getDrugFamily(key, diseaseMap):
    found = 'N/A'
    for dcode in diseaseMap: 
        if key.name.find(dcode) == 0:
            found = dcode
            break
    drug = [found]*len(key)
    return pd.Series(drug,index=key.index)

def getDisease(key, diseaseMap):
    found = 'N/A'
    for dcode in diseaseMap: 
        if key.name.find(dcode) == 0:
            found = diseaseMap[dcode]['disease'].replace('\"','').replace('+',' ')
            break
    drug = [found]*len(key)
    return pd.Series(drug,index=key.index)

def getDrug(key, diseaseMap):
    found = 'N/A'
    for dcode in diseaseMap: 
        if key.name.find(dcode) == 0:
            found = diseaseMap[dcode]['chemName']
            break
    drug = [found]*len(key)
    return pd.Series(drug,index=key.index)

def getDrugPotency(key):
    name = list(set(key))
    if len(name) > 1:
        print("found synonyms")
    text= name[-1]
    found = 0.0
    switch1 = text.find('mcg')
    switch2 = text.find('mg')
    switch3 = text.find('ml')
    
    if switch1 > 0 or switch2 > 0 or switch3 > 0:
        weight = re.findall(r'[0-9]*\.?[0-9]+', text)
        if len(weight) > 0:
            found = max([float(k) for k in weight])
            if switch1 > 0:
                found = found/1000.0
    potency = [found]*len(key)
    return pd.Series(potency,index=key.index)

def countSpecificDrugs(Df, drugs,GPs):
    df_slice = Df.groupby(3)[3].apply(getDrug,drugs)
    selected = df_slice[df_slice!='N/A']
    len(selected)
    df_selected =  Df.iloc[selected.index,:]
    df_selected = df_selected[df_selected[2].isin(GPs.keys())]
    return np.sum(df_selected[5])


def countSpecificDrugCosts(Df, drugs,GPs):
    df_slice = Df.groupby(3)[3].apply(getDrug,drugs)
    selected = df_slice[df_slice!='N/A']
    len(selected)
    df_selected =  Df.iloc[selected.index,:]
    df_selected = df_selected[df_selected[2].isin(GPs.keys())]
    return np.sum(df_selected[6])

def countDrugsByCategoryList(pdp,codes):
    total_drugs = 0.0
    drugs = None
    for name , group in pdp.groupby(3):
        for dcode in codes:
            if name.find(dcode) == 0:
                total_drugs+=np.sum(group[5])
    return total_drugs

def countPrescriptionsByCategoryList(pdp,codes):
    total_drugs = 0.0
    drugs = None
    for name , group in pdp.groupby(3):
        for dcode in codes:
            if name.find(dcode) == 0:
                total_drugs+=len(group)
    return total_drugs


def countDrugsCostByCategoryList(pdp,codes):
    total_drugs = 0.0
    for name , group in pdp.groupby(3):
        for dcode in codes:
            if name.find(dcode) == 0:
                total_drugs+=np.sum(group[7])
    return total_drugs

def countDrugsCostByGenerics(pdp,codes):
    total_drugs = 0.0
    generics= pdp[pdp[20] == 'AA']
    for name , group in generics.groupby(3):
        for dcode in codes:
            if name.find(dcode) == 0:
                total_drugs+=np.sum(group[7])
    return total_drugs

def compareCostsForGenericsAndBranded(pdp,codes):
    genericsCosts = {}
    brandedCosts = {}
    for name , group in pdp.groupby(16):
        for dcode in codes:
            if name == dcode:
                generics= group[group[20] == 'AA']
                if len(generics)>0:
                    total_drugs =np.sum(group[7])
                    generic_drugs = np.sum(generics[7])
                    brandedCosts[dcode] = total_drugs - generic_drugs
                    genericsCosts[dcode] = generic_drugs
                else:
                    print("Did not find any generic drugs")
                    continue
    return brandedCosts , genericsCosts

def func_Cost(potgroup):
    
    generics= potgroup.loc[potgroup[20] == 'AA']
    nonGenerics =  potgroup.loc[potgroup[20] != 'AA']

    minCost = np.min(generics[7])
    minpotdf = generics.loc[generics[7] == minCost]
    minQuant = np.min(minpotdf[8])
    if minQuant == 0:
        normalizer = minCost
    else:
        normalizer = float(minCost)/float(minQuant)
    
    if np.isnan(normalizer):
        normalizer = 1.0
    potgroup[21] = normalizer
    
    minCostBrand = np.min(nonGenerics[7])
    minpotdfBrand = nonGenerics.loc[nonGenerics[7] == minCostBrand]
    minQuantBrand = np.min(minpotdfBrand[8])
    
    if minQuantBrand == 0:
        unitNonGenericCost = minCostBrand
    else:
        unitNonGenericCost = float(minCostBrand)/float(minQuantBrand)
    
    if np.isnan(unitNonGenericCost):
        unitNonGenericCost = 1.0
    potgroup[22] = unitNonGenericCost
    if unitNonGenericCost > normalizer:
        potgroup[23] = float(unitNonGenericCost - normalizer)*potgroup[8]    
    return potgroup

def func_Drugs(group,codes):
    return group.groupby(15,as_index=False).apply(lambda df : func_Cost(df))
    

def computeSavingsNew(pdp,codes):
    pdp[21] = 0.0
    pdp[22] = 0.0
    pdp[23] = 0.0
    return pdp.groupby(16,as_index=False).apply(lambda df: func_Drugs(df , codes))


def computeSavings(pdp,codes):
    pdp[21] = 0.0
    pdp[22] = 0.0
    pdp[23] = 0.0
    for name , group in pdp.groupby(16):
        #we can remove this to allow computing savings across all drugs
        if name in codes:
            for pot , potgroup in group.groupby(15):
                generics= potgroup.loc[potgroup[20] == 'AA']
                nonGenerics =  potgroup.loc[potgroup[20] != 'AA']

                minCost = np.min(generics[7])
                minpotdf = generics.loc[generics[7] == minCost]
                minQuant = np.min(minpotdf[8])
                normalizer = float(minCost)/float(minQuant)
                potgroup[21] = normalizer

                minCostBrand = np.min(nonGenerics[7])
                minpotdfBrand = nonGenerics.loc[nonGenerics[7] == minCostBrand]
                minQuantBrand = np.min(minpotdfBrand[8])

                unitNonGenericCost = float(minCostBrand)/float(minQuantBrand)
                potgroup[22] = unitNonGenericCost
                
                if unitNonGenericCost > normalizer:
                    nonGenerics[23] = float(unitNonGenericCost - normalizer)*nonGenerics[8]


def countTotalDrugDosage(pdp,codes):
    total_drugs = 0.0
    for name , group in pdp.groupby(3):
        for dcode in codes:
            if name.find(dcode) == 0:
                total_drugs+=np.sum(group[19])
    return total_drugs

def normalizePills(keys):
    minima = np.min(keys)
    if minima > 0:
        potency = keys/minima
    else:
        potency = 1.0
    return pd.Series(potency,index=keys.index)
        
    
def normalizePotency(keys):
    minima = np.min(keys)
    if minima > 0:
        potency = keys/minima
    else:
        potency = 1.0
    return pd.Series(potency,index=keys.index)
    
def normalize(dataFrame):
    dataFrame[16] = dataFrame[3].str[:9]
    dataFrame[17] = dataFrame.groupby(16)[8].apply(normalizePills)
    dataFrame[18] = dataFrame.groupby(16)[15].apply(normalizePotency) 
    dataFrame[19] = dataFrame[18]*dataFrame[17]
    dataFrame[20] = dataFrame[3].str[9:11]
    dataFrame[21] = dataFrame[15]/dataFrame[8]
    
    
def normalize_new(dataFrame):
    dataFrame[16] = dataFrame['BNF_CODE'].str[:9]
    dataFrame[17] = dataFrame.groupby(16)['TOTAL_QUANTITY'].apply(normalizePills)
    dataFrame[18] = dataFrame.groupby(16)[15].apply(normalizePotency) 
    dataFrame[19] = dataFrame[18]*dataFrame[17]
    dataFrame[20] = dataFrame['BNF_CODE'].str[9:11]
    dataFrame[21] = dataFrame[15]/dataFrame['TOTAL_QUANTITY']
    
    
    
def doImportantMappings(Df):
    #BNF family
#     Df[11] = ''  
#     Df[11] = Df.groupby(3)[3].apply(getDrugFamily,symptomMap)
#     #Disease
#     Df[12] = ''  
#     Df[12] = Df.groupby(3)[3].apply(getDisease,diseaseMap)
#     #Symptom
#     Df[13] = ''  
#     Df[13] = Df.groupby(3)[3].apply(getDisease,symptomMap)
#     #Checm Name
#     Df[14] = ''  
#     Df[14] = Df.groupby(3)[3].apply(getDrug,symptomMap)
    #Chem potency
    Df[15] = ''  
    Df[15] = Df.groupby(3)[4].apply(getDrugPotency)

    normalize(Df)

    return Df



def doImportantMappings_new(Df):
    #BNF family
#     Df[11] = ''  
#     Df[11] = Df.groupby('BNF_CODE')['BNF_CODE'].apply(getDrugFamily,symptomMap)
#     #Disease
#     Df[12] = ''  
#     Df[12] = Df.groupby('BNF_CODE')['BNF_CODE'].apply(getDisease,diseaseMap)
#     #Symptom
#     Df[13] = ''  
#     Df[13] = Df.groupby('BNF_CODE')['BNF_CODE'].apply(getDisease,symptomMap)
#     #Checm Name
#     Df[14] = ''  
#     Df[14] = Df.groupby('BNF_CODE')['BNF_CODE'].apply(getDrug,symptomMap)
    #Chem potency
    Df[15] = ''  
    Df[15] = Df.groupby('BNF_CODE')['BNF_DESCRIPTION'].apply(getDrugPotency)

    normalize_new(Df)

    return Df