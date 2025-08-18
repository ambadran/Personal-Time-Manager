'''
backend API Endpoints processing for EfficientTutor Frontend
'''
from flask import Blueprint, request, jsonify
import time
from ..database.db_handler import DatabaseHandler

# create a Blueprint and the Database Handler
main_routes = Blueprint('main_routes', __name__)
db = DatabaseHandler()

# --- API Endpoints ---

@main_routes.route('/', methods=['GET'])
def health_check():
    if not db.check_connection():
        return jsonify({"error": "Database connection failed"}), 503
    return jsonify({"status": "ok", "message": "Backend is running and database is connected"}), 200

@main_routes.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user_data, message = db.signup_user(email, password)
    if not user_data:
        return jsonify({"error": message}), 409
    
    print(f"New user signed up: {email} (ID: {user_data['id']})")
    return jsonify({"message": message, "user": user_data}), 201

@main_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user_data, message = db.login_user(email, password)
    if not user_data:
        return jsonify({"error": message}), 401
    
    print(f"User logged in: {email}")
    return jsonify({"message": message, "user": user_data}), 200

@main_routes.route('/students', methods=['GET', 'POST', 'DELETE'])
def handle_students():
    if request.method == 'GET':
        user_id = request.args.get('userId')
    else: # POST or DELETE
        user_id = request.get_json().get('userId')

    if not user_id:
        return jsonify({"error": "Invalid or missing user ID"}), 401

    if request.method == 'GET':
        students = db.get_students(user_id)
        return jsonify(students), 200

    if request.method == 'POST':
        time.sleep(1.5) # Simulate delay
        student_data = request.get_json().get('student')
        student_id = db.save_student(user_id, student_data)
        print(f"Saved student '{student_data['basicInfo']['firstName']}' for user {user_id}")
        return jsonify({"message": "Student saved", "studentId": student_id}), 200

    if request.method == 'DELETE':
        student_id = request.get_json().get('studentId')
        if db.delete_student(user_id, student_id):
            print(f"Deleted student {student_id} for user {user_id}")
            return jsonify({"message": "Student deleted"}), 200
        return jsonify({"error": "Student not found"}), 404

# Mock endpoints remain the same
@main_routes.route('/timetable', methods=['GET'])
def get_timetable():
    student_id = request.args.get('student_id')
    if not student_id: return jsonify({"error": "student_id parameter is required"}), 400
    mock_timetable = { "tuitions": [ { "day": "saturday", "subject": "Math", "start": "10:00", "end": "11:30" }, { "day": "monday", "subject": "Physics", "start": "19:00", "end": "20:00" } ] }
    return jsonify(mock_timetable)

@main_routes.route('/logs', methods=['GET'])
def get_logs():
    student_id = request.args.get('student_id')
    if not student_id: return jsonify({"error": "student_id is required"}), 400
    mock_logs = { "summary": { "unpaid_count": 3, "paid_count": 2, "total_due": 0.00 }, "detailed_logs": [ { "subject": 'Math', "date": '2025-07-21', "time_start": '10:00', "time_end": '11:30', "duration": '1.5h', "status": 'Paid' }, { "subject": 'Physics', "date": '2025-07-22', "time_start": '19:00', "time_end": '20:00', "duration": '1.0h', "status": 'Unpaid' } ] }
    return jsonify(mock_logs)

@main_routes.route('/export', methods=['GET'])
def export_data():
    all_data = db.export_all_data()
    return jsonify(all_data)

