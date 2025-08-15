'''
Testing the constraints classes
'''
import pytest
from datetime import datetime, timedelta
from personal_time_manager.csp.csp import CSP, Constraint
from personal_time_manager.sessions.prayers import Prayers
from personal_time_manager.sessions.base_session import Session

def test_NoTimeOverlapConstraint():
    wanted_week = datetime(2025, 12, 6)  # Saturday
    prayers = Prayers(wanted_week)
    # work_meetings = ["weekly_plan_saturday_meeting"]
    # lessons = ["abdullah_math1", "abdullah_math2", "omran_mila_math"]
    # personal = ["lunch_prepare", "lunch_time"]
    # others = []

    variables: list[Session] = []
    domains: dict[Session: list[datetime]] = {}

    variables.extend(prayers.csp_variables)
    domains.update(prayers.csp_domains)

    # the sessions needed to be fulfilled
    # Creating CSP framework
    csp: CSP = CSP(variables, domains)

    # Applying constraints
    for session in prayers.csp_variables:
        csp.add_constraint(NoTimeOverlapConstraint(session, timedelta(minutes=0))) # no tolerance

    # for session in work_meetings:
    #     pass #TODO:
    # for session in lessons:
    #     pass #TODO: assign the appropriate time for each lesson
    # for session in personal:
    #     pass #TODO: assign the appropriate time for each personal item
    # for session in others:
    #     pass #TODO

    # Find solution
    solution: Optional[dict[str, int]] = csp.backtracking_search()
    if solution is None:
        print("No solution found!")
    else:
        print(solution)


