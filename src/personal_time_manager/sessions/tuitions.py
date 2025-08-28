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
from pydantic import BaseModel
from typing import Optional
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor, SessionPriority
from personal_time_manager.database.db_handler import DatabaseHandler
from psycopg2.extras import RealDictRow

# Temp
# from pprint import pprint

#TODO: all these defaults should be set from admin panel in frontend
DEFAULT_COST_PER_HOUR = 6
DEFAULT_DURATION = timedelta(minutes=90)

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

DEFAULT_STUDENT_STATUS = StudentStatus.NONE

class Student(BaseModel):
    id: str
    first_name: str
    family_name: str
    grade: int
    cost_per_hour: float
    status: StudentStatus
    availability: list[datetime]

    def __eq__(self, other) -> bool:
        return self.id == other.id
    
    def __repr__(self) -> str:
        return f"Student(\"{self.first_name} {self.family_name}\", grade={self.grade})"

    def __str__(self) -> str:
        return f"<{self.first_name} {self.family_name}, G{self.grade}>"

class Tuition(BaseModel, SessionDescriptor):
    students: list[Student]
    subject: Subject
    duration: timedelta

    @property
    def name(self):
        tuition_name = ""
        for student in self.students:
            tuition_name += f"{student.first_name}_"
        tuition_name += self.subject.name

        return tuition_name

    def __eq__(self, other: Tuition) -> bool:
        '''
        This function is mainly used to test whether a tuition class was already created or not.
        This is especially important to prevent duplicate tuition class for shared classes
        '''
        for student in self.students:
            if student not in other.students:
                return False

        for student in other.students:
            if student not in self.students:
                return False

        return self.subject == other.subject

    def __repr__(self) -> str:
        return f"Tuition({self.subject.name}, {[s.first_name for s in self.students]}, {self.duration})"

    def __str__(self) -> str:
        return f"{self.name} ({self.duration})"


