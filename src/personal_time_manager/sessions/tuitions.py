'''
* INPUTS to this Module *
Student Data are acquired from online Postegres Database that contains:
    - The amount/type of Tuition needed for each student per week
    - The NOT available time for each student during a week

* OUTPUTS from this Module *
This Module generates Inputs to CSP Framework
    - CSP Session Variable list, all the tuition classes I need to give per week
    - CSP Domain Variable Dictionary, all possible start times of each tuition class 
'''
from __future__ import annotations
from datetime import datetime, timedelta, time
from enum import Enum, auto
from pydantic import BaseModel, ConfigDict
from typing import Optional
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor
from personal_time_manager.database.db_handler import DatabaseHandler
from psycopg2.extras import RealDictRow
import logging

logger = logging.getLogger(__name__)

# Temp
# from pprint import pprint

class Subject(Enum):
    Math = auto()
    Physics = auto()
    Chemistry = auto()
    Biology = auto()
    IT = auto()
    Geography = auto()

    def __eq__(self, other: Subject) -> bool:
        return self.name == other.name

    @classmethod
    def from_string(cls, json_raw_string: str) -> Subject:
        for subject in cls:
            if json_raw_string == subject.name:
                return subject
        raise ValueError(f"Undefined subject: {json_raw_string}")

class StudentStatus(Enum): # ;)
    NONE = auto()
    Alpha = auto()
    Omega = auto()
    Sigma = auto()
    HIM = auto()

class Student(BaseModel):
    id: str # The student's unique ID from within the JSON data
    first_name: str
    first_name: str
    family_name: str
    grade: int
    cost_per_hour: float
    status: StudentStatus
    busy_intervals: list[tuple[datetime, datetime]]

    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self) -> str:
        return f"Student('{self.first_name} {self.family_name}', G{self.grade})"

class Tuition(BaseModel, SessionDescriptor):
    """
    A self-contained descriptor for a specific tuition session. 
    """
    students: list[Student]
    subject: Subject
    min_duration: timedelta
    max_duration: timedelta
    lesson_index: int # NEW: Tracks which lesson this is (1, 2, etc.)

    model_config = ConfigDict(frozen=True)

    @property
    def name(self):
        student_names = "_".join(s.first_name for s in sorted(self.students, key=lambda x: x.id))
        name = f"Tuition_{student_names}_{self.subject.name}"
        if self.lesson_index > 1: # Only add index if more than one lesson
            name += f"_{self.lesson_index}"
        return name

    # FIX: Implement a stable, value-based hash
    def __hash__(self):
        # Create a sorted, immutable tuple of student IDs
        student_ids = tuple(sorted(s.id for s in self.students))
        # Hash the combination of students, subject, and lesson index
        return hash((student_ids, self.subject, self.lesson_index))

