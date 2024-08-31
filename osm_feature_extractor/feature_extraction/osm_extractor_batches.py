import logging
import os
import pickle
from collections import defaultdict

import osmium
from ordered_set import OrderedSet

from osm_feature_extractor.feature_augmenting.features_to_tags import node_tags, way_tags
from osm_feature_extractor.feature_extraction.osm_datamodel import Node, SimpleNode, Way
from osm_feature_extractor.feature_extraction.osm_extractor import (
    in_bbox,
    check_status,
)


class OSMFileHandler(osmium.SimpleHandler):
    def __init__(self, bounds=None, missing_edges=None, way_edges=None, batch=None):
        osmium.SimpleHandler.__init__(self)

        self.all_nodes = {}
        self.nodes_counter = 0
        self.ways_counter = 0
        self.ways = dict(**{tag: [] for tag in way_tags})
        self.nodes = dict(**{tag: [] for tag in node_tags})
        self.bounds = bounds if bounds else [-180, -90, 180, 90]
        self.border_edges = missing_edges if missing_edges else defaultdict(lambda: {})
        self.way_edges = way_edges if way_edges else defaultdict(lambda: set())
        self.batch = batch

    def node(self, n):

        coords = [n.location.lon, n.location.lat]

        if not in_bbox(coords, self.bounds):
            return

        check_status(self.nodes_counter, "nodes")

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

            check_status(self.ways_counter, "ways")

            self.ways_counter += 1

            if False in bool_nodes_in_bounds:

                edges = zip(nodes, nodes[1:])

                nodes_in_bounds = [OrderedSet()]
                coords_in_bounds = [[]]

                for edge in edges:

                    if edge in self.way_edges[w.id]:

                        logging.info(f"edge {edge} was not imputed")
                        continue

                    if (
                        len(nodes_in_bounds[-1]) > 0
                        and nodes_in_bounds[-1][-1] != edge[0]
                    ):
                        nodes_in_bounds.append(OrderedSet())

                    if edge[0] in self.all_nodes and edge[1] in self.all_nodes:

                        coords = [self.all_nodes[node].coordinates for node in edge]

                        nodes_in_bounds[-1].update(edge)
                        coords_in_bounds[-1].extend(coords)

                    elif edge[0] in self.all_nodes:

                        nodes_in_bounds, coords_in_bounds = self.handle_missing_node(
                            edge, edge[1], edge[0], nodes_in_bounds, coords_in_bounds
                        )

                    elif edge[1] in self.all_nodes:

                        nodes_in_bounds, coords_in_bounds = self.handle_missing_node(
                            edge, edge[0], edge[1], nodes_in_bounds, coords_in_bounds
                        )

                    else:
                        continue

            else:
                nodes_in_bounds = [nodes]
                coords_in_bounds = [
                    [self.all_nodes[node].coordinates for node in nodes]
                ]

            tags = dict(version=w.version, **{tag.k: tag.v for tag in w.tags})

            for node_ids, coords in zip(nodes_in_bounds, coords_in_bounds):

                if len(coords) < 2:
                    continue

                pairs = list(zip(node_ids, node_ids[1:]))

                self.way_edges[w.id].update({pair for pair in pairs})

                for tag_id in way_tags:

                    if tag_id in tags:

                        if tag_id == "cycleway" and tags.get("highway") == "cycleway":
                            continue

                        way = Way(w.id, coords, node_ids, tags=tags)

                        self.ways[tag_id].append(way)

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
            self.border_edges[edge][existing_node] = self.all_nodes[
                existing_node
            ].coordinates

        return nodes_in_bounds, coords_in_bounds

    def save(self, path=""):

        with open(os.path.join(path, "nodes.pickle"), "wb") as f:
            pickle.dump(self.nodes, f)

        with open(os.path.join(path, "ways.pickle"), "wb") as f:
            pickle.dump(self.ways, f)


def extract_features_batches(osm_file, bounds, border_edges=None, way_edges=None, batch=None):

    osm_handler = OSMFileHandler(bounds, border_edges, way_edges, batch)
    osm_handler.apply_file(osm_file)

    osm_handler.save()

    return (
        osm_handler.nodes,
        osm_handler.ways,
        osm_handler.border_edges,
        osm_handler.way_edges,
    )
