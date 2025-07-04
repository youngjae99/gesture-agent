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
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # 얼굴 감지 모듈 추가
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        
        # 얼굴 메시 모듈 추가 (표정 및 눈동자 감지용)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.confidence_threshold = confidence_threshold
        
        self.wave_history = []
        self.palm_up_start_time = None
        self.thumbs_up_start_time = None
        self.peace_sign_start_time = None
        self.fist_start_time = None
        self.face_detected_start_time = None
        self.smile_start_time = None
        self.blink_start_time = None
        self.wink_start_time = None
        self.eyebrows_raised_start_time = None
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.0
        
        # 눈 깜빡임 감지를 위한 히스토리
        self.left_eye_history = []
        self.right_eye_history = []
        self.eye_aspect_ratio_threshold = 0.25
        
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
    
    def detect_thumbs_up_gesture(self, landmarks) -> bool:
        """엄지손가락 업 제스처 감지"""
        thumb_tip = landmarks[4]
        thumb_mcp = landmarks[2]
        
        # 다른 손가락들
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]
        pinky_mcp = landmarks[17]
        
        # 엄지손가락이 위로 올라가 있는지 확인
        thumb_up = thumb_tip.y < thumb_mcp.y
        
        # 다른 손가락들이 접혀있는지 확인
        other_fingers_down = all([
            index_tip.y > index_mcp.y,
            middle_tip.y > middle_mcp.y,
            ring_tip.y > ring_mcp.y,
            pinky_tip.y > pinky_mcp.y
        ])
        
        if thumb_up and other_fingers_down:
            if self.thumbs_up_start_time is None:
                self.thumbs_up_start_time = time.time()
            elif time.time() - self.thumbs_up_start_time > 1.0:
                self.thumbs_up_start_time = None
                return True
        else:
            self.thumbs_up_start_time = None
            
        return False
    
    def detect_peace_sign_gesture(self, landmarks) -> bool:
        """브이 사인 제스처 감지"""
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]
        pinky_mcp = landmarks[17]
        
        # 검지와 중지만 펴져있는지 확인
        index_up = index_tip.y < index_mcp.y
        middle_up = middle_tip.y < middle_mcp.y
        ring_down = ring_tip.y > ring_mcp.y
        pinky_down = pinky_tip.y > pinky_mcp.y
        
        # 검지와 중지가 벌어져 있는지 확인
        fingers_spread = abs(index_tip.x - middle_tip.x) > 0.05
        
        if index_up and middle_up and ring_down and pinky_down and fingers_spread:
            if self.peace_sign_start_time is None:
                self.peace_sign_start_time = time.time()
            elif time.time() - self.peace_sign_start_time > 1.0:
                self.peace_sign_start_time = None
                return True
        else:
            self.peace_sign_start_time = None
            
        return False
    
    def detect_fist_gesture(self, landmarks) -> bool:
        """주먹 제스처 감지"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        thumb_mcp = landmarks[2]
        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]
        pinky_mcp = landmarks[17]
        
        # 모든 손가락이 접혀있는지 확인
        all_fingers_down = all([
            thumb_tip.y > thumb_mcp.y,
            index_tip.y > index_mcp.y,
            middle_tip.y > middle_mcp.y,
            ring_tip.y > ring_mcp.y,
            pinky_tip.y > pinky_mcp.y
        ])
        
        if all_fingers_down:
            if self.fist_start_time is None:
                self.fist_start_time = time.time()
            elif time.time() - self.fist_start_time > 1.0:
                self.fist_start_time = None
                return True
        else:
            self.fist_start_time = None
            
        return False
    
    def detect_face_gesture(self, face_detections) -> bool:
        """얼굴 감지를 통한 제스처 인식"""
        if face_detections.detections:
            # 얼굴이 감지되면 1.5초 유지 후 제스처로 인식
            if self.face_detected_start_time is None:
                self.face_detected_start_time = time.time()
            elif time.time() - self.face_detected_start_time > 1.5:
                self.face_detected_start_time = None
                return True
        else:
            self.face_detected_start_time = None
            
        return False
    
    def calculate_eye_aspect_ratio(self, eye_landmarks) -> float:
        """눈의 종횡비 계산 (Eye Aspect Ratio)"""
        # 눈의 세로 거리 계산
        A = np.linalg.norm(np.array([eye_landmarks[1].x, eye_landmarks[1].y]) - 
                          np.array([eye_landmarks[5].x, eye_landmarks[5].y]))
        B = np.linalg.norm(np.array([eye_landmarks[2].x, eye_landmarks[2].y]) - 
                          np.array([eye_landmarks[4].x, eye_landmarks[4].y]))
        
        # 눈의 가로 거리 계산
        C = np.linalg.norm(np.array([eye_landmarks[0].x, eye_landmarks[0].y]) - 
                          np.array([eye_landmarks[3].x, eye_landmarks[3].y]))
        
        # EAR 계산
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink_gesture(self, face_landmarks) -> bool:
        """눈 깜빡임 감지"""
        # 왼쪽 눈 랜드마크 인덱스 (MediaPipe Face Mesh)
        left_eye_indices = [362, 385, 387, 263, 373, 380]
        # 오른쪽 눈 랜드마크 인덱스
        right_eye_indices = [33, 160, 158, 133, 153, 144]
        
        left_eye_landmarks = [face_landmarks[i] for i in left_eye_indices]
        right_eye_landmarks = [face_landmarks[i] for i in right_eye_indices]
        
        left_ear = self.calculate_eye_aspect_ratio(left_eye_landmarks)
        right_ear = self.calculate_eye_aspect_ratio(right_eye_landmarks)
        
        # 양쪽 눈 EAR 평균
        avg_ear = (left_ear + right_ear) / 2.0
        
        # 깜빡임 히스토리에 추가
        self.left_eye_history.append(left_ear)
        self.right_eye_history.append(right_ear)
        
        # 히스토리 길이 제한
        if len(self.left_eye_history) > 5:
            self.left_eye_history.pop(0)
            self.right_eye_history.pop(0)
        
        # 빠른 깜빡임 감지 (양쪽 눈 동시)
        if len(self.left_eye_history) >= 3:
            if (avg_ear < self.eye_aspect_ratio_threshold and 
                all(ear > self.eye_aspect_ratio_threshold for ear in self.left_eye_history[-3:-1])):
                return True
        
        return False
    
    def detect_wink_gesture(self, face_landmarks) -> bool:
        """윙크 감지"""
        # 왼쪽 눈 랜드마크 인덱스
        left_eye_indices = [362, 385, 387, 263, 373, 380]
        # 오른쪽 눈 랜드마크 인덱스
        right_eye_indices = [33, 160, 158, 133, 153, 144]
        
        left_eye_landmarks = [face_landmarks[i] for i in left_eye_indices]
        right_eye_landmarks = [face_landmarks[i] for i in right_eye_indices]
        
        left_ear = self.calculate_eye_aspect_ratio(left_eye_landmarks)
        right_ear = self.calculate_eye_aspect_ratio(right_eye_landmarks)
        
        # 한쪽 눈은 감고 다른 쪽 눈은 뜨고 있는 상태
        wink_detected = False
        if left_ear < self.eye_aspect_ratio_threshold and right_ear > self.eye_aspect_ratio_threshold:
            wink_detected = True
        elif right_ear < self.eye_aspect_ratio_threshold and left_ear > self.eye_aspect_ratio_threshold:
            wink_detected = True
        
        if wink_detected:
            if self.wink_start_time is None:
                self.wink_start_time = time.time()
            elif time.time() - self.wink_start_time > 0.5:  # 0.5초 유지
                self.wink_start_time = None
                return True
        else:
            self.wink_start_time = None
            
        return False
    
    def detect_smile_gesture(self, face_landmarks) -> bool:
        """미소 감지"""
        # 입 모서리 랜드마크 인덱스
        mouth_left = face_landmarks[61]  # 왼쪽 입 모서리
        mouth_right = face_landmarks[291]  # 오른쪽 입 모서리
        mouth_top = face_landmarks[13]  # 입 위쪽
        mouth_bottom = face_landmarks[14]  # 입 아래쪽
        
        # 입 모서리가 올라가 있는지 확인
        mouth_width = abs(mouth_right.x - mouth_left.x)
        mouth_height = abs(mouth_top.y - mouth_bottom.y)
        
        # 미소 비율 계산
        smile_ratio = mouth_width / mouth_height if mouth_height > 0 else 0
        
        # 입 모서리가 입 중앙보다 높이 올라가 있는지 확인
        mouth_center_y = (mouth_top.y + mouth_bottom.y) / 2
        corners_raised = (mouth_left.y < mouth_center_y and mouth_right.y < mouth_center_y)
        
        if smile_ratio > 3.0 and corners_raised:
            if self.smile_start_time is None:
                self.smile_start_time = time.time()
            elif time.time() - self.smile_start_time > 1.0:
                self.smile_start_time = None
                return True
        else:
            self.smile_start_time = None
            
        return False
    
    def detect_eyebrows_raised_gesture(self, face_landmarks) -> bool:
        """눈썹 올림 감지"""
        # 눈썹 랜드마크 인덱스
        left_eyebrow_top = face_landmarks[70]
        right_eyebrow_top = face_landmarks[300]
        left_eye_top = face_landmarks[159]
        right_eye_top = face_landmarks[386]
        
        # 눈썹과 눈 사이의 거리
        left_distance = abs(left_eyebrow_top.y - left_eye_top.y)
        right_distance = abs(right_eyebrow_top.y - right_eye_top.y)
        
        avg_distance = (left_distance + right_distance) / 2
        
        # 눈썹이 평소보다 높이 올라가 있는지 확인
        if avg_distance > 0.02:  # 임계값 조정 필요
            if self.eyebrows_raised_start_time is None:
                self.eyebrows_raised_start_time = time.time()
            elif time.time() - self.eyebrows_raised_start_time > 1.0:
                self.eyebrows_raised_start_time = None
                return True
        else:
            self.eyebrows_raised_start_time = None
            
        return False
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[str]]:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 손 제스처 감지
        hand_results = self.hands.process(rgb_frame)
        
        # 얼굴 감지
        face_results = self.face_detection.process(rgb_frame)
        
        # 얼굴 메시 감지 (표정 분석용)
        face_mesh_results = self.face_mesh.process(rgb_frame)
        
        detected_left_hand_gesture = None
        detected_right_hand_gesture = None
        detected_face_gesture = None
        current_time = time.time()
        
        # 현재 제스처 상태 저장 (GUI 업데이트용)
        self.current_left_hand_gesture = None
        self.current_right_hand_gesture = None
        self.current_face_gesture = None
        
        # 손 제스처 감지 처리 (양손 지원)
        if hand_results.multi_hand_landmarks and hand_results.multi_handedness:
            for hand_landmarks, handedness in zip(hand_results.multi_hand_landmarks, hand_results.multi_handedness):
                landmarks = hand_landmarks.landmark
                
                # 손의 좌우 구분 (MediaPipe는 카메라 관점에서 판단하므로 반전 필요)
                is_right_hand = handedness.classification[0].label == "Left"  # 카메라 관점에서 Left = 실제 오른손
                is_left_hand = handedness.classification[0].label == "Right"  # 카메라 관점에서 Right = 실제 왼손
                
                # 제스처 감지
                detected_gesture = None
                if self.detect_wave_gesture(landmarks):
                    detected_gesture = "wave"
                elif self.detect_palm_up_gesture(landmarks):
                    detected_gesture = "palm_up"
                elif self.detect_thumbs_up_gesture(landmarks):
                    detected_gesture = "thumbs_up"
                elif self.detect_peace_sign_gesture(landmarks):
                    detected_gesture = "peace_sign"
                elif self.detect_fist_gesture(landmarks):
                    detected_gesture = "fist"
                
                # 좌우 손에 따라 저장
                if detected_gesture:
                    if is_left_hand:
                        detected_left_hand_gesture = detected_gesture
                        self.current_left_hand_gesture = detected_gesture
                    elif is_right_hand:
                        detected_right_hand_gesture = detected_gesture
                        self.current_right_hand_gesture = detected_gesture
                
                # 손 랜드마크 그리기
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                )
        
        # 얼굴 제스처 감지 처리 (손 제스처와 독립적으로 처리)
        if face_mesh_results.multi_face_landmarks:
            for face_landmarks in face_mesh_results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                
                # 빠른 깜빡임 감지
                if self.detect_blink_gesture(landmarks):
                    detected_face_gesture = "blink"
                    self.current_face_gesture = "blink"
                    break
                # 윙크 감지
                elif self.detect_wink_gesture(landmarks):
                    detected_face_gesture = "wink"
                    self.current_face_gesture = "wink"
                    break
                # 미소 감지
                elif self.detect_smile_gesture(landmarks):
                    detected_face_gesture = "smile"
                    self.current_face_gesture = "smile"
                    break
                # 눈썹 올림 감지
                elif self.detect_eyebrows_raised_gesture(landmarks):
                    detected_face_gesture = "eyebrows_raised"
                    self.current_face_gesture = "eyebrows_raised"
                    break
        
        # 기본 얼굴 감지 (표정이 감지되지 않을 때)
        elif self.detect_face_gesture(face_results):
            detected_face_gesture = "face_detected"
            self.current_face_gesture = "face_detected"
        
        # 얼굴 경계 박스 그리기
        if face_results.detections:
            for detection in face_results.detections:
                self.mp_drawing.draw_detection(frame, detection)
        
        # 얼굴 메시 그리기 (선택적)
        if face_mesh_results.multi_face_landmarks:
            for face_landmarks in face_mesh_results.multi_face_landmarks:
                # 주요 랜드마크만 그리기 (눈, 입, 눈썹)
                self.mp_drawing.draw_landmarks(
                    frame, face_landmarks, 
                    self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                )
        
        # 진행 중인 제스처에 대한 타이머 표시
        y_offset = 60
        if self.palm_up_start_time is not None:
            remaining_time = 1.5 - (current_time - self.palm_up_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Hold palm up: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                y_offset += 30
        
        if self.thumbs_up_start_time is not None:
            remaining_time = 1.0 - (current_time - self.thumbs_up_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Hold thumbs up: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y_offset += 30
        
        if self.peace_sign_start_time is not None:
            remaining_time = 1.0 - (current_time - self.peace_sign_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Hold peace sign: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                y_offset += 30
        
        if self.fist_start_time is not None:
            remaining_time = 1.0 - (current_time - self.fist_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Hold fist: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                y_offset += 30
        
        if self.face_detected_start_time is not None:
            remaining_time = 1.5 - (current_time - self.face_detected_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Face detected: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                y_offset += 30
        
        if self.smile_start_time is not None:
            remaining_time = 1.0 - (current_time - self.smile_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Smile detected: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                y_offset += 30
        
        if self.wink_start_time is not None:
            remaining_time = 0.5 - (current_time - self.wink_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Wink detected: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 30
        
        if self.eyebrows_raised_start_time is not None:
            remaining_time = 1.0 - (current_time - self.eyebrows_raised_start_time)
            if remaining_time > 0:
                cv2.putText(frame, f"Eyebrows raised: {remaining_time:.1f}s", 
                           (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 0, 128), 2)
        
        # 제스처 조합 결정 및 AI 호출 처리
        detected_gesture = None
        if (current_time - self.last_gesture_time) > self.gesture_cooldown:
            # 양손 + 얼굴 조합
            if detected_left_hand_gesture and detected_right_hand_gesture and detected_face_gesture:
                detected_gesture = f"left_{detected_left_hand_gesture}+right_{detected_right_hand_gesture}+{detected_face_gesture}"
                self.last_gesture_time = current_time
            # 양손 조합
            elif detected_left_hand_gesture and detected_right_hand_gesture:
                detected_gesture = f"left_{detected_left_hand_gesture}+right_{detected_right_hand_gesture}"
                self.last_gesture_time = current_time
            # 왼손 + 얼굴
            elif detected_left_hand_gesture and detected_face_gesture:
                detected_gesture = f"left_{detected_left_hand_gesture}+{detected_face_gesture}"
                self.last_gesture_time = current_time
            # 오른손 + 얼굴
            elif detected_right_hand_gesture and detected_face_gesture:
                detected_gesture = f"right_{detected_right_hand_gesture}+{detected_face_gesture}"
                self.last_gesture_time = current_time
            # 단일 제스처
            elif detected_left_hand_gesture:
                detected_gesture = f"left_{detected_left_hand_gesture}"
                self.last_gesture_time = current_time
            elif detected_right_hand_gesture:
                detected_gesture = f"right_{detected_right_hand_gesture}"
                self.last_gesture_time = current_time
            elif detected_face_gesture:
                detected_gesture = detected_face_gesture
                self.last_gesture_time = current_time
        
        # 화면에 제스처 상태 칩 표시
        self._draw_gesture_chips(frame, detected_left_hand_gesture, detected_right_hand_gesture, detected_face_gesture)
        
        return frame, detected_gesture
    
    def _draw_gesture_chips(self, frame, left_hand_gesture, right_hand_gesture, face_gesture):
        """제스처 상태를 칩 형태로 화면에 표시"""
        height, width = frame.shape[:2]
        
        # 칩 그리기 시작 위치 (우상단)
        chip_x = width - 250
        chip_y = 30
        chip_height = 25
        chip_margin = 35
        
        # Left Hand Gesture 칩
        if left_hand_gesture:
            # 배경 사각형
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (0, 100, 150), -1)
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (0, 150, 255), 2)
            
            # 텍스트
            cv2.putText(frame, f"Left: {left_hand_gesture}", (chip_x + 5, chip_y + 18), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            # 비활성 상태
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (50, 50, 50), -1)
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (100, 100, 100), 2)
            cv2.putText(frame, "Left: None", (chip_x + 5, chip_y + 18), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        # Right Hand Gesture 칩
        chip_y += chip_margin
        if right_hand_gesture:
            # 배경 사각형
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (0, 150, 0), -1)
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (0, 255, 0), 2)
            
            # 텍스트
            cv2.putText(frame, f"Right: {right_hand_gesture}", (chip_x + 5, chip_y + 18), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            # 비활성 상태
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (50, 50, 50), -1)
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (100, 100, 100), 2)
            cv2.putText(frame, "Right: None", (chip_x + 5, chip_y + 18), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        # Face Gesture 칩
        chip_y += chip_margin
        if face_gesture:
            # 배경 사각형
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (150, 0, 150), -1)
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (255, 0, 255), 2)
            
            # 텍스트
            cv2.putText(frame, f"Face: {face_gesture}", (chip_x + 5, chip_y + 18), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            # 비활성 상태
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (50, 50, 50), -1)
            cv2.rectangle(frame, (chip_x, chip_y), (chip_x + 200, chip_y + chip_height), (100, 100, 100), 2)
            cv2.putText(frame, "Face: None", (chip_x + 5, chip_y + 18), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    def cleanup(self):
        self.hands.close()
        self.face_detection.close()
        self.face_mesh.close()