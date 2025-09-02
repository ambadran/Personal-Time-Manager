'''
This session module defines the CSP variables and domains of personal persistent times that is not defined in any of apple / google calenders.
Example is work time, my sleep time, Gym times and more
'''
from datetime import datetime, timedelta, time
from enum import Enum, auto
from typing import Any
from pydantic import BaseModel, ConfigDict
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor, AllowedTimes
from personal_time_manager.database.db_handler2 import DatabaseHandler #TODO: remove the 2 when db_handler is finished
from psycopg2.extras import RealDictRow

class WorkType(Enum):
    MAINJOB = auto()
    FREELANCE = auto()
    # Pydantic will auto-convert MainJob_Freelance from the DB
    MAINJOB_FREELANCE = auto()
    TUITION = auto()

class GymType(Enum):
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
    allowed_intervals: list[dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Gym-{self.workout.name}"

class Sleep(BaseModel, SessionDescriptor):
    type: SleepType
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: list[dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Sleep-{self.sleep_type.name}"

class Work(BaseModel, SessionDescriptor):
    type: WorkType
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: list[dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Work-{self.work_type.name}"

class Meal(BaseModel, SessionDescriptor):
    type: MealType
    min_duration: timedelta
    max_duration: timedelta
    allowed_intervals: list[dict[str, Any]] # Stores the DB rules

    model_config = ConfigDict(frozen=True)

    @property
    def name(self) -> str:
        return f"Meal-{self.meal_type.name}"

class FixedActivities(SessionGroup):
    """
    Generates all fixed personal activities for a week (Sleep, Work, Gym, Meals)
    based on parameters fetched from the database.

    I had the amazing idea of making 3 rules to ensure modularity and not having to define strings explicitly 
    to handle database

    **The RULES**
    1- Database Category Name is EXACTLY the same as Python Class Name
        - DB: 'Gym' -> Python: class Gym()
    2- Database Type Column is EXACTLY the same as Python Class Name followed by '_type'
        - For 'Gym' class -> DB column must be gym_type
    3- Python Enum Class is EXACTLY the same as Python Class Name
        - 'class Gym' must use enum named 'GymType'
    """
    WORKING_DAYS = [1, 2, 3, 4, 5] # Sun-Thu in Egypt
    def __init__(self, week_start_date: datetime, db_handler: DatabaseHandler):
        super().__init__(week_start_date, db_handler)

        # 1. Load all fixed activity records from the database
        activity_rows = self._load_fixed_activities_from_db()

        # 2. Create all descriptors from the database rows using our new automated logic
        self.fixed_descriptors = self._create_descriptors_from_rows(activity_rows)

        # 3. Create the final list of Session variables (this part is unchanged)
        self._csp_variables: list[Session] = []
        for descriptor in self.fixed_descriptors:
            self._csp_variables.append(
                Session(
                    session_descriptor=descriptor,
                    allowed_times=self.get_allowed_times(descriptor),
                    min_duration=self.get_min_duration(descriptor),
                    max_duration=self.get_max_duration(descriptor)
                )
            )
        
    def _load_fixed_activities_from_db(self) -> list[dict[str, Any]]:
        """ Fetches all records from the fixed_activities table. """
        print("INFO: Loading fixed activity settings from database...")
        query = "SELECT * FROM fixed_activities;"
        return self.db_handler.fetch_all(query)

    def _create_descriptors_from_rows(self, activity_rows: list[dict[str, Any]]) -> list[SessionDescriptor]:
        """
        Dynamically parses database rows into the correct Pydantic models
        based on the established naming convention.

        The automated logic if the rules applies is as follows
            # Rule 1: Find the Pydantic model class (e.g., Gym)
            # Rule 2: Find the Enum class (e.g., GymType)
            # Rule 3: Determine the database column name (e.g., "gym_type")
        """
        descriptors = []
        #IMP Get a reference to all items defined in the current module's scope :D
        current_module_scope = globals()

        for row in activity_rows:
            category_str = row['fixed_activity_category'] # e.g., "Gym"

            # --- Automation Logic ---
            # Rule 1: Find the Pydantic model class (e.g., Gym)
            model_class = current_module_scope.get(category_str)
            # Rule 2: Find the Enum class (e.g., GymType)
            enum_class = current_module_scope.get(f"{category_str}Type")
            # Rule 3: Determine the database column name (e.g., "gym_type")
            type_col = f"{category_str.lower()}_type"
            # --- End of Automation Logic ---

            if not all([model_class, enum_class]):
                print(f"WARNING: No matching Python model/enum for category '{category_str}'. Skipping.")
                continue
            
            try:
                descriptor = model_class(
                    type=enum_class[row[type_col]],
                    min_duration=timedelta(minutes=row['min_duration_mins']),
                    max_duration=timedelta(minutes=row['max_duration_mins']),
                    allowed_intervals=row['allowed_intervals']
                )
                descriptors.extend([descriptor] * row['sessions_per_week'])
            except (ValidationError, KeyError) as e:
                raise ValueError(f"WARNING: Skipping broken fixed activity record (ID: {row.get('id', 'N/A')}). Reason: {e}")
                # print(f"WARNING: Skipping broken fixed activity record (ID: {row.get('id', 'N/A')}). Reason: {e}")
                # continue
        
        return descriptors

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
            "working_days": self.WORKING_DAYS
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


