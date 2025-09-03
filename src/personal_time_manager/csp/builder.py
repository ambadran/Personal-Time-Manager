'''
Main CSP Algorithm Workflow and manages constraints
'''
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from personal_time_manager.csp.csp import CSP
from personal_time_manager.csp.constraints import NoTimeOverlapConstraint, NoSameDayTuition
from personal_time_manager.sessions import CSPInputs
from personal_time_manager.sessions.base_session import Session, SessionTime
from personal_time_manager.database.db_handler2 import DatabaseHandler #TODO: remove the 2 when db_handler is finished
from personal_time_manager.common.config import START_OF_WEEK_DAY_INDEX, ALGORITHM_TRIGGER_DAY_INDEX

class CSPBuilder:
    '''
    This class is solely made to generate the main `CSP` variable that is capable of generating the Perfect Timetable ;D
    All CSP inputs are created by the `CSPInputs` class in the Session builder module. It handles all that fuss
    This class just get the inputs ready made input them to the CSP as well as the other input the CSP needs.
    Which is processing the `Constraints` objects into the csp for the right variables

    the db_handler is passed to this class, it's is used in the most upper level of this Program as a `listener` to any updates in DB
    '''
    def __init__(self, db_handler: DatabaseHandler, week_start_day: Optional[datetime] = None):
        '''
        if no specific datetime is inserted then automatically fall back to this week's Saturday
        unless it's Friday, then run the next week's
        '''
        #### EXTERNAL INPUTS ####
        # Preparing inputs to CSPInputs (there are more inputs to CSPInputs(like apis), but these must come from outside them)
        self.db_handler = db_handler
        self.week_start_day = week_start_date or self._get_default_week_start()
        #########################

        # Step 1: Get the variables and domains of the CSP framework
        self.csp_inputs = CSPInputs(self.week_start_day, self.db_handler)

        # Step 2: Creating CSP framework
        csp = CSP(self.csp_inputs.variables, self.csp_inputs.domains) # :D

        # Step 3: Applying Constraints classes
        # The first and most important
        csp.add_constraint(NoTimeOverlapConstraint(csp_inputs.variables))
        # The NoSameDayTuition constraing
        for group in self.get_tuition_by_subject():
            if len(group) > 1:
                csp.add_constraint(NoSameDayTuition(group))

        #### OUTPUT ######
        self.csp: CSP = csp

    def _get_tuitions_by_group(self) -> list[list[Session]]:
        """ Groups tuition sessions to apply constraints. """
        tuitions_by_group = defaultdict(list)
        for session in self.csp_inputs.variables:
            if isinstance(session.session_descriptor, Tuition):
                # Use the descriptor's hash to group identical tuitions
                # (same students and subject)
                tuitions_by_group[hash(session.session_descriptor)].append(session)
        return list(tuitions_by_group.values())

    def _get_default_week_start(self) -> datetime:
        """
        Calculates the start of the week using the class-level constants.
        """
        today = datetime.now()
        
        # If today is the trigger day (Friday) or later, plan for next week
        if today.weekday() >= self.ALGORITHM_TRIGGER_DAY_INDEX:
            # Find the upcoming Saturday
            days_until_saturday = (self.START_OF_WEEK_DAY_INDEX - today.weekday() - 1 + 7) % 7
            start_date = today + timedelta(days=days_until_saturday + 1)
        else: # Otherwise, plan for the current week
            # Find the most recent Saturday
            days_since_saturday = (today.weekday() - self.START_OF_WEEK_DAY_INDEX + 7) % 7
            start_date = today - timedelta(days=days_since_saturday)
            
        return start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    

