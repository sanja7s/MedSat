
# __MEDSAT__

The code for __MEDSAT__: A public health dataset for England featuring satellite imagery and medical prescriptions.


👩‍⚕️ 🏥 🌲 🏡 💊 💉 🧑‍💼 👨‍👩‍👧‍👦 👶 👵


The __MEDSAT__ dataset serves as a comprehensive resource for public and population health studies in England, encompassing medical prescription quantity per capita as outcomes and a wide array of sociodemographic and environmental variables as features. 
In this release, we provide data snapshots for the years 2019 (pre-COVID) and 2020 (COVID). Sociodemographic variables align with the latest UK census from 2021.

![__MEDSAT__  structure](figures/data_diagram_hist.jpg)



Access to the code is available at this respository, while the data can be found at https://tinyurl.com/medsatpoint. The dataset is released under the CC BY-SA 4.0 license.


### THE CODE STRUCTURE 
1. `collate_data` -- contains the code for producing the four data segments from different sources, and merging them into a single dataset, __MEDSAT__.
    - `data_master.ipynb` -- this code collates the 4 segments into single *master data files* for each year. It produces both .csv and .geojson master files as output.
    - `environmental_data_extractor` -- this module produces *environmental point features* and is the only module that requires signing up for an external service, which is Google Earth Engine. The reason is that we collate, process, and analyse enormous amounts of satellite products to calculate the yearly environmental point features. The instructions for signing up and running the extractor code are found in the README file, and we also associated slides with screenshots to help in the process.
    - `image_features_extractor` -- here we provide the code for extracting area-(LSOA)-level features from the Sentinel-2 composite images.  
    - `NHS_prescription_parser` -- this module serves for extracting outcomes for __MEDSAT__ from NHS prescription data.
    - `sociodemographic_data_parser` -- this notebook allows extraction of sociodemographic features per LSOA from the raw files downloaded from the UK ONS website.
2.  `models_and_xai` -- contains the code for predicting and explaining health outcomes from the features.
### THE DATA STRUCTURE 
	- ```auxiliary_data``` -- holds spatial data, i.e., LSOA and Redion shapefiles. 
	- ```point_data/data_sources``` -- contains raw input donwloaded from the UK Census 2021.
	- ```point_data/image_features``` -- contains the features extracted from each image composite band across LSOAs for two seasons: winter (DJF), and summer (JJA) for the year 2020.
	- ```point_data/data_segments``` -- this is where the results from each module parsing different data sources are placed to be merged into yearly master files.

	


> **STEPS**
For each module generating one of the 4 __MEDSAT__ data segments (1-4 below), you will find their own README file inside specifying how to use the code within the module. We also provide a specific conda envrionment .yml specification for each module (or a guide for how to setup GEE in the Google Colab environment in the case of ```environmental_data_extractor```). 
1. run the jupyter notebooks from ```environmental_data_extractor``` to obtain *environmental point features*. Since this runs in the Google Colab environment, the results will get saved into your Google Drive, and you can download and place them into ```data/point_data/data_segments/{year}_environment.csv```
2. run ```NHS_prescriptions_parser``` to obtain *prescrption outcomes* for selected conditions. The resulting outputs will get placed into ```data/point_data/data_segments/{year}_outcomes.csv```
3. `WasdiAverageComposite` runs on WASDI servers to obtain *environmental image features*, i.e., 37 x 4 seasonal Sentinel-2 composite images (totalling ~120 GB per season, i.e., ~600 GB per year). This data is saved on the TUM server (on the data address provided at the beginning of this file). You can download (a part of) this data into ```data/image_data/``` to continue parsing them with the code provided here.
4. run ```sociodemographic_data_parser``` to obtain *sociodemographic features* from the UK census. They will get placed into ```data/point_data/data_segments/controls.csv```
5. ```collate data``` pulls the four extracted data segments into a single *master file* per year saved into ```data/point_data/{year}_spatial_raw_master``` both as .csv and .geojson. 
6. run ```models_and_xai``` to analyse the __MEDSAT__ data.




### PEAKS INTO THE DATASET

#### Example __MEDSAT__  point features
![example __MEDSAT__  point features](figures/maps_data_diagram.jpg)

#### Example __MEDSAT__  image features
![example __MEDSAT__  image features](figures/composite_data_vis.jpg)


