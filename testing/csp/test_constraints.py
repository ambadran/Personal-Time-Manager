'''
Testing the constraints classes
'''
from datetime import datetime, timedelta
import pytest
from personal_time_manager.csp.csp import CSP, Constraint
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.base_session import Session

def test_NoTimeOverlapConstraint(prayers: Prayers):
    '''
    Testing all possible scenarios the No over lap constraints could fail
    '''
    pass

