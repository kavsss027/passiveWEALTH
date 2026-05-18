import logging
from app.core.logging import setup_logging, get_logger

def test_setup_logging_and_get_logger():
    setup_logging("DEBUG")
    logger = get_logger("test_logger")
    assert logger.name == "test_logger"
    # Basic verification that it doesn't crash and returns a structlog logger
    
    # We can also test default level
    setup_logging()
    logger2 = get_logger("test_logger2")
    assert logger2.name == "test_logger2"
