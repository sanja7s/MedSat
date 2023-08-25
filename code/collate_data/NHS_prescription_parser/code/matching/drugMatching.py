import networkx as nx
import pandas as pd
from matching.utils import findDrugsForCategory,findDrugsForDisease
import argparse


class DrugMatcher:
    def __init__(self, mappings_dir='../mappings/', output_dir='../../data_prep/'):
        self.mappings_dir = mappings_dir
        self.output_dir = output_dir
        self.drug_association_graph = nx.read_gexf(self.mappings_dir + 'drug_association_graph.gexf')
        self.drug_cat_association_graph = nx.read_gexf(self.mappings_dir + 'category_association_graph.gexf')
        self.chem_master = pd.read_csv(self.mappings_dir + 'CHEM_MASTER_MAP.csv')
    
    def DrugMatching(self, drugNames, isCat=False):
        matchedDrugs = {}
        for d in drugNames:
            if not isCat:
                drugs = findDrugsForDisease(self.drug_association_graph, d ,self.chem_master)
            else:
                drugs = findDrugsForCategory(self.drug_cat_association_graph, d , self.chem_master)

            for drug in drugs:
                matchedDrugs[drug] = {}
                matchedDrugs[drug]['chemName'] = drugs[drug]['name']
                matchedDrugs[drug]['disease'] = d

        drug_map = {}
        for k in matchedDrugs:
            if matchedDrugs[k]['disease'] not in drug_map:
                drug_map[matchedDrugs[k]['disease']] = []
            drug_map[matchedDrugs[k]['disease']].append(k)
        return matchedDrugs , drug_map

    def dumpDrugs(self, matchedDrugs):
        drug_map_dict = {'BNF_code':[], 'Drug_name':[] , 'Mapped_Condition': []}
        for k in matchedDrugs:
            drug_map_dict['BNF_code'].append(k)
            drug_map_dict['Drug_name'].append(matchedDrugs[k]['chemName'])
            drug_map_dict['Mapped_Condition'].append(matchedDrugs[k]['disease'])
        drug_map_df = pd.DataFrame.from_dict(drug_map_dict)    
        drug_map_df.to_csv(self.output_dir + 'Drugs.csv',index=False)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c' , '--condition' ,nargs="+" ,help=" Condition for which we need drugs ")
    args = parser.parse_args()
    condition = args.condition
    print("Running for : ",condition)
    matcher = DrugMatcher()
    print(matcher.DrugMatching(condition))