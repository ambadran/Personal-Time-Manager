'''
Abstract class of sessions
This script defines:
    - Session -> The CSP Variable Type
    - SessionDescriptor -> to add more custom information for different types of Activities (Sessions)
    - SessionGroup -> This is the class the is required to return the CSP Variable list and CSP Domain Dictionary.
'''
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime, timedelta
from personal_time_manager.database.db_handler import DatabaseHandler
from personal_time_manager.database.db_handler2 import DatabaseHandler #TODO: remove the 2 when db_handler is finished

class AllowedTimes:
    '''
    A list of allowed times representaed as a list of (start, end).
    '''
    def __init__(self, allowed_times: list[tuple[datetime, datetime]]):
        ''' Constructor '''
        if not isinstance(allowed_times, list):
            raise TypeError("allowed_times must be a list of tuples.")
        for interval in allowed_times:
            if not (isinstance(interval, tuple) and len(interval) == 2 and
                    isinstance(interval[0], datetime) and isinstance(interval[1], datetime)):
                raise ValueError("Each item in allowed_times must be a tuple of two datetime objects.")
        self.intervals = allowed_times

    def __contains__(self, other: Union[datetime, SessionTime, AllowedTimes]) -> bool:
        """
        Checks if a datetime, SessionTime, or another AllowedTimes object
        overlaps with any of the intervals in this instance.
        """
        # Case 1: other is a single point in time (datetime)
        if isinstance(other, datetime):
            for start, end in self.intervals:
                if start <= other < end:
                    return True
            return False

        # Case 2: other is a time duration (SessionTime)
        # This now correctly checks for any overlap, not just full containment.
        elif 'SessionTime' in globals() and isinstance(other, SessionTime):
            for self_start, self_end in self.intervals:
                # Standard interval overlap condition
                if self_start < other.end_time and other.start_time < self_end:
                    return True
            return False

        # Case 3: other is another set of intervals (AllowedTimes)
        elif isinstance(other, AllowedTimes):
            for self_start, self_end in self.intervals:
                for other_start, other_end in other.intervals:
                    # Check for overlap between any pair of intervals
                    if self_start < other_end and other_start < self_end:
                        return True # Found an overlap, no need to check further
            return False # No overlap found after checking all combinations

        # Case 4: Raise an error for any other unsupported datatype
        else:
            raise ValueError(
                f"Unsupported type for 'in' operator: {type(other).__name__}. "
                "Allowed types are datetime, SessionTime, and AllowedTimes."
            )

class SessionDescriptor(ABC):
    """
    Abstract base class for session metadata (e.g., name, type).
    This is made so that the Main Session class can accomodate any type or idea of sessions. 
    The different types of sessions will need different attributes to describe and process them on their own.
    """
    def get_allowed_to_overlap_types(self) -> list[str]:
        """
        Mock implementation. In a real scenario, this would fetch from a database.
        Returns a list of class names (strings) that are allowed to overlap this type.
        """
        # MOCK DATA: Simulating a JSON fetch from a database
        overlap_rules = {
            'Prayer': [],
            'Tuition': ['Prayer'],
            'Sleep': ['Prayer'],
            'WorkMeeting': ['Prayer'],
            'Gym': ['Prayer'] # Example: Gym can be interrupted by Prayer
        }
        return overlap_rules.get(self.__class__.__name__, [])

    @property
    @abstractmethod
    def name(self) -> str:
        pass

class Session(BaseModel):
    """
    !!! This is the CSP variable type !!!

    Represents session description and overlap rules.
    """
    session_descriptor: SessionDescriptor
    allowed_times: AllowedTimes
    min_duration: timedelta
    max_duration: timedelta
    allowed_to_overlap_types: list[str] = []
    allowed_to_overlap: list[Session] = []
    #TODO: do some sort of check as must run self.get_allowed_to_overlap with all sessions before we can define domain

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self.allowed_to_overlap_types = self.session_descriptor.get_allowed_to_overlap_types()

    def get_allowed_to_overlap(self, csp_variables: list[Session]) -> None:
        '''
        This Method runs after all CSP variables are defined then they are passed as argument and filtered with type

        IMP: However, in the case I want to fine tune for specific Session objects, I can just inherit this function, get its return and tweak it however I want :D
        '''
        self.allowed_to_overlap = []
        for session in csp_variables:
            if type(session.session_descriptor) in self.allowed_to_overlap_type:
                self.allowed_to_overlap.append(session)

    def __hash__(self):
        return id(self)

    def __repr__(self) -> str:
        return f"Session(name={self.session_descriptor.name})"

