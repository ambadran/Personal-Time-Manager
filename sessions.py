'''
Abstract class of sessions
This script defines the "variables" in the CSP framework which is time 'sessions' of different types and need different constraints and has specific time domains
'''
from abc import ABC, abstractmethod

class Session(ABC):
    '''
    This is the Sesssion Abstract Class
    '''
    def __init__(self, name: str, base_duration: int, allowed_to_overlap_session: list[Session] = []):
        '''

        '''
        self.name = name
        self.base_duration = duration
        self.allowed_to_overlap_session = allowed_to_overlap_session
        self.overlapped_sessions = []

    def add_overlap(self, overlapped_session: Session):
        '''
        adds the overlapped session and modifies duration accordingly
        '''
        self.overlapped_sessions.append(overlapped_session)

    def reset_overlap(self):
        '''
        resets overlap list
        '''
        self.overlapped_sessions = []

    @property
    def duration(self):
        duration = self.base_duration
        for overlapped_session in self.overlapped_sessions:
            duration += overlapped_session.duration

        return duration

