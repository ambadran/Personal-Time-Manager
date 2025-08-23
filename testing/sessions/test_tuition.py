'''
Testing Tuition session management
'''
from datetime import datetime
import pytest
from personal_time_manager.sessions.tuitions import Tuitions
from psycopg2.extras import RealDictRow
from pprint import pprint

def test_tuition_db_access():
    '''
    Tests that connection to db was successful and it did return RealDictRow
    '''
    test_db_handler = Tuitions.__new__(Tuitions)
    raw_data = test_db_handler.get_latest_db_data()
    pprint(raw_data)
    assert len(raw_data) > 0  # make sure there is data to test

    # test the data structure to be as expected so that the Tuitions processing does what it does to expected data structure
    #TODO
    assert type(raw_data[0]) == RealDictRow

# The user's original schedule data for use in the standard test case
USER_SCHEDULE = {
    'friday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'}],
    'monday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'},
               {'end': '15:30', 'start': '06:00', 'type': 'school'},
               {'end': '19:45', 'start': '18:45', 'type': 'sports'}],
    'saturday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'}],
    'sunday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'},
               {'end': '15:30', 'start': '06:00', 'type': 'school'},
               {'end': '20:15', 'start': '18:15', 'type': 'sports'}],
    'thursday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'},
                 {'end': '15:30', 'start': '06:00', 'type': 'school'},
                 {'end': '20:00', 'start': '18:00', 'type': 'sports'}],
    'tuesday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'},
                {'end': '15:30', 'start': '06:00', 'type': 'school'},
                {'end': '17:00', 'start': '16:00', 'type': 'others'}],
    'wednesday': [{'end': '05:00', 'start': '22:00', 'type': 'sleep'},
                  {'end': '15:30', 'start': '06:00', 'type': 'school'}]
}

# A schedule where the entire week is booked
FULLY_BUSY_SCHEDULE = {
    day: [{'start': '00:00', 'end': '00:00'}] # 00:00 to 00:00 is a full 24h block
    for day in ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']
}

@pytest.mark.parametrize(
    "test_name, week_start_str, schedule, expected_free_minutes, check_times",
    [
        (
            "Standard user schedule",
            "2025-08-16", # A Saturday
            USER_SCHEDULE,
            3930, # 10080 total minutes - 6150 busy minutes
            [
                ("2025-08-18 15:29", False), # End of school on Mon -> Busy
                ("2025-08-18 15:30", True),  # First minute after school -> Free
                ("2025-08-18 18:44", True),  # Minute before sports -> Free
                ("2025-08-18 18:45", False), # Start of sports -> Busy
                ("2025-08-19 04:59", False), # End of Mon night sleep -> Busy
                ("2025-08-19 05:00", True),  # First minute after sleep -> Free
            ],
        ),
        (
            "Empty schedule (fully available)",
            "2025-09-20",
            {},
            10080, # All minutes in a week should be free
            [
                ("2025-09-20 00:00", True),
                ("2025-09-22 12:00", True),
                ("2025-09-26 23:59", True),
            ],
        ),
        (
            "Fully busy schedule",
            "2025-10-04",
            FULLY_BUSY_SCHEDULE,
            0, # No minutes should be free
            [
                ("2025-10-04 08:00", False),
                ("2025-10-06 15:30", False),
            ],
        ),
        (
            "Back-to-back intervals",
            "2025-11-01",
            {'monday': [
                {'start': '09:00', 'end': '10:00'},
                {'start': '10:00', 'end': '11:00'}
            ]},
            10080 - 120, # Week minus 2 hours
            [
                ("2025-11-03 09:59", False), # End of first block -> Busy
                ("2025-11-03 10:00", False), # Start of second block -> Busy
                ("2025-11-03 11:00", True),  # Minute after second block -> Free
            ]
        ),
        (
            "Overnight interval spanning end-of-week",
            "2025-11-22", # Week starts on Saturday, Nov 22
            {'friday': [{'start': '23:00', 'end': '01:00'}]},
            9960, # Correct total free minutes
            [
                # Check Friday, Nov 28 (end of the week)
                ("2025-11-28 22:59", True),
                ("2025-11-28 23:30", False),
                
                # **FIX**: Check Saturday, Nov 22 (start of the week), NOT Nov 29
                ("2025-11-22 00:30", False), # This time is now busy due to the wrap-around
                ("2025-11-22 01:00", True)   # This is the first free minute on Saturday
            ]
        ),
        (
            "Malformed schedule data",
            "2025-12-06",
            {'tuesday': [
                {'start': '09:00'}, # Missing 'end'
                {'end': '12:00'},   # Missing 'start'
                {'start': '14:00', 'end': '15:00'} # This one is valid
            ]},
            10080 - 60, # Only the 1-hour valid block should be processed
            [
                ("2025-12-09 10:00", True),  # Should be free as interval was skipped
                ("2025-12-09 14:30", False), # Should be busy
            ]
        ),
    ]
)
def test_generate_availability(tuitions, test_name, week_start_str, schedule, expected_free_minutes, check_times):
    """
    Tests the _generate_availability method with various schedules and conditions.
    
    Args:
        tuitions: The pytest fixture for the Tuition class instance.
        test_name: A descriptive name for the test case.
        week_start_str: The Saturday start date for the week.
        schedule: The dictionary of busy times.
        expected_free_minutes: The total number of free minutes expected.
        check_times: A list of specific (datetime_str, is_free) tuples to verify.
    """
    # 1. Setup: Set the start date on the tuitions instance
    tuitions.week_start_date = datetime.fromisoformat(week_start_str)

    # 2. Execution: Run the method to get the list of free minutes
    result = tuitions._generate_availability(schedule)
    
    # 3. Assertions: Verify the results
    
    # Create a set for faster lookups of specific times
    result_set = set(result)

    # Check the total count of free minutes
    assert len(result) == expected_free_minutes, f"Failed on '{test_name}': Incorrect total free minutes."

    # Check specific time points for their expected availability
    for time_str, should_be_free in check_times:
        specific_time = datetime.fromisoformat(time_str)
        is_in_results = specific_time in result_set
        
        assert is_in_results == should_be_free, \
            f"Failed on '{test_name}': Time {time_str} should be {'free' if should_be_free else 'busy'} but was not."

def test_get_student_list(tuitions: Tuitions):
    '''
    #TODO: put pytest.mark.parametrize test cases
    '''
    print(tuitions.student_list)

def test_get_tuition_list(tuitions: Tuitions):
    '''
    #TODO: put pytest.mark.parametrize test cases
    '''
    # pprint(tuitions.raw_data)  # get raw data to save in the mock
    for tuition in tuitions.tuition_list:
        print(f"{tuition}\t{repr(tuition)}")
    # print(tuitions.student_list[0])
    # for time in tuitions.student_list[0].availability:
    #     print(time)


def test_tuition_class(tuitions: Tuitions):
    '''
    Tests if the Tuition(SessionGroup) class will run properly:
        - No Errors
        - generate correct CSP Variables list
        - generate correct CSP Domain Dictionary

    '''
    # pprint(tuitions.raw_data)
    # print(type(tuitions.raw_data))
    # print(type(tuitions.raw_data[0]))
    # pprint(tuitions.raw_data[0]['students'][0])

    for session in tuitions.csp_variables:
        print(f"{session.session_descriptor.name}, Domain len: {len(session.domain_values)}, Example: ({session.domain_values[0].strftime('%Y-%m-%d %H:%M')}, {session.domain_values[1].strftime('%Y-%m-%d %H:%M')})")





