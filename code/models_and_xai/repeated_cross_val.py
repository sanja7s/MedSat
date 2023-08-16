import os
import pandas
import geopandas as gpd
import pandas as pd

from util import *
from lightGBM import train_evaluate_light_gbm
from fNN import fnn_train_evaluation
# import spacv
import itertools



data_folder = "../../data/point_data/"
image_features_folder = os.path.join(data_folder, "image_features", "England_JJA2020")
results_folder = "../../results/models/"
processing_folder = "../../processing/models/spatial_cv_folds/"

def get_dataset_fold_splits(dataset, test_size=0.5):
    kf = KFold(n_splits=5, shuffle=True)
    fold_splits = []
    for train_index, test_index in kf.split(dataset):
        train_fold, test_fold = dataset.iloc[train_index], dataset.iloc[test_index]
        test_fold, val_fold = train_test_split(test_fold, test_size=test_size)
        print(len(train_fold), len(val_fold), len(test_fold))
        fold_splits.append((train_fold, val_fold, test_fold))

    return fold_splits

def get_dataset_spatial_fold_splits(dataset, year, fold_iterration, val_size=0.5):
    cv = pd.read_csv(processing_folder + "{}_{}_folds_with_geography_code.csv".format(fold_iterration+1, year))

    sdataset = dataset.set_index('geography code')

    fold_splits = []
    for i in range(5):
        cv_fold = cv[cv["Fold"]==i+1]
        train_index = list(cv_fold[cv_fold["Type"]=="Train"]["GeographyCode"])
        test_index = list(cv_fold[cv_fold["Type"]=="Test"]["GeographyCode"])

        missing_indices = set(train_index + test_index) - set(sdataset.index)
        print(len(missing_indices))

        train_fold, test_fold = sdataset.loc[train_index], sdataset.loc[test_index]
        train_fold, val_fold = train_test_split(train_fold, test_size=val_size)
        print(len(train_fold), len(val_fold), len(test_fold))
        fold_splits.append((train_fold, val_fold, test_fold))
    
    return fold_splits


# SLOO FOLDS
# def get_dataset_SLOO_fold_splits(sdataset, buffer_radius=1000, test_size=0.5):
#     """

#     """
#     spatial_splits = []

#     XYs = sdataset['geometry']
#     sample_XYs = XYs.sample(1000)

#     cv = spacv.SKCV(n_splits = len(sample_XYs), buffer_radius=10)

#     for train_index,test_index in cv.split(XYs):
#         train_fold, test_fold = sdataset.iloc[train_index], sdataset.iloc[test_index]

#         train_fold, val_fold = train_test_split(train_fold, test_size=test_size)
#         print(len(train_fold), len(val_fold), len(test_fold))
#         spatial_splits.append((train_fold, val_fold, test_fold))

#     return spatial_splits

def perform_repeated_cross_val(year, model_fn, model_dir, modalities=all_modalities):
    dataset = pd.read_csv(data_folder+'{}_spatial_raw_master.csv'.format(year), index_col='geography code').dropna()

    if os.path.exists(image_features_folder):
        image_features = pd.read_csv(os.path.join(image_features_folder, "lsoas_pixel_statistics.csv"), index_col="geography code")
        image_features.columns = ["image_{}".format(col) for col in image_features.columns]
        dataset = pd.merge(dataset, image_features, left_index=True, right_index=True)

    cross_validation_times = 5
    folds_test_scores = None
    for i in range(cross_validation_times):
        fold_splits = get_dataset_fold_splits(dataset)
        cross_val_result = model_fn(fold_splits, modalities)
        if folds_test_scores is None:
            folds_test_scores = cross_val_result
        else:
            for key in folds_test_scores.keys():
                folds_test_scores[key]["r2"] = folds_test_scores[key]["r2"] + cross_val_result[key]["r2"]
                folds_test_scores[key]["mse"] = folds_test_scores[key]["mse"] + cross_val_result[key]["mse"]

    summarized_results = dict()

    for condition in folds_test_scores:
        r2_scores_condition = np.array(folds_test_scores[condition]["r2"])
        summarized_results[condition] = r2_scores_condition

    summarized_results = pd.DataFrame.from_dict(summarized_results)
    summarized_results_mean = summarized_results.mean(axis=0)
    summarized_results_std = summarized_results.std(axis=0)

    model_results_dir = results_folder + "{}/repeated_kfold/".format(model_dir)
    if not os.path.exists(results_folder):
        os.makedirs(model_results_dir)

    summarized_results_mean.to_csv("{}/{}_{}_mean.csv".format(model_results_dir, year, "_".join(modalities)))
    summarized_results_std.to_csv("{}/{}_{}_std.csv".format(model_results_dir, year, "_".join(modalities)))

