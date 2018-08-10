""" Mostly based on script from  https://en.wikipedia.org/wiki/Maze_generation_algorithm"""

import numpy as np
import matplotlib.pyplot as pyplot
from random import randint, randrange


class Maze:
    """ Maze' Labirynth object
    built with array with elements 0-path, 1-wall, 2-exit

    standard beginning: maze_obj.fill_borders -> maze_obj.make_aisles
    """
    def __init__(self, width , height, complexity=0.75, density=0.75):
        # Only odd shapes
        self.shape = ((height // 2) * 2 + 1, (width // 2) * 2 + 1)
        # Adjust complexity and density relative to maze size
        self.complexity = int(complexity * (5 * (self.shape[0] + self.shape[1])))  # number of components
        self.density = int(density * ((self.shape[0] // 2) * (self.shape[1] // 2)))  # size of components
        # Build actual maze
        self.exit = []
        self.grid = np.zeros(self.shape)

    def __str__(self):
        str_array = np.array(self.grid.flatten())
        str_array.resize(self.shape)
        return str(str_array)

    def copy(self):
        other = Maze(self.shape[1], self.shape[0], self.complexity, self.density)
        other.grid = np.copy(self.grid)
        other.exit = self.exit[:]
        return other

    def fill_borders(self, value=1):
        self.grid[0, :] = self.grid[-1, :] = value
        self.grid[:, 0] = self.grid[:, -1] = value
        # print(np.argwhere(self.grid == 1))

    def make_aisles(self):
        for i in range(self.density):
            x, y = randrange(0, self.shape[1]+1, 2), randrange(0, self.shape[0]+1, 2) # pick a random position
            self.grid[y, x] = 1
            for j in range(self.complexity):
                neighbours = []
                if x > 1:             neighbours.append((y, x - 2))
                if x < self.shape[1] - 2:  neighbours.append((y, x + 2))
                if y > 1:             neighbours.append((y - 2, x))
                if y < self.shape[0] - 2:  neighbours.append((y + 2, x))
                if len(neighbours) > 0:
                    y_, x_ = neighbours[randint(0, len(neighbours)-1)]
                    if self.grid[y_, x_] == 0:
                        self.grid[y_, x_] = 1
                        self.grid[y_ + (y - y_) // 2, x_ + (x - x_) // 2] = 1
                        x, y = x_, y_

    def set_exit(self):
        x = y = 0
        # side of the entrance; 0-top 1-bottom 2-left 3-right
        side = randint(0, 3)
        if side < 2:
            x = randint(1, self.shape[1]-2)
            if side == 1:
                y = self.shape[0] - 1
        if side > 1:
            y = randint(1, self.shape[0]-2)
            if side == 3:
                x = self.shape[1] - 1
        self.exit = [y, x]
        self.grid[y, x] = 2

    def add_obj(self, number_repr, coor_y, coor_x):
        self.grid[coor_y, coor_x] = number_repr


if __name__ == '__main__':
    np.set_printoptions(threshold=np.nan)

    m = Maze(15,20)
    m.fill_borders()
    m.make_aisles()
    m.set_exit()
    print(m.exit)
    print(m)

    pyplot.figure(figsize=(4, 4))
    pyplot.imshow(m.grid, cmap=pyplot.cm.binary, interpolation='nearest')
    pyplot.xticks([]), pyplot.yticks([])
    pyplot.show()

