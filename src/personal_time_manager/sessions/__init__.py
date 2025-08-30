'''

'''
from datetime import datetime
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.tuitions import Tuitions
from personal_time_manager.sessions.admin_panel import FixedActivities
from personal_time_manager.apple_google_calender import WorkMeetings, OtherActivities

#TOOD: make __all__ for base datatypes

def generate_csp_vars_and_domains(week_start_date: datetime) -> list[Session], dict[Session, list[SessionTime]]:
    '''

    '''
    # Step 1: Create list of ALL CSP variables `Session`
    prayers = Prayers(week_start_date)
    tuitions = Tuitions(week_start_date)
    fixed_activities = FixedActivities(week_start_date) 
    calendar_activities = CalendarActivities(week_start_date)
    csp_variables: list[Session] = []
    csp_variables.extend(prayers.csp_variables)
    csp_variables.extend(tuitions.csp_variables)
    csp_variables.extend(fixed_activities.csp_variables)
    csp_variables.extend(calendar_activities.csp_variables)

    # Step 2: Create the CSP Variable list
    for session in csp_variables:  # finish the setup
        session.get_allowed_to_overlap(csp_variables)

    # Step 3: Create the CSP Domain Dictionary
    #TODO generate the domain values after adding the new overlapping session with its time domain (after recursion) and taking it into consideration and taking own allowed_times into consideration as well as durations
    csp_domains: dict[Session: list[datetime]] = {}
    for session in csp_variables:
        csp_domains[session] = SessionTime.from_raw_data(
                                            session.allowed_times,
                                            session.min_duration,
                                            session.max_duration,
                                            session.allowed_to_overlap)

    return csp_variables, csp_domains

