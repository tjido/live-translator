import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import threading
import queue
import time
import io

# Google Cloud imports
from google.cloud import speech
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel

# --- Configuration ---
GCP_PROJECT_ID = "project-translate-83538"
GCP_LOCATION = "us-central1"
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"

# Audio recording settings
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_DURATION = 5.0  # Collect 5 seconds of audio before processing
INPUT_DEVICE_NAME_PART = "BlackHole 2ch"

# Translation settings
TRANSLATION_INTERVAL_SECONDS = 15  # Translate every 15 seconds
MIN_CHARS_FOR_TRANSLATION = 100

# --- Global Variables ---
audio_buffer = []
audio_buffer_lock = threading.Lock()
stop_event = threading.Event()
french_text_buffer = ""
french_text_lock = threading.Lock()

def find_input_device_id(device_name_part):
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device_name_part.lower() in device['name'].lower() and device['max_input_channels'] > 0:
            print(f"Found input device: {device['name']} with ID: {i}")
            return i
    print(f"Warning: Could not find input device containing '{device_name_part}'. Using default.")
    return None

def audio_callback(indata, frames, time, status):
    """Callback function for continuous audio recording"""
    if status:
        print(f"Audio callback status: {status}")
    
    with audio_buffer_lock:
        audio_buffer.extend(indata[:, 0])  # Take first channel only

def audio_processor():
    """Process accumulated audio buffer periodically"""
    print("Starting audio processor...")
    speech_client = speech.SpeechClient()
    
    while not stop_event.is_set():
        time.sleep(BUFFER_DURATION)  # Wait for buffer to fill
        
        with audio_buffer_lock:
            if len(audio_buffer) < SAMPLE_RATE * 2:  # Skip if less than 2 seconds
                continue
            
            # Copy and clear buffer
            audio_data = np.array(audio_buffer, dtype=np.float32)
            audio_buffer.clear()
        
        try:
            # Convert to int16 and create WAV
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wav_io = io.BytesIO()
            sf.write(wav_io, audio_int16, SAMPLE_RATE, format='WAV', subtype='PCM_16')
            wav_io.seek(0)
            content = wav_io.read()

            # Speech-to-Text
            audio_input = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SAMPLE_RATE,
                language_code="fr-FR",
                enable_automatic_punctuation=True,
                model="latest_long"  # Better for longer audio
            )

            response = speech_client.recognize(config=config, audio=audio_input)
            
            french_chunk = ""
            for result in response.results:
                french_chunk += result.alternatives[0].transcript + " "
            
            french_chunk = french_chunk.strip()
            if french_chunk:
                print(f"French: {french_chunk}")
                
                with french_text_lock:
                    global french_text_buffer
                    french_text_buffer += french_chunk + " "

        except Exception as e:
            print(f"Error in audio processing: {e}")

def translator():
    """Handle translation of accumulated French text"""
    print("Starting translator...")
    
    try:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
        model = GenerativeModel(GEMINI_MODEL_NAME)
        print("Vertex AI initialized successfully.")
    except Exception as e:
        print(f"Error initializing Vertex AI: {e}")
        return

    last_translation_time = time.time()
    
    while not stop_event.is_set():
        time.sleep(2)  # Check every 2 seconds
        
        current_time = time.time()
        
        with french_text_lock:
            global french_text_buffer
            text_to_translate = french_text_buffer.strip()
            
            # Translate if enough text and time has passed
            should_translate = (
                len(text_to_translate) >= MIN_CHARS_FOR_TRANSLATION and
                (current_time - last_translation_time) >= TRANSLATION_INTERVAL_SECONDS
            )
            
            if should_translate or (stop_event.is_set() and text_to_translate):
                if text_to_translate:
                    print(f"\n--- Translating ({len(text_to_translate)} chars) ---")
                    
                    try:
                        prompt = (f"Translate this French text to English concisely. "
                                f"Provide one coherent translation:\n\n{text_to_translate}")
                        
                        response = model.generate_content(prompt)
                        if response.candidates and response.candidates[0].content.parts:
                            english_text = response.candidates[0].content.parts[0].text.strip()
                            print(f"English: {english_text}")
                            print("-" * 50)
                        
                        french_text_buffer = ""  # Clear buffer
                        last_translation_time = current_time
                        
                    except Exception as e:
                        print(f"Translation error: {e}")

def main():
    # Configuration checks
    if not GCP_PROJECT_ID or GCP_PROJECT_ID == "project-translate-83538":
        print("Warning: Using default project ID")
    
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("Error: GOOGLE_APPLICATION_CREDENTIALS not set")
        return

    print(f"Configuration: BufferDuration={BUFFER_DURATION}s, TranslationInterval={TRANSLATION_INTERVAL_SECONDS}s")

    device_id = find_input_device_id(INPUT_DEVICE_NAME_PART)
    
    # Start threads
    processor_thread = threading.Thread(target=audio_processor)
    translator_thread = threading.Thread(target=translator)
    
    processor_thread.start()
    translator_thread.start()
    
    try:
        # Start continuous audio recording
        print(f"Starting continuous audio recording from device {device_id}...")
        with sd.InputStream(samplerate=SAMPLE_RATE,
                          channels=CHANNELS,
                          device=device_id,
                          callback=audio_callback):
            print("Recording... Press Ctrl+C to stop.")
            while not stop_event.is_set():
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        stop_event.set()
        processor_thread.join(timeout=10)
        translator_thread.join(timeout=10)
        print("Stopped.")

if __name__ == "__main__":
    main()