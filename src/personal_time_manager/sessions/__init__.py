'''
This is the main workflow of the Session module.
It generates ALL CSP variables and CSP domains with all the needed preprocessing!
'''
from datetime import datetime
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.tuitions import Tuitions
from personal_time_manager.sessions.fixed_activities import FixedActivities
from personal_time_manager.sessions.apple_google_calendar import CalendarActivities
from personal_time_manager.sessions.base_session import Session, SessionTime

#TOOD: make __all__ for base datatypes

def generate_csp_vars_and_domains(week_start_date: datetime) -> tuple[list[Session], dict[Session, list[SessionTime]]]:
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
        csp_domains[session] = SessionTime.from_raw_data(session)
        if not csp_domains[session]:
            raise ValueError(f"No domain values generated for {session}")

    return csp_variables, csp_domains

