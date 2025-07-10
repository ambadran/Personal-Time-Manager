'''
This is the script that gets the latest prayer times
'''
import requests
from time import struct_time, strftime
import time
from datetime import datetime
import json
from sessions import SessionGroup, Session

class Prayers(SessionGroup):
    PRAYERS_WEEKLY = ("FAJR_SATURDAY", "DHUHR_SATURDAY", "ASR_SATURDAY", "MAGHRIB_SATURDAY", "ISHA_SATURDAY", "FAJR_SUNDAY", "DHUHR_SUNDAY", "ASR_SUNDAY", "MAGHRIB_SUNDAY", "ISHA_SUNDAY", "FAJR_MONDAY", "DHUHR_MONDAY", "ASR_MONDAY", "MAGHRIB_MONDAY", "ISHA_MONDAY", "FAJR_TUESDAY", "DHUHR_TUESDAY", "ASR_TUESDAY", "MAGHRIB_TUESDAY", "ISHA_TUESDAY", "FAJR_WEDNESDAY", "DHUHR_WEDNESDAY", "ASR_WEDNESDAY", "MAGHRIB_WEDNESDAY", "ISHA_WEDNESDAY", "FAJR_THURSDAY", "DHUHR_THURSDAY", "ASR_THURSDAY", "MAGHRIB_THURSDAY", "ISHA_THURSDAY", "FAJR_FRIDAY", "DHUHR_FRIDAY", "ASR_FRIDAY", "MAGHRIB_FRIDAY", "ISHA_FRIDAY")

    EQAMA_TIMES = [20, 20, 20, 10, 20] 

    LATITUDE = 29.954090 
    LONGITUDE = 31.067551
 
    BASE_URL = "http://api.aladhan.com/v1/timings"
    PRAYER_CALC_METHOD = 2 # https://api.aladhan.com/v1/methods shows the index for each method

    def __init__(self, week_start_date: struct_time):
        if week_start_date.tm_wday != 5:
            raise ValueError("week_start_date must be a Saturday!")
        super().__init__(week_start_date)

        # creating the sessions
        self._csp_variables = [Session(prayer_name, self.get_prayer_domain_times(prayer_name)) for prayer_name in self.PRAYERS_WEEKLY]

    def get_prayer_day_pointer(self, prayer: str) -> int:
        '''
        takes in a prayer from the week and return the pointer of the day it is in 
        0 is saturday, 1 is monday, etc..
        '''
        # check if name is valid
        if prayer not in self.PRAYERS_WEEKLY:
            raise ValueError(f"Prayer name is wrong\nPlease choose from\n{self.PRAYERS_WEEKLY}")

        prayer_name, day = prayer.split("_")
        week_days = ("SATURDAY", "SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY")
        return week_days.index(day)


    def prayer_name_to_date_and_name(self, prayer: str) -> tuple[str, str]:
        '''
        returns the data needed to be parsed as json and sent as HTML request to server
        '''
        # check if name is valid
        if prayer not in self.PRAYERS_WEEKLY:
            raise ValueError(f"Prayer name is wrong\nPlease choose from\n{self.PRAYERS_WEEKLY}")

        # find day pointer
        day_pointer = self.get_prayer_day_pointer(prayer)

        # find which prayer in the day
        # prayer_per_day = ("FAJR", "DHUHR", "ASR", "MAGHRIB", "ISHA")
        # prayer_num = prayer_per_day.index(prayer_name)
        
        # the API uses format: first letter capital and rest is small case
        prayer_name, _ = prayer.split("_")
        prayer_name = prayer_name.lower().capitalize()
        
        # get wanted data
        wanted_date = struct_time((self.week_start_date.tm_year, self.week_start_date.tm_mon, self.week_start_date.tm_mday+day_pointer, 0, 0, 0, 0, 0, -1))
        wanted_date_proper_format = strftime("%d-%m-%Y", wanted_date)

        return wanted_date_proper_format, prayer_name
 

    def get_prayer_time(self, prayer: str) -> struct_time:
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
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            data: dict = response.json()
            
            if data["code"] == 200 and "data" in data:
                timings = data["data"]["timings"]
                print(timings)
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

    def get_prayer_domain_times(self, prayer: str) -> list[struct_time]:
        return []

    @property
    def csp_variables(self) -> list[Session]:
        pass

    @property
    def csp_domains(self) -> dict[Session: list[struct_time]]:
        pass

# Example usage
if __name__ == "__main__":
    wanted_week = struct_time((2025, 12, 7, 0, 0, 0, 5, 0, -1))
    prayers = Prayers(wanted_week)
   
    print(prayers.get_prayer_time("FAJR_SATURDAY"))

