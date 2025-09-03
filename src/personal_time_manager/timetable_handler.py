'''
This file is responsible to handle everything related to the output of the CSP and the Post-Process of running the CSP algorithm
'''
from datetime import datetime
from enum import Enum, auto
from typing import Optional
from personal_time_manager.database.db_handler import DatabaseHandler
from personal_time_manager.sessions.base_session import Session, SessionTime

class FailureCode(Enum):
    """ Defines the standard types of CSP run failures. """
    NO_SOLUTION = auto()
    BUILD_ERROR = auto()
    UNKNOWN_ERROR = auto()

class FailureReason(BaseModel):
    """ A structured way to represent why a CSP run failed. """
    code: FailureCode
    message: str

class TimeTable:
    """
    Handles the result of a CSP run, including timing, serialization,
    and saving the outcome to the database.
    """
    def __init__(
        self,
        input_hash: str,
        trigger_source: str,
        run_start_time: datetime,
        run_end_time: datetime,
        db_handler: DatabaseHandler,
        solution: Optional[Dict[Session, SessionTime]] = None,
        failure_reason: Optional[FailureReason] = None
    ):
        self.solution = solution
        self.failure_reason = failure_reason
        self.input_hash = input_hash
        self.trigger_source = trigger_source
        self.run_start_time = run_start_time
        self.run_end_time = run_end_time
        self.db_handler = db_handler
        
        # The duration is now calculated here, inside the class.
        self.duration_ms = int((self.run_end_time - self.run_start_time).total_seconds() * 1000)

    def handle_and_save(self):
        """
        Determines if the run was successful and saves the result to the database.
        """
        if self.solution is None:
            self._log_failed_run()
        else:
            self._log_successful_run()

    def _log_failed_run(self):
        print(f"ERROR: No solution found! (Duration: {self.duration_ms}ms)")
        sql = """
            INSERT INTO timetable_runs (run_started_at, run_duration_ms, status, input_version_hash, trigger_source, error_message)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        self.db_handler.execute_query(sql, (self.run_started_at, self.duration_ms, 'FAILED', self.input_hash, self.trigger_source, 'No valid schedule could be found.'))

    def _log_successful_run(self):
        print(f"SUCCESS: New timetable generated in {self.duration_ms}ms!")
        schedule_json = serialize_solution(self.solution)
        sql = """
            INSERT INTO timetable_runs (run_started_at, run_duration_ms, status, input_version_hash, trigger_source, solution_data)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        self.db_handler.execute_query(sql, (self.run_started_at, self.duration_ms, 'SUCCESS', self.input_hash, self.trigger_source, schedule_json))
