"""
audio_sensing.py  —  Gio / Machine 1
=====================================
Body Conductor | Audio feature extractor

Reads the microphone in real time, computes 6 low-level audio features with
librosa, normalises each to [0, 1], and forwards them as an OSC message to
Sam's forwarder sketch (or directly to Wekinator during isolated tests) at
≈30 Hz.

OSC contract (must match Sam's osc_forwarder.pde and Stella's Wekinator config):
  address : /features/audio
  payload : 6 floats in this exact order —
            [rms, centroid, zcr, mfcc1, mfcc2, mfcc3]
  port    : 9001   (Rani owns 9000 — never use the same port)

The merged 10-value vector that Wekinator finally sees is:
  [arm_spread, tilt_angle, head_height, arm_elevation,   <- Rani's 4
   rms, centroid, zcr, mfcc1, mfcc2, mfcc3]              <- Gio's 6

Install dependencies once:
    pip install librosa sounddevice python-osc numpy

Run (replace IP with Machine 2's actual IP when connecting for real):
    python audio_sensing.py --ip 127.0.0.1 --port 9001
"""

import argparse
import time

import librosa
import numpy as np
import sounddevice as sd
from pythonosc import udp_client

# ──────────────────────────────────────────────────────────────────────────────
# Audio capture settings
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE_RATE = 22050   # Hz  — librosa's native default; keep this consistent
FRAME_SIZE  = 2048    # samples per callback (~93 ms at 22050 Hz → well above 30 Hz)

# ──────────────────────────────────────────────────────────────────────────────
# Normalisation ranges
# Tune these by running with --calibrate for 30 s while making all kinds of
# sounds (silence, speech, clap, hum, shout).  Values outside the range are
# clamped to [0, 1] — that is intentional.
# ──────────────────────────────────────────────────────────────────────────────
NORM_RANGES = {
    "rms"      : (0.0,   0.3),
    "centroid" : (200.0, 8000.0),
    "zcr"      : (0.0,   0.5),
    "mfcc1"    : (-600.0, 200.0),
    "mfcc2"    : (-100.0, 100.0),
    "mfcc3"    : (-80.0,  80.0),
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def normalise(value: float, min_val: float, max_val: float) -> float:
    """Clamp-normalise a scalar to [0, 1]."""
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compute_features(frame: np.ndarray, sr: int) -> list[float]:
    """
    Extract the 6 audio features from a single audio frame.

    Parameters
    ----------
    frame : np.ndarray
        Raw audio samples from sounddevice (shape: [FRAME_SIZE, 1] or [FRAME_SIZE])
    sr : int
        Sample rate in Hz

    Returns
    -------
    list[float]
        [rms_n, centroid_n, zcr_n, mfcc1_n, mfcc2_n, mfcc3_n]  — all in [0, 1]
    """
    frame = frame.flatten().astype(np.float32)

    # ── Raw feature extraction ──────────────────────────────────────────────
    rms      = float(librosa.feature.rms(y=frame)[0][0])
    centroid = float(librosa.feature.spectral_centroid(y=frame, sr=sr)[0][0])
    zcr      = float(librosa.feature.zero_crossing_rate(frame)[0][0])

    # librosa.feature.mfcc returns shape (n_mfcc, n_frames); we take the mean
    # of each coefficient across the (short) frame.
    mfccs = librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=4)
    mfcc1 = float(mfccs[0].mean())
    mfcc2 = float(mfccs[1].mean())
    mfcc3 = float(mfccs[2].mean())

    # ── Normalise to [0, 1] ─────────────────────────────────────────────────
    rms_n      = normalise(rms,      *NORM_RANGES["rms"])
    centroid_n = normalise(centroid, *NORM_RANGES["centroid"])
    zcr_n      = normalise(zcr,      *NORM_RANGES["zcr"])
    mfcc1_n    = normalise(mfcc1,    *NORM_RANGES["mfcc1"])
    mfcc2_n    = normalise(mfcc2,    *NORM_RANGES["mfcc2"])
    mfcc3_n    = normalise(mfcc3,    *NORM_RANGES["mfcc3"])

    return [rms_n, centroid_n, zcr_n, mfcc1_n, mfcc2_n, mfcc3_n]


