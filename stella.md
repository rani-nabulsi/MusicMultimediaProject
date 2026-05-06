# Stella — Wekinator Manual
## Machine 2 | Wekinator | 3 Models | No Coding Required

---

## What You Are Building

You are responsible for the machine learning layer of the entire system. You configure and train three models inside Wekinator. These models sit between the raw feature data coming from Machine 1 and the visual/audio output rendered by Sam's Processing sketch. The quality of the whole performance depends on how well you train these models.

You write zero lines of code. Everything you do is inside the Wekinator graphical interface. However, you need to understand what you are doing conceptually, because the professor will ask you about it.

You cannot start training until both Gio and Rani have their scripts running and confirmed to be sending data. Schedule a session with both of them before you begin.

---

## Lecture and Lab References

Before touching Wekinator, read:

- **Lecture 4 (Cognitive Agents and ML)** — this is your primary reference. It covers Wekinator from start to finish: what it is, how to configure inputs and outputs, how to record examples, how KNN classification and KNN regression work, and the difference between the two. The lecture slide titled "Train and Use a Machine" shows every field you need to fill in. Study it.
- **Lab 2, Exercise 1** — this lab uses Wekinator with KNN classification (k=3) for sound classification. The training procedure you follow is identical to what you did in this lab.
- **Lab 3, Exercise 1** — this lab uses Wekinator with KNN regression (k=3) mapping mouse gesture features to visual outputs. Your two regression models follow exactly this workflow.
- **Lab 3, Exercise 2** — uses Wekinator regression with MediaPipe hand landmarks as input. This is the closest existing example to what Rani is sending you.

---

## The Three Models

You run all three models inside a single Wekinator project simultaneously. Here is the exact configuration for each:

### Model 1 — Mood Classifier

| Setting | Value |
|---|---|
| Type | Classification |
| Algorithm | KNN, k=3 |
| Number of inputs | 10 (4 from Rani + 6 from Gio) |
| Number of outputs | 1 |
| Output type | Integer (class label) |
| Classes | 4 (calm=1, tense=2, chaotic=3, harmonic=4) |
| Input OSC port | Wekinator receives on one port; both Gio and Rani send to the same Wekinator port |
| Output sent to | Processing, port 12000, address `/wek/outputs` |

This model answers: "which of the 4 moods is the performer in right now?"

### Model 2 — Visual Intensity Regressor

| Setting | Value |
|---|---|
| Type | Regression |
| Algorithm | KNN, k=3 |
| Number of inputs | 4 (body features from Rani only) |
| Number of outputs | 3 |
| Output meaning | Output 1 = particle count, Output 2 = particle scale, Output 3 = particle speed |
| Output range | [0, 1] for all three |

This model answers: "given this body pose, how intense should the visuals be?"

### Model 3 — Audio Synth Regressor

| Setting | Value |
|---|---|
| Type | Regression |
| Algorithm | KNN, k=3 |
| Number of inputs | 6 (audio features from Gio only) |
| Number of outputs | 3 |
| Output meaning | Output 1 = oscillator pitch offset, Output 2 = filter cutoff, Output 3 = reverb depth |
| Output range | [0, 1] for all three |

This model answers: "given this sound, how should the synthesised audio respond?"

---

## Important: How Wekinator Receives Both Scripts

Wekinator listens on a single input port. Both Gio (port 9001) and Rani (port 9000) send to Machine 2. You need to configure Wekinator so it merges both streams into a single input vector of 10 values. The standard approach is to run a small OSC router or to configure Wekinator with a custom input address. Discuss this with Sam — he may write a small Processing sketch that receives both streams and forwards them as a single merged message to Wekinator's default port (6448). This forwarding sketch is Sam's responsibility, but you need to agree on the merged message format together.

The merged input Wekinator receives must be a single OSC message with 10 floats in this order:
`[arm_spread, tilt_angle, head_height, arm_elevation, rms, centroid, zcr, mfcc1, mfcc2, mfcc3]`

---

## Training Procedure

**Step 1 — Train the mood classifier first.**

