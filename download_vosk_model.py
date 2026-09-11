"""
Downloads the Vosk small English model (~40MB) if not already present.
Run this once before using push-to-talk.
"""
import os
import urllib.request
import zipfile

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_ZIP = "vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "vosk-model-small-en-us-0.15"

if os.path.exists(MODEL_DIR):
    print(f"Model already exists at: {MODEL_DIR}")
else:
    print(f"Downloading Vosk model (~40MB)... please wait")
    urllib.request.urlretrieve(MODEL_URL, MODEL_ZIP)
    print("Extracting...")
    with zipfile.ZipFile(MODEL_ZIP, 'r') as z:
        z.extractall(".")
    os.remove(MODEL_ZIP)
    print(f"Model ready at: {MODEL_DIR}")