class Tuitions(SessionGroup):
    """
    Generates all Tuition sessions for a week based on DB data. 
    """
    def __init__(self, week_start_date: datetime, db_handler: DatabaseHandler):
        super().__init__(week_start_date, db_handler)

        # Step 1: Fetch all raw data from Database
        all_students_map = self._load_all_students_from_db()
        tuition_rows = self._load_tuitions_from_db()

        # Step 2: Parse Raw data
        self.tuition_descriptors: list[Tuition] = self._create_tuition_descriptors(tuition_rows, all_students_map)

        # 3. Create the final list of Session variables
        self._csp_variables: list[Session] = []
        for tuition_descriptor in self.tuition_descriptors:
            self._csp_variables.append(
                Session(
                    session_descriptor=tuition_descriptor,
                    allowed_times=self.get_allowed_times(tuition_descriptor),
                    min_duration=self.get_min_duration(tuition_descriptor),
                    max_duration=self.get_max_duration(tuition_descriptor)
                )
            )

    def _load_all_students_from_db(self) -> Dict[str, Student]:
        """
        Fetches all students, reading basic info and admin parameters from
        their dedicated columns.
        """
        logger.info("INFO: Loading student data from database...")
        # UPDATED QUERY: Select all the necessary dedicated columns
        query = "SELECT first_name, last_name, grade, cost_per_hour, status, student_data FROM students;"
        rows = self.db_handler.fetch_all(query)
        
        students_map: Dict[str, Student] = {}
        for row in rows:
            try:
                student_json = row['student_data']
                student_id = student_json['id']
                
                # UPDATED LOGIC: Create the Student model with all fields from the DB
                students_map[student_id] = Student(
                    id=student_id,
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    grade=row['grade'],
                    cost_per_hour=row['cost_per_hour'],
                    status=StudentStatus[row['status']], # Convert string from DB to Enum
                    busy_intervals=self._generate_busy_intervals(student_json.get('availability', {}))
                )
            except (ValidationError, KeyError) as e:
                student_name = f"{row.get('first_name', 'Unknown')} {row.get('last_name', '')}".strip()
                logger.warning(f"WARNING: Skipping broken student record for '{student_name}'. Reason: {e}")
                raise ValueError()
        return students_map

    def _load_tuitions_from_db(self) -> List[Dict[str, Any]]:
        """ Fetches the definitive list of required tuitions for the week. """
        logger.info("INFO: Loading required tuitions from database...")
        query = "SELECT student_ids, subject, lesson_index, min_duration_minutes, max_duration_minutes FROM tuitions;"
        return self.db_handler.fetch_all(query)

    def _create_tuition_descriptors(self, tuition_rows: List[Dict], students_map: Dict[str, Student]) -> List[Tuition]:
        """ Creates all unique Tuition descriptors needed for the week. """
        descriptors = []
        for row in tuition_rows:
            try:
                student_ids = row['student_ids']
                current_students = [students_map[sid] for sid in student_ids if sid in students_map]
                
                if len(current_students) != len(student_ids):
                    logger.warning(f"Skipping tuition because some student IDs were not found: {student_ids}")
                    continue

                descriptor = Tuition(
                    students=current_students,
                    subject=Subject.from_string(row['subject']),
                    lesson_index=row['lesson_index'],
                    min_duration=timedelta(minutes=row['min_duration_minutes']),
                    max_duration=timedelta(minutes=row['max_duration_minutes'])
                )
                descriptors.append(descriptor)
            except (ValidationError, KeyError, ValueError) as e:
                logger.warning(f"Skipping broken tuition record. Reason: {e}")
                continue
        return descriptors

    def _generate_busy_intervals(self, availability_dict: dict) -> list[Tuple[datetime, datetime]]:
        """
        Converts the 'not available' JSON data into a list of
        concrete (start_busy, end_busy) datetime tuples for the week.
        """
        busy_intervals = []
        start_of_week_date = self.week_start_date.date()
        day_names = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']

        for day_offset, day_name in enumerate(day_names):
            current_date = start_of_week_date + timedelta(days=day_offset)
            for interval in availability_dict.get(day_name, []):
                try:
                    start_time = datetime.strptime(interval['start'], '%H:%M').time()
                    end_time = datetime.strptime(interval['end'], '%H:%M').time()
                    start_dt = datetime.combine(current_date, start_time)
                    end_dt = datetime.combine(current_date, end_time)
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                    busy_intervals.append((start_dt, end_dt))
                except (ValueError, KeyError):
                    continue
        return sorted(busy_intervals)

    # --- Implementation of SessionGroup Abstract Methods ---

    def get_allowed_times(self, tuition: Tuition) -> AllowedTimes:
        """ Calculates the common free time for all students in a tuition session. """
        week_start = self.week_start_date
        week_end = week_start + timedelta(days=7)
        free_intervals = [(week_start, week_end)]

        for student in tuition.students:
            next_free_intervals = []
            for free_start, free_end in free_intervals:
                student_free_slots = self._subtract_busy_from_interval(
                    (free_start, free_end), student.busy_intervals
                )
                next_free_intervals.extend(student_free_slots)
            free_intervals = next_free_intervals

        return AllowedTimes(free_intervals)

    def _subtract_busy_from_interval(self, free_interval: Tuple, busy_intervals: list[Tuple]) -> list[Tuple]:
        """ Helper function to poke holes in a free interval based on busy times. """
        free_start, free_end = free_interval
        remaining_slots = [(free_start, free_end)]

        for busy_start, busy_end in busy_intervals:
            new_remaining = []
            for current_start, current_end in remaining_slots:
                if busy_end <= current_start or busy_start >= current_end:
                    new_remaining.append((current_start, current_end))
                    continue
                if busy_start > current_start:
                    new_remaining.append((current_start, busy_start))
                if busy_end < current_end:
                    new_remaining.append((busy_end, current_end))
            remaining_slots = new_remaining
        return remaining_slots

    def get_min_duration(self, tuition: Tuition) -> timedelta:
        return tuition.min_duration

    def get_max_duration(self, tuition: Tuition) -> timedelta:
        return tuition.max_duration
    @property
    def csp_variables(self) -> list[Session]:
        return self._csp_variables



