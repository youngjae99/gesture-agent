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
        self.setFixedSize(640, 520)
        
        self.init_ui()
        self.init_system_tray()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        header = QLabel("GestureAgent - Touchless AI Interface")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(header)
        
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.camera_frame = QLabel()
        self.camera_frame.setFixedSize(640, 480)
        self.camera_frame.setStyleSheet("border: 2px solid #333; background-color: #222;")
        self.camera_frame.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camera_frame)
        
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Detection")
        self.start_btn.clicked.connect(self.toggle_detection)
        button_layout.addWidget(self.start_btn)
        
        config_btn = QPushButton("Configuration")
        config_btn.clicked.connect(self.show_config)
        button_layout.addWidget(config_btn)
        
        minimize_btn = QPushButton("Minimize to Tray")
        minimize_btn.clicked.connect(self.hide)
        button_layout.addWidget(minimize_btn)
        
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
        
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
    
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create a simple icon for the system tray
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
    
    def show_response(self, response_text):
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