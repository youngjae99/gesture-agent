import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv, set_key


class ConfigManager:
    def __init__(self, config_file: str = "config.json", env_file: str = ".env"):
        self.config_file = config_file
        self.env_file = env_file
        self.config = {}
        self.env_vars = {}
        
        self.load_config()
        self.load_env_vars()
    
    def load_config(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                self.save_config()
            
            return self.config
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = self.get_default_config()
            return self.config
    
    def load_env_vars(self) -> Dict[str, str]:
        try:
            load_dotenv(self.env_file)
            
            self.env_vars = {
                'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
                'ASSISTANT_ID': os.getenv('ASSISTANT_ID', ''),
                'SCREENSHOT_DIR': os.getenv('SCREENSHOT_DIR', './screenshots'),
                'GESTURE_SENSITIVITY': float(os.getenv('GESTURE_SENSITIVITY', '0.8')),
                'CAPTURE_MODE': os.getenv('CAPTURE_MODE', 'fullscreen')
            }
            
            return self.env_vars
            
        except Exception as e:
            print(f"Error loading environment variables: {e}")
            return {}
    
    def get_default_config(self) -> Dict[str, Any]:
        return {
            "gestures": {
                "wave": {
                    "enabled": True,
                    "description": "Horizontal hand wave",
                    "confidence_threshold": 0.8
                },
                "palm_up": {
                    "enabled": True,
                    "description": "Open palm facing camera",
                    "confidence_threshold": 0.7
                }
            },
            "screenshot": {
                "mode": "fullscreen",
                "quality": 90,
                "format": "PNG"
            },
            "ui": {
                "show_camera_preview": True,
                "response_window_timeout": 10,
                "enable_tts": False
            },
            "openai": {
                "model": "gpt-4",
                "max_tokens": 500,
                "temperature": 0.7
            },
            "system": {
                "camera_device": 0,
                "fps": 30,
                "log_level": "INFO",
                "auto_cleanup_days": 7
            }
        }
    
    def save_config(self) -> bool:
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def update_config(self, path: str, value: Any) -> bool:
        try:
            keys = path.split('.')
            target = self.config
            
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            target[keys[-1]] = value
            return self.save_config()
            
        except Exception as e:
            print(f"Error updating config at {path}: {e}")
            return False
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        try:
            keys = path.split('.')
            target = self.config
            
            for key in keys:
                if key in target:
                    target = target[key]
                else:
                    return default
            
            return target
            
        except Exception as e:
            print(f"Error getting config value at {path}: {e}")
            return default
    
    def set_env_var(self, key: str, value: str) -> bool:
        try:
            if not os.path.exists(self.env_file):
                with open(self.env_file, 'w') as f:
                    f.write("")
            
            set_key(self.env_file, key, value)
            self.env_vars[key] = value
            os.environ[key] = value
            
            return True
            
        except Exception as e:
            print(f"Error setting environment variable {key}: {e}")
            return False
    
    def get_env_var(self, key: str, default: str = "") -> str:
        return self.env_vars.get(key, default)
    
    def validate_config(self) -> tuple[bool, list]:
        errors = []
        
        if not self.get_env_var('OPENAI_API_KEY'):
            errors.append("OpenAI API key is required")
        
        gesture_sensitivity = self.get_config_value('gestures.wave.confidence_threshold')
        if not (0.1 <= gesture_sensitivity <= 1.0):
            errors.append("Gesture sensitivity must be between 0.1 and 1.0")
        
        screenshot_quality = self.get_config_value('screenshot.quality')
        if not (10 <= screenshot_quality <= 100):
            errors.append("Screenshot quality must be between 10 and 100")
        
        screenshot_mode = self.get_config_value('screenshot.mode')
        if screenshot_mode not in ['fullscreen', 'active_window']:
            errors.append("Screenshot mode must be 'fullscreen' or 'active_window'")
        
        return len(errors) == 0, errors
    
    def reset_to_defaults(self) -> bool:
        try:
            self.config = self.get_default_config()
            return self.save_config()
            
        except Exception as e:
            print(f"Error resetting config to defaults: {e}")
            return False
    
    def export_config(self, filepath: str) -> bool:
        try:
            export_data = {
                'config': self.config,
                'env_vars': {k: v for k, v in self.env_vars.items() 
                           if k != 'OPENAI_API_KEY'}
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=4)
            
            return True
            
        except Exception as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            if 'config' in import_data:
                self.config = import_data['config']
                self.save_config()
            
            if 'env_vars' in import_data:
                for key, value in import_data['env_vars'].items():
                    if key != 'OPENAI_API_KEY':
                        self.set_env_var(key, str(value))
            
            return True
            
        except Exception as e:
            print(f"Error importing config: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        return {
            'config': self.config,
            'env_vars': self.env_vars
        }