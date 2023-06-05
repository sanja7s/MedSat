#!/usr/bin/env python
# coding: utf-8
import os.path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.model_selection import ShuffleSplit
from sklearn.metrics import r2_score
import lightgbm as lgb
import shap
import pickle
from sklearn.preprocessing import StandardScaler

import util
from util import variables_to_drop, variable_mapping
import matplotlib.pyplot as plt

tex_fonts = {
    #source: https://jwalton.info/Embed-Publication-Matplotlib-Latex/
    # Use LaTeX to write all text
    "text.usetex": True,
    "font.family": "serif",
    # Use 10pt font in plots, to match 10pt font in document
    "axes.labelsize": 6,
    "font.size": 10,
    # Make the legend/label fonts a little smaller
    "legend.fontsize": 8,
    "axes.titlesize": 8,
    #"xtick.labelsize": 8,
    #"ytick.labelsize": 8,
    'text.latex.preamble': r"\usepackage{amsmath}"
}

from util import extract_features_and_labels, split_dataset
from lightGBM import train_LGB



def prepare_model_inputs(dataset,outcome_col, all_outcomes):
    
    labels = np.array(dataset[outcome_col])
    # Remove the labels from the features
    # axis 1 refers to the columns
    features= dataset.drop(all_outcomes, axis = 1)
    
    return features, labels


def LGB(x_train, y_train, x_val, y_val, x_test, y_test):

    # Define LightGBM parameters
    params = {
        'objective': 'regression',
        'metric': 'rmse',
    }

    # Train and evaluate model using cross-validation

    # Create LightGBM datasets
    train_data = lgb.Dataset(x_train, label=y_train)
    val_data = lgb.Dataset(x_val, label=y_val)

    # Train model with early stopping
    model = lgb.train(params, train_data, valid_sets=[val_data], early_stopping_rounds=10)

    train_r2 = r2_score(y_train, model.predict(x_train))
    val_r2 = r2_score(y_val, model.predict(x_val))
    test_r2 = r2_score(y_test, model.predict(x_test))

    print(f'Train R^2: {train_r2:.4f}')
    print(f'Validation R^2: {val_r2:.4f}')

    return model

def plot_individual_LSOAs(lsoa_id, dataset, shap_values, condition):
    # shap.summary_plot(np.array(shap_values), test_features, plot_type="bar")
    lsoa_index = dataset.index.get_loc(lsoa_id)
    shap.plots.waterfall(shap_values[lsoa_index], max_display=10, show=False)

    plt.title("SHAP for {} and {}".format(lsoa_id, condition))
    plt.tight_layout()
    plt.show()

#latex article class has witdh of 397.484pt
def visualize_shap_values(shap_explainer, condition):
    width = 3.7
    if condition == "diabetes":
        width = 3.3
    fig = plt.figure()
    shap.summary_plot(shap_explainer, show=False, max_display=10, color_bar=False, cmap="plasma")
    plt.gcf().set_size_inches(width, 4)
    plt.yticks(fontsize=8)
    plt.xticks(fontsize=8)
    if condition != "diabetes":
        import matplotlib.cm as cm
        #color = shap.plots.colors.blue_rgb
        #cmap = shap.plots._utils.convert_color(color)
        m = cm.ScalarMappable(cmap="plasma")
        m.set_array([0, 1])
        cb = plt.colorbar(m, ticks=[0, 1], aspect=50)
        cb.set_ticklabels(["Low", "High"])
        cb.set_label("Feature value", size=10, labelpad=-2)
        cb.ax.tick_params(labelsize=8, length=0)
        cb.set_alpha(1)
        cb.outline.set_visible(False)


    plt.xlabel("SHAP", fontsize=10)
    plt.title("{} prescriptions".format(condition.capitalize()), fontsize=10)
    fig.tight_layout()
    plt.savefig(os.path.join(xai_results_base_dir, "shap_values_{}.pdf".format(condition)), dpi=300)
    plt.close()


def compute_feature_rank(condition, feature_name="population density"):
    total_feature_importances = np.abs(shap_values_test_df).mean(0)
    feature_importance = pd.DataFrame(list(zip(shap_values_test_df.columns, total_feature_importances)),
                                      columns=['col_name', 'feature_importance_vals'])
    feature_importance.sort_values(by=['feature_importance_vals'], ascending=False, inplace=True)
    print(feature_importance.head())
    feature_rank_index = feature_importance.index[feature_importance['col_name'] == feature_name]

    print(condition, feature_name, feature_rank_index)

if __name__ == '__main__':

    #set the style for the plots
    #plt.rcParams.update(tex_fonts)

    xai_results_base_dir = "./data/results/xai"

    train_data = pd.read_csv('data/train_raw.csv', index_col=['geography code'])
    val_data = pd.read_csv('data/val_raw.csv', index_col=['geography code'])
    test_data = pd.read_csv('data/test_raw.csv', index_col=['geography code'])

    shap_values_per_condition=[]
    test_features_per_condition = []
    test_labels_per_condition = []

    for i, condition in enumerate(util.all_conditions):
        med_condition = "o_{}_quantity_per_capita".format(condition)
        # Separate features and target variable
        x_train, y_train = extract_features_and_labels(train_data, med_condition, util.modalities)
        x_val, y_val = extract_features_and_labels(val_data, med_condition, util.modalities)
        x_test, y_test = extract_features_and_labels(test_data, med_condition, util.modalities)

        #normalize data
        scaler = StandardScaler()
        x_train_norm = scaler.fit_transform(x_train)
        x_val_norm = scaler.transform(x_val)
        x_test_norm = scaler.transform(x_test)

        model = train_LGB(x_train_norm, y_train, x_val_norm, y_val)
        predictions = model.predict(x_test_norm)
        test_r2 = r2_score(y_test, predictions)
        print('Test R^2: {} for condition {}'.format(test_r2, med_condition))

        # Compute SHAP values for test set
        #SHAPLEY value interpretation:
        print("Initializing SHAP explainer for: {}".format(med_condition))
        explainer = shap.TreeExplainer(model,feature_names=x_train.columns)

        print("Computing SHAP values")
        shap_values_train = explainer(x_train_norm)
        shap_values_val = explainer(x_val_norm)
        shap_values_test = explainer(x_test_norm)
        shap_values_train_df = pd.DataFrame(shap_values_train.values, columns=x_train.columns, index=x_train.index)
        shap_values_val_df = pd.DataFrame(shap_values_val.values, columns=x_val.columns, index=x_val.index)
        shap_values_test_df = pd.DataFrame(shap_values_test.values, columns=x_test.columns, index=x_test.index)

        shap_values_train_df.to_csv(os.path.join(xai_results_base_dir, "shap_values_train_{}.csv".format(condition)))
        shap_values_val_df.to_csv(os.path.join(xai_results_base_dir, "shap_values_val_{}.csv".format(condition)))
        shap_values_test_df.to_csv(os.path.join(xai_results_base_dir, "shap_values_test_{}.csv".format(condition)))

        if condition == "total":
            plot_individual_LSOAs("E01023500", val_data, shap_values_val, condition)
            plot_individual_LSOAs("E01014782", train_data, shap_values_train, condition)

        visualize_shap_values(shap_values_test, condition)
        compute_feature_rank(condition)
        compute_feature_rank(condition, feature_name="total population")
