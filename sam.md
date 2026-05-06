# Sam — Processing Renderer and Streaming Manual
## Machine 2 | Processing + oscP5 + Sound Library + OBS + mediamtx

---

## What You Are Building

You are responsible for two things: the audiovisual renderer in Processing, and the live streaming setup with OBS and mediamtx.

The Processing sketch listens for Wekinator's output on localhost port 12000, reads 7 values per frame, and uses them to drive a particle system, a colour field, a waveform ribbon, and synthesised audio. This is the visible face of the entire project — everything the audience sees and hears comes from your sketch.

The streaming setup captures your Processing window with OBS and pushes it to a mediamtx server so anyone on the network can watch in a browser.

You also have one additional technical responsibility: writing a small OSC forwarding sketch that merges Rani's and Gio's two separate OSC streams into a single message for Wekinator. This is a short piece of code but it is critical because Wekinator expects one combined input, not two separate ones.

---

## Lecture and Lab References

Before writing any code, read the following:

- **Tools lecture (02_2 Tools PDF)** — covers Processing, the Sound library, and oscP5. It shows that Processing can do sound synthesis (oscillators), audio capture, and OSC communication. This is your toolkit reference.
- **Lab 2, Exercise 1 (Part 2)** — the visualisation sketch that receives a class from Wekinator and changes the canvas colour. This is the exact starting pattern your renderer extends. The professor's `Processing_ColorAndSound_1Classifier.pde` file is your template for OSC receiving.
- **Lab 3, Exercise 1 (Part 2)** — receives regression outputs from Wekinator and uses them to control a circle's size and alpha. This is the regression receiving pattern you extend.
- **Lecture 4 (Cognitive Agents and ML)** — explains what OSC is, how `/wek/outputs` is structured, and what port 12000 means in the Wekinator context.
- **Project Assignment PDF** — section on streaming specifies OBS as the required capture tool and mediamtx as the suggested server. Read this section so you understand the requirements.

---

## Part 1: The OSC Forwarder (Write This First)

Before building the renderer, you need a small Processing sketch that solves the following problem: Gio sends to port 9001, Rani sends to port 9000, but Wekinator expects one single OSC message with all 10 features combined.

Write a sketch called `osc_forwarder.pde` that:
1. Listens on ports 9000 and 9001
2. Stores the last received body features (4 floats) and audio features (6 floats) in global arrays
3. Every draw loop, sends a single merged OSC message to Wekinator on port 6448 with all 10 floats combined

```processing
import oscP5.*;
import netP5.*;

OscP5 oscP5_body;
OscP5 oscP5_audio;
NetAddress wekinator;

float[] bodyFeatures  = {0, 0, 0, 0};
float[] audioFeatures = {0, 0, 0, 0, 0, 0};

void setup() {
  size(300, 100);
  oscP5_body  = new OscP5(this, 9000);
  oscP5_audio = new OscP5(this, 9001);
  wekinator   = new NetAddress("127.0.0.1", 6448);
}

void draw() {
  frameRate(30);
  background(40);
  text("Forwarder running", 10, 50);

  OscMessage msg = new OscMessage("/wek/inputs");
  for (float v : bodyFeatures)  msg.add(v);
  for (float v : audioFeatures) msg.add(v);
  oscP5_body.send(msg, wekinator);
}

void oscEvent(OscMessage m) {
  if (m.checkAddrPattern("/features/body") && m.typetag().length() >= 4) {
    for (int i = 0; i < 4; i++) bodyFeatures[i] = m.get(i).floatValue();
  }
  if (m.checkAddrPattern("/features/audio") && m.typetag().length() >= 6) {
    for (int i = 0; i < 6; i++) audioFeatures[i] = m.get(i).floatValue();
  }
}
```

Run this sketch on Machine 2 at the same time as Wekinator. Confirm Stella sees 10 inputs arriving in Wekinator before she starts training.

---

## Part 2: The Main Renderer

The renderer is a separate Processing sketch in `machine2/processing_renderer/`. It listens on port 12000 for `/wek/outputs` from Wekinator and drives the visuals and audio.

### What the 7 values mean

```
wekOutputs[0] = mood class (integer 1-4: 1=calm, 2=tense, 3=chaotic, 4=harmonic)
wekOutputs[1] = particle count multiplier  [0,1]
wekOutputs[2] = particle scale             [0,1]
wekOutputs[3] = particle speed             [0,1]
wekOutputs[4] = oscillator pitch offset    [0,1]
wekOutputs[5] = filter cutoff              [0,1]
wekOutputs[6] = reverb depth               [0,1]
```

### Receiving OSC (from Processing_ColorAndSound_1Classifier.pde pattern)

```processing
import oscP5.*;
import netP5.*;

OscP5 oscP5;
float[] wekOutputs = new float[7];

void setup() {
  size(800, 600);
  oscP5 = new OscP5(this, 12000);  // same port used in the lab examples
}

void oscEvent(OscMessage m) {
  if (m.checkAddrPattern("/wek/outputs")) {
    for (int i = 0; i < min(7, m.typetag().length()); i++) {
      wekOutputs[i] = m.get(i).floatValue();
    }
  }
}
```

### Colour field based on mood class

```processing
color getMoodColour(int mood) {
  if (mood == 1) return color(0, 50, 150);    // calm: deep blue
  if (mood == 2) return color(200, 120, 0);   // tense: amber
  if (mood == 3) return color(220, 30, 30);   // chaotic: red
  if (mood == 4) return color(0, 160, 150);   // harmonic: teal
  return color(50);
}
```

