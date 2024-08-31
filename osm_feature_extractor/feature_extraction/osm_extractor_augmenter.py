import logging
import os

import osmium
from shapely.geometry import MultiPoint

from osm_feature_extractor.feature_augmenting.features_to_tags import node_tags, way_tags, area_tags
from osm_feature_extractor.feature_extraction.osm_datamodel import Node, Way, SimpleNode, Area
from osm_feature_extractor.feature_augmenting.features_augmenter import (
    match_nodes_to_polygon,
    match_ways_to_polygon,
    load_r_tree,
    match_areas_to_polygon)
from osm_feature_extractor.feature_extraction.osm_extractor import check_status


class OSMFileHandler(osmium.SimpleHandler):
    """
    Main OSM file processor. Takes an osm file and parses every node and way, checking
    if they belong to any of the specified tags, and if so, passes the node / way to
    the respective feature augmenter, which will in turn map those objects to the geojson
    containing the polygon(s) of the area in study.

    """

    def __init__(
        self,
        polygons,
        r_tree_index,
        invalid_location_nodes=None,
        invalid_location_ways=None,
    ):
        osmium.SimpleHandler.__init__(self)

        self.nodes_counter = 0
        self.ways_counter = 0
        self.invalid_location_nodes = (
            invalid_location_nodes if invalid_location_nodes else set()
        )
        self.incomplete_ways = (
            invalid_location_ways if invalid_location_ways else set()
        )
        self.polygons = polygons
        self.r_tree_index = r_tree_index
        self.nodes = {}
        self.convex_hull = []

    def node(self, n):

        coords = [n.location.lon, n.location.lat]

        tags = {**{"version": n.version}, **{tag.k: tag.v for tag in n.tags}}

        check_status(self.nodes_counter, "nodes")

        self.nodes_counter += 1

        node = Node(n.id, coords, tags=tags)

        existing_tags = set(tags).intersection(node_tags)

        if len(existing_tags) != 0:
            self.polygons = match_nodes_to_polygon(
                existing_tags, [node], self.r_tree_index, self.polygons
            )

    def way(self, w):

        check_status(self.ways_counter, "ways")

        self.ways_counter += 1

        if any(tag in w.tags for tag in {*way_tags, *area_tags}):

            tags = {**{"version": w.version}, **{tag.k: tag.v for tag in w.tags}}

            nodes = [node.ref for node in w.nodes]

            try:
                coords = [[n.lon, n.lat] for n in w.nodes]
            except osmium.InvalidLocationError:
                return

            if nodes[0] == nodes[-1]:
                for tag_id in area_tags:
                    if tag_id in tags:
                        self.process_area(w, tag_id, tags, nodes, coords)
            else:
                for tag_id in way_tags:
                    if tag_id in tags:
                        self.process_way(w, tag_id, tags, nodes, coords)

    def process_way(self, w, tag_id, tags, nodes, coords):
        """
        Creates a Way object and sends it to the feature augmenter for ways

        :param w: osm way object
        :param tag_id: tag being analysed
        :param tags: osm object tags
        :param nodes: nodes belonging to way
        :param coords: coordinates of nodes in way
        :return: None
        """

        if self.check_for_mutually_exclusive(tag_id, tags):
            return

        way = Way(w.id, coords, nodes, tags=tags)

        self.polygons = match_ways_to_polygon(
            [tag_id], [way], self.r_tree_index, self.polygons
        )

    def process_area(self, a, tag_id, tags, nodes, coords):

        """
       Creates an Area object and sends it to the feature augmenter for areas

       :param a: osm area object
       :param tag_id: tag being analysed
       :param tags: osm object tags
       :param nodes: nodes belonging to area
       :param coords: coordinates of nodes in area
       :return: None
       """

        if self.check_for_mutually_exclusive(tag_id, tags):
            return

        area = Area(a.id, coords, nodes, tags=tags)

        self.polygons = match_areas_to_polygon(
            [tag_id], [area], self.r_tree_index, self.polygons
        )

    @staticmethod
    def check_for_mutually_exclusive(tag_id, tags):
        if tag_id == "cycleway" and tags.get("highway") == "cycleway":
            return True
        elif tag_id == "railway" and tags.get("public_transport") == "station":
            return True
        else:
            return False


def extract_features_augment(osm_file, polygons, r_tree_path):
    """
    Method that wraps the calls to the OSMFileHandler class and returns the results

    :param osm_file: Path to the osm file
    :param polygons: GeoJSON object with polygons to be mapped
    :param r_tree_path: path to the RTree index files
    :return: mapped polygons
    """

    r_tree_index = load_r_tree(r_tree_path)

    logging.info(f"\tParsing OSM file: {osm_file}...")

    osm_handler = OSMFileHandler(polygons, r_tree_index)
    osm_handler.apply_file(osm_file, locations=True, idx='flex_mem')

    return osm_handler.polygons
