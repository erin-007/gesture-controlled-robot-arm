import cv2
import mediapipe as mp
import numpy as np
import socket
import time

UBUNTU_IP  = "10.76.58.91"
UDP_PORT   = 5005
ALPHA      = 0.55
WRIST      = 0
MID_BASE   = 9
THUMB_TIP  = 4
INDEX_TIP  = 8
INDEX_MCP  = 5   # index finger base

def lm(hand, idx):
    p = hand.landmark[idx]
    return np.array([p.x, p.y, p.z])

def orientation_vector(hand):
    w = lm(hand, WRIST)
    m = lm(hand, MID_BASE)
    v = m - w
    norm = np.linalg.norm(v)
    return v / norm if norm > 1e-6 else v

def apply_deadzone(value, dz):
    if abs(value) < dz:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - dz) / (1.0 - dz)

def clamp(value, lo=-1.0, hi=1.0):
    return max(lo, min(hi, value))

def main():
    sock   = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target = (UBUNTU_IP, UDP_PORT)

    mp_hands = mp.solutions.hands
    mp_draw  = mp.solutions.drawing_utils
    hands    = mp_hands.Hands(max_num_hands=1,
                               min_detection_confidence=0.7,
                               min_tracking_confidence=0.6)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    neutral_vec    = None
    neutral_index_y = None   # calibrated index finger Y position
    smooth_x       = 0.0
    smooth_y       = 0.0
    grip           = 1.0
    calibrated     = False
    last_send      = 0.0

    print("Press SPACE to calibrate. Q to quit.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        move_x, move_y = 0.0, 0.0

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            cur_vec = orientation_vector(hand)

            # Index fingertip Y position (0=top, 1=bottom in image)
            index_tip_y = lm(hand, INDEX_TIP)[1]

            if calibrated and neutral_vec is not None:
                # ── LEFT/RIGHT from wrist orientation (your working control) ──
                delta  = cur_vec - neutral_vec
                raw_x  = delta[0] / 0.70
                move_x = clamp(apply_deadzone(raw_x, 0.12 / 0.70))
                smooth_x = ALPHA * smooth_x + (1 - ALPHA) * move_x
                move_x = smooth_x

                # ── UP/DOWN from index finger Y position ──
                # finger moves up in image → y decreases → robot goes up
                delta_y = neutral_index_y - index_tip_y   # positive = finger went up
                raw_y   = delta_y / 0.15                  # 0.15 = full range scale
                move_y  = clamp(apply_deadzone(raw_y, 0.1))
                smooth_y = ALPHA * smooth_y + (1 - ALPHA) * move_y
                move_y = smooth_y

            # ── GRIPPER: thumb-index pinch ──
            t    = lm(hand, THUMB_TIP)
            i    = lm(hand, INDEX_TIP)
            dist = np.linalg.norm(t - i)
            if dist > 0.08:
                grip = 1.0
            elif dist < 0.05:
                grip = 0.0

        now = time.time()
        if now - last_send >= 1.0 / 30:
            payload = f"{move_x:.4f},{move_y:.4f},{grip:.1f}"
            sock.sendto(payload.encode(), target)
            last_send = now

        status = "CALIBRATED" if calibrated else "Press SPACE to calibrate"
        color  = (0, 200, 100) if calibrated else (60, 60, 200)
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        if calibrated:
            cv2.putText(frame, f"X:{move_x:+.2f} Y:{move_y:+.2f} grip:{'OPEN' if grip>0.5 else 'CLOSED'}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
            cv2.putText(frame, "Wrist tilt = left/right | Index finger = up/down",
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        cv2.imshow("Gesture Controller", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' ') and result.multi_hand_landmarks:
            hand        = result.multi_hand_landmarks[0]
            neutral_vec = orientation_vector(hand)
            neutral_index_y = lm(hand, INDEX_TIP)[1]
            calibrated  = True
            smooth_x, smooth_y = 0.0, 0.0
            print(f"Calibrated! neutral_index_y={neutral_index_y:.3f}")

    cap.release()
    cv2.destroyAllWindows()
    sock.close()

if __name__ == "__main__":
    main()