#!/usr/bin/env python3
"""
Test script to verify all components work properly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    print("Testing imports...")
    
    try:
        from src.gesture_detector import GestureDetector
        print("✅ GestureDetector imported successfully")
    except Exception as e:
        print(f"❌ GestureDetector import failed: {e}")
    
    try:
        from src.ai_assistant import AIAssistant
        print("✅ AIAssistant imported successfully")
    except Exception as e:
        print(f"❌ AIAssistant import failed: {e}")
    
    try:
        from src.screenshot_manager import ScreenshotManager
        print("✅ ScreenshotManager imported successfully")
    except Exception as e:
        print(f"❌ ScreenshotManager import failed: {e}")
    
    try:
        from src.tts_manager import TTSManager
        print("✅ TTSManager imported successfully")
    except Exception as e:
        print(f"❌ TTSManager import failed: {e}")
    
    try:
        from src.config_manager import ConfigManager
        print("✅ ConfigManager imported successfully")
    except Exception as e:
        print(f"❌ ConfigManager import failed: {e}")
    
    try:
        from src.logger import GestureAgentLogger
        print("✅ Logger imported successfully")
    except Exception as e:
        print(f"❌ Logger import failed: {e}")

def test_config():
    print("\nTesting configuration...")
    
    try:
        from src.config_manager import ConfigManager
        config_manager = ConfigManager()
        
        print(f"✅ Config loaded: {len(config_manager.config)} sections")
        
        is_valid, errors = config_manager.validate_config()
        if is_valid:
            print("✅ Configuration is valid")
        else:
            print(f"⚠️  Configuration issues: {errors}")
            
    except Exception as e:
        print(f"❌ Config test failed: {e}")

def test_gesture_detector():
    print("\nTesting gesture detector...")
    
    try:
        from src.gesture_detector import GestureDetector
        detector = GestureDetector()
        print("✅ GestureDetector initialized successfully")
        detector.cleanup()
        
    except Exception as e:
        print(f"❌ GestureDetector test failed: {e}")

def test_screenshot():
    print("\nTesting screenshot manager...")
    
    try:
        from src.screenshot_manager import ScreenshotManager
        screenshot_manager = ScreenshotManager()
        
        # Test fullscreen capture
        screenshot_path = screenshot_manager.capture_fullscreen()
        if screenshot_path and os.path.exists(screenshot_path):
            print(f"✅ Screenshot captured: {screenshot_path}")
            os.remove(screenshot_path)  # Clean up test file
        else:
            print("⚠️  Screenshot capture failed (may need screen recording permission)")
            
    except Exception as e:
        print(f"❌ Screenshot test failed: {e}")

def test_tts():
    print("\nTesting TTS manager...")
    
    try:
        from src.tts_manager import TTSManager
        tts = TTSManager()
        print("✅ TTSManager initialized successfully")
        tts.cleanup()
        
    except Exception as e:
        print(f"❌ TTS test failed: {e}")

if __name__ == "__main__":
    print("🧪 GestureAgent Component Tests")
    print("=" * 40)
    
    test_imports()
    test_config()
    test_gesture_detector()
    test_screenshot()
    test_tts()
    
    print("\n" + "=" * 40)
    print("✅ Component testing completed!")
    print("\nTo run the full application:")
    print("  source venv/bin/activate && python run.py")