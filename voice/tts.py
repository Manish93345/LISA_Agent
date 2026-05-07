"""
LISA — Text to Speech (gTTS + pygame)
"""

import re
import os
import warnings
import logging
from gtts import gTTS
from pathlib import Path
from config.settings import BASE_DIR, TTS_LANG, TTS_RATE

# Pygame warnings suppress karo
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger('gtts').setLevel(logging.ERROR)

import pygame

TEMP_MP3  = str(BASE_DIR / "temp_tts.mp3")
_initialized = False


def _init_pygame():
    global _initialized
    if not _initialized:
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.mixer.init()
        _initialized = True


def _clean_text(text: str) -> str:
    # Emojis aur Devanagari remove — gTTS ke liye Roman only
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)   # emojis
    text = re.sub(r'[\u0900-\u097F]', '', text)            # Devanagari
    text = re.sub(r'[^\w\s\,\.\!\?\-\'\"]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def speak(text: str) -> None:
    if not text or not text.strip():
        return

    text_clean = _clean_text(text)
    if not text_clean:
        return

    try:
        _init_pygame()

        # Stop agar kuch chal raha ho
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

        tts = gTTS(text=text_clean, lang=TTS_LANG, slow=False)
        tts.save(TEMP_MP3)

        pygame.mixer.music.load(TEMP_MP3)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

    except Exception as e:
        print(f"  [TTS] Error: {e}")