'''
Main CSP Algorithm Workflow and manages constraints
'''
from typing import Optional
from personal_time_manager.csp.csp import CSP
from personal_time_manager.csp.constraints import NoTimeOverlapConstraint
from personal_time_manager.sessions.base_session import Session, SessionTime
from personal_time_manager.sessions import CSPInputs
from personal_time_manager.database.db_handler2 import DatabaseHandler #TODO: remove the 2 when db_handler is finished

def create_csp() -> CSP:
    '''
    creates the CSP framework
    '''
    #TODO: fetch the saturday of this week
    week_start_day
    db_handler = DatabaseHandler()

    # Step 1: Get the variables and domains of the CSP framework
    csp_inputs = CSPInputs(week_start_day, db_handler)

    # Step 2: Creating CSP framework
    csp = CSP(csp_inputs.variables, csp_inputs.domains)

    # Step 3: Applying Constraints classes
    csp.add_constraint(NoTimeOverlapConstraint(csp_inputs.variables))
    #TODO: add NoSameDayTuition to tuition sessions

    return csp


