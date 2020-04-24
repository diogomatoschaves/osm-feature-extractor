from collections import namedtuple
from typing import List, Dict
from shapely.geometry import Point, LineString


SimpleNode = namedtuple("Node", ("id", "coordinates", "tags"))


class Node(Point):
    """This class stores data relative to nodes

    Attributes:
        id: ID of Node
        coords (list): coordinates of point
        tags (dict): tags of node
    """

    def __init__(self, id_=None, coords=None, tags=None):
        Point.__init__(self, coords)

        self.id: int = id_
        self.tags: Dict = tags

    @property
    def coordinates(self):
        return [list(coord) for coord in self.coords][0]

    def __getinitargs__(self):
        return self.id, self.coords, self.tags


class Way(LineString):

    """
    This class stores information about osm ways

    Attributes:
        id (int): ID of way
        coords (list): coordinates of LineString
        nodes (list): list of node ids
        tags (dict): dict with tags
    """

    def __init__(self, id_=None, coords=None, nodes=None, tags=None):
        LineString.__init__(self, coords)

        self.id: int = id_
        self.nodes: List[int] = nodes
        self.tags: Dict = tags

    @property
    def coordinates(self):
        return [list(coord) for coord in self.coords]

    def __getinitargs__(self):
        return self.id, self.coords, self.nodes, self.tags
