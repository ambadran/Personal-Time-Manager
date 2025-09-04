'''
The Highest Point of execution of this whole Program ;)

Runs `listener` logic to capture any real-time change in any of the inputs:
    - Week start date
    - Database changes
    - Calendar changes
    - Manual trigger from Admin Panel
'''
import time
import logging
from datetime import datetime

from personal_time_manager.common.logger import setup_logging
from personal_time_manager.core.triggers import Triggers
from personal_time_manager.csp.builder import CSPBuilder
from personal_time_manager.database.db_handler import DatabaseHandler
from personal_time_manager.core.timetable_handler import TimeTable, FailureReason, FailureCode

# Initiating logger, this is the only time it needs to be configured
setup_logging()

# initiating logger for this file
# This is the standard way to use the logger throughout all files
logger = logging.getLogger(__name__)

def main():
    """
    The main, persistent application loop.
    """
    db_handler = DatabaseHandler()
    triggers = Triggers(db_handler)
    
    logger.info("Application starting up. Listening for triggers...")
    while True:
        try:
            # 1. Check for triggers
            if triggers.any():
                logger.info(f"Trigger detected! Source: {triggers.source}")

                # Ensure those exist for the finally block
                solution = None
                failure = None
                csp_builder = None

                # start timer
                start_time = datetime.now()

                try:
                    # 2. Build and run the CSP
                    csp_builder = CSPBuilder(db_handler)
                    csp = csp_builder.csp
                    solution = csp.backtracking_search()

                    if solution is None:
                        failure = FailureReason(code=FailureCode.NO_SOLUTION, message="No valid schedule could be found.")

                except Exception as e:
                    # Catch any other error during the build or search
                    logger.critical(f"A CRITICAL ERROR occurred: {e}")
                    failure = FailureReason(code=FailureCode.BUILD_ERROR, message=str(e))

                finally:
                    end_time = datetime.now()
                    
                    # 3. Handle the output cleanly via the TimeTable class
                    timetable_result = TimeTable(
                        solution=solution,
                        failure_reason=failure,
                        input_hash=csp_builder.csp_inputs.unique_identifier if csp_builder else 'hash_failed_during_build',
                        trigger_source=triggers.source,
                        run_start_time=start_time,
                        run_end_time=end_time,
                        db_handler=db_handler
                    )
                    timetable_result.handle_and_save()
            
            # Wait before checking for triggers again
            time.sleep(10)
        
        except KeyboardInterrupt:
            logger.info("\nShutting down listener...")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}")
            time.sleep(30) # Wait a bit before retrying on major errors

if __name__ == "__main__":
    # run by `python -m personal_time_manager` ;)
    main()
