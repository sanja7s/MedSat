import os
import pandas

from util import *
from lightGBM import train_evaluate_light_gbm
from fNN import fnn_train_evaluation

def get_dataset_fold_splits(dataset, test_size=0.5):
    kf = KFold(n_splits=5, shuffle=True)
    fold_splits = []
    for train_index, test_index in kf.split(dataset):
        train_fold, test_fold = dataset.iloc[train_index], dataset.iloc[test_index]
        test_fold, val_fold = train_test_split(test_fold, test_size=test_size)
        print(len(train_fold), len(val_fold), len(test_fold))
        fold_splits.append((train_fold, val_fold, test_fold))

    return fold_splits

def perform_repeated_cross_val(year, model_fn, model_dir):
    dataset = pd.read_csv('./data/{}_raw_master.csv'.format(year), index_col=['geography code']).dropna()
    cross_validation_times = 5
    folds_test_scores = None
    for i in range(cross_validation_times):
        fold_splits = get_dataset_fold_splits(dataset)
        cross_val_result = model_fn(fold_splits)
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

    model_results_dir = "./results/models/{}/repeated_kfold/".format(model_dir)
    if not os.path.exists(model_results_dir):
        os.makedirs(model_results_dir)

    summarized_results.to_csv("{}/{}.csv".format(model_results_dir, year))

if __name__ == '__main__':
    #perform_repeated_cross_val(2020, train_evaluate_light_gbm, "lightGBM")
    perform_repeated_cross_val(2020, fnn_train_evaluation, "fnn")
