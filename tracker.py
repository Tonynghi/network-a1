import threading
import sys 
import os
import json
from flask import Flask, request, jsonify

class Tracker : 
    def __init__ (
        self, 
        ip='localhost',
        port=7000,
    ) -> None :
        self.ip = ip
        self.port = port

        # Lock for concurrency handling
        self.lock = threading.Lock()

        # Tracking list
        self.peer_list = {}
        self.file_list = {}

        # Flask app
        self.app = None

    def init(self) -> None :
        print('Initializing tracker ...')

        # Flask thread
        flask_thread = threading.Thread(target=self.init_flask, daemon=True)
        flask_thread.start()

        #CLI thread
        cli_thread = threading.Thread(target=self.init_cli)
        cli_thread.start()
    

    def init_flask(self) -> None :
        self.app = Flask(__name__)

        @self.app.route('/', methods=['GET'])
        def home():
            tracker_info = {
                'name': 'Tracker for torrent connection',
                'message': 'Hello World!'
            }
            return jsonify(tracker_info), 200
        
        @self.app.route('/file/<infohash>', methods=['GET'])
        def search_file(infohash):
            if not infohash in self.file_list :
                print(f'File with infohash {infohash} not found!')
                return self.generate_error_response_json(message='File not found!', status=404)
            
            file_data = self.file_list[infohash]
            peers = []

            for seed in file_data['seeds'] : 
                peers.append({
                    'peer_id': seed['id'],
                    'ip': seed['ip'],
                    'port': seed['port'],
                })

            response_payload = {
                'tracker_id': f'{self.ip}:{self.port}',
                'peers': peers
            }

            return jsonify(response_payload), 200

        @self.app.route('/file', methods=['POST'])
        def seed_file():
            data = request.get_json()
            id = data['id']
            ip = data['ip']
            port = str(data['port'])

            if not id or id.strip() == '' :
                return self.generate_error_response_json(message='Missing Seed ID!', status=400)

            if not ip or ip.strip() == '' :
                return self.generate_error_response_json(message='Missing Seed IP Address!', status=400)
            
            if not port or port.strip() == '' :
                return self.generate_error_response_json(message='Missing Seed Port!', status=400)
            
            files = data['files']

            if len(files) <= 0 :
                return self.generate_error_response_json(message='Missing files to be seeded!', status=400)

            response_payload = []

            self.lock.acquire() # Concurrency handling
            for file in files:
                # file = json.loads(json.dumps(file))
                valid = self.insert_file(infohash=file['infohash'], name=file['name'], size=file['size'], path=file['path'], id=id, ip=ip, port=port)
                if valid : 
                    response_payload.append(file)
            self.lock.release()

            return jsonify(response_payload), 200


        self.app.run(host=self.ip, port=self.port)

    def init_cli(self) -> None : 
        while True:
            try:
                command = input('> ')

                if command == 'view peers' :
                    self.view_peers()

                elif command == 'view files' :
                    self.view_files()
                
                elif command == 'exit' :
                    raise KeyboardInterrupt
                
                else : continue

            except Exception as e:
                print(e)
            except BaseException:
                self.shutdown()
            except KeyboardInterrupt:
                self.shutdown()
                break

    def shutdown(self, payload=None) -> None:
        print('\nShutting Down...')

        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    # FUNCTIONALITY
    def insert_file(self, infohash, name, size, path, ip, port, id) :
        valid = True

        if not infohash in self.file_list : self.file_list[infohash] = {
            'name': name,
            'size': size,
            'seeds': []
        }

        peer_data = {
            'id': id,
            'ip': ip,
            'port': port,
            'path': path,
        }

        if peer_data in self.file_list[infohash]['seeds'] :
            valid = False 
            print(f'This peer has already contributed this file!\n')
        
        self.file_list[infohash]['seeds'].append(peer_data)
        
        if not id in self.peer_list : self.peer_list[id] = {
            'id': id,
            'ip': ip,
            'port': port,
            'files': []
        }
        
        file_data = {
            'infohash': infohash,
            'name': name,
            'size': size
        }

        self.peer_list[id]['files'].append(file_data)

        return valid

    # VIEW METHODS
    def view_peers(self) :
        print('Contributed peer list: \n')
        for address in self.peer_list.keys() :
            print(f'{address}:\nContributed files:\n' )
            for path in self.peer_list[address] :
                print(f'> {path}\n')
        print('Total number of contributed peers: ' + str(len(self.peer_list)) + '\n')

    def view_files(self) :
        print('Published file list: \n')
        for infohash in self.file_list.keys() :
            file_data = self.file_list[infohash]
            print('----------\n')
            print(f'Name: {file_data['name']}\n')
            print(f'Infohash: {infohash}\n')
            print(f'Size: {file_data['size']}B\n')
            print(f'Seeds:\n')
            for seed in self.file_list[infohash]['seeds'] :
                print(f'  > Peer:  {seed['id']}\n')
                print(f'    IP Address:  {seed['ip']}\n')
                print(f'    Download port:  {seed['port']}\n\n')
            print('----------\n')
        print('Total number of published files: ' + str(len(self.file_list)) + '\n')

    # HELPERS
    def generate_error_response_json(self, message, status) :
        response = {
            'failure_reason': message
        }

        return jsonify(response), status


if __name__ == '__main__' :
    tracker = Tracker(ip='localhost', port=7000)

    tracker.init()

