'''
This file defines all the `Constraint` classes the CSP framework needs to take into account.

Constraints:
    - NoTimeOverlapConstraint(Constraint)
'''
from datetime import datetime, timedelta
from personal_time_manager.csp.csp import Constraint, CSP
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.base_session import Session, SessionTime
from typing import Optional

#temp
from pprint import pprint

class NoTimeOverlapConstraint(Constraint):
    '''
    Constraint class to prevent time slots from overlapping

    There is an Argument to allow overlap for specific variables (for example prayer in middle of lesson)

    Testing for overlap of specific self.session with the other assignment dictionary
    1- update overlapped_sessions every run, to account for possible change in previous trial
    2- Tests:
        1- any of the others start after self.session starts
        AND
        2- any of the others starts before self.session ends
        AND
        3- not in the allowed_to_overlap_session
        AND
        4- not within tolerance of next session starting time

    Session Starts -> datetime in assignment dictionary
    Session Ends -> datetime in assignment dictionary + session.duration
    '''
    def __init__(self, variable: Session, tolerance: timedelta):
        '''
        :param variable: the `Session` variable that this Constraint applies to
        :param tolerance: `timedelta` variable of the amount of time where even if an exception session starts after the start but within specific amount of minutes <tolerance> will be rejected (not satisfied)
        '''
        super().__init__([variable])
        self.session = variable
        self.tolerance = tolerance

    def satisfied(self, assignment: dict[Session: SessionTime]) -> bool:
        '''
        Testing for overlap of specific self.session with the other assignment dictionary
        1- update overlapped_sessions every run, to account for possible change in previous trial
        2- Tests:
            1- any of the others start after self.session starts
            AND
            2- any of the others starts before self.session ends
            AND
            3- not in the allowed_to_overlap_session
            AND
            4- not within tolerance of next session starting time

        Session Starts -> datetime in assignment dictionary
        Session Ends -> datetime in assignment dictionary + session.duration
        '''
        if self.session not in assignment.keys():
            # Skip entirely if this session is not yet assigned
            return True

        ### Step 1:
        #TODO: re-implement using new CSP implementation
        #TODO: the main challenge is to incorporate overlapped_sessions features again with new domain type definition
        # Update overlapped_sessions list and duration if an allowed_to_overlap_session is present
        # self.session.reset_overlap()
        # for other_session, other_session_start_time in assignment.items():
        #     # skip test if it's the session to be tested
        #     if other_session == self.session:
        #         continue

        #     # test time overlap and if allowed overlap session and tolerance
        #     if (
        #         (((other_session_start_time >= assignment[self.session]) and \
        #         (other_session_start_time <= (assignment[self.session] + self.session.duration))) \
        #             or \
        #         ((assignment[self.session] >= other_session_start_time) and \
        #         (assignment[self.session] <= (other_session_start_time + other_session.duration))))
        #         and \
        #         (other_session in self.session.allowed_to_overlap_session) \
        #         and \
        #         ((other_session_start_time - assignment[self.session]) > self.tolerance)):
        #             self.session.add_overlap(other_session)

        ### Step 2:
        # Actual test
        #TODO: re-implement using new CSP implementation
        # test_var = False
        # for other_session, other_session_start_time in assignment.items():
        #     # skip test if it's the session to be tested
        #     if other_session == self.session:
        #         continue

        #     if other_session in self.session.overlapped_sessions:
        #         # skip if this is allowed overlapping
        #         continue


        #     if (
        #         ((other_session_start_time >= assignment[self.session]) and \
        #         (other_session_start_time <= (assignment[self.session] + self.session.duration))) \
        #         or \
        #         ((assignment[self.session] >= other_session_start_time) and \
        #         (assignment[self.session] <= (other_session_start_time + other_session.duration)))
        #         ):
        #         return False

        return True

class NoSameDayTuition(Constraint):
    '''
    Constraint class to prevent having the same tuition and 
    '''
