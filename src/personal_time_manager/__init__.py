'''
This Application has 
- inputs (Sessions, backend)
- Main Algorithm (CSP)
- output (Sessions, backend)

The Main Routine
- Keeps looking for any new inputs..
- Upon Receiving a new input, the master algorithm is triggered
- Then new TimeTable is saved into the database and updated to all outputs
'''
import threading
from flask import Flask
from flask_cors import CORS
from .backend.app import main_routes

def gunicorn_main_routine():
    '''
    starts all underlying inputs, algorithm, outputs

    This is the function that will run on the hosting service
    like the one I am using `Render`
    '''
    ### Backend Initialization
    backend = Flask(__name__)
    CORS(backend)
    backend.register_blueprint(main_routes)

    ### Start other input fetching as threads
    #TODO:

    return backend