# SPATIAL EVALUATION
def perform_repeated_spatial_cross_val(year, model_fn, model_dir, SLOO=False, modalities=all_modalities):
    """
    we need spatial dataset here, so we read geojson
    this way, we can split the LSOAs based on their centroid distances
    """
    sdataset = gpd.read_file(data_folder+'{}_spatial_raw_master.geojson'.format(year)).dropna()

    cross_validation_times = 5
    buffer_radius=None
    folds_test_scores = None
    for i in range(cross_validation_times):
        if SLOO:
            fold_splits = get_dataset_spatial_fold_splits(sdataset, year=year, fold_iterration=i)
        else:
            fold_splits = get_dataset_spatial_fold_splits(sdataset, year=year, fold_iterration=i)

        print (fold_splits)
        cross_val_result = model_fn(fold_splits, modalities)
        if folds_test_scores is None:
            folds_test_scores = cross_val_result
        else:
            for key in folds_test_scores.keys():
                folds_test_scores[key]["r2"] = folds_test_scores[key]["r2"] + cross_val_result[key]["r2"]
                folds_test_scores[key]["mse"] = folds_test_scores[key]["mse"] + cross_val_result[key]["mse"]

    summarized_results = dict()

    for condition in folds_test_scores:
        r2_scores_condition = np.array(folds_test_scores[condition]["r2"])
        summarized_results[condition] = r2_scores_condition

    summarized_results = pd.DataFrame.from_dict(summarized_results)
    summarized_results_mean = summarized_results.mean(axis=0)
    summarized_results_std = summarized_results.std(axis=0)

    if SLOO:
        model_results_dir = results_folder + "{}/repeated_SLOO_kfold/".format(model_dir)
    else:
        model_results_dir = results_folder +  "{}/repeated_spatial_kfold/".format(model_dir)
    
    if not os.path.exists(model_results_dir):
        os.makedirs(model_results_dir)

    if buffer_radius is None:
        buffer_radius = ''

    summarized_results_mean.to_csv("{}/{}_{}_{}_mean.csv".format(model_results_dir, year, buffer_radius, "_".join(modalities)))
    summarized_results_std.to_csv("{}/{}_{}_{}_std.csv".format(model_results_dir, year, buffer_radius, "_".join(modalities)))


if __name__ == '__main__':

    #single modality
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "image"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "image"])
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "sociodemograhic"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "sociodemograhic"])
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "environmental"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "environmental"])
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["sociodemograhic"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["sociodemograhic"])
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo"])

    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "image", "sociodemographic"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "image", "sociodemographic"])
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "image", "environmental"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "image", "environmental"])
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "sociodemograhic", "environmental"])
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", modalities=["geo", "sociodemograhic", "environmental"])

    #all modalities
    perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM")
    perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM")

    # perform_repeated_spatial_cross_val(2019, train_evaluate_light_gbm, "lightGBM")
    # perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM")
    # perform_repeated_spatial_cross_val(2020, train_evaluate_light_gbm, "lightGBM", SLOO=True)
