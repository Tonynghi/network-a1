#helpers.py
import numpy as np

def parse_command(command) :
    if((not command) or command == '') : return None, None

    components = np.array(command.split())

    if len(components) <= 1 : return None, None

    method = components[0].strip().upper()
    content = np.array(components[1:])

    return method, content

