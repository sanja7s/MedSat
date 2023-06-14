import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split

variables_to_drop = ["e_lake_bottom_temperature", "e_surface_thermal_radiation_downwards_sum", "e_surface_pressure",
                     "e_soil_temperature_level_3", "e_soil_temperature_level_1", "e_temperature_2m",
                     "e_dewpoint_temperature_2m", "e_lake_mix_layer_temperature", "e_snow_density",
                     "e_total_evaporation_sum", "e_surface_latent_heat_flux_sum", "e_surface_solar_radiation_downwards_sum",
                     "e_surface_net_solar_radiation_sum", "e_evaporation_from_bare_soil_sum", "e_lake_total_layer_temperature",
                     "e_leaf_area_index_low_vegetation", "e_evaporation_from_the_top_of_canopy_sum", "e_volumetric_soil_water_layer_1"]

e_variable_mapping = {
    "NO2": "NO2",
    "ozone": "ozone",
    "total_aerosol_optical_depth_at_550nm_surface": "aerosols",
    "particulate_matter_d_less_than_25_um_surface": "PM2.5",
    "ndvi": "greenery",
    "leaf_area_index_high_vegetation": "high vegetation leaf area index",
    "leaf_area_index_low_vegetation": "low vegetation leaf area index",
    "temperature_2m": "temperature",
    "soil_temperature_level_1": "surface soil temperature",
    "soil_temperature_level_3": "deep soil temperature",
    "lake_bottom_temperature": "lake bottom temperature",
    "lake_mix_layer_depth": "lake mix layer depth",
    "lake_mix_layer_temperature": "lake mix layer temperature",
    "lake_total_layer_temperature": "lake total layer temperature",
    "snow_albedo": "snow albedo",
    "snow_cover": "snow cover",
    "snow_density": "snow density",
    "snow_depth": "snow depth",
    "volumetric_soil_water_layer_1": "surface soil water content",
    "volumetric_soil_water_layer_3": "deep soil water content",
    "surface_latent_heat_flux_sum": "surface latent heat flux sum",
    "surface_net_solar_radiation_sum": "total solar energy absorption",
    "surface_solar_radiation_downwards_sum": "solar radiation",
    "surface_thermal_radiation_downwards_sum": "thermal radiation",
    "evaporation_from_bare_soil_sum": "total bare soil evaporation",
    "evaporation_from_the_top_of_canopy_sum": "total canopy evaporation",
    "evaporation_from_open_water_surfaces_excluding_oceans_sum": "evaporation open water surfaces",
    "total_evaporation_sum": "total evaporation sum",
    "u_component_of_wind_10m": "east-west wind",
    "v_component_of_wind_10m": "north-south wind",
    "surface_pressure": "atmospheric pressure",
    "total_precipitation_sum": "accumulated precipitation",
    "surface_runoff_sum": "total surface runoff",
    "Tree cover": "Tree cover",
    "Shrubland": "Shrubland",
    "Grassland": "Grassland",
    "Cropland": "Cropland",
    "Built-up": "Built-up",
    "Bare / sparse vegetation": "Bare / sparse vegetation",
    "Snow and ice": "Snow and ice",
    "Permanent water bodies": "Permanent water bodies",
    "Herbaceous wetland": "Herbaceous wetland",
    "Mangroves": "Mangroves",
    "Moss and lichen": "Moss and lichen"
}
e_variable_mapping = {'e_'+k:v for (k,v) in e_variable_mapping.items()}