Interpolate smoothly between the current and target colour using `lerpColor()`:

```processing
color currentBg = color(0, 50, 150);

void draw() {
  color targetBg = getMoodColour((int) wekOutputs[0]);
  currentBg = lerpColor(currentBg, targetBg, 0.05);
  background(currentBg);
  // ... rest of draw
}
```

### Particle system

Create an array of `Particle` objects. Each frame, spawn new particles based on `wekOutputs[1]` (count multiplier), draw them with size based on `wekOutputs[2]`, and move them with velocity based on `wekOutputs[3]`.

```processing
class Particle {
  PVector pos, vel;
  float lifespan;
  color col;

  Particle(float x, float y, float speed, float size, color c) {
    pos = new PVector(x, y);
    vel = PVector.random2D().mult(speed * 4);
    lifespan = 255;
    col = c;
  }

  void update() {
    pos.add(vel);
    lifespan -= 4;
  }

  void display(float sz) {
    noStroke();
    fill(col, lifespan);
    ellipse(pos.x, pos.y, sz, sz);
  }

  boolean isDead() { return lifespan <= 0; }
}
```

In `draw()`, spawn particles proportional to `wekOutputs[1]` and update/display them with `wekOutputs[2]` and `wekOutputs[3]`.

### Audio synthesis (Processing Sound library)

```processing
import processing.sound.*;

SinOsc osc1, osc2;
LowPassSP filter;

void setup() {
  // ... existing setup code
  osc1 = new SinOsc(this);
  osc2 = new SinOsc(this);
  osc1.play();
  osc2.play();
}

void draw() {
  // map wekOutputs[4] (0-1) to a frequency range e.g. 100-800 Hz
  float freq = map(wekOutputs[4], 0, 1, 100, 800);
  osc1.freq(freq);
  osc2.freq(freq * 1.5);  // harmony interval

  // map wekOutputs[5] to amplitude
  float amp = map(wekOutputs[5], 0, 1, 0.0, 0.4);
  osc1.amp(amp);
  osc2.amp(amp * 0.6);
}
```

Note: The Sound library uses `SinOsc`, `SawOsc`, `LowPassSP`, and `Reverb` classes. These are covered in the Tools lecture and the Processing Sound library reference at https://processing.org/reference/libraries/.

---

## Part 3: Streaming Setup (OBS + mediamtx)

Do this after the renderer is working and stable.

### mediamtx

1. Download mediamtx from https://github.com/bluenviron/mediamtx/releases — pick the binary for your OS.
2. Extract it. The default config file `mediamtx.yml` works out of the box.
3. Run it: `./mediamtx` in the terminal. It starts an RTMP server on port 1935 and an HLS/WebRTC server on port 8888.

### OBS Studio

1. Download OBS from https://obsproject.com and install it.
2. In OBS, create a new Scene.
3. Add a Source: choose "Window Capture" and select the Processing renderer window.
4. Go to Settings > Stream:
   - Service: Custom
   - Server: `rtmp://localhost/live`
   - Stream Key: `stream`
5. Click "Start Streaming".

### Verify the stream

On any device on the same network, open a browser and go to:
```
http://<machine2-ip>:8888/live/stream
```

You should see the Processing window streaming live. Test this from a phone or a second laptop before the demo.

---

## TODO List

**OSC Forwarder**
- [ ] Read the oscP5 documentation and the `OSC_receiver_test.pde` professor example to understand how to receive on multiple ports
- [ ] Write `osc_forwarder.pde` in `machine2/processing_renderer/`
- [ ] Test it by running Gio's and Rani's scripts and confirming Wekinator sees 10 inputs live

**Renderer — OSC and basic structure**
- [ ] Study `Processing_ColorAndSound_1Classifier.pde` provided by the professor — this is your OSC receiving template
- [ ] Create the main sketch `body_conductor.pde` and set up OSC listening on port 12000
- [ ] Print the 7 received values to the console and confirm they change as the performer moves

**Renderer — visuals**
- [ ] Implement the colour field with `lerpColor()` switching between the 4 mood palettes
- [ ] Implement the Particle class with position, velocity, and lifespan
- [ ] Implement particle spawning driven by `wekOutputs[1]`, size by `wekOutputs[2]`, speed by `wekOutputs[3]`
- [ ] Test visuals with hardcoded values before connecting to Wekinator output

**Renderer — audio**
- [ ] Install the Processing Sound library via Sketch > Import Library > Add Library
- [ ] Add two SinOsc oscillators driven by `wekOutputs[4]`
- [ ] Map `wekOutputs[5]` to amplitude
- [ ] Verify audio output works and does not cause feedback with the microphone on Machine 1

**Integration**
- [ ] Run the full chain: Rani + Gio scripts running, Wekinator trained, renderer receiving — confirm everything responds end to end
- [ ] Check that the frame rate stays at 30 fps under full load

**Streaming**
- [ ] Download and run mediamtx — confirm the RTMP endpoint is accessible
- [ ] Set up OBS with the Processing window as source
- [ ] Configure OBS to stream to `rtmp://localhost/live` with key `stream`
- [ ] Verify the stream appears in a browser at `http://<machine2-ip>:8888/live/stream`
- [ ] Test the stream from a second device (phone or laptop) on the same network
- [ ] Push all code to your branch `feature/rendering-streaming` and open a pull request to main

---

## Hand-Off Condition

You are done when:
1. The renderer visibly responds to the performer's body and voice in real time.
2. The stream is accessible from a browser on a second device on the same network.
3. A 2-minute run-through of the full system end to end completes without crashes.

This is the final integration point. Everyone's work converges here.
