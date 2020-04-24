import logging
import os
import pickle

import osmium

from population_model.feature_extraction.osm_datamodel import Node, SimpleNode, Way


node_tags = {"highway"}
way_tags = {"highway"}


class OSMFileHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

        self.all_nodes = {}
        self.nodes_counter = 0
        self.ways_counter = 0
        self.ways = dict(**{tag: [] for tag in way_tags})
        self.nodes = dict(**{tag: [] for tag in node_tags})

    def node(self, n):

        self.check_status(self.nodes_counter, "nodes")

        coords = [n.location.lon, n.location.lat]

        tags = dict(version=n.version, **{tag.k: tag.v for tag in n.tags},)

        node = SimpleNode(n.id, coords, tags=tags)

        self.all_nodes[node.id] = node

        for tag in node_tags:

            if tag in tags:
                node = Node(n.id, coords, tags=tags)

                self.nodes[tag].append(node)

        self.nodes_counter += 1

    def way(self, w):

        self.check_status(self.ways_counter, "ways")

        if any(tag in w.tags for tag in ["highway", "cycleway"]):

            node_ids = [node.ref for node in w.nodes]
            coords = [self.all_nodes[node].coordinates for node in node_ids]

            tags = dict(version=w.version, **{tag.k: tag.v for tag in w.tags})

            self.ways["highway"].append(Way(w.id, coords, node_ids, tags=tags))

        self.ways_counter += 1

    def area(self, a):
        pass

    @staticmethod
    def check_status(count, obj_name):

        if count == 0:
            logging.info(f"\tProcessing {obj_name}...")

        elif count % 100000 == 0:
            logging.info(f"\t\tProcessed {count} {obj_name}...")

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


def extract_features(osm_data_dir, osm_file):

    file_path = os.path.join(osm_data_dir, osm_file)

    osm_handler = OSMFileHandler()
    osm_handler.apply_file(file_path)
    osm_handler.save(osm_data_dir)

    return osm_handler.nodes, osm_handler.ways
