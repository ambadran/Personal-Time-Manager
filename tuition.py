'''
This is the script to read the json file storing all the data of the pupils regarding
'''
from datetime import datetime, timedelta, time
from enum import Enum, auto
from dataclasses import dataclass, field
import pickle
from typing import Optional
from sessions import SessionGroup, Session, SessionDescriptor

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
    PKL_TUITION_DOMAIN_DICT_FILE_NAME = "tuition_domain_dict.pkl"

    def __init__(self, week_start_date: datetime):
        super().__init__(week_start_date)

    def get_tuition_list_from_pkl(self) -> list[Session]:
        '''
        Reads the local pkl file generated manually or from App that contains the list of all the wanted tuition in a week and the domain of each Tuition.
        
        Returns:
            list[Session]: A list of Session objects containing tuition information and their domains.
        '''
        try:
            with open(self.PKL_TUITION_DOMAIN_DICT_FILE_NAME, 'rb') as pkl_file:
                tuition_list = pickle.load(pkl_file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: File {self.PKL_TUITION_DOMAIN_DICT_FILE_NAME} not found.")
        except Exception as e:
            raise Exception(f"Error loading pickle file: {e}")

        return tuition_list

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





