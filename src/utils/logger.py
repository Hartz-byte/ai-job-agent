import logging
import sys
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    # Remove any existing handlers
    logging.basicConfig(handlers=[])
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    log_dir = Path('output/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_dir / f'{name}.log', mode='w')
    fh.setLevel(logging.DEBUG)
    
    # Create console handler with a higher log level
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger
