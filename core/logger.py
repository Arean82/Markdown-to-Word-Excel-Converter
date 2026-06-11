# core/logger.py
# This module defines the Logger class, which provides a singleton logger for the application. It writes logs to a file and optionally to the console. It also provides methods to retrieve log content and clear logs. 
# Logger module - Singleton logger for the application

import logging
from pathlib import Path
from datetime import datetime


class Logger:
    """Singleton logger that writes to file and console"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Setup logger with file handler"""
        # Create logs directory
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Create log file with today's date
        log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
        
        # Setup logger
        self.logger = logging.getLogger('MarkdownConverter')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # Console handler (optional)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def get_log_content(self) -> str:
        """Get content of today's log file"""
        log_dir = Path(__file__).parent.parent / 'logs'
        if not log_dir.exists():
            return "No logs found"
        
        today_log = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
        if today_log.exists():
            with open(today_log, 'r', encoding='utf-8') as f:
                return f.read()
        return "No logs for today"
    
    def clear_logs(self) -> bool:
        """Clear all log files"""
        log_dir = Path(__file__).parent.parent / 'logs'
        if log_dir.exists():
            import shutil
            shutil.rmtree(log_dir)
            log_dir.mkdir()
            return True
        return False