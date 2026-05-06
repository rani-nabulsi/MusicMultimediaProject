# Gio — Audio Sensing Manual
## Machine 1 | Python + librosa + sounddevice + OSC

---

## What You Are Building

You are responsible for the audio sensing component of Machine 1. Your Python script opens the microphone, reads audio frames in real time, computes 6 audio features per frame using librosa, normalises them to [0, 1], and sends them as an OSC message to Machine 2 at approximately 30 Hz.

Your script feeds the third Wekinator model (the audio synth regressor) and contributes to the mood classifier. Without your script, the audio dimension of the performance is completely absent. Your piece runs in parallel with Rani's body sensing script. The two scripts are independent of each other and never talk to each other directly.

---

## Lecture and Lab References

Before writing any code, read the following:

- **Lab 2, Exercise 1** — your primary conceptual reference. It implements real-time audio capture, FFT analysis, and feature extraction in Processing, then sends results to Wekinator via OSC. You are doing the same thing in Python. The features and the intent are identical; only the tools are different.
- **Lecture 2.3 (Perception)** — covers all six features you are computing. The lecture slide titled "LLF" (Low-Level Features) lists RMS, spectral centroid, zero crossing rate, and MFCCs explicitly as compact representations of the spectrum and waveform. This is the theoretical basis for what your script does.
- **Lecture 4 (Cognitive Agents and ML)** — explains OSC message structure: address, type tag, arguments. Your script is an OSC sender. Wekinator is the receiver. The lecture explains how Wekinator expects input as OSC.

---

## The 6 Features You Must Extract

All features come from a short window of audio (one frame) read from the microphone. You use `sounddevice` to capture the microphone in a callback loop and `librosa` to compute the features from each frame.

| Feature | librosa function | What it represents (Lecture 2.3) |
|---|---|---|
| RMS energy | `librosa.feature.rms(y=frame)` | Overall loudness of the sound |
| Spectral centroid | `librosa.feature.spectral_centroid(y=frame, sr=sr)` | Brightness — where the energy sits in the spectrum |
| Zero crossing rate | `librosa.feature.zero_crossing_rate(frame)` | Noisiness / breathiness of the signal |
| MFCC 1 | `librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=4)[0]` | Timbre coefficient 1 |
| MFCC 2 | `librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=4)[1]` | Timbre coefficient 2 |
| MFCC 3 | `librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=4)[2]` | Timbre coefficient 3 |

You send these 6 values in this exact order. All must be normalised to [0, 1] before sending.

---

## Normalisation

librosa returns raw values, not normalised ones. You need to clip and normalise based on expected ranges. Use a min/max normalisation:

```python
def normalise(value, min_val, max_val):
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
```

Approximate ranges to use (tune these during testing if values are clipping too much):

| Feature | Approximate min | Approximate max |
|---|---|---|
| RMS | 0.0 | 0.3 |
| Spectral centroid | 200 | 8000 |
| ZCR | 0.0 | 0.5 |
| MFCC 1 | -600 | 200 |
| MFCC 2 | -100 | 100 |
| MFCC 3 | -80 | 80 |

Print the raw values for 30 seconds while making sound to verify these ranges fit your microphone and environment.

---

## Port and Address Agreement

Agree on these with Rani and Sam before writing any code:

- **Target IP:** Machine 2's IP address (get this from Sam)
- **Your OSC port:** `9001`
- **Your OSC address:** `/features/audio`
- **Payload:** 6 floats in this exact order: `[rms, centroid, zcr, mfcc1, mfcc2, mfcc3]`

Rani sends to port `9000`. You send to port `9001`. Never the same port.

---

## How the Code Is Structured

```python
import sounddevice as sd
import numpy as np
import librosa
from pythonosc import udp_client
import argparse

SAMPLE_RATE = 22050
FRAME_SIZE  = 2048   # number of audio samples per frame

def compute_features(frame, sr):
    frame = frame.flatten().astype(np.float32)

    rms      = librosa.feature.rms(y=frame)[0][0]
    centroid = librosa.feature.spectral_centroid(y=frame, sr=sr)[0][0]
    zcr      = librosa.feature.zero_crossing_rate(frame)[0][0]
    mfccs    = librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=4)

    # normalise each value to [0, 1]
    rms_n      = normalise(rms, 0.0, 0.3)
    centroid_n = normalise(centroid, 200, 8000)
    zcr_n      = normalise(zcr, 0.0, 0.5)
    mfcc1_n    = normalise(float(mfccs[0].mean()), -600, 200)
    mfcc2_n    = normalise(float(mfccs[1].mean()), -100, 100)
    mfcc3_n    = normalise(float(mfccs[2].mean()), -80, 80)

    return [rms_n, centroid_n, zcr_n, mfcc1_n, mfcc2_n, mfcc3_n]

def normalise(value, min_val, max_val):
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9001)
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    def callback(indata, frames, time, status):
        features = compute_features(indata, SAMPLE_RATE)
        client.send_message("/features/audio", features)
        print(features)  # keep this during testing

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        blocksize=FRAME_SIZE, callback=callback):
        print("Audio sensing running. Press Ctrl+C to stop.")
        while True:
            sd.sleep(1000)
```

---

## How to Test Without Machine 2

Same approach as Rani: use `OSC_receiver_test.pde` on localhost with port 9001. Confirm all 6 values are in [0, 1]. Then physically test:

- Silence: RMS should be near 0
- Loud clap or voice: RMS should spike toward 1
- High-pitched sound: spectral centroid should be high
- Low hum: spectral centroid should be low
- Noisy breath sound: ZCR should be high

If any feature is stuck at 0 or 1 all the time, your normalisation range is wrong. Adjust the min/max values.

---

## TODO List

- [ ] Install dependencies: `pip install librosa sounddevice python-osc numpy`
- [ ] Read Lab 2 Exercise 1 fully to understand the feature concepts before writing code
- [ ] Confirm the target IP and port with Sam (Machine 2's IP, your port is 9001)
- [ ] Create `machine1/audio_sensing/audio_sensing.py` on your branch `feature/audio-sensing`
- [ ] Implement the `compute_features()` function with all 6 features
- [ ] Run the script with `--ip 127.0.0.1 --port 9001` and verify microphone opens without errors
- [ ] Print raw (un-normalised) values for 30 seconds to understand your actual ranges
- [ ] Adjust normalisation min/max values based on real measurements
- [ ] Run the script again and confirm all 6 values stay in [0, 1] across silence, voice, clap, hum
- [ ] Test using `OSC_receiver_test.pde` to confirm OSC messages arrive correctly on port 9001
- [ ] Run simultaneously with Rani's script — confirm both scripts run at the same time with no errors
- [ ] Confirm Wekinator on Machine 2 receives your messages on port 9001 — Stella verifies this with you
- [ ] Push finished and tested code to your branch and open a pull request to main

---

## Hand-Off Condition

You are done when Stella can open Wekinator on Machine 2, see 6 inputs arriving live on port 9001 with address `/features/audio`, and the values visibly react when you clap, speak, or stay silent. That is the acceptance test. Do not mark yourself done until this is confirmed with Stella present.
