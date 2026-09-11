"""
wake_word.py — Continuous listening state machine for Jarvis.

Replaces push_to_talk.py.
State 1 (Passive): openwakeword listens for "hey jarvis" (low CPU).
State 2 (Active) : vosk transcribes the command until silence is detected.
"""

import os
import json
import threading
import winsound
import numpy as np
import sounddevice as sd
import time

from push_to_talk import _load_vosk_model, VOSK_RATE, CHUNK

_is_listening = False
_listener_thread = None

def _play_wake_chime():
    """Play a subtle native Windows ding to confirm wake word."""
    # SND_ASYNC means it plays in background without blocking
    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)


def start_wake_word_listener(on_transcribed_callback, on_error_callback=None):
    """Start the continuous wake-word and command listening thread."""
    global _is_listening, _listener_thread
    
    if _is_listening:
        return

    # 1. Load Vosk
    vosk_rec, _ = _load_vosk_model()
    if not vosk_rec:
        print("[Voice] Vosk failed to load. Wake word disabled.")
        return

    # 2. Load openWakeWord
    try:
        from openwakeword.model import Model
        # Find the jarvis model automatically from built-ins
        import openwakeword
        paths = openwakeword.get_pretrained_model_paths()
        jarvis_path = next((p for p in paths if "jarvis" in p.lower()), None)
        
        if jarvis_path:
            oww = Model(wakeword_models=[jarvis_path], inference_framework="onnx")
            jarvis_key = list(oww.models.keys())[0]
        else:
            print("[Voice] No built-in Jarvis model found in openwakeword. Using defaults.")
            oww = Model(inference_framework="onnx")
            jarvis_key = next((k for k in oww.models.keys() if "jarvis" in k.lower()), list(oww.models.keys())[0])
            
    except ImportError:
        print("[Voice] 'openwakeword' not installed. Please run: pip install openwakeword")
        return

    _is_listening = True

    def listener_loop():
        from hud import set_hud_state
        print("\n[OK] Wake word active: Say 'Hey Jarvis' to wake.")
        
        # Audio stream parameters: openwakeword and vosk both need 16kHz 16-bit mono
        RATE = 16000
        CHUNK_SIZE = 1280  # 80ms chunks (ideal for openwakeword)
        
        state = "SLEEPING"
        silence_timeout = 5.0  # Max seconds to wait for a command before sleeping
        wake_time = 0.0

        try:
            with sd.RawInputStream(samplerate=RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE) as stream:
                while _is_listening:
                    data, overflow = stream.read(CHUNK_SIZE)
                    if overflow:
                        continue
                        
                    audio_np = np.frombuffer(data, dtype=np.int16)

                    if state == "SLEEPING":
                        # Feed to openWakeWord
                        prediction = oww.predict(audio_np)
                        
                        # Threshold check
                        if prediction.get(jarvis_key, 0.0) > 0.5:
                            print("\n[WAKE] Heard 'Hey Jarvis'!")
                            _play_wake_chime()
                            set_hud_state("listening")
                            vosk_rec.Reset()
                            state = "AWAKE"
                            wake_time = time.time()
                            
                    elif state == "AWAKE":
                        # Feed to Vosk
                        is_final = vosk_rec.AcceptWaveform(data)
                        
                        # Fallback timeout in case user wakes but says nothing
                        if time.time() - wake_time > silence_timeout:
                            print("[WAKE] Timeout — returning to sleep.")
                            set_hud_state("idle")
                            state = "SLEEPING"
                            continue
                            
                        # If Vosk detects a full utterance (silence endpointing)
                        if is_final:
                            result = json.loads(vosk_rec.Result())
                            text = result.get("text", "").strip()
                            
                            set_hud_state("thinking")
                            if text:
                                print(f"\n[VOICE] {text}")
                                # Execute command in a new thread so we don't block audio loop
                                threading.Thread(target=on_transcribed_callback, args=(text,), daemon=True).start()
                            else:
                                set_hud_state("idle")
                                
                            # Go back to sleep immediately
                            state = "SLEEPING"
                            
        except Exception as e:
            print(f"[Voice] Audio stream crashed: {e}")
            if on_error_callback:
                on_error_callback("My audio stream crashed, sir.")

    _listener_thread = threading.Thread(target=listener_loop, daemon=True, name="WakeWord")
    _listener_thread.start()

