import pandas as pd
import time
from constraints import solution as schedule_dict

# Suppose your schedule dict is of the form:
#   { session_obj: struct_time, … }
# and each session_obj has .name and .base_duration (in minutes).

# Build a flat list of events
rows = []
for session, start in schedule_dict.items():
    rows.append({
        "Name": session.name,
        "Start": time.strftime("%Y-%m-%d %H:%M", start),
        "Duration (min)": session.base_duration
    })

# Turn it into a DataFrame
df = pd.DataFrame(rows).sort_values("Start")

# Show it
print(df.to_string(index=False))
