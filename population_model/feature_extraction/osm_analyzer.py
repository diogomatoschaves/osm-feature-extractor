import logging
import os

import osmium
import numpy as np
from scipy import stats


class OSMFileAnalyzer(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

        self.nodes_counter = 0
        self.bbox = [np.inf, np.inf, -np.inf, -np.inf]
        self.centroid = [0, 0]
        self.previous_centroid = [0, 0]
        self.variance = [0, 0]

    def node(self, n):

        coords = [n.location.lon, n.location.lat]

        if self.nodes_counter % 1e6 == 0:
            logging.debug(f"\t\tProcessed {self.nodes_counter} nodes")

        self.nodes_counter += 1

        self.previous_centroid = self.centroid

        self.centroid = [
            self.update_centroid(self.centroid[0], coords[0]),
            self.update_centroid(self.centroid[1], coords[1]),
        ]

        self.variance = [
            self.update_std(
                self.variance[0], self.previous_centroid[0], self.centroid[0], coords[0]
            ),
            self.update_std(
                self.variance[1], self.previous_centroid[1], self.centroid[1], coords[1]
            ),
        ]

        self.bbox = self.update_bbox(self.bbox, coords)

    def update_centroid(self, previous, new):

        return previous + (new - previous) / self.nodes_counter

    @staticmethod
    def update_std(previous_std, previous_mean, new_mean, new_point):

        variance = previous_std + (new_point - previous_mean) * (new_point - new_mean)

        return variance

    @staticmethod
    def update_bbox(bounding_box, coords):

        if bounding_box[0] > coords[0]:
            bounding_box[0] = coords[0]
        if bounding_box[1] > coords[1]:
            bounding_box[1] = coords[1]
        if bounding_box[2] < coords[0]:
            bounding_box[2] = coords[0]
        if bounding_box[3] < coords[1]:
            bounding_box[3] = coords[1]

        return bounding_box


def analyze_osm_file(osm_data_dir, osm_file):

    file_path = os.path.join(osm_data_dir, osm_file)

    osm_handler = OSMFileAnalyzer()
    osm_handler.apply_file(file_path)

    std = [
        np.sqrt(osm_handler.variance[0] / osm_handler.nodes_counter),
        np.sqrt(osm_handler.variance[1] / osm_handler.nodes_counter),
    ]

    return osm_handler.nodes_counter, osm_handler.bbox, osm_handler.centroid, std


def split_bounds(number_nodes, bbox, centroid, std, max_nodes_box=5e6):

    xy_divisions = []

    number_splits = np.ceil(np.sqrt(number_nodes / max_nodes_box))

    for i in range(2):

        distribution = stats.norm(loc=centroid[i], scale=std[i])

        bounds_for_range = distribution.cdf([bbox[i], bbox[i + 2]])

        pp = np.linspace(*bounds_for_range, num=int(number_splits + 1))

        divisions = distribution.ppf(pp)

        divisions[0] = bbox[i]
        divisions[-1] = bbox[i + 2]

        xy_divisions.append(divisions)

    return xy_divisions
