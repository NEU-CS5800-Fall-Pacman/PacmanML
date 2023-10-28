##################################################
## Contains all the maze information and valid
## operations to perform
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import curses
import numpy as np

from MazeObject import MazeObject
from Action import Action


class Maze:
    def __init__(self, size, data):
        self._sprite = {MazeObject.WALL: ("█", "█"), MazeObject.AGENT: ("⬤", " "), MazeObject.EMPTY: (" ", " "),
                        MazeObject.ENEMIES: ("⬤", " "), MazeObject.REWARD: (" ", "·")}
        self._color = {MazeObject.WALL: curses.color_pair(2), MazeObject.AGENT: curses.color_pair(3),
                       MazeObject.EMPTY: curses.color_pair(1), MazeObject.ENEMIES: curses.color_pair(4),
                       MazeObject.REWARD: curses.color_pair(1)}
        self._move = {Action.UP: (-1, 0), Action.DOWN: (1, 0), Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}
        self._size = size

        self._box = curses.newwin(self._size + 2, (self._size + 1) * 2, 0, 0)
        self._box.attrset(curses.color_pair(2))
        self._box.box()
        self._data = data
        self._agent = None

        # Initialize agent position
        while True:
            x = np.random.randint(0, self._size)
            y = np.random.randint(0, self._size)

            if data[y][x] == MazeObject.WALL.value:
                continue

            data[y][x] = MazeObject.AGENT.value
            self._agent = (y, x)
            break

        # Initialize object drawing
        for j in range(0, self._size):
            for i in range(0, self._size):
                obj = MazeObject(self._data[j][i])
                char = self._sprite[obj]

                self._box.addstr(j + 1, 2 * i + 1, char[0], self._color[obj])
                self._box.addstr(j + 1, 2 * i + 2, char[1], self._color[obj])

    def refresh(self):
        self._box.refresh()

    def get_agent_valid_move(self):
        moves = []
        if ((self._agent[0] - 1) >= 0 and
                not (self._data[self._agent[0] - 1][self._agent[1]] == MazeObject.WALL.value)):
            moves.append(Action.UP.value)
        if ((self._agent[0] + 1) < self._size and
                not (self._data[self._agent[0] + 1][self._agent[1]] == MazeObject.WALL.value)):
            moves.append(Action.DOWN.value)
        if ((self._agent[1] - 1) >= 0 and
                not (self._data[self._agent[0]][self._agent[1] - 1] == MazeObject.WALL.value)):
            moves.append(Action.LEFT.value)
        if ((self._agent[1] + 1) < self._size and
                not (self._data[self._agent[0]][self._agent[1] + 1] == MazeObject.WALL.value)):
            moves.append(Action.RIGHT.value)

        return moves

    def move_agent(self, direction=None):
        valid_moves = self.get_agent_valid_move()

        # Random if not given
        if direction is None:
            direction = Action(np.random.choice(valid_moves))
        elif direction.value not in valid_moves:
            return -1  # Failure

        # Set old cell to empty
        self._data[self._agent[0]][self._agent[1]] = MazeObject.EMPTY.value
        char = self._sprite[MazeObject.EMPTY]
        self._box.addstr(self._agent[0] + 1, 2 * self._agent[1] + 1, char[0], self._color[MazeObject.EMPTY])
        self._box.addstr(self._agent[0] + 1, 2 * self._agent[1] + 2, char[1], self._color[MazeObject.EMPTY])

        # Set new cell to agent and change tracker
        self._agent = (self._agent[0] + self._move[direction][0], self._agent[1] + self._move[direction][1])
        self._data[self._agent[0]][self._agent[1]] = MazeObject.AGENT.value
        char = self._sprite[MazeObject.AGENT]
        self._box.addstr(self._agent[0] + 1, 2 * self._agent[1] + 1, char[0], self._color[MazeObject.AGENT])
        self._box.addstr(self._agent[0] + 1, 2 * self._agent[1] + 2, char[1], self._color[MazeObject.AGENT])

        return 0  # Success

