# Body Sensing — How to Run

## Every time you open a new terminal

**Step 1 — Navigate to the project root:**
```bash
cd ..../path/to/project
```

**Step 2 — Activate the virtual environment:**
```bash
source .venv/bin/activate
```
Your prompt must show `(.venv)` before continuing. If it does not, something is wrong.

**Step 3 — Navigate to the script:**
```bash
cd machine_1/body_sensing
```

**Step 4 — Run (local test, no Machine 2 needed):**
```bash
python3 body_sensing.py --ip 127.0.0.1 --port 9000
```

**Step 4 — Run (real deployment, sending to Machine 2):**
```bash
python3 body_sensing.py --ip <machine2-ip> --port 9000
```

Press **ESC** in the webcam window to exit.

---

## One-time setup (already done, do not repeat)

These commands were run once to set everything up. You do not need to run them again.

```bash
# Download the MediaPipe pose model (already in machine_1/body_sensing/)
curl -o pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task

# Install all dependencies inside the venv
pip3 install mediapipe opencv-python python-osc
```

---

## If something breaks

**`No module named 'cv2'` or `No module named 'mediapipe'`:**
You forgot to activate the venv. Go back to Step 2.

**`No such file or directory: body_sensing.py`:**
You are in the wrong folder. Run `pwd` to check where you are, then `cd` to the right place.

**`Could not open webcam`:**
Another app is using the camera. Close FaceTime, Zoom, or any browser tab with camera access, then try again.

**`FileNotFoundError: pose_landmarker.task`:**
The model file is missing from the current folder. Make sure `pose_landmarker.task` is inside `machine_1/body_sensing/`.