class Tuitions(SessionGroup):
    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        # Step 1: Get raw json data from Database
        self.raw_data = self.get_latest_db_data()

        # Step 2: Parse Raw data
        self.student_list: list[Student] = self.get_student_list()
        self.tuition_list: list[Tuition] = self.get_tuition_list()

        # Step 3: Create CSP variable list
        self._csp_variables: list[Session] = []
        for tuition in self.tuition_list:
            self._csp_variables.append(
                Session(
                    session_descriptor=tuition, 
                    base_duration=tuition.duration, 
                    domain_values=self.get_domain_times_for_tuition(tuition),
                    priority=SessionPriority.HIGH))

    def get_latest_db_data(self) -> list[RealDictRow]:
        '''return all raw data from database'''
        return DatabaseHandler().export_all_data()

    def get_student_list(self) -> list[Student]:
        '''
        return list of all registered students 

        Remember the input 'available' mentions that opposite.
        It provides the times where the student is NOT free
        (It was designed like that because it's easier to input 
        and to encourage give me more time to work with ;) )
        '''
        try:
            # Step 1: get each student dictionary
            raw_student_dict_list: list[dict] = []
            for user in self.raw_data:
                for student_dict in user['students']:
                    raw_student_dict_list.append(student_dict)

            # Step 2: create the Student instance for each student dict
            student_list: list[Student] = []
            for raw_student_dict in raw_student_dict_list:

                id = raw_student_dict['id']
                first_name = raw_student_dict['basicInfo']['firstName']
                family_name = raw_student_dict['basicInfo']['lastName']
                grade = raw_student_dict['basicInfo']['grade']
                #TODO: should get this from future admin frontend -> admin database
                cost_per_hour = 6
                #TODO: should get this from future admin frontend -> admin database
                status = StudentStatus.NONE 
                availability = self._generate_availability(raw_student_dict['availability'])
                student_list.append(Student(id=id,
                                            first_name=first_name,
                                            family_name=family_name,
                                            grade=grade,
                                            cost_per_hour=cost_per_hour,
                                            status=status,
                                            availability=availability))

            return student_list

        except KeyError:
            # pprint(self.raw_data)
            raise KeyError(f"Propably some json key not found: {e}")



    def get_student_by_id(self, id: str) -> Optional[Student]:
        '''
        return student from self.student_list by id
        '''
        for student in self.student_list:
            if student.id == id:
                return student

    def _generate_availability(self, availability_dict: dict) -> list[datetime.datetime]:
        '''
        Generates a list of all available one-minute datetime objects for a given week.

        Args:
            availability_dict: A dictionary with days of the week as keys and lists
                               of busy time intervals as values.

        Returns:
            A list of datetime.datetime objects, each representing a single minute
            of free time during the week.
        '''
        busy_intervals = []
        start_of_week_date = self.week_start_date.date()
        day_names = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']

        # --- 1. Generate intervals for the single target week ---
        for day_offset, day_name in enumerate(day_names):
            current_date = start_of_week_date + timedelta(days=day_offset)
            for interval in availability_dict.get(day_name, []):
                if 'start' not in interval or 'end' not in interval:
                    continue

                try:
                    start_time = datetime.strptime(interval['start'], '%H:%M').time()
                    end_time = datetime.strptime(interval['end'], '%H:%M').time()

                    start_dt = datetime.combine(current_date, start_time)
                    end_dt = datetime.combine(current_date + timedelta(days=1 if end_time <= start_time else 0), end_time)
                    
                    busy_intervals.append((start_dt, end_dt))
                except ValueError:
                    continue

        # --- 2. **FIX**: Explicitly handle the Friday-to-Saturday wrap-around ---
        # Any overnight event on Friday also makes the Saturday of that same week busy.
        for interval in availability_dict.get('friday', []):
            if 'start' not in interval or 'end' not in interval:
                continue
            try:
                start_time = datetime.strptime(interval['start'], '%H:%M').time()
                end_time = datetime.strptime(interval['end'], '%H:%M').time()

                # If it's an overnight interval, add a corresponding busy block to Saturday morning
                if end_time <= start_time:
                    wrap_around_start = datetime.combine(start_of_week_date, time.min)
                    wrap_around_end = datetime.combine(start_of_week_date, end_time)
                    busy_intervals.append((wrap_around_start, wrap_around_end))
            except ValueError:
                continue

        # --- 3. Iterate through the week and find free slots ---
        free_minutes = []
        start_of_week_dt = datetime.combine(start_of_week_date, time.min)
        
        for minute_offset in range(10080):
            current_minute = start_of_week_dt + timedelta(minutes=minute_offset)
            is_busy = False
            for start_busy, end_busy in busy_intervals:
                if start_busy <= current_minute < end_busy:
                    is_busy = True
                    break
            
            if not is_busy:
                free_minutes.append(current_minute)
                
        return free_minutes

    def get_tuition_list(self) -> list[Tuition]:
        '''
        this method REQUIRES self.student_list to be defined properly
        return list of all tuitions to be given in a week 
        '''
        try:
            # Step 1: get each student dictionary
            raw_student_dict_list: list[dict] = []
            for user in self.raw_data:
                for student_dict in user['students']:
                    raw_student_dict_list.append(student_dict)

            # Step 2: create the Student instance for each student dict
            tuition_list: list[Tuition] = []
            for raw_student_dict in raw_student_dict_list:

                for subject in raw_student_dict['subjects']:

                    # Step 1: Get Subject Instance from Json data
                    subject_obj = Subject.from_string(subject['name'])

                    # Step 2: complete shareWith if there is any other students to add 
                    students_list = [self.get_student_by_id(raw_student_dict['id'])]
                    for student_id in subject['sharedWith']:
                        students_list.append(self.get_student_by_id(student_id))

                    # Step 3: Get duration 
                    #TODO

                    # Step 4: Create the proper amount of lessons per week
                    new_tuition = Tuition(
                                        students=students_list,
                                        subject=subject_obj,
                                        duration=DEFAULT_DURATION
                                            )
                    if new_tuition not in tuition_list:
                        for tuition_num in range(subject['lessonsPerWeek']):
                            tuition_list.append(new_tuition)

            return tuition_list

        except KeyError as e:
            # pprint(self.raw_data)
            raise KeyError(f"Propably some json key not found: {e}")

    def get_domain_times_for_tuition(self, tuition: Tuition) -> list[datetime]:
        '''
        return list of all the allowed minutes for this specific Tuition
        '''
        # Step 1: get a list of set for each student
        allowed_times_each_student: list[set[datetime]] = []
        for student in tuition.students:
            allowed_times_each_student.append(set(student.availability))

        # Step 2: Union all the sets ;D
        big_set = allowed_times_each_student[0]
        for time_set in allowed_times_each_student[1:]:
            big_set &= time_set

        # Step 3: return ordered list
        return sorted(big_set)

    @property
    def csp_variables(self) -> list[Session]:
        return self._csp_variables

    @property
    def csp_domains(self) -> dict[Session: list[datetime]]:
        #TODO: make a ._csp_domains like .csp_variables
        # return {session: session.domain_values for session in self.csp_variables}



