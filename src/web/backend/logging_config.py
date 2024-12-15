import logging
import logging.handlers
import sys
from pathlib import Path

def setup_logging():
    """Configure logging for the application."""
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Create debug file handler
    debug_log_path = Path('plm_debug.log')
    file_handler = logging.handlers.RotatingFileHandler(
        debug_log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Set levels for specific loggers
    logging.getLogger('src.web.backend').setLevel(logging.DEBUG)
    logging.getLogger('src.web.backend.services').setLevel(logging.DEBUG)
    logging.getLogger('src.web.backend.api').setLevel(logging.DEBUG)

    # Ensure uvicorn logs are captured
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn").addHandler(console_handler)
    logging.getLogger("uvicorn").addHandler(file_handler)

    # Log startup message
    root_logger.info("=== PLM Backend Starting ===")
    root_logger.debug("Logging configured successfully") 