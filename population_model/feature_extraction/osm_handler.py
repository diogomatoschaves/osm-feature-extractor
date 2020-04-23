import logging
import pickle

import osmium

from population_model.feature_extraction.osm_datamodel import Node, SimpleNode, Way


node_tags = {"highway"}


class OSMFileHandler(osmium.SimpleHandler):

    def __init__(self):
        osmium.SimpleHandler.__init__(self)

        self.all_nodes = {}
        self.ways = {}
        self.nodes = dict(**{tag: [] for tag in node_tags})

    def node(self, n):

        self.check_status('nodes')

        coords = [n.location.lon, n.location.lat]

        tags = dict(
            version=n.version,
            **{tag.k: tag.v for tag in n.tags},
        )

        node = SimpleNode(n.id, coords, tags=tags)

        self.all_nodes[node.id] = node

        for tag in node_tags:

            if tag in tags:
                node = Node(n.id, coords, tags=tags)

                self.nodes[tag].append(node)

    def way(self, w):

        self.check_status('ways')

        if any(tag in w.tags for tag in ["highway", "cycleway"]):

            node_ids = [node.ref for node in w.nodes]
            coords = [self.all_nodes[node].coordinates for node in node_ids]

            tags = dict(version=w.version, **{tag.k: tag.v for tag in w.tags})

            self.ways[w.id] = Way(w.id, coords, node_ids, tags=tags)

    def area(self, a):
        pass

    def check_status(self, osm_object):

        processed_objects = len(getattr(self, osm_object))

        if processed_objects == 0:
            logging.info(f'Processing {osm_object}...')

        elif processed_objects % 100000 == 0:
            logging.info(f'Processed {processed_objects} {osm_object}...')

    def save(self, path='feature_extraction.pickle'):

        class FeatureExtraction:
            def __init__(self, nodes, ways):
                self.nodes = nodes
                self.ways = ways

        with open(path, 'wb') as f:
            pickle.dump(FeatureExtraction(self.nodes, self.ways), f)
