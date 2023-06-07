import os.path

import pandas as pd
import numpy as np
import itertools

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import lightgbm as lgb

from util import *


def train_LGB(x_train, y_train, x_val, y_val):

    params = {
        'objective': 'regression',
        'metric': 'rmse'}

    # Create LightGBM datasets
    train_data = lgb.Dataset(x_train, label=y_train)
    val_data = lgb.Dataset(x_val, label=y_val)

    # Train model with early stopping
    model = lgb.train(params, train_data, valid_sets=[val_data], early_stopping_rounds=10)

    train_r2 = r2_score(y_train, model.predict(x_train))
    val_r2 = r2_score(y_val, model.predict(x_val))

    print(f'Train R^2: {train_r2:.4f}')
    print(f'Validation R^2: {val_r2:.4f}')

    return model





def evaluate_lightgbm_per_modality_comb(fold_splits, modality_comb):

    results = []
    for med_condition in all_conditions:
        test_r2_scores = []
        test_rmse_scores = []
        med_condition = "o_{}_quantity_per_capita".format(med_condition)
        for fold in fold_splits:
            # Split data into training and validation sets for this fold
            train_fold = fold[0]
            val_fold = fold[1]
            test_fold = fold[2]

            scaler = StandardScaler()
            x_train, y_train = extract_features_and_labels(train_fold, med_condition, modality_comb)
            x_train = scaler.fit_transform(x_train)
            x_val, y_val = extract_features_and_labels(val_fold, med_condition, modality_comb)
            x_val = scaler.transform(x_val)
            x_test, y_test = extract_features_and_labels(test_fold, med_condition, modality_comb)
            x_test = scaler.transform(x_test)

            lgb_model = train_LGB(x_train, y_train, x_val, y_val)

            r2_test = r2_score(y_test, lgb_model.predict(x_test))
            mse_test = mean_squared_error(y_test, lgb_model.predict(x_test))
            test_r2_scores.append(r2_test)
            test_rmse_scores.append(mse_test)

        r2_per_cond = np.mean(np.array(test_r2_scores))
        mse_per_cond = np.mean(np.array(test_rmse_scores))
        results.append((med_condition, r2_per_cond, mse_per_cond))

    results = pd.DataFrame(results, columns=["Condition", "R2", "MSE"])

    light_gbm_results_dir = "./results/models/lightGBM/kfold/"
    if not os.path.exists(light_gbm_results_dir):
        os.makedirs(light_gbm_results_dir)
    results.to_csv("{}/{}.csv".format(light_gbm_results_dir,"_".join(modality_comb)), index=False)



if __name__ == '__main__':
    dataset = pd.read_csv('./data/raw_master.csv', index_col=['geography code'])
    fold_splits = get_dataset_fold_splits(dataset)
    for L in range(len(modalities) + 1):
        for modality_comb in itertools.combinations(modalities, L):
            if len(modality_comb) > 0:
                evaluate_lightgbm_per_modality_comb(fold_splits, modality_comb)


