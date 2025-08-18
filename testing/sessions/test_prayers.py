'''
Testing prayers session management
'''
from datetime import datetime
import pytest
from personal_time_manager.sessions.prayers import Prayers, Prayer, PrayerType, WeekDay

def test_actual_api_connection_response(TEST_START_DATE: datetime):
    '''
    Test that API calls are working indeed, just one call is enough
    Basically, we are testing self.get_prayer_time
    '''
    # I don't want to run the __init__
    custom_prayers = Prayers.__new__(Prayers)

    # manually setting the start_date so that the
    custom_prayers.week_start_date = TEST_START_DATE

    # now calling the .get_prayer_time for only one Prayer 
    test_date_saturday_fajr_datetime = custom_prayers.get_prayer_time(Prayer(type=PrayerType.FAJR, day=WeekDay.SATURDAY))

    # Make sure it did indeed return the right time :D
    print(f"API HTML resp Fajr on Date: {TEST_START_DATE} is\n{test_date_saturday_fajr_datetime}")
    assert type(test_date_saturday_fajr_datetime) == datetime


def test_prayer_class(prayers: Prayers):
    '''
    the prayers argument here is the fixture prayers object :D which runs a mock api response using mokeypatch http request interception ;)

    Tests if the Prayers(SessionGroup) class will run properly:
        - No Errors
        - generate correct CSP Variables list
        - generate correct CSP Domain Dictionary
    '''

    # Test1: This running without errors is the first test
    for session in prayers.csp_variables:
        print(f"{session.session_descriptor.name}: {session.domain_values[0].strftime('%Y-%m-%d %H:%M')}")

    # Test2: 
    assert len(prayers.csp_variables) == 5*7

