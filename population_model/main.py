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

from population_model.feature_augmenting.features_augmenter import (
    match_polygons_to_features,
)
from population_model.feature_extraction.osm_analyzer import (
    analyze_osm_file,
    split_bounds,
)
from population_model.utils.config_parser import get_config
from population_model.utils.logger import configure_logger
from population_model.feature_augmenting.data_preparation import (
    process_base_data,
    load_json,
)
from population_model.feature_extraction.osm_extractor_batches import (
    extract_features_batches,
)
from population_model.feature_extraction.osm_extractor_augmenter import (
    extract_features_augment,
)


def osm_extract_in_batches(config, hexagons):

    logging.info("\tAnalyzing OSM file...")

    nr_nodes, bbox, centroid, std = analyze_osm_file(
        config.osm_data_dir, config.osm_file
    )

    split_lng, split_lat = split_bounds(
        nr_nodes, bbox, centroid, std, max_nodes_box=9e6
    )

    number_batches = (len(split_lng) - 1) ** 2

    logging.info(f"\t\tFile will be processed in {number_batches} batches...")

    r_tree_path = os.path.join(config.base_data_dir, config.r_tree_file)

    i = 1

    border_edges = defaultdict(lambda: {})
    way_edges = defaultdict(lambda: set())

    for lng_bounds in zip(split_lng, split_lng[1:]):
        for lat_bounds in zip(split_lat, split_lat[1:]):

            bounds = (lng_bounds[0], lat_bounds[0], lng_bounds[1], lat_bounds[1])

            logging.info(f"\tProcessing OSM data for batch {i}: {bounds}...")

            nodes, ways, border_edges, way_edges = extract_features_batches(
                config.osm_data_dir, config.osm_file, bounds, border_edges, way_edges, i
            )

            # ===========================  =================================

            logging.info(f"\tAugmenting data for batch {i}: {bounds}...")

            hexagons = match_polygons_to_features(hexagons, r_tree_path, nodes, ways)

            i += 1

    return hexagons


def osm_extract_augment(config, hexagons):

    r_tree_path = os.path.join(config.base_data_dir, config.r_tree_file)

    hexagons = extract_features_augment(
        config.osm_data_dir, config.osm_file, hexagons, r_tree_path
    )

    return hexagons


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
            create_r_tree=False,
        )

    else:
        logging.info("Importing preprocessed base data...")

    time.sleep(5)

    hexagons = load_json(
        base_data_dir=config.base_data_dir, file_name=config.hexagons_file
    )

    # ========================= Extract features & Augment data ===============================

    logging.info("Processing OSM data and Augmenting base data...")

    if eval(config.process_in_batches):

        hexagons = osm_extract_in_batches(config, hexagons)

    else:
        hexagons = osm_extract_augment(config, hexagons)

    # ========================== Export Results ===================================

    logging.info("Exporting data...")

    polygons_collection = feature_collection(list(hexagons.values()))

    with open(config.out_file, "w") as f:
        json.dump(polygons_collection, f)


if __name__ == "__main__":
    main()
