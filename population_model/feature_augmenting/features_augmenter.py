from turf import length

from population_model.feature_augmenting.features_to_tags import highway_tags, highway_features


def match_polygons_to_features(
    polygons,
    r_tree_index,
    nodes,
    ways,
    areas=None
):

    updated_polygons = set()

    for node in nodes:

        features = get_feature(node.tags)

        matches = list(r_tree_index.intersection(node.bounds, objects=True))

        for match in matches:
            if node.within(match.object):
                for feature in features:
                    if "count" in feature:
                        polygons[match.id]["properties"][feature] += 1

                        updated_polygons.add(match.id)

    for way in ways:
        features = get_feature(way.tags)

        matches = list(r_tree_index.intersection(way.bounds, objects=True))

        for match in matches:

            intersection = way.intersection(match.object)

            if not intersection.is_empty:

                coords = [list(coord) for coord in intersection.coords]

                line_length = length(coords)

                for feature in features:
                    if "length" in feature:
                        polygons[match.id]["properties"][feature] += line_length

                        updated_polygons.add(match.id)

    return polygons, updated_polygons


def get_feature(tags):

    features = []
    if "highway" in tags:
        try:
            feature_name = highway_tags[tags["highway"]]
            feature_suffix = highway_features[feature_name]

            feature = feature_name + feature_suffix

            features.append(feature)
        except KeyError:
            pass

    if "cycleway" in tags:
        feature_name = "cycleway"
        feature_suffix = highway_features[feature_name]

        feature = feature_name + feature_suffix

        features.append(feature)

    return features
