##################################################
## Enumeration for objects within the maze
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

from enum import Enum


class MazeObject(Enum):
    EMPTY = 0
    WALL = 1
    AGENT = 2
    REWARD = 3
    ENEMIES = 4
