'''
Testing prayers session management
'''
from typing import Any
from unittest.mock import MagicMock
import pytest
from test_base_session import TEST_START_DATE
from mock_prayers_html_response import athan_api_data
from personal_time_manager.sessions.prayers import Prayers

@pytest.fixture
def prayers(monkeypatch: pytest.MonkeyPatch) -> Prayers:
    '''
    Creating a Fixture for the prayers class which intercept the HTTP request to api and replace with mock data to prevent time waste with every test
    '''
    def fake_get(url: str, params: dict[str, Any]) -> Any:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = athan_api_data[params["date"]] #TODO
        return mock_response

    monkeypatch.setattr("requests.get", fake_get)
    prayers = Prayers(TEST_START_DATE)
    return Prayers()


def test_prayer_class(prayers: Prayers):

    # # ONLY USED FOR TESTING to avoid doing all the HTTP Requests
    # data = athan_api_data[prayer.name]
    
    for session in prayers.csp_variables:
        print(f"{session.session_descriptor.name}: {session.domain_values[0].strftime('%Y-%m-%d %H:%M')}")

