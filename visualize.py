import pandas as pd
from datetime import datetime, timedelta
from csp import CSP
from constraints import NoTimeOverlapConstraint
from sessions import Session
from prayers import Prayers
import time
from typing import Optional

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
schedule_dict: Optional[dict[str, int]] = csp.backtracking_search()
if schedule_dict is None:
    print("No solution found!")
else:
    print(schedule_dict)


# Build a flat list of events
rows = []
for session, start in schedule_dict.items():
    rows.append({
        "Name": session.session_descriptor.name,
        "Start": start.strftime("%Y-%m-%d %H:%M"),
        "Duration (min)": session.base_duration
    })

# Turn it into a DataFrame
df = pd.DataFrame(rows).sort_values("Start")

# Show it
print(df.to_string(index=False))