# ──────────────────────────────────────────────────────────────────────────────
# Calibration helper  (run with --calibrate to find your real ranges)
# ──────────────────────────────────────────────────────────────────────────────

def calibrate(duration: float = 30.0) -> None:
    """
    Record raw (un-normalised) feature values for `duration` seconds and print
    min/max for each.  Use the output to update NORM_RANGES above.
    """
    print(f"\n[CALIBRATE] Make all kinds of sounds for {duration:.0f} seconds …\n")
    records: dict[str, list[float]] = {k: [] for k in NORM_RANGES}

    def _cb(indata, frames, t, status):
        f = indata.flatten().astype(np.float32)
        records["rms"].append(float(librosa.feature.rms(y=f)[0][0]))
        records["centroid"].append(
            float(librosa.feature.spectral_centroid(y=f, sr=SAMPLE_RATE)[0][0])
        )
        records["zcr"].append(float(librosa.feature.zero_crossing_rate(f)[0][0]))
        mfccs = librosa.feature.mfcc(y=f, sr=SAMPLE_RATE, n_mfcc=4)
        records["mfcc1"].append(float(mfccs[0].mean()))
        records["mfcc2"].append(float(mfccs[1].mean()))
        records["mfcc3"].append(float(mfccs[2].mean()))

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1,
        blocksize=FRAME_SIZE, callback=_cb,
    ):
        time.sleep(duration)

    print("\n[CALIBRATE] Suggested NORM_RANGES (raw min / raw max observed):")
    print(f"{'Feature':<12}  {'min':>10}  {'max':>10}")
    print("-" * 36)
    for key, vals in records.items():
        if vals:
            print(f"{key:<12}  {min(vals):>10.4f}  {max(vals):>10.4f}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Body Conductor — Gio audio sensing (OSC sender)"
    )
    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="Target IP (Machine 2).  Use 127.0.0.1 for localhost tests.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9001,
        help="OSC destination port (default: 9001 — Rani owns 9000).",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run a 30-second calibration pass and print recommended ranges.",
    )
    parser.add_argument(
        "--calibrate-duration",
        type=float,
        default=30.0,
        metavar="SECONDS",
        help="Duration of the calibration pass (default: 30 s).",
    )
    args = parser.parse_args()

    if args.calibrate:
        calibrate(args.calibrate_duration)
        return

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    print(f"[Gio] Audio sensing running.")
    print(f"      Sending /features/audio  →  {args.ip}:{args.port}")
    print(f"      Sample rate: {SAMPLE_RATE} Hz | Frame size: {FRAME_SIZE} samples")
    print("      Press Ctrl+C to stop.\n")

    # Header for the console table printed every frame
    print(f"{'rms':>6}  {'centroid':>8}  {'zcr':>6}  {'mfcc1':>6}  {'mfcc2':>6}  {'mfcc3':>6}")
    print("-" * 50)

    def callback(indata: np.ndarray, frames: int, t, status) -> None:
        if status:
            # e.g. input overflow — log but don't crash
            print(f"[sounddevice] {status}")

        features = compute_features(indata, SAMPLE_RATE)

        # Send OSC — address and payload must match Sam's osc_forwarder.pde
        client.send_message("/features/audio", features)

        # Console feedback (remove in final performance to reduce CPU)
        rms, cen, zcr, m1, m2, m3 = features
        print(
            f"{rms:6.3f}  {cen:8.3f}  {zcr:6.3f}  {m1:6.3f}  {m2:6.3f}  {m3:6.3f}",
            flush=True,
        )

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        blocksize=FRAME_SIZE,
        callback=callback,
    ):
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            print("\n[Gio] Stopped.")


if __name__ == "__main__":
    main()