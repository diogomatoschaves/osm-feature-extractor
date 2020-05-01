import sys
import os
import logging
import json
import time
from collections import defaultdict

from turf import feature_collection

try:
    directory_path = "/".join(
        os.path.dirname(os.path.realpath(__file__)).split("/")[:-1]
    )
    sys.path.append(directory_path)
except NameError:
    pass

from feature_extractor.utils.config_parser import get_config
from feature_extractor.utils.logger import configure_logger
from feature_extractor.feature_augmenting.data_preparation import (
    process_base_data,
    load_json,
)
from feature_extractor.feature_extraction.osm_extractor_augmenter import (
    extract_features_augment,
)


def get_r_tree_name(config):

    input_data_path = os.path.join(config.base_data_dir, config.input_data_file)

    if os.path.exists(input_data_path):
        prefix = config.input_data_file.split('.')[0]

    else:
        prefix = 'world'

    r_tree_file_name = f"{prefix}_rtree"
    r_tree_path = os.path.join(config.base_data_dir, r_tree_file_name)
    r_tree_file_path = r_tree_path + '.idx'

    return r_tree_path, r_tree_file_path


def main():

    # ============================ Setup ===================================

    configure_logger()

    config = get_config()

    # ========================== Load & prepare input data ==============================

    polygon_template = True

    r_tree_path, r_tree_file_path = get_r_tree_name(config)

    if eval(config.process_base_data) or not os.path.exists(r_tree_file_path):
        logging.info("Processing base data...")

        polygon_template = process_base_data(
            config.base_data_dir,
            config.population_data_folder,
            config.countries_file,
            config.input_data_file,
            r_tree_path,
            config.polygons_file,
            import_pop_files=False,
            intersect=False,
            create_r_tree=True,
        )

    else:
        logging.info("Importing preprocessed base data...")

    polygons = load_json(
        base_data_dir=config.base_data_dir, file_name=config.polygons_file
    )

    # ========================= Extract features & Augment data ===============================

    logging.info("Processing OSM data and Augmenting base data...")

    polygons = extract_features_augment(
        config.osm_data_dir, config.osm_file, polygons, r_tree_path, polygon_template
    )

    # ========================== Export Results ===================================

    logging.info("Exporting data...")

    polygons_collection = feature_collection(list(polygons.values()))

    with open(config.out_file, "w") as f:
        json.dump(polygons_collection, f)


if __name__ == "__main__":
    main()
