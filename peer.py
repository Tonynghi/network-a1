#peer
import socket
import threading
import os
import sys
import requests
import numpy as np
from helpers import parse_command
from colorama import Fore, Back, Style
from flask import jsonify
from hashlib import sha256

class Peer : 
    def __init__ (
            self,
            id,
            upload_port,
            download_port,
            self_host = 'localhost',
            tracker_host = 'localhost',
            tracker_port = 7000,

    ) -> None :
        self.id = id
        self.self_host = self_host
        self.upload_port = int(upload_port)
        self.upload_port = int(download_port)
        self.tracker_host = tracker_host
        self.tracker_port = int(tracker_port)
        self.tracker_url = 'http://' + self.tracker_host + ':' + str(self.tracker_port)

    def init(self) : 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.self_host, self.upload_port))
        self.socket.listen(1)

        print('Peer is listening on %s:%s' % (self.self_host, self.upload_port))

        #CLI thread
        cli_thread = threading.Thread(target=self.init_cli)
        cli_thread.start()



    def init_cli(self) -> None : 
        while True:
            try:
                command = input('> ')

                if command == 'ping' :
                    print('pong')
                
                elif command == 'hello tracker' :
                    response = self.send_hello_request()
                    print(response)

                elif command == 'exit' :
                    raise KeyboardInterrupt
                
                else :
                    method, content = parse_command(command=command)
                    if(method == 'SEED') : 
                        valid = self.check_seed_files(paths=content)

                        if not valid :
                            raise Exception(Fore.RED +  'Some files can not be found! Abort command!\n' + Fore.WHITE)
                        response = self.send_seed_file_request(paths=content)
                        print({
                            'status': response.status_code,
                            'payload': response.json()
                        })
                    else :
                        print('Command unknown!\n> ')
                        continue

            except Exception as e:
                print(e)
            except BaseException:
                self.shutdown()
            except KeyboardInterrupt:
                self.shutdown()
                break
    
    # FUNCTIONS
    def check_seed_files(self, paths):
        valid = True

        if(len(paths) <= 0) :
            print(Fore.RED +  f'No file specified.\n' + Fore.WHITE)
            valid = False

        for path in paths :
            exists = self.check_existence(path)
            if not exists:
                print(Fore.RED +  f'File path {path} does not exist.\n' + Fore.WHITE)
                valid = False
        
        return valid

    def check_existence (self, path):
        return os.path.isfile(path)

    # REQUESTS
    def send_hello_request(self) :
        url = self.tracker_url + '/'

        response = requests.get(url=url)

        return response
    
    def send_seed_file_request(self, paths) :
        url = self.tracker_url + '/file'
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        files = []

        for path in paths :
            path_components = path.split('/')
            name = path_components[-1]
            size = os.path.getsize(path)
            infohash = sha256(name.encode()).hexdigest()
            files.append({
                'name': name,
                'size': size,
                'path': path,
                'infohash': infohash
            })

        data = {
            'files': files,
            'ip': self.self_host,
            'port': self.upload_port,
            'id': self.id
        }

        response = requests.post(url=url, json=data, headers=headers)

        return response

    def shutdown(self, payload=None) -> None:
        print('\nShutting Down...')

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__' :
    peer = Peer(id=sys.argv[1], self_host=sys.argv[2], upload_port=sys.argv[3], download_port=sys.argv[4])

    peer.init()
