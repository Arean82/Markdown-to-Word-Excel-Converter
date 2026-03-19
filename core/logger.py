import logging
import os
from pathlib import Path
from datetime import datetime

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        # Create logs directory
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
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
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def get_log_content(self):
        log_dir = Path(__file__).parent.parent / 'logs'
        if not log_dir.exists():
            return "No logs found"
        
        # Get today's log file
        today_log = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
        if today_log.exists():
            with open(today_log, 'r', encoding='utf-8') as f:
                return f.read()
        return "No logs for today"
    
    def clear_logs(self):
        log_dir = Path(__file__).parent.parent / 'logs'
        if log_dir.exists():
            import shutil
            shutil.rmtree(log_dir)
            log_dir.mkdir()
            return True
        return False