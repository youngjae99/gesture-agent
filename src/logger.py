import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class GestureAgentLogger:
    def __init__(self, log_level: str = "INFO", log_dir: str = "./logs"):
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        os.makedirs(log_dir, exist_ok=True)
        
        self.logger = logging.getLogger("GestureAgent")
        self.logger.setLevel(self.log_level)
        
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        file_handler = RotatingFileHandler(
            os.path.join(self.log_dir, f"gesture_agent_{datetime.now().strftime('%Y%m%d')}.log"),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(log_format)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(log_format)
        
        error_handler = RotatingFileHandler(
            os.path.join(self.log_dir, f"errors_{datetime.now().strftime('%Y%m%d')}.log"),
            maxBytes=5*1024*1024,
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(log_format)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def log_gesture_detection(self, gesture_type: str, confidence: float):
        self.info(f"Gesture detected: {gesture_type} (confidence: {confidence:.2f})")
    
    def log_ai_interaction(self, prompt: str, response: str, duration: float):
        self.info(f"AI interaction completed in {duration:.2f}s - Prompt length: {len(prompt)}, Response length: {len(response)}")
    
    def log_screenshot_capture(self, filepath: str, mode: str):
        self.info(f"Screenshot captured: {filepath} (mode: {mode})")
    
    def log_config_change(self, setting: str, old_value, new_value):
        self.info(f"Config changed - {setting}: {old_value} -> {new_value}")
    
    def log_system_event(self, event_type: str, details: str):
        self.info(f"System event [{event_type}]: {details}")


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = GestureAgentLogger()
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def setup_global_exception_handler():
    sys.excepthook = handle_exception


class ErrorHandler:
    def __init__(self, logger: Optional[GestureAgentLogger] = None):
        self.logger = logger or GestureAgentLogger()
    
    def handle_camera_error(self, error: Exception) -> str:
        error_msg = f"Camera error: {str(error)}"
        self.logger.error(error_msg)
        return "Camera unavailable. Please check camera permissions and connection."
    
    def handle_ai_error(self, error: Exception) -> str:
        error_msg = f"AI service error: {str(error)}"
        self.logger.error(error_msg)
        
        if "api" in str(error).lower():
            return "AI service temporarily unavailable. Please check your API key and connection."
        elif "rate" in str(error).lower():
            return "AI service rate limit reached. Please wait a moment and try again."
        else:
            return "AI service error. Please try again."
    
    def handle_screenshot_error(self, error: Exception) -> str:
        error_msg = f"Screenshot error: {str(error)}"
        self.logger.error(error_msg)
        return "Screenshot capture failed. Please check screen recording permissions."
    
    def handle_gesture_detection_error(self, error: Exception) -> str:
        error_msg = f"Gesture detection error: {str(error)}"
        self.logger.error(error_msg)
        return "Gesture detection temporarily unavailable."
    
    def handle_config_error(self, error: Exception) -> str:
        error_msg = f"Configuration error: {str(error)}"
        self.logger.error(error_msg)
        return "Configuration error. Settings have been reset to defaults."
    
    def handle_tts_error(self, error: Exception) -> str:
        error_msg = f"Text-to-speech error: {str(error)}"
        self.logger.error(error_msg)
        return "Voice output unavailable."
    
    def handle_generic_error(self, error: Exception, context: str = "") -> str:
        error_msg = f"Unexpected error in {context}: {str(error)}"
        self.logger.error(error_msg)
        return f"An unexpected error occurred{f' in {context}' if context else ''}. Please try again."