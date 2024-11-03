import cv2
import mediapipe as mp
import random
import numpy as np
import time
import os
import pygame

pygame.mixer.init()
jumpscare_sound = "jumpscare.mp3"

if not os.path.exists(jumpscare_sound):
    raise Exception(f"Sound file not found: {jumpscare_sound}")

pygame.mixer.music.load(jumpscare_sound)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera")
    exit(1)

cv2.namedWindow("Hand Tracking", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Hand Tracking", cv2.WINDOW_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

def load_image_with_alpha(path):
    if not os.path.exists(path):
        raise Exception(f"Image file not found: {path}")
    
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise Exception(f"Could not load image: {path}")
    
    if len(img.shape) == 3 and img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img

try:
    ball_images = [
        load_image_with_alpha("blue purple virus.png"),
        load_image_with_alpha("red virusbg.png"),
        load_image_with_alpha("green virusbg.png")
    ]
    bullet_image = load_image_with_alpha("aqua.jpeg")
    hit_ball_image = load_image_with_alpha("web.png")
    win_image = load_image_with_alpha("ambafait.jpg")
    
    ball_images = [cv2.resize(img, (40, 40)) for img in ball_images]
    bullet_image = cv2.resize(bullet_image, (20, 20))
    hit_ball_image = cv2.resize(hit_ball_image, (40, 40))
    win_image = cv2.resize(win_image, (640, 480))
except Exception as e:
    print(f"Error loading images: {e}")
    cap.release()
    exit(1)

def overlay_image(background, overlay, x, y):
    try:
        h, w = overlay.shape[:2]
        y1, y2 = max(0, y), min(background.shape[0], y + h)
        x1, x2 = max(0, x), min(background.shape[1], x + w)

        if y1 >= y2 or x1 >= x2:
            return

        overlay_crop = overlay[max(0, -y):min(h, background.shape[0] - y), 
                               max(0, -x):min(w, background.shape[1] - x)]
        background_crop = background[y1:y2, x1:x2]

        if overlay_crop.shape[2] == 4:
            alpha_s = overlay_crop[:, :, 3] / 255.0
            alpha_l = 1.0 - alpha_s

            for c in range(0, 3):
                background_crop[:, :, c] = (alpha_s * overlay_crop[:, :, c] + 
                                            alpha_l * background_crop[:, :, c])
    except Exception as e:
        print(f"Error in overlay_image: {e}")

num_balls = 5
balls = []
ball_speed_min, ball_speed_max = 7, 10

for _ in range(num_balls):
    ball_x = random.randint(50, 600)
    ball_y = random.randint(-500, -50)
    ball_speed = random.randint(ball_speed_min, ball_speed_max)
    ball_image = random.choice(ball_images)
    balls.append([ball_x, ball_y, ball_speed, ball_image])

score = 0
bullet_fired = {0: False, 1: False} 
bullet_positions = {0: [0, 0], 1: [0, 0]}  
bullet_directions = {0: [0, 0], 1: [0, 0]}  
bullet_speed = 20
last_bullet_time = {0: time.time(), 1: time.time()}
bullet_delay = 0.2

start_time = time.time()
game_duration = 60

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break

        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        for ball in balls:
            ball[1] += ball[2]
            if ball[1] > frame.shape[0]:
                ball[0] = random.randint(50, frame.shape[1] - 50)
                ball[1] = random.randint(-500, -50)
                ball[3] = random.choice(ball_images)
            overlay_image(frame, ball[3], ball[0], ball[1])

        if result.multi_hand_landmarks:
            for hand_idx, hand_lms in enumerate(result.multi_hand_landmarks[:2]):
                mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

                wrist = hand_lms.landmark[0]
                index_finger_tip = hand_lms.landmark[8]
                h, w, c = frame.shape
                wrist_x, wrist_y = int(wrist.x * w), int(wrist.y * h)
                index_x, index_y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)

                hand_orientation = "Front" if wrist_y < index_y else "Back"
                cv2.putText(frame, f'Hand Orientation: {hand_orientation}', 
                            (w - 300, 50 + hand_idx * 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                if not bullet_fired[hand_idx] and time.time() - last_bullet_time[hand_idx] >= bullet_delay:
                    bullet_fired[hand_idx] = True
                    bullet_positions[hand_idx] = [index_x, index_y]
                    bullet_dir_x = index_x - wrist_x
                    bullet_dir_y = index_y - wrist_y
                    
                    magnitude = np.sqrt(bullet_dir_x**2 + bullet_dir_y**2)
                    if magnitude > 0:
                        bullet_directions[hand_idx] = [bullet_dir_x / magnitude, bullet_dir_y / magnitude]
                    
                    last_bullet_time[hand_idx] = time.time()

        for hand_idx in [0, 1]:
            if bullet_fired[hand_idx]:
                bullet_positions[hand_idx][0] += int(bullet_speed * bullet_directions[hand_idx][0])
                bullet_positions[hand_idx][1] += int(bullet_speed * bullet_directions[hand_idx][1])
                
                overlay_image(frame, bullet_image, 
                              bullet_positions[hand_idx][0] - bullet_image.shape[1] // 2,
                              bullet_positions[hand_idx][1] - bullet_image.shape[0] // 2)

                if (bullet_positions[hand_idx][0] < 0 or bullet_positions[hand_idx][0] > frame.shape[1] or 
                    bullet_positions[hand_idx][1] < 0 or bullet_positions[hand_idx][1] > frame.shape[0]):
                    bullet_fired[hand_idx] = False

                for ball in balls:
                    if ((ball[0] - 20 < bullet_positions[hand_idx][0] < ball[0] + 20) and 
                        (ball[1] - 20 < bullet_positions[hand_idx][1] < ball[1] + 20)):
                        score += 1
                        ball[0] = random.randint(50, frame.shape[1] - 50)
                        ball[1] = random.randint(-500, -50)
                        
                        overlay_image(frame, hit_ball_image, ball[0], ball[1])
                        bullet_fired[hand_idx] = False

        elapsed_time = time.time() - start_time
        remaining_time = max(0, game_duration - elapsed_time)
        cv2.putText(frame, f'Score: {score}', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Time: {int(remaining_time)}s', (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if remaining_time <= 0:
            if score <= 40:
                cv2.putText(frame, "YOU LOSE", (frame.shape[1] // 2 - 100, frame.shape[0] // 2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                overlay_image(frame, win_image, 0, 0)
                pygame.mixer.music.play()
            else:
                cv2.putText(frame, "YOU WIN", (frame.shape[1] // 2 - 100, frame.shape[0] // 2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                
            
            
            cv2.imshow("Hand Tracking", frame)
            cv2.waitKey(2000)
            break

        cv2.imshow("Hand Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
except Exception as e:
    print(f"Error in main loop: {e}")
finally:
    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.quit()
