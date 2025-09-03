'''
The main logger logic
'''
import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv

def setup_logging():
    """
    Configures the root logger for the entire application.
    - Logs to the console.
    - Logs to a rotating file (`app.log`).
    - Log level can be configured via .env file.
    """
    load_dotenv()
    
    # Get log level from environment variable, defaulting to INFO
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Define the format for log messages
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get the root logger
    logger = logging.getLogger("personal_time_manager")
    logger.setLevel(log_level)
    
    # --- Console Handler ---
    # Logs messages to the standard output (your terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # --- File Handler ---
    # Creates a new log file every day and keeps the last 7 days of logs.
    # This is crucial for services like Render where you can't always see the console.
    log_file_path = "app.log"
    file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    print(f"INFO: Logging configured. Level: {log_level_str}. Output file: {log_file_path}")
