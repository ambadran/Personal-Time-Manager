'''

'''
from datetime import datetime, timedelta
from csp import Constraint, CSP
from prayers import Prayers
from sessions import Session
from typing import Optional

class NoTimeOverlapConstraint(Constraint):
    '''
    Constraint class to prevent time slots from overlapping
    Argument to allow overlap for specific variables (for example prayer in middle of lesson)


    Overlap is defined as following:
    session A overlap session B if session A starts after session B and before the duration needed for session B
    '''
    def __init__(self, variable: Session, tolerance: timedelta):
        '''
        Variable of the session that the overlap prevention constraint applies to
        Takes into account the .
        param tolerance: an integer of the amount of minutes where even if an exception session starts after the start but within specific amount of minutes <tolerance> will be rejected (not satisfied)
        '''
        super().__init__([variable])
        self.session = variable
        self.tolerance = tolerance

    def satisfied(self, assignment: dict[Session: datetime]) -> bool:
        '''
        actual testing for overlap of specific self.session with the other assignment dictionary
        1- update overlapped_sessions every run, to account for possible change in previous trial
        2- test 
            1- any of the others start after self.session starts
            AND
            2- any of the others starts before self.session ends
            AND
            3- not in the allowed_to_overlap_session
            AND
            4- not within tolerance of next session starting time
        '''
        if self.session not in assignment.keys():
            # Skip entirely if this session is not yet assigned
            return True


        ### Step 1:
        # Update overlapped_sessions list and duration if an allowed_to_overlap_session is present
        self.session.reset_overlap()
        for other_session, other_session_start_time in assignment.items():
            # skip test if it's the session to be tested
            if other_session == self.session:
                continue

            # test time overlap and if allowed overlap session and tolerance
            if ((other_session_start_time > assignment[self.session] and \
                other_session_start_time < (assignment[self.session] + self.session.duration)) and \
                (other_session in self.session.allowed_to_overlap_session) and \
                ((other_session_start_time - assignment[self.session]) > self.tolerance)):
                    self.session.add_overlap(other_session)

        ### Step 2:
        # Actual test
        for other_session, other_session_start_time in assignment.items():
            # skip test if it's the session to be tested
            if other_session == self.session:
                continue

            if other_session in self.session.overlapped_sessions:
                # skip if this is allowed overlapping
                continue

            if (other_session_start_time > assignment[self.session] and \
                other_session_start_time < (assignment[self.session] + self.session.duration)):
                return False

        return True

