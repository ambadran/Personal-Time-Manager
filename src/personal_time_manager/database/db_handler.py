'''

'''
import os
import json
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

class DatabaseHandler:
    """
    Handles all interactions with the PostgreSQL database.
    """
    def __init__(self):
        load_dotenv()
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

    def get_student_by_id(self, user_id, student_id):
        """Fetches a single student's data by their ID."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT student_data FROM students WHERE user_id = %s AND id = %s;", (user_id, student_id))
                row = cur.fetchone()
                return row['student_data'] if row else None

    def _update_student_record(self, cur, user_id, student_data):
        """Helper function to update a student record within a transaction."""
        cur.execute(
            """
            INSERT INTO students (id, user_id, student_data)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET student_data = EXCLUDED.student_data;
            """,
            (student_data['id'], user_id, json.dumps(student_data))
        )

    def save_student(self, user_id, student_data):
        """Saves a student's data and handles reciprocal sharing logic."""
        student_id = student_data.get('id', str(uuid.uuid4()))
        student_data['id'] = student_id

        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 1. Get the original student data before making changes
                cur.execute("SELECT student_data FROM students WHERE id = %s;", (student_id,))
                original_student_row = cur.fetchone()
                original_student_data = original_student_row['student_data'] if original_student_row else None

                # 2. Save the primary student's new data
                self._update_student_record(cur, user_id, student_data)

                # 3. Process reciprocal sharing
                if original_student_data:
                    old_subjects = {s['name']: set(s.get('sharedWith', [])) for s in original_student_data.get('subjects', [])}
                else:
                    old_subjects = {}
                
                new_subjects = {s['name']: set(s.get('sharedWith', [])) for s in student_data.get('subjects', [])}

                all_subject_names = set(old_subjects.keys()) | set(new_subjects.keys())

                for subject_name in all_subject_names:
                    old_shared_with = old_subjects.get(subject_name, set())
                    new_shared_with = new_subjects.get(subject_name, set())

                    # Find students that were added
                    added_students = new_shared_with - old_shared_with
                    for target_student_id in added_students:
                        cur.execute("SELECT student_data FROM students WHERE id = %s;", (target_student_id,))
                        target_student_row = cur.fetchone()
                        if target_student_row:
                            target_student = target_student_row['student_data']
                            # Find the matching subject and add the source student
                            for subject in target_student.get('subjects', []):
                                if subject['name'] == subject_name:
                                    if 'sharedWith' not in subject: subject['sharedWith'] = []
                                    if student_id not in subject['sharedWith']:
                                        subject['sharedWith'].append(student_id)
                                    break
                            self._update_student_record(cur, user_id, target_student)

                    # Find students that were removed
                    removed_students = old_shared_with - new_shared_with
                    for target_student_id in removed_students:
                        cur.execute("SELECT student_data FROM students WHERE id = %s;", (target_student_id,))
                        target_student_row = cur.fetchone()
                        if target_student_row:
                            target_student = target_student_row['student_data']
                            # Find the matching subject and remove the source student
                            for subject in target_student.get('subjects', []):
                                if subject['name'] == subject_name and 'sharedWith' in subject and student_id in subject['sharedWith']:
                                    subject['sharedWith'].remove(student_id)
                                    break
                            self._update_student_record(cur, user_id, target_student)

                # 4. Update the user's is_first_sign_in flag if necessary
                cur.execute("UPDATE users SET is_first_sign_in = FALSE WHERE id = %s AND is_first_sign_in = TRUE;", (user_id,))
                
                conn.commit()
                return student_id

    # --- Other methods (signup_user, login_user, get_students, etc.) remain unchanged ---
    
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
