'''
Testing prayers session management
'''
from typing import Any
from datetime import datetime
from unittest.mock import MagicMock
import pytest
from test_base_session import TEST_START_DATE
from mock_prayers_html_response import athan_api_data
from personal_time_manager.sessions.prayers import Prayers, Prayer, PrayerType, WeekDay

def test_actual_api_connection_response():
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
    assert test_date_saturday_fajr_datetime == datetime(2025, 12, 6, 5, 14)

@pytest.fixture
def prayers(monkeypatch: pytest.MonkeyPatch) -> Prayers:
    '''
    Creating a Fixture for the prayers class which intercept the HTTP request to api and replace with mock data to prevent time waste with every test
    '''
    def fake_get(url: str, params: dict[str, Any]) -> Any:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        print("pytest print", params["date"], type(params['date']))
        mock_response.json.return_value = athan_api_data[params["date"]] #TODO
        return mock_response

    monkeypatch.setattr("requests.get", fake_get)
    prayers = Prayers(TEST_START_DATE)
    return prayers


def test_prayer_class(prayers: Prayers):
    '''
    the prayers argument here is the fixture prayers object :D which runs a mock api response using mokeypatch http request interception ;)
    '''

    # Test1: This running without errors is the first test
    for session in prayers.csp_variables:
        print(f"{session.session_descriptor.name}: {session.domain_values[0].strftime('%Y-%m-%d %H:%M')}")

    # Test2: 
    assert len(prayers.csp_variables) == 5*7

