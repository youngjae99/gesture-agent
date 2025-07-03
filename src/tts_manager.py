import pyttsx3
import subprocess
import platform
from typing import Optional


class TTSManager:
    def __init__(self, use_system_tts: bool = True):
        self.use_system_tts = use_system_tts
        self.engine = None
        
        if not use_system_tts:
            try:
                self.engine = pyttsx3.init()
                self._configure_engine()
            except Exception as e:
                print(f"Failed to initialize pyttsx3: {e}")
                self.use_system_tts = True
    
    def _configure_engine(self):
        if self.engine:
            voices = self.engine.getProperty('voices')
            if voices:
                self.engine.setProperty('voice', voices[0].id)
            
            self.engine.setProperty('rate', 180)
            self.engine.setProperty('volume', 0.8)
    
    def speak_text(self, text: str, block: bool = False) -> bool:
        try:
            if self.use_system_tts and platform.system() == "Darwin":
                return self._speak_macos(text, block)
            elif self.engine:
                return self._speak_pyttsx3(text, block)
            else:
                print(f"TTS not available: {text}")
                return False
                
        except Exception as e:
            print(f"Error in TTS: {e}")
            return False
    
    def _speak_macos(self, text: str, block: bool = False) -> bool:
        try:
            clean_text = text.replace('"', '\\"').replace("'", "\\'")
            cmd = ["say", clean_text]
            
            if block:
                subprocess.run(cmd, check=True)
            else:
                subprocess.Popen(cmd)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"macOS TTS error: {e}")
            return False
    
    def _speak_pyttsx3(self, text: str, block: bool = False) -> bool:
        try:
            self.engine.say(text)
            if block:
                self.engine.runAndWait()
            
            return True
            
        except Exception as e:
            print(f"pyttsx3 TTS error: {e}")
            return False
    
    def stop_speaking(self):
        try:
            if self.use_system_tts and platform.system() == "Darwin":
                subprocess.run(["killall", "say"], check=False)
            elif self.engine:
                self.engine.stop()
                
        except Exception as e:
            print(f"Error stopping TTS: {e}")
    
    def is_speaking(self) -> bool:
        try:
            if self.use_system_tts and platform.system() == "Darwin":
                result = subprocess.run(["pgrep", "say"], capture_output=True)
                return result.returncode == 0
            elif self.engine:
                return self.engine.isBusy()
            
        except Exception as e:
            print(f"Error checking TTS status: {e}")
        
        return False
    
    def set_voice_properties(self, rate: Optional[int] = None, 
                           volume: Optional[float] = None):
        if self.engine:
            if rate is not None:
                self.engine.setProperty('rate', rate)
            if volume is not None:
                self.engine.setProperty('volume', volume)
    
    def get_available_voices(self) -> list:
        voices = []
        
        try:
            if self.engine:
                engine_voices = self.engine.getProperty('voices')
                for voice in engine_voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'language': getattr(voice, 'language', 'Unknown')
                    })
            
        except Exception as e:
            print(f"Error getting voices: {e}")
        
        return voices
    
    def cleanup(self):
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass