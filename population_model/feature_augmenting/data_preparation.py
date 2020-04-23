import os
import json

import geopandas as gpd
import pandas as pd

from rtree.index import Index

from population_model.utils.logger import configure_logging
from population_model.feature_augmenting.features_to_tags import highway_features

directory_path = os.path.dirname(os.path.realpath(__file__))

# data_location = os.path.join(directory_path, 'data')

logger = configure_logging()


def import_polygons_data(dataset_dir):
    df = None
    for filename in os.listdir(dataset_dir):
        file_path = os.path.join(dataset_dir, filename)
        if df is not None:
            df = pd.concat([df, gpd.read_file(file_path)])
        else:
            df = gpd.read_file(file_path)

    return df


def import_data(data_folder, base_data_dir, geojson_file="countries.geojson"):

    logger.info('Importing data...')

    countries_df = gpd.read_file(os.path.join(data_folder, geojson_file))

    base_data_df = import_polygons_data(base_data_dir)

    return base_data_df, countries_df


def intersect_polygons(df_1, df_2, country_code):

    logger.info('Intersecting polygons...')

    country_df = df_2[df_2["ISO_A3"] == country_code]

    polygons_df = gpd.overlay(df_1, country_df, how="intersection")

    return polygons_df


def clean_data(base_data_df):

    logger.info('Cleaning data...')

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

    return base_data_df


def build_polygons_tree(polygons_df, r_tree_index=None):

    logger.info('Building R-Tree...')

    if not r_tree_index:
        r_tree_index = Index()

    hexagons_dict = {}

    for i in range(polygons_df.shape[0]):

        geojson = json.loads(polygons_df.iloc[i : i + 1, :].to_json())
        geojson = initialize_features(geojson)

        hexagons_dict[i] = geojson

        polygon = polygons_df.iloc[i:]["geometry"]

        bounding_box = polygon.bbox

        r_tree_index.insert(i, bounding_box, polygon)

    return r_tree_index, hexagons_dict


def initialize_features(geojson):

    for key, value in highway_features.items():
        geojson["properties"][key + value] = 0

    return geojson


def process_base_data(data_folder, files_dir="kontur-tiles-pop"):

    base_data_dir = os.path.join(data_folder, files_dir)

    base_data_df, countries_df = import_data(data_folder, base_data_dir)

    polygons_df = intersect_polygons(base_data_df, countries_df, 'GBR')

    polygons_df = clean_data(polygons_df)

    r_tree_index, hexagons_dict = build_polygons_tree(polygons_df)

    return r_tree_index, hexagons_dict