class SessionTime:
    '''
    !!! This is the CSP Domain type !!!

    Represents a specific time slot with 
    - Start time
    - End time
    # - Base Duration (without overlapped sessions)
    # - list of allowed to overlap SessionTime(s)
    '''
    DEFAULT_STEP_MINUTE = 1
    def __init__(self,
                 start_time: datetime,
                 end_time: datetime):
                 # end_time: Optional[datetime]=None,
                 # base_duration: Optional[timedelta]=None,
                 # overlapping_sessions: dict[Session: SessionTime] = {}):
        '''
        Must give start_time as datetime,
        Then give either end_time as datetime or duration as timedelta
        Or if given both end_time and duration , then they must match relative to start_time
        '''
        # Type checking..
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise TypeError("start_time and end_time must be datetime objects.")
        if start_time >= end_time:
            raise ValueError("start_time must be before end_time.")
        self.start_time = start_time
        self.end_time = end_time

    @property
    def duration(self) -> timedelta:
        """ Returns the duration of this specific time slot. """
        return self.end_time - self.start_time

    def overlaps(self, other: SessionTime) -> bool:
        """ Returns True if another SessionTime overlaps with this one. """
        return self.start_time < other.end_time and self.end_time > other.start_time

    def contains(self, other: SessionTime) -> bool:
        """ Returns True if another SessionTime is fully contained within this one. """
        return self.start_time <= other.start_time and self.end_time >= other.end_time

    def __repr__(self) -> str:
        return f"SessionTime({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

    def __hash__(self):
        return hash((self.start_time, self.end_time))

    @classmethod
    def from_raw_data(cls,
                      session: Session,
                      step_minutes: int = DEFAULT_STEP_MINUTE) -> list[SessionTime]:
        """
        Generates an exhaustive list of all possible SessionTime slots.
        """
        domain: list[SessionTime] = []
        # The step for generating potential start times
        start_time_step = timedelta(minutes=step_minutes)

        for start_interval, end_interval in session.allowed_times.intervals:
            current_start = start_interval
            # Loop 1: Generate all possible start times based on the step
            while current_start < end_interval:
                # Convert durations to simple minute integers for the loop
                min_dur_mins = int(session.min_duration.total_seconds() / 60)
                max_dur_mins = int(session.max_duration.total_seconds() / 60)
                
                # Loop 2: For each start time, check every possible duration (1-minute resolution)
                for duration_min in range(min_dur_mins, max_dur_mins + 1):
                    current_duration = timedelta(minutes=duration_min)
                    end_time = current_start + current_duration

                    # Boundary Check: Ensure the generated slot fits within the allowed interval
                    if end_time <= end_interval:
                        domain.append(cls(start_time=current_start, end_time=end_time))
                
                current_start += start_time_step
        
        return list(dict.fromkeys(domain)) # Return unique values

class SessionGroup(ABC):
    """
    Abstract base class for a group of related sessions.

    This is the class that is supposed to generate:
    - list[Session] -> CSP Variables list
    - dict[Session: list[SessionTime]] -> CSP Domain Dictionary

    for a specific group of sessions
    """
    WEEK_START_DAY = 5 # saturday
    def __init__(
            self, 
            week_start_date: datetime,
            db_handler: DatabaseHandler):
        ''' Constructor '''
        if week_start_date.weekday() != self.WEEK_START_DAY:
            raise ValueError("week_start_date must be a Saturday!")
        self.week_start_date: datetime = week_start_date
        self.db_handler = db_handler

    @abstractmethod
    def get_allowed_times(self, session_descriptor: SessionDescriptor) -> AllowedTimes:
        ...

    @abstractmethod
    def get_min_duration(self, session_descriptor: SessionDescriptor) -> timedelta:
        ...

    @abstractmethod
    def get_max_duration(self, session_descriptor: SessionDescriptor) -> timedelta:
        ...

    @abstractmethod
    def csp_variables(self) -> list[Session]:
        ''' Generates list of CSP `Session` variables '''
        pass

       
