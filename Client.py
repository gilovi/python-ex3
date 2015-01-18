__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys
import Protocol
from Player import Player
from copy import deepcopy
import re

EXIT_ERROR = 1
BOARD_SIZE = 10
MISS_CHAR = 'X'
HIT_CHAR = 'H'
SHIP_CHAR = '0'


class Client:
    def __init__(self, s_name, s_port, player_name, player_ships):

        self.server_name = s_name
        self.server_port = s_port

        self.player_name = player_name
        self.opponent_name = ""
        self.player = Player(player_name, parse_ships(player_ships))
        self.my_turn = False
        self.last_attack = ('')

        self.socket_to_server = None

        self.all_sockets = []

        """
        DO NOT CHANGE
        If you want to run you program on windowns, you'll
        have to temporarily remove this line (but then you'll need
        to manually give input to your program). 
        """
        self.all_sockets.append(sys.stdin)  # DO NOT CHANGE

    def connect_to_server(self):

        # Create a TCP/IP socket_to_server
        try:
            self.socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:

            self.socket_to_server = None
            sys.stderr.write(repr(msg) + '\n')
            exit(EXIT_ERROR)

        server_address = (self.server_name, int(self.server_port))
        try:
            self.socket_to_server.connect(server_address)
            self.all_sockets.append(
                self.socket_to_server)  # this will allow us to use Select System-call

        except socket.error as msg:
            self.socket_to_server.close()
            self.socket_to_server = None
            sys.stderr.write(repr(msg) + '\n')
            exit(EXIT_ERROR)

        # we wait to get ok from server to know we can send our name
        num, msg = Protocol.recv_all(self.socket_to_server)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.close_client()

        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print "Server has closed connection."
            self.close_client()

        # send our name to server
        eNum, eMsg = Protocol.send_all(self.socket_to_server, sys.argv[3])
        if eNum:
            sys.stderr.write(eMsg)
            self.close_client()

        print "*** Connected to server on %s ***" % server_address[0]
        print
        print "Waiting for an opponent..."
        print

    def close_client(self):

        self.socket_to_server.close()

        print
        print "*** Goodbye... ***"
        exit(0)

    def __handle_standard_input(self):

        msg = sys.stdin.readline().strip().upper()

        if msg == 'EXIT':  # user wants to quit
            self.close_client()

        elif self.my_turn:
            self.send_attack(msg)
            self.last_attack = tuple(msg.split(' '))
            self.my_turn = False

    def __handle_server_request(self):

        num, msg = Protocol.recv_all(self.socket_to_server)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.close_client()

        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print "Server has closed connection."
            self.close_client()

        if "start" in msg:
            self.__start_game(msg)

        elif msg:
            (who, what, data) = msg.split(':')

            if what == 'EXIT':
				print 'Your opponent has disconnected. You win!\n'
				self.close_client()

            if who == 'client':
				result = {'attacking': self.defend,
                          'defending': self.update_result,
                          }.get(what)(data.upper())

				if result:
					self.send_defend(result)
					self.my_turn = True
					print
					print self.opponent_name + ' plays: ' + data
					self.print_board()
					print "It's your turn..."
                    
				else:
					self.print_board()
                    # else: #its the server talking...
                    # if  what == 'turn' :
                    #         self.my_turn = True
                    #         print "It's your turn..."
                    #
                    #     elif what == 'not_turn' : self.my_turn = False

    def update_result(self, result):
        self.player.update_results(self.last_attack, result, self.player.op_board)
        return None

    def defend(self, place):

        return self.player.defend(tuple(place.split(' ')))

    def send_defend(self, result):
        msg = 'client:defending:' + result

        eNum, eMsg = Protocol.send_all(self.socket_to_server, msg)
        if eNum:
            sys.stderr.write(eMsg)
            self.close_client()

    def send_attack(self, place):
        msg = 'client:attacking:' + place

        eNum, eMsg = Protocol.send_all(self.socket_to_server, msg)
        if eNum:
            sys.stderr.write(eMsg)
            self.close_client()

    def __start_game(self, msg):

        print "Welcome " + self.player_name + "!"

        self.opponent_name = msg.split('|')[2]
        print "You're playing against: " + self.opponent_name + ".\n"

        self.print_board()
        if "not_turn" in msg:
            return

        print "It's your turn..."
        self.my_turn = True

    letters = list(map(chr, range(65, 65 + BOARD_SIZE)))

    def print_board(self):
        hits = self.player.board.hits
        miss = self.player.board.miss
        ships = [place for ship in (self.player.board.ships) for place in ship]

        op_hits = self.player.op_board.hits
        op_miss = self.player.op_board.miss

        """
        TODO: use this method for the prints of the board. You should figure
        out how to modify it in order to properly display the right boards.
        """
        print
        print "%s %59s" % ("My Board:", self.opponent_name + "'s Board:"),

        print
        print "%-3s" % "",
        for i in range(BOARD_SIZE):  # a classic case of magic number!
            print "%-3s" % str(i + 1),

        print(" |||   "),
        print "%-3s" % "",
        for i in range(BOARD_SIZE):
            print "%-3s" % str(i + 1),

        print

        for i in range(BOARD_SIZE):
            print "%-3s" % Client.letters[i],
            for j in range(BOARD_SIZE):
                place = (Client.letters[i], str(j+1))
                print "%-3s" % self.get_char(place, hits, miss, ships),

            print(" |||   "),
            print "%-3s" % Client.letters[i],
            for j in range(BOARD_SIZE):
                place = (Client.letters[i], str(j+1))
                print "%-3s" % self.get_char(place, op_hits, op_miss, []),

            print

        print

    def get_char(self, place, hits, miss, ships):

        return HIT_CHAR if place in hits else MISS_CHAR if place in miss else SHIP_CHAR if place in ships else '*'

    def run_client(self):

        while True:

            r_sockets = select.select(self.all_sockets, [], [])[
                0]  # We won't use writable and exceptional sockets

            if sys.stdin in r_sockets:
                self.__handle_standard_input()

            elif self.socket_to_server in r_sockets:
                self.__handle_server_request()


def parse_ships(ship_path):
    ships = []
    with open(ship_path, 'r') as f:

        for line in f:
            ship = set()
            places = line.split(',')
            for place in places:
                match = re.match('([A-Z])(\d+)', place)
                ship.add((match.group(1), match.group(2)))
            ships.append(ship)
	return ships	

def main():
    client = Client(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
    client.connect_to_server()
    client.run_client()


if __name__ == "__main__":
    main()
