#peer
import socket
import threading
import os
import sys
import requests
import numpy as np
import json
import math
import mmap
from helpers import parse_command
from colorama import Fore, Back, Style
from flask import jsonify
from hashlib import sha256

class Peer : 
    def __init__ (
            self,
            id,
            upload_port,
            self_host = 'localhost',
            tracker_host = 'localhost',
            tracker_port = 7000,

    ) -> None :
        self.id = id
        self.self_host = self_host
        self.upload_port = int(upload_port)
        self.tracker_host = tracker_host
        self.tracker_port = int(tracker_port)
        self.tracker_url = 'http://' + self.tracker_host + ':' + str(self.tracker_port)

    def init(self) : 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.self_host, self.upload_port))

        #Socket listen thread
        listen_thread = threading.Thread(target=self.init_listen)
        listen_thread.start()

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
                        valid = self.check_seed_files(names=content)

                        if not valid :
                            raise Exception(Fore.RED +  'Some files can not be found! Abort command!\n' + Fore.WHITE)
                        response = self.send_seed_file_request(names=content)

                        if (response.status_code == 200) : 
                            print(Fore.GREEN + 'Sucessfully seeded files' + Fore.WHITE)
                        
                        self.print_response(response=response.json(), status_code=response.status_code)
                    elif(method == 'SEARCH') :
                        if(len(content) != 1) : 
                            raise Exception(Fore.RED +  'Only one file can be submitted for this command! Abort command!\n' + Fore.WHITE)
                        
                        response = self.send_search_file_request(name=content[0])

                        if (response.status_code == 200) : 
                            print(Fore.GREEN + 'Sucessfully searched for the file' + Fore.WHITE)
                        self.print_response(response=response.json(), status_code=response.status_code)
                    elif(method == 'DOWNLOAD') :
                        # if(len(content) != 1) : 
                        #     raise Exception(Fore.RED +  'Only one file can be submitted for this command! Abort command!\n' + Fore.WHITE)
                        
                        # self.init_download(content[0])

                        if(len(content) <= 0) : 
                            raise Exception(Fore.RED +  'A minimum number of 1 file name must be submitted for this command!\n' + Fore.WHITE)
                        
                        download_file_threads = []
                        for name in content :
                            download_file_thread = threading.Thread(target=self.init_download, args=(name,))
                            download_file_thread.start()
                            download_file_threads.append(download_file_thread)
                        for download_file_thread in  download_file_threads :
                            download_file_thread.join()
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

    def init_listen(self) -> None :
        self.socket.listen(5)
        print(f'Peer {self.id} is listening on {self.self_host}:{self.upload_port}')

        while True :
            try :
                connection, address = self.socket.accept()
                print(f'Peer with address {address[0]}:{address[1]} connected.\n')
                
                request = connection.recv(1024)
                if not request : break

                print(f'Request: {request.decode()}')
                parsed_request = json.loads(request.decode())
                name = parsed_request['name']
                index = parsed_request['index']
                count = parsed_request['count']

                # Create threads to handle each peer request
                peer_request_handler = threading.Thread(
                    target=self.handle_download_chunk_request,
                    args=(name, index, count, connection, address[0], address[1])
                )

                peer_request_handler.start()
            except Exception as e:
                print(e)
                break
            except BaseException:
                print('Peer is shutting down...')
                self.shutdown()
                break

    def init_download(self, name) :
        path = './data/' + name
        exists = self.check_existence(name=name)

        if exists : 
            print(f'File {name} already exists in system!')
            return
        
        response = self.send_search_file_request(name=name)
        print(response)

        if response.status_code == 404 :
            print(Fore.RED + f'File {name} is not found or not seeded yet!' + Fore.WHITE)
            return
        
        if response.status_code != 200 :
            print(Fore.RED + f'Something has gone wrong while downloading file {name}!' + Fore.WHITE)
            return
        
        payload = response.json()
        peers = payload['peers']
        peer_count = len(peers)
        
        file_chunks = []
        download_chunk_threads = []
        # Download chunks by creating connections to peers and receive chunks sent by them 
        for index, peer in enumerate(peers) :
            id = peer['peer_id']
            ip = peer['ip']
            port = peer['port']
            download_chunk_thread = threading.Thread(target=self.download_chunk_from_peer, args=(id, ip, port, name, index, peer_count, file_chunks))
            download_chunk_thread.start()
            download_chunk_threads.append(download_chunk_thread)
        for download_chunk_thread in download_chunk_threads :
            download_chunk_thread.join()

        file_chunks.sort(key=lambda tup: tup[0])

        # print(file_chunks)
        print('Download process completed! Assembling chunks ...')

        self.create_file_from_chunks(chunk_list=file_chunks,path=path)

        print(Fore.GREEN + f'File {name} is completely assembled! Process completed' + Fore.WHITE)
    
    # FUNCTIONS
    def check_seed_files(self, names):
        valid = True

        if(len(names) <= 0) :
            print(Fore.RED +  f'No file specified.\n' + Fore.WHITE)
            valid = False

        for name in names :
            exists = self.check_existence(name)
            if not exists:
                print(Fore.RED +  f'File named {name} does not exist.\n' + Fore.WHITE)
                valid = False
        
        return valid

    def check_existence (self, name):
        path = './data/' + name
        return os.path.isfile(path)
    
    def get_chunk (self, path, chunk_size, index) :
        file = open(path, 'r+b')
        start = chunk_size * index
        end = chunk_size * (index + 1)
        chunk_map = mmap.mmap(file.fileno(), 0)[start:end]
        file.close()
        return chunk_map
    
    def create_file_from_chunks(self, chunk_list, path) :
        file = open(path, 'bx+')
        for index, chunk in chunk_list :
            encoded_data = str(chunk).encode()
            file.write(encoded_data)
        file.close()
    
    # PEER CONNECTIONS
    def download_chunk_from_peer(self, id, ip, port, name, index, peer_count, file_chunks) : 
        connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        download_request = {
            'name': name,
            'id': id,
            'index': index,
            'count': peer_count
        }
        dumped_download_request = json.dumps(download_request)
        try :
            connect_socket.connect((ip, int(port)))
            print(f'Sucessfully connected to peer {id} with address {ip}:{port}! Sending request ...\n')
            connect_socket.sendall(dumped_download_request.encode())
            print(f'Request sent to peer {id}! Waiting for data ..')
        except Exception as e :
            print(e)
            return None
        
        while True :
            response = connect_socket.recv(1024).decode()
            if not response : break

            parsed_response = json.loads(response)

            file_chunks.append((parsed_response['index'], parsed_response['chunk_map']))

            break

    def handle_download_chunk_request (self, name, index, count, connection, ip, port) -> None :
        # print(f'File name: {name}\n')
        # print(f'Chunk index: {index}\n')
        # print(f'Total count of chunks: {count}\n')

        path = './data/' + name
        exists = self.check_existence(name=name)

        if not exists : 
            response = 'File does not exist in this peer system! Abort download!' 
            connection.sendall(response.encode())
            return
        
        size = os.path.getsize(path)
        chunk_size = math.ceil(size / count)

        print(chunk_size)

        chunk_map = self.get_chunk(path=path, chunk_size=chunk_size, index=index)

        response = {
            'name': name,
            'id': self.id,
            'source_ip': self.self_host,
            'source_port': self.upload_port,
            'index': index,
            'chunk_map': chunk_map.decode(encoding='utf-8')
        }

        connection.sendall(json.dumps(response).encode())

        print(f'A chunk has been sent back as requested by peer at {ip}:{port}')

    # REQUESTS
    def send_hello_request(self) :
        url = self.tracker_url + '/'

        response = requests.get(url=url)

        return response
    
    def send_seed_file_request(self, names) :
        url = self.tracker_url + '/file'
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        files = []

        for name in names :
            # path_components = path.split('/')
            # name = path_components[-1]
            path = './data/' + name
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
    
    def send_search_file_request(self, name) :
        infohash = sha256(name.encode()).hexdigest()
        url = self.tracker_url + '/file/' + infohash

        response = requests.get(url=url)

        return response

    def print_response(self, response, status_code) :
        print({
            'status': status_code,
            'payload': response
        })

    def shutdown(self, payload=None) -> None:
        print('\nShutting Down...')

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

if __name__ == '__main__' :
    peer = Peer(id=sys.argv[1], self_host=sys.argv[2], upload_port=sys.argv[3])

    peer.init()
