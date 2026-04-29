import logging
import os
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Configure logging
def setup_logging():
    logger = logging.getLogger("video_downloader")
    logger.setLevel(logging.DEBUG)

    # Console Handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # File Handler
    f_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
    
    return logger

# Custom logger for yt-dlp
class YtDlpLogger:
    def __init__(self, logger):
        self.logger = logger

    def debug(self, msg):
        # yt-dlp debug can be very verbose, we'll log it to file only via logger.debug
        if msg.startswith('[debug] '):
            self.logger.debug(msg)
        else:
            self.logger.info(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

app_logger = setup_logging()
yt_logger = YtDlpLogger(app_logger)
