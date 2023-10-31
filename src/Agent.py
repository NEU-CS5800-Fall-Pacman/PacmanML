##################################################
## Agent object
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

class Agent:
    def __init__(self, color, is_hostile, position):
        self._color = color
        self._is_hostile = is_hostile
        self._position = position

    def is_hostile(self):
        return self._is_hostile

    def get_color(self):
        return self._color

    def get_y(self):
        return self._position[0]

    def get_x(self):
        return self._position[1]

    def get_position(self):
        return self._position

    def set_position(self, y, x):
        self._position = (y, x)
