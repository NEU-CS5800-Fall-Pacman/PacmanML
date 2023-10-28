##################################################
## Core file for Pacman machine learning project
##################################################
## Author: Khoa Nguyen
## Copyright: Copyright 2023
## License: GPL
##################################################

import curses
from time import sleep
import numpy as np

from Maze import Maze
from MazeObject import MazeObject

# Global configuration
maze_size = 40
frame_per_second = 2

maze = np.random.choice([MazeObject.EMPTY.value, MazeObject.WALL.value], size=(maze_size, maze_size), p=[0.8, 0.2])


def main(screen):
    # Setting color
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)

    # Term options
    screen.clear()
    curses.noecho()  # Do not echo keys back to the client
    curses.cbreak()  # Do not wait for Enter key to be pressed.
    curses.curs_set(False)  # Turn off blinking cursor
    screen.nodelay(True)  # Turn off keystroke waiting
    curses.use_default_colors()  # Use terminal color

    m = Maze(maze_size, maze)

    # Main UI loop
    while True:
        # Move agent
        m.move_agent(direction=None)

        # Re-draw
        screen.refresh()
        m.refresh()
        screen.getch()

        # Wait for next frame
        sleep(1 / frame_per_second)


curses.wrapper(main)
