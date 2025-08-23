'''
Testing Main CSP framework
'''
import pandas as pd
from datetime import datetime, timedelta
import pytest
from personal_time_manager.csp.csp import CSP
from personal_time_manager.csp.constraints import NoTimeOverlapConstraint
from personal_time_manager.sessions.base_session import Session
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.tuitions import Tuitions

def test_csp_complete_workflow(prayers: Prayers, tuitions: Tuitions):
    '''
    Testing the complete workflow by bringing mock sessions of all defined types and making sure the whole algorithm 
        - Inputs ALL (Sessions) Properly
        - Outputs A Timetable


    if successful will visualize the timetable clearly
    use
    pytest -rA to make the stdout is shown
    '''
    # Step 1: Create the CSP Variable list
    variables: list[Session] = []
    variables.extend(prayers.csp_variables)
    variables.extend(tuitions.csp_variables)

    # Step 2: Create the CSP Domain Dictionary
    domains: dict[Session: list[datetime]] = {}
    domains.update(prayers.csp_domains)
    domains.update(tuitions.csp_domains)

    # Step 3: Creating CSP framework
    csp: CSP = CSP(variables, domains)

    # Step 4: Applying Constraints classes
    for session in prayers.csp_variables:
        csp.add_constraint(NoTimeOverlapConstraint(session, timedelta(minutes=0))) # no tolerance
    for session in tuitions.csp_variables:
        csp.add_constraint(NoTimeOverlapConstraint(session, timedelta(minutes=10))) # tolerance is


    # Step 5: Execute DP Algorithm to find solution ;D
    solution: Optional[dict[str, int]] = csp.backtracking_search()
    if solution is None:
        print("No solution found!")
        assert False
    else:  # will print proper in the test_visualize
        # Build a flat list of events
        rows = []
        for session, start in solution.items():
            rows.append({
                "Name": session.session_descriptor.name,
                "Start": start.strftime("%Y-%m-%d %H:%M"),
                "Duration (min)": session.base_duration
            })

        # Turn it into a DataFrame
        df = pd.DataFrame(rows).sort_values("Start")

        # Show it
        print(df.to_string(index=False))


def test_output_timetable():
    '''
    Validates the output timetable form the CSP is correct.

    Validation Points:
    1- 
    '''
    pass




