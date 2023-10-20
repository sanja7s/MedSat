import math
import os

import rasterio
import rasterio.mask
import geopandas
from shapely.geometry import mapping
import pandas as pd
import numpy as np

band_names = ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]

def save_lsoa_as_tiff(lsoa_image_root_dir, sen2_composite, lsoa_id, lsoa_crop, lsoa_transform):
    print("Visualizing lsoa {}".format(lsoa_id))
    lsoa_pixels_output_dir = os.path.join(lsoa_image_root_dir, "lsoa_images")
    if not os.path.exists(lsoa_pixels_output_dir):
        os.makedirs(lsoa_pixels_output_dir)

    lsoa_meta = sen2_composite.meta
    lsoa_meta.update({"driver": "GTiff",
                     "height": lsoa_crop.shape[1],
                     "width": lsoa_crop.shape[2],
                     "transform": lsoa_transform})

    with rasterio.open("{}.tif".format(os.path.join(lsoa_pixels_output_dir, lsoa_id)), "w", **lsoa_meta) as dest:
        dest.write(lsoa_crop)

def extract_lsoa_pixel_statistics(out_image, nodata_value):
    if np.isfinite(nodata_value):
        masked_data = np.ma.masked_where(out_image == nodata_value, out_image)
    else:
        masked_data = np.ma.masked_invalid(out_image)

    median_per_band = np.ma.median(masked_data, axis=(1, 2))
    mean_per_band = masked_data.mean(axis=(1,2))
    std_per_band = masked_data.std(axis=(1, 2))
    min_per_band = masked_data.min(axis=(1, 2))
    max_per_band = masked_data.max(axis=(1, 2))
    lsoa_pixel_statistics = np.concatenate((median_per_band, mean_per_band, std_per_band, min_per_band, max_per_band)).tolist()

    median_col_names = ["median_{}".format(band) for band in band_names]
    mean_col_names = ["mean_{}".format(band) for band in band_names]
    std_col_names = ["std_{}".format(band) for band in band_names]
    min_col_names = ["min_{}".format(band) for band in band_names]
    max_col_names = ["max_{}".format(band) for band in band_names]
    col_names = median_col_names + mean_col_names + std_col_names + min_col_names + max_col_names

    return lsoa_pixel_statistics, col_names


def aggregate_pixel_statistics(image_features):
    #aggregation is performed because an LSOA might lie on the boundaries between
    image_features = image_features.drop(columns=["region", "SEN-2_ID"])
    image_features_mean = image_features.groupby("geography code").agg("mean").filter(regex="^(mean_)|(std_)")
    image_features_max = image_features.groupby("geography code").agg("max").filter(regex="^(max_)")
    image_features_min = image_features.groupby("geography code").agg("min").filter(regex="^(min_)")
    image_features_median = image_features.groupby("geography code").agg("median").filter(regex="^(median_)")

    return pd.concat([image_features_mean, image_features_min, image_features_max, image_features_median],
                     axis=1)

def read_lsoas_with_region_names(lsoa_shapefile, lsoa_region_mapping_file):
    lsoa_shapes = geopandas.read_file(lsoa_shapefile)
    regions_mapping = pd.read_csv(lsoa_region_mapping_file)
    lsoa_shapes = lsoa_shapes.merge(regions_mapping, on="LSOA21CD", how="left")
    return lsoa_shapes

def extract_lsoa_image_features(lsoa_shapefile, lsoa_region_mapping_file, image_dir, num_lsoas_to_visualize=50):

    sen_2_season = os.path.split(image_dir)[1]
    output_file_root_dir = os.path.join("../../../data/point_data/image_features/", sen_2_season)
    if not os.path.exists(output_file_root_dir):
        os.makedirs(output_file_root_dir)

    lsoa_shapes_and_regions = read_lsoas_with_region_names(lsoa_shapefile, lsoa_region_mapping_file)
    print("Number of LSOAs: {}".format(len(lsoa_shapes_and_regions.index)))
    print("LSOA CRS: {}".format(lsoa_shapes_and_regions.crs))
    associations = []

    num_visualized_lsoas = 0
    for image_file in os.listdir(image_dir):
        image_abs_path = os.path.join(image_dir, image_file)
        if image_file.endswith(".tif"):
            with rasterio.open(image_abs_path) as sen2_composite:
                print("Processing image {} with crs {}".format(image_file, sen2_composite.crs))
                match_found=False
                lsoa_shapes_and_regions = lsoa_shapes_and_regions.to_crs(crs=sen2_composite.crs)
                for key, geom in lsoa_shapes_and_regions.geometry.apply(mapping).items():
                    lsoa_id = lsoa_shapes_and_regions.loc[key]["LSOA21CD"]
                    lsoa_region = lsoa_shapes_and_regions.loc[key]["RGN22NM"]
                    try:
                        out_image, out_transform = rasterio.mask.mask(sen2_composite, [geom], crop=True)
                        lsoa_pixels_statistics, col_names = extract_lsoa_pixel_statistics(out_image, sen2_composite.nodata)
                        lsoa_pixels_agg = [lsoa_id, lsoa_region, image_file] + lsoa_pixels_statistics
                        associations.append(lsoa_pixels_agg)
                        if lsoa_region == "London" and num_visualized_lsoas < num_lsoas_to_visualize:
                            save_lsoa_as_tiff(image_dir, sen2_composite, lsoa_id, out_image, out_transform)
                            num_visualized_lsoas = num_visualized_lsoas + 1
                        match_found = True
                    except:
                        pass

                print("LSOA found in image : {}".format(match_found), "Image ID: {}".format(image_file),
                      "Image crs: {}".format(sen2_composite.crs))

    col_names = ["geography code", "region", "SEN-2_ID"] + col_names
    lsoa_image_data = pd.DataFrame(associations, columns=col_names)
    print("Number of matched LSOAs: {}".format(len(lsoa_image_data["geography code"].unique())))
    image_features = aggregate_pixel_statistics(lsoa_image_data)
    lsoa_image_mapping = lsoa_image_data[["geography code", "region", "SEN-2_ID"]]

    image_features.to_csv(os.path.join(output_file_root_dir, "lsoas_pixel_statistics.csv"))
    lsoa_image_mapping.to_csv(os.path.join(output_file_root_dir, "lsoa_image_mapping.csv"))

if __name__ == '__main__':

    lsoa_shapefile_root_dir = "../../../data/auxiliary_data/lsoas_2021/LSOA_(Dec_2021)_Boundaries_Generalised_Clipped_EW_(BGC)"
    lsoa_shapefile = os.path.join(lsoa_shapefile_root_dir,  "LSOA_(Dec_2021)_Boundaries_Generalised_Clipped_EW_(BGC).shp")
    lsoa_region_mapping_file = "../../../data/auxiliary_data/lsoas_regions_mapping.csv"

    image_dir = "../../../data/image_data/England_JJA2020"
    extract_lsoa_image_features(lsoa_shapefile, lsoa_region_mapping_file, image_dir)
