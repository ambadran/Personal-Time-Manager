'''
This is the script to read the json file storing all the data of the pupils regarding
'''
from datetime import datetime, timedelta, time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor
from personal_time_manager.database.db_handler import DatabaseHandler

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

@dataclass
class Student:
    first_name: str
    family_name: str
    grade: int
    status: StudentStatus

@dataclass
class Tuition(SessionDescriptor):
    students: list[Student]
    subject: Subject
    duration: timedelta

    @property
    def name(self):
        return f"Tuition(({subject}) for ({self.students}) for ({duration}))"

class Tuitions(SessionGroup):

    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

        # creating the sessions

    @property
    def csp_variables(self) -> list[Session]:
        return self.get_tuition_list_from_pkl()

    @property
    def csp_domains(self) -> dict[Session: list[datetime]]:
        return {session: session.domain_values for session in self.csp_variables}

if __name__ == "__main__":
    start_date = datetime(2025, 12, 6)  # Saturday
    tuitions = Tuitions(start_date)
    
    for session in tuitions.csp_variables:
        print(f"{session.session_descriptor.name}: {session.domain_values[0].strftime('%Y-%m-%d %H:%M')}")





