
# __MEDSAT__

The code for __MEDSAT__: A public health dataset for England featuring satellite imagery and medical prescriptions.


👩‍⚕️ 🏥 🌲 🏡 💊 💉 🧑‍💼 👨‍👩‍👧‍👦 👶 👵


The __MEDSAT__ dataset serves as a comprehensive resource for public and population health studies in England, encompassing medical prescription quantity per capita as outcomes and a wide array of sociodemographic and environmental variables as features. 
In this release, we provide data snapshots for the years 2019 (pre-COVID) and 2020 (COVID). Sociodemographic variables align with the latest UK census from 2021.

![__MEDSAT__  structure](figures/data_diagram_hist.jpg)



Access to the code is available at this respository, while the data can be found at \url{https://tinyurl.com/medsatpoint}. The dataset is released under the CC BY-SA 4.0 license.


### HOW TO USE THIS CODE

> **STEPS**
1. run the jupyter notebooks from ```environmental_data_extractor``` to obtain environmental indicators.
2. run ```NHS_prescriptions_parser``` to obtain prescrptions for selected conditions.
3. run ```sociodemographic_data_parser``` to obtain sociodemographic indicators from the UK census.
4. ```colate data``` pulls three extracted data sources into a single master file, i.e., __MEDSAT__.
5. run ```models_and_xai``` to analyse the data.



### PEAKS INTO THE DATASET

#### Example __MEDSAT__  point features
![example __MEDSAT__  point features](figures/maps_data_diagram.jpg)


#### Example __MEDSAT__  image features
![example __MEDSAT__  image features](figures/composite_data_vis.jpg)


#### Example SHAP results
![example SHAP features diabetes](figures/appendix_shap_values_diabetes.pdf)
![example SHAP features total](figures/appendix_shap_values_total.pdf)


> **NOTE**: **WAIT** Happy new project.


❤️ this project
