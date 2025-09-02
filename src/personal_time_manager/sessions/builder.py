'''
This is the main workflow of the Session module.
It generates ALL CSP variables and CSP domains with all the needed preprocessing!
'''
import json
import hashlib
from datetime import datetime
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.tuitions import Tuitions
from personal_time_manager.sessions.fixed_activities import FixedActivities
from personal_time_manager.sessions.apple_google_calendar import CalendarActivities
from personal_time_manager.sessions.base_session import Session, SessionTime
from personal_time_manager.database.db_handler2 import DatabaseHandler #TODO: remove the 2 when db_handler is finished

class CSPInputs:
    '''
    This class is the main heart of the Session Modules.
    It is responsible to run the main routine to run all the session Modules
    It creates the CSP ALgorithm Framework inputs:
    - CSP Variables (list[Session])
    - CSP Domains (dict[Session, list[SessionTime]])

    It also creates a unique fingerprint for all the given inputs.
    This is extremely important to relate with output timetable later ;)
    '''
    def __init__(self, week_start_date: datetime, db_handler: DatabaseHandler):

        ### INPUTS ###
        overlap_rules = db_handler.fetch_overlap_rules()
        prayers = Prayers(week_start_date, db_handler)
        tuitions = Tuitions(week_start_date, db_handler)
        fixed_activities = FixedActivities(week_start_date, db_handler) 
        calendar_activities = CalendarActivities(week_start_date, db_handler)
        ##############

        # Step 1: Create list of ALL CSP variables `Session`
        csp_variables: list[Session] = []
        csp_variables.extend(prayers.csp_variables)
        csp_variables.extend(tuitions.csp_variables)
        csp_variables.extend(fixed_activities.csp_variables)
        csp_variables.extend(calendar_activities.csp_variables)

        # Step 2: Create the CSP Variable list
        for session in csp_variables:
            session.populate_overlap_types(overlap_rules) # First, set the allowed types
        
        for session in csp_variables:  # finish the setup
            session.get_allowed_to_overlap(csp_variables)

        # Step 3: Create the CSP Domain Dictionary
        csp_domains: dict[Session: list[datetime]] = {}
        for session in csp_variables:
            csp_domains[session] = SessionTime.from_raw_data(session)
            if not csp_domains[session]:
                raise ValueError(f"No domain values generated for {session}")

        ### OUTPUTS ####
        self._overlap_rules = overlap_rules
        self.variables: list[Session] = csp_variables
        self.domains: dict[Session, list[SessionTime]] = csp_domains
        self.unique_identifier: str = self.generate_input_hash()
        ##############

    def generate_input_hash(self, db_handler) -> str:
        """
        Fetches all relevant settings and data, creates a canonical representation,
        and returns a SHA-256 hash of that data.
        """
        #TODO: hash the csp_variables and csp_domain somehow
