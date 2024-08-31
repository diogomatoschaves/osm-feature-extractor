import os
import json
import logging

import geopandas as gpd
from rtree.index import Rtree

from osm_feature_extractor.feature_augmenting.features_to_tags import (
    features_types,
    building_tags,
    highway_tags,
    cycleway_tags,
    amenity_tags,
    landuse_tags,
    railway_tags,
    public_transport_tags,
    shop_tags,
    unspecific_tags,
    node_tags,
    way_tags,
    area_tags,
)


def load_data(file_path):
    """
    Loads base data from file if it exists, otherwise loads a polygon
    from template.geojson

    :param file_path: Path to file with the polygon geojson features to be mapped
    :return: base data dataframe
    """

    base_data_df = gpd.read_file(file_path)

    return base_data_df


def save_data(data_df, base_data_dir, file_name):
    """
    Saves GeoDataFrame onto disk

    :param data_df: DataFrame to be saved
    :param base_data_dir: path to base data directory
    :param file_name: name of file to be saved
    :return: None
    """

    logging.info(f"\tSaving {file_name} in {base_data_dir}...")

    file_path = os.path.join(base_data_dir, file_name)

    logging.info(file_path)

    data_df.to_file(file_path, driver="GeoJSON")


def load_json(osm_extractor_files_dir, file_name):
    """
    Loads dat from JSON file

    :param osm_extractor_files_dir: path to base data directory
    :param file_name: name of file with base data
    :return: Loaded data
    """

    file_path = os.path.join(osm_extractor_files_dir, file_name)

    with open(file_path, "r") as f:
        data = json.load(f)

    return data


def save_json(data, osm_extractor_files_dir, file_name):
    """
    :param data: data to be saved
    :param osm_extractor_files_dir: path to base data directory
    :param file_name: name of file to be saved
    :return: None
    """

    logging.info(f"\tSaving {file_name} in {osm_extractor_files_dir}...")

    file_path = os.path.join(osm_extractor_files_dir, file_name)

    with open(file_path, "w") as f:
        json.dump(data, f)


def build_r_tree(polygons_df, r_tree_path, create_r_tree):
    """
    Build RTree index with input data polygons. To be used later on on polygons intersections

    :param polygons_df: GeoDataFrame with polygons to be indexed
    :param r_tree_path: path of where to save the RTree index on disk
    :param create_r_tree: if RTree should be created or not
    :return: None
    """

    r_tree_file_path = r_tree_path + '.idx'

    if create_r_tree or not os.path.exists(r_tree_file_path):

        logging.info("\tBuilding R-Tree...")

        r_tree_index = Rtree(r_tree_path, overwrite=True)

        polygons = polygons_df["geometry"].values
        polygon_indexes = polygons_df.index

        for i, polygon in enumerate(polygons):

            bounding_box = polygon.bounds

            r_tree_index.insert(polygon_indexes[i], bounding_box, polygon)

        r_tree_index.close()


def initialize_features(polygon_df):
    """
    Initializes features that will be extracted at a later stage with 0 values

    :param polygon_df: GeoDataFrame with polygons that will be initialized
    :return: The GeoDataFrame with initialized features
    """

    logging.info("\tInitializing features...")

    polygon_df["updated"] = False

    for obj in [("node", "count"), ("way", "length"), ("area", "area")]:

        object_tags = eval(f"{obj[0]}_tags")

        for tag in object_tags:

            if tag in unspecific_tags:
                feature_name = tag

                feature = "_".join([feature_name, obj[1]])

                polygon_df[feature] = 0

            else:
                features_dict = eval(f"{tag}_tags")

                features_set = {value for value in features_dict.values()}

                for feature_name in features_set:

                    if obj[1] in features_types[feature_name]:

                        feature = "_".join([feature_name, obj[1]])

                        polygon_df[feature] = 0

    return polygon_df


def process_base_data(
    osm_extractor_files_dir,
    input_polygons_file,
    r_tree_path,
    polygons_file,
    create_r_tree=True,
):
    """
    Methods that wraps all the data processing logic.

    :param osm_extractor_files_dir: path to extractor files data directory
    :param input_polygons_file: name of file with base data
    :param r_tree_path: path of where to save the RTree index on disk
    :param polygons_file: name of file where initialized GeoDataFrame will be saved
    :param create_r_tree: if RTree should be created or not
    :return: None
    """

    logging.info("\tImporting data...")

    base_data_df = load_data(input_polygons_file)

    polygons_df = initialize_features(base_data_df)

    build_r_tree(polygons_df, r_tree_path, create_r_tree)

    polygons = {
        feature["id"]: feature
        for feature in json.loads(polygons_df.to_json())["features"]
    }

    save_json(polygons, osm_extractor_files_dir, polygons_file)
