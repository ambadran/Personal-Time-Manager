'''
This session module defines the CSP variables and domains of personal persistent times that is not defined in any of apple / google calenders.
Example is work time, my sleep time, Gym times and more
'''
from datetime import datetime, timedelta, time
from personal_time_manager.sessions.base_session import Session, SessionGroup, SessionDescriptor
from personal_time_manager.database.db_handler import DatabaseHandler
from psycopg2.extras import RealDictRow


