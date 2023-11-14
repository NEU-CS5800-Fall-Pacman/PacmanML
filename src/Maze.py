##################################################
## Contains all the maze information and valid
## operations to perform
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

from collections import deque
import numpy as np

from MazeObject import MazeObject
from Action import Action
from Color import *
from Agent import Agent


class Maze:
    def __init__(self, size, data=None, wall_coverage=None, filled_reward=False):
        self._sprite = {MazeObject.WALL: ("█", "█"), MazeObject.EMPTY: (" ", " "),
                        MazeObject.REWARD: (".", ""), MazeObject.AGENT: ("A", "")}
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

        self._init_draw()
        
    def bfs_to_nearest_reward(self, start):
            queue = deque([start])
            visited = {start}
            parent = {start: None}
            while queue:
                current = queue.popleft()
                if self._data[current[0]][current[1]] == MazeObject.REWARD.value:
                    path = []
                    while current:
                        path.append(current)
                        current = parent[current]
                    return path[::-1]  # Reverse the path to start from the agent's position
                for direction in Action:
                    if direction == Action.STAY:
                        continue
                    dy, dx = self._move[direction]
                    next_y, next_x = current[0] + dy, current[1] + dx
                    if (0 <= next_y < self._size and 0 <= next_x < self._size and
                            self._data[next_y][next_x] != MazeObject.WALL.value and
                            (next_y, next_x) not in visited):
                        visited.add((next_y, next_x))
                        parent[(next_y, next_x)] = current
                        queue.append((next_y, next_x))
            return None  # No reward found

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

            agent = Agent(color, is_hostile, (y, x))
            break

        self._agents.append(agent)

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

        moves = [Action.STAY.value]

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
        self._agents = []
        self._red_zone = []
        self._green_zone = []

        for ag in temp_agents:
            self.add_agent(ag.get_color(), ag.is_hostile())

    

    def move_agent(self, agent_index):
        agent = self._agents[agent_index]
        start_position = agent.get_position()
        path_to_reward = self.bfs_to_nearest_reward(start_position)
        
        if path_to_reward and len(path_to_reward) > 1:  # If a path exists and is not just the current position
            # The next step towards the reward
            next_position = path_to_reward[1]
            
            # Get the old position of the agent to clear it
            old_y, old_x = start_position
            
            # Clear the old position of the agent on the display
            self._box.addstr(old_y + 1, 2 * old_x + 1, self._sprite[MazeObject.EMPTY][0], self._static_color[MazeObject.EMPTY])
            
            # Set the new position of the agent
            self._agents[agent_index].set_position(*next_position)
            
            # Draw the agent at the new position on the display
            new_y, new_x = next_position
            self._box.addstr(new_y + 1, 2 * new_x + 1, self._sprite[MazeObject.AGENT][0], agent.get_color())

            # Update the maze data if necessary, such as removing a reward if collected
            if self._data[new_y][new_x] == MazeObject.REWARD.value:
                self._score += 1  # Assuming we increase score when collecting a reward
                # Remove the reward from the data
                self._data[new_y][new_x] = MazeObject.EMPTY.value



 
