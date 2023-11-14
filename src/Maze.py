##################################################
## Contains all the maze information and valid
## operations to perform
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import numpy as np

from MazeObject import MazeObject
from Action import Action
from Color import *
from Agent import Agent
from Astar import *


class Maze:
    def __init__(self, size, data=None, wall_coverage=None, filled_reward=False):
        self._sprite = {MazeObject.WALL: ("█", "█"), MazeObject.EMPTY: (" ", " "),
                        MazeObject.REWARD: ("・", ""), MazeObject.AGENT: ("A", "")}
        self._static_color = {MazeObject.WALL: Color.BLUE,
                              MazeObject.EMPTY: Color.WHITE,
                              MazeObject.REWARD: Color.WHITE}
        self._move = {Action.STAY: (0, 0), Action.UP: (-1, 0), Action.DOWN: (1, 0),
                      Action.LEFT: (0, -1), Action.RIGHT: (0, 1)}
        self._size = size  # Maze size
        self._wall_coverage = wall_coverage  # Percentage of the maze wall should be covered
        self._filled_reward = filled_reward  # If reward should be filled within non-wall space

        # Main game box
        self._box = curses.newwin(self._size + 2, (self._size + 1) * 2, 4, 0)
        self._box.attrset(Color.BLUE)
        self._box.box()

        # Agent properties
        self._agents = []  # List of agents
        self._red_zone = []  # Coordinates of hostile agents
        self._green_zone = []  # Coordinates of non-hostile agents

        # Score box
        self._score_box = curses.newwin(self._size + 2, (self._size + 1) * 2, 0, 0)
        self._score = 0
        self._iteration = 0

        # Render score box
        for line in range(4):
            self._score_box.addstr(line, 0, " " * (self._size + 1) * 2, self._static_color[MazeObject.REWARD])

        self._score_box.addstr(1, 0, " ITERATIONS", curses.A_BOLD | Color.WHITE)
        self._score_box.addstr(1, (self._size + 1) * 2 - 14, "🍒 HIGH SCORE", curses.A_BOLD | Color.WHITE)
        self._update_score()
        self._update_iteration()

        # Initialize maze data
        self._data = data
        self._initial_data = np.copy(data)
        self._initial_agents_pos = []

        self._init_draw()

    def _init_draw(self):
        if self._data is None:
            if self._wall_coverage < 0 or self._wall_coverage >= 1:
                raise Exception("Coverage should be between 0.0 and 1.0")

            non_wall_obj = MazeObject.EMPTY.value
            if self._filled_reward:
                non_wall_obj = MazeObject.REWARD.value

            self._data = np.random.choice([MazeObject.WALL.value, non_wall_obj], size=(self._size, self._size),
                                          p=[self._wall_coverage, 1.0 - self._wall_coverage])
            self._initial_data = np.copy(self._data)

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

    def add_reward(self, y=None, x=None):
        """
        Add reward to the maze. If x and y not given, spawn random on a valid spot

        :param y: y coordinate of the reward (Optional)
        :param x: x coordinate of the reward (Optional)
        :return: tuple of (y, x)
        """

        if x is None or y is None:
            while True:  # Random x and y
                rand_x = np.random.randint(0, self._size)
                rand_y = np.random.randint(0, self._size)

                if (self._data[rand_y][rand_x] == MazeObject.WALL.value or
                        (rand_y, rand_x) in self._red_zone or (rand_y, rand_x) in self._green_zone):
                    continue

                x = rand_x
                y = rand_y
                break
        elif self._data[y][x] == MazeObject.WALL.value or (y, x) in self._red_zone or (y, x) in self._green_zone:
            return -1  # Not a valid spawn point

        # Store and render
        self._data[y][x] = MazeObject.REWARD.value
        self._box.addstr(y + 1, 2 * x + 1, self._sprite[MazeObject.REWARD][0], Color.WHITE)
        self._box.addstr(y + 1, 2 * x + 2, self._sprite[MazeObject.REWARD][1], Color.WHITE)

        return tuple([y, x])

    def add_agent(self, color, is_hostile):
        """
        Add new agent into the maze, given color of the agent, and if agent is hostile

        :param color: color of the agent, use Color class
        :param is_hostile: whether the agent consumes reward and catch non-hostile agents
        :return: index of newly added agent
        """

        agent = None
        while True:
            x = np.random.randint(0, self._size)
            y = np.random.randint(0, self._size)

            if self._data[y][x] == MazeObject.WALL.value or (y, x) in self._red_zone or (y, x) in self._green_zone:
                continue
            else:
                agent = Agent(color, is_hostile, (y, x))
                break

        self._agents.append(agent)
        self._initial_agents_pos.append(agent.get_position())

        if is_hostile:
            self._red_zone.append(agent.get_position())
            self._green_zone.append(0)
        else:
            self._green_zone.append(agent.get_position())
            self._red_zone.append(0)

        self._box.addstr(y + 1, 2 * x + 1, self._sprite[MazeObject.AGENT][0], color)
        self._box.addstr(y + 1, 2 * x + 2, self._sprite[MazeObject.AGENT][1], color)

        return len(self._agents) - 1

    def refresh(self):
        """
        Refresh entire box, only call after each frame is drawn
        """

        self._score_box.refresh()
        self._box.refresh()

    def get_agent_valid_move(self, index):
        """
        Return list of valid moves, given agent index

        :param index: index of the agent
        :return: list of valid Actions
        """

        moves = []

        agent = self._agents[index]
        if ((agent.get_y() - 1) >= 0 and
                not (self._data[agent.get_y() - 1][agent.get_x()] == MazeObject.WALL.value)):
            moves.append(Action.UP)
        if ((agent.get_y() + 1) < self._size and
                not (self._data[agent.get_y() + 1][agent.get_x()] == MazeObject.WALL.value)):
            moves.append(Action.DOWN)
        if ((agent.get_x() - 1) >= 0 and
                not (self._data[agent.get_y()][agent.get_x() - 1] == MazeObject.WALL.value)):
            moves.append(Action.LEFT)
        if ((agent.get_x() + 1) < self._size and
                not (self._data[agent.get_y()][agent.get_x() + 1] == MazeObject.WALL.value)):
            moves.append(Action.RIGHT)

        return moves

    def reset(self):
        """
        Reset the maze to its original generation
        """

        # Update scoreboard
        self._iteration = self._iteration + 1
        self._update_iteration()
        self._score = 0
        self._update_score()

        # Re-draw initial state
        self._data = np.copy(self._initial_data)
        self._init_draw()

        # Re-init agents
        temp_agents = np.copy(self._agents)
        for index in range(len(temp_agents)):
            y = self._initial_agents_pos[index][0]
            x = self._initial_agents_pos[index][1]
            temp_agents[index].set_position(y, x)
        self._agents = []
        #self._red_zone = []
        #self._green_zone = []
        self._agents = temp_agents
        # for ag in temp_agents:
        #     self.add_agent(ag.get_color(), ag.is_hostile())

    def get_agent_pos(self):
        for agent in self._agents:
            if not agent.is_hostile():
                return agent.get_position()

    def get_enemy_direction(self, enemy_pos, agent_pos):
        a_star = AStar(self._size, enemy_pos, agent_pos)
        path = a_star.find_path(self)
        direction = Action.STAY
        if path and len(path) > 1:
            next_cell = path[1]
            # Determine the direction to move
            delta_y = next_cell[0] - enemy_pos[0]
            delta_x = next_cell[1] - enemy_pos[1]

            if delta_x == 0 and delta_y == -1:
                direction = Action.UP
            elif delta_x == 0 and delta_y == 1:
                direction = Action.DOWN
            elif delta_x == -1 and delta_y == 0:
                direction = Action.LEFT
            elif delta_x == 1 and delta_y == 0:
                direction = Action.RIGHT

        return direction

    def move_agent(self, index, direction=None):
        """
        Move agent within the maze, given agent index and direction. If direction isn't given,
        agent will randomly choose from the list of valid Actions

        :param index: index of the agent
        :param direction: Actions enum to let the system know where to move the agent (Optional)
        :return: 0 for success, otherwise -1
        """

        valid_moves = self.get_agent_valid_move(index)

        # Random if not given
        if direction is None:
            direction = Action(np.random.choice(valid_moves))
        elif direction.value not in valid_moves:
            return -1  # Failure

        # Set agent into an obj
        agent = self._agents[index]
        prev_agent_position = agent.get_position()

        # if the agent is an enemy
        if agent.is_hostile():
            direction = self.get_enemy_direction(agent.get_position(), self.get_agent_pos())

        # Set old cell to empty/reward
        char = self._sprite[MazeObject(self._data[agent.get_y()][agent.get_x()])]
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, char[0], Color.WHITE)
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, char[1], Color.WHITE)

        # Set new cell to agent and change tracker
        agent.set_position(agent.get_y() + self._move[direction][0], agent.get_x() + self._move[direction][1])

        # Data update
        if not agent.is_hostile():
            if self._data[agent.get_y()][agent.get_x()] == MazeObject.REWARD.value:
                self._score = self._score + 1
                self._update_score()
            elif agent.get_position() in self._red_zone:
                self.reset()
                return

            self._data[agent.get_y()][agent.get_x()] = MazeObject.EMPTY.value
            self._green_zone[index] = agent.get_position()
        else:
            if agent.get_position() in self._green_zone:
                self.reset()
                return

            self._red_zone[index] = agent.get_position()

        char = self._sprite[MazeObject.AGENT]
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 1, char[0], agent.get_color())
        self._box.addstr(agent.get_y() + 1, 2 * agent.get_x() + 2, char[1], agent.get_color())

        return 0  # Success
