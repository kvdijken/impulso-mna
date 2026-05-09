from enum import Enum

class Analysis(Enum):
    DC = 1
    AC = 2
    TRANSIENT = 3

class TopologyError(Exception):
    pass


