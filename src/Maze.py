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
from Color import *
from Agent import Agent


class Maze:
    def __init__(self, size, data=None, wall_coverage=None, filled_reward=False):
        self._sprite = {MazeObject.WALL: ("█", "█"), MazeObject.EMPTY: (" ", " "),
                        MazeObject.REWARD: (" ", "·"), MazeObject.AGENT: ("⬤", " ")}
        self._static_color = {MazeObject.WALL: Color.BLUE,
                              MazeObject.EMPTY: Color.WHITE,
                              MazeObject.REWARD: Color.WHITE}
        self._move = {Action.UP: (-1, 0), Action.DOWN: (1, 0), Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}
        self._size = size

        self._box = curses.newwin(self._size + 2, (self._size + 1) * 2, 4, 0)
        self._box.attrset(curses.color_pair(2))
        self._box.box()
        self._agents = []

        # Score box
        self._score_box = curses.newwin(self._size + 2, (self._size + 1) * 2, 0, 0)
        self._score = 0
        self._iteration = 0

        for line in range(4):
            self._score_box.addstr(line, 0, " " * (self._size + 1) * 2, self._static_color[MazeObject.REWARD])

        self._score_box.addstr(1, 0, " ITERATIONS", curses.A_BOLD | Color.WHITE)
        self._score_box.addstr(1, (self._size + 1) * 2 - 14, "🍒 HIGH SCORE", curses.A_BOLD | Color.WHITE)
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

        # Initialize object drawing
        for j in range(0, self._size):
            for i in range(0, self._size):
                obj = MazeObject(self._data[j][i])
                char = self._sprite[obj]

                self._box.addstr(j + 1, 2 * i + 1, char[0], self._static_color[obj])
                self._box.addstr(j + 1, 2 * i + 2, char[1], self._static_color[obj])

    def _update_score(self):
        self._score_box.addstr(2, (self._size + 1) * 2 - 1 - len(f'{self._score:08}'), f'{self._score:08}',
                               Color.WHITE)

    def _update_iteration(self):
        self._score_box.addstr(2, 0, " " + f'{self._iteration:06}', Color.WHITE)

    def add_agent(self, color, is_hostile):
        agent = None
        while True:
            x = np.random.randint(0, self._size)
            y = np.random.randint(0, self._size)

            if self._data[y][x] == MazeObject.WALL.value or self._data[y][x] == MazeObject.AGENT:
                continue

            agent = Agent(color, is_hostile, (y, x))
            break

        self._agents.append(agent)
        self._box.addstr(y + 1, 2 * x + 1, self._sprite[MazeObject.AGENT][0], color)
        self._box.addstr(y + 1, 2 * x + 2, self._sprite[MazeObject.AGENT][1], color)

        return len(self._agents) - 1

    def refresh(self):
        self._score_box.refresh()
        self._box.refresh()

    def get_agent_valid_move(self, index):
        moves = []

        agent = self._agents[index]
        if ((agent.get_y() - 1) >= 0 and
                not (self._data[agent.get_y() - 1][agent.get_x()] == MazeObject.WALL.value)):
            moves.append(Action.UP.value)
        if ((agent.get_y() + 1) < self._size and
                not (self._data[agent.get_y() + 1][agent.get_x()] == MazeObject.WALL.value)):
            moves.append(Action.DOWN.value)
        if ((agent.get_x() - 1) >= 0 and
                not (self._data[agent.get_y()][agent.get_x() - 1] == MazeObject.WALL.value)):
            moves.append(Action.LEFT.value)
        if ((agent.get_x() + 1) < self._size and
                not (self._data[agent.get_y()][agent.get_x() + 1] == MazeObject.WALL.value)):
            moves.append(Action.RIGHT.value)

        return moves

    def move_agent(self, index, direction=None):
        valid_moves = self.get_agent_valid_move(index)

        # Random if not given
        if direction is None:
            direction = Action(np.random.choice(valid_moves))
        elif direction.value not in valid_moves:
            return -1  # Failure

        # Set agent into an obj
        agent = self._agents[index]

        # Set old cell to empty/reward
        char = self._sprite[MazeObject(self._data[agent.get_y()][agent.get_x()])]
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, char[0], Color.WHITE)
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, char[1], Color.WHITE)

        # Set new cell to agent and change tracker
        agent.set_position(agent.get_y() + self._move[direction][0], agent.get_x() + self._move[direction][1])

        # Score
        if not agent.is_hostile() and self._data[agent.get_y()][agent.get_x()] == MazeObject.REWARD.value:
            self._score = self._score + 1
            self._update_score()

        # Data update
        if not agent.is_hostile():
            self._data[agent.get_y()][agent.get_x()] = MazeObject.EMPTY.value

        char = self._sprite[MazeObject.AGENT]
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, char[0], agent.get_color())
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, char[1], agent.get_color())

        return 0  # Success

