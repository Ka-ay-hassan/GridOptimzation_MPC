

from components.infrastructure.grid._grid import Grid
from components.enums.resource import Resource


class ResourceNetwork(Grid):
    def __init__(self, resource: Resource) -> None:
        self.resource = resource