Have the performer stand in front of the camera and microphone. Run both Gio's and Rani's scripts. Select class 1 (calm) in Wekinator. Have the performer adopt the calm state: standing still, arms relaxed, quiet or soft voice. Click "Start Recording". Wait 10 to 15 seconds — this gives you 20 to 30 examples at 30 Hz. Click "Stop Recording". Repeat for all four states:

- Class 1 Calm: still body, arms down, soft or no voice
- Class 2 Tense: hunched posture, arms close to body, sharp short sounds or silence
- Class 3 Chaotic: arms wide and moving fast, loud or erratic voice
- Class 4 Harmonic: arms open and balanced, slow movements, sustained steady tone

Record at least 20 examples per class. More is better. Click "Train". Click "Run". You should now see the output changing in real time as the performer shifts between states.

**Step 2 — Train the visual regressor.**

Switch to Model 2. Set output sliders to maximum (1, 1, 1). Have the performer spread arms wide and move energetically. Record 15 to 20 examples. Then set output sliders to minimum (0, 0, 0). Have the performer stand still with arms down. Record 15 to 20 examples. Add a few intermediate positions with intermediate slider values. Train.

**Step 3 — Train the audio synth regressor.**

Switch to Model 3. Set output sliders to (1, 1, 1). Have the performer make a loud, bright, dense sound (clap, shout, sing loudly). Record examples. Set to (0, 0, 0). Have the performer stay silent or hum very quietly. Record examples. Train.

This procedure is exactly what Lab 3 Exercise 1 practises with mouse gestures. The logic is the same.

---

## Verifying the Output

After training all three models and clicking Run, the `/wek/outputs` message Wekinator sends to Processing should contain 7 values:
`[mood_class, visual1, visual2, visual3, audio1, audio2, audio3]`

Sam's Processing sketch listens for this on port 12000. Coordinate with Sam to verify the values arrive and are in the expected ranges before he starts the full renderer.

---

## Saving Your Work

Save the Wekinator project file after every training session. The file has a `.wekproj` extension. Copy it into `machine2/wekinator_project/` in the repository so the whole group has a backup.

---

## TODO List

- [ ] Read Lecture 4 (Cognitive Agents and ML) in full, especially the sections on KNN, classification, regression, and Wekinator setup
- [ ] Re-do Lab 2 Exercise 1 mentally to recall the classification training workflow
- [ ] Re-do Lab 3 Exercise 1 mentally to recall the regression training workflow
- [ ] Download Wekinator from http://www.wekinator.org/downloads/ and confirm it runs on Machine 2
- [ ] Wait for Gio and Rani to confirm their scripts are sending OSC — do not start configuring until this is done
- [ ] Coordinate with Sam on the OSC merging strategy (how both streams become one input to Wekinator)
- [ ] Configure Model 1: classification, 10 inputs, 1 output, 4 classes, KNN k=3
- [ ] Configure Model 2: regression, 4 inputs, 3 outputs, KNN k=3
- [ ] Configure Model 3: regression, 6 inputs, 3 outputs, KNN k=3
- [ ] Run a training session for Model 1 with the performer — minimum 20 examples per class for all 4 moods
- [ ] Train Model 1 and verify the classifier output changes correctly as the performer shifts states
- [ ] Run a training session for Model 2 with extreme body positions
- [ ] Train Model 2 and verify regression outputs respond smoothly to body movement
- [ ] Run a training session for Model 3 with loud/soft sounds
- [ ] Train Model 3 and verify regression outputs respond smoothly to voice/sound changes
- [ ] Confirm `/wek/outputs` is being sent to port 12000 and Sam's sketch receives the 7 values
- [ ] Save the `.wekproj` file and add it to `machine2/wekinator_project/` in the repository
- [ ] If the classifier is confused between states, add more training examples for the failing classes and retrain

---

## Hand-Off Condition

You are done when Sam's Processing sketch is receiving `/wek/outputs` on port 12000, the 7 values are in [0, 1] range (except the first which is 1-4), and all three values respond visibly to the performer's body and voice. Run the full system end to end with everyone present before calling this complete.
