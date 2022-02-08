from enum import IntEnum, unique, auto


@unique
class DataStorageType(IntEnum):
    NONE = auto()
    MEMORY = auto()
    FILE = auto()
