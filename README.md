# MusicMultimediaProject
Music &amp; Multimedia Streaming Over the Internet Project


# Body Conductor

A live, distributed HMI performance system in which the human body becomes a musical and visual instrument. A performer stands in front of a camera and microphone, and their body posture and voice jointly sculpt a generative audiovisual landscape broadcast as a live stream to any browser. The machine has been trained to interpret gestures and sonic states as expressive intentions, mapping them to distinct aesthetic zones: calm, tense, chaotic, and harmonic. The audience watches the stream; the performer conducts the machine.

---

## Table of Contents

- [Concept](#concept)
- [System Architecture](#system-architecture)
- [Team and Division of Work](#team-and-division-of-work)
- [Components](#components)
  - [Machine 1 — Sensing](#machine-1--sensing)
  - [Machine 2 — Machine Learning](#machine-2--machine-learning)
  - [Machine 2 — Rendering](#machine-2--rendering)
  - [Streaming](#streaming)
- [OSC Message Design](#osc-message-design)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Setup and Running](#setup-and-running)

---

## Concept

This project is framed as a performative piece. The system has been trained — through supervised KNN classification and regression via Wekinator — to interpret the body as an expressive language. It sits at the intersection of Human-Machine Interaction and classical machine learning. No deep learning is involved; all models are trained interactively during rehearsal using the Wekinator workflow covered in the course lectures.

The project satisfies the group-of-4 complexity requirements:

- **Input variety** — both body landmarks (video) and audio features (microphone) are extracted, covering spatial/geometric, spectral, and temporal feature families.
- **Multiple trained models** — three Wekinator models run simultaneously: one classifier and two regressors.
- **Rich rendering** — Processing generates layered generative graphics (particle systems, waveforms, colour fields) plus synthesised audio (oscillators, filters), all driven by ML output.
- **Two physical machines over the network** — mandatory for groups of 2 or more.

---

## System Architecture

```
┌──────────────────────────────────┐         OSC over UDP (30 Hz)        ┌──────────────────────────────────────────┐
│           MACHINE 1              │ ──────────────────────────────────► │              MACHINE 2                   │
│                                  │   /features/body  (4 floats)        │                                          │
│  Python                          │   /features/audio (6 floats)        │  Wekinator                               │
│  ├── MediaPipe Pose              │                                      │  ├── Mood classifier   (4 classes)       │
│  │   └── 4 geometric features   │                                      │  ├── Visual regressor  (3 floats)        │
│  └── librosa + sounddevice       │                                      │  └── Audio regressor   (3 floats)        │
│      └── 6 audio features        │                                      │         │                                │
│                                  │                                      │         │ OSC localhost /wek/outputs     │
│                                  │                                      │         ▼                                │
│                                  │                                      │  Processing                              │
│                                  │                                      │  ├── Particle system                     │
│                                  │                                      │  ├── Colour field (mood)                 │
│                                  │                                      │  ├── Waveform ribbon                     │
│                                  │                                      │  └── Audio synthesis                     │
│                                  │                                      │         │                                │
│                                  │                                      │         │ OBS capture                    │
│                                  │                                      │         ▼                                │
│                                  │                                      │  mediamtx  (RTMP → HLS)                  │
│                                  │                                      │         │                                │
└──────────────────────────────────┘                                      └─────────┼────────────────────────────────┘
                                                                                    │
                                                                                    ▼
                                                                         Any browser on the network
                                                                         http://machine2-ip:8888/live
```

---

## Team and Division of Work

| Student | Branch | Responsibility |
|---|---|---|
| Gio | `feature/body-sensing` | MediaPipe Pose, geometric feature extraction, OSC sender |
| Rani | `feature/audio-sensing` | librosa + sounddevice, audio feature extraction, OSC sender |
| Stella | — | Wekinator model training, OSC routing, regression and classification setup |
| Sam | `feature/rendering-streaming` | Processing renderer, OBS + mediamtx streaming setup |

> Stella's Wekinator project file will be added to `machine2/wekinator_project/` once training is complete.

---

## Components

### Machine 1 — Sensing

Machine 1 runs two Python scripts in parallel, both sending OSC to Machine 2 at 30 Hz.

#### Body sensing (Gio)

Uses `mediapipe.solutions.pose` to track 33 body keypoints per frame from the webcam. From the raw keypoint positions, four derived geometric features are computed and normalised to [0, 1]:

| Feature | Description |
|---|---|
| Arm spread ratio | Euclidean distance between wrists divided by shoulder width |
| Body tilt angle | Angle of the vector from left hip to left shoulder |
| Head height | Normalised y-coordinate of the nose landmark |
| Right-arm elevation | Angle between right shoulder, right elbow, and horizontal |

**OSC address:** `/features/body` — 4 floats at 30 Hz

This directly extends the Lab 3 Exercise 2 workflow (MediaPipe hand landmarks → OSC → Wekinator), scaled from 21 hand points to full-body pose.

#### Audio sensing (Rani)

Uses `sounddevice` to read microphone frames in real time and `librosa` to compute six audio features per frame, normalised to [0, 1]:

| Feature | Description |
|---|---|
| RMS energy | Loudness / intensity of the sound |
| Spectral centroid | Brightness of the voice or sound |
| Zero crossing rate | Noisiness / breathiness of the signal |
| MFCC 1–4 | First four Mel-frequency cepstral coefficients (timbre) |

**OSC address:** `/features/audio` — 6 floats at 30 Hz

This extends the Lab 2 Exercise 1 feature extraction workflow, ported from Processing FFT to Python/librosa.

---

### Machine 2 — Machine Learning

Wekinator runs on Machine 2 and hosts three models trained simultaneously.

| Model | Type | Inputs | Outputs | Meaning |
|---|---|---|---|---|
| Mood classifier | KNN classification, k=3, 4 classes | All 10 features | 1 integer (0–3) | Calm / Tense / Chaotic / Harmonic |
| Visual intensity regressor | KNN regression, k=3 | 4 body features | 3 floats | Particle count, scale, speed |
| Audio synth regressor | KNN regression, k=3 | 6 audio features | 3 floats | Oscillator pitch, filter cutoff, reverb depth |

**Training procedure:** the performer adopts each of the four mood states deliberately while the group records a minimum of 20 examples per class. Training follows the exact workflow covered in the Wekinator lecture: record examples, train, run.

**OSC output:** `/wek/outputs` — 7 values (1 integer + 6 floats) sent to Processing over localhost.

---

### Machine 2 — Rendering

The Processing sketch listens on localhost for `/wek/outputs` and produces a generative audiovisual scene.

**Visual output:**

- Particle system: particle count, size, and velocity driven by the 3 visual regression outputs.
- Background colour field: shifts according to the mood classification output. Each of the 4 states has a distinct palette:
  - Calm → deep blue
  - Tense → amber
  - Chaotic → red / white
  - Harmonic → teal / green
- Waveform ribbon: a polyline drawn across the canvas whose amplitude follows the RMS regression value.

**Audio output (Processing Sound library):**

- Two `SinOsc` oscillators whose frequencies are offset by the first audio regression output.
- A `LowPassSP` filter whose cutoff is set by the second audio regression output.
- A `Reverb` effect whose room size is set by the third audio regression output.

---

### Streaming

OBS Studio runs on Machine 2 and captures the Processing window as a scene. It streams via RTMP to a local mediamtx instance. mediamtx serves the stream as HLS, accessible at:

```
http://<machine2-ip>:8888/live/stream
```

Any browser on the network can open this URL and watch the performance live. No external streaming services are used.

---

## OSC Message Design

OSC is the only channel for structural data exchange between the two machines. The message design reflects the conceptual flow: human input, extracted features, machine interpretation, rendered output.

| Address | Direction | Payload | Rate |
|---|---|---|---|
| `/features/body` | Machine 1 → Machine 2 | 4 floats: arm spread, tilt angle, head height, arm elevation | 30 Hz |
| `/features/audio` | Machine 1 → Machine 2 | 6 floats: RMS, spectral centroid, ZCR, MFCC 1–4 | 30 Hz |
| `/wek/outputs` | Wekinator → Processing | 7 values: 1 int (mood class) + 3 floats (visual) + 3 floats (audio synth) | 30 Hz |

The 30 Hz rate matches the webcam frame rate, keeping all three layers synchronised.

---

## Technology Stack

| Component | Technology | Machine |
|---|---|---|
| Body sensing | Python + MediaPipe | Machine 1 |
| Audio sensing | Python + librosa + sounddevice | Machine 1 |
| OSC sender | python-osc | Machine 1 |
| ML models | Wekinator | Machine 2 |
| OSC receiver/sender | Wekinator built-in | Machine 2 |
| Rendering | Processing + Sound library + oscP5 | Machine 2 |
| Stream capture | OBS Studio | Machine 2 |
| Stream server | mediamtx (RTMP/HLS) | Machine 2 |
| Client playback | Any web browser | Any machine |

---

## Repository Structure

```
body-conductor/
├── machine1/
│   ├── body_sensing/         # Gio — MediaPipe Pose + OSC sender
│   └── audio_sensing/        # Rani — librosa + sounddevice + OSC sender
├── machine2/
│   ├── processing_renderer/  # Sam — Processing sketch
│   └── wekinator_project/    # Stella — Wekinator project file
└── docs/
    └── README.md
```

---

## Setup and Running

### Machine 1

Install dependencies:

```bash
pip install mediapipe opencv-python librosa sounddevice python-osc
```

Run the body sensing script:

```bash
cd machine1/body_sensing
python body_sensing.py --ip <machine2-ip> --port 9000
```

Run the audio sensing script:

```bash
cd machine1/audio_sensing
python audio_sensing.py --ip <machine2-ip> --port 9001
```

### Machine 2

1. Open the Wekinator project from `machine2/wekinator_project/`.
2. Set Wekinator to listen on ports 9000 and 9001 and output to port 9002.
3. Open the Processing sketch from `machine2/processing_renderer/` and run it.
4. Open OBS Studio, set the stream output to `rtmp://localhost/live/stream`.
5. Start mediamtx: `./mediamtx`.
6. Start the OBS stream.
7. Open a browser on any machine on the network and navigate to `http://<machine2-ip>:8888/live/stream`.

---

*Music and Multimedia Streaming over the Internet — Politecnico di Torino, 2025/2026*
*Cristina Rottondi, Massimiliano Zanoni, Leonardo Severi*
