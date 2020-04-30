import logging
import re
from shapely.errors import TopologicalError

from rtree import Rtree
from turf import length, area as polygon_area, line_string, feature_collection, InvalidInput, polygon

from population_model.feature_augmenting.features_to_tags import (
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


def get_features(tags, tag_id, feature_suffix):

    if tag_id in tags:

        if tag_id in unspecific_tags:
            feature_name = tag_id

        else:
            tags_dict = eval(f"{tag_id}_tags")

            try:
                feature_name = tags_dict[tags[tag_id]]
                if feature_suffix not in features_types[feature_name]:
                    return
            except KeyError:
                return

        feature = "_".join([feature_name, feature_suffix])

        return feature

    return


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


def match_nodes_to_polygon(tag_id, nodes, r_tree_index, polygons):

    for node in nodes:

        feature = get_features(node.tags, tag_id, "count")

        if not feature:
            return polygons

        matches = list(r_tree_index.intersection(node.bounds, objects=True))

        for match in matches:
            if node.within(match.object):
                polygons[str(match.id)]["properties"][feature] += 1
                polygons[str(match.id)]["properties"]["updated"] = True

    return polygons


def match_ways_to_polygon(tag_id, ways, r_tree_index, polygons):

    for way in ways:

        feature = get_features(way.tags, tag_id, "length")

        if not feature:
            return polygons

        matches = list(r_tree_index.intersection(way.bounds, objects=True))

        for match in matches:
            
            try:
                intersection = way.intersection(match.object)
            except TopologicalError:
                continue

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

                line_length = length(coords, {"units": "meters"})

                polygons[str(match.id)]["properties"][feature] += line_length
                polygons[str(match.id)]["properties"]["updated"] = True

    return polygons


def match_areas_to_polygon(tag_id, areas, r_tree_index, polygons):

    for area in areas:

        feature = get_features(area.tags, tag_id, "area")

        if not feature:
            return polygons

        matches = list(r_tree_index.intersection(area.bounds, objects=True))

        for match in matches:

            try:
                intersection = area.intersection(match.object)
            except TopologicalError:
                continue

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

                poly_area = polygon_area([coords])

                polygons[str(match.id)]["properties"][feature] += poly_area
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
