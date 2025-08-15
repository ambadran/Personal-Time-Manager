'''

'''
import os
import json
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseHandler:
    """
    Handles all interactions with the PostgreSQL database.
    """
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set.")

    def _get_connection(self):
        """Establishes and returns a new database connection."""
        try:
            return psycopg2.connect(self.database_url)
        except psycopg2.OperationalError as e:
            print(f"!!! DATABASE CONNECTION FAILED: {e} !!!")
            return None

    def check_connection(self):
        """Checks if a connection to the database can be established."""
        conn = self._get_connection()
        if conn:
            conn.close()
            return True
        return False

    def signup_user(self, email, password):
        """Creates a new user in the database."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
                if cur.fetchone():
                    return None, "User with this email already exists"

                new_user_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO users (id, email, password, is_first_sign_in) VALUES (%s, %s, %s, %s);",
                    (new_user_id, email, password, True)
                )
                conn.commit()
                
                user_data = {"id": new_user_id, "email": email, "isFirstSignIn": True}
                return user_data, "Signup successful"

    def login_user(self, email, password):
        """Authenticates a user against the database."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
                user = cur.fetchone()

                if user and user['password'] == password:
                    return {
                        "id": str(user['id']), 
                        "email": user['email'], 
                        "isFirstSignIn": user['is_first_sign_in']
                    }, "Login successful"
                
                return None, "Invalid email or password"

    def get_students(self, user_id):
        """Retrieves all students for a given user."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT student_data FROM students WHERE user_id = %s;", (user_id,))
                return [row['student_data'] for row in cur.fetchall()]

    def save_student(self, user_id, student_data):
        """Saves (inserts or updates) a student's data."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                student_id = student_data.get('id', str(uuid.uuid4()))
                student_data['id'] = student_id
                
                cur.execute(
                    """
                    INSERT INTO students (id, user_id, student_data)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET student_data = EXCLUDED.student_data;
                    """,
                    (student_id, user_id, json.dumps(student_data))
                )
                
                cur.execute("UPDATE users SET is_first_sign_in = FALSE WHERE id = %s AND is_first_sign_in = TRUE;", (user_id,))
                conn.commit()
                return student_id

    def delete_student(self, user_id, student_id):
        """Deletes a student from the database."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM students WHERE id = %s AND user_id = %s;", (student_id, user_id))
                conn.commit()
                return cur.rowcount > 0

    def export_all_data(self):
        """Exports all users and their students as a JSON object."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, email, is_first_sign_in FROM users;")
                users = cur.fetchall()
                
                cur.execute("SELECT user_id, student_data FROM students;")
                students_rows = cur.fetchall()
                
                students_by_user = {}
                for row in students_rows:
                    user_id_str = str(row['user_id'])
                    if user_id_str not in students_by_user:
                        students_by_user[user_id_str] = []
                    students_by_user[user_id_str].append(row['student_data'])

                for user in users:
                    user_id_str = str(user['id'])
                    user['id'] = user_id_str
                    user['students'] = students_by_user.get(user_id_str, [])
                
                return users
