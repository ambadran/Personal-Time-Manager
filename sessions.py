'''
Abstract class of sessions
This script defines the "variables" in the CSP framework which is time 'sessions' of different types and need different constraints and has specific time domains
'''
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeAlias
from datetime import datetime, timedelta

class SessionDescriptor(ABC):
    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

class Session:
    '''
    This is the Session Abstract Class
    '''
    def __init__(self, session_descriptor: SessionDescriptor, 
                 base_duration: timedelta, 
                 domain_values: list[datetime],
                 allowed_to_overlap_session: list[Session] = []):
        '''

        '''
        self.session_descriptor = session_descriptor
        self.base_duration = base_duration
        self.domain_values = domain_values
        self.allowed_to_overlap_session = allowed_to_overlap_session
        self.overlapped_sessions = []

    def add_overlap(self, overlapped_session: Session) -> None:
        '''
        adds the overlapped session and modifies duration accordingly
        '''
        self.overlapped_sessions.append(overlapped_session)

    def reset_overlap(self) -> None:
        '''
        resets overlap list
        '''
        self.overlapped_sessions = []

    @property
    def duration(self) -> timedelta:
        duration = self.base_duration
        for overlapped_session in self.overlapped_sessions:
            duration += overlapped_session.duration

        return duration

    def __repr__(self):
        return f"(Session Obj: {self.session_descriptor.name} for {self.duration})"


    def __str__(self):
        return f"{self.session_descriptor.name} for {self.duration}\n@ {self.domain_values}"

class SessionGroup(ABC):
    '''
    This is session group class
    '''
    WEEK_START_DAY = 5 # saturday
    def __init__(self, week_start_date: datetime):
        if week_start_date.weekday() != self.WEEK_START_DAY:
            raise ValueError("week_start_date must be a Saturday!")
        self.week_start_date: datetime = week_start_date

    @abstractmethod
    def csp_variables(self) -> list[Session]:
        pass

    @abstractmethod
    def csp_domains(self) -> dict[Session: list[datetime]]:
        pass
        
