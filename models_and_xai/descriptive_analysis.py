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
    descriptive_analysis_dir = "./data/descriptive/"
    if not os.path.exists(descriptive_analysis_dir):
        os.makedirs(descriptive_analysis_dir)

    dataset = pd.read_csv('./data/{}_raw_master.csv'.format(year), index_col=['geography code'])
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
    dataset = pd.read_csv('./data/{}_raw_master.csv'.format(year), index_col=['geography code'])
    missing_values = dataset.isnull()
    total_rows_missing = missing_values.any(axis=1).sum()
    print("{} instances have missing values for year {}".format(total_rows_missing, year))
    missing_values_per_column = missing_values.sum()
    columns_with_missing_values = missing_values_per_column[missing_values_per_column > 0]
    columns_with_missing_values.to_csv("./data/{}_missing_values.csv".format(year))

def plot_light_gbm_fnn_results(year):
    light_gbm_results_file = "./results/models/lightGBM/repeated_kfold/{}_raw_master.csv".format(year)
    light_gbm_results = pd.read_csv(light_gbm_results_file)
    light_gbm_results_long = pd.melt(light_gbm_results, id_vars='Condition', value_vars=['R2'])

    light_gbm_results["model"]="lightGBM"

    fnn_results_file = "./results/models/fnn/repeated_kfold/{}_raw_master.csv".format(year)
    fnn_results = pd.read_csv(fnn_results_file)
    fnn_results["model"]="fNN"

    summary_results = pd.concat([light_gbm_results, fnn_results], ignore_index=True, sort=False)

    fig, ax = plt.subplots(figsize=(4, 4))

    sns.catplot(data=summary_results, kind="bar",x="condition", y="R2", hue="model",
                errorbar="sd", palette="dark", alpha=.6, ax=ax)




if __name__ == '__main__':
    plot_correlation_among_features(2020, "environmental", env_features_to_show)