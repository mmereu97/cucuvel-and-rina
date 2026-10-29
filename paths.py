"""Unde stau fișierele aplicației.

Codul și resursele (personaje, fundaluri, curriculum) sunt în acest folder.
Tot ce ține de familie stă separat, în Data/, care NU urcă pe GitHub:

    <rădăcină>/
    ├── Project/   codul + resursele (GitHub)
    └── Data/      family.json, voice_profiles/, conversation_logs/, config.json,
                   .env, models/ (modelul de recunoaștere vocală), temp/

Rulat ca .exe (PyInstaller), Data/ se creează lângă executabil.
Variabila de mediu TEATRU_DATA_DIR mută Data/ oriunde.
"""
import os
import sys

FROZEN = getattr(sys, "frozen", False)

# Resursele: lângă cod, sau în arhiva despachetată de PyInstaller
CODE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
INSTALL_DIR = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(CODE_DIR)

DATA_DIR = os.environ.get("TEATRU_DATA_DIR") or os.path.join(INSTALL_DIR, "Data")

ENV_FILE = os.path.join(DATA_DIR, ".env")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
FAMILY_FILE = os.path.join(DATA_DIR, "family.json")
VOICE_PROFILES_DIR = os.path.join(DATA_DIR, "voice_profiles")
CONVERSATION_LOGS_DIR = os.path.join(DATA_DIR, "conversation_logs")
MODELS_DIR = os.path.join(DATA_DIR, "models")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

for _d in (DATA_DIR, VOICE_PROFILES_DIR, CONVERSATION_LOGS_DIR, MODELS_DIR, TEMP_DIR):
    os.makedirs(_d, exist_ok=True)


def resource_path(relative_path: str) -> str:
    """Resursă livrată cu aplicația (assets/, characters/, curriculum/ …)."""
    return os.path.join(CODE_DIR, relative_path)
