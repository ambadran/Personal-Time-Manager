'''
The Highest Point of execution of this whole Program ;)

Runs `listener` logic to capture any real-time change in any of the inputs:
    - Week start date
    - Database changes
    - Calendar changes
    - Manual trigger from Admin Panel
'''
from typing import Optional
from datetime import datetime
from personal_time_manager.csp.builder import CSPBuilder
from personal_time_manager.database.db_handler import DatabaseHandler
from personal_time_manager.sessions.base_session import Session, SessionTime
# from personal_time_manager.sessions.apple_google_calendar import GoogleCalendarListener, AppleCalendarListener

def Main:
    '''
    Finally, The Main Routine ;)
    '''
    triggers = Triggers()

    while True:

        # Main trigger poll Logic
        if triggers.any():
            #TODO: log

            # Start timing
            run_start_time = datetime.now()

            # Step 1: Make a Builder to create the CSP framework ;)
            csp_builder = CSPBuilder()

            # Step 2: get the CSP Framework ;)
            csp = csp_builder.csp

            # Step 3: Execute DP Algorithm to find solution ;D
            solution: TimeTable = TimeTable(csp.backtracking_search(), trigger.source, csp_builder.unique_identifier, )

            # Step 4: Handle the output 
            TimeTable.handle()

        time.sleep(10)

if __name__ == '__main__':
    Main()
