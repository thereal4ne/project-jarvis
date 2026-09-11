"""
push_to_talk.py — Hold Ctrl+Space to speak to Jarvis.

Uses Vosk for 100% offline speech recognition — no subprocess,
no FLAC encoder, no internet, no WinError 50.
"""

import os
import json
import wave
import struct
import threading
import tempfile
import numpy as np
import sounddevice as sd

CHUNK     = 1024
VOSK_RATE = 16000   # Vosk requires 16000 Hz — we resample from mic rate

def _find_vosk_model() -> str:
    """Auto-detect the best available Vosk model in the project directory.

    Preference order (higher index = preferred):
      small < lgraph < full large model
    Any folder matching vosk-model* is considered. Largest folder wins
    as a heuristic for best accuracy — drop a new model folder in and
    this will automatically prefer it over the small model.
    """
    base = os.path.dirname(__file__)
    candidates = [
        d for d in os.listdir(base)
        if d.startswith("vosk-model") and os.path.isdir(os.path.join(base, d))
    ]
    if not candidates:
        raise FileNotFoundError(
            "No Vosk model found. Download one from https://alphacephei.com/vosk/models\n"
            "Recommended: vosk-model-en-us-0.22-lgraph (128MB, good accuracy)\n"
            f"Extract into: {base}"
        )
    # Prefer by total recursive folder size (largest = most accurate in practice)
    def _folder_size(path: str) -> int:
        total = 0
        for dirpath, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
        return total

    candidates.sort(key=lambda d: _folder_size(os.path.join(base, d)), reverse=True)

    chosen = os.path.join(base, candidates[0])
    print(f"[PTT] Using Vosk model: {candidates[0]}")
    return chosen

MODEL_DIR = _find_vosk_model()


def _get_device_sample_rate() -> int:
    try:
        info = sd.query_devices(kind='input')
        return int(info['default_samplerate'])
    except Exception:
        return 44100


def _resample(audio_np: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
    """Simple linear resample from orig_rate to target_rate."""
    if orig_rate == target_rate:
        return audio_np
    ratio = target_rate / orig_rate
    new_len = int(len(audio_np) * ratio)
    return np.interp(
        np.linspace(0, len(audio_np) - 1, new_len),
        np.arange(len(audio_np)),
        audio_np.astype(np.float32)
    ).astype(np.int16)


def _load_vosk_model():
    """Loads Vosk model + creates a persistent recognizer reused across calls."""
    try:
        import vosk
        vosk.SetLogLevel(-1)
        if not os.path.exists(MODEL_DIR):
            print(f"[Voice] Vosk model not found at: {MODEL_DIR}")
            print("[Voice] Run: python download_vosk_model.py")
            return None, None
        model = vosk.Model(MODEL_DIR)
        rec = vosk.KaldiRecognizer(model, VOSK_RATE)
        rec.SetWords(False)   # Words=False is faster — we only need final text
        return rec, vosk
    except ImportError:
        print("[Voice] Vosk not installed. Run: pip install vosk")
        return None, None


def _transcribe_vosk(audio_np: np.ndarray, rec, vosk_module) -> str:
    """Transcribes using pre-loaded recognizer. Reset() is instant vs new instance."""
    rec.Reset()   # Clear state between calls — much faster than creating a new recognizer

    chunk_size = 4000
    for i in range(0, len(audio_np), chunk_size):
        chunk = audio_np[i:i + chunk_size]
        rec.AcceptWaveform(chunk.tobytes())

    result = json.loads(rec.FinalResult())
    return result.get("text", "").strip()


def start_push_to_talk_listener(on_transcribed_callback, on_error_callback=None):
    """
    Starts a background thread for push-to-talk using Vosk offline STT.
    """
    try:
        import keyboard
    except ImportError:
        print("[Voice] 'keyboard' library not installed.")
        return None

    rec, vosk_module = _load_vosk_model()
    if rec is None:
        print("[Voice] STT unavailable — push-to-talk disabled.")
        return None

    MIC_RATE = _get_device_sample_rate()
    print(f"[PTT] Mic: {MIC_RATE} Hz -> Vosk: {VOSK_RATE} Hz (resampled offline)")

    def full_listener():
        while True:
            try:
                # --- Wait for Ctrl+Space press ---
                keyboard.wait("ctrl+space")
                from hud import set_hud_state
                set_hud_state("listening")
                print("\n[MIC] Listening... (release Ctrl+Space when done)")

                frames = []

                # Blocking read loop — more compatible than callback on Windows
                with sd.InputStream(samplerate=MIC_RATE, channels=1, dtype='int16') as stream:
                    while keyboard.is_pressed("ctrl") or keyboard.is_pressed("space"):
                        data, _ = stream.read(CHUNK)
                        frames.append(data.copy())

                set_hud_state("thinking")
                print("[>>] Recognizing...")

                if not frames:
                    set_hud_state("idle")
                    msg = "I didn't catch any audio, sir. Please try again."
                    print(f"[Voice] {msg}")
                    if on_error_callback:
                        on_error_callback(msg)
                    continue

                # Flatten + resample to 16000 Hz for Vosk
                audio_np = np.concatenate(frames, axis=0).flatten()
                duration = len(audio_np) / MIC_RATE

                if duration < 0.4:
                    set_hud_state("idle")
                    msg = "Too short, sir. Hold the key while speaking."
                    print(f"[Voice] {msg}")
                    if on_error_callback:
                        on_error_callback(msg)
                    continue

                audio_16k = _resample(audio_np, MIC_RATE, VOSK_RATE)
                text = _transcribe_vosk(audio_16k, rec, vosk_module)

                if text:
                    print(f"\nYOU (voice) > {text}")
                    on_transcribed_callback(text)
                else:
                    set_hud_state("idle")
                    msg = "I didn't understand that, sir. Please try again."
                    print(f"[Voice] {msg}")
                    if on_error_callback:
                        on_error_callback(msg)
                        
                # Visually reprint the prompt for the main thread
                import sys
                sys.stdout.write("\n👤 YOU > ")
                sys.stdout.flush()
                
                # Command handled, return to idle
                set_hud_state("idle")

            except Exception as e:
                set_hud_state("idle")
                print(f"[Voice] Listener error: {e}")
                import time
                time.sleep(0.5)

    thread = threading.Thread(target=full_listener, daemon=True, name="PTT-Listener")
    thread.start()
    return thread
