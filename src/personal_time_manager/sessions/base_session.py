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

class AllowedTimes:
    '''
    A list of allowed times representaed as a list of (start, end).
    '''
    def __init__(self, allowed_times: list[tuple[datetime, datetime]]):
        ''' Constructor '''
        wrong_datatype = False
        if allowed_times not in [list, tuple]:
            wrong_datatype = True
        for allowed_time in allowed_times:
            if type(allowed_time) not in [list, tuple] or \
               type(allowed_times[0]) != datetime or \
               type(allowed_times[1]) != datetime:
                wrong_datatype = True

        if wrong_datatype:
            raise ValueError("Parameter allowed_times must be list or tuple of two datetime pairs in list or tuple")

    def __contains__(self, other: Union[datetime, "AllowedTimes"]):
        ''' checks if another AllowedTimes or datetime is within this time '''
        #TODO:
        ...

class SessionDescriptor(ABC):
    """
    Abstract base class for session metadata (e.g., name, type).
    This is made so that the Main Session class can accomodate any type or idea of sessions. 
    The different types of sessions will need different attributes to describe and process them on their own.
    """
    def __init__(self):
        #TODO: make sure all the SessionDescriptor obj run super().__init__()
        self.allowed_to_overlap_types = self.get_allowed_to_overlap_types()

    def get_allowed_to_overlap_types(self) -> list[SessionDescriptor]:
        '''
        normally allowed_to_overlap list is all of a SessionDescriptor Sessions compared allowed in another SessionDescriptor Sessions. 

        This method gets the list of SessionDescriptor Types that a specific SessionDescriptor Type treats as allowed_to_overlap. So any Session with session_descriptor of this type should be inside the allowed_to_overlap list of `Session`s in the Session attribute

        Example Json data:
        {'Prayer': [],
        'Tuition': ['Prayer'],
        'Sleep': ['Prayer', 'Tuition', 'WorkMeetings'],
        'WorkMeetings': ['Prayer', 'Tuition']}

        all of those strings are the __name__ of the respective classes defined in their own files to handle their types
        '''
        #TODO: connect to db and get json return of allowed_to_overlap table
        #TODO: parse the json data and return the one with key same as __name__ of this class
        pass

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
         allowed_times: AllowedTimes
         min_duration: timedelta
         max_duration: timedelta
    ):
        if type(session_descriptor) != SessionDescriptor:
            raise ValueError("<session_descriptor> must be <SessionDescriptor> type")
        elif type(allowed_times) != AllowedTimes:
            raise ValueError("<> must be <> type")
        elif type(min_duration) != timedelta:
            raise ValueError("<> must be <> type")
        elif type(max_duration) != timedelta:
            raise ValueError("<> must be <> type")
        elif type(allowed_to_overlap) not in [list, tuple, NoneType]:
            raise ValueError("<> must be <> type")

        self.session_descriptor = session_descriptor
        self.allowed_times = allowed_times
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.allowed_to_overlap_types = session_descriptor.allowed_to_overlap_types
        self.allowed_to_overlap = None  # must run self.get_allowed_to_overlap with all sessions before we can define domain

    def get_allowed_to_overlap(self, csp_variables: list[Session]) -> None:
        '''
        This Method runs after all CSP variables are defined then they are passed as argument and filtered with type

        IMP: However, in the case I want to fine tune for specific Session objects, I can just inherit this function, get its return and tweak it however I want :D
        '''
        self.allowed_to_overlap = []
        for session in csp_variables:
            if type(session.session_descriptor) in self.allowed_to_overlap_type:
                self.allowed_to_overlap.append(session)

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
    - Base Duration (without overlapped sessions)
    - list of allowed to overlap SessionTime(s)
    '''
    DEFAULT_STEP_MINUTE = 1
    def __init__(self,
                 start_time: datetime,
                 end_time: Optional[datetime]=None,
                 base_duration: Optional[timedelta]=None,
                 overlapping_sessions: dict[Session: SessionTime] = {}):
        '''
        Must give start_time as datetime,
        Then give either end_time as datetime or duration as timedelta
        Or if given both end_time and duration , then they must match relative to start_time
        '''
        # Type checking..
        if type(start_time) != datetime:
            raise TypeError("type of start_time argument must be datetime")
        else:
            self.start_time = start_time
        if end_time and base_duration:
            if type(end_time) != datetime:
                raise TypeError("type of end_time argument must be datetime")
            elif type(base_duration) != timedelta:
                raise TypeError("type of base_duration argument must be datetime")
            elif (end_time-start_time) != base_duration:
                raise ValueError("end_time given doesn't match base_duration value relative to given start_time")
            else:
                self.end_time = end_time
                self.base_duration = base_duration
        elif end_time:
            if type(end_time) != datetime:
                raise TypeError("type of end_time argument must be datetime")
            self.end_time = end_time
            self.base_duration = end_time - start_time
        elif base_duration:
            if type(base_duration) != timedelta:
                raise TypeError("type of base_duration argument must be datetime")
            self.base_duration = base_duration
            self.end_time = start_time + base_duration
        else:
            raise ValueError("Must define either end_time or base_duration argument")

        self.overlapping_sessions = overlapping_sessions

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

    @property
    def duration(self) -> timedelta:
        '''
        returns the actual duration of this SessionTime including the overlapping sessions
        '''
        duration = self.base_duration
        for session_time in self.overlapping_sessions.values():
            duration += session_time.duration
        return duration

    @classmethod
    def from_raw_data(self, 
                  allowed_intervals: AllowedTimes,
                  min_duration: timedelta,
                  max_duration: timedelta,
                  allowed_to_overlap: Optional[list[Session]] = {},
                  step_minutes: int = DEFAULT_STEP_MINUTE) -> list[SessionTime]:
        '''
        This function is extremely important, it's what returns the domain list
        The domain list is the list of possible values that could be assigned to a specific Session CSP variable

        allowed_intervals: list of list of start & end times
        min_duration: 
        max_duration:
        allowed_to_overlap: list of Sessions to check overlapping
        step_minutes: the resolution of the output
        '''
        TODO:
        for main_sess in csp_variables:
            for overlapping_sess in csp_var.allowed_to_overlap: # a recursive function must be implemented to cover .allowed_to_overlap inside the overlapping_sess and make sure its duration is updated and so on..

                # Testing if any allowed_times of the main_sess and overlapping_sess actually overlap in time
                if main_sess.allowed_times in overlapping_sess.allowed_times: #TODO: haven't fully developed AllowedTimes or its __contains__

                            ### There are four possibilities when a session possible domain time overlaps an allowed_to_overlap session.
                            # Possibility 1: the allowed_to_overlap session starts before main session end and ends after main session ends
                            if possible_overlapping_domain.start_time > possible_main_domain.start_time \
                                    and possible_overlapping_domain.start_time < possible_main_domain.end_time \
                                    and possible_overlapping_domain.end_time > possible_main_domain.start_time \
                                    and possible_overlapping_domain.end_time > possible_main_domain.end_time:
                                # add a new attribute that saves the overlapping session and the allowed_times object periods (already recursed with any inner overlapping session with same four rules here.) within the main sess allowed_times. this helps when we actually create the domain values
                                #TODO: main session doesn't change start time and just pushes the end time the duration of overlapping session
                                #TODO: check if added time is within allowed_times of main session
                                #TODO: add overlapping session as key and its SessionTime as value in the main ovoerlapping SessionTime.overlapping dictionary
                                pass

                            # Possibility 2: the allowed_to_overlap session starts before main session end and ends after main session ends
                            elif possible_overlapping_domain.start_time < possible_main_domain.start_time \
                                    and possible_overlapping_domain.start_time < possible_main_domain.end_time \
                                    and possible_overlapping_domain.end_time > possible_main_domain.start_time \
                                    and possible_overlapping_domain.end_time < possible_main_domain.end_time:
                                # I don't think this scenario should be covered as overlapping. The CSP logic should cover this
                                # the wanted here is the main gets pushed after the overlapping session which will happen if this time exists in the main sessions domain anyway.
                                pass

                            # Possibility 3: the allowed_to_overlap session whole duration is within the main session's duration
                            elif possible_overlapping_domain.start_time < possible_main_domain.start_time \
                                    and possible_overlapping_domain.start_time < possible_main_domain.end_time \
                                    and possible_overlapping_domain.end_time > possible_main_domain.start_time \
                                    and possible_overlapping_domain.end_time < possible_main_domain.end_time:
                                #TODO: main session doesn'
    t change start time and just pushes the end time the duration of overlapping session
                                #TODO: check if added time is within allowed_times of main session
                                #TODO: add overlapping session as key and its SessionTime as value in the main ovoerlapping SessionTime.overlapping dictionary
                                pass



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
            higher_priority_session_group: SessionGroup):
        ''' Constructor '''
        if week_start_date.weekday() != self.WEEK_START_DAY:
            raise ValueError("week_start_date must be a Saturday!")
        self.week_start_date: datetime = week_start_date

    @abstractmethod
    def csp_variables(self) -> list[Session]:
        ''' Generates list of CSP `Session` variables '''
        pass

    @abstractmethod
    def csp_domains(self) -> dict[Session: list[SessionTime]]:
        ''' 
        Generates dictionary key CSP `Session` variable 
        And Value list of possible domain `SessionTime` values 

        Here is where the magic of pre-processing happens
        Here is where higher_priority_session_group Session are checked
        '''
        pass
        
