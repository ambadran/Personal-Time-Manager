'''
This file defines all the `Constraint` classes the CSP framework needs to take into account.

Constraints:
    - NoTimeOverlapConstraint(Constraint)
'''
from itertools import combinations
from datetime import datetime, timedelta
from personal_time_manager.csp.csp import Constraint, CSP
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.base_session import Session, SessionTime
from typing import Optional

#temp
from pprint import pprint

class NoTimeOverlapConstraint(Constraint):
    """
    Constraint to prevent illegal time slot overlaps.
    An overlap is "legal" if a session is fully contained within another session
    that explicitly allows it.
    """
    def __init__(self, variables: list[Session]):
        super().__init__(variables)

    def satisfied(self, assignment: dict[Session, SessionTime]) -> bool:
        # Step 1: Check for any fundamentally illegal overlaps.
        # Using combinations ensures we check each pair only once.
        assigned_pairs = combinations(assignment.items(), 2)

        for (session1, time1), (session2, time2) in assigned_pairs:
            if time1.overlaps(time2):
                # An overlap exists. Check if it's a legal, contained one.
                # Case A: Session2 is legally inside Session1
                is_legal_A = (session2 in session1.allowed_to_overlap and time1.contains(time2))
                # Case B: Session1 is legally inside Session2
                is_legal_B = (session1 in session2.allowed_to_overlap and time2.contains(time1))

                if not is_legal_A and not is_legal_B:
                    return False # This is a strictly illegal overlap. Fail immediately.

        # Step 2: If all overlaps are geometrically legal, calculate work times.
        # This part only runs if the assignment is potentially valid.
        work_time_cache = {s: t.duration for s, t in assignment.items()}

        for host_session, host_time in assignment.items():
            for interrupter_session, interrupter_time in assignment.items():
                if host_session == interrupter_session:
                    continue
                
                # If it's a legal interruption, subtract the duration.
                if (interrupter_session in host_session.allowed_to_overlap and 
                        host_time.contains(interrupter_time)):
                    work_time_cache[host_session] -= interrupter_time.duration

        # Step 3: Verify that all sessions meet their minimum work time.
        for session, work_time in work_time_cache.items():
            if work_time < session.min_duration:
                return False # Violation: Did not meet minimum work time.

        return True # All checks passed.

#     def satisfied(self, assignment: dict[Session, SessionTime]) -> bool:
#             """
#             Checks all pairs for illegal overlaps or for legal overlaps
#             that violate the minimum duration requirement.
#             """
#             # A cache to store the calculated work time for each session
#             work_time_cache = {session: time.duration for session, time in assignment.items()}

#             # First, find all legal interruptions and subtract their duration
#             for host_session, host_time in assignment.items():
#                 for interrupter_session, interrupter_time in assignment.items():
#                     if host_session == interrupter_session:
#                         continue

#                     # Check for a legal, contained overlap
#                     if (interrupter_session in host_session.allowed_to_overlap and
#                             host_time.contains(interrupter_time)):
                        
#                         # Subtract the interrupter's duration from the host's work time
#                         work_time_cache[host_session] -= interrupter_time.duration

#             # Now, perform the two final checks
#             for session1, time1 in assignment.items():
#                 # 1. Check if the final work time meets the minimum duration
#                 if work_time_cache[session1] < session1.min_duration:
#                     return False # Violation: Work time is less than required minimum

#                 # 2. Check for any remaining illegal overlaps
#                 for session2, time2 in assignment.items():
#                     if session1 == session2:
#                         continue
                    
#                     # If they overlap and it's NOT a legal containment, it's a violation
#                     if time1.overlaps(time2):
#                         is_legal_overlap = (session2 in session1.allowed_to_overlap and time1.contains(time2))
#                         if not is_legal_overlap:
#                             return False # Violation: Illegal overlap found
            
#             return True # All checks passed

class NoSameDayTuition(Constraint):
    '''
    Constraint to prevent sessions of the same student
    from being scheduled on the same day.
    '''
    def __init__(self, same_tuition_sessions: list[Session]):
        """
        Takes a list of sessions that should not occur on the same day.
        """
        super().__init__(same_tuition_sessions)
        self.tuition_sessions = same_tuition_sessions

    def satisfied(self, assignment: dict[Session, SessionTime]) -> bool:
        """
        Checks that any two sessions from its list that are in the assignment
        do not fall on the same calendar day.
        """
        ...
