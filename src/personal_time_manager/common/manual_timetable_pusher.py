import json
import logging
from datetime import datetime

# Assuming your db_handler is in this path. Adjust if necessary.
from personal_time_manager.database.db_handler import DatabaseHandler
from personal_time_manager.common.logger import setup_logging

# Configure logging to see output
setup_logging()
logger = logging.getLogger(__name__)

# --- THIS TIMETABLE NOW REFLECTS YOUR EXACT MANUAL SCHEDULE ---
# A full week's schedule from Saturday, Sep 6, 2025, to Friday, Sep 12, 2025.
mock_timetable_json = """
[
  {
    "name": "Prayer-SATURDAY_FAJR",
    "category": "Prayer",
    "start_time": "2025-09-06T05:31:00",
    "end_time": "2025-09-06T05:46:00"
  },
  {
    "name": "Sleep-NIGHT",
    "category": "Sleep",
    "start_time": "2025-09-06T05:46:00",
    "end_time": "2025-09-06T09:00:00"
  },
  {
    "name": "Meal-BREAKFAST",
    "category": "Meal",
    "start_time": "2025-09-06T09:00:00",
    "end_time": "2025-09-06T09:30:00"
  },
  {
    "name": "Gym-PUSH",
    "category": "Gym",
    "start_time": "2025-09-06T10:00:00",
    "end_time": "2025-09-06T11:30:00"
  },
  {
    "name": "Prayer-SATURDAY_DHUHR",
    "category": "Prayer",
    "start_time": "2025-09-06T12:48:00",
    "end_time": "2025-09-06T13:03:00"
  },
  {
    "name": "Meal-LUNCH",
    "category": "Meal",
    "start_time": "2025-09-06T14:00:00",
    "end_time": "2025-09-06T14:45:00"
  },
  {
    "name": "Tuition_Ali_Math_1",
    "category": "Tuition",
    "start_time": "2025-09-06T15:00:00",
    "end_time": "2025-09-06T16:30:00"
  },
  {
    "name": "Tuition_Abdullah_Math_1",
    "category": "Tuition",
    "start_time": "2025-09-06T16:30:00",
    "end_time": "2025-09-06T18:00:00"
  },
  {
    "name": "Tuition_Omran_Mila_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-06T18:00:00",
    "end_time": "2025-09-06T19:30:00"
  },
  {
    "name": "Tuition_Lily_Math_1",
    "category": "Tuition",
    "start_time": "2025-09-06T19:30:00",
    "end_time": "2025-09-06T21:00:00"
  },
  {
    "name": "Tuition_Lily_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-07T16:30:00",
    "end_time": "2025-09-07T18:00:00"
  },
  {
    "name": "Tuition_Yassin_Math_1",
    "category": "Tuition",
    "start_time": "2025-09-07T18:00:00",
    "end_time": "2025-09-07T19:30:00"
  },
  {
    "name": "Tuition_Abdullah_Biology_1",
    "category": "Tuition",
    "start_time": "2025-09-07T19:30:00",
    "end_time": "2025-09-07T21:00:00"
  },
  {
    "name": "Tuition_Adham_Chemistry_1",
    "category": "Tuition",
    "start_time": "2025-09-08T16:30:00",
    "end_time": "2025-09-08T18:00:00"
  },
  {
    "name": "Tuition_Ali_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-08T18:00:00",
    "end_time": "2025-09-08T19:30:00"
  },
  {
    "name": "Tuition_Omran_Mila_Physics_2",
    "category": "Tuition",
    "start_time": "2025-09-08T19:30:00",
    "end_time": "2025-09-08T21:00:00"
  },
  {
    "name": "Tuition_Abdullah_Chemistry_1",
    "category": "Tuition",
    "start_time": "2025-09-09T16:00:00",
    "end_time": "2025-09-09T17:30:00"
  },
  {
    "name": "Tuition_Jacob_Math_1",
    "category": "Tuition",
    "start_time": "2025-09-09T17:30:00",
    "end_time": "2025-09-09T19:00:00"
  },
  {
    "name": "Tuition_Lily_Math_2",
    "category": "Tuition",
    "start_time": "2025-09-09T19:00:00",
    "end_time": "2025-09-09T20:30:00"
  },
  {
    "name": "Tuition_Yassin_Chemistry_1",
    "category": "Tuition",
    "start_time": "2025-09-09T20:30:00",
    "end_time": "2025-09-09T22:00:00"
  },
  {
    "name": "Tuition_Adham_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-10T16:30:00",
    "end_time": "2025-09-10T18:00:00"
  },
  {
    "name": "Tuition_Ali_Chemistry_1",
    "category": "Tuition",
    "start_time": "2025-09-10T18:00:00",
    "end_time": "2025-09-10T19:30:00"
  },
  {
    "name": "Tuition_Omran_Mila_Chemistry_1",
    "category": "Tuition",
    "start_time": "2025-09-10T19:30:00",
    "end_time": "2025-09-10T21:00:00"
  },
  {
    "name": "Tuition_Jacob_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-11T15:30:00",
    "end_time": "2025-09-11T17:00:00"
  },
  {
    "name": "Tuition_Yassin_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-11T17:30:00",
    "end_time": "2025-09-11T19:00:00"
  },
  {
    "name": "Tuition_Lily_Physics_2",
    "category": "Tuition",
    "start_time": "2025-09-11T19:00:00",
    "end_time": "2025-09-11T20:30:00"
  },
  {
    "name": "Tuition_Abdullah_Physics_1",
    "category": "Tuition",
    "start_time": "2025-09-11T20:30:00",
    "end_time": "2025-09-11T22:00:00"
  }
]
"""

def push_manual_timetable():
    """
    Connects to the database and inserts the mock timetable data as a new
    run with a 'MANUAL' status.
    """
    try:
        # Validate that the mock data is valid JSON before proceeding
        json.loads(mock_timetable_json)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in mock data. Please fix the syntax. Error: {e}")
        return

    db_handler = DatabaseHandler()
    now = datetime.now()

    sql = """
        INSERT INTO timetable_runs (
            run_started_at,
            run_duration_ms,
            status,
            input_version_hash,
            trigger_source,
            solution_data
        )
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    
    # These are placeholder values for a manual run
    params = (
        now,                             # run_started_at
        0,                               # run_duration_ms (instantaneous)
        'MANUAL',                        # status
        f"manual_entry_{now.isoformat()}", # input_version_hash (unique placeholder)
        "manual_push_script",            # trigger_source
        mock_timetable_json              # solution_data
    )

    print("lkajsdlkfj")
    logger.info("Attempting to push manual timetable to the database...")
    success = db_handler.execute_query(sql, params)

    if success:
        logger.info("Manual timetable successfully saved to the database!")
    else:
        logger.error("Failed to save manual timetable.")

if __name__ == "__main__":
    push_manual_timetable()
