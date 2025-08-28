'''
Abstract class of sessions
This script defines:
    - Session -> The CSP Variable Type
    - SessionDescriptor -> to add more custom information for different types of Activities (Sessions)
    - SessionGroup -> This is the class the is required to return the CSP Variable list and CSP Domain Dictionary.
'''
# from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from personal_time_manager.database.db_handler import DatabaseHandler

class SessionDescriptor(ABC):
    """
    Abstract base class for session metadata (e.g., name, type).
    This is made so that the Main Session class can accomodate any type or idea of sessions. 
    The different types of sessions will need different attributes to describe and process them on their own.

    The only shared attribute that has to be in all is 'name' (for now)
    """
    def __init__(self):
        #TODO: make sure ALL SessionDescriptor do super().__init__() !!!!!!
        self.priority = self.get_priority()

    def get_priority(self) -> int:
        '''
        # find priority from db
        # init db, get db priority json data, parse json, 
        class.__name__ of SessionDescriptor to int priority value
        '''
        #TODO:
        return 10

    @property
    @abstractmethod
    def name(self) -> str:
        pass

class Session(BaseModel):
    """
    !!! This is the CSP variable type !!!

    Represents session description and overlap rules.
    """
    def __init__(
         self, 
         session_descriptor: SessionDescriptor, 
         allowed_to_overlap_session: Optional[list[Session]] = None
    ):
        if type(session_descriptor) != SessionDescriptor:
            raise ValueError("<session_descriptor> must be <SessionDescriptor> type")
        # elif type() != :
        #     raise ValueError("<> must be <> type")

        self.session_descriptor = session_descriptor
        self.priority = session_descriptor.priority
        self.allowed_to_overlap_session = allowed_to_overlap_session or []
        self.overlapped_sessions: list[Session] = []


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

    def __repr__(self) -> str:
        return f"Session(name={self.session_descriptor.name}, priority={self.priority})"

    def __str__(self) -> str:
        return f"{self.session_descriptor.name}, Priority: {self.priority}"

class SessionTime:
    '''
    !!! This is the CSP Domain type !!!

    Represents a specific time slot with 
    - Start time
    - End time
    - Duration
    '''
    DEFAULT_STEP_MINUTE = 1
    def __init__(self,
                 start_time: datetime,
                 end_time: Optional[datetime]=None,
                 duration: Optional[timedelta]=None):
        '''
        Must give start_time as datetime,
        Then give either end_time as datetime or duration as timedelta
        Or if given both end_time and duration , then they must match relative to start_time
        '''
        if type(start_time) != datetime:
            raise TypeError("type of start_time argument must be datetime")
        else:
            self.start_time = start_time

        if end_time and duration:
            if type(end_time) != datetime:
                raise TypeError("type of end_time argument must be datetime")
            elif type(duration) != timedelta:
                raise TypeError("type of duration argument must be datetime")
            elif (end_time-start_time) != duration:
                raise ValueError("end_time given doesn't match duration value relative to given start_time")
            else:
                self.end_time = end_time
                self.duration = duration

        elif end_time:
            if type(end_time) != datetime:
                raise TypeError("type of end_time argument must be datetime")
            self.end_time = end_time
            self.duration = end_time - start_time

        elif duration:
            if type(duration) != timedelta:
                raise TypeError("type of duration argument must be datetime")
            self.duration = duration
            self.end_time = start_time + duration

        else:
            raise ValueError("Must define either end_time or duration argument")

    def __contains__(self, other: "SessionTime") -> bool:
        '''
        returns if another SessionTime overlaps this one
        '''
        if type(other) != SessionTime:
            raise TypeError("Can only do __contains__ with a variable with same SessionTime datatype")
        if (
            ((other.start_time >= self.start_time) and \
            (other.start_time <= self.end_time)) \
            or \
            ((self.start_time >= other.start_time) and \
            (self.start_time <= other.end_time))
            ):
            return False

        return True

    @classmethod
    def from_raw_data(self, 
                  allowed_intervals: list[list[datetime, datetime]], 
                  min_duration: timedelta,
                  max_duration: timedelta,
                  step_minutes: int = DEFAULT_STEP_MINUTE) -> list[SessionTime]:
        '''
        This function is extremely important, it's what returns the domain list
        The domain list is the list of possible values that could be assigned to a specific Session CSP variable

        allowed_intervals: list of list of start & end times
        min_duration: 
        max_duration:
        step_minutes: the resolution of the output
        '''
        domain: List[D] = []
        min_dur_td = timedelta(minutes=duration_range[0])
        max_dur_td = timedelta(minutes=duration_range[1])
        step_td = timedelta(minutes=step_minutes)
        
        # Use a dummy date to work with datetime objects, which makes timedelta arithmetic easier
        today = datetime.now().date()

        for interval_start, interval_end in allowed_intervals:
            current_time = datetime.combine(today, interval_start)
            interval_end_dt = datetime.combine(today, interval_end)
            
            # Iterate through all possible start times within the allowed interval
            while current_time < interval_end_dt:
                # Iterate through all possible durations
                duration = min_dur_td
                while duration <= max_dur_td:
                    end_time = current_time + duration
                    # If the activity fits within the interval, add it to the domain
                    if end_time <= interval_end_dt:
                        domain.append((current_time.time(), end_time.time()))
                    duration += step_td
                current_time += step_td
                
        return list(set(domain)) # Use set to remove duplicate slots

class SessionGroup(ABC):
    """
    Abstract base class for a group of related sessions.

    This is the class that is supposed to generate:
    - list[Session] -> CSP Variables list
    - dict[Session: list[datetime]] -> CSP Domain Dictionary

    for a specific group of sessions
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
    def csp_domains(self) -> dict[Session: list[SessionTime]]:
        pass
        
