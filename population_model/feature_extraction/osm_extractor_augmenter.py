import logging
import os

import osmium

from population_model.feature_augmenting.features_to_tags import node_tags, way_tags, area_tags
from population_model.feature_extraction.osm_datamodel import Node, Way, SimpleNode, Area
from population_model.feature_augmenting.features_augmenter import (
    match_nodes_to_polygon,
    match_ways_to_polygon,
    load_r_tree,
    match_areas_to_polygon)
from population_model.feature_extraction.osm_extractor import check_status


class OSMFileHandler(osmium.SimpleHandler):
    def __init__(
        self,
        polygons,
        r_tree_index,
        invalid_location_nodes=None,
        invalid_location_ways=None,
        first_pass=True,
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
        self.first_pass = first_pass

    def node(self, n):

        coords = [n.location.lon, n.location.lat]

        tags = dict(version=n.version, **{tag.k: tag.v for tag in n.tags})

        if self.first_pass:
            for tag_id in node_tags:

                if tag_id in tags:
                    node = Node(n.id, coords, tags=tags)

                    self.polygons = match_nodes_to_polygon(
                        tag_id, [node], self.r_tree_index, self.polygons
                    )

            check_status(self.nodes_counter, "nodes")

            self.nodes_counter += 1

        elif n.id in self.invalid_location_nodes:
            self.nodes[n.id] = SimpleNode(n.id, coords, {})

            check_status(self.nodes_counter, "nodes")

            self.nodes_counter += 1

    def way(self, w):

        if not self.first_pass and w.id not in self.incomplete_ways:
            return

        if any(tag in w.tags for tag in {*way_tags, *area_tags}):

            check_status(self.ways_counter, "ways")

            self.ways_counter += 1

            tags = dict(version=w.version, **{tag.k: tag.v for tag in w.tags})

            nodes = [node.ref for node in w.nodes]

            if not self.first_pass and w.id in self.incomplete_ways:
                coords = [self.nodes[node].coordinates for node in nodes]
            else:
                try:
                    coords = [[n.lon, n.lat] for n in w.nodes]
                except osmium.InvalidLocationError:
                    self.incomplete_ways.add(w.id)
                    self.invalid_location_nodes.update(nodes)
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

        if self.check_for_mutually_exclusive(tag_id, tags):
            return

        way = Way(w.id, coords, nodes, tags=tags)

        self.polygons = match_ways_to_polygon(
            tag_id, [way], self.r_tree_index, self.polygons
        )

    def process_area(self, a, tag_id, tags, nodes, coords):

        if self.check_for_mutually_exclusive(tag_id, tags):
            return

        area = Area(a.id, coords, nodes, tags=tags)

        self.polygons = match_areas_to_polygon(
            tag_id, [area], self.r_tree_index, self.polygons
        )

    @staticmethod
    def check_for_mutually_exclusive(tag_id, tags):
        if tag_id == "cycleway" and tags.get("highway") == "cycleway":
            return True
        elif tag_id == "railway" and tags.get("public_transport") == "station":
            return True
        else:
            return False


def extract_features_augment(osm_data_dir, osm_file, polygons, r_tree_path):

    r_tree_index = load_r_tree(r_tree_path)

    file_path = os.path.join(osm_data_dir, osm_file)

    logging.info(f"\tPerforming first pass on OSM file...")

    osm_handler = OSMFileHandler(polygons, r_tree_index)
    osm_handler.apply_file(file_path, locations=True, idx='flex_mem')

    invalid_ways_ratio = (
        len(osm_handler.incomplete_ways) /
        osm_handler.ways_counter * 100
    )

    logging.info(
        f"\t{round(invalid_ways_ratio, 2)} % of ways could not be processed on first pass"
    )

    if invalid_ways_ratio != 0:

        logging.info(f"\tPerforming second pass on OSM file...")

        osm_handler = OSMFileHandler(
            osm_handler.polygons,
            r_tree_index,
            osm_handler.invalid_location_nodes,
            osm_handler.incomplete_ways,
            first_pass=False,
        )
        osm_handler.apply_file(file_path, locations=True)

    return osm_handler.polygons
