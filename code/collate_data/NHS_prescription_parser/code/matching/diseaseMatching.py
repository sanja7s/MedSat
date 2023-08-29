import networkx as nx
import pandas as pd
from tqdm import tqdm
from matching.utils import findDrugsForDisease , findDrugsForCategory

class diseaseMatcher:
    def __init__(self , mappings_dir="../mappings/"):
        self.mappings_dir = mappings_dir

    def drug_matching(self, conditions, is_cat=False):
        drug_association_graph = nx.read_gexf(self.mappings_dir + 'drug_association_graph.gexf')
        drug_cat_association_graph = nx.read_gexf(self.mappings_dir + 'category_association_graph.gexf')
        chem = pd.read_csv(self.mappings_dir + 'CHEM_MASTER_MAP.csv')

        disease_drugs = {}
        for d in tqdm(conditions):
            if not is_cat:
                drugs = findDrugsForDisease(drug_association_graph, d, chem)
            else:
                drugs = findDrugsForCategory(drug_cat_association_graph, d, chem)

            for drug in drugs:
                disease_drugs[drug] = {}
                disease_drugs[drug]['chemName'] = drugs[drug]['name']
                disease_drugs[drug]['disease'] = d

        disease_drug_map = {}
        for k in tqdm(disease_drugs):
            if disease_drugs[k]['disease'] not in disease_drug_map:
                disease_drug_map[disease_drugs[k]['disease']] = []
            disease_drug_map[disease_drugs[k]['disease']].append(k)
        return disease_drugs, disease_drug_map

    def dump_drugs(self, disease_drugs):
        drug_map_dict = {'BNF_code': [], 'Drug_name': [], 'Mapped_Condition': []}
        for k in tqdm(disease_drugs):
            drug_map_dict['BNF_code'].append(k)
            drug_map_dict['Drug_name'].append(disease_drugs[k]['chemName'])
            drug_map_dict['Mapped_Condition'].append(disease_drugs[k]['disease'])
        drug_map_df = pd.DataFrame.from_dict(drug_map_dict)
        drug_map_df.to_csv(self.output_dir + 'Drugs.csv', index=False)
        return self.output_dir + 'Drugs.csv'