import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

import spreg
from libpysal.weights import Queen

data_folder = "../../data/point_data/collated_data/"
results_folder = "../../results/models/spatialRegression/"


def parse_single_year(the_year):

	full = gpd.read_file(data_folder + f"{the_year}_spatial_raw_master.geojson").dropna()
	england = full

	modalities = {}

	# all_modalities = ["sociodemograhic", "environmental", "geo"]
	# two_modalities = ["sociodemograhic", "environmental"]
	# single_modality_soc = ["sociodemograhic"]
	# single_modality_env = ["environmental"]

	#exclude the outcome columns
	features = england.filter(regex="^(?!o_)")
	features_soc = features.filter(regex='^(c_)')
	features_env = features.filter(regex='^(e_)')
	# features_geo = features.filter(regex='^(centroid_)')

	# all_modality_df = []
	two_modality_df = []
	single_modality_soc_df = []
	single_modality_env_df = []
	single_modality_soc_df.append(features_soc)
	single_modality_env_df.append(features_env)
	two_modality_df.append(features_soc)
	two_modality_df.append(features_env)


	modalities['soc'] = single_modality_soc_df
	modalities['env'] = single_modality_env_df
	# modalities['soc_env'] = two_modality_df

	# all_modality_dfs.append(features_soc)
	# all_modality_dfs.append(features_env)
	# all_modality_dfs.append(features_geo)
	# X_coords = pd.concat(all_modality_dfs, axis=1)
	# coords = england[['centroid_x','centroid_y']].values

	for mod, modality_df in modalities.items():

		for condition in ['opioids','depression', 'asthma', 'diabetes', 'anxiety', 'hypertension', 'total']:

			X = pd.concat(modality_df, axis=1)
			X_vars = list(X.columns)

			print (f"**** Parsing {the_year} year for condition {condition} ****")

			y = england[f"o_{condition}_quantity_per_capita"]

			w = Queen.from_dataframe(england)
			w.transform = 'R'

			slm = spreg.ML_Lag(y.values, X.values, method='LU', w=w, name_y=f"o_{condition}_quantity_per_capita", name_x=X_vars)

			print(slm.summary)

			with open(results_folder + f"{the_year}_{condition}_{mod}_summary_output.txt", "w") as file:
				file.write(str(slm.summary))


for year in [2019, 2020]:
	parse_single_year(year)