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

class Subject(Enum):
    Maths = auto()
    Physics = auto()
    Chemistry = auto()
    Biology = auto()
    IT = auto()
    Geography = auto()

class StudentStatus(Enum):
    Sigma = auto()
    Omega = auto()
    Alpha = auto()
    HIM = auto()

class Student(BaseModel):
    first_name: str
    family_name: str
    grade: int
    status: StudentStatus

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

    def get_latest_db_data(self) -> list[RealDictRow]:
        return DatabaseHandler().export_all_data()

    @property
    def csp_variables(self) -> list[Session]:
        return []

    @property
    def csp_domains(self) -> dict[Session: list[datetime]]:
        return {session: session.domain_values for session in self.csp_variables}



