#tracker
import socket
import threading
import sys 
import os
from helpers import parse_request

class Tracker:
    # Constructor of the tracker
    def __init__ (
        self, 
        ip='localhost',
        port=7777,
    ) :
        # Assign addresses
        self.ip = ip
        self.port = port
        
        # Lock for concurrency handling
        self.lock = threading.Lock()

        # Tracking list
        # {adress: peer}
        self.peer_list = {}

        # {file_name: peers : [address]}
        self.file_list = {}

    def shutdown(self, payload=None):
        print('\nShutting Down...')
        self.socket.close()
        
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
                
    # Initialize the socket server
    def initTracker (self) :
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(2)

        print('Tracker server is listening on %s:%s' % (self.ip, self.port))

        # CLI thread
        self.cli_thread = threading.Thread(target=self.initCLIThread)
        self.cli_thread.start()
        
        # Connection threads
        while True:
            try:
                peer, address = self.socket.accept()
                print('A peer with address %s:%s has connected!' % (address[0], address[1]))
                
                self.peer_list[address] = peer

                # Create thread to handle each peer connection
                peer_handler = threading.Thread(
                    target=self.handle_peer_connection,
                    args=(peer, address)
                )

                peer_handler.start()
                print('Command: ')
            except KeyboardInterrupt:
                print('Server is shutting down...')
                self.shutdown()
                break
    
    def initCLIThread(self) : 
        while True:
            try:
                command = input('Command: ')

                if command == 'view peers' :
                    self.view_peers()

                elif command == 'view files' :
                    self.view_files()
                
                elif command == 'stop' :
                    raise KeyboardInterrupt
                
                else : continue

            except Exception as e:
                print(e)
            except BaseException:
                self.shutdown()
            except KeyboardInterrupt:
                self.shutdown()
                break

    def handle_peer_connection(self, peer_socket: socket.socket, address):
        while True:
            try:
                request = peer_socket.recv(1024).decode()
                
                if(request == ''):
                    raise AttributeError
                else :
                    method, content = parse_request(request)
                    if method == 'SEED' :
                        for file in content :
                            components = file.split('/')
                            filename = components[len(components) - 1]
                            self.insert_file(filename=filename, address=address)


            except ConnectionError:
                print(f'Peer at {address} disconnected.\n> ', end='')
                print('Command: ')
                break
            except Exception:
                break

    def insert_file(self, filename, address) :
        if not filename in self.file_list : self.file_list[filename] = []
        
        self.file_list[filename].append(address)
        
    
    # VIEW METHODS
    def view_peers(self) :
        print('Connected peer list: \n')
        for address, peer in self.peer_list :
            print(str(address) + ': ' + str(peer) + '\n')
        print('Total number of connected peers: ' + str(len(self.peer_list)) + '\n')

    def view_files(self) :
        print('Published file list: \n')
        print(self.file_list)
        for filename in self.file_list.keys() :
            print(str(filename) + ':\n')
            for peer in self.file_list[filename] :
                print('> ' + str(peer) + '\n')
        print('Total number of published files: ' + str(len(self.file_list)) + '\n')    

if __name__ == '__main__':
    trackerServer = Tracker(ip='localhost')

    trackerServer.initTracker()
    