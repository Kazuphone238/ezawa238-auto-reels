import math
import random
import shutil
import subprocess
import wave
from array import array
from pathlib import Path

DURATION = 15
RATE = 44100
BPM = 128
BEAT = 60 / BPM
OUT = Path("output")
OUT.mkdir(exist_ok=True)

if not shutil.which("ffmpeg"):
    raise SystemExit("FFmpeg is required. Run through GitHub Actions.")

rng = random.Random()
root = rng.choice([57, 59, 60, 62])
notes = [0, 7, 12, 10, 7, 3, 5, 7]
chords = [0, -3, -5, -7]


def frequency(note):
    return 440 * 2 ** ((note - 69) / 12)


samples = array("h")
for i in range(RATE * DURATION):
    t = i / RATE
    beat_pos = t % BEAT
    step = int(t / (BEAT / 2))
    note_pos = t % (BEAT / 2)
    chord = chords[int(t / (BEAT * 4)) % 4]

    # A descending kick, offbeat bass and bright arpeggio.
    kick_phase = 2 * math.pi * (
        48 * beat_pos
        + 100 * 0.025 * (1 - math.exp(-beat_pos / 0.025))
    )
    kick = math.sin(kick_phase) * math.exp(-beat_pos * 22)

    bass_note = frequency(root - 12 + chord)
    bass_env = math.sin(math.pi * beat_pos / BEAT) ** 2
    bass = math.sin(2 * math.pi * bass_note * t) * bass_env

    lead_note = frequency(root + notes[step % len(notes)])
    lead_env = (1 - math.exp(-note_pos * 120))
    lead_env *= math.exp(-note_pos * 9)
    lead = (
        math.sin(2 * math.pi * lead_note * t)
        + 0.3 * math.sin(4 * math.pi * lead_note * t)
    ) * lead_env

    hat_pos = t % (BEAT / 2)
    hat = rng.uniform(-1, 1) * math.exp(-hat_pos * 110)

    pad = sum(
        math.sin(2 * math.pi * frequency(root + chord + n) * t)
        for n in [0, 3, 7]
    ) / 3
    duck = 0.25 + 0.75 * min(beat_pos / 0.12, 1)
    energy = 0.55 if 5.5 <= t < 7.5 else 1.0
    fade = min(t / 0.03, (DURATION - t) / 0.25, 1)

    sound = (
        0.42 * kick * energy
        + duck * (
            0.20 * bass * energy
            + 0.18 * lead
            + 0.09 * pad
            + 0.07 * hat * energy
        )
    ) * fade
    samples.append(int(max(-1, min(1, sound)) * 32767))

audio = OUT / "music.wav"
with wave.open(str(audio), "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(RATE)
    import sys
    if sys.byteorder != "little":
        samples.byteswap()
    f.writeframes(samples.tobytes())

video = OUT / "ezawa238_reel.mp4"
subprocess.run([
    "ffmpeg", "-y", "-i", str(audio),
    "-filter_complex",
    "[0:a]showwaves=s=1080x1920:mode=cline:"
    "rate=30:colors=0x00E5FF,format=yuv420p[v]",
    "-map", "[v]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
    "-c:a", "aac", "-b:a", "192k",
    "-t", str(DURATION), "-movflags", "+faststart",
    str(video)
], check=True)

print(f"Created: {video}")
