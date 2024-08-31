import logging
import re
from shapely.errors import TopologicalError

from rtree import Rtree
from turf import length, area as polygon_area, line_string, feature_collection, InvalidInput, polygon

from osm_feature_extractor.feature_augmenting.features_to_tags import (
    features_types,
    building_tags,
    highway_tags,
    cycleway_tags,
    amenity_tags,
    landuse_tags,
    railway_tags,
    public_transport_tags,
    shop_tags,
    unspecific_tags,
    node_tags,
    way_tags,
    area_tags,
)


def load_r_tree(file_path):

    r_tree_index = Rtree(file_path)

    return r_tree_index


def get_features(tags, tag_ids, feature_suffix):

    features = []

    for tag in tag_ids:
        if tag in {*unspecific_tags, "total"}:
            feature_name = tag

        else:
            tags_dict = eval(f"{tag}_tags")

            try:
                feature_name = tags_dict[tags[tag]]
                if feature_suffix not in features_types[feature_name]:
                    continue
            except KeyError:
                continue

        feature = "_".join([feature_name, feature_suffix])

        features.append(feature)

    return features


def get_regex_matches(regex_str):

    pattern = r"\((.*?)\)"

    matches = re.findall(pattern, regex_str)

    matches = [match.replace("(", "").replace(")", "").split(", ") for match in matches]

    return matches


def handle_multi_line_string(multi_line_string):

    matches = get_regex_matches(multi_line_string)

    line_strings = []

    for match in matches:

        coords = [[float(c) for c in coord.split(" ")] for coord in match]

        line_strings.append(line_string(coords))

    return feature_collection(line_strings)


def handle_multi_polygon(multi_polygon):

    matches = get_regex_matches(multi_polygon)

    polygons = []

    for match in matches:

        coords = [[[float(c) for c in coord.split(" ")] for coord in match]]

        try:
            polygons.append(polygon(coords))
        except InvalidInput:
            coords[0].append(coords[0][0])
            polygons.append(polygon(coords))

    return feature_collection(polygons)


def match_nodes_to_polygon(tag_ids, nodes, r_tree_index, polygons):

    for node in nodes:

        features = get_features(node.tags, tag_ids, "count")

        if len(features) == 0:
            return polygons

        matches = list(r_tree_index.intersection(node.point.bounds, objects=True))

        for match in matches:
            if node.point.within(match.object):
                for feature in features:
                    polygons[str(match.id)]["properties"][feature] += 1

                polygons[str(match.id)]["properties"]["updated"] = True

    return polygons


def match_ways_to_polygon(tag_ids, ways, r_tree_index, polygons):

    for way in ways:

        features = get_features(way.tags, tag_ids, "length")

        if len(features) == 0:
            continue

        matches = list(r_tree_index.intersection(way.line_string.bounds, objects=True))

        for match in matches:
            
            try:
                intersection = way.line_string.intersection(match.object)

                if not intersection.is_empty:

                    geom_type = intersection.geom_type

                    if geom_type == "LineString":
                        coords = [list(coord) for coord in intersection.coords]

                    elif geom_type == "MultiLineString":

                        try:
                            coords = handle_multi_line_string(intersection.wkt)
                        except InvalidInput:
                            logging.info(
                                f"Found LineString with only 1 coords: {intersection.wkt}"
                            )
                            continue

                    else:
                        logging.info(f"Found geometry type {geom_type}")
                        continue
                else:
                    continue

            except TopologicalError:
                if len(polygons) == 1:
                    coords = way.line_string.coords
                else:
                    continue

            line_length = round(length(coords, {"units": "meters"}), 2)

            for feature in features:
                polygons[str(match.id)]["properties"][feature] += line_length

            polygons[str(match.id)]["properties"]["updated"] = True

    return polygons


def match_areas_to_polygon(tag_ids, areas, r_tree_index, polygons):

    for area in areas:

        features = get_features(area.tags, tag_ids, "area")

        if len(features) == 0:
            continue

        matches = list(r_tree_index.intersection(area.polygon.bounds, objects=True))

        for match in matches:

            try:
                intersection = area.polygon.intersection(match.object)
                if not intersection.is_empty:

                    geom_type = intersection.geom_type

                    if geom_type == "Polygon":
                        coords = [list(coord) for coord in intersection.exterior.coords]

                    elif geom_type == "MultiPolygon":

                        try:
                            coords = handle_multi_polygon(intersection.wkt)
                        except InvalidInput:
                            logging.info(
                                f"Found Polygon with invalid coordinates: {intersection.wkt}"
                            )
                            continue

                    else:
                        logging.info(f"Found geometry type {geom_type}")
                        continue
                else:
                    continue

            except TopologicalError:
                if len(polygons) == 1:
                    coords = area.polygon.coords
                else:
                    continue

            poly_area = round(polygon_area([coords]), 2)

            for feature in features:
                polygons[str(match.id)]["properties"][feature] += poly_area

                if "building" in feature:
                    feature = feature.replace("_area", "_count")
                    polygons[str(match.id)]["properties"][feature] += 1

            polygons[str(match.id)]["properties"]["updated"] = True

    return polygons


def match_polygons_to_features(polygons, r_tree_path, nodes, ways, areas=None):

    r_tree_index = load_r_tree(r_tree_path)

    logging.info("\t\tMatching node features to polygons...")

    for tag_id, nodes_lst in nodes.items():

        polygons = match_nodes_to_polygon(tag_id, nodes_lst, r_tree_index, polygons)

    logging.info("\t\tMatching way features to polygons...")

    for tag_id, ways_lst in ways.items():

        polygons = match_ways_to_polygon(tag_id, ways_lst, r_tree_index, polygons)

    return polygons
