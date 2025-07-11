'''
This is the script that gets the latest prayer times
'''
import requests
from time import struct_time, strftime
import time
from datetime import datetime
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

    EQAMA_TIMES = {PrayerType.FAJR: 20, PrayerType.DHUHR: 20, PrayerType.ASR: 20, PrayerType.MAGHRIB: 10, PrayerType.ISHA: 20}

    PRAYER_DURATION = 15  # how much it takes to go and return from prayer
    EQAMA_TOLERANCE = 5  # time I need to get up before eqama to not miss prayer

    LATITUDE = 29.954090 
    LONGITUDE = 31.067551
 
    BASE_URL = "http://api.aladhan.com/v1/timings"
    PRAYER_CALC_METHOD = 2 # https://api.aladhan.com/v1/methods shows the index for each method

    def __init__(self, week_start_date: struct_time):
        if week_start_date.tm_wday != 5:
            raise ValueError("week_start_date must be a Saturday!")
        super().__init__(week_start_date)

        # creating the sessions
        self._csp_variables = [Session(prayer, self.PRAYER_DURATION, self.get_prayer_domain_times(prayer)) for prayer in self.ALL_PRAYERS]

    def get_prayer_eqama(self, prayer: Prayer) -> int:
        '''
        return duration
        '''
        # check if name is valid
        if prayer not in self.ALL_PRAYERS:
            raise ValueError(f"Prayer name is wrong\nPlease choose from\n{self.ALL_PRAYERS}")

        return self.EQAMA_TIMES[prayer.type]


    def get_prayer_day_pointer(self, prayer: Prayer) -> int:
        '''
        takes in a prayer from the week and return the pointer of the day it is in 
        0 is saturday, 1 is monday, etc..
        '''
        # check if name is valid
        if prayer not in self.ALL_PRAYERS:
            raise ValueError(f"Prayer name is wrong\nPlease choose from\n{self.ALL_PRAYERS}")

        return list(WeekDay).index(prayer.day)

    def prayer_name_to_date_and_name(self, prayer: Prayer) -> tuple[str, str]:
        '''
        returns the data needed to be parsed as json and sent as HTML request to server
        '''
        # check if name is valid
        if prayer not in self.ALL_PRAYERS:
            raise ValueError(f"Prayer name is wrong\nPlease choose from\n{self.ALL_PRAYERS}")

        # find day pointer
        day_pointer = self.get_prayer_day_pointer(prayer)

        # find which prayer in the day
        # prayer_per_day = ("FAJR", "DHUHR", "ASR", "MAGHRIB", "ISHA")
        # prayer_num = prayer_per_day.index(prayer_name)
        
        # the API uses format: first letter capital and rest is small case
        prayer_name = prayer.type.name.lower().capitalize()
        
        # get wanted data
        wanted_date = struct_time((self.week_start_date.tm_year, self.week_start_date.tm_mon, self.week_start_date.tm_mday+day_pointer, 0, 0, 0, 0, 0, -1))
        wanted_date_proper_format = strftime("%d-%m-%Y", wanted_date)

        return wanted_date_proper_format, prayer_name
 


    def get_prayer_time(self, prayer: Prayer) -> struct_time:
        '''
        returns the struct_time of the time of a specific prayer within this week
        '''
        wanted_date_proper_format, prayer_name = self.prayer_name_to_date_and_name(prayer)
       
        params = {
            "latitude": self.LATITUDE,
            "longitude": self.LONGITUDE,
            "date": wanted_date_proper_format,
            "method": self.PRAYER_CALC_METHOD
        }
        try:
            # response = requests.get(self.BASE_URL, params=params)
            # response.raise_for_status()  # Raise exception for HTTP errors
            # data: dict = response.json()
            
            # ONLY USED FOR TESTING to avoid doing all the HTTP Requests
            from test_api import athan_api_data
            data = athan_api_data[prayer.name]
            
            if data["code"] == 200 and "data" in data:
                print(f"acccessed {self.BASE_URL}")
                timings = data["data"]["timings"]
                date_info = data["data"]["date"]["readable"]
                
                hour, minute = timings[prayer_name].split(":")  # format \d\d:\d\d -> hour:minutes
            else:
                raise ValueError("Invalid response from server")
                # return {"success": False, "message": "Invalid response from server"}
                
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {str(e)}")
            # return {"success": False, "message": f"Request failed: {str(e)}"}
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response")
            # return {"success": False, "message": "Invalid JSON response"}

        return struct_time((self.week_start_date.tm_year, self.week_start_date.tm_mon, self.week_start_date.tm_mday+self.get_prayer_day_pointer(prayer), int(hour), int(minute), 0, 0, 0, -1))

    def get_prayer_domain_times(self, prayer: Prayer) -> list[struct_time]:
        '''
        return a list of all the possible time to start prayer
        '''
        # converting struct_time to epoch time to be able to add
        athan_time: int = time.mktime(self.get_prayer_time(prayer)) 
        # adding the minutes I want then convert back to struct_time
        get_up_time = time.localtime(athan_time + 60*self.get_prayer_eqama(prayer)-60*self.EQAMA_TOLERANCE)
        return [get_up_time]

    @property
    def csp_variables(self) -> list[Session]:
        return self._csp_variables

    @property
    def csp_domains(self) -> dict[Session: list[struct_time]]:
        domains = {}
        for session in self.csp_variables:
            domains[session] = session.domain_values

        return domains

# Example usage
if __name__ == "__main__":
    wanted_week = struct_time((2025, 12, 7, 0, 0, 0, 5, 0, -1))
    prayers = Prayers(wanted_week)

    print()
    for i in prayers.csp_variables:
        print(i)
   

