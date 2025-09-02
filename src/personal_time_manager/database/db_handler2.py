'''
This is the new and improved db_handler
I don't want to re-rewrite the original db_handler just yet.

I still need to seperate the efficienttutor backend from the CSP framework and make each one their own repository
'''
import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

class DatabaseHandler:
    """
    Handles all interactions with the PostgreSQL database using a connection pool.
    """
    _pool = None

    def __init__(self):
        if DatabaseHandler._pool is None:
            load_dotenv()
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set.")
            
            try:
                # Create a connection pool. minconn=1, maxconn=5
                DatabaseHandler._pool = pool.SimpleConnectionPool(1, 5, database_url)
                print("INFO: Database connection pool created successfully.")
            except psycopg2.OperationalError as e:
                raise ConnectionError(f"Database connection pool failed: {e}")

    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """ Fetches a single row from the database. """
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchone()
        except Exception as e:
            print(f"ERROR: Database fetch_one failed: {e}")
            return None
        finally:
            if conn:
                self._pool.putconn(conn)

    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """ Fetches all rows for a given query. """
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as e:
            print(f"ERROR: Database fetch_all failed: {e}")
            return []
        finally:
            if conn:
                self._pool.putconn(conn)

    def execute_query(self, query: str, params: Optional[tuple] = None) -> bool:
        """ Executes a query that modifies data (INSERT, UPDATE, DELETE). """
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"ERROR: Database execute_query failed: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._pool.putconn(conn)

    def fetch_overlap_rules(self) -> Dict[str, List[str]]:
            """
            Fetches all overlap rules and formats them into a dictionary
            where keys are hosts and values are a list of interrupters.
            e.g., {'Gym': ['Prayer'], 'Tuition': ['Prayer']}
            """
            print("INFO: Loading overlap rules from database...")
            query = "SELECT host_category, interrupter_category FROM activity_overlap_rules;"
            rows = self.fetch_all(query)

            rules = {}
            for row in rows:
                host = row['host_category']
                interrupter = row['interrupter_category']
                if host not in rules:
                    rules[host] = []
                rules[host].append(interrupter)
            return rules

