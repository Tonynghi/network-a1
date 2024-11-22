#helpers.py
import numpy as np

def parse_command(command) :
    if((not command) or command == '') : return None, None

    components = np.array(command.split())

    if len(components) <= 1 : return None, None

    method = components[0].strip().upper()
    content = np.array(components[1:])

    return method, content



def parse_request(request) :
    
    if((not request) or request == '') : return None, None

    components = np.array(request.split())

    method = None
    content = None

    if(components[0].upper().strip() == 'GET') :
        method = 'GET'
        content = np.array(components[1:])
    elif (components[0].upper().strip() == 'SEED') :
        method = 'SEED'
        content = np.array(components[1:])

    return method, content

