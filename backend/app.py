
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- Database Connection ---
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        # This error is critical. We log it and will let the calling function handle it.
        print(f"!!! DATABASE CONNECTION FAILED: {e} !!!")
        return None

# --- API Endpoints ---

@app.route('/', methods=['GET'])
def health_check():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 503 # Service Unavailable
    conn.close()
    return jsonify({"status": "ok", "message": "Backend is running and database is connected"}), 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database service is currently unavailable"}), 503
        
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
            if cur.fetchone():
                return jsonify({"error": "User with this email already exists"}), 409

            new_user_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO users (id, email, password, is_first_sign_in) VALUES (%s, %s, %s, %s);",
                (new_user_id, email, password, True)
            )
            conn.commit()
            print(f"New user signed up: {email} (ID: {new_user_id})")
            
            return jsonify({
                "message": "Signup successful",
                "user": {"id": new_user_id, "email": email, "isFirstSignIn": True}
            }), 201
    except psycopg2.Error as e:
        print(f"Database error during signup: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    finally:
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database service is currently unavailable"}), 503

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
            user = cur.fetchone()

            if user and user['password'] == password:
                print(f"User logged in: {email}")
                return jsonify({
                    "message": "Login successful",
                    "user": {
                        "id": str(user['id']), 
                        "email": user['email'], 
                        "isFirstSignIn": user['is_first_sign_in']
                    }
                }), 200
            else:
                return jsonify({"error": "Invalid email or password"}), 401
    except psycopg2.Error as e:
        print(f"Database error during login: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    finally:
        if conn:
            conn.close()

@app.route('/students', methods=['GET', 'POST', 'DELETE'])
def handle_students():
    user_id = request.args.get('userId') if request.method == 'GET' else request.get_json().get('userId')
    if not user_id:
        return jsonify({"error": "Invalid or missing user ID"}), 401

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database service is currently unavailable"}), 503

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if request.method == 'GET':
                cur.execute("SELECT student_data FROM students WHERE user_id = %s;", (user_id,))
                user_students = [row['student_data'] for row in cur.fetchall()]
                return jsonify(user_students), 200

            if request.method == 'POST':
                # Simulate a delay to make the loading spinner more noticeable
                time.sleep(1.5) 
                student_data = request.get_json().get('student')
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
                print(f"Saved student '{student_data['basicInfo']['firstName']}' for user {user_id}")
                return jsonify({"message": "Student saved", "studentId": student_id}), 200

            if request.method == 'DELETE':
                student_id = request.get_json().get('studentId')
                cur.execute("DELETE FROM students WHERE id = %s AND user_id = %s;", (student_id, user_id))
                conn.commit()
                print(f"Deleted student {student_id} for user {user_id}")
                return jsonify({"message": "Student deleted"}), 200
    except psycopg2.Error as e:
        print(f"Database error in /students: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    finally:
        if conn:
            conn.close()

# Mock endpoints remain the same
@app.route('/timetable', methods=['GET'])
def get_timetable():
    student_id = request.args.get('student_id')
    if not student_id: return jsonify({"error": "student_id parameter is required"}), 400
    mock_timetable = { "tuitions": [ { "day": "saturday", "subject": "Math", "start": "10:00", "end": "11:30" }, { "day": "monday", "subject": "Physics", "start": "19:00", "end": "20:00" } ] }
    return jsonify(mock_timetable)

@app.route('/logs', methods=['GET'])
def get_logs():
    student_id = request.args.get('student_id')
    if not student_id: return jsonify({"error": "student_id is required"}), 400
    mock_logs = { "summary": { "unpaid_count": 3, "paid_count": 2, "total_due": 150.00 }, "detailed_logs": [ { "subject": 'Math', "date": '2025-07-21', "time_start": '10:00', "time_end": '11:30', "duration": '1.5h', "status": 'Paid' }, { "subject": 'Physics', "date": '2025-07-22', "time_start": '19:00', "time_end": '20:00', "duration": '1.0h', "status": 'Unpaid' } ] }
    return jsonify(mock_logs)

@app.route('/export', methods=['GET'])
def export_data():
    conn = get_db_connection()
    if conn is None: return jsonify({"error": "Database service is currently unavailable"}), 503
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, email, is_first_sign_in FROM users;")
            users = cur.fetchall()
            cur.execute("SELECT user_id, student_data FROM students;")
            students_rows = cur.fetchall()
            students_by_user = {}
            for row in students_rows:
                user_id = str(row['user_id'])
                if user_id not in students_by_user: students_by_user[user_id] = []
                students_by_user[user_id].append(row['student_data'])
            for user in users:
                user['id'] = str(user['id'])
                user['students'] = students_by_user.get(user['id'], [])
            return jsonify(users)
    except psycopg2.Error as e:
        print(f"Database error during export: {e}")
        return jsonify({"error": "A database error occurred during export."}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
