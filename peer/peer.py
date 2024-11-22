#client
import socket
import threading
import os
import sys
from helpers import parse_command
import numpy as np

class Peer :
    def __init__(
        self,
        id,
        ip='localhost',
        port=7001,
        tracker_ip='localhost',
        tracker_port=7777

    ) -> None : 
        # Assign address
        self.ip = ip
        self.port = port
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port

        # Personal information
        self.id = id

    def initPeer (self) :
        # Initialize and connect to tracker socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.tracker_ip, self.tracker_port))

        # Initialize CLI thread
        self.cli_thread = threading.Thread(target=self.initCLIThread)
        self.cli_thread.start()

        while True:
            try:
                data = self.socket.recv(1024).decode()
                
                if data:
                    print(data)
                    
                    
            except Exception as e:
                print(e)
                break
            except BaseException:
                print('Client is shutting down...')
                self.shutdown()
                break

    def initCLIThread(self) : 
        while True:
            try:
                command = input('Command: ')
                
                if command == 'ping' :
                    self.socket.send("ping".encode())
                elif command == 'stop' :
                    raise KeyboardInterrupt
                else :
                    method, content = parse_command(command)
                    if(method == 'SEED') : 
                        self.seed_files(content)
                    
                
            except Exception as e:
                print(e)
            except BaseException:
                self.shutdown()
            except KeyboardInterrupt:
                self.shutdown()
                break

    def seed_files(self, paths):
        seeded_files = ''

        for path in paths :
            exists = self.check_existence(path)
            if not exists:
                print(f'File path {path} does not exist.\n')
                return
            
            seeded_files = seeded_files + path + ' '
        
        request = 'SEED ' + seeded_files
        self.socket.send(request.encode())

    def check_existence (self, path):
        return os.path.isfile(path)

    def shutdown(self, payload=None):
        print('\nShutting Down...')
        self.socket.close()
        
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
        
if __name__ == '__main__':
    peer = Peer(id=sys.argv[1], ip=sys.argv[2], port=sys.argv[3])

    peer.initPeer()