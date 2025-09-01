'''
* INPUTS to this Module *
Prayer Times are acquired from online prayer api (in Prayers.BASE_URL)

* OUTPUTS from this Module *
This Module generates Inputs to CSP Framework
    - CSP Session Variable list, all prayer sessions in a week
    - CSP Domain Variable Dictionary, each possible start time of each prayer session variable

'''
import json
import requests
from enum import Enum, auto
from typing import Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta, time
from personal_time_manager.sessions.base_session import AllowedTimes, SessionDescriptor, Session, SessionTime, SessionGroup

class PrayerType(Enum):
    FAJR = auto()
    DHUHR = auto()
    ASR = auto()
    MAGHRIB = auto()
    ISHA = auto()

class WeekDay(Enum):
    SATURDAY = auto()
    SUNDAY = auto()
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()

class Prayer(BaseModel, SessionDescriptor):
    type: PrayerType
    day: WeekDay
    eqama_time: timedelta
    min_duration: timedelta
    max_duration: timedelta

    # Pydantic v2 config for immutability (equivalent to frozen=True)
    model_config = ConfigDict(frozen=True)

    @property
    def name(self):
        if self.type == PrayerType.DHUHR and self.day == WeekDay.FRIDAY:
            return "JUMAH"
        return f"{self.type.name}_{self.day.name}"

class Prayers(SessionGroup):
    '''

    '''
    BASE_URL = "http://api.aladhan.com/v1/timings"
    EQAMA_TOLERANCE = timedelta(minutes=5) # Time to get ready before Eqama
    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        # Get DB Parameters
        self.db_data = self._load_db_parameters()
        self.latitude = self.db_data["location"]["latitude"]
        self.longitude = self.db_data["location"]["longitude"]
        self.prayer_calc_method = self.db_data["api_method"]
        self._prayer_time_cache: dict[str, Dict] = {}

        # Create list of all distinct SessionDescriptor that will have its be used in a seperate Session variable
        self.prayer_descriptors: list[Prayer] = []
        for prayer_type in PrayerType:
            for day in WeekDay:
                min_dur, max_dur = self._get_duration_from_db(prayer_type, day)
                self.prayer_descriptors.append(
                        Prayer(
                            type=prayer_type,
                            day=day,
                            eqama_time = self._get_eqama_from_db(prayer),
                            min_duration=min_dur,
                            max_duration=max_dur
                            )
                        )

        # creating the sessions
        self._csp_variables: list[Session] = []
        for prayer_descriptor in self.prayer_descriptors:
            self._csp_variables.append(
                Session(
                    session_descriptor=prayer_descriptor, 
                    allowed_times = self.get_allowed_times(prayer),
                    min_duration = self.get_min_duration(prayer),
                    max_duration = self.get_max_duration(prayer)
                    ))

    def _load_db_parameters(self) -> dict[str, Any]:
        """ Mocks fetching configuration from a Postgres database. """
        print("INFO: Loading prayer settings from database...")
        return {
            "location": {"latitude": 29.954090, "longitude": 31.067551},
            "api_method": 2, # Islamic Society of North America
            "eqama_times": { # Offset from Athan time in minutes
                "FAJR": 25, "DHUHR": 20, "ASR": 20, "MAGHRIB": 10, "ISHA": 20
            },
            "durations": { # Duration of the prayer session in minutes
                "default_min": 15,    # NEW
                "default_max": 25,    # NEW
                "JUMAH_min": 45,      # NEW
                "JUMAH_max": 60       # NEW
            }
        }

    def _get_eqama_from_db(self, prayer_type: PrayerType) -> timedelta:
        """ Gets the eqama offset for a prayer type from the DB data. """
        minutes = self.db_data["eqama_times"].get(prayer_type.name, 20)
        return timedelta(minutes=minutes)

    def _get_duration_from_db(self, prayer_type: PrayerType, day: WeekDay) -> tuple[timedelta, timedelta]:
        """ Gets the session duration range, handling special cases like Jumah. """
        if prayer_type == PrayerType.DHUHR and day == WeekDay.FRIDAY:
            min_minutes = self.db_data["durations"]["JUMAH_min"]
            max_minutes = self.db_data["durations"]["JUMAH_max"]
        else:
            min_minutes = self.db_data["durations"]["default_min"]
            max_minutes = self.db_data["durations"]["default_max"]
        return timedelta(minutes=min_minutes), timedelta(minutes=max_minutes)

    # --- Implementation of SessionGroup Abstract Methods ---

    def get_allowed_times(self, prayer: Prayer) -> AllowedTimes:
        """
        Calculates the single, precise time window for a prayer using the
        parameters stored within the Prayer descriptor itself.
        """
        athan_time = self._get_prayer_time_from_api(prayer)
        
        # The start time is fixed
        start_time = athan_time + prayer.eqama_time - self.EQAMA_TOLERANCE
        # The window must be large enough to accommodate the max duration
        end_time = start_time + prayer.max_duration
        
        return AllowedTimes([(start_time, end_time)])

    def get_min_duration(self, prayer: Prayer) -> timedelta:
        """ The duration is fixed, so min_duration is read from the descriptor. """
        return prayer.min_duration

    def get_max_duration(self, prayer: Prayer) -> timedelta:
        """ The duration is fixed, so max_duration is read from the descriptor. """
        return prayer.max_duration

    # --- Internal Helper Methods ---

    def _get_prayer_day_offset(self, prayer: Prayer) -> int:
        return list(WeekDay).index(prayer.day)

    def _get_prayer_time_from_api(self, prayer: Prayer) -> datetime:
        """
        Efficiently fetches prayer times from the API, caching results by day.
        """
        day_offset = self._get_prayer_day_offset(prayer)
        prayer_date = self.week_start_date + timedelta(days=day_offset)
        date_str = prayer_date.strftime("%d-%m-%Y")
        api_prayer_name = prayer.type.name.lower().capitalize()

        if date_str not in self._prayer_time_cache:
            params = {
                "latitude": self.latitude, "longitude": self.longitude,
                "date": date_str, "method": self.prayer_calc_method
            }
            try:
                response = requests.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                self._prayer_time_cache[date_str] = data["data"]["timings"]
            except requests.RequestException as e:
                raise ConnectionError(f"Failed to get prayer times for {date_str}: {e}")

        timings = self._prayer_time_cache[date_str]
        hour, minute = map(int, timings[api_prayer_name].split(":"))
        return datetime.combine(prayer_date.date(), time(hour, minute))

    @property
    def csp_variables(self) -> list[Session]:
        """ Implements the abstract method from SessionGroup. """
        return self._csp_variables

