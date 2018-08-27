# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 12:20:17 2018

@author: Kukiss7
exc: https://www.reddit.com/r/dailyprogrammer/comments/4vrb8n/weekly_25_escape_the_trolls/
implemented: working game in tkinker environment, trolls find their paths to hero, Text_Map gives information on the screen, random maps

"""
import string
import random
import tkinter as tk
import numpy as np
from Maze import Maze


class Game:
    """ Game representation
        New turn with every player move

    Attributes:
        map: Maze object which is based on np.array
        hero: Hero object; player
        hero_map: Maze object; copy of a game map with hero and trolls marked
        trolls: list of Troll objects
        top_layer_on: boolean; Tell if there is a message on the screen
        top_layer_map: Text_map object; it is for writing a message in the middle of the screen
        turn: int; actual turn
        winning_turn: int; turn upon winning
        status: 0,1,2,3  - pre_start, in_progress, win, lost
        tkinter variables:
        root
        view
        label
    """

    directions = {'up': 3, 'down': 4, 'left': 5, 'right': 6}
    grid_elements = {i: j for i, j in enumerate([' ', '#', 'X', '^', 'v', '<', '>', 't'])}

    def __init__(self, map_width, map_height, restarted=False):
        self.map = Maze(map_width, map_height)
        self.map.fill_borders()
        self.map.make_aisles()
        self.map.set_exit()
        self.hero_map = self.map.copy()
        self.hero = Hero()
        self.hero.appear(self)
        self.hero_map.add_obj(3, self.hero.coor[0], self.hero.coor[1])
        self.trolls = []
        self.top_layer_on = False
        self.top_layer_map = Text_map()
        self.turn = 0
        self.winning_turn = -1
        self.status = 0
        self.spawn_trolls(15)
        self.refresh_hero_map()
        if not restarted:
            self.root = tk.Tk()
            self.view = tk.StringVar()
            self.label = tk.Label(self.root,
                             font=("Lucida Console", 14),
                             textvariable=self.view)  # takefocus=1 may be useful

    def __str__(self):
        """
            Main "graphics" engine as the game is built without real graphics - just text
            Interprets nparrays from Maze objects (base labirynth is made with integers 0,1,2), 
            Text_Map and final array are made of string signs 
        """
        def decode(str_number):
            # function to map arrays
            try:
                return Game.grid_elements[int(float(str_number))]
            except KeyError:
                return str(str_number)[0] # if not found in Game.grid_elements
            except ValueError:
                return str_number  # top layer signs ' ' etc
        res = ''
        res_array = np.empty(self.map.shape, dtype='<U11')
        res_array[:, :] = self.hero_map.grid
        # Checking if needed and calculating top_layer with message for player
        if self.top_layer_on:
            top_layer_x_start = (self.map.shape[1] - self.top_layer_map.shape[1]) // 2
            top_layer_y_start = (self.map.shape[0] - self.top_layer_map.shape[0]) // 2
            res_array[top_layer_y_start : top_layer_y_start + self.top_layer_map.shape[0],
                      top_layer_x_start: top_layer_x_start + self.top_layer_map.shape[1]] = self.top_layer_map.grid
        # 'printing' results 
        for i in range(self.map.shape[0]):
            str_array_line = np.array(list(map(decode, res_array[i, :])))
            res += ''.join(str_array_line)
            res += '\n'
        return res

    def play(self):
        """ Main game function. Captures key presses, launches tk.root.mainloop() to start the app
        """
        self.status = 1
        a = str(self)
        self.view.set(a)

        self.root.bind('<Up>', self.hero_up)
        self.root.bind('<Down>', self.hero_down)
        self.root.bind('<Left>', self.hero_left)
        self.root.bind('<Right>', self.hero_right)
        self.root.bind('<r>', self.restart)
        self.label.pack()
        self.root.mainloop()

    def hero_up(self, key_pressed):
        self.hero_action('up')
        self.new_turn()

    def hero_down(self, key_pressed):
        self.hero_action('down')
        self.new_turn()

    def hero_left(self, key_pressed):
        self.hero_action('left')
        self.new_turn()

    def hero_right(self, key_pressed):
        self.hero_action('right')
        self.new_turn()

    def restart(self, key_pressed):
        """ Restarts the game
        """
        if self.status > 1:
            shape = self.map.shape
            self.__init__(self.map.shape[1], self.map.shape[0], restarted=True)
            self.play()

    def new_turn(self):
        """ Controls every new turn
            calculates trolls moves, refreshes map, checks if game is lost
            Sets new viewport
        """
        self.trolls_action()
        self.refresh_hero_map()
        self.turn += 1
        if self.is_lost():
            self.lose()
        self.view.set(str(self))

    def hero_action(self, direction):
        """ Controls hero move after given key press
            Checks if hero should turn himself or go in given direction if he's already turned there
            Win/Lose is also checked at the end
        """
        if self.status == 3:
            pass
        elif not self.hero.turn(direction):
            if self.check_space(self.hero.coor, direction) == 0:
                if self.hero.move(direction):
                    return True
            elif self.check_space(self.hero.coor, direction) == 1:
                if self.check_wall(direction) == 0:
                    self.push_wall(direction)
                    self.hero.move(direction)
            elif self.check_space(self.hero.coor, direction) == 2:
                self.win()
            elif self.check_space(self.hero.coor, direction) == 7:  # 7 means trolls
                self.lose()

    def spawn_trolls(self, n):
        """ Iterates through self.trolls list and spawns them.
            n: number of trolls
        """
        for i in range(n):
            self.trolls.append(Troll(self))
            self.trolls[i].appear(self)

    def trolls_action(self):
        """ Iterates through self.trolls list and controlls them.
            Every troll finds his path to hero and moves towards him.
        """
        for troll in self.trolls:
            troll.copy_game_map()
            troll.find_path()
            direction = troll.path[1]['direction']
            if not troll.turn(direction):
                troll.move(direction)

    def clear_trolls(self):
        """ Deletes all trolls from the game.
        """
        self.trolls.clear()

    def check_space(self, coor, direction, length=1):
        """ Checks space in given direction from the given coordinates

        length: int; tells how far we are checking
        returns value of a grid: int: 0-7"""
        assert direction in list(Game.directions.keys())
        try:
            if direction == 'up':
                return self.hero_map.grid[coor[0]-length, coor[1]]
            elif direction == 'down':
                return self.hero_map.grid[(coor[0]+length, coor[1])]
            elif direction == 'left':
                return self.hero_map.grid[(coor[0], coor[1]-length)]
            elif direction == 'right':
                return self.hero_map.grid[(coor[0], coor[1]+length)]
        except KeyError: # looking outside the map
            return 1

    def check_wall(self, direction):
        """ Checks a space in given direction from the hero
            returns value of a grid: int: 0-7
        """
        return self.check_space(self.hero.coor, direction, 2)

    def push_wall(self, direction):
        """ Moves a wall near hero in given direction
        """
        if direction == 'up':
            self.map.grid[self.hero.coor[0]-1, self.hero.coor[1]] = 0
            self.map.grid[self.hero.coor[0]-2, self.hero.coor[1]] = 1
        elif direction == 'down':
            self.map.grid[self.hero.coor[0]+1, self.hero.coor[1]] = 0
            self.map.grid[self.hero.coor[0]+2, self.hero.coor[1]] = 1
        elif direction == 'left':
            self.map.grid[self.hero.coor[0], self.hero.coor[1] - 1] = 0
            self.map.grid[self.hero.coor[0], self.hero.coor[1] - 2] = 1
        elif direction == 'right':
            self.map.grid[self.hero.coor[0], self.hero.coor[1] + 1] = 0
            self.map.grid[self.hero.coor[0], self.hero.coor[1] + 2] = 1

    def refresh_hero_map(self):
        self.hero_map = self.map.copy()
        if self.status != 3:
            self.hero_map.grid[self.hero.coor] = Game.directions[self.hero.direction]
        for troll in self.trolls:
            self.hero_map.grid[troll.coor] = 7

    def win(self):
        """ After winning procedures:
            set Game.status, give a message to the player, set winning turn, clear trolls
        """
        self.top_layer_on = True
        self.status = 2
        # self.top_layer_map.clear_all()
        if self.turn - self.winning_turn == 1:
            self.change_top_layer(text="Seriously...You've already won\nR for restart")
        else:
            self.winning_turn = self.turn
            self.change_top_layer(text='You won!!!\nR for restart')
        self.clear_trolls()

    def is_lost(self):
        """ Check if game is lost: does any trolls's coordinates equals to hero coors
        """
        for troll in self.trolls:
            if troll.coor == self.hero.coor:
                return True
        return False

    def lose(self):
        """ After losing procedures:
            set Game.status, give a message to player
        """
        self.top_layer_on = True
        self.status = 3
        self.change_top_layer(text="You've been eaten\nR for restart")

    def change_top_layer(self, text=None):
        """ Changes a message to player
        """
        self.top_layer_map = Text_map(text=text)
        if text:
            self.top_layer_map.make_frame()
            self.top_layer_map.add_text()

    @staticmethod
    def new_coor(coor, direction, length=1):
        """Returns new coordinates based on given by
        coor and shifted by direction and length

        length: int; tells how far we are checking
        returns coor; (letter, number)"""
        assert direction in list(Game.directions.keys())
        if direction == 'up':
            return (coor[0]-length, coor[1])
        elif direction == 'down':
            return (coor[0]+length, coor[1])
        elif direction == 'left':
            return (coor[0], coor[1] - length)
        elif direction == 'right':
            return (coor[0], coor[1] + length)

    @staticmethod
    def coors_dist(coor1, coor2):
        y_dist = abs(coor1[0] - coor2[0])
        x_dist = abs(coor1[1] - coor2[1])
        return y_dist + x_dist

    @staticmethod
    def objects_dist(object1, object2):
        y_dist = abs(object1.coor[0] - object2.coor[0])
        x_dist = abs(object1.coor[1] - object2.coor[1])
        return y_dist + x_dist


class Text_map():
    """Representation for text labels on screen
    https://stackoverflow.com/questions/40690248/copy-numpy-array-into-part-of-another-array
    """
    def __init__(self, text=None):
        if text is not None:
            self.text = text
            self.shape = (text.count('\n')+5), \
                         (max([len(line) for line in text.split('\n')])+4)
            self.grid = np.empty(self.shape, dtype='<U11')

    def make_frame(self):
        self.grid[0, :] = self.grid[-1, :] = '#'
        self.grid[:, 0] = self.grid[:, -1] = '#'
        self.grid[1, 1:self.shape[1]-1] = self.grid[-2, 1:self.shape[1]-1] = ' '
        self.grid[1:self.shape[0]-1, 1] = self.grid[1:self.shape[0]-1, -2] = ' '

    def add_text(self):
        text_lines = self.text.split('\n')
        for i in range(len(text_lines)):
            text_lines[i] = text_lines[i].center(self.shape[1]-4, ' ')
            for j in range(len(text_lines[i])):
                self.grid[i+2, j+2] = text_lines[i][j]

    def clear_all(self):
        """Clears the Text_map"""
        self.text = 0
        self.grid = np.empty(0,0)


class Hero:
    """ Player's hero representation

    coor: coordinates; tuple(y,x)
    direction: one of  '^'/'v'/'<'/'>'
    """

    def __init__(self):
        self.coor = tuple()
        self.direction = random.choice(list(Game.directions.keys()))

    def appear(self, game):
        """Hero appears on map

        map: game_map object"""
        self.coor = random.randrange(1, game.map.shape[0]-1), random.randrange(1, game.map.shape[1]-1)
        n = 0
        while game.map.grid[self.coor] != 0:
            self.coor = random.randrange(1, game.map.shape[0] - 1), random.randrange(1, game.map.shape[1] - 1)
            n += 1
            assert n < 99, 'Tried to appear a hero %d times; last try coor: %s; game.map.grid[coor]: %s' % (
                n, self.coor, game.map.grid[self.coor[0], self.coor[1]])

    def turn(self, turn_direction):
        if self.direction == turn_direction:
            return False
        else:
            self.direction = turn_direction
            return True

    def move(self, move_direction):
        """
        move_direction can be: up, down, left, right
        """
        self.coor = Game.new_coor(self.coor, move_direction)


class Troll(Hero):
    def __init__(self, game):
        """
            Troll (enemy) representation

            path: list; list of needed moves to reach the hero (player); max 300 moves
            map = copy of game map; every troll has its own copy only for debugging purposes 
        """
        super().__init__()
        self.path = []
        self.game = game
        self.map = game.hero_map.copy()

    def copy_game_map(self):
        self.map = self.game.hero_map.copy()

    def find_path(self):
        """
            Based on A* search algorithm
            coor: tuple; self coordinates (unchangeable)
            g_cost: int; is the movement cost from the start point to the current square
            h_cost: int; is the estimated movement cost from the current square to the destination point
            sum_cost = g_cost + h_cost
            parent: grid element the leads to given element
        """
        self.path = []
        open_list = []
        close_list = [{'coor': self.coor, 'direction': None,
                       'g_cost': 0,
                       'h_cost': Game.objects_dist(self, self.game.hero),
                       'sum_cost': Game.objects_dist(self, self.game.hero),
                       'parent': None}]
        finished = False
        for n in range(300):
            for direction in Game.directions:
                new_coor = Game.new_coor(close_list[-1]['coor'], direction)
                if self.game.map.grid[new_coor[0], new_coor[1]] == 0 or new_coor == self.game.hero.coor:
                    if new_coor == self.game.hero.coor:
                        finished = True
                    checked = False
                    for element in close_list:
                        if element['coor'] == new_coor: checked = True
                    if checked:
                        continue
                    #changing direction costs two moves (g_cost)
                    if close_list[-1]['direction'] == direction:
                        g_cost = close_list[-1]['g_cost'] + 1
                    else:
                        g_cost = close_list[-1]['g_cost'] + 2
                    h_cost = Game.coors_dist(self.game.hero.coor, new_coor)
                    sum_cost = g_cost + h_cost
                    parent = close_list[-1]['coor']
                    open_list.append({'coor': new_coor,
                                      'direction': direction,
                                      'g_cost': g_cost,
                                      'h_cost': h_cost,
                                      'sum_cost': sum_cost,
                                      'parent': parent})
            try:
                lowest_sum_cost = min([element['sum_cost'] for element in open_list])
            except ValueError:
                pass # troll is trapped
            for i in range(len(open_list) - 1, -1, -1):
                if open_list[i]['sum_cost'] == lowest_sum_cost:
                    close_list.append(open_list.pop(i))
                    break
            if finished:
                break
        self.path.append({'coor': close_list[-1]['coor'],
                          'direction': close_list[-1]['direction'],
                          'parent': close_list[-1]['parent']})
        for step in range(len(close_list) - 1, -1, -1):
            if close_list[step]['coor'] == self.path[-1]['parent']:
                self.path.append({'coor': close_list[step]['coor'],
                                  'direction': close_list[step]['direction'],
                                  'parent': close_list[step]['parent']})
        self.path.reverse()
        """
        This part prints trolls' maps 
        It help for debugging
        for element in open_list:
            self.map.grid[element['coor']] = '"'
        for i in range(len(close_list)):
            self.map.grid[close_list[i]['coor']] = 'o'
        for j in self.path:
            self.map.grid[j['coor']] = 'p'
        print(self.map.__str__(self.game))
        print('next_turn')"""


if __name__ == '__main__':
    game = Game(60, 25)
    game.play()
