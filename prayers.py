'''
This is the script that gets the latest prayer times
'''
import requests
from datetime import datetime
import json

class Prayers:
    PRAYERS_DAILY = [
            "FAJR",
            "DHUHR",
            "ASR",
            "MAGHRIB",
            "ISHA"]
    PRAYERS_WEEKLY = [
            "FAJR_SATURDAY",
            "DHUHR_SATURDAY",
            "ASR_SATURDAY",
            "MAGHRIB_SATURDAY",
            "ISHA_SATURDAY",
            "FAJR_SUNDAY",
            "DHUHR_SUNDAY",
            "ASR_SUNDAY",
            "MAGHRIB_SUNDAY",
            "ISHA_SUNDAY",
            "FAJR_MONDAY",
            "DHUHR_MONDAY",
            "ASR_MONDAY",
            "MAGHRIB_MONDAY",
            "ISHA_MONDAY",
            "FAJR_TUESDAY",
            "DHUHR_TUESDAY",
            "ASR_TUESDAY",
            "MAGHRIB_TUESDAY",
            "ISHA_TUESDAY",
            "FAJR_WEDNESDAY",
            "DHUHR_WEDNESDAY",
            "ASR_WEDNESDAY",
            "MAGHRIB_WEDNESDAY",
            "ISHA_WEDNESDAY",
            "FAJR_THURSDAY",
            "DHUHR_THURSDAY",
            "ASR_THURSDAY",
            "MAGHRIB_THURSDAY",
            "ISHA_THURSDAY",
            "FAJR_FRIDAY",
            "DHUHR_FRIDAY",
            "ASR_FRIDAY",
            "MAGHRIB_FRIDAY",
            "ISHA_FRIDAY"]
    def __init__(self, week_start_date: str):
        # check if date is correct, a saturday day
        #TODO 
        pass


def get_prayer_times(latitude, longitude, method=None):
    """
    Get prayer times from Aladhan API
    
    Parameters:
    - latitude: float
    - longitude: float
    - method: int (optional) - Calculation method (see API docs)
    
    Returns:
    - Dictionary containing prayer times or error message
    """
    
    base_url = "http://api.aladhan.com/v1/timings"
    
    # Get current date in DD-MM-YYYY format
    today = datetime.now().strftime("%d-%m-%Y")
    print(today)
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "date": today,
        "method": method if method else 2  # Default to ISNA method
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        if data["code"] == 200 and "data" in data:
            timings = data["data"]["timings"]
            date_info = data["data"]["date"]["readable"]
            
            return {
                "success": True,
                "date": date_info,
                "times": timings,
                "method": data["data"]["meta"]["method"]["name"],
                "location": f"{latitude}, {longitude}"
            }
        else:
            return {"success": False, "message": "Invalid response from server"}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"success": False, "message": "Invalid JSON response"}

# Example usage
if __name__ == "__main__":
    # Coordinates for New York City
    latitude = 29.954090 
    longitude = 31.067551
    
    prayer_times = get_prayer_times(latitude, longitude, method=5)
    
    if prayer_times["success"]:
        print(f"Prayer Times for {prayer_times['date']}")
        print(f"Location: {prayer_times['location']}")
        print(f"Calculation Method: {prayer_times['method']}\n")
        
        for prayer, time in prayer_times["times"].items():
            print(f"{prayer}: {time}")
    else:
        print(f"Error: {prayer_times['message']}")
