'''
Testing Tuition session management
'''
from datetime import datetime
import pytest
from personal_time_manager.sessions.tuitions import Tuitions
from psycopg2.extras import RealDictRow
from pprint import pprint

def test_tuition_db_access():
    '''
    Tests that connection to db was successful and it did return RealDictRow
    '''
    test_db_handler = Tuitions.__new__(Tuitions)
    raw_data = test_db_handler.get_latest_db_data()
    assert len(raw_data) > 0  # make sure there is data to test

    # test the data structure to be as expected so that the Tuitions processing does what it does to expected data structure
    #TODO
    assert type(raw_data[0]) == RealDictRow


def test_tuition_class(tuitions: Tuitions):
    '''
    Tests if the Tuition(SessionGroup) class will run properly:
        - No Errors
        - generate correct CSP Variables list
        - generate correct CSP Domain Dictionary

    '''
    pprint(tuitions.raw_data)
    print(type(tuitions.raw_data))
    print(type(tuitions.raw_data[0]))



    for session in tuitions.csp_variables:
        print(f"{session.session_descriptor.name}: {session.domain_values[0].strftime('%Y-%m-%d %H:%M')}")





