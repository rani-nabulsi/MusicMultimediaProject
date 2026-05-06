# Rani — Body Sensing Manual
## Machine 1 | Python + MediaPipe Pose + OSC

---

## What You Are Building

You are responsible for the body sensing component of Machine 1. Your Python script opens the webcam, detects the performer's full-body skeleton using MediaPipe Pose, computes 4 geometric features from the skeleton positions, normalises them to the range [0, 1], and sends them continuously as an OSC message to Machine 2 at 30 Hz.

This is the input that feeds two of the three Wekinator models. Without your script running, Stella cannot train and Sam's renderer has no data. Your piece is the first domino.

The starting point for your work is the professor-provided file `WobbleBass_MediaPipe.py`. That script already does MediaPipe hand tracking and OSC sending. Your job is to adapt it to track the full body instead of the hand, and to compute meaningful geometric features rather than a raw average of all landmarks.

---

## Lecture and Lab References

Before writing any code, read the following:

- **Lab 3, Exercise 2** — this is your primary reference. It describes exactly the workflow you are implementing: Python + MediaPipe + OSC to Wekinator. The professor's `WobbleBass_MediaPipe.py` file is the template you adapt.
- **Lecture 4 (Cognitive Agents and ML)** — explains what OSC is, how messages are structured (address + type tag + arguments), and how Wekinator expects to receive input. Your script is the OSC sender; Wekinator is the OSC receiver.
- **Lecture 2.3 (Perception)** — explains why we extract geometric features from landmarks instead of sending all raw coordinates. The lecture shows a hand with 21 joints, noting that 63 raw numbers need to be reduced to a small set of meaningful descriptors before being useful as ML input. The same principle applies here with 33 body landmarks.

---

## The 4 Features You Must Extract

MediaPipe Pose gives you 33 landmarks. Each landmark has an `x`, `y`, and `z` coordinate normalised to [0, 1] relative to the image frame. You do not send all 33 as raw numbers. You compute these 4 derived geometric values:

| Feature | Landmark indices used | Formula |
|---|---|---|
| Arm spread ratio | LEFT_WRIST (15), RIGHT_WRIST (16), LEFT_SHOULDER (11), RIGHT_SHOULDER (12) | distance(wrist_L, wrist_R) / distance(shoulder_L, shoulder_R) |
| Body tilt angle | LEFT_HIP (23), LEFT_SHOULDER (11) | atan2(shoulder.y - hip.y, shoulder.x - hip.x) in radians, then normalised |
| Head height | NOSE (0) | nose.y directly (already in [0,1], 0 = top of frame) |
| Right-arm elevation | RIGHT_SHOULDER (12), RIGHT_ELBOW (14) | atan2(elbow.y - shoulder.y, elbow.x - shoulder.x) normalised |

All four values must be clipped and normalised to [0, 1] before sending. Use Python's `max(0, min(1, value))` for any value that could exceed the range.

---

## Port and Address Agreement

You and Gio must agree on these values before either of you writes a line of code. Do not change them later without telling everyone:

- **Target IP:** Machine 2's IP address on the local network (ask Sam what it is)
- **Your OSC port:** `9000`
- **Your OSC address:** `/features/body`
- **Payload:** 4 floats in this exact order: `[arm_spread, tilt_angle, head_height, arm_elevation]`

Gio sends to port `9001` with address `/features/audio`. Your ports must not be the same.

---

## How the Code Is Structured

Base your file on `WobbleBass_MediaPipe.py`. The structure is:

```python
import cv2
import mediapipe as mp
import math
from pythonosc import udp_client
import argparse

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def compute_features(landmarks):
    # Extract specific landmarks by index
    # Compute the 4 geometric values
    # Normalise each to [0, 1]
    # Return as a list of 4 floats
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    cap = cv2.VideoCapture(0)
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                continue

            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                features = compute_features(results.pose_landmarks.landmark)
                client.send_message("/features/body", features)
                print(features)  # keep this during testing

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.imshow('Body Sensing', cv2.flip(image, 1))
            if cv2.waitKey(5) & 0xFF == 27:
                break

    cap.release()
```

The key difference from the professor's hand script: `mp.solutions.hands` becomes `mp.solutions.pose`, `hands.process()` becomes `pose.process()`, and `results.multi_hand_landmarks` becomes `results.pose_landmarks`.

---

## How to Access Specific Landmarks

In MediaPipe Pose, you access landmarks by index:

```python
lm = results.pose_landmarks.landmark

nose        = lm[0]
left_shoulder  = lm[11]
right_shoulder = lm[12]
left_hip    = lm[23]
right_wrist = lm[15]
right_wrist = lm[16]
right_elbow = lm[14]
```

Each has `.x`, `.y`, `.z` attributes. For 2D geometry, you only need `.x` and `.y`.

Distance between two points:
```python
def dist(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)
```

Angle between two points (for tilt and arm elevation):
```python
def angle(a, b):
    return math.atan2(b.y - a.y, b.x - a.x)  # returns radians in [-pi, pi]
    # normalise to [0,1]: (angle + math.pi) / (2 * math.pi)
```

---

## How to Test Without Machine 2

You do not need Wekinator running to test your script. Use the `OSC_receiver_test.pde` Processing sketch provided by the professor. Run it on any machine (or on Machine 1 itself on localhost), set the port to 9000, and you will see your feature values printed in the Processing console every frame. Confirm all 4 values are in [0, 1] and that they respond to your body movement as expected.

Specifically test:
- Arms fully spread wide: arm spread ratio should be close to 1
- Arms down by your sides: arm spread ratio should be close to 0
- Stand straight: tilt angle should be around 0.5
- Lean to one side: tilt angle should shift away from 0.5

---

## TODO List

- [ ] Install dependencies: `pip install mediapipe opencv-python python-osc`
- [ ] Read `WobbleBass_MediaPipe.py` fully and understand its structure before modifying anything
- [ ] Confirm the target IP and port with Sam (Machine 2's IP, your port is 9000)
- [ ] Create `machine1/body_sensing/body_sensing.py` on your branch `feature/body-sensing`
- [ ] Implement the `compute_features()` function with all 4 geometric calculations
- [ ] Add normalisation to [0, 1] for every feature value
- [ ] Run the script and verify the webcam opens and MediaPipe draws the skeleton overlay
- [ ] Test feature values using `OSC_receiver_test.pde` or a print statement — confirm all 4 stay in [0, 1]
- [ ] Test all 4 feature responses physically: spread arms, tilt body, raise arm, vary head position
- [ ] Run simultaneously with Gio's script and confirm both can send OSC at the same time without conflict (different ports)
- [ ] Confirm Wekinator on Machine 2 receives your messages on port 9000 — Stella must verify this with you
- [ ] Push finished and tested code to your branch and open a pull request to main

---

## Hand-Off Condition

You are done when Stella can open Wekinator on Machine 2, see 4 inputs arriving live on port 9000 with address `/features/body`, and the values visibly change as the performer moves. That is the acceptance test. Do not mark yourself done until this is confirmed with Stella present.
