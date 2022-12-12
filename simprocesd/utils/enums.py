from enum import IntEnum, unique, auto


@unique
class DataStorageType(IntEnum):
    '''Options for how to store data.
    '''
    NONE = auto()  # Do not store.
    MEMORY = auto()  # Store in memory (RAM).
    FILE = auto()  # Store on a drive/disk.
