'''
Main CSP Algorithm Workflow
'''
from personal_time_manager.csp.csp import CSP
from personal_time_manager.csp.constraints import NoTimeOverlapConstraint
from personal_time_manager.sessions.base_session import Session, SessionTime
from personal_time_manager.sessions import generate_csp_vars_and_domains

def run_csp() -> Optional[dict[Session: SessionTime]]:
    '''
    Runs the main Algorithm with all its inputs
    '''
    # Step 1: Get the variables and domains of the CSP framework
    csp_variables, csp_domains = generate_csp_vars_and_domains()

    # Step 2: Creating CSP framework
    csp: CSP = CSP(csp_variables, csp_domains)

    # Step 3: Applying Constraints classes
    for session in prayers.csp_variables:
        csp.add_constraint(NoTimeOverlapConstraint(session, timedelta(minutes=0))) # no tolerance
    for session in tuitions.csp_variables:
        csp.add_constraint(NoTimeOverlapConstraint(session, timedelta(minutes=10))) # tolerance is
        # csp.add_constraint(NoSameDayTuition(session))  #TODO:

    # Step 4: Execute DP Algorithm to find solution ;D
    solution: Optional[dict[str, int]] = csp.backtracking_search()
    if solution is None:
        #TODO: what do I do if no timetable possible?!?
        print("No solution found!")
        raise ValueError("CSP no solution found!")

    else:  # will print proper in the test_visualize
        return solution


