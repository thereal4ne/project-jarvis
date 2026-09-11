<div align="center">
  
# 🌐 Jarvis: Hybrid Edge-Cloud AI Assistant

**A context-aware, voice-activated desktop assistant featuring zero-latency deterministic routing, privacy-first offline wake-word detection, and deep Windows OS integration.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-0078d7.svg)]()
[![Gemini API](https://img.shields.io/badge/AI-Google_Gemini-FFA700.svg)]()

</div>

---

## 🚀 Overview

Most AI wrappers blindly forward all user input to a cloud LLM, resulting in high latency, unnecessary API costs, and privacy concerns. 

This project solves that by implementing a **Dual-Layer Intent Router**. It processes strict, deterministic commands (like media controls or hardware queries) instantly on your local machine using RegEx and OS APIs. Only complex, ambiguous, or conversational queries are routed to the cloud AI (Google Gemini 2.0 Flash) for semantic reasoning.

## ✨ Core Features

* 🎙️ **Privacy-First Edge Audio:** Uses `openWakeWord` (ONNX) and `Vosk` (Kaldi) for 100% offline, continuous wake-word detection and Speech-to-Text (STT). Audio is never streamed to the cloud without an explicit wake trigger.
* ⚡ **Hybrid Routing Engine:** System commands execute in <10ms locally. The LLM is injected with local Python functions as actionable tools only when necessary.
* 💻 **Deep OS Integration:** Hooks directly into Windows APIs using `pycaw`, `psutil`, and `ctypes` for hardware-level volume control, process tree management, and system telemetry.
* 🛡️ **Security Guardrails:** Destructive OS commands (e.g., terminating processes, shutting down) are isolated behind a local `PENDING_ACTION` state machine requiring two-factor authorization or passphrase confirmation.
* 🎨 **Cinematic UI:** Features a multi-threaded, pure-Python (`tkinter`) 3D boot animation, particle networks, and a dynamic floating HUD orb that reflects system states (Passive, Listening, Thinking).

---

## 🧠 Technical Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Brain / LLM** | Google Gemini 2.0 Flash | Semantic reasoning and dynamic tool-calling |
| **Wake Word** | openWakeWord | Ultra-low CPU (<2%) continuous edge listening |
| **Speech-to-Text**| Vosk | Fast, offline transcription with VAD endpointing |
| **Text-to-Speech**| Edge-TTS & pyttsx3 | Neural voice generation + local TTS caching |
| **OS Control** | pycaw, psutil, ctypes | Hardware telemetry, media, and process control |
| **UI** | tkinter, Pillow, pystray | 3D Graphics, HUD, and system tray daemon |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
* Python 3.10 or higher
* A Windows environment
* A free [Google Gemini API Key](https://aistudio.google.com/)

### 2. Clone and Install
```bash
git clone https://github.com/thereal4ne/project-jarvis
cd project-jarvis
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your API keys. This file is Git-ignored for security.
```env
GEMINI_API_KEY=your_api_key_here
JARVIS_PASSPHRASE=your_optional_security_passphrase
```

### 4. Configuration
You can tune the assistant's behavior, voice shortcuts, and UI settings in the safe-to-commit `jarvis.ini` file.

### 5. Run
```bash
python jarvis.py
```

---

## 🗣️ Usage

Once the boot animation completes, the assistant enters Passive Mode. 

1. Say **"Hey Jarvis"**.
2. Wait for the audio chime and the HUD to turn bright cyan.
3. Speak your command naturally (e.g., *"What's my current RAM usage?"* or *"Open Spotify and set the volume to 30%."*)
4. The system automatically detects when you stop speaking, processes the request, and returns to Passive Mode.

You can also bypass the wake word entirely by typing commands directly into the terminal.

---

## 📝 License
This project is licensed under the MIT License.