soc_variable_mapping = {
    "c_percent asian": "Asian ethnicity",
    "c_percent black": "Black ethnicity",
    "c_percent mixed": "Mixed ethnicity",
    "c_percent white": "White ethnicity",
    "c_percent christian" : "Christian religion",
    "c_percent jewish": "Jewish religion",
    "c_percent no religion": "no religion",
    "c_percent muslim": "Muslim religion",
    "c_percent no central heating": "no central heating",
    "c_percent wood heating": "wood heating",
    "c_percent communal heating": "communal heating",
    "c_percent TFW less than 2km": "travel to work less than 2km",
    "c_percent TFW 2km to 5km": "travel to work between 2km and 5km",
    "c_percent TFW 60km and over": "travel to work more than 60km",
    "c_percent WFH": "work from home",
    "c_percent part-time": "part-time work",
    "c_percent 15 hours or less worked": "worked less than 15h",
    "c_percent 49 or more hours worked": "worked more than 49 hours",
    "c_percent commute on foot": "commute on foot",
    "c_percent commute bus": "commute by bus",
    "c_percent commute bicycle": "commute by bicycle",
    "c_percent same address": "unchanged address",
    "c_percent student moved to address": "students moved",
    "c_percent occupancy rating bedrooms +2": "occupancy rating bedrooms +2",
    "c_percent occupancy rating bedrooms 0": "occupancy rating bedrooms 0",
    "c_percent occupancy rating bedrooms -2": "occupancy rating bedrooms -2",
    "c_percent occupancy rating rooms +2": "occupancy rating rooms +2",
    "c_percent occupancy rating rooms 0": "occupancy rating rooms 0",
    "c_percent occupancy rating rooms -2": "occupancy rating rooms -2",
    "c_percent 1. Managers directors and senior officials": "managers, directors and senior officials",
    "c_percent 2. Professional occupations": "prof. occupation",
    "c_percent 6. Caring leisure and other service occupations": "caring leisure and other service occupations",
    "c_percent 7. Sales and customer service occupations": "sales and customer service occupations",
    "c_percent 9. Elementary occupations": "elementary occupations",
    "c_percent born in the UK": "born in the UK",
    "c_percent 10 years or more": "UK resident 10+ years",
    "c_percent 2 years or more but less than 5 years": "reside in the UK between 2 years and 5 years",
    "c_percent less than 2 years": "reside in the UK for less than 2 years",
    "c_pop_density": "population density",
    "c_percent children up to 14": "children up to 14",
    "c_percent aged 65plus": "aged 65plus",
    "c_percent married or in civil partnership": "married or in civil partnership",
    "c_percent unemployed": "percent unemployed",
    "c_percent very good health": "very good health",
    "c_percent bad health": "bad health",
    "c_percent poor-english": "poor-english",
    "c_percent highly-deprived": "highly-deprived",
    "c_percent mid-deprived": "mid-deprived",
    "c_percent male": "percent male",
    "c_total population": "total population",
}

variable_mapping = {**e_variable_mapping, **soc_variable_mapping}

land_cover_columns = ["e_Tree cover", "e_Shrubland", "e_Grassland", "e_Cropland", "e_Built-up", "e_Bare sparse vegetation",
                      "e_Permanent water bodies", "e_Herbaceous wetland", "e_Moss and lichen"]

all_conditions = ['diabetes', 'hypertension', 'opioids', 'depression', 'anxiety', 'asthma', 'total']

modalities = ["sociodemograhic", "environmental"]



def split_dataset(dataset, ratio_test=0.3):
    dataset_train, other_dataset = train_test_split(
        dataset, test_size=ratio_test, random_state=0)
    dataset_test, dataset_val = train_test_split(
        other_dataset, test_size=0.5, random_state=0)

    dataset_train.to_csv('data/train_raw.csv')
    dataset_val.to_csv('data/val_raw.csv')
    dataset_test.to_csv('data/test_raw.csv')

    print("Dataset size: {}".format(len(dataset)))
    print("Train size: {}".format(len(dataset_train)))
    print("Validation size: {}".format(len(dataset_val)))
    print("Test size: {}".format(len(dataset_test)))

    return dataset_train, dataset_val, dataset_test


def extract_features_and_labels(dataset, outcome_col, modalities, log_normalize=False):
    labels = np.array(dataset[outcome_col])
    if log_normalize and outcome_col in ["o_opioids_quantity_per_capita", "o_total_quantity_per_capita"]:
        labels = np.log(labels)

    #exclude the outcome columns
    features = dataset.filter(regex="^(?!o_)")

    modality_dfs = []
    for modality in modalities:
        if modality == "sociodemograhic":
            features_per_modality = features.filter(regex='^(c_)')
        else:
            features_per_modality = features.filter(regex='^(e_)')

        modality_dfs.append(features_per_modality)

    modalities_features = pd.concat(modality_dfs, axis=1)
    modalities_features.rename(columns=variable_mapping, inplace=True)

    return modalities_features, labels


if __name__ == '__main__':
    dataset = pd.read_csv('./data/raw_master.csv', index_col=['geography code'])
    split_dataset(dataset)



