"""
LISA — Text to Speech (gTTS - Google)
=======================================
Google ka TTS engine — Hinglish naturally handle karta hai.
Free, unlimited, no API key.
Sirf internet chahiye.

Settings mein change karo:
  TTS_LANG = "hi"   → Hindi dominant
  TTS_LANG = "en"   → English dominant  
  TTS_LANG = "hi"   → Hinglish ke liye "hi" best hai
"""

import re
import os
import subprocess
from pathlib import Path
from gtts import gTTS
from config.settings import BASE_DIR, TTS_LANG, TTS_RATE, FFPLAY_PATH

TEMP_MP3 = str(BASE_DIR / "temp_tts.mp3")


def _clean_text(text: str) -> str:
    """Emojis remove karo, text clean karo."""
    text = re.sub(r'[^\w\s\,\.\!\?\-\'\"\।]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def speak(text: str) -> None:
    if not text or not text.strip():
        return

    text_clean = _clean_text(text)
    if not text_clean:
        return

    try:
        # Generate audio
        tts = gTTS(text=text_clean, lang=TTS_LANG, slow=False)
        tts.save(TEMP_MP3)

        if not os.path.exists(TEMP_MP3):
            print("  [TTS] File nahi bani")
            return

        # Play using pygame (no window, clean playback)
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(TEMP_MP3)
        pygame.mixer.music.play()

        # Wait for finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

    except Exception as e:
        print(f"  [TTS] pygame error: {e}, trying ffplay...")
        _ffplay_fallback()


def _ffplay_fallback():
    """Agar pygame nahi chala toh ffplay try karo."""
    try:
        if os.path.exists(TEMP_MP3):
            subprocess.run(
                [FFPLAY_PATH, "-nodisp", "-autoexit", "-loglevel", "quiet", TEMP_MP3],
                capture_output=True
            )
    except Exception as e:
        print(f"  [TTS] Fallback bhi fail: {e}")