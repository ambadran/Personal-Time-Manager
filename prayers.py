'''
This is the script that gets the latest prayer times
'''
import requests
import time
from datetime import datetime, timedelta, time
import json
from sessions import SessionGroup, Session, SessionDescriptor
from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple

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

@dataclass(frozen=True)
class Prayer(SessionDescriptor):
    type: PrayerType
    day: WeekDay
    
    @property
    def name(self):
        if self.type == PrayerType.DHUHR and self.day == WeekDay.FRIDAY:
            return "JUMAH"
        return f"{self.type.name}_{self.day.name}"

# Create all combinations programmatically
class Prayers(SessionGroup):
    ALL_PRAYERS = tuple(Prayer(type=prayer, day=day) for prayer in PrayerType for day in WeekDay)

    EQAMA_TIMES: dict[PrayerType: timedelta] = {
                   PrayerType.FAJR: timedelta(minutes=20), 
                   PrayerType.DHUHR: timedelta(minutes=20), 
                   PrayerType.ASR: timedelta(minutes=20), 
                   PrayerType.MAGHRIB: timedelta(minutes=20), 
                   PrayerType.ISHA: timedelta(minutes=20)}

    PRAYER_DURATION = timedelta(minutes=15)  # how much it takes to go and return from prayer
    EQAMA_TOLERANCE = timedelta(minutes=5)  # time I need to get up before eqama to not miss prayer

    LATITUDE = 29.954090 
    LONGITUDE = 31.067551
 
    BASE_URL = "http://api.aladhan.com/v1/timings"
    PRAYER_CALC_METHOD = 2 # https://api.aladhan.com/v1/methods shows the index for each method

    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        # creating the sessions
        self._csp_variables = [
            Session(prayer, self.PRAYER_DURATION, self.get_prayer_domain_times(prayer))
            for prayer in self.ALL_PRAYERS
        ]

    def get_prayer_eqama(self, prayer: Prayer) -> timedelta:
        '''
        return duration
        '''
        # check if name is valid
        if prayer not in self.ALL_PRAYERS:
            raise ValueError(f"Invalid prayer: {prayer}")

        return self.EQAMA_TIMES[prayer.type]

    def get_prayer_day_offset(self, prayer: Prayer) -> int:
        '''
        takes in a prayer from the week and return the offset of the day it is in 
        0 is saturday, 1 is monday, etc..
        '''
        # check if name is valid
        if prayer not in self.ALL_PRAYERS:
            raise ValueError(f"Invalid prayer: {prayer}")

        return list(WeekDay).index(prayer.day)

    def prayer_to_api_params(self, prayer: Prayer) -> tuple[str, str]:
        '''
        returns the data needed to be parsed as json and sent as HTML request to server
        '''
        # check if name is valid
        if prayer not in self.ALL_PRAYERS:
            raise ValueError(f"Invalid prayer: {prayer}")

        # find day offset
        day_offset = self.get_prayer_day_offset(prayer)
        prayer_date = self.week_start_date + timedelta(days=day_offset)
        prayer_name = prayer.type.name.lower().capitalize()
        
        return prayer_date.strftime("%d-%m-%Y"), prayer_name

    def get_prayer_time(self, prayer: Prayer) -> datetime:
        '''
        returns the datetime of the time of a specific prayer within this week
        '''
        date_str, prayer_name = self.prayer_to_api_params(prayer)

        params = {
            "latitude": self.LATITUDE,
            "longitude": self.LONGITUDE,
            "date": date_str,
            "method": self.PRAYER_CALC_METHOD
        }

        try:
            # response = requests.get(self.BASE_URL, params=params)
            # response.raise_for_status()  # Raise exception for HTTP errors
            # data: dict = response.json()
            
            # ONLY USED FOR TESTING to avoid doing all the HTTP Requests
            from test_api import athan_api_data
            data = athan_api_data[prayer.name]
            if data["code"] != 200 or "data" not in data:
                raise ValueError("Invalid response from server")
                
            timings = data["data"]["timings"]
            hour, minute = map(int, timings[prayer_name].split(":"))
            
            day_offset = self.get_prayer_day_offset(prayer)
            prayer_date = self.week_start_date + timedelta(days=day_offset)

            return datetime.combine(prayer_date.date(), time(hour, minute))
            
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to get prayer time: {str(e)}")           

    def get_prayer_domain_times(self, prayer: Prayer) -> list[datetime]:
        '''
        return a list of all the possible time to start prayer
        There is actually only one time!!!
        the athan_time+eqama-offset_to_actually_get_there
        '''
        athan_time = self.get_prayer_time(prayer)
        eqama_offset = self.get_prayer_eqama(prayer)
        get_up_time = athan_time + eqama_offset - self.EQAMA_TOLERANCE
        return [get_up_time]

    @property
    def csp_variables(self) -> list[Session]:
        return self._csp_variables

    @property
    def csp_domains(self) -> dict[Session: list[datetime]]:
        return {session: session.domain_values for session in self.csp_variables}

# Example usage
if __name__ == "__main__":
    start_date = datetime(2025, 12, 6)  # Saturday
    prayers = Prayers(start_date)
    
    for session in prayers.csp_variables:
        print(f"{session.session_descriptor.name}: {session.domain_values[0].strftime('%Y-%m-%d %H:%M')}")

