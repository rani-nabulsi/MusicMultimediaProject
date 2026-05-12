import argparse 
import math
import cv2
import mediapipe as mp
from pythonosc import udp_client

# Media pipe Pose module and drawing utility
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def clamp01(value):
    # parse any float to [0.0, 1.0] before sending over OSC
    return max(0.0, min(1.0, value))

def dist(a, b):
    # calculate distance between 2 marks in 2D (x & y)
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def norm_angle(angle_rad):
    # map the result of atan2 from [-pi, pi] to [0.0, 1.0] (OSC friendly range)
    return clamp01((angle_rad + math.pi) / (2.0 * math.pi))

def compute_features(landmarks):
    # extract all 4 geometric features/gestures from 33 MediaPipe
    # all values are normalised to [0.0, 1.0]
    nose = landmarks[0] 
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    right_elbow = landmarks[14]
    left_wrist = landmarks[15]
    right_wrist = landmarks[16]
    left_hip = landmarks[23]

    # feature 1 — arm spread ratio
    # wrist-to-wrist distance divided by shoulder width
    shoulder_width = dist(left_shoulder, right_shoulder)
    if shoulder_width > 0.0001:
        arm_spread = dist(left_wrist, right_wrist) / shoulder_width
    else:
        arm_spread = 0.0

    # feature 2 — body tilt angle
    # angle of the vector from left hip to left shoulder
    body_tilt = math.atan2(left_shoulder.y - left_hip.y,
                           left_shoulder.x - left_hip.x)
    
    # feature 3 — head height
    head_height = nose.y

    # feature 4 - right arm elevation
    right_arm_elev = math.atan2(right_elbow.y - right_shoulder.y,
                                right_elbow.x - right_shoulder.x)
    
    # returns all 4 features as a list
    return [clamp01(arm_spread),
            norm_angle(body_tilt),
            clamp01(head_height),
            norm_angle(right_arm_elev),]

def main():
    parser = argparse.ArgumentParser(description="Body Sensing: MediaPipe Pose + OSC sender")
    parser.add_argument("--ip", default="127.0.0.1", help="IP address of Machine 2")
    parser.add_argument("--port", type=int, default=9000, help="OSC port on Machine 2")
    args = parser.parse_args()

    # Create OSC client once (never inside the loop)
    client = udp_client.SimpleUDPClient(args.ip, args.port)
    print(f"[body_sensing] Sending OSC to {args.ip}:{args.port} -> /features/body")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[body_sensing] Error :( : Could not open webcam!!!")
        return 
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("[body_sensing] Ignoring empty camera frame.")
                continue

            # MediaPipe expects RGB input: openCV captures BGR (converts before processing)
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            # restore writeable and convert back to BGR for display
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                features = compute_features(results.pose_landmarks.landmark)
                client.send_message("/features/body", features)
                print(f"arm_spread={features[0]:.3f}  tilt={features[1]:.3f} "
                      f"head_height={features[2]:.3f}  arm_elev={features[3]:.3f}")
                
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # flip horizontally (acts like a mirror)
            cv2.imshow("Body Sensing", cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:
                break
                
cap.release()
cv2.destroyAllWindows()

if __name__ == "__main__":
    main()