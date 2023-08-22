import pandas as pd
import geopandas as gpd
import numpy as np
import os
import matplotlib.pyplot as plt
from util import *

import spreg
from libpysal.weights import Queen




def parse_single_year(the_year, modalities):

    mod = "_".join(modalities)

    print ("READING IN DATA.")
    dataset =  read_spatial_dataset(the_year).dropna()
    print (dataset.describe())
    print ("READING IN DONE.")

    for condition in all_conditions:
        med_condition = "o_{}_quantity_per_capita".format(condition)
        print (f"PROCESSING {med_condition}.")    
        X, y = extract_features_and_labels(dataset, med_condition, modalities + ['spatial'])
        X = X.set_index('geometry')
        
        X = X[[c for c in X if ( ('image' not in c) or ((('_mean_' in c) or ('_std_' in c)) & (('B01' in c) or ('B06' in c) or  ('B12' in c)))) ]]
        X_vars = list(X.columns)

        print ("STANDARDIZING FEATURES.")
        print (X.head(2))
        X = standardize_data(X)
        print (X.head(2))
        print ("STANDARDIZING DONE.")

        print (f"**** Parsing {the_year} year and modality {mod} for condition {condition} ****")

        w = Queen.from_dataframe(dataset)
        w.transform = 'R'

        slm = spreg.ML_Lag(y, X.values, method='LU', w=w, name_y=med_condition, name_x=X_vars)
        print(slm.summary)

        with open(spatialreg_results_folder + f"{the_year}_{condition}_{mod}_summary_output.txt", "w") as file:
            file.write(str(slm.summary))

        print (f"PROCESSING {med_condition} DONE.")  


    

# parse_single_year(2020, ["image"])
# parse_single_year(2020, ["environmental"])
parse_single_year(2020, ["sociodemographic"])
parse_single_year(2020, ["sociodemographic", "environmental", "image"])

parse_single_year(2019, ["image"])
parse_single_year(2019, ["environmental"])
parse_single_year(2019, ["sociodemographic"])
parse_single_year(2019, ["sociodemographic", "environmental", "image"])


