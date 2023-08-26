# Submodule to extract LSOA images and descriptive features from the Sentinel-2 images. 
Running the script `lsoa_images_features_extractor.py` extracts LSOA images from the Sentinel-2 images 
and computes descriptive statistics over the LSOA pixels that can be used as simple LSOA image features. 
To run the script, it is required to have the following folder structure inside the 
`../../../data/` folder:
1. `image_data/{sen_2_season}/` - this folder should contain the Sentinel-2 images for a calendar season
2. `auxiliary_data/lsoas_2021/` - this folder should contain the LSOAs geographical coordinates and shapefiles

As output, the script will create the following two files inside the folder `../../../data/point_data/image_features/{sen_2_season}`:
1. `lsoas_pixel_statistics.csv` - contains the descriptive statistics for every LSOA in the dataset
2. `lsoa_image_mapping.csv` - provides information to which Sentinel-2 images an LSOA belongs.

Additionally, when calling the function `extract_lsoa_image_features`, the user can provide a list of LSOA IDs for which
their Sentinel-2 image can also be saved on the disk for further processing. The LSOA images will be stored in the folder:
`../../../data/image_data/{sen_2_seaon}/lsoa_images`.