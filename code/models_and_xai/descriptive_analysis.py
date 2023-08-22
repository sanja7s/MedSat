import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from util import *

env_features_to_show = ["temperature", "surface soil temperature", "snow density", "atmospheric pressure", "thermal radiation"]
tex_fonts = {
    #source: https://jwalton.info/Embed-Publication-Matplotlib-Latex/
    # Use LaTeX to write all text
    #"text.usetex": True,
    #"font.family": "serif",
    # Use 10pt font in plots, to match 10pt font in document
    "axes.labelsize": 6,
    "font.size": 10,
    # Make the legend/label fonts a little smaller
    "legend.fontsize": 6,
    "axes.titlesize": 6,
    "xtick.labelsize": 6,
    "ytick.labelsize": 6,
    'text.latex.preamble': r"\usepackage{amsmath}"
}

def plot_correlation_among_features(year, target_modality, features_to_show):
    if not os.path.exists(descriptive_analysis_dir):
        os.makedirs(descriptive_analysis_dir)

    dataset = read_spatial_dataset(year)
    features, labels = extract_features_and_labels(dataset, "o_diabetes_quantity_per_capita", [target_modality])
    features = features.rename(columns=variable_mapping)
    correlation_matrix = features.corr()
    corr_viz = correlation_matrix.loc[correlation_matrix.index.isin(features_to_show)][features_to_show]

    plt.rcParams.update(tex_fonts)
    fig, ax = plt.subplots(figsize=(4, 3))
    sns.heatmap(corr_viz, ax=ax, cmap="plasma")
    ax.set_title("{} features".format(target_modality))

    fig.tight_layout()
    plt.savefig(os.path.join(descriptive_analysis_dir, "corr_matrix_{}_{}.pdf".format(year, target_modality)), dpi=300)
    plt.close()

def get_missing_values_per_year(year):
    dataset = read_spatial_dataset(year)
    missing_values = dataset.isnull()
    total_rows_missing = missing_values.any(axis=1).sum()
    print("{} instances have missing values for year {}".format(total_rows_missing, year))
    missing_values_per_column = missing_values.sum()
    columns_with_missing_values = missing_values_per_column[missing_values_per_column > 0]
    columns_with_missing_values.to_csv("./data/{}_missing_values.csv".format(year))


def plot_distribution(year, columns_of_interest,  modalities, var_name="age group"):
    if not os.path.exists(descriptive_analysis_dir):
        os.makedirs(descriptive_analysis_dir)

    dataset = read_spatial_dataset(year)
    features, labels = extract_features_and_labels(dataset, "o_diabetes_quantity_per_capita", modalities)
    features = features[columns_of_interest]
    features = pd.melt(features, var_name=var_name, value_name="percent")
    fig, ax = plt.subplots(figsize=(3, 4))
    sns.barplot(data=features, x=var_name, y="percent",
                errorbar="sd", palette="dark", alpha=.6, ax=ax, order=columns_of_interest)
    ax.set_title("{} distribution".format(var_name))
    ax.set_xticklabels(ax.xaxis.get_ticklabels(), rotation=45, ha="right")

    fig.tight_layout()
    plt.savefig(os.path.join(descriptive_analysis_dir, "{}.pdf".format(var_name)), dpi=300)
    plt.close()

def plot_light_gbm_fnn_results(year, modalities=all_modalities):

    light_gbm_results_file = os.path.join(results_folder, "lightGBM", "repeated_spatial_kfold", "{}__{}.csv".format(year, "_".join(modalities)))
    light_gbm_results = pd.read_csv(light_gbm_results_file, index_col=0)
    light_gbm_results_long = pd.melt(light_gbm_results, var_name="condition", value_name="R2")
    light_gbm_results_long["model"] = "LightGBM"

    fnn_results_file = os.path.join(results_folder, "fNN", "repeated_spatial_kfold", "{}__{}.csv".format(year, "_".join(modalities)))
    fnn_results = pd.read_csv(fnn_results_file, index_col=0)
    fnn_results_long = pd.melt(fnn_results, var_name="condition", value_name="R2")
    fnn_results_long["model"] = "fNN"

    summary_results = pd.concat([light_gbm_results_long, fnn_results_long], ignore_index=True, sort=False)

    model_comparison_dir = os.path.join(results_folder, "model_comparison")
    if not os.path.exists(model_comparison_dir):
        os.makedirs(model_comparison_dir)

    fig, ax = plt.subplots(figsize=(4, 4))

    conditions_order = ["diabetes", "hypertension", "depression", "anxiety", "opioids", "asthma", "total"]
    sns.barplot(data=summary_results, x="condition", y="R2", hue="model",
                errorbar="sd", palette="dark", alpha=.6, ax=ax, order=conditions_order)
    ax.set_title("prescription prediction for {}".format(year))
    ax.set_xticklabels(ax.xaxis.get_ticklabels(), rotation=45, ha="right")
    ax.set_ylabel(r'$R^2$ score')

    fig.tight_layout()
    plt.savefig(os.path.join(model_comparison_dir, "model_comparison_{}_{}.pdf".format(year, "_".join(modalities))),
                             dpi=300)
    plt.close()



if __name__ == '__main__':
    plot_light_gbm_fnn_results(2020, ["environmental", "image", "sociodemographic"])
    # plot_correlation_among_features(2020, "environmental", env_features_to_show)