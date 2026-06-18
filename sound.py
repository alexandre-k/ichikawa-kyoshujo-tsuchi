import shutil
import time
import os
import time
import math
import struct
import wave
import shutil
import subprocess
import tempfile


def _write_sine_wav(path, freq=880.0, duration=0.18, sr=44100, volume=0.5):
    n_samples = int(sr * duration)
    amplitude = int(32767 * volume)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sr)
        for i in range(n_samples):
            t = i / sr
            sample = int(amplitude * math.sin(2.0 * math.pi * freq * t))
            wf.writeframesraw(struct.pack("<h", sample))

def victory_sound():
    tones = [880.0, 1320.0, 1760.0]  # A5, E6, A6-ish

    paplay = shutil.which("paplay")
    aplay = shutil.which("aplay")
    ffplay = shutil.which("ffplay")

    print("[sound] tools:", {"paplay": bool(paplay), "aplay": bool(aplay), "ffplay": bool(ffplay)})

    if not (paplay or aplay or ffplay):
        print("[sound] No paplay/aplay/ffplay found; fallback bell:", flush=True)
        print("\a🎉 VICTORY 🎉", flush=True)
        return

    tmp_dir = tempfile.gettempdir()
    played_any = False

    for j, f in enumerate(tones):
        wav_path = os.path.join(tmp_dir, f"victory_{j}_{int(f)}.wav")
        _write_sine_wav(wav_path, freq=f)

        cmd = None
        if paplay:
            cmd = [paplay, wav_path]
        elif aplay:
            cmd = [aplay, wav_path]
        else:
            # ffplay is commonly used like: ffplay -nodisp -autoexit <file>
            cmd = [ffplay, "-nodisp", "-autoexit", wav_path]

        try:
            print("[sound] running:", " ".join(cmd))
            p = subprocess.run(cmd, check=False)
            print("[sound] exit code:", p.returncode)
            played_any = True
        except Exception as e:
            print("[sound] command failed:", e)

        time.sleep(0.03)

    if not played_any:
        print("[sound] attempted playback but nothing worked.")

