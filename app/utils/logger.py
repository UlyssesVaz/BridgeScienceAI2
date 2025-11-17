# app/utils/logger.py

import logging
import sys
import os
from pythonjsonlogger import jsonlogger

# Define the format for the JSON log entries
LOG_FORMAT = '%(levelname)s %(asctime)s %(module)s %(funcName)s %(lineno)d %(message)s'
logger = logging.getLogger(__name__)

def configure_logging(level=logging.INFO):
    """Configures the root logger for structured JSON output."""
    
    # 1. Set the root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 2. Prevent duplicate handlers (important for --reload)
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        
        # 3. Use the JSON formatter
        formatter = jsonlogger.JsonFormatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        
        root_logger.addHandler(handler)
        
# Initialize logging right now
configure_logging()