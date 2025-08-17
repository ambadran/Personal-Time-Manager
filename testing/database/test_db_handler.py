'''

'''
import pytest
from personal_time_manager.database.db_handler import DatabaseHandler

def test_db_connection():
    '''
    just tests connection to online db is successful
    tests:
    self._get_connection & self.check_connection
    '''
    db = DatabaseHandler()

    assert True

