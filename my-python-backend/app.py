from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import uuid

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# --- In-Memory Database Simulation ---
# In a real application, this would be a proper database like PostgreSQL or MongoDB.
db = {
    "users": {},      # { "user_id": { "email": "...", "password": "...", "isFirstSignIn": True } }
    "students": {}  # { "user_id": { "student_id": { ...student_data... } } }
}

# --- API Endpoints ---

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Check if user already exists
    for user_id, user_data in db["users"].items():
        if user_data["email"] == email:
            return jsonify({"error": "User with this email already exists"}), 409

    # Create new user
    new_user_id = str(uuid.uuid4())
    db["users"][new_user_id] = {"email": email, "password": password, "isFirstSignIn": True}
    db["students"][new_user_id] = {}

    print(f"New user signed up: {email} (ID: {new_user_id})")
    
    return jsonify({
        "message": "Signup successful",
        "user": {"id": new_user_id, "email": email, "isFirstSignIn": True}
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Find user and check password
    for user_id, user_data in db["users"].items():
        if user_data["email"] == email and user_data["password"] == password:
            print(f"User logged in: {email}")
            return jsonify({
                "message": "Login successful",
                "user": {"id": user_id, "email": email, "isFirstSignIn": user_data.get("isFirstSignIn", False)}
            }), 200

    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/students', methods=['GET', 'POST', 'DELETE'])
def handle_students():
    user_id = request.args.get('userId') if request.method == 'GET' else request.get_json().get('userId')
    if not user_id or user_id not in db["users"]:
        return jsonify({"error": "Invalid or missing user ID"}), 401

    if request.method == 'GET':
        user_students = list(db["students"].get(user_id, {}).values())
        return jsonify(user_students), 200

    if request.method == 'POST':
        student_data = request.get_json().get('student')
        student_id = student_data.get('id', str(uuid.uuid4()))
        student_data['id'] = student_id
        
        db["students"][user_id][student_id] = student_data
        
        # Mark that the user is no longer a first-time signer-in
        if db["users"][user_id]["isFirstSignIn"]:
            db["users"][user_id]["isFirstSignIn"] = False

        print(f"Saved student '{student_data['basicInfo']['firstName']}' for user {user_id}")
        return jsonify({"message": "Student saved", "studentId": student_id}), 200

    if request.method == 'DELETE':
        student_id = request.get_json().get('studentId')
        if student_id in db["students"].get(user_id, {}):
            del db["students"][user_id][student_id]
            print(f"Deleted student {student_id} for user {user_id}")
            return jsonify({"message": "Student deleted"}), 200
        return jsonify({"error": "Student not found"}), 404

@app.route('/timetable', methods=['GET'])
def get_timetable():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id parameter is required"}), 400
    mock_timetable = {
        "tuitions": [
            { "day": "saturday", "subject": "Math", "start": "10:00", "end": "11:30" },
            { "day": "monday", "subject": "Physics", "start": "19:00", "end": "20:00" },
        ]
    }
    return jsonify(mock_timetable)

@app.route('/logs', methods=['GET'])
def get_logs():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400
    mock_logs = {
        "summary": { "unpaid_count": 3, "paid_count": 2, "total_due": 150.00 },
        "detailed_logs": [
            { "subject": 'Math', "date": '2025-07-21', "time_start": '10:00', "time_end": '11:30', "duration": '1.5h', "status": 'Paid' },
            { "subject": 'Physics', "date": '2025-07-22', "time_start": '19:00', "time_end": '20:00', "duration": '1.0h', "status": 'Unpaid' },
            { "subject": 'IT', "date": '2025-07-14', "time_start": '16:00', "time_end": '17:30', "duration": '1.5h', "status": 'Unpaid' },
            { "subject": 'Biology', "date": '2025-07-12', "time_start": '11:00', "time_end": '12:00', "duration": '1.0h', "status": 'Unpaid' },
        ]
    }
    return jsonify(mock_logs)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
