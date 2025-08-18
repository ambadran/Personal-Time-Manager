from typing import Any
from datetime import datetime
from unittest.mock import MagicMock
import pytest
from personal_time_manager.sessions.prayers import Prayers
from sessions.mock_prayers_html_response import athan_api_data
from personal_time_manager.sessions.tuitions import Tuitions
from sessions.mock_db_export_all import db_mock as db_export_all_data

@pytest.fixture
def TEST_START_DATE() -> datetime:
    """Provides a consistent start date for tests."""
    return datetime(2025, 12, 6)  # Saturday

@pytest.fixture
def prayers(monkeypatch: pytest.MonkeyPatch, TEST_START_DATE: datetime) -> Prayers:
    '''
    Creating a Fixture for the prayers class which intercept the HTTP request to api and replace with mock data to prevent time waste with every test
    '''
    def fake_get(url: str, params: dict[str, Any]) -> Any:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = athan_api_data[params["date"]] #TODO

        print("\n--- Intercepted HTTP Request to Prayers API, returning mock data instead! ---")
        return mock_response

    monkeypatch.setattr("requests.get", fake_get)
    prayers = Prayers(TEST_START_DATE)
    return prayers


@pytest.fixture
def tuitions(monkeypatch: pytest.MonkeyPatch, TEST_START_DATE: datetime) -> Tuitions:
    '''
    Creating a Fixture for the Tuition class which intercept the database access step and replace with mock data to prevent time waste with every test
    '''
    #REMEMBER: if I want to get real life data from online database 
    # I CAN just comment out the next 8 lines and run pytest as normal
    def mock_get_latest_db_data(self) -> list[Any]:
        """
        A fake database access function that returns predefined mock data.
        """
        print("\n--- Intercepted DB export all call, returning mock data instead! ---")
        return db_export_all_data

    monkeypatch.setattr(Tuitions, 'get_latest_db_data', mock_get_latest_db_data)
    
    tuitions = Tuitions(TEST_START_DATE)
    return tuitions


