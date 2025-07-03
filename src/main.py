import cv2
import sys
import threading
import time
from typing import Optional
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer

from gesture_detector import GestureDetector
from ai_assistant import AIAssistant
from screenshot_manager import ScreenshotManager
from tts_manager import TTSManager
from config_manager import ConfigManager
from logger import GestureAgentLogger, ErrorHandler, setup_global_exception_handler
from gui import create_app, MainWindow


class GestureAgentCore(QThread):
    gesture_detected = pyqtSignal(str)
    frame_updated = pyqtSignal(object)
    ai_response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = GestureAgentLogger(
            log_level=config_manager.get_config_value('system.log_level', 'INFO')
        )
        self.error_handler = ErrorHandler(self.logger)
        
        self.running = False
        self.camera = None
        self.gesture_detector = None
        self.ai_assistant = None
        self.screenshot_manager = None
        self.tts_manager = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        try:
            config = self.config_manager.config
            
            sensitivity = config['gestures']['wave']['confidence_threshold']
            self.gesture_detector = GestureDetector(sensitivity)
            
            self.ai_assistant = AIAssistant()
            
            screenshot_dir = self.config_manager.get_env_var('SCREENSHOT_DIR', './screenshots')
            self.screenshot_manager = ScreenshotManager(screenshot_dir)
            
            enable_tts = config['ui']['enable_tts']
            self.tts_manager = TTSManager() if enable_tts else None
            
            self.logger.log_system_event("initialization", "All components initialized successfully")
            
        except Exception as e:
            error_msg = self.error_handler.handle_generic_error(e, "component initialization")
            self.error_occurred.emit(error_msg)
    
    def _initialize_camera(self) -> bool:
        try:
            camera_device = self.config_manager.get_config_value('system.camera_device', 0)
            self.camera = cv2.VideoCapture(camera_device)
            
            if not self.camera.isOpened():
                raise RuntimeError("Could not open camera")
            
            fps = self.config_manager.get_config_value('system.fps', 30)
            self.camera.set(cv2.CAP_PROP_FPS, fps)
            
            self.logger.log_system_event("camera", f"Camera initialized on device {camera_device}")
            return True
            
        except Exception as e:
            error_msg = self.error_handler.handle_camera_error(e)
            self.error_occurred.emit(error_msg)
            return False
    
    def start_detection(self):
        if not self.running:
            if self._initialize_camera():
                self.running = True
                self.start()
                self.logger.log_system_event("detection", "Gesture detection started")
            else:
                self.error_occurred.emit("Failed to start camera")
    
    def stop_detection(self):
        if self.running:
            self.running = False
            self.wait()
            
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.logger.log_system_event("detection", "Gesture detection stopped")
    
    def run(self):
        last_gesture_time = 0
        gesture_cooldown = 3.0
        
        while self.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    continue
                
                frame = cv2.flip(frame, 1)
                
                processed_frame, detected_gesture = self.gesture_detector.process_frame(frame)
                
                self.frame_updated.emit(processed_frame)
                
                current_time = time.time()
                if (detected_gesture and 
                    (current_time - last_gesture_time) > gesture_cooldown):
                    
                    last_gesture_time = current_time
                    self.gesture_detected.emit(detected_gesture)
                    self._handle_gesture(detected_gesture)
                
                self.msleep(33)
                
            except Exception as e:
                error_msg = self.error_handler.handle_gesture_detection_error(e)
                self.error_occurred.emit(error_msg)
                break
    
    def _handle_gesture(self, gesture_type: str):
        try:
            self.logger.log_gesture_detection(gesture_type, 0.8)
            
            screenshot_mode = self.config_manager.get_config_value('screenshot.mode', 'fullscreen')
            screenshot_quality = self.config_manager.get_config_value('screenshot.quality', 90)
            screenshot_format = self.config_manager.get_config_value('screenshot.format', 'PNG')
            
            screenshot_path = self.screenshot_manager.capture_screenshot(
                mode=screenshot_mode,
                quality=screenshot_quality,
                format=screenshot_format
            )
            
            if screenshot_path:
                self.logger.log_screenshot_capture(screenshot_path, screenshot_mode)
            
            prompt = self._get_gesture_prompt(gesture_type)
            
            start_time = time.time()
            response = self.ai_assistant.send_message(prompt, screenshot_path)
            duration = time.time() - start_time
            
            self.logger.log_ai_interaction(prompt, response, duration)
            
            self.ai_response_received.emit(response)
            
            if self.tts_manager and self.config_manager.get_config_value('ui.enable_tts', False):
                self.tts_manager.speak_text(response, block=False)
            
        except Exception as e:
            error_msg = self.error_handler.handle_generic_error(e, "gesture handling")
            self.error_occurred.emit(error_msg)
    
    def _get_gesture_prompt(self, gesture_type: str) -> str:
        prompts = {
            'wave': "Hello! I just waved at you. Can you help me with what's currently on my screen?",
            'palm_up': "I'm holding my palm up to you. Please provide assistance based on what you can see on my screen."
        }
        return prompts.get(gesture_type, "I performed a gesture. Please help me with my current screen.")
    
    def cleanup(self):
        self.stop_detection()
        
        if self.gesture_detector:
            self.gesture_detector.cleanup()
        
        if self.tts_manager:
            self.tts_manager.cleanup()
        
        self.logger.log_system_event("shutdown", "Application cleanup completed")


