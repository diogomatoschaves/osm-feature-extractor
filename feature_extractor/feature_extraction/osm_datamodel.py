from abc import ABC
from collections import namedtuple
from typing import List, Dict
from shapely.geometry import Point, LineString, Polygon

SimpleNode = namedtuple("Node", ("id", "coordinates", "tags"))


class Node:
    """This class stores data relative to nodes

    Attributes:
        id: ID of Node
        coords (list): coordinates of point
        tags (dict): tags of node
    """

    def __init__(self, id_=None, coords=None, tags=None):

        point = Point(coords)

        self.id: int = id_
        self.tags: Dict = tags
        self.point = point

    @property
    def coordinates(self):
        return [list(coord) for coord in self.point.coords][0]

    def __getinitargs__(self):
        return self.id, self.point.coords, self.tags


class Way:

    """
    This class stores information about osm ways

    Attributes:
        id (int): ID of way
        coords (list): coordinates of LineString
        nodes (list): list of node ids
        tags (dict): dict with tags
    """

    def __init__(self, id_=None, coords=None, nodes=None, tags=None):
        line_string = LineString(coords)

        self.id: int = id_
        self.nodes: List[int] = nodes
        self.tags: Dict = tags
        self.line_string: LineString = line_string

    @property
    def coordinates(self):
        return [list(coord) for coord in self.line_string.coords]

    def __getinitargs__(self):
        return self.id, self.line_string.coords, self.nodes, self.tags


class Area:

    """
    This class stores information about osm areas

    Attributes:
        id (int): ID of way
        coords (list): coordinates of LineString
        nodes (list): list of node ids
        tags (dict): dict with tags
    """

    def __init__(self, id_=None, coords=None, nodes=None, tags=None):
        polygon = Polygon(coords)

        self.id: int = id_
        self.nodes: List[int] = nodes
        self.tags: Dict = tags
        self.polygon = polygon

    @property
    def coordinates(self):
        return [list(coord) for coord in self.polygon.exterior.coords]

    def __getinitargs__(self):
        return self.id, self.polygon.exterior.coords, self.nodes, self.tags
