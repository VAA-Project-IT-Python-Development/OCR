import cv2
import mediapipe as mp
import time
import requests

# Mediapipe Initialization
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Global variable to store the detected sign sequence
detected_sequence = ""

# Function to check if only the index finger is extended (for deletion)
def is_one_finger_up(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    # Check if index finger is extended and other fingers are curled
    if (index_tip.y < landmarks[6].y and  # Index finger is extended
        thumb_tip.y > landmarks[3].y and  # Thumb is curled
        middle_tip.y > landmarks[10].y and  # Middle finger is curled
        ring_tip.y > landmarks[14].y and  # Ring finger is curled
        pinky_tip.y > landmarks[18].y):  # Pinky finger is curled
        return True
    return False


def recognize_letter(landmarks, width, height):
    """
    Nhận diện các chữ cái và số dựa trên vị trí các điểm landmark của bàn tay
    
    Nguyên tắc chung:
    - Sử dụng vị trí tương đối của các điểm khớp ngón tay
    - So sánh độ cao (y) và vị trí ngang (x) của các điểm
    
    Parameters:
    - landmarks: Danh sách các điểm landmark của bàn tay
    - width, height: Chiều rộng và cao của khung hình (chưa sử dụng)
    
    Returns:
    - Ký tự nhận dạng được hoặc None nếu không nhận dạng được
    """
    lm = landmarks  # Viết gọn để dễ đọc
    
    # Các hàm hỗ trợ kiểm tra trạng thái ngón tay
    def is_finger_bent(base, tip):
        """Kiểm tra xem ngón tay có bị gập không"""
        return tip.y > base.y
    
    def is_finger_straight(base, tip):
        """Kiểm tra xem ngón tay có duỗi thẳng không"""
        return tip.y < base.y

    # Nhận dạng chữ cái
    
    # A: Tất cả các ngón đều gập, ngón cái gần ngón trỏ
    if (all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 5)) and 
        abs(lm[4].y - lm[6].y) < 0.1):
        return "A"
    
    # B: Tất cả các ngón đều gập, ngón cái ở bên phải ngón trỏ
    elif (all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 5)) and 
          lm[2].x > lm[4].x and lm[2].x > lm[8].x):
        return "B"
    
    # C: Bàn tay tạo hình cong như chữ C
    elif (all(lm[i*4+2].x > lm[i*4].x for i in range(1, 5))):
        return "C"
    
    # D: Ngón trỏ duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(2, 5)) and 
          lm[4].y > lm[8].y):
        return "D"
    
    # E: Tất cả các ngón gập, các ngón nằm trong một khoảng không gian
    elif (all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 5)) and 
          lm[17].x < lm[0].x < lm[5].x and 
          lm[4].y > lm[6].y):
        return "E"
    
    # F: Ngón trỏ và ngón giữa duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          is_finger_bent(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "F"
    
    # H: Ngón trỏ và ngón giữa duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          is_finger_bent(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "H"
    
    # I: Chỉ ngón út duỗi
    elif (all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 4)) and 
          is_finger_straight(lm[18], lm[20])):
        return "I"
    
    # K: Ngón trỏ và ngón giữa tạo hình chữ V
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          abs(lm[8].x - lm[12].x) > 0.1 and 
          is_finger_bent(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "K"
    
    # L: Ngón trỏ và ngón cái duỗi thẳng, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[3], lm[4]) and 
          is_finger_bent(lm[10], lm[12]) and 
          is_finger_bent(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "L"
    
    # O: Các ngón tay tạo hình tròn
    elif (abs(lm[4].x - lm[8].x) < 0.1 and 
          all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 5))):
        return "O"
    
    # U: Ngón trỏ và ngón giữa duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          is_finger_bent(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "U"
    
    # W: Ba ngón trên duỗi
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          is_finger_straight(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "W"
    
    # Y: Ngón cái và ngón út duỗi, các ngón khác gập
    elif (is_finger_straight(lm[3], lm[4]) and 
          is_finger_straight(lm[18], lm[20]) and 
          all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 3)) and 
          is_finger_bent(lm[14], lm[16])):
        return "Y"
    
    # Nhận dạng số
    
    # 1: Ngón trỏ duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(2, 5))):
        return "1"
    
    # 2: Ngón trỏ và ngón giữa duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(3, 5))):
        return "2"
    
    # 3: Ba ngón trên duỗi, các ngón khác gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          is_finger_straight(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "3"
    
    # 4: Ba ngón trên duỗi, ngón út gập
    elif (is_finger_straight(lm[6], lm[8]) and 
          is_finger_straight(lm[10], lm[12]) and 
          is_finger_straight(lm[14], lm[16]) and 
          is_finger_bent(lm[18], lm[20])):
        return "4"
    
    # 5: Tất cả các ngón đều gập
    elif (all(is_finger_bent(lm[i*4+1], lm[i*4+3]) for i in range(1, 5))):
        return "5"
   
    
    return None

# Function to detect the sign language sequence
def detect_sign_language_sequence():
    global detected_sequence
    camera = cv2.VideoCapture(0)
    last_update_time = time.time()
    h, w = 0, 0

    while True:
        ret, frame = camera.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)

        output_text = "No matching gesture"
        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0, 255, 255), thickness=4, circle_radius=5),
                    mp_draw.DrawingSpec(color=(0, 128, 255), thickness=2)
                )

                # Check for letter recognition
                detected_letter = recognize_letter(hand_landmarks.landmark, w, h)
                if detected_letter:
                    output_text = f"Letter '{detected_letter}' detected"
                    if time.time() - last_update_time >= 2:
                        detected_sequence += detected_letter + " "
                        last_update_time = time.time()
                        requests.post("http://127.0.0.1:5000/save_detected_text", json={"text": detected_sequence})

                # Check if one finger (index) is up to clear the last character
                if is_one_finger_up(hand_landmarks.landmark):
                    output_text = "Clear last character"
                    if detected_sequence:
                        detected_sequence = detected_sequence[:-1]  # Remove the last character
                        requests.post("http://127.0.0.1:5000/save_detected_text", json={"text": detected_sequence})

        # Display the detected sign sequence on the screen
        cv2.putText(frame, output_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
        cv2.putText(frame, "Detected Sequence: " + detected_sequence, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')