class GestureAgentApp:
    def __init__(self):
        setup_global_exception_handler()
        
        self.config_manager = ConfigManager()
        self.logger = GestureAgentLogger()
        self.error_handler = ErrorHandler(self.logger)
        
        self.app = None
        self.window = None
        self.core = None
        
        self._validate_setup()
    
    def _validate_setup(self):
        is_valid, errors = self.config_manager.validate_config()
        
        if not is_valid:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
        
        if not self.config_manager.get_env_var('OPENAI_API_KEY'):
            self.logger.warning("OpenAI API key not set. Please configure in .env file")
    
    def run(self):
        try:
            self.app, self.window = create_app()
            
            self.core = GestureAgentCore(self.config_manager)
            
            self.core.gesture_detected.connect(self._on_gesture_detected)
            self.core.frame_updated.connect(self.window.update_camera_frame)
            self.core.ai_response_received.connect(self.window.show_response)
            self.core.error_occurred.connect(self._on_error)
            
            self.window.start_btn.clicked.connect(self._toggle_detection)
            
            cleanup_timer = QTimer()
            cleanup_timer.timeout.connect(self._periodic_cleanup)
            cleanup_timer.start(300000)
            
            self.window.show()
            self.logger.log_system_event("startup", "GestureAgent application started")
            
            return self.app.exec_()
            
        except Exception as e:
            error_msg = self.error_handler.handle_generic_error(e, "application startup")
            if self.app:
                QMessageBox.critical(None, "Startup Error", error_msg)
            else:
                print(f"Critical startup error: {error_msg}")
            return 1
    
    def _toggle_detection(self):
        try:
            if self.core.running:
                self.core.stop_detection()
                self.window.start_btn.setText("Start Detection")
                self.window.status_label.setText("Status: Stopped")
            else:
                self.core.start_detection()
                self.window.start_btn.setText("Stop Detection")
                self.window.status_label.setText("Status: Running - Watching for gestures...")
                
        except Exception as e:
            error_msg = self.error_handler.handle_generic_error(e, "detection toggle")
            self._on_error(error_msg)
    
    def _on_gesture_detected(self, gesture_type: str):
        self.window.status_label.setText(f"Status: Gesture detected - {gesture_type}")
        
        QTimer.singleShot(3000, lambda: 
            self.window.status_label.setText("Status: Running - Watching for gestures..."))
    
    def _on_error(self, error_message: str):
        self.window.status_label.setText(f"Status: Error - {error_message}")
        
        if self.core and self.core.running:
            self.core.stop_detection()
            self.window.start_btn.setText("Start Detection")
    
    def _periodic_cleanup(self):
        try:
            auto_cleanup_days = self.config_manager.get_config_value('system.auto_cleanup_days', 7)
            if self.core and self.core.screenshot_manager:
                self.core.screenshot_manager.cleanup_old_screenshots(auto_cleanup_days)
            
        except Exception as e:
            self.logger.error(f"Error during periodic cleanup: {e}")
    
    def shutdown(self):
        try:
            if self.core:
                self.core.cleanup()
            
            self.logger.log_system_event("shutdown", "Application shutdown initiated")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


def main():
    app = GestureAgentApp()
    
    try:
        exit_code = app.run()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        exit_code = 0
    finally:
        app.shutdown()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())