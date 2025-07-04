import sys
import threading
import time
from typing import Optional

import cv2
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox

from ai_assistant import AIAssistant
from config_manager import ConfigManager
from gesture_detector import GestureDetector
from gui import MainWindow, create_app
from logger import (ErrorHandler, GestureAgentLogger,
                    setup_global_exception_handler)
from screenshot_manager import ScreenshotManager
from tts_manager import TTSManager


class GestureAgentCore(QThread):
    gesture_detected = pyqtSignal(str)
    frame_updated = pyqtSignal(object)
    ai_response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    gesture_status_updated = pyqtSignal(str, str, str)  # left_hand_gesture, right_hand_gesture, face_gesture
    
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
                
                # 제스처 상태 업데이트 시그널 방출
                left_hand_gesture = getattr(self.gesture_detector, 'current_left_hand_gesture', None)
                right_hand_gesture = getattr(self.gesture_detector, 'current_right_hand_gesture', None)
                face_gesture = getattr(self.gesture_detector, 'current_face_gesture', None)
                self.gesture_status_updated.emit(left_hand_gesture or "", right_hand_gesture or "", face_gesture or "")
                
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
            
            # 스크린샷 캡처를 비동기로 처리
            screenshot_thread = threading.Thread(
                target=self._capture_screenshot_async,
                args=(gesture_type, screenshot_mode, screenshot_quality, screenshot_format)
            )
            screenshot_thread.daemon = True
            screenshot_thread.start()
            
        except Exception as e:
            error_msg = self.error_handler.handle_generic_error(e, "gesture handling")
            self.error_occurred.emit(error_msg)
    
    def _capture_screenshot_async(self, gesture_type: str, screenshot_mode: str, screenshot_quality: int, screenshot_format: str):
        """비동기로 스크린샷 캡처 및 AI 처리"""
        try:
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
            error_msg = self.error_handler.handle_generic_error(e, "async screenshot capture")
            self.error_occurred.emit(error_msg)
    
    def _get_gesture_prompt(self, gesture_type: str) -> str:
        # 복합 제스처 처리
        if '+' in gesture_type:
            parts = gesture_type.split('+')
            if len(parts) == 3:  # 양손 + 얼굴
                return f"I'm doing a {parts[0]}, {parts[1]}, and {parts[2]} simultaneously! Can you help me with what's on my screen based on this complex combination?"
            elif len(parts) == 2:  # 두 가지 조합
                if 'left_' in parts[0] and 'right_' in parts[1]:
                    # 양손 조합
                    left = parts[0].replace('left_', '')
                    right = parts[1].replace('right_', '')
                    return f"I'm doing a {left} with my left hand and a {right} with my right hand simultaneously! Can you help me with what's on my screen based on this two-handed gesture?"
                else:
                    # 손 + 얼굴 조합
                    if 'left_' in parts[0]:
                        hand = parts[0].replace('left_', '')
                        return f"I'm doing a {hand} with my left hand and a {parts[1]} with my face! Can you help me with what's on my screen based on this combination?"
                    elif 'right_' in parts[0]:
                        hand = parts[0].replace('right_', '')
                        return f"I'm doing a {hand} with my right hand and a {parts[1]} with my face! Can you help me with what's on my screen based on this combination?"
                    else:
                        return f"I'm doing both a {parts[0]} and a {parts[1]}! Can you help me with what's on my screen based on this combination?"
        
        # 단일 제스처 처리
        if gesture_type.startswith('left_'):
            base_gesture = gesture_type.replace('left_', '')
            return f"I'm doing a {base_gesture} with my left hand! Can you help me with what's currently on my screen?"
        elif gesture_type.startswith('right_'):
            base_gesture = gesture_type.replace('right_', '')
            return f"I'm doing a {base_gesture} with my right hand! Can you help me with what's currently on my screen?"
        
        # 기존 단일 제스처 프롬프트
        prompts = {
            'wave': "Hello! I just waved at you. Can you help me with what's currently on my screen?",
            'palm_up': "I'm holding my palm up to you. Please provide assistance based on what you can see on my screen.",
            'thumbs_up': "I'm giving you a thumbs up! Can you analyze what's on my screen and provide positive feedback or suggestions?",
            'peace_sign': "I'm showing you a peace sign. Can you help me with what's on my screen in a friendly way?",
            'fist': "I'm making a fist gesture. Can you help me take action on what's currently displayed on my screen?",
            'face_detected': "I'm looking at the camera! Can you see me and help me with what's currently on my screen?",
            'blink': "I just blinked deliberately at the camera! Can you help me with what's on my screen quickly?",
            'wink': "I winked at you! Can you give me a quick tip or insight about what's currently on my screen?",
            'smile': "I'm smiling at the camera! Can you help me with what's on my screen in a positive and encouraging way?",
            'eyebrows_raised': "I raised my eyebrows at the camera! Can you help me understand or explain what's currently on my screen?"
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
            self.core.gesture_status_updated.connect(self._on_gesture_status_updated)
            
            
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
        print(f"Status: Gesture detected - {gesture_type}")
        self.window.status_label.setText(f"Status: Gesture detected - {gesture_type}")
        
        # AI 상태를 processing으로 변경
        self.window.update_gesture_status(ai_status="processing")
        
        QTimer.singleShot(3000, lambda: 
            self.window.status_label.setText("Status: Running - Watching for gestures..."))
    
    def _on_gesture_status_updated(self, left_hand_gesture: str, right_hand_gesture: str, face_gesture: str):
        """제스처 상태 업데이트"""
        self.window.update_gesture_status(
            left_hand_gesture=left_hand_gesture if left_hand_gesture else None,
            right_hand_gesture=right_hand_gesture if right_hand_gesture else None,
            face_gesture=face_gesture if face_gesture else None
        )
    
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