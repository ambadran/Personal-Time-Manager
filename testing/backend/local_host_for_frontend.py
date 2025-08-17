from dotenv import load_dotenv
# Load environment variables from .env file before anything else
load_dotenv()

# Now we can import the app factory
from personal_time_manager import gunicorn_main_routine

if __name__ == '__main__':
    # Create the app instance using your factory
    app = gunicorn_main_routine()
    # Run the app in debug mode on port 5000
    app.run(debug=True, port=5000)
