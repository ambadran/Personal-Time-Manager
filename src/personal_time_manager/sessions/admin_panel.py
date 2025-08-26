'''
This session module defines the CSP variables and domains of personal persistent times that is not defined in any of apple / google calenders.
Example is work time, my sleep time, Gym times and more
'''
from datetime import datetime, timedelta, time
from enum import Enum, auto
from pydantic import BaseModel
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor, SessionPriority
from personal_time_manager.database.db_handler import DatabaseHandler
from psycopg2.extras import RealDictRow

class WorkType(Enum):
    MainJob = auto()
    Freelance = auto()
    MainJob_Freelance = auto()
    tuition = auto()

class GymWorkout(Enum):
    PUSH = auto()
    PULL = auto()
    LEG = auto()

class SleepType(Enum):
    NIGHT = auto()
    NAP = auto()

class MealType(Enum):
    BREAKFAST = auto()
    SNACK = auto()
    LUNCH = auto()
    DINNER = auto()

class Gym(BaseModel, SessionDescriptor):
    workout: GymWorkout
    duration_range: tuple[timedelta, timedelta]

    @property
    def name(self) -> str:
        return f"<{self.workout.name} Gym Session>"

    def __repr__(self) -> str:
        return f"Gym(workout={self.workout.name})"

    def __str__(self) -> str:
        return f"Gym(workout={self.workout.name}, duration={self.duration_range})"

class Sleep(BaseModel, SessionDescriptor):
    sleep_type: SleepType
    duration_range: tuple[timedelta, timedelta]

    @property
    def name(self) -> str:
        return f"<{self.sleep_type.name} Sleep Session>"

    def __repr__(self) -> str:
        return f"Sleep(sleep_type={self.sleep_type.name})"

    def __str__(self) -> str:
        return f"Sleep(sleep_type={self.sleep_type.name})"


class Work(BaseModel, SessionDescriptor):
    work_type: WorkType
    duration_range: tuple[timedelta, timedelta]

    @property
    def name(self) -> str:
        return f"<{self.work_type.name} Work Session>"

    def __repr__(self) -> str:
        return f"Work(work_type={self.work_type.name})"

    def __str__(self) -> str:
        return f"Work(work_type={self.work_type.name})"

class Meal(BaseModel, SessionDescriptor):
    meal_type: MealType

    @property
    def name(self) -> str:
        return f"<{self.meal_type.name} Meal Session>"

    def __repr__(self) -> str:
        return f"Meal(meal_type={self.meal_type.name})"

    def __str__(self) -> str:
        return f"Meal(meal_type={self.meal_type.name})"

class FixedActivities(SessionGroup):
    '''
    This class fetches all the values of the fixed activities from database and parses the data
    Then Generates list of Session variables with dictionary of domain values
    '''
    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        #TODO:
        self._csp_variables = []
        
    @property
    def csp_variables(self) -> list[Session]:
        return self._csp_variables

    @property
    def csp_domains(self) -> dict[Session: list[datetime]]:
        return {session: session.domain_values for session in self.csp_variables}

