import sys
import os
import logging
import json

from turf import feature_collection

try:
    directory_path = "/".join(
        os.path.dirname(os.path.realpath(__file__)).split("/")[:-1]
    )
    sys.path.append(directory_path)
except NameError:
    pass

from osm_feature_extractor.utils.config_parser import get_config
from osm_feature_extractor.utils.logger import configure_logger
from osm_feature_extractor.feature_extraction.osm_analyzer import analyze_osm_file
from osm_feature_extractor.feature_augmenting.data_preparation import (
    process_base_data,
    load_json,
)
from osm_feature_extractor.feature_extraction.osm_extractor_augmenter import (
    extract_features_augment,
)


def get_r_tree_name(config):

    input_data_path = config.input_polygons_file

    if os.path.exists(input_data_path):
        prefix = config.input_polygons_file.split('/')[-1].split('.')[0]

    else:
        prefix = 'world'

    r_tree_file_name = f"{prefix}_rtree"
    r_tree_path = os.path.join(config.osm_extractor_files_dir, r_tree_file_name)
    r_tree_file_path = r_tree_path + '.idx'

    return r_tree_path, r_tree_file_path


def extract_features(config):

    # ========================== Load & prepare input data ==============================

    r_tree_path, r_tree_file_path = get_r_tree_name(config)

    if config.process_base_data or not os.path.exists(r_tree_file_path):
        logging.info("Processing base data...")

        process_base_data(
            config.osm_extractor_files_dir,
            config.input_polygons_file,
            r_tree_path,
            config.polygons_file,
            create_r_tree=False,
        )

    else:
        logging.info("Importing preprocessed base data...")

    polygons = load_json(
        osm_extractor_files_dir=config.osm_extractor_files_dir, file_name=config.polygons_file
    )

    # ========================= Extract features & Augment data ===============================

    logging.info("Processing OSM data and Augmenting base data...")

    polygons = extract_features_augment(config.osm_file, polygons, r_tree_path)

    # ========================== Export Results ===================================

    logging.info("Exporting data...")

    polygons_collection = feature_collection(list(polygons.values()))

    with open(config.output_file, "w") as f:
        json.dump(polygons_collection, f)


def analyze_file(config):

    filename = config.osm_file.split('/')[-1]

    logging.info(f"Analyzing {filename} OSM file...")
    analysis = analyze_osm_file(config.osm_file)

    logging.info(f"\tNodes: {analysis[0]}")
    logging.info(f"\tWays: {analysis[1]}")
    logging.info(f"\tBounds: {analysis[2]}")
    logging.info(f"\tCentroid: {analysis[3]}")


def main():

    # ============================ Setup ===================================

    configure_logger()

    config = get_config()

    if not os.path.exists(config.osm_extractor_files_dir):
        os.makedirs(config.osm_extractor_files_dir)

    if config.command == "extract":
        return extract_features(config)

    elif config.command == "analyze":
        return analyze_file(config)


if __name__ == "__main__":
    main()
