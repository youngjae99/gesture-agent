import json
import sys

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPixmap
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
                             QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu,
                             QMessageBox, QProgressBar, QPushButton, QSlider,
                             QSystemTrayIcon, QTabWidget, QTextEdit,
                             QVBoxLayout, QWidget)


class ResponseWindow(QDialog):
    def __init__(self, response_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Response")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon('assets/app_icon.png'))
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(30, 30, 30, 220);
                border-radius: 10px;
                border: 2px solid #4a9eff;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout()
        
        response_label = QLabel(response_text)
        response_label.setWordWrap(True)
        response_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(response_label)
        
        self.setLayout(layout)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.start(8000)
        
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() // 4
        self.move(x, y)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.close()


class ConfigWindow(QDialog):
    config_changed = pyqtSignal(dict)
    
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("GestureAgent Configuration")
        self.setFixedSize(500, 400)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        tabs = QTabWidget()
        
        gesture_tab = QWidget()
        gesture_layout = QVBoxLayout()
        
        gesture_layout.addWidget(QLabel("Gesture Settings:"))
        
        self.wave_enabled = QCheckBox("Enable Wave Gesture")
        self.wave_enabled.setChecked(self.config['gestures']['wave']['enabled'])
        gesture_layout.addWidget(self.wave_enabled)
        
        self.palm_enabled = QCheckBox("Enable Palm Up Gesture") 
        self.palm_enabled.setChecked(self.config['gestures']['palm_up']['enabled'])
        gesture_layout.addWidget(self.palm_enabled)
        
        gesture_layout.addWidget(QLabel("Gesture Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(int(self.config['gestures']['wave']['confidence_threshold'] * 10))
        gesture_layout.addWidget(self.sensitivity_slider)
        
        gesture_tab.setLayout(gesture_layout)
        tabs.addTab(gesture_tab, "Gestures")
        
        screenshot_tab = QWidget()
        screenshot_layout = QVBoxLayout()
        
        screenshot_layout.addWidget(QLabel("Screenshot Mode:"))
        self.screenshot_mode = QComboBox()
        self.screenshot_mode.addItems(["fullscreen", "active_window"])
        self.screenshot_mode.setCurrentText(self.config['screenshot']['mode'])
        screenshot_layout.addWidget(self.screenshot_mode)
        
        screenshot_layout.addWidget(QLabel("Screenshot Quality:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(self.config['screenshot']['quality'])
        screenshot_layout.addWidget(self.quality_slider)
        
        screenshot_tab.setLayout(screenshot_layout)
        tabs.addTab(screenshot_tab, "Screenshot")
        
        ui_tab = QWidget()
        ui_layout = QVBoxLayout()
        
        self.show_preview = QCheckBox("Show Camera Preview")
        self.show_preview.setChecked(self.config['ui']['show_camera_preview'])
        ui_layout.addWidget(self.show_preview)
        
        self.enable_tts = QCheckBox("Enable Text-to-Speech")
        self.enable_tts.setChecked(self.config['ui']['enable_tts'])
        ui_layout.addWidget(self.enable_tts)
        
        ui_tab.setLayout(ui_layout)
        tabs.addTab(ui_tab, "Interface")
        
        layout.addWidget(tabs)
        
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_config)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_config(self):
        self.config['gestures']['wave']['enabled'] = self.wave_enabled.isChecked()
        self.config['gestures']['palm_up']['enabled'] = self.palm_enabled.isChecked()
        self.config['gestures']['wave']['confidence_threshold'] = self.sensitivity_slider.value() / 10.0
        self.config['gestures']['palm_up']['confidence_threshold'] = self.sensitivity_slider.value() / 10.0
        
        self.config['screenshot']['mode'] = self.screenshot_mode.currentText()
        self.config['screenshot']['quality'] = self.quality_slider.value()
        
        self.config['ui']['show_camera_preview'] = self.show_preview.isChecked()
        self.config['ui']['enable_tts'] = self.enable_tts.isChecked()
        
        self.config_changed.emit(self.config)
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.setWindowTitle("GestureAgent")
        self.setFixedSize(640, 600)
        
        # 컴팩트 모드 관련 속성 추가
        self.is_compact_mode = False
        self.normal_size = (640, 600)
        self.compact_size = (300, 100)
        self.dragging = False
        
        self.init_ui()
        self.init_system_tray()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout()
        
        # 헤더
        self.header = QLabel("GestureAgent - Touchless AI Interface")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFont(QFont("Arial", 16, QFont.Bold))
        self.main_layout.addWidget(self.header)
        
        # 상태 라벨
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_label)
        
        # 제스처 상태 표시 프레임
        self.gesture_status_frame = QFrame()
        self.gesture_status_frame.setFixedHeight(80)
        self.gesture_status_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        
        gesture_status_layout = QHBoxLayout()
        gesture_status_layout.setSpacing(20)
        
        # Left Hand Gesture 칩
        self.left_hand_gesture_chip = QLabel("Left: None")
        self.left_hand_gesture_chip.setFixedSize(140, 35)
        self.left_hand_gesture_chip.setAlignment(Qt.AlignCenter)
        self.left_hand_gesture_chip.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: #888;
                border: 1px solid #555;
                border-radius: 17px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        gesture_status_layout.addWidget(self.left_hand_gesture_chip)
        
        # + 연결 표시
        plus_label_1 = QLabel("+")
        plus_label_1.setAlignment(Qt.AlignCenter)
        plus_label_1.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        gesture_status_layout.addWidget(plus_label_1)
        
        # Right Hand Gesture 칩
        self.right_hand_gesture_chip = QLabel("Right: None")
        self.right_hand_gesture_chip.setFixedSize(140, 35)
        self.right_hand_gesture_chip.setAlignment(Qt.AlignCenter)
        self.right_hand_gesture_chip.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: #888;
                border: 1px solid #555;
                border-radius: 17px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        gesture_status_layout.addWidget(self.right_hand_gesture_chip)
        
        # + 연결 표시
        plus_label_2 = QLabel("+")
        plus_label_2.setAlignment(Qt.AlignCenter)
        plus_label_2.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        gesture_status_layout.addWidget(plus_label_2)
        
        # Face Gesture 칩
        self.face_gesture_chip = QLabel("Face: None")
        self.face_gesture_chip.setFixedSize(140, 35)
        self.face_gesture_chip.setAlignment(Qt.AlignCenter)
        self.face_gesture_chip.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: #888;
                border: 1px solid #555;
                border-radius: 17px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        gesture_status_layout.addWidget(self.face_gesture_chip)
        
        # + 연결 표시
        plus_label_3 = QLabel("+")
        plus_label_3.setAlignment(Qt.AlignCenter)
        plus_label_3.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                font-weight: bold;
                background: transparent;
            }
        """)
        gesture_status_layout.addWidget(plus_label_3)
        
        # AI Status 칩
        self.ai_status_chip = QLabel("AI: Ready")
        self.ai_status_chip.setFixedSize(140, 35)
        self.ai_status_chip.setAlignment(Qt.AlignCenter)
        self.ai_status_chip.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: #888;
                border: 1px solid #555;
                border-radius: 17px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        gesture_status_layout.addWidget(self.ai_status_chip)
        
        self.gesture_status_frame.setLayout(gesture_status_layout)
        self.main_layout.addWidget(self.gesture_status_frame)
        
        # 카메라 프레임
        self.camera_frame = QLabel()
        self.camera_frame.setFixedSize(640, 480)
        self.camera_frame.setStyleSheet("border: 2px solid #333; background-color: #222;")
        self.camera_frame.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.camera_frame)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Detection")
        self.start_btn.clicked.connect(self.toggle_detection)
        button_layout.addWidget(self.start_btn)
        
        config_btn = QPushButton("Configuration")
        config_btn.clicked.connect(self.show_config)
        button_layout.addWidget(config_btn)
        
        # 컴팩트 모드 토글 버튼 추가
        self.compact_btn = QPushButton("Compact Mode")
        self.compact_btn.clicked.connect(self.toggle_compact_mode)
        button_layout.addWidget(self.compact_btn)
        
        minimize_btn = QPushButton("Minimize to Tray")
        minimize_btn.clicked.connect(self.hide)
        button_layout.addWidget(minimize_btn)
        
        self.main_layout.addLayout(button_layout)
        
        central_widget.setLayout(self.main_layout)
        
        self.apply_normal_style()
    
    def apply_normal_style(self):
        """일반 모드 스타일 적용"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QLabel {
                color: white;
                padding: 5px;
            }
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2563eb;
            }
        """)
    
    def apply_compact_style(self):
        """컴팩트 모드 스타일 적용 (glassmorphism)"""
        self.setStyleSheet("""
            QMainWindow {
            }
            QLabel {
                color: white;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.6);
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
            }
            QPushButton {
                background-color: rgba(74, 158, 255, 0.3);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 5px;
                border-radius: 6px;
                font-size: 10px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: rgba(74, 158, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(74, 158, 255, 0.7);
            }
        """)
    
    def toggle_compact_mode(self):
        """컴팩트 모드와 일반 모드 전환"""
        if self.is_compact_mode:
            self.switch_to_normal_mode()
        else:
            self.switch_to_compact_mode()
    
    def switch_to_compact_mode(self):
        """컴팩트 모드로 전환"""
        self.is_compact_mode = True
        
        # 창 속성 변경
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        # 크기 조정
        self.setFixedSize(*self.compact_size)
        
        # UI 요소 숨기기/조정
        self.header.hide()
        self.camera_frame.hide()
        
        # 모든 버튼 숨기기
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item and hasattr(item, 'layout') and item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, QPushButton):
                        widget.hide()
        
        # 상태 라벨 크기 조정 (더 큰 폰트)
        self.status_label.setFixedHeight(50)
        self.status_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_label.setStyleSheet("color: white; background-color: transparent;")
        # 컴팩트 모드에서 라벨의 마우스 이벤트 비활성화
        # self.status_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # 트레이 메뉴 텍스트 업데이트
        if hasattr(self, 'compact_action'):
            self.compact_action.setText("Normal Mode")
        
        # 스타일 적용
        self.apply_compact_style()
        
        # 화면 우상단으로 이동
        self.move_to_top_right()
        
        # 창 다시 표시
        self.show()
    
    def switch_to_normal_mode(self):
        """일반 모드로 전환"""
        self.is_compact_mode = False
        
        # 창 속성 복원
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 크기 복원
        self.setFixedSize(*self.normal_size)
        
        # UI 요소 다시 표시
        self.header.show()
        self.camera_frame.show()
        
        # 모든 버튼 다시 표시
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            if item and hasattr(item, 'layout') and item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, QPushButton):
                        widget.show()
        
        # 상태 라벨 크기 복원
        self.status_label.setFixedHeight(20)
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("")
        # 노멀 모드에서 라벨의 마우스 이벤트 활성화
        self.status_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        # 버튼 텍스트 변경
        self.compact_btn.setText("Compact Mode")
        
        # 스타일 복원
        self.apply_normal_style()
        
        # 창 다시 표시
        self.show()
    
    def move_to_top_right(self):
        """창을 화면 우상단으로 이동"""
        screen = QApplication.desktop().screenGeometry()
        x = screen.width() - self.width() - 20  # 오른쪽 여백 20px
        y = 20  # 위쪽 여백 20px
        self.move(x, y)
    
    def mousePressEvent(self, event):
        """컴팩트 모드에서 창 드래그 가능하도록"""
        if self.is_compact_mode:
            if event.button() == Qt.LeftButton:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self.dragging = True
                event.accept()
            elif event.button() == Qt.RightButton:
                # 우클릭으로 노말 모드로 전환
                self.switch_to_normal_mode()
                event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """컴팩트 모드에서 창 드래그"""
        if self.is_compact_mode:
            print('draggingStart in compact mode')
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """드래그 종료"""
        if self.is_compact_mode and hasattr(self, 'dragging'):
            print('dragend')
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Load SVG icon for the system tray
        icon_path = "assets/tray_icon.svg"
        try:
            self.tray_icon.setIcon(QIcon(icon_path))
        except Exception as e:
            # Fallback to simple icon if SVG fails to load
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(74, 158, 255))
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "GA")
            painter.end()
            self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self.show)
        
        # 컴팩트 모드 토글 메뉴 추가
        self.compact_action = tray_menu.addAction("Compact Mode")
        self.compact_action.triggered.connect(self.toggle_compact_mode)
        
        config_action = tray_menu.addAction("Configuration")
        config_action.triggered.connect(self.show_config)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
    
    def show_config(self):
        config_dialog = ConfigWindow(self.config, self)
        config_dialog.config_changed.connect(self.update_config)
        config_dialog.exec_()
    
    def update_config(self, new_config):
        self.config = new_config
        with open('config.json', 'w') as f:
            json.dump(new_config, f, indent=4)
    
    def toggle_detection(self):
        if self.start_btn.text() == "Start Detection":
            self.start_btn.setText("Stop Detection")
            self.status_label.setText("Status: Running - Watching for gestures...")
        else:
            self.start_btn.setText("Start Detection")
            self.status_label.setText("Status: Stopped")
    
    def update_camera_frame(self, frame):
        if self.config['ui']['show_camera_preview']:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_image)
            self.camera_frame.setPixmap(pixmap.scaled(640, 480, Qt.KeepAspectRatio))
        else:
            self.camera_frame.setText("Camera preview disabled")
    
    def update_gesture_status(self, left_hand_gesture=None, right_hand_gesture=None, face_gesture=None, ai_status=None):
        """제스처 상태 칩 업데이트"""
        if left_hand_gesture is not None:
            if left_hand_gesture:
                self.left_hand_gesture_chip.setText(f"Left: {left_hand_gesture}")
                self.left_hand_gesture_chip.setStyleSheet("""
                    QLabel {
                        background-color: #1e3a8a;
                        color: #60a5fa;
                        border: 1px solid #3b82f6;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
            else:
                self.left_hand_gesture_chip.setText("Left: None")
                self.left_hand_gesture_chip.setStyleSheet("""
                    QLabel {
                        background-color: #333;
                        color: #888;
                        border: 1px solid #555;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
        
        if right_hand_gesture is not None:
            if right_hand_gesture:
                self.right_hand_gesture_chip.setText(f"Right: {right_hand_gesture}")
                self.right_hand_gesture_chip.setStyleSheet("""
                    QLabel {
                        background-color: #0d5016;
                        color: #4ade80;
                        border: 1px solid #16a34a;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
            else:
                self.right_hand_gesture_chip.setText("Right: None")
                self.right_hand_gesture_chip.setStyleSheet("""
                    QLabel {
                        background-color: #333;
                        color: #888;
                        border: 1px solid #555;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
        
        if face_gesture is not None:
            if face_gesture:
                self.face_gesture_chip.setText(f"Face: {face_gesture}")
                self.face_gesture_chip.setStyleSheet("""
                    QLabel {
                        background-color: #4c1d95;
                        color: #c084fc;
                        border: 1px solid #7c3aed;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
            else:
                self.face_gesture_chip.setText("Face: None")
                self.face_gesture_chip.setStyleSheet("""
                    QLabel {
                        background-color: #333;
                        color: #888;
                        border: 1px solid #555;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
        
        if ai_status is not None:
            if ai_status == "processing":
                self.ai_status_chip.setText("AI: Processing")
                self.ai_status_chip.setStyleSheet("""
                    QLabel {
                        background-color: #ea580c;
                        color: #fed7aa;
                        border: 1px solid #f97316;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
            elif ai_status == "ready":
                self.ai_status_chip.setText("AI: Ready")
                self.ai_status_chip.setStyleSheet("""
                    QLabel {
                        background-color: #333;
                        color: #888;
                        border: 1px solid #555;
                        border-radius: 17px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                """)
    
    def show_response(self, response_text):
        # AI 상태를 ready로 변경
        self.update_gesture_status(ai_status="ready")
        
        response_window = ResponseWindow(response_text, self)
        response_window.show()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "GestureAgent", 
                                  "Application minimized to tray. Use the tray icon to access options.")


def create_app():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    window = MainWindow(config)
    return app, window