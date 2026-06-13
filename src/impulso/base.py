from enum import Enum

class Analysis(Enum):
    IC = 0
    DC = 1
    AC = 2
    TRANSIENT = 3

class TopologyError(Exception):
    pass

type Node = int | str


