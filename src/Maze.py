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
    def __init__(self, size, data=None, wall_coverage=None, filled_reward=False):
        self._sprite = {MazeObject.WALL: ("█", "█"), MazeObject.AGENT: ("⬤", " "), MazeObject.EMPTY: (" ", " "),
                        MazeObject.ENEMIES: ("⬤", " "), MazeObject.REWARD: (" ", "·")}
        self._color = {MazeObject.WALL: curses.color_pair(2), MazeObject.AGENT: curses.color_pair(3),
                       MazeObject.EMPTY: curses.color_pair(1), MazeObject.ENEMIES: curses.color_pair(4),
                       MazeObject.REWARD: curses.color_pair(1)}
        self._move = {Action.UP: (-1, 0), Action.DOWN: (1, 0), Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}
        self._size = size

        self._box = curses.newwin(self._size + 2, (self._size + 1) * 2, 4, 0)
        self._box.attrset(curses.color_pair(2))
        self._box.box()
        self._agent = None

        # Score box
        self._score_box = curses.newwin(self._size + 2, (self._size + 1) * 2, 0, 0)
        self._score = 0
        self._iteration = 0

        for line in range(4):
            self._score_box.addstr(line, 0, " " * (self._size + 1) * 2, self._color[MazeObject.REWARD])

        self._score_box.addstr(1, 0, " ITERATIONS", curses.A_BOLD | self._color[MazeObject.REWARD])
        self._score_box.addstr(1, (self._size + 1) * 2 - 14, "🍒 HIGH SCORE", curses.A_BOLD | self._color[MazeObject.REWARD])
        self._update_score()
        self._update_iteration()

        # Initialize data
        self._data = data
        if self._data is None:
            if wall_coverage < 0 or wall_coverage >= 1:
                raise Exception("Coverage should be between 0.0 and 1.0")

            non_wall_obj = MazeObject.EMPTY.value
            if filled_reward:
                non_wall_obj = MazeObject.REWARD.value

            self._data = np.random.choice([MazeObject.WALL.value, non_wall_obj], size=(size, size),
                                          p=[wall_coverage, 1.0 - wall_coverage])

        # Initialize agent position
        while True:
            x = np.random.randint(0, self._size)
            y = np.random.randint(0, self._size)

            if self._data[y][x] == MazeObject.WALL.value:
                continue

            self._data[y][x] = MazeObject.AGENT.value
            self._agent = (y, x)
            break

        # Initialize object drawing
        for j in range(0, self._size):
            for i in range(0, self._size):
                obj = MazeObject(self._data[j][i])
                char = self._sprite[obj]

                self._box.addstr(j + 1, 2 * i + 1, char[0], self._color[obj])
                self._box.addstr(j + 1, 2 * i + 2, char[1], self._color[obj])

    def _update_score(self):
        self._score_box.addstr(2, (self._size + 1) * 2 - 1 - len(f'{self._score:08}'), f'{self._score:08}', self._color[MazeObject.REWARD])

    def _update_iteration(self):
        self._score_box.addstr(2, 0, " " + f'{self._iteration:06}', self._color[MazeObject.REWARD])

    def refresh(self):
        self._score_box.refresh()
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

        # Score
        if self._data[self._agent[0]][self._agent[1]] == MazeObject.REWARD.value:
            self._score = self._score + 1
            self._update_score()

        # Data update
        self._data[self._agent[0]][self._agent[1]] = MazeObject.AGENT.value
        char = self._sprite[MazeObject.AGENT]
        self._box.addstr(self._agent[0] + 1, 2 * self._agent[1] + 1, char[0], self._color[MazeObject.AGENT])
        self._box.addstr(self._agent[0] + 1, 2 * self._agent[1] + 2, char[1], self._color[MazeObject.AGENT])

        return 0  # Success

