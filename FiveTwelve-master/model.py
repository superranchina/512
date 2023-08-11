"""
The game state and logic (model component) of 512, 
a game based on 2048 with a few changes. 
This is the 'model' part of the model-view-controller
construction plan.  It must NOT depend on any
particular view component, but it produces event 
notifications to trigger view updates. 
"""

from game_element import GameElement, GameEvent, EventKind
from typing import List, Tuple, Optional
import random

# Configuration constants
GRID_SIZE = 4


class Vec():
    """A Vec is an (x,y) or (row, column) pair that
    represents distance along two orthogonal axes.
    Interpreted as a position, a Vec represents
    distance from (0,0).  Interpreted as movement,
    it represents distance from another position.
    Thus we can add two Vecs to get a Vec.
    """
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: 'Vec') -> bool:
        return self.x == other.x and self.y == other.y

    def __add__(self, other: 'Vec') -> 'Vec':
        new_x = self.x + other.x
        new_y = self.y + other.y
        return Vec(new_x, new_y)


class Tile(GameElement):
    """A slidy numbered thing."""

    def __init__(self, pos: Vec, value: int):
        super().__init__()
        self.row = pos.x
        self.col = pos.y
        self.value = value

    def __repr__(self):
        """Not like constructor --- more useful for debugging"""
        return f"Tile[{self.row},{self.col}]:{self.value}"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other: "Tile"):
        return self.value == other.value

    def move_to(self, new_pos: Vec):
        self.row = new_pos.x
        self.col = new_pos.y
        self.notify_all(GameEvent(EventKind.tile_updated, self))

    def merge(self, other: "Tile"):
        # This tile incorporates the value of the other tile
        self.value = self.value + other.value
        self.notify_all(GameEvent(EventKind.tile_updated, self))
        # The other tile has been absorbed.  Resistance was futile.
        other.notify_all(GameEvent(EventKind.tile_removed, other))


