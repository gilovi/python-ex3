__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys

import Protocol

MAX_CONNECTIONS = 2  # DO NOT CHANGE
ERROR_EXIT = 1
PLAYERS = 2


class Server:
    def __init__(self, s_name, s_port):
        self.server_name = s_name
        self.server_port = s_port

        self.l_socket = None
        self.players_sockets = []
        self.players_names = []

        self.all_sockets = []

        """
        DO NOT CHANGE
        If you want to run you program on windowns, you'll
        have to temporarily remove this line (but then you'll need
        to manually give input to your program). 
        """
        self.all_sockets.append(sys.stdin)

    def connect_server(self):

        # Create a TCP/IP socket_to_server
        try:
            self.l_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.l_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # DP NOT CHANGE
        except socket.error as msg:

            self.l_socket = None
            sys.stderr.write(repr(msg) + '\n')
            exit(ERROR_EXIT)

        server_address = (self.server_name, int(self.server_port))
        try:
            self.l_socket.bind(server_address)
            self.l_socket.listen(MAX_CONNECTIONS)
            self.all_sockets.append(self.l_socket)  # this will allow us to use Select System-call
        except socket.error as msg:
            self.l_socket.close()
            self.l_socket = None
            sys.stderr.write(repr(msg) + '\n')
            exit(ERROR_EXIT)

        print "*** Server is up on %s ***" % server_address[0]
        print

    def shut_down_server(self,err):
        for soc in filter(lambda (x): x is not sys.stdin, self.all_sockets):
            soc.close()
            print
            print '*** Server is down ***'
            exit(err)

    def __handle_standard_input(self):

        """
        handles the standard input of client.

        """
        msg = sys.stdin.readline().strip().upper()

        if msg == 'EXIT':
            self.shut_down_server(0)

    def __handle_new_connection(self):

        connection, client_address = self.l_socket.accept()

        # Request from new client to send his name
        eNum, eMsg = Protocol.send_all(connection, "ok_name")
        if eNum:
            sys.stderr.write(eMsg)
            self.shut_down_server(1)

        # ###############################################


        # Receive new client's name
        num, msg = Protocol.recv_all(connection)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.shut_down_server(1)
        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            sys.stderr.write(msg)
            self.shut_down_server(1)

        self.players_names.append(msg)

        self.players_sockets.append(connection)
        self.all_sockets.append(connection)
        print "New client named '%s' has connected at address %s." % (msg, client_address[0])

        if len(self.players_sockets) == 2:  # we can start the game
            self.__set_start_game(0)
            self.__set_start_game(1)

    def __set_start_game(self, player_num):
        welcome_msg = "start|turn|" + self.players_names[1] if not player_num else "start|not_turn|" + self.players_names[0]

        eNum, eMsg = Protocol.send_all(self.players_sockets[player_num], welcome_msg)
        if eNum:
            sys.stderr.write(eMsg)
            self.shut_down_server(1)

    def __handle_existing_connections(self):

        """
        this method handles connections.
        if somebody disconnected it informs the other. and in any other case (not error), it
        simply sends the message to the other
        """
        # find out witch socket is the active one & witch isn't
        r_socket = select.select(self.players_sockets, [], [])[0][0]  # recived socket
        s_socket = [soc for soc in self.players_sockets if soc is not r_socket][0]  # socket to send in
        # Receive client's message
        num, msg = Protocol.recv_all(r_socket)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.shut_down_server(1)
		
        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            self.inform_disconnection(s_socket)

        else:
            eNum, eMsg = Protocol.send_all(s_socket, msg)
            if eNum:
                sys.stderr.write(eMsg)
                self.shut_down_server(1)
	
    def inform_disconnection(self, s_socket):
        """
        informs a player that the other one has disconnected
        :param s_socket: the socket of the informed player
        """
        msg = 'client:EXIT:EXIT'
        eNum, eMsg = Protocol.send_all(s_socket, msg)
        if eNum:
            sys.stderr.write(eMsg)
            self.shut_down_server(1)
        self.shut_down_server(0)

    def run_server(self):

        while True:

            r_sockets = select.select(self.all_sockets, [], [])[0]  # We won't use writable and exceptional sockets

            if sys.stdin in r_sockets:
                self.__handle_standard_input()

            elif self.l_socket in r_sockets:
                self.__handle_new_connection()

            elif self.players_sockets[0] in \
                    r_sockets or \
                    self.players_sockets[1] in r_sockets:

                self.__handle_existing_connections()


def main():
    server = Server(sys.argv[1], int(sys.argv[2]))
    server.connect_server()
    server.run_server()


if __name__ == "__main__":
    main()
