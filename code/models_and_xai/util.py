import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split


e_variable_mapping = {
    "NO2": "NO2",
    "ozone": "ozone",
    "total_aerosol_optical_depth_at_550nm_surface": "aerosols",
    "particulate_matter_d_less_than_25_um_surface": "PM2.5",
    "ndvi": "greenery",
    "leaf_area_index_high_vegetation": "high vegetation LAI",
    "leaf_area_index_low_vegetation": "low vegetation LAI",
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
    "evaporation_from_bare_soil_sum": "bare soil evaporation",
    "evaporation_from_the_top_of_canopy_sum": "canopy evaporation",
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
    "c_percent TFW less than 2km": "work travel less than 2km",
    "c_percent TFW 2km to 5km": "work travel 2km and 5km",
    "c_percent TFW 60km and over": "work travel more than 60km",
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
    "c_percent male": "male",
    "c_total population": "total population",
    "c_percent 8. Process plant and machine operatives": "machine operatives",
    "c_percent 5. Skilled trades occupations": "skilled trades occupations",
    "c_percent commute car": "commute by car",
    "c_net annual income": "net annual income",
    "c_percent   can speak english very well": "speaks english very well",
    "c_percent Aged 4 years and under": "4 years and under",
    "c_percent Aged 5 to 9 years": "5 to 9 years",
    "c_percent Aged 10 to 14 years": "10 to 14 years",
    "c_percent Aged 15 to 19 years": "15 to 19 years",
    "c_percent Aged 20 to 24 years": "20 to 24 years",
    "c_percent Aged 25 to 29 years": "25 to 29 years",
    "c_percent Aged 30 to 34 years": "30 to 34 years",
    "c_percent Aged 35 to 39 years": "35 to 39 years",
    "c_percent Aged 40 to 44 years": "40 to 44 years",
    "c_percent Aged 45 to 49 years": "45 to 49 years",
    "c_percent Aged 50 to 54 years": "50 to 54 years",
    "c_percent Aged 55 to 59 years": "55 to 59 years",
    "c_percent Aged 60 to 64 years": "60 to 64 years",
    "c_percent Aged 65 to 69 years": "65 to 69 years",
    "c_percent Aged 70 to 74 years": "70 to 74 years",
    "c_percent Aged 75 to 79 years": "75 to 79 years",
    "c_percent Aged 80 to 84 years": "80 to 84 years",
    "c_percent Aged 85 years and over": "85 years and over"

}

variable_mapping = {**e_variable_mapping, **soc_variable_mapping}

land_cover_columns = ["e_Tree cover", "e_Shrubland", "e_Grassland", "e_Cropland", "e_Built-up", "e_Bare sparse vegetation",
                      "e_Permanent water bodies", "e_Herbaceous wetland", "e_Moss and lichen"]

all_conditions = ['diabetes', 'hypertension', 'opioids', 'depression', 'anxiety', 'asthma', 'total']

all_modalities = ["sociodemograhic", "environmental", "geo", "image"]

age_columns = ["4 years and under", "5 to 9 years", "10 to 14 years", "15 to 19 years",
               "20 to 24 years", "25 to 29 years", "30 to 34 years", "35 to 39 years",
               "40 to 44 years", "45 to 49 years", "50 to 54 years", "55 to 59 years",
               "60 to 64 years", "65 to 69 years", "70 to 74 years", "75 to 79 years",
               "80 to 84 years", "85 years and over"]

gender_columns = ["male"]

geo_columns = ["centroid_x","centroid_y"]

def split_dataset(year, ratio_test=0.3):
    dataset = pd.read_csv('./data/{}_raw_master.csv'.format(year), index_col=['geography code'])
    dataset_train, other_dataset = train_test_split(dataset, test_size=ratio_test, random_state=0)
    dataset_test, dataset_val = train_test_split(other_dataset, test_size=0.5, random_state=0)

    dataset_train.to_csv('data/{}_train_raw.csv'.format(year))
    dataset_val.to_csv('data/{}_val_raw.csv'.format(year))
    dataset_test.to_csv('data/{}_test_raw.csv'.format(year))

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
        elif modality == "environmental":
            features_per_modality = features.filter(regex='^(e_)')
        elif modality == "geo":
            features_per_modality = features.filter(regex='^(centroid_)')
        else:
            features_per_modality = features.filter(regex='^(image_)')
        modality_dfs.append(features_per_modality)

    modalities_features = pd.concat(modality_dfs, axis=1)
    modalities_features.rename(columns=variable_mapping, inplace=True)

    return modalities_features, labels


if __name__ == '__main__':
    split_dataset(2019)



