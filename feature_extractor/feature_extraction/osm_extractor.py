import logging
import os
import pickle
from typing import Sequence


def in_bbox(point: Sequence, bbox: Sequence):
    """
    Checks if point is inside bbox

    :param point: point coordinates [lng, lat]
    :param bbox: bbox [west, south, east, north]
    :return: True if point is inside, False otherwise
    """
    return bbox[0] <= point[0] <= bbox[2] and bbox[1] <= point[1] <= bbox[3]


def check_status(count, obj_name):
    """
    Checks status of the osm file processing and prints status
    :param count: number of osm objects currently processed
    :param obj_name: osm object name
    :return: None
    """

    if count == 0:
        logging.info(f"\t\tProcessing {obj_name}...")

    elif count % 100000 == 0:
        logging.info(f"\t\t\tProcessed {count} {obj_name}...")


def load_osm_data(osm_data_dir):
    """
    Loads saved nodes and ways. Only used if nodes and ways are saved in memory.
    :param osm_data_dir: osm data directory
    :return: Loaded nodes and ways
    """

    with open(os.path.join(osm_data_dir, "nodes.pickle"), "rb") as f:
        nodes = pickle.load(f)

    with open(os.path.join(osm_data_dir, "ways.pickle"), "rb") as f:
        ways = pickle.load(f)

    return nodes, ways
