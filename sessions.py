'''
Abstract class of sessions
This script defines the "variables" in the CSP framework which is time 'sessions' of different types and need different constraints and has specific time domains
'''
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeAlias
from datetime import datetime, timedelta

class SessionDescriptor(ABC):
    """
    Abstract base class for session metadata (e.g., name, type).
    """
    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

class Session:
    """
    Represents a schedulable session with duration and overlap rules.
    Durations are stored and manipulated as `timedelta` objects.
    """
    def __init__(
         self, 
         session_descriptor: SessionDescriptor, 
         base_duration: timedelta, 
         domain_values: list[datetime],
         allowed_to_overlap_session: Optional[List["Session"]] = None
    ):
        self.session_descriptor = session_descriptor
        self.base_duration = base_duration
        self.domain_values = domain_values
        self.allowed_to_overlap_session = allowed_to_overlap_session or []
        self.overlapped_sessions: list[Session] = []
        allowed_to_overlap_session: list[Session] = []

    def add_overlap(self, overlapped_session: Session) -> None:
        """
        Registers an allowed overlapping session.
        """
        self.overlapped_sessions.append(overlapped_session)

    def reset_overlap(self) -> None:
        """
        Clears all tracked overlaps.
        """
        self.overlapped_sessions.clear()

    @property
    def duration(self) -> timedelta:
        """
        Total duration (base + overlapped sessions).
        """
        duration = self.base_duration
        for overlapped_session in self.overlapped_sessions:
            duration += overlapped_session.duration

        return duration


        # return self.base_duration + sum(
        #     session.duration for session in self.overlapped_sessions
        # )

    def __repr__(self) -> str:
        return f"Session(name={self.session_descriptor.name}, duration={self.duration})"

    def __str__(self) -> str:
        return (
            f"{self.session_descriptor.name}\n"
            f"Duration: {self.duration}\n"
            f"Available slots: {len(self.domain_values)}"
        )

class SessionGroup(ABC):
    """
    Abstract base class for a group of related sessions.
    """
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
        
