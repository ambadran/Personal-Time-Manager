'''
This Python file processes all things related to trigger mechanisms and returning the trigger source later
'''
import time
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional

from personal_time_manager.database.db_handler import DatabaseHandler
from personal_time_manager.common.config import START_OF_WEEK_DAY_INDEX, ALGORITHM_TRIGGER_DAY_INDEX

class TriggerSource(Enum):
    '''
    This holds all the possible Trigger sources for the CSP to re-run
    '''
    DATABASE = auto()
    GOOGLE_CALENDAR = auto()
    APPLE_CALENDAR = auto()
    WEEK_START = auto()

class Listener(ABC):
    """ Abstract base class for all trigger source listeners. """
    @abstractmethod
    def check_trigger(self) -> bool:
        """ Returns True if a trigger event has occurred. """
        pass

    @abstractmethod
    def get_source(self) -> str:
        """ Returns a string representation of the trigger source. """
        pass

class DatabaseListener(Listener):
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler
        self._payload: Optional[str] = None

    def check_trigger(self) -> bool:
        self._payload = self.db_handler.listener_check()
        return self._payload is not None

    def get_source(self) -> str:
        return f"db_notify:{self._payload}"

class WeekStartListener(Listener):
    def __init__(self):
        self._last_run_week_start: Optional[datetime] = None

    def check_trigger(self) -> bool:
        """
        Triggers once at the beginning of the trigger day (e.g., Friday 12:00 AM).
        """
        today = datetime.now()
        current_target_week_start: datetime
        
        # If today is the trigger day or later, plan for the upcoming week
        if today.weekday() >= ALGORITHM_TRIGGER_DAY_INDEX:
            days_until_saturday = (START_OF_WEEK_DAY_INDEX - today.weekday() - 1 + 7) % 7
            current_target_week_start = today + timedelta(days=days_until_saturday + 1)
        else: # Otherwise, plan for the current week
            days_since_saturday = (today.weekday() - START_OF_WEEK_DAY_INDEX + 7) % 7
            current_target_week_start = today - timedelta(days=days_since_saturday)
        
        target_date = current_target_week_start.date()

        # The trigger condition: Has the target week changed since our last run?
        if target_date != self._last_planned_week_start:
            self._last_planned_week_start = target_date
            return True
            
        return False

    def get_source(self) -> str:
        return TriggerSource.WEEK_START.name

class GoogleCalendarListener(Listener):
    #TODO:
    ...

class Triggers:
    """
    Manages and checks all trigger sources for the CSP solver.
    """
    def __init__(self, db_handler: DatabaseHandler):
        self.source: Optional[str] = None
        # The list of all listener objects. Easy to add new ones here!
        self._listeners: List[Listener] = [
            DatabaseListener(db_handler),
            WeekStartListener(),
            # GoogleCalendarListener(), # Future
        ]

    def any(self) -> bool:
        """
        Checks all trigger sources and returns True if any are active.
        Stores the source of the first trigger found.
        """
        for listener in self._listeners:
            if listener.check_trigger():
                self.source = listener.get_source()
                return True
        return False
