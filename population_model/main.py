import logging
import os
import sys
import json
import time

from turf import feature_collection

from population_model.feature_augmenting.features_augmenter import (
    match_polygons_to_features,
)
from population_model.utils.config_parser import get_config
from population_model.utils.logger import configure_logger
from population_model.feature_augmenting.data_preparation import (
    process_base_data,
    load_json,
)
from population_model.feature_extraction.osm_handler import (
    extract_features,
    load_osm_data,
)

# directory_path = '/'.join(os.path.dirname(os.path.realpath(__file__)).split('/')[:-1])

# sys.path.append(directory_path)


def main():

    # ============================ Setup ===================================

    configure_logger()

    config = get_config()

    # ========================== Load & prepare input data ==============================

    if eval(config.process_base_data):
        logging.info("Processing base data...")

        process_base_data(
            config.base_data_dir,
            config.population_data_folder,
            config.countries_file,
            config.clean_data_file,
            config.r_tree_file,
            config.hexagons_file,
            skip_data_cleaning=True,
            create_r_tree=False
        )

    else:
        logging.info("Importing preprocessed base data...")

    time.sleep(5)

    hexagons = load_json(
        base_data_dir=config.base_data_dir, file_name=config.hexagons_file
    )

    # ========================= Extract features ===============================

    if eval(config.process_osm_data):

        logging.info("Processing OSM data...")

        nodes, ways = extract_features(config.osm_data_dir, config.osm_file)

    else:
        logging.info("Importing preprocessed OSM data...")

        nodes, ways = load_osm_data(config.osm_data_dir)

    # =========================== Augment data =================================

    logging.info("Augmenting data...")

    r_tree_path = os.path.join(config.base_data_dir, config.r_tree_file)

    hexagons, updated_polygons = match_polygons_to_features(
        hexagons, r_tree_path, nodes, ways
    )

    # ========================== Export Results ===================================

    logging.info("Exporting data...")

    polygons_collection = feature_collection(list(hexagons.values()))

    with open(config.out_file, "w") as f:
        json.dump(polygons_collection, f)

    return updated_polygons


if __name__ == "__main__":
    updated_polygons = main()
