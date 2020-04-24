import logging
import re

from rtree import Rtree
from turf import length, line_string, feature_collection, InvalidInput

from population_model.feature_augmenting.features_to_tags import (
    highway_tags,
    highway_features,
)


def load_r_tree(file_path):

    r_tree_index = Rtree(file_path)

    return r_tree_index


def get_features(tags):

    features = []
    if "highway" in tags:
        try:
            feature_name = highway_tags[tags["highway"]]
            feature_suffix = highway_features[feature_name]

            feature = '_'.join([feature_name, feature_suffix])

            features.append(feature)
        except KeyError:
            pass

    if "cycleway" in tags:
        feature_name = "highway_cycleway"
        feature_suffix = highway_features[feature_name]

        feature = '_'.join([feature_name, feature_suffix])

        features.append(feature)

    return features


def handle_multi_line_string(multi_line_string):

    pattern = r"\((.*?)\)"

    matches = re.findall(pattern, multi_line_string)

    line_strings = []

    for match in matches:

        clean_match = match.replace('(', '').replace(')', '').split(', ')

        coords = [[float(c) for c in coord.split(' ')] for coord in clean_match]

        line_strings.append(line_string(coords))

    return feature_collection(line_strings)


def match_polygons_to_features(polygons, r_tree_path, nodes, ways, areas=None):

    r_tree_index = load_r_tree(r_tree_path)

    updated_polygons = set()

    logging.info("\tMatching node features to polygons...")

    for tag_id, nodes_lst in nodes.items():

        for node in nodes_lst:

            features = get_features(node.tags)

            matches = list(r_tree_index.intersection(node.bounds, objects=True))

            for match in matches:
                if node.within(match.object):
                    for feature in features:
                        if "count" in feature:
                            polygons[str(match.id)]["properties"][feature] += 1
                            polygons[str(match.id)]["properties"]["updated"] = True

                            updated_polygons.add(match.id)

    logging.info("\tMatching way features to polygons...")

    for tag_id, ways_lst in ways.items():
        for way in ways_lst:
            features = get_features(way.tags)

            matches = list(r_tree_index.intersection(way.bounds, objects=True))

            for match in matches:

                intersection = way.intersection(match.object)

                if not intersection.is_empty:

                    geom_type = intersection.geom_type

                    if geom_type == 'LineString':
                        coords = [list(coord) for coord in intersection.coords]

                    elif geom_type == 'MultiLineString':

                        try:
                            coords = handle_multi_line_string(intersection.wkt)
                        except InvalidInput:
                            logging.info(f'Found LineString with only 1 coords: {intersection.wkt}')
                            continue

                    else:
                        logging.info(f'Found geometry type {geom_type}')

                        continue

                    line_length = length(coords)

                    for feature in features:
                        if "length" in feature:
                            polygons[str(match.id)]["properties"][feature] += line_length
                            polygons[str(match.id)]["properties"]["updated"] = True

                            updated_polygons.add(match.id)

    return polygons, updated_polygons
