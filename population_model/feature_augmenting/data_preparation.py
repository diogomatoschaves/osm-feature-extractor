import os
import json
import logging

import geopandas as gpd
import pandas as pd
from rtree.index import Rtree

from population_model.feature_augmenting.features_to_tags import highway_features


def load_data(base_data_dir, file_name):

    file_path = os.path.join(base_data_dir, file_name)

    base_data_df = gpd.read_file(file_path)

    return base_data_df


def save_data(data_df, base_data_dir, file_name):

    logging.info(f"\tSaving {file_name} in {base_data_dir}...")

    file_path = os.path.join(base_data_dir, file_name)

    logging.info(file_path)

    data_df.to_file(file_path, driver="GeoJSON")


def load_json(base_data_dir, file_name):

    file_path = os.path.join(base_data_dir, file_name)

    with open(file_path, "r") as f:
        data = json.load(f)

    return data


def save_json(data, base_data_dir, file_name):

    logging.info(f"\tSaving {file_name} in {base_data_dir}...")

    file_path = os.path.join(base_data_dir, file_name)

    with open(file_path, "w") as f:
        json.dump(data, f)


def import_polygons_data(dataset_dir):
    df = None
    for filename in os.listdir(dataset_dir):
        file_path = os.path.join(dataset_dir, filename)
        if df is not None:
            df = pd.concat([df, gpd.read_file(file_path)])
        else:
            df = gpd.read_file(file_path)

    return df


def import_data(base_data_dir, population_data_folder, countries_file):

    logging.info("\tImporting data...")

    population_data = os.path.join(base_data_dir, population_data_folder)

    countries_df = gpd.read_file(os.path.join(base_data_dir, countries_file))

    base_data_df = import_polygons_data(population_data)

    return base_data_df, countries_df


def intersect_polygons(df_1, df_2, country_code):

    logging.info("\tIntersecting polygons...")

    country_df = df_2[df_2["ISO_A3"] == country_code]

    polygons_df = gpd.overlay(df_1, country_df, how="intersection")

    return polygons_df


def clean_data(base_data_df):

    logging.info("\tCleaning data...")

    base_data_df = base_data_df.drop_duplicates(
        subset=[
            "building_count",
            "highway_length",
            "population",
            "gdp",
            "avg_ts",
            "max_ts",
            "p90_ts",
            "area_km2",
        ]
    )

    base_data_df = base_data_df.drop(
        columns=["one", "avg_ts", "max_ts", "p90_ts", "local_hours", "total_hours"]
    )

    return base_data_df.reset_index(drop=True)


def build_polygons_dataset(polygons_df, base_data_dir, r_tree_file, create_r_tree):

    logging.info("\tInitializing features...")

    polygons_df = initialize_features(polygons_df)

    if create_r_tree:

        logging.info("\tBuilding R-Tree...")

        build_r_tree(polygons_df, base_data_dir, r_tree_file)

    return polygons_df


def build_r_tree(polygons_df, base_data_dir, r_tree_file):

    r_tree_path = os.path.join(base_data_dir, r_tree_file)

    r_tree_index = Rtree(r_tree_path, overwrite=True)

    polygons = polygons_df["geometry"].values
    polygon_indexes = polygons_df.index

    for i, polygon in enumerate(polygons):

        bounding_box = polygon.bounds

        r_tree_index.insert(polygon_indexes[i], bounding_box, polygon)

    r_tree_index.close()


def initialize_features(polygon_df):

    polygon_df["updated"] = False

    for key, value in highway_features.items():
        feature = "_".join([key, value])

        polygon_df[feature] = 0

    return polygon_df


def process_base_data(
    base_data_dir,
    population_data_folder,
    countries_file,
    clean_data_file,
    r_tree_file,
    hexagons_file,
    skip_data_cleaning=False,
    create_r_tree=True,
):

    if skip_data_cleaning:
        logging.info("\tImporting data...")

        base_data_df = load_data(base_data_dir, clean_data_file)
    else:
        base_data_df, countries_df = import_data(
            base_data_dir, population_data_folder, countries_file
        )

        base_data_df = intersect_polygons(base_data_df, countries_df, "GBR")

        base_data_df = clean_data(base_data_df)

        save_data(base_data_df, base_data_dir, clean_data_file)

    polygons_df = build_polygons_dataset(
        base_data_df, base_data_dir, r_tree_file, create_r_tree
    )

    polygons = {
        feature["id"]: feature
        for feature in json.loads(polygons_df.to_json())["features"]
    }

    save_json(polygons, base_data_dir, hexagons_file)
