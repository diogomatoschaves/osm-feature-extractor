import logging
import os
import pickle
from collections import defaultdict
from typing import Sequence

import osmium
from ordered_set import OrderedSet

from population_model.feature_extraction.osm_datamodel import Node, SimpleNode, Way


node_tags = {"highway"}
way_tags = {"highway"}


class OSMFileHandler(osmium.SimpleHandler):
    def __init__(self, bounds=None, missing_edges=None, edges=None):
        osmium.SimpleHandler.__init__(self)

        self.all_nodes = {}
        self.nodes_counter = 0
        self.ways_counter = 0
        self.ways = dict(**{tag: [] for tag in way_tags})
        self.nodes = dict(**{tag: [] for tag in node_tags})
        self.bounds = bounds if bounds else [-180, -90, 180, 90]
        self.border_edges = missing_edges if missing_edges else defaultdict(lambda: {})
        self.edges = set() if not edges else edges

    def node(self, n):

        coords = [n.location.lon, n.location.lat]

        if not self.in_bbox(coords, self.bounds):
            return

        self.check_status(self.nodes_counter, "nodes")

        tags = dict(version=n.version, **{tag.k: tag.v for tag in n.tags},)

        node = SimpleNode(n.id, coords, tags=tags)

        self.all_nodes[node.id] = node

        for tag in node_tags:

            if tag in tags:
                node = Node(n.id, coords, tags=tags)

                self.nodes[tag].append(node)

        self.nodes_counter += 1

    def way(self, w):

        if any(tag in w.tags for tag in ["highway", "cycleway"]):

            nodes = [node.ref for node in w.nodes]

            bool_nodes_in_bounds = {node_id in self.all_nodes for node_id in nodes}

            if True not in bool_nodes_in_bounds:
                return

            self.check_status(self.ways_counter, "ways")

            self.ways_counter += 1

            # if False in bool_nodes_in_bounds:
            if True:

                edges = zip(nodes, nodes[1:])

                nodes_in_bounds = [OrderedSet()]
                coords_in_bounds = [[]]

                for edge in edges:

                    if len(nodes_in_bounds[-1]) > 0 and nodes_in_bounds[-1][-1] != edge[0]:
                        nodes_in_bounds.append(OrderedSet())

                    if edge[0] in self.all_nodes and edge[1] in self.all_nodes:

                        coords = [self.all_nodes[node].coordinates for node in edge]

                        nodes_in_bounds[-1].update(edge)
                        coords_in_bounds[-1].extend(coords)

                    elif edge[0] in self.all_nodes:

                        self.handle_missing_node(
                            edge, edge[1], edge[0], nodes_in_bounds, coords_in_bounds
                        )

                    elif edge[1] in self.all_nodes:

                        self.handle_missing_node(
                            edge, edge[0], edge[1], nodes_in_bounds, coords_in_bounds
                        )

                    else:
                        continue

            else:
                nodes_in_bounds = [nodes]
                coords_in_bounds = [[self.all_nodes[node].coordinates for node in nodes]]

            tags = dict(version=w.version, **{tag.k: tag.v for tag in w.tags})

            for node_ids, coords in zip(nodes_in_bounds, coords_in_bounds):

                if len(coords) < 2:
                    continue

                pairs = list(zip(node_ids, node_ids[1:]))

                if any(p in self.edges for p in pairs):
                    a = 1

                self.edges.update(pairs)

                id_ = w.id

                way = Way(id_, coords, node_ids, tags=tags)

                self.ways["highway"].append(way)

    def area(self, a):
        pass

    def handle_missing_node(
        self, edge, missing_node, existing_node, nodes_in_bounds, coords_in_bounds
    ):

        if edge in self.border_edges:

            node_1_coords = self.border_edges[edge][missing_node]
            node_2_coords = self.all_nodes[existing_node].coordinates

            self.border_edges[edge][existing_node] = node_2_coords

            nodes_in_bounds[-1].update(edge)
            coords_in_bounds[-1].extend([node_1_coords, node_2_coords])

        else:
            self.border_edges[edge][existing_node] = self.all_nodes[existing_node].coordinates

        return nodes_in_bounds, coords_in_bounds

    @staticmethod
    def in_bbox(point: Sequence, bbox: Sequence):
        """
        Checks if point is inside bbox

        :param point: point coordinates [lng, lat]
        :param bbox: bbox [west, south, east, north]
        :return: True if point is inside, False otherwise
        """
        return bbox[0] <= point[0] <= bbox[2] and bbox[1] <= point[1] <= bbox[3]

    @staticmethod
    def check_status(count, obj_name):

        if count == 0:
            logging.info(f"\t\tProcessing {obj_name}...")

        elif count % 100000 == 0:
            logging.info(f"\t\t\tProcessed {count} {obj_name}...")

    def save(self, path=""):

        with open(os.path.join(path, "nodes.pickle"), "wb") as f:
            pickle.dump(self.nodes, f)

        with open(os.path.join(path, "ways.pickle"), "wb") as f:
            pickle.dump(self.ways, f)


def load_osm_data(osm_data_dir):

    with open(os.path.join(osm_data_dir, "nodes.pickle"), "rb") as f:
        nodes = pickle.load(f)

    with open(os.path.join(osm_data_dir, "ways.pickle"), "rb") as f:
        ways = pickle.load(f)

    return nodes, ways


def extract_features(osm_data_dir, osm_file, bounds, border_edges=None, edges=None):

    file_path = os.path.join(osm_data_dir, osm_file)

    osm_handler = OSMFileHandler(bounds, border_edges)
    osm_handler.apply_file(file_path)
    osm_handler.save(osm_data_dir)

    return osm_handler.nodes, osm_handler.ways, osm_handler.border_edges, osm_handler.edges
