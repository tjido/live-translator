# 🎧 Live French-to-English Audio Translator

This tool listens to spoken French from Zoom, YouTube, or any macOS audio output and provides real-time English translations using:

- 🎙️ Google Cloud Speech-to-Text  
- 🤖 Vertex AI Gemini 2.5 Flash  
- 🎛️ BlackHole 2ch (virtual audio routing for macOS)

It runs locally and privately on your Mac. Nothing is recorded or stored unless you do so.

---

## ✅ Step-by-Step Setup (All In One)

### 1. Install Python 3.9+

- Open Terminal and run:
  ```bash
  xcode-select --install
  ```
- Or download Python manually from:  
  https://www.python.org/downloads/mac-osx/

---

### 2. Install BlackHole 2ch for audio routing

- Download BlackHole 2ch:  
  https://github.com/ExistentialAudio/BlackHole

- Follow their install instructions.

- Open **Audio MIDI Setup** (search via Spotlight).

- Click ➕ and select **Create Multi-Output Device**.

- Include:
  - ✅ BlackHole 2ch
  - ✅ Your real speakers or headphones

- Go to **System Settings > Sound > Output**, and select your new Multi-Output Device.

---

### 3. Create or open a Google Cloud project

- Go to the console:  
  https://console.cloud.google.com

- Create a new project, or select an existing one.

---

### 4. Enable required APIs

- In the Cloud Console, search for and enable:
  - ✅ **Speech-to-Text API**
  - ✅ **Vertex AI API**

---

### 5. Create a Service Account and download the key

- Go to **IAM & Admin > Service Accounts**
- Click **+ CREATE SERVICE ACCOUNT**
- Name it `audio-translator`
- Grant it the following roles:
  - ✅ Vertex AI User
  - ✅ Cloud Speech-to-Text Admin
- After creation, click into the service account → **Keys** tab → **Add Key > Create new key > JSON**
- This downloads a `.json` file to your machine

---

### 6. Rename and move the credentials file

- Rename the downloaded file to:
  ```bash
  gcp_credentials.json
  ```
- Move it into the project folder:
  ```
  live-translator/
  ├── gcp_credentials.json
  ```

---

### 7. Clone the repo and enter the folder

```bash
git clone https://github.com/tjido/live-translator.git
cd live-translator
```

---

### 8. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 9. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 10. Set your Google credentials

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/gcp_credentials.json"
```

You must run this command **every time you restart Terminal** (unless you add it to `.bashrc` or `.zshrc`).

---

### 11. Start the translator

```bash
./run_translator.sh
```

---

## 🧠 How It Works

1. Captures all sound playing on your Mac (via BlackHole)
2. Sends live French audio to Google's Speech-to-Text API
3. Every 15 seconds, sends transcribed French to Gemini
4. Gemini replies with one clear English translation
5. All output is printed live in your Terminal

---

## ⚙️ Technical Details

- **Audio Device:** BlackHole 2ch (input routed via macOS Multi-Output Device)
- **Speech Model:** `latest_long` (fr-FR) via Google Cloud
- **Translation Model:** `gemini-2.5-flash-preview-05-20` via Vertex AI

**Translation Prompt:**
> Translate this French text to English concisely. Provide one coherent translation.

---

## 📁 Project Structure

```bash
live-translator/
├── gcp_credentials.json       # Your GCP service account key (keep private!)
├── live_translator_google.py  # Main translator script
├── requirements.txt           # Required Python packages
├── run_translator.sh          # Easy launcher script
└── README.md                  # This file
```

---

## 🔐 Security Notes

- Never commit `gcp_credentials.json` to GitHub.
- A `.gitignore` is already set up to protect it.
- Treat your API key like a password — it gives full access to your billing.
- This project only uses paid APIs when it is running.

---

## ✅ What You'll See

- 💬 French text printed every few seconds (transcribed)
- 🌐 English translations every 15 seconds (from Gemini)
- All updates stream live in your Terminal window

---

## 🆘 Troubleshooting Tips

- If you see `GOOGLE_APPLICATION_CREDENTIALS not set`, run:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="$PWD/gcp_credentials.json"
  ```
- If audio doesn’t register, make sure BlackHole is selected in your system output.
- For any dependency errors, run:
  ```bash
  pip install -r requirements.txt
  ```
- You can always rerun:
  ```bash
  ./run_translator.sh
  ```

---

🧑‍💻 Built by [@tjido](https://github.com/tjido) – contributions welcome!
