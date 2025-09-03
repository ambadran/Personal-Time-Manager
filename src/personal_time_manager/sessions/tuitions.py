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
from personal_time_manager.database.db_handler2 import DatabaseHandler #TODO: remove the 2 when db_handler is finished
from psycopg2.extras import RealDictRow

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
    id: str
    first_name: str
    family_name: str
    grade: int
    cost_per_hour: float
    status: StudentStatus
    # availability: list[datetime]
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

        # Step 1: Fetch all student data in a single query
        all_student_rows = self._load_student_data_from_db()

        # Step 2: Parse Raw data
        self.students: list[Student] = self._parse_students(raw_student_data)
        self.tuition_descriptors: list[Tuition] = self._create_tuition_descriptors(raw_student_data, self.students)

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

    def _load_student_data_from_db(self) -> list[RealDictRow]:
        """ Fetches all student records and their parameters in one go. """
        #TODO: put this in the logging system
        print("INFO: Loading all student data from database...")
        #TODO: update this after students table in the database is updated
        query = "SELECT id, user_id, student_data, cost_per_hour, status, min_duration_mins, max_duration_mins FROM students;"
        return self.db_handler.fetch_all(query)

    def _parse_students(self, all_student_rows: list[RealDictRow]) -> list[Student]:
        """ Parses all unique students using the real per-student admin parameters. """
        students_map: Dict[str, Student] = {}
        for row in all_student_rows:
            try:
                student_json = row['student_data']
                student_id = student_json['id'] # The ID within the JSON
                if student_id in students_map:
                    continue
                
                info = student_json['basicInfo']
                student = Student(
                    id=student_id,
                    first_name=info['firstName'],
                    family_name=info['lastName'],
                    grade=info['grade'],
                    cost_per_hour=row['cost_per_hour'], # From its own column
                    status=StudentStatus[row['status']], # From its own column
                    busy_intervals=self._generate_busy_intervals(student_json.get('availability', {})),
                    min_duration=timedelta(minutes=row['min_duration_mins']), # From its own column
                    max_duration=timedelta(minutes=row['max_duration_mins'])  # From its own column
                )
                students_map[student_id] = student

            except (ValidationError, KeyError) as e:
                student_name = row.get('student_data', {}).get('basicInfo', {}).get('firstName', 'Unknown')
                raise ValueError(f"WARNING: Skipping broken student record for '{student_name}'. Reason: {e}")
                # print(f"WARNING: Skipping broken student record for '{student_name}'. Reason: {e}")
                # continue
        return list(students_map.values())

    def _create_tuition_descriptors(self, all_student_rows: list[RealDictRow], student_list: list[Student]) -> list[Tuition]:
        """ Creates all unique Tuition descriptors needed for the week. """
        students_map = {s.id: s for s in student_list}
        tuition_list = []

        for row in all_student_rows:
            student_json = row['student_data']
            primary_student_id = student_json['id']
            primary_student = students_map.get(primary_student_id)
            if not primary_student: continue # Skip if parsing failed earlier

            for subject_info in student_json.get('subjects', []):
                try:
                    student_ids = [primary_student_id] + subject_info.get('sharedWith', [])
                    current_students = [students_map[sid] for sid in student_ids if sid in students_map]
                    lessons_count = subject_info.get('lessonsPerWeek', 1)
                    for i in range(lessons_count):
                        descriptor = Tuition(
                            students=current_students,
                            subject=Subject.from_string(subject_info['name']),
                            min_duration=primary_student.min_duration,
                            max_duration=primary_student.max_duration,
                            lesson_index=i + 1 # Add the lesson index here
                        )
                        tuition_list.append(descriptor)

                except (ValidationError, KeyError) as e:
                    raise ValueError(f"WARNING: Skipping broken tuition record for '{primary_student.first_name}'. Reason: {e}")
                    # print(f"WARNING: Skipping broken tuition record for '{primary_student.first_name}'. Reason: {e}")
                    # continue
        return tuition_list
 
    def _generate_busy_intervals(self, availability_dict: dict) -> list[Tuple[datetime, datetime]]:
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



