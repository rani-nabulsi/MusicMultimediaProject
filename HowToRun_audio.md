# Audio Sensing — How to Run

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
cd machine_1/audio_sensing
```

**Step 4 — Run (local test, no Machine 2 needed):**
```bash
python3 audio_sensing.py --ip 127.0.0.1 --port 9001
```

**Step 4 — Run (real deployment, sending to Machine 2):**
```bash
python3 audio_sensing.py --ip <machine2-ip> --port 9001
```

Press **Ctrl+C** in the terminal to stop.

---

## Calibration (do this before your first real session with Stella)

Run this once in your room, with your actual microphone, and make all kinds of sounds
for 30 seconds (silence, speech, clap, shout, hum):

```bash
python3 audio_sensing.py --calibrate
```

The script will print the real min/max values it observed for each feature.
Compare them to the `NORM_RANGES` dictionary at the top of `audio_sensing.py` and
adjust if any feature is constantly clipping to 0 or 1.

---

## How to verify it is working

You will see a table printed in the terminal every frame, like this:

```
   rms  centroid     zcr   mfcc1   mfcc2   mfcc3
------------------------------------------------------
 0.032     0.461   0.210   0.587   0.431   0.502
 0.041     0.489   0.198   0.601   0.420   0.511
```

Check:
- **Silence** → `rms` should be close to 0
- **Loud clap or shout** → `rms` should spike toward 1
- **High-pitched sound** → `centroid` should be high
- **Low hum** → `centroid` should be low
- **Breathy or noisy sound** → `zcr` should be high
- **All 6 values must stay in [0, 1]** at all times — if any is stuck at exactly 0 or 1 constantly, run `--calibrate` and adjust the ranges

---

## Running alongside Rani

Both scripts run at the same time with no conflict because they use **different ports**:

| Script | Port | Address |
|---|---|---|
| `body_sensing.py` (Rani) | 9000 | `/features/body` |
| `audio_sensing.py` (Gio) | 9001 | `/features/audio` |

Open two terminals, activate the venv in each, and run both scripts simultaneously.
Sam's `osc_forwarder.pde` will show a green status line once it receives from both.

---

## One-time setup (already done, do not repeat)

```bash
# Install all dependencies inside the venv
pip3 install librosa sounddevice python-osc numpy
```

No model file needed — unlike Rani's script, audio_sensing.py uses only the microphone.

---

## If something breaks

**`No module named 'librosa'` or `No module named 'sounddevice'`:**
You forgot to activate the venv. Go back to Step 2.

**`No such file or directory: audio_sensing.py`:**
You are in the wrong folder. Run `pwd` to check, then `cd` to `machine_1/audio_sensing`.

**`PortAudio / sounddevice error on open`:**
Another app is using the microphone (Zoom, FaceTime, browser tab). Close it and retry.

**All values stuck at 0:**
The microphone is not picking up sound or the normalisation floor is too high.
Run `--calibrate` and check the raw values.

**All values stuck at 1:**
The normalisation ceiling is too low for your environment.
Run `--calibrate` and raise the `max_val` for the clipping feature in `NORM_RANGES`.

**Sam's forwarder still shows red for AUDIO after you started:**
Check that you are sending to the right IP and port 9001.
If testing locally, use `--ip 127.0.0.1`. For Machine 2, use `--ip <machine2-ip>`.

**Stella says Wekinator does not see 10 inputs:**
Make sure Sam's `osc_forwarder.pde` is running first, then Rani's script, then yours.
The forwarder must be open before Wekinator is configured.
