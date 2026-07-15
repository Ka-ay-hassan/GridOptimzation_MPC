from components.storages.storage import Storage
from components.enums.resource import Resource


class ResourceStorage(Storage):
    def __init__(self, resource: Resource) -> None:
        self.resource = resource