class Board(GameElement):
    """The game grid.  Inherits 'add_listener' and 'notify_all'
    methods from game_element.GameElement so that the game
    can be displayed graphically.
    """

    def __init__(self, rows=4, cols=4):
        # this is same code as the code in HOWTO.md
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.tiles = [ ]
        for row in range(rows):
            row_tiles = [ ]
            for col in range(cols):
                row_tiles.append(None)
            self.tiles.append(row_tiles)

    def __getitem__(self, pos: Vec) -> Tile:
        return self.tiles[pos.x][pos.y]

    def __setitem__(self, pos: Vec, tile: Tile):
        self.tiles[pos.x][pos.y] = tile

    def _empty_positions(self) -> List[Vec]:
        # Same as HOWTO.md
        empties = []
        for row in range(len(self.tiles)):
            for col in range(len(self.tiles[row])):
                if self.tiles[row][col] is None:
                    empties.append(Vec(row, col))
        return empties

    def has_empty(self) -> bool:
        # use len to check the lengh of em_list
        # if is not empty, return True
        em_list = self._empty_positions()
        if len(em_list) != 0:
            return True

    def place_tile(self, value=None):
        """Place a tile on a randomly chosen empty square."""
        empties = self._empty_positions()
        assert len(empties) > 0
        choice = random.choice(empties)
        row, col = choice.x, choice.y
        if value is None:
            # 0.1 probability of 4
            if random.random() > 0.1:
                value = 2
            else:
                value = 4
        new_tile = Tile(Vec(row, col), value)
        self.tiles[row][col] = new_tile
        self.notify_all(GameEvent(EventKind.tile_created, new_tile))

    def to_list(self) -> List[List[int]]:
        """Test scaffolding: represent each Tile by its
        integer value and empty positions as 0
        """
        # same as HOWTO
        result = []
        for row in self.tiles:
            row_values = []
            for col in row:
                if col is None:
                    row_values.append(0)
                else:
                    row_values.append(col.value)
            result.append(row_values)
        return result

    def from_list(self, values: List[List[int]]):
        """Test scaffolding: set board tiles to the
        given values, where 0 represents an empty space.
        """
        # ues nested for loop to get the every elements' index,
        # and check every position in the list Value,
        # if there is a 0 in the list we check, make it
        # to 0, and if that element is not 0, we set the list into a tile by
        # calling Tile(), and return copy it into the board, which is self.tiles.
        # at last, return self.tiles.
        for row in range(len(values)):
            for col in range(len(values[row])):
                if values[row][col] == 0:
                    self.tiles[row][col] = None
                else:
                    self.tiles[row][col] = Tile(Vec(row, col), values[row][col])
        return self.tiles

    def in_bounds(self, pos: Vec) -> bool:
        """Is position (pos.x, pos.y) a legal position on the board?"""
        # rows = how many list in the self.tiles.
        # cols = how many element in a list of rows, since lists in the self.tiles all
        # have same length, so I check the first list of self.tiles.
        # and I let x,y get the position data from "pos" ,
        # if each of them are greater than 0, and less than rows - 1 and cols - 1,
        # because the len() is from 0 to start to count.
        rows = len(self.tiles)
        cols = len(self.tiles[0])
        x = pos.x
        y = pos.y
        if 0 <= x <= rows - 1 and 0 <= y <= cols - 1:
            return True
        else:
            return False

    def _move_tile(self, old_pos: Vec, new_pos: Vec):
        # copy the tile into new position.
        # let the old position in the board = None
        # tell the tile about new position
        self.tiles[new_pos.x][new_pos.y] = self.tiles[old_pos.x][old_pos.y]
        self.tiles[old_pos.x][old_pos.y] = None
        self[new_pos].move_to(new_pos)

    def slide(self, pos: Vec,  dir: Vec):
        """Slide tile at row,col (if any)
        in direction (dx,dy) until it bumps into
        another tile or the edge of the board.
        """
        # same as HOWTO.md
        if self[pos] is None:
            return
        while True:
            new_pos = pos + dir
            if not self.in_bounds(new_pos):
                break
            if self[new_pos] is None:
                self._move_tile(pos, new_pos)
            elif self[pos] == self[new_pos]:
                self[pos].merge(self[new_pos])
                self._move_tile(pos, new_pos)
                 # Stop moving when we merge with another tile
            else:
                # Stuck against another tile
                break
            pos = new_pos

    def right(self):
        # loop start from the the most right element
        # i creat two list to help me to loop in my order.
        # in this way, i cant control which element slide first.
        dir = Vec(0, 1)
        row = [0, 1, 2, 3]
        col = [3, 2, 1, 0]
        for i in row:
            for j in col:
                pos = Vec(i, j)
                self.slide(pos, dir)

    def left(self):
        # loop start from the the most left element
        dir = Vec(0, -1)
        row = [0, 1, 2, 3]
        col = [0, 1, 2, 3]
        for i in row:
            for j in col:
                pos = Vec(i, j)
                self.slide(pos, dir)

    def up(self):
        # loop start from the the most top element
        dir = Vec(-1, 0)
        row = [0, 1, 2, 3]
        col = [0, 1, 2, 3]
        for i in col:
            for j in row:
                pos = Vec(j, i)
                self.slide(pos, dir)

    def down(self):
        # loop start from the the deepest element
        dir = Vec(1, 0)
        row = [0, 1, 2, 3]
        col = [3, 2, 1, 0]
        for i in col:
            for j in row:
                pos = Vec(j, i)
                self.slide(pos, dir)

    def score(self) -> int:
        """
        Calculate a score from the board.
        (Differs from classic 1024, which calculates score
        based on sequence of moves rather than state of
        board.
        """
        score = 0
        for row in range(len(self.tiles)):
            for col in range(len(self.tiles[row])):
                value = self.tiles[row][col].value
                score += value
        return score


