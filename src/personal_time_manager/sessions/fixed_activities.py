'''
This session module defines the CSP variables and domains of personal persistent times that is not defined in any of apple / google calenders.
Example is work time, my sleep time, Gym times and more
'''
from datetime import datetime, timedelta, time
from enum import Enum, auto
from pydantic import BaseModel, ConfigDict
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor, AllowedTimes
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
    MEALPREP = auto()
    BREAKFAST = auto()
    SNACK = auto()
    LUNCH = auto()
    DINNER = auto()

class Gym(BaseModel, SessionDescriptor):
    type: GymWorkout
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: List[Dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Gym-{self.workout.name}"

class Sleep(BaseModel, SessionDescriptor):
    type: SleepType
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: List[Dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Sleep-{self.sleep_type.name}"

class Work(BaseModel, SessionDescriptor):
    type: WorkType
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: List[Dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Work-{self.work_type.name}"

class Meal(BaseModel, SessionDescriptor):
    type: MealType
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: List[Dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Meal-{self.meal_type.name}"

class FixedActivities(SessionGroup):
    """
    Generates all fixed personal activities for a week (Sleep, Work, Gym, Meals)
    based on parameters fetched from the database.
    """
    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        # 1. Load all parameters from the (mocked) database
        self.db_data = self._load_db_parameters()

        # 2. Define an activity map to automate processing
        self.activity_map = {
            "gym": {"model": Gym, "enum": GymWorkout},
            "sleep": {"model": Sleep, "enum": SleepType},
            "work": {"model": Work, "enum": WorkType},
            "meal": {"model": Meal, "enum": MealType},
        }

        # 3. Create all descriptors by iterating over the map
        self.fixed_descriptors: List[SessionDescriptor] = []
        for activity_key, config in self.activity_map.items():
            self._create_descriptors_from_db(
                activity_key=activity_key,
                model_class=config["model"],
                enum_class=config["enum"]
            )

        # 3. Create the final list of Session variables
        self._csp_variables: List[Session] = []
        for descriptor in self.fixed_descriptors:
            self._csp_variables.append(
                Session(
                    session_descriptor=descriptor,
                    allowed_times=self.get_allowed_times(descriptor),
                    min_duration=self.get_min_duration(descriptor),
                    max_duration=self.get_max_duration(descriptor)
                )
            )
        
    def _load_db_parameters(self) -> Dict[str, Any]:
        """ Mocks the new, more flexible database structure. """
        #TODO: put this in the logging system
        print("INFO: Loading fixed activity settings from flexible DB structure...")
        return {
            "gym": [
                {"type": "PUSH", "sessions_per_week": 1, "min_duration_mins": 60, "max_duration_mins": 90, "allowed_intervals": [{"day": "saturday", "start": "10:00", "end": "20:00"}]},
                {"type": "PULL", "sessions_per_week": 1, "min_duration_mins": 60, "max_duration_mins": 75, "allowed_intervals": [{"day": "monday", "start": "18:00", "end": "22:00"}]},
                {"type": "LEG", "sessions_per_week": 1, "min_duration_mins": 75, "max_duration_mins": 90, "allowed_intervals": [{"day": "wednesday", "start": "18:00", "end": "22:00"}]}
            ],
            "sleep": [{"type": "NIGHT", "sessions_per_week": 7, "min_duration_mins": 420, "max_duration_mins": 540, "allowed_intervals": [{"day": "all", "start": "21:00", "end": "09:00"}]}],
            "work": [{"type": "MAIN_JOB", "sessions_per_week": 5, "min_duration_mins": 480, "max_duration_mins": 540, "allowed_intervals": [{"day": "working_days", "start": "08:00", "end": "18:00"}]}],
            "meal": [{"type": "LUNCH", "sessions_per_week": 7, "min_duration_mins": 30, "max_duration_mins": 60, "allowed_intervals": [{"day": "all", "start": "12:00", "end": "15:00"}]}]
        }

    def _create_descriptors_from_db(self, activity_key: str, model_class, enum_class, enum_field: str):
        """
        Parses a list of activity entries from the DB data to create descriptors.
        """
        activity_entries = self.db_data.get(activity_key, [])
        for entry in activity_entries:
            descriptor = model_class(
                type=enum_class[entry['type']],
                min_duration=timedelta(minutes=entry['min_duration_mins']),
                max_duration=timedelta(minutes=entry['max_duration_mins']),
                allowed_intervals=entry['allowed_intervals']
            )
            self.fixed_descriptors.extend([descriptor] * entry['sessions_per_week'])

    def get_allowed_times(self, descriptor: SessionDescriptor) -> AllowedTimes:
        """
        Parses the interval rules stored within the descriptor itself
        into concrete datetime intervals for the week.
        """
        intervals = []
        day_map = {
            "saturday": [0], "sunday": [1], "monday": [2], "tuesday": [3],
            "wednesday": [4], "thursday": [5], "friday": [6],
            "all": list(range(7)),
            "working_days": [1, 2, 3, 4, 5] # Sun-Thu in Egypt
        }
        
        # This logic is already automated as you suggested
        activity_key = descriptor.__class__.__name__.lower()

        for rule in descriptor.allowed_intervals:
            start_time = datetime.strptime(rule['start'], '%H:%M').time()
            end_time = datetime.strptime(rule['end'], '%H:%M').time()
            for day_offset in day_map.get(rule['day'], []):
                current_date = self.week_start_date + timedelta(days=day_offset)
                start_dt = datetime.combine(current_date.date(), start_time)
                end_dt = datetime.combine(current_date.date(), end_time)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                intervals.append((start_dt, end_dt))
        return AllowedTimes(intervals)

    def get_min_duration(self, descriptor: SessionDescriptor) -> timedelta:
        return descriptor.min_duration

    def get_max_duration(self, descriptor: SessionDescriptor) -> timedelta:
        return descriptor.max_duration

    @property
    def csp_variables(self) -> list[Session]:
        return self._csp_variables


