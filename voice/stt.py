"""
LISA — Speech to Text (Whisper)
"""

import whisper
import sounddevice as sd
import numpy as np
import wave
import os
from config.settings import WHISPER_MODEL_SIZE, BASE_DIR

# Fixed paths — project folder mein
TEMP_WAV = str(BASE_DIR / "temp_audio.wav")

print(f"  [STT] Whisper '{WHISPER_MODEL_SIZE}' load ho rha hai...")
_model = whisper.load_model(WHISPER_MODEL_SIZE)
print(f"  [STT] Ready!")

SAMPLE_RATE    = 16000
SILENCE_THRESH = 0.015
SILENCE_SECS   = 2.0


def _record_audio(max_seconds: int = 30) -> np.ndarray:
    print("  [Listening...] Bolo na jaan...")
    chunks        = []
    silence_count = 0
    chunk_size    = int(SAMPLE_RATE * 0.1)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        for _ in range(int(max_seconds * 10)):
            chunk, _ = stream.read(chunk_size)
            chunks.append(chunk.copy())
            volume = float(np.sqrt(np.mean(chunk ** 2)))
            silence_count = silence_count + 1 if volume < SILENCE_THRESH else 0
            if silence_count >= int(SILENCE_SECS * 10):
                break

    return np.concatenate(chunks, axis=0).flatten()


def _save_wav(audio: np.ndarray):
    audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(TEMP_WAV, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())


def listen_once(max_seconds: int = 30) -> str:
    try:
        audio = _record_audio(max_seconds)
        if len(audio) < SAMPLE_RATE * 0.5:
            return ""

        print("  [STT] Processing...")
        _save_wav(audio)

        if not os.path.exists(TEMP_WAV):
            print(f"  [STT] WAV file nahi bana: {TEMP_WAV}")
            return ""

        result = _model.transcribe(TEMP_WAV, language=None, fp16=False)
        text   = result["text"].strip()
        if text:
            print(f"  [Heard] {text}")
        return text

    except KeyboardInterrupt:
        return "quit"
    except Exception as e:
        print(f"  [STT] Error: {e}")
        return ""