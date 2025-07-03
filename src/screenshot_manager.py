import os
import time
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image
import Quartz
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
from AppKit import NSWorkspace


class ScreenshotManager:
    def __init__(self, screenshot_dir: str = "./screenshots"):
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)
    
    def capture_fullscreen(self, quality: int = 90, format: str = "PNG") -> Optional[str]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fullscreen_{timestamp}.{format.lower()}"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            region = Quartz.CGRectInfinite
            image = Quartz.CGWindowListCreateImage(
                region,
                Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID,
                Quartz.kCGWindowImageDefault
            )
            
            if image:
                width = Quartz.CGImageGetWidth(image)
                height = Quartz.CGImageGetHeight(image)
                
                bitmap_rep = Quartz.NSBitmapImageRep.alloc()
                bitmap_rep.initWithCGImage_(image)
                
                if format.upper() == "PNG":
                    image_data = bitmap_rep.representationUsingType_properties_(
                        Quartz.NSBitmapImageFileTypePNG, None
                    )
                else:
                    properties = {Quartz.NSImageCompressionFactor: quality / 100.0}
                    image_data = bitmap_rep.representationUsingType_properties_(
                        Quartz.NSBitmapImageFileTypeJPEG, properties
                    )
                
                image_data.writeToFile_atomically_(filepath, True)
                return filepath
            
        except Exception as e:
            print(f"Error capturing fullscreen: {e}")
            return None
    
    def get_active_window_info(self) -> Optional[dict]:
        try:
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            
            if not active_app:
                return None
            
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            )
            
            for window in window_list:
                if (window.get('kCGWindowOwnerPID') == active_app['NSApplicationProcessIdentifier'] and
                    window.get('kCGWindowLayer') == 0):
                    
                    bounds = window.get('kCGWindowBounds')
                    if bounds:
                        return {
                            'app_name': active_app['NSApplicationName'],
                            'window_id': window.get('kCGWindowNumber'),
                            'bounds': bounds,
                            'title': window.get('kCGWindowName', 'Unknown')
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting active window info: {e}")
            return None
    
    def capture_active_window(self, quality: int = 90, format: str = "PNG") -> Optional[str]:
        try:
            window_info = self.get_active_window_info()
            if not window_info:
                return self.capture_fullscreen(quality, format)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            app_name = window_info['app_name'].replace(' ', '_')
            filename = f"window_{app_name}_{timestamp}.{format.lower()}"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            window_id = window_info['window_id']
            bounds = window_info['bounds']
            
            region = Quartz.CGRectMake(
                bounds['X'],
                bounds['Y'], 
                bounds['Width'],
                bounds['Height']
            )
            
            image = Quartz.CGWindowListCreateImage(
                region,
                Quartz.kCGWindowListOptionOnScreenOnly,
                window_id,
                Quartz.kCGWindowImageBoundsIgnoreFraming
            )
            
            if image:
                bitmap_rep = Quartz.NSBitmapImageRep.alloc()
                bitmap_rep.initWithCGImage_(image)
                
                if format.upper() == "PNG":
                    image_data = bitmap_rep.representationUsingType_properties_(
                        Quartz.NSBitmapImageFileTypePNG, None
                    )
                else:
                    properties = {Quartz.NSImageCompressionFactor: quality / 100.0}
                    image_data = bitmap_rep.representationUsingType_properties_(
                        Quartz.NSBitmapImageFileTypeJPEG, properties
                    )
                
                image_data.writeToFile_atomically_(filepath, True)
                return filepath
            
        except Exception as e:
            print(f"Error capturing active window: {e}")
            return self.capture_fullscreen(quality, format)
    
    def capture_screenshot(self, mode: str = "fullscreen", **kwargs) -> Optional[str]:
        if mode == "fullscreen":
            return self.capture_fullscreen(**kwargs)
        elif mode == "active_window":
            return self.capture_active_window(**kwargs)
        else:
            print(f"Unknown capture mode: {mode}")
            return self.capture_fullscreen(**kwargs)
    
    def cleanup_old_screenshots(self, max_age_days: int = 7):
        try:
            current_time = time.time()
            cutoff_time = current_time - (max_age_days * 24 * 60 * 60)
            
            for filename in os.listdir(self.screenshot_dir):
                filepath = os.path.join(self.screenshot_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        print(f"Removed old screenshot: {filename}")
                        
        except Exception as e:
            print(f"Error cleaning up screenshots: {e}")
    
    def get_recent_screenshots(self, count: int = 10) -> list:
        try:
            screenshots = []
            for filename in os.listdir(self.screenshot_dir):
                filepath = os.path.join(self.screenshot_dir, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    screenshots.append({
                        'filename': filename,
                        'filepath': filepath,
                        'timestamp': os.path.getmtime(filepath)
                    })
            
            screenshots.sort(key=lambda x: x['timestamp'], reverse=True)
            return screenshots[:count]
            
        except Exception as e:
            print(f"Error getting recent screenshots: {e}")
            return []