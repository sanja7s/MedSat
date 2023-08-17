import pandas as pd
import geopandas as gpd
import numpy as np
import os
import matplotlib.pyplot as plt
from util import *

import spreg
from libpysal.weights import Queen


data_folder = "../../data/point_data/collated_data/"
results_folder = "../../results/models/spatialRegression/"
image_features_folder = os.path.join(data_folder, "image_features", "England_JJA2020")


def parse_single_year(the_year, modalities):

    mod = "_".join(modalities)

    dataset = gpd.read_file(data_folder + f"{the_year}_spatial_raw_master.geojson").dropna()

    if (os.path.exists(image_features_folder)):
        features_image = pd.read_csv(os.path.join(image_features_folder, "lsoas_pixel_statistics.csv"), index_col="geography code")
        features_image.columns = ["image_mean_{}".format(col) for col in features_image.columns]
        dataset = pd.merge(dataset, features_image, on=['geography code']).dropna()

        print (dataset.describe())

    for condition in all_conditions:

        med_condition = "o_{}_quantity_per_capita".format(condition)

        X, y = extract_features_and_labels(dataset, med_condition, modalities+["spatial"])
        X = X.set_index("geometry")
        X_vars = list(X.columns)

        print (X_vars)
        print (X.head())
        print (y)

        print (f"**** Parsing {the_year} year and modality {mod} for condition {condition} ****")

        w = Queen.from_dataframe(dataset)
        w.transform = 'R'

        slm = spreg.ML_Lag(y, X.values, method='LU', w=w, name_y=med_condition, name_x=X_vars)
        print(slm.summary)

        with open(results_folder + f"{the_year}_{condition}_{mod}_summary_output.txt", "w") as file:
            file.write(str(slm.summary))


    
# parse_single_year(2020, ["environmental"])
parse_single_year(2020, ["image"])
parse_single_year(2020, ["sociodemograhic", "environmental", "image"])

parse_single_year(2019, ["image"])
parse_single_year(2019, ["environmental"])
parse_single_year(2019, ["sociodemograhic"])
parse_single_year(2019, ["sociodemograhic", "environmental", "image"])
