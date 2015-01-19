from itertools import product
from copy import deepcopy

__author__ = 'gilmor'


class Player:
    def __init__(self, name, ships):
        self.__name = name
        self.board = Board(ships)
        self.op_board = Board()
        
	
    def update_results(self, place, result, board, index=None):
	"""
	updates a given board (my board or the opponent's by a given result)
	:param place: the place to update
	:param result: the given result
	:param board:the board to update
	:param index: optional. the ship index which the place is part of
	"""
        {'HIT': board.add_hit,
         'MISS': board.add_miss,
         'SUNK': board.sunk,
         'LOST': board.lost}.get(str(result))({place}, index)
         
	
    def defend(self, place):
	"""
	finds the result for an attack on place and updates the board with it
	"""
        result = ''
        hit = [i for i, ship in enumerate(self.board.unhit_ships) if place in ship]
        if hit:
            # we have a 'hit'
            result = 'HIT'
            if len(self.board.unhit_ships[hit[0]]) == 1:
                # the hit place is the last place in the ship - ship is destroyed.
                result = 'SUNK'
                if len(self.board.unhit_ships) == 1:
                    #this was the last ship - we lost!
                    result = 'LOST'
        else:
            result = 'MISS'
        self.update_results(place, result, self.board, hit[0] if hit else None)
        return result


class Board:

    def __init__(self, ships=[]):
        self.ships = ships
        self.unhit_ships = deepcopy(self.ships)
        self.hits = set()
        self.miss = set()

	
    def add_hit(self, place, index):

        """
        adds a hit to the board.
        additionally, if we knew about the ship, remove the place in the corresponding ship of
        that index
        if we didn't know, add the place to a ship in __ships.
        :param place: set of tuple represents the place on the board that was been hit
        :param index: the hit ship index in ships. if none, we didn't know about this ship part
        existence.
        """
        place = list(place).pop()
        if index is not None:
            self.unhit_ships[index].remove(place)
            if self.unhit_ships[index] == set([]):
                self.unhit_ships.pop(index)
        else:
            # its an opponent's ship.
            index = self.add_ship_pos(place)

        self.hits |= {place}
        return index

    def add_miss(self, places, index):
        """
        adds a set of places to the missed places on the board
        :param places: is tuples set of the places to add to the miss list
        :param index: not used.
        """
        self.miss |= places

    def sunk(self, last_place, index):
        """
        the operations that happens when a ship is sunk:
        remove the ship from self.ships add the last place to the hit list and runs a BFS to add
        all the ships surroundings to the miss set
        :param last_place: the last hit place in the ship.
        """
        index = self.add_hit(last_place, index)
        self.miss_surroundings(index)


    def lost(self, place, index):
        """
        the operations happens in case of loss in the game board,
        for completeness purpose (don't do anything fancy yet)
        :param place:the place that was hit
        :param index: the hit ship index
        """
        self.sunk(place, index)


    def add_ship_pos(self, place):
        """
        using the prior knowledge of the ship's shapes to determine place belonging to a ship,
        and adds the place to that ship. (if no fitting ship, create a new one)
        :param place: the place to add to one of the ships
        :return:
        """
        adjacents = self.get_adjacents(place)
        ship_index = {i for i, ship in enumerate(self.ships) for aj in adjacents if aj in ship}
        if ship_index:
            f_ind = ship_index.pop()
            # if this place connects few different ships to one ship we update the ships accordingly
            while ship_index:
                ind = ship_index.pop()
                self.ships[f_ind] |= self.ships.pop(ind)
            # add the place to the ship it belongs to
            self.ships[f_ind].add(place)
        else:
            # there is no 'mother ship' so create a new one
            self.ships.append({place})
            f_ind = len(self.ships) - 1

        return f_ind

    def get_adjacents(self, place):
        int_letter = ord(place[0])
        return list(product(map(chr, range(int_letter - 1, int_letter + 2)),
			(map(str, range(int(place[1]) - 1, int(place[1]) + 2)))))
       
    def miss_surroundings(self, index):
        ship = self.ships[index]
        missed = {adj for place in ship for adj in self.get_adjacents(place) if
                  adj not in ship}
        self.add_miss(missed, None)

