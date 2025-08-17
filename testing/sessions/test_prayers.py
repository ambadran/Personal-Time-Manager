'''
Testing prayers session management
'''
from typing import Any
from unittest.mock import MagicMock
import pytest
from test_base_session import TEST_START_DATE
from mock_prayers_html_response import athan_api_data
from personal_time_manager.sessions.prayers import Prayers

def test_actual_api_connection_response():
    pass

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

