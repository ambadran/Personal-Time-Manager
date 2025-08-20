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
from datetime import datetime, timedelta, time
from enum import Enum, auto
from pydantic import BaseModel
from typing import Optional
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor
from personal_time_manager.database.db_handler import DatabaseHandler
from psycopg2.extras import RealDictRow

# temp
from pprint import pprint

class Subject(Enum):
    Maths = auto()
    Physics = auto()
    Chemistry = auto()
    Biology = auto()
    IT = auto()
    Geography = auto()

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
    availability: list[datetime]

    def __eq__(self) -> bool:
        return self.id == self.id
    
    def __repr__(self) -> str:
        return f"Student(\"{self.first_name} {self.family_name}\", grade={self.grade})"

class Tuition(BaseModel, SessionDescriptor):
    students: list[Student]
    subject: Subject
    duration: timedelta

    @property
    def name(self):
        return f"Tuition(({subject}) for ({self.students}) for ({duration}))"

class Tuitions(SessionGroup):
    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        # Step 1: Get raw json data from Database
        self.raw_data = self.get_latest_db_data()

        # Step 2: Parse Raw data
        self.student_list: list[Student] = self.get_student_list()
        self.tuition_list: list[Tuition] = self.get_tuition_list()

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

    def _generate_availability(self, availability_dict: dict) -> list[datetime]:
        '''
        Generates a list of all available one-minute datetime objects for a given week.

        Args:
            availability_dict: A dictionary with days of the week as keys and lists
                               of busy time intervals as values.

        Returns:
            A list of datetime objects, each representing a single minute
            of free time during the week.
        '''
        # --- 1. Pre-process busy intervals into a list of datetime tuples ---
        busy_intervals = []
        # Use the .date() part of the start date to ensure we begin at midnight
        start_of_week_date = self.week_start_date.date()
        
        # Define the order of days for a week starting on Saturday
        day_names = ['saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday']

        for day_offset, day_name in enumerate(day_names):
            current_date = start_of_week_date + timedelta(days=day_offset)
            
            # Process each busy block for the current day
            for interval in availability_dict.get(day_name, []):
                try:
                    start_time = datetime.strptime(interval['start'], '%H:%M').time()
                    end_time = datetime.strptime(interval['end'], '%H:%M').time()

                    start_dt = datetime.combine(current_date, start_time)
                    
                    # IMPORTANT: Handle overnight intervals (e.g., 22:00 to 05:00)
                    # If the end time is on the next day, add a day to the end datetime
                    if end_time <= start_time:
                        end_dt = datetime.combine(current_date + timedelta(days=1), end_time)
                    else:
                        end_dt = datetime.combine(current_date, end_time)
                    
                    busy_intervals.append((start_dt, end_dt))
                except (KeyError, ValueError):
                    # Skip any malformed interval data
                    continue

        # --- 2. Iterate through every minute of the week and find free slots ---
        free_minutes = []
        start_of_week_dt = datetime.combine(start_of_week_date, time.min)
        
        # A week has 7 days * 24 hours/day * 60 minutes/hour = 10,080 minutes
        for minute_offset in range(10080):
            current_minute = start_of_week_dt + timedelta(minutes=minute_offset)
            
            is_busy = False
            # Check if the current minute falls within any of the busy intervals
            for start_busy, end_busy in busy_intervals:
                if start_busy <= current_minute < end_busy:
                    is_busy = True
                    break  # Minute is busy, no need to check other intervals
            
            if not is_busy:
                free_minutes.append(current_minute)
                
        return free_minutes

    def get_tuition_list(self) -> list[Tuition]:
        '''
        this method REQUIRES self.student_list to be defined properly
        return list of all tuitions to be given in a week 
        '''
        # Step 1: get each student dictionary
        raw_student_dict_list: list[dict] = []
        for user in self.raw_data:
            for student_dict in user['students']:
                raw_student_dict_list.append(student_dict)

        # Step 2: create the Student instance for each student dict
        tuition_list: list[Tuition] = []
        for raw_student_dict in raw_student_dict_list:

            for subject in raw_student_dict['subjects']:
                #TODO: TEST new DB code to make sure it doesn't cause any frontend/backend bugs and output the correct sharedStudent list with the shared student in both lists
                pass

        return tuition_list

    @property
    def csp_variables(self) -> list[Session]:
        return []

    @property
    def csp_domains(self) -> dict[Session: list[datetime]]:
        return {session: session.domain_values for session in self.csp_variables}



