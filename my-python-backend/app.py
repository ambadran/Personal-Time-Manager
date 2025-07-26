from flask import Flask, request, jsonify
from flask_cors import CORS
import json

# Initialize the Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) to allow requests from the web app
CORS(app)

# --- API Endpoints ---

@app.route('/register', methods=['POST'])
def register_student():
    """
    Receives student registration data from the frontend.
    In a real application, this would trigger the timetable generation logic.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    student_id = data.get('student_id')
    
    print("\n--- Received Student Registration ---")
    print(f"Student Firestore ID: {student_id}")
    # Pretty print the received JSON data
    print(json.dumps(data, indent=2))
    print("--- End of Registration Data ---\n")

    # Here, you would typically save this data and run your
    # Python script to generate the timetable for this student.

    return jsonify({
        "status": "success",
        "message": f"Registration received for student {student_id}."
    }), 200


@app.route('/timetable', methods=['GET'])
def get_timetable():
    """
    Returns a mock timetable for a given student.
    In a real application, this would read a generated timetable file.
    """
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id parameter is required"}), 400

    print(f"\n--- Timetable requested for student: {student_id} ---")

    # Mock data: In a real app, you would load the specific
    # timetable JSON file generated for this student_id.
    mock_timetable = {
        "student_id": student_id,
        "tuitions": [
            {
                "day": "saturday",
                "subject": "Math",
                "start": "10:00",
                "end": "11:30"
            },
            {
                "day": "monday",
                "subject": "Physics",
                "start": "19:00",
                "end": "20:00"
            },
            {
                "day": "wednesday",
                "subject": "Chemistry",
                "start": "17:00",
                "end": "18:30"
            }
        ]
    }
    
    return jsonify(mock_timetable)


@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Returns mock logs and a summary for a given student.
    In a real application, this would read from a log file or database.
    """
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({"error": "student_id parameter is required"}), 400
        
    print(f"\n--- Logs requested for student: {student_id} ---")

    # Mock data: In a real app, you would load and process log files.
    mock_logs = {
        "summary": {
            "unpaid_count": 3,
            "paid_count": 2,
            "total_due": 150.00 # Assuming $50 per lesson
        },
        "detailed_logs": [
            { "subject": 'Math', "date": '2025-07-21', "time_start": '10:00', "time_end": '11:30', "duration": '1.5h', "status": 'Paid' },
            { "subject": 'Physics', "date": '2025-07-22', "time_start": '19:00', "time_end": '20:00', "duration": '1.0h', "status": 'Unpaid' },
            { "subject": 'Chemistry', "date": '2025-07-15', "time_start": '17:00', "time_end": '18:00', "duration": '1.0h', "status": 'Paid' },
            { "subject": 'IT', "date": '2025-07-14', "time_start": '16:00', "time_end": '17:30', "duration": '1.5h', "status": 'Unpaid' },
            { "subject": 'Biology', "date": '2025-07-12', "time_start": '11:00', "time_end": '12:00', "duration": '1.0h', "status": 'Unpaid' },
        ]
    }

    return jsonify(mock_logs)


if __name__ == '__main__':
    # Runs the Flask app on localhost, port 5000
    # The debug=True flag enables auto-reloading when you save the file.
    app.run(debug=True)

