import sounddevice as sd
import numpy as np
import speech_recognition as sr
import traceback

SAMPLE_RATE = 44100

print("Step 1: Testing InputStream open...")
try:
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
        print("Step 2: Stream opened OK. Reading 1 chunk...")
        data, _ = stream.read(1024)
        print(f"Step 3: Read OK. Shape: {data.shape}")
    print("Step 4: Stream closed OK.")
except Exception as e:
    print(f"FAILED at InputStream: {e}")
    traceback.print_exc()

print("\nStep 5: Testing numpy concatenate...")
try:
    dummy = [np.zeros((1024,1), dtype=np.int16) for _ in range(10)]
    audio = np.concatenate(dummy, axis=0).flatten()
    print(f"Concat OK. Shape: {audio.shape}")
except Exception as e:
    print(f"FAILED at concatenate: {e}")
    traceback.print_exc()

print("\nStep 6: Testing Google Speech Recognition call...")
try:
    recognizer = sr.Recognizer()
    # Use 1 second of silence as test data
    silence = np.zeros(SAMPLE_RATE, dtype=np.int16)
    audio_data = sr.AudioData(silence.tobytes(), SAMPLE_RATE, 2)
    text = recognizer.recognize_google(audio_data, language="en-IN")
    print(f"Recognized: {text}")
except sr.UnknownValueError:
    print("Step 6 OK: Google returned UnknownValueError (silence, expected)")
except sr.RequestError as e:
    print(f"FAILED at RequestError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"FAILED at recognize_google: {e}")
    traceback.print_exc()
