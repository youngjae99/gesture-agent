import cv2
import mediapipe as mp
import numpy as np
import time
from typing import Dict, Optional, Tuple


class GestureDetector:
    def __init__(self, confidence_threshold: float = 0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.confidence_threshold = confidence_threshold
        
        self.wave_history = []
        self.palm_up_start_time = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0
        
    def detect_wave_gesture(self, landmarks) -> bool:
        wrist = landmarks[0]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        fingers_up = [
            index_tip.y < landmarks[6].y,
            middle_tip.y < landmarks[10].y,
            ring_tip.y < landmarks[14].y,
            pinky_tip.y < landmarks[18].y
        ]
        
        if sum(fingers_up) >= 3:
            self.wave_history.append(wrist.x)
            
            if len(self.wave_history) > 10:
                self.wave_history.pop(0)
            
            if len(self.wave_history) >= 8:
                x_positions = np.array(self.wave_history)
                x_diff = np.diff(x_positions)
                
                direction_changes = 0
                for i in range(1, len(x_diff)):
                    if (x_diff[i] > 0 and x_diff[i-1] < 0) or (x_diff[i] < 0 and x_diff[i-1] > 0):
                        direction_changes += 1
                
                movement_range = max(x_positions) - min(x_positions)
                
                if direction_changes >= 2 and movement_range > 0.1:
                    self.wave_history.clear()
                    return True
        else:
            self.wave_history.clear()
            
        return False
    
    def detect_palm_up_gesture(self, landmarks) -> bool:
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]
        pinky_mcp = landmarks[17]
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        palm_facing_up = all([
            tip.y < mcp.y for tip, mcp in [
                (index_tip, index_mcp),
                (middle_tip, middle_mcp),
                (ring_tip, ring_mcp),
                (pinky_tip, pinky_mcp)
            ]
        ])
        
        fingers_extended = all([
            abs(tip.y - mcp.y) > 0.05 for tip, mcp in [
                (index_tip, index_mcp),
                (middle_tip, middle_mcp),
                (ring_tip, ring_mcp),
                (pinky_tip, pinky_mcp)
            ]
        ])
        
        if palm_facing_up and fingers_extended:
            if self.palm_up_start_time is None:
                self.palm_up_start_time = time.time()
            elif time.time() - self.palm_up_start_time > 1.5:
                self.palm_up_start_time = None
                return True
        else:
            self.palm_up_start_time = None
            
        return False
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[str]]:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        detected_gesture = None
        current_time = time.time()
        
        if results.multi_hand_landmarks and (current_time - self.last_gesture_time) > self.gesture_cooldown:
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = hand_landmarks.landmark
                
                if self.detect_wave_gesture(landmarks):
                    detected_gesture = "wave"
                    self.last_gesture_time = current_time
                    break
                elif self.detect_palm_up_gesture(landmarks):
                    detected_gesture = "palm_up"
                    self.last_gesture_time = current_time
                    break
                
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
        
        if self.palm_up_start_time is not None:
            remaining_time = 1.5 - (current_time - self.palm_up_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Hold palm up: {remaining_time:.1f}s", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return frame, detected_gesture
    
    def cleanup(self):
        self.hands.close()