'''
This is the script to read the json file storing all the data of the pupils regarding



'''
from time import struct_time, strftime
import time
import json
from sessions import SessionGroup, Session, SessionDescriptor
from enum import Enum, auto
from dataclasses import dataclass, field

class Subject(Enum):
    Maths = auto()
    Physics = auto()
    Chemistry = auto()
    Biology = auto()
    IT = auto()
    Geography = auto()

@dataclass
class Student:
    first_name: str
    family_name: str
    grade: int

@dataclass
class Tuition(SessionDescriptor):
    pass

 
class Tuitions(SessionGroup):
    pass


