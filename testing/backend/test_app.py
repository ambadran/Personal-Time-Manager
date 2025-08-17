'''

'''
import pytest
from personal_time_manager import gunicorn_main_routine
from dotenv import load_dotenv

# Load environment variables from .env file before anything else
load_dotenv()

@pytest.fixture
def client():
    backend = gunicorn_main_routine()
    backend.config['TESTING'] = True
    with backend.test_client() as client:
        yield client


def test_root_endpoint_healthcheck(client):
    """
    Test the root endpoint
    it just does database Health check then return status_code 200
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "application/json" in response.headers["Content-Type"]

def test_export_date(client):
    '''
    Tests the export all data method
    Extremely important to process the tuition.py

    Must make sure structure is correct
    '''
    pass
