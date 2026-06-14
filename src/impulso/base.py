from enum import Enum

class Analysis(Enum):
    IC = 0
    DC = 1
    AC = 2
    TRANSIENT = 3

class TopologyError(Exception):
    pass

'''
For now, we still allow str | int. str is required for
compound components, which generate their own disguised
internal nodes. int is easier for the user to query
node voltages. Leave it like it as for the time being.
'''
type Node = int | str



