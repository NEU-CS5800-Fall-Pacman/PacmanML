##################################################
## Core file for Pacman machine learning project
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import curses
from time import sleep
from Color import *
import numpy as np

from Maze import Maze
from MazeObject import MazeObject

# Global configuration
maze_size = 18
frame_per_second = 30


def main(screen):
    curses.start_color()
    Color.initialize()

    # Term options
    screen.clear()
    curses.noecho()  # Do not echo keys back to the client
    curses.cbreak()  # Do not wait for Enter key to be pressed.
    curses.curs_set(False)  # Turn off blinking cursor
    screen.nodelay(True)  # Turn off keystroke waiting
    curses.use_default_colors()  # Use terminal color

    # Maze setup
    maze = Maze(maze_size, wall_coverage=0.2, filled_reward=False)
    
    for _ in range(10):
        maze.add_reward()
    maze.add_agent(Color.YELLOW, True)
    maze.add_agent(Color.RED, True)
    maze.add_agent(Color.GREEN, True)
    maze.add_agent(Color.CYAN, True)
    maze.add_agent(Color.MAGENTA, True)

    # Main UI loop
    while True:
        # Move agent
        maze.move_agent(0)
        maze.move_agent(1)
        # maze.move_agent(2)
        # maze.move_agent(3)
        # maze.move_agent(4)

        # Re-draw
        screen.refresh()
        maze.refresh()
        screen.getch()

        # Wait for next frame
        sleep(1 / frame_per_second)


curses.wrapper(main)
