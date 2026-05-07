import sounddevice as sd
import numpy as np
import wave
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from config.settings import BASE_DIR, GROQ_API_KEY

SAMPLE_RATE    = 16000
SILENCE_THRESH = 0.015
SILENCE_SECS   = 2.0
TEMP_WAV       = str(BASE_DIR / "temp_audio.wav")

HINGLISH_PROMPT = "haan yaar, main theek hoon. kya haal hai? achha suno na, YouTube pe gaana chala do. Lisa baby, kaisi ho tum? bhai dekho, kya kar rahe ho. theek hai jaan, chal karte hain."


def _record_audio(max_seconds=30):
    print("  [Listening...] Bolo na jaan...")
    chunks, silence_count = [], 0
    chunk_size = int(SAMPLE_RATE * 0.1)
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        for _ in range(int(max_seconds * 10)):
            chunk, _ = stream.read(chunk_size)
            chunks.append(chunk.copy())
            volume = float(np.sqrt(np.mean(chunk ** 2)))
            silence_count = silence_count + 1 if volume < SILENCE_THRESH else 0
            if silence_count >= int(SILENCE_SECS * 10):
                break
    return np.concatenate(chunks, axis=0).flatten()


def _save_wav(audio):
    audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(TEMP_WAV, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


def listen_once(max_seconds=30):
    try:
        audio = _record_audio(max_seconds)
        if len(audio) < SAMPLE_RATE * 0.5:
            return ""
        print("  [STT] Processing...")
        _save_wav(audio)
        if not os.path.exists(TEMP_WAV):
            return ""
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        with open(TEMP_WAV, "rb") as f:
            result = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3-turbo",
                prompt=HINGLISH_PROMPT,
                response_format="text",
                temperature=0.0
            )
        text = result.strip() if isinstance(result, str) else result.text.strip()
        if text:
            print(f"  [Heard] {text}")
        return text
    except KeyboardInterrupt:
        return "quit"
    except Exception as e:
        print(f"  [STT] Error: {e}")
        return ""
