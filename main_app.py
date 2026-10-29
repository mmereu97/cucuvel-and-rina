# main_app.py

import sys
import os
import paths   # Data/ (date personale) în afara codului
os.chdir(paths.CODE_DIR)   # resursele (assets/, characters/, curriculum/) au căi relative
import time
import json
import math
import random
import re
import queue
import threading

# =================================================================================
# SISTEM CONFIGURABIL DE LOGGING
# =================================================================================

LOG_CONFIG = {
    # --- Setări de Performanță și Debug General ---
    "app": True,           # 🚀 Mesaje generale despre ciclul de viață al aplicației (pornire, oprire, schimbări de stare majore).
    "config": True,        # ⚙️ Încărcarea și salvarea fișierelor de configurare (config.json, family.json).
    "cleanup": True,       # 🧹 Operațiuni de curățare a thread-urilor și fișierelor temporare.
    
    # --- Setări pentru Componentele Audio/Vizuale ---
    "audio": False,        # 📊 Niveluri audio periodice de la microfon (foarte zgomotos, util pentru calibrare).
    "vad": True,          # 🎤 Detalii de la Silero VAD (începuturi/sfârșituri de vorbire).
    "process": True,       # 🎵 Procesarea segmentelor audio captate (durată, salvare fișier temporar).
    "transcription": True, # 🗣️ Interacțiunea cu API-ul de Speech-to-Text și rezultatele transcrierii.
    "voice": True,         # 👤 Log-uri specifice pentru înregistrarea și identificarea profilului vocal (SpeechBrain).
    "tts": True,           # 🔊 Ciclul de viață al generării audio (Text-to-Speech).
    "tts_debug": False,    # 🔍 Debug detaliat pas-cu-pas pentru TTS (FOARTE vorbăreț - doar pentru depanare!)
    "filler": False,        # 💭 Redarea sunetelor de umplutură ("hmm", "ăăă").
    "echo": True,         # 🔁 Verificări de similaritate pentru detecția ecoului.
    "mute": True,          # 🔇 Pauzarea și reluarea ascultării microfonului.
    "webcam": False,       # 📷 Mesaje periodice de la worker-ul camerei web.

    # --- Setări pentru Logica AI și Interacțiune ---
    "gemini_debug": True, # 🔬 Detalii complete despre request-urile și răspunsurile de la Gemini (util pentru depanare prompt-uri).
    "intent": True,        # 🤖 Rezultatul clasificării intenției utilizatorului.
    "router": True,        # 🚦 Logica de rutare a input-ului utilizatorului (ce acțiune se decide).
    "memory": True,        # 🧠 Log-uri legate de memoria pe termen scurt (ex: pe cine a salutat deja).

    # --- Setări pentru Scenă și Personaje ---
    "scene": True,         # 🌆 Schimbări de scenă și încărcarea fundalurilor.
    "character": True,     # 🎭 Adăugarea, eliminarea și mișcarea personajelor pe scenă.
    "animator": False,      # 👀 Log-uri de la animatoare (clipit, respirație) - extrem de zgomotos!
    "emotion": False,      # 😍 Aplicarea stărilor emoționale.
    "sync": True,         # 🎬 Detalii despre sincronizarea audio-vizuală (vizeme).
    
    # --- Setări Speciale de Debugging Avansat (de obicei False) ---
    "ui_debug": False,     # 📐 Log-uri detaliate despre calculul dimensiunilor, scalare DPI, poziții UI.
    "path_debug": True,   # 📂 Afișarea căilor de sistem la pornire.
    "gaze": False,         # 👀 Calculul și aplicarea direcției privirii.
    "semafor": False,      # 🚦 Actualizări de stare ale semaforului vizual.
    "curriculum": False,   # 📚 Detalii despre încărcarea fiecărui tier și întrebare din curriculum.
}


# Funcție wrapper pentru logging controlat
START_TIME = time.time()

# =================================================================================
# ⭐ ENVIRONMENT VARIABLES PENTRU HIGH DPI (ÎNAINTE DE ORICE IMPORT Qt!)
# =================================================================================
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1" 
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"


# =============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# MONKEY PATCH v5 (FINAL, CORECT) PENTRU SPEECH_RECOGNITION
# =============================================================================
import speech_recognition as sr
import soundfile as sf
import numpy as np
import io

# ▼▼▼ MODIFICARE CRITICĂ AICI ▼▼▼
# Adăugăm **kwargs pentru a accepta orice argumente suplimentare (precum 'convert_rate')
def get_flac_data_in_memory(self, **kwargs):
# ▲▲▲ MODIFICARE CRITICĂ AICI ▲▲▲
    """
    Suprascrie funcționalitatea originală pentru a converti WAV în FLAC
    în memorie, folosind soundfile și numpy, fără a apela un subproces.
    Aceasta elimină complet eroarea [WinError 50].
    """
    # Convertim datele audio brute (bytes) într-un array numpy
    audio_data = np.frombuffer(self.frame_data, dtype=np.int16)

    # Creăm un buffer (fișier virtual) în memorie
    in_memory_file = io.BytesIO()

    # Scriem datele numpy în bufferul virtual, în format FLAC
    sf.write(in_memory_file, audio_data, self.sample_rate, format='FLAC')

    # Mutăm cursorul la începutul bufferului
    in_memory_file.seek(0)

    # Citim conținutul FLAC (bytes) din buffer
    return in_memory_file.read()

# Înlocuim metoda originală, problematică, cu versiunea noastră sigură
sr.AudioData.get_flac_data = get_flac_data_in_memory
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# =============================================================================



# --- COD DE DEBUGGING PENTRU CALEA PROIECTULUI ---
if LOG_CONFIG.get("path_debug", False):
    print("--- START DEBUGGING PATH ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Directorul scriptului (script_dir): {script_dir}")

    working_dir = os.getcwd()
    print(f"Directorul de lucru (working_dir): {working_dir}")

    print("Căile de sistem ale lui Python (sys.path):")
    for path in sys.path:
        print(f"  - {path}")
    print("--- END DEBUGGING PATH ---")
    print("\n" * 2)


# Aici încep importurile originale...



# --- Importuri PySide6 ---
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTextEdit, QTabWidget, QScrollArea,
                               QSlider, QProgressBar, QGroupBox, QFormLayout, QCheckBox, QComboBox,
                               QListWidget, QListWidgetItem, QSpinBox, QDialog, QMessageBox)
from PySide6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QScreen  # ⭐ Adaugă QScreen
from PySide6.QtCore import QThread, Signal, QObject, QTimer, Qt, QPoint, QRect


import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchaudio.*")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")


# =================================================================================
# ⭐ ACTIVARE ATRIBUTE Qt HIGH DPI (IMEDIAT DUPĂ IMPORTURI Qt!)
# =================================================================================
QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

# --- Importuri Librării Externe ---
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import edge_tts
import pygame
import speech_recognition as sr
import torch
import sounddevice as sd
import collections
import wave
import tempfile
import cv2
import asyncio
import numpy as np
import glob
from pathlib import Path
from datetime import datetime  # Deja există

import torchaudio
from speechbrain.inference.speaker import SpeakerRecognition  # ⭐ SCHIMBAT

from managers.scene_manager import SceneManager
from managers.character_manager import CharacterManager
from characters.animators import ANIMATOR_REGISTRY, BreathingAnimator, BlinkingAnimator, EmotionAnimator




def resource_path(relative_path):
    """ Obține calea absolută către o resursă, funcționează atât în dev cât și pentru PyInstaller """
    import paths
    return paths.resource_path(relative_path)


# ═══════════════════════════════════════════════════════════════════════════════
# VOICE PRINT MANAGER - SPEAKER RECOGNITION
# ═══════════════════════════════════════════════════════════════════════════════

class VoicePrintManager:
    """Gestionează înregistrarea și recunoașterea vocilor familiei."""
    
    def __init__(self):
        self.voice_profiles_folder = Path(paths.VOICE_PROFILES_DIR)   # în ../Data
        self.voice_profiles_folder.mkdir(exist_ok=True)
        self.model = None
        log_timestamp("🎤 [VOICE PRINT] Manager inițializat", "voice")
    
    def load_model(self):
        """Încarcă modelul SpeechBrain (descarcă automat la prima rulare)."""
        if self.model is None:
            log_timestamp("📥 [VOICE PRINT] Se încarcă modelul ECAPA-TDNN (metoda finală combinată)...", "voice")
            
            # Importurile necesare
            import shutil
            import huggingface_hub
            from huggingface_hub import hf_hub_download
            from speechbrain.inference.speaker import SpeakerRecognition 

            # Facem backup la funcția originală pentru a o restaura la final
            original_hf_hub_download = huggingface_hub.hf_hub_download
            
            try:
                # ====================================================================
                # PASUL 1: ACTIVĂM MONKEY PATCH-UL ESENȚIAL
                # Acesta va rămâne activ pe parcursul întregului bloc 'try'
                # ====================================================================
                def patched_hf_hub_download(*args, **kwargs):
                    if 'use_auth_token' in kwargs:
                        kwargs['token'] = kwargs.pop('use_auth_token')
                    return original_hf_hub_download(*args, **kwargs)
                
                huggingface_hub.hf_hub_download = patched_hf_hub_download
                log_timestamp("🔧 [VOICE PRINT] Patch 'use_auth_token' aplicat.", "voice")

                # ====================================================================
                # PASUL 2: CURĂȚARE FORȚATĂ ȘI COPIERE MANUALĂ (METODA BULLETPROOF)
                # ====================================================================
                repo_id = "speechbrain/spkrec-ecapa-voxceleb"
                savedir = Path(paths.MODELS_DIR) / "spkrec-ecapa-voxceleb"   # descărcat la prima rulare
                
                if not savedir.exists() or not any(savedir.iterdir()):
                    log_timestamp(f"    -> Folder destinație gol. Se curăță și se populează...", "voice")
                    if savedir.exists():
                        shutil.rmtree(savedir, ignore_errors=True)
                    savedir.mkdir(parents=True, exist_ok=True)

                    filenames = ["hyperparams.yaml", "embedding_model.ckpt", "mean_var_norm_emb.ckpt", "label_encoder.txt"]
                    for filename in filenames:
                        cached_path = hf_hub_download(repo_id=repo_id, filename=filename)
                        shutil.copy(cached_path, savedir / filename)
                    log_timestamp("    -> Toate fișierele au fost copiate manual cu succes.", "voice")
                else:
                    log_timestamp("    -> Folder destinație deja populat. Se sare peste descărcare.", "voice")

                # ====================================================================
                # PASUL 3: INIȚIALIZARE DIN FOLDERUL LOCAL
                # Monkey patch-ul este încă activ pentru apelurile interne ale acestei funcții!
                # ====================================================================
                self.model = SpeakerRecognition.from_hparams(
                    source=str(savedir),
                    run_opts={"device": "cpu"}
                )
                
                log_timestamp("✅ [VOICE PRINT] Model încărcat cu succes prin metoda finală!", "voice")

            except Exception as e:
                log_timestamp(f"❌ [VOICE PRINT] Eroare critică la încărcarea modelului: {e}", "voice")
                import traceback
                log_timestamp(f"Stack trace: {traceback.format_exc()}", "voice")
                raise
            
            finally:
                # Indiferent de rezultat, restaurăm funcția originală pentru a nu afecta alte părți ale programului
                huggingface_hub.hf_hub_download = original_hf_hub_download
                log_timestamp("🔧 [VOICE PRINT] Patch HuggingFace restaurat la starea originală.", "voice")
    
    def extract_embedding(self, audio_path):
        """Extrage embedding-ul vocal din fișier audio."""
        if self.model is None:
            self.load_model()
        
        try:
            # Încarcă audio
            signal, fs = torchaudio.load(audio_path)
            
            # Resample la 16kHz dacă e necesar
            if fs != 16000:
                resampler = torchaudio.transforms.Resample(fs, 16000)
                signal = resampler(signal)
            
            # Extrage embedding
            embedding = self.model.encode_batch(signal)
            return embedding.squeeze().cpu().numpy()
        
        except Exception as e:
            log_timestamp(f"❌ [VOICE PRINT] Eroare extragere embedding: {e}", "voice")
            return None
    
    def save_voice_profile(self, name, audio_path):
        """Salvează profilul vocal al unei persoane."""
        embedding = self.extract_embedding(audio_path)
        if embedding is None:
            return False
        
        profile_path = self.voice_profiles_folder / f"{name}.npy"
        np.save(profile_path, embedding)
        log_timestamp(f"✅ [VOICE PRINT] Profil salvat: {profile_path}", "voice")
        return True
    
    def identify_speaker(self, audio_path, family_data, threshold=0.75):
        """
        Identifică vorbitorul din audio comparând cu profilurile existente.
        
        Returns:
            tuple: (nume_persoana, confidence_score) sau (None, 0) dacă nu recunoaște
        """
        if self.model is None:
            self.load_model()
        
        # Extrage embedding din audio
        test_embedding = self.extract_embedding(audio_path)
        if test_embedding is None:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        # Compară cu toate profilurile
        for member in family_data:
            name = member.get("name")
            voice_profile = member.get("voice_profile", {})
            
            if not voice_profile.get("has_profile", False):
                continue
            
            # Încarcă embedding salvat
            profile_path = self.voice_profiles_folder / f"{name}.npy"
            if not profile_path.exists():
                continue
            
            saved_embedding = np.load(profile_path)
            
            # Calculează similaritate (cosine similarity via speechbrain)
            score = self.model.similarity(
                torch.tensor(test_embedding).unsqueeze(0),
                torch.tensor(saved_embedding).unsqueeze(0)
            ).item()
            
            log_timestamp(f"🔍 [VOICE PRINT] {name}: {score:.2%} similitudine", "voice")
            
            if score > best_score:
                best_score = score
                best_match = name
        
        # Verifică threshold
        if best_score >= threshold:
            log_timestamp(f"✅ [VOICE PRINT] Identificat: {best_match} ({best_score:.2%})", "voice")
            return best_match, best_score
        else:
            log_timestamp(f"⚠️ [VOICE PRINT] Nicio potrivire peste threshold ({threshold:.2%})", "voice")
            return None, 0.0
    
    def delete_voice_profile(self, name):
        """Șterge profilul vocal al unei persoane."""
        profile_path = self.voice_profiles_folder / f"{name}.npy"
        if profile_path.exists():
            profile_path.unlink()
            log_timestamp(f"🗑️ [VOICE PRINT] Profil șters: {name}", "voice")
            return True
        return False
    
    def verify_recording_quality(self, audio_files):
        """
        Verifică calitatea înregistrărilor comparând similaritatea între ele.
        
        Args:
            audio_files: list de căi către fișierele audio (3 fraze)
        
        Returns:
            tuple: (is_valid, scores) - is_valid=True dacă calitatea e OK
        """
        if self.model is None:
            self.load_model()
        
        embeddings = []
        for audio_path in audio_files:
            emb = self.extract_embedding(audio_path)
            if emb is None:
                return False, []
            embeddings.append(torch.tensor(emb).unsqueeze(0))
        
        # Calculează similaritate între toate perechile
        scores = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                score = self.model.similarity(embeddings[i], embeddings[j]).item()
                scores.append(score)
                log_timestamp(f"📊 [QUALITY] Fraza {i+1} vs Fraza {j+1}: {score:.2%}", "voice")
        
        # Calitatea e OK dacă media e peste 0.70
        avg_score = sum(scores) / len(scores)
        is_valid = avg_score >= 0.65
        
        if is_valid:
            log_timestamp(f"✅ [QUALITY] Calitate OK: {avg_score:.2%}", "voice")
        else:
            log_timestamp(f"❌ [QUALITY] Calitate insuficientă: {avg_score:.2%}", "voice")
        
        return is_valid, scores

class VoiceTrainingDialog(QDialog):
    """Dialog pentru înregistrarea celor 3 fraze pentru profil vocal."""
    
    PHRASES = [
        # ⭐ FRAZA NOUĂ, MAI LUNGĂ ȘI MAI NATURALĂ ⭐
        "Aceasta este vocea mea. O folosesc pentru a vorbi clar, astfel încât sistemul să mă poată recunoaște cu ușurință în viitor.",
        
        "Vreau să învăț și să descopăr lucruri noi alături de tine, Cucuvel!",
        "Salut! Numele meu este {name} și îmi place să învăț lucruri noi!"
    ]
    
    def __init__(self, member_name, voice_print_manager, parent=None):
        super().__init__(parent)
        self.member_name = member_name
        self.voice_manager = voice_print_manager
        self.current_phrase_index = 0
        self.recorded_files = []
        self.is_recording = False
        self.stream = None  # ⭐ Inițializare explicită
        
        self.setWindowTitle(f"🎤 Înregistrare Voce - {member_name}")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        self.init_audio()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel(f"Înregistrare Profil Vocal pentru {self.member_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.progress_label = QLabel("Pasul 1 din 3")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)
        
        phrase_group = QGroupBox("📝 Citește această frază:")
        phrase_layout = QVBoxLayout()
        
        self.phrase_label = QLabel()
        self.phrase_label.setWordWrap(True)
        self.phrase_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        phrase_layout.addWidget(self.phrase_label)
        
        phrase_group.setLayout(phrase_layout)
        layout.addWidget(phrase_group)
        
        recording_layout = QHBoxLayout()
        
        self.timer_label = QLabel("⏱️ 0:00 / 0:10")
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        recording_layout.addWidget(self.timer_label)
        
        recording_layout.addStretch()
        
        self.level_bar = QProgressBar()
        self.level_bar.setMaximum(100)
        self.level_bar.setValue(0)
        self.level_bar.setTextVisible(False)
        self.level_bar.setFixedWidth(150)
        recording_layout.addWidget(self.level_bar)
        
        layout.addLayout(recording_layout)
        
        button_layout = QHBoxLayout()
        
        self.record_button = QPushButton("⏺️ Înregistrează")
        self.record_button.setStyleSheet("background-color: #d9534f; color: white; font-size: 14px; padding: 10px;")
        self.record_button.clicked.connect(self.toggle_recording)
        
        self.cancel_button = QPushButton("❌ Anulează")
        self.cancel_button.clicked.connect(self.safe_reject)
        
        button_layout.addWidget(self.record_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.status_label = QLabel("Apasă 'Înregistrează' pentru a începe")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        self.update_phrase()
    
    def init_audio(self):
        """Inițializează sistemul de înregistrare audio."""
        self.sample_rate = 16000
        self.frames = []
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_ui)
        self.start_time = 0
        self.max_duration = 10
    
    def update_phrase(self):
        """Actualizează fraza curentă în UI."""
        phrase = self.PHRASES[self.current_phrase_index].format(name=self.member_name)
        self.phrase_label.setText(phrase)
        self.progress_label.setText(f"Pasul {self.current_phrase_index + 1} din {len(self.PHRASES)}")
    
    def toggle_recording(self):
        """Pornește/Oprește înregistrarea."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Pornește înregistrarea."""
        self.is_recording = True
        self.frames = []
        self.start_time = time.time()
        
        self.record_button.setText("⏹️ Oprește")
        self.record_button.setStyleSheet("background-color: #5cb85c; color: white; font-size: 14px; padding: 10px;")
        self.status_label.setText("🔴 Înregistrare în curs...")
        self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=self.audio_callback
            )
            self.stream.start()
            self.recording_timer.start(100)
            log_timestamp(f"🔴 [VOICE TRAINING] Start înregistrare fraza {self.current_phrase_index + 1}", "voice")
        except Exception as e:
            log_timestamp(f"❌ [VOICE TRAINING] Eroare pornire stream: {e}", "voice")
            self.is_recording = False
            QMessageBox.critical(self, "Eroare", f"Nu pot porni microfonul: {e}")
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback pentru stream audio."""
        if status:
            log_timestamp(f"⚠️ [AUDIO] {status}", "voice")
        
        if self.is_recording:
            self.frames.append(indata.copy())
            
            rms = np.sqrt(np.mean(indata**2))
            db_level = min(max(20 * np.log10(rms + 1e-6) + 90, 0), 100)
            
            # ⭐ Folosim QMetaObject pentru thread safety ⭐
            QTimer.singleShot(0, lambda: self.level_bar.setValue(int(db_level)))
    
    def update_recording_ui(self):
        """Actualizează UI-ul în timpul înregistrării."""
        if not self.is_recording:
            return
            
        elapsed = time.time() - self.start_time
        
        self.timer_label.setText(f"⏱️ {int(elapsed)}:{int((elapsed % 1) * 100):02d} / 0:10")
        
        if elapsed >= self.max_duration:
            self.stop_recording()
    
    def stop_recording(self):
        """Oprește înregistrarea și salvează. ⭐ VERSIUNE STABILĂ ⭐"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.recording_timer.stop()
        
        # ⭐ PROTECȚIE CRITICĂ ⭐
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None
        except Exception as e:
            log_timestamp(f"⚠️ [VOICE TRAINING] Eroare închidere stream: {e}", "voice")
        
        self.record_button.setText("⏺️ Înregistrează")
        self.record_button.setStyleSheet("background-color: #d9534f; color: white; font-size: 14px; padding: 10px;")
        self.status_label.setText("✅ Înregistrare salvată!")
        self.status_label.setStyleSheet("color: #5cb85c; font-weight: bold;")
        
        # Salvează audio
        if len(self.frames) == 0:
            log_timestamp("⚠️ [VOICE TRAINING] Niciun frame captat!", "voice")
            QMessageBox.warning(self, "Atenție", "Nu s-a captat niciun sunet. Încearcă din nou.")
            return
        
        try:
            audio_data = np.concatenate(self.frames, axis=0)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            self.recorded_files.append(temp_file.name)
            log_timestamp(f"✅ [VOICE TRAINING] Fraza {self.current_phrase_index + 1} salvată: {temp_file.name}", "voice")
            
            QTimer.singleShot(1000, self.next_phrase)
            
        except Exception as e:
            log_timestamp(f"❌ [VOICE TRAINING] Eroare salvare: {e}", "voice")
            QMessageBox.critical(self, "Eroare", f"Eroare salvare: {e}")
    
    def next_phrase(self):
        """Trece la următoarea frază sau finalizează."""
        self.current_phrase_index += 1
        
        if self.current_phrase_index < len(self.PHRASES):
            self.update_phrase()
            self.status_label.setText("Apasă 'Înregistrează' pentru următoarea frază")
            self.status_label.setStyleSheet("color: #666; font-style: italic;")
            self.timer_label.setText("⏱️ 0:00 / 0:10")
            self.level_bar.setValue(0)
        else:
            self.finalize_training()
    
    def finalize_training(self):
        """Verifică calitatea și salvează profilul."""
        self.status_label.setText("🔄 Procesez înregistrările...")
        self.record_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        QApplication.processEvents()
        
        try:
            is_valid, scores = self.voice_manager.verify_recording_quality(self.recorded_files)
            
            if not is_valid:
                reply = QMessageBox.warning(
                    self,
                    "❌ Calitate insuficientă",
                    "Înregistrările nu sunt suficient de consistente.\n\n"
                    "Te rog re-înregistrează frazele.\n\n"
                    f"Scor calitate: {sum(scores)/len(scores):.1%} (necesar: >70%)",
                    QMessageBox.Retry | QMessageBox.Ignore
                )
                
                if reply == QMessageBox.Retry:
                    self.cleanup_temp_files()
                    self.recorded_files = []
                    self.current_phrase_index = 0
                    self.update_phrase()
                    self.record_button.setEnabled(True)
                    self.cancel_button.setEnabled(True)
                    self.status_label.setText("Apasă 'Înregistrează' pentru a reîncepe")
                    self.status_label.setStyleSheet("color: #666; font-style: italic;")
                    return
            
            success = self.voice_manager.save_voice_profile(self.member_name, self.recorded_files[0])
            
            self.cleanup_temp_files()
            
            if success:
                QMessageBox.information(self, "✅ Succes", f"Profilul vocal pentru {self.member_name} a fost salvat!")
                self.accept()
            else:
                QMessageBox.critical(self, "❌ Eroare", "Eroare la salvare profil.")
                self.reject()
                
        except Exception as e:
            log_timestamp(f"❌ [VOICE TRAINING] Eroare finalizare: {e}", "voice")
            self.cleanup_temp_files()
            QMessageBox.critical(self, "❌ Eroare", f"Eroare: {e}")
            self.reject()
    
    def cleanup_temp_files(self):
        """Șterge fișierele temporare."""
        for f in self.recorded_files:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except:
                pass
    
    def safe_reject(self):
        """Închidere sigură cu cleanup."""
        if self.is_recording:
            self.stop_recording()
        
        self.cleanup_temp_files()
        self.reject()
    
    def closeEvent(self, event):
        """Override pentru cleanup la închidere."""
        if self.is_recording:
            self.stop_recording()
        
        self.cleanup_temp_files()
        event.accept()

class DPIScaler:
    """
    Gestionează scalarea automată pentru diferite DPI-uri și rezoluții.
    
    Versiune îmbunătățită care detectează scaling-ul în mai multe moduri:
    1. Pe baza DPI-ului (metoda standard)
    2. Pe baza dimensiunii ecranului (fallback pentru compatibility mode)
    3. Manual, prin config (override)
    """
    
    def __init__(self, app):
        """
        Args:
            app: Instanța QApplication
        """
        self.app = app
        self.base_dpi = 96  # DPI standard Windows (100%)
        self.detect_scaling()
    
    def detect_scaling(self):
        """Detectează factorul de scalare actual (versiune îmbunătățită)."""
        try:
            # Obține ecranul principal
            primary_screen = self.app.primaryScreen()
            
            if primary_screen:
                # Metodă 1: DPI fizic vs logic
                physical_dpi = primary_screen.physicalDotsPerInch()
                logical_dpi = primary_screen.logicalDotsPerInch()
                dpi_scale_factor = logical_dpi / self.base_dpi
                
                # Metodă 2: Dimensiune fizică vs logică (mai robustă!)
                screen_geometry = primary_screen.geometry()
                physical_width = screen_geometry.width()
                physical_height = screen_geometry.height()
                
                available_geometry = primary_screen.availableGeometry()
                logical_width = available_geometry.width()
                logical_height = available_geometry.height()
                
                width_scale = physical_width / logical_width if logical_width > 0 else 1.0
                height_scale = physical_height / logical_height if logical_height > 0 else 1.0
                dimension_scale_factor = (width_scale + height_scale) / 2
                
                # Metodă 3: Device pixel ratio (alternativă Qt)
                device_pixel_ratio = primary_screen.devicePixelRatio()
                
                # Înlocuirea blocului de print() cu log_timestamp()
                log_timestamp("="*60, "ui_debug")
                log_timestamp("🖥️  DETECȚIE DPI ȘI SCALARE", "ui_debug")
                log_timestamp("="*60, "ui_debug")
                log_timestamp(f"  📊 METODA 1 (DPI):", "ui_debug")
                log_timestamp(f"     - Physical DPI: {physical_dpi:.1f}", "ui_debug")
                log_timestamp(f"     - Logical DPI: {logical_dpi:.1f}", "ui_debug")
                log_timestamp(f"     - Scale Factor (DPI): {dpi_scale_factor:.2f}", "ui_debug")
                log_timestamp(f"  📐 METODA 2 (DIMENSIUNI):", "ui_debug")
                log_timestamp(f"     - Rezoluție Fizică: {physical_width}x{physical_height}", "ui_debug")
                log_timestamp(f"     - Rezoluție Logică: {logical_width}x{logical_height}", "ui_debug")
                log_timestamp(f"     - Scale Factor (Dimensiuni): {dimension_scale_factor:.2f}", "ui_debug")
                log_timestamp(f"  📱 METODA 3 (DEVICE PIXEL RATIO):", "ui_debug")
                log_timestamp(f"     - Device Pixel Ratio: {device_pixel_ratio:.2f}", "ui_debug")
                
                # ⭐ DECIZIE FINALĂ: Folosește metoda cea mai fiabilă
                if abs(dimension_scale_factor - 1.0) > 0.05:
                    self.scale_factor = dimension_scale_factor
                    detection_method = "dimensiuni ecran"
                elif abs(device_pixel_ratio - 1.0) > 0.05:
                    self.scale_factor = device_pixel_ratio
                    detection_method = "device pixel ratio"
                else:
                    self.scale_factor = dpi_scale_factor
                    detection_method = "DPI"
                
                # Rotunjește la valori comune
                common_scales = [1.0, 1.25, 1.5, 1.75, 2.0]
                rounded_scale = min(common_scales, key=lambda x: abs(x - self.scale_factor))
                
                if abs(rounded_scale - self.scale_factor) < 0.05:
                    self.scale_factor = rounded_scale
                
                self.screen_width = logical_width
                self.screen_height = logical_height
                
                log_timestamp("-" * 60, "ui_debug")
                log_timestamp(f"  ✅ FACTOR SCALARE FINAL: {self.scale_factor:.2f} ({self.scale_factor*100:.0f}%)", "ui_debug")
                log_timestamp(f"     - Detectat prin: {detection_method}", "ui_debug")
                log_timestamp(f"     - Ecran disponibil: {self.screen_width}x{self.screen_height}", "ui_debug")
                log_timestamp(f"     - Dimensiuni fereastră scalate: {self.scaled(1920)}x{self.scaled(1080)}", "ui_debug")
                log_timestamp("=" * 60, "ui_debug")

            else:
                log_timestamp("⚠️ [DPI] Nu s-a putut detecta ecranul principal, folosesc scale_factor=1.0", "app")
                self.scale_factor = 1.0
                self.screen_width = 1920
                self.screen_height = 1080
                
        except Exception as e:
            log_timestamp(f"❌ [DPI] Eroare la detectarea DPI: {e}", "app")
            import traceback
            log_timestamp(f"  Stack trace: {traceback.format_exc()}", "app")
            self.scale_factor = 1.0
            self.screen_width = 1920
            self.screen_height = 1080
    
    def scaled(self, value):
        """
        Scalează o valoare (dimensiune sau coordonată).
        
        Args:
            value: Valoare originală (int sau float)
        
        Returns:
            Valoare scalată (int)
        """
        return round(value / self.scale_factor)  # ⭐ round() în loc de int()!
    
    def scaled_point(self, x, y):
        """Scalează un punct (coordonată 2D)."""
        return QPoint(self.scaled(x), self.scaled(y))
    
    def scaled_rect(self, x, y, width, height):
        """Scalează un dreptunghi."""
        return QRect(
            self.scaled(x), 
            self.scaled(y), 
            self.scaled(width), 
            self.scaled(height)
        )
    
    def scale_config_positions(self, config_data):
        """
        Scalează pozițiile din config.json (pentru personaje).
        
        Args:
            config_data: Dict cu configurație personaj
        
        Returns:
            Config actualizat cu poziții scalate
        """
        if "scene_configs" in config_data:
            for scene_id, scene_config in config_data["scene_configs"].items():
                if "pos" in scene_config and isinstance(scene_config["pos"], list):
                    original_pos = scene_config["pos"]
                    scaled_pos = [self.scaled(original_pos[0]), self.scaled(original_pos[1])]
                    scene_config["pos"] = scaled_pos
                    # Înlocuirea print() cu log_timestamp() sub categoria "ui_debug"
                    log_timestamp(f"  📍 Poziție scalată [{scene_id}]: {original_pos} -> {scaled_pos}", "ui_debug")
        
        return config_data
    
    def get_optimal_window_size(self):
        """Calculează dimensiunea optimă a ferestrei pentru ecranul curent."""
        base_width = 1920
        base_height = 1080
        
        log_timestamp("="*60, "ui_debug")
        log_timestamp("📐 CALCUL DIMENSIUNE OPTIMĂ FEREASTRĂ", "ui_debug")
        log_timestamp("="*60, "ui_debug")
        log_timestamp(f"  - Dimensiuni de bază: {base_width}x{base_height}", "ui_debug")
        log_timestamp(f"  - Factor de scalare: {self.scale_factor}", "ui_debug")
        log_timestamp(f"  - Ecran disponibil: {self.screen_width}x{self.screen_height}", "ui_debug")
        
        # Calculăm dimensiuni scalate
        target_width = self.scaled(base_width)
        target_height = self.scaled(base_height)
        log_timestamp(f"  - Țintă după scalare: {target_width}x{target_height}", "ui_debug")
        
        # Verificăm dacă depășește ecranul
        exceeds_width = target_width > self.screen_width
        exceeds_height = target_height > self.screen_height
        log_timestamp(f"  - Depășește lățimea? {exceeds_width} ({target_width} > {self.screen_width})", "ui_debug")
        log_timestamp(f"  - Depășește înălțimea? {exceeds_height} ({target_height} > {self.screen_height})", "ui_debug")
        
        if exceeds_width or exceeds_height:
            log_timestamp("  -> ⚠️ Fereastră prea mare, se recalculează...", "ui_debug")
            width_ratio = self.screen_width / target_width
            height_ratio = (self.screen_height - 50) / target_height # Marjă siguranță
            log_timestamp(f"     - Raport lățime: {width_ratio:.3f}", "ui_debug")
            log_timestamp(f"     - Raport înălțime: {height_ratio:.3f}", "ui_debug")
            
            ratio = min(width_ratio, height_ratio)
            log_timestamp(f"     - Se folosește raportul: {ratio:.3f}", "ui_debug")
            
            target_width = int(target_width * ratio * 0.95) # Marjă siguranță
            target_height = int(target_height * ratio * 0.95) # Marjă siguranță
            log_timestamp(f"     - Dimensiuni finale după reducere: {target_width}x{target_height}", "ui_debug")
        
        x = max(0, (self.screen_width - target_width) // 2)
        y = max(0, (self.screen_height - target_height) // 2)
        log_timestamp(f"  - Poziție finală calculată: ({x}, {y})", "ui_debug")
        log_timestamp("="*60, "ui_debug")
        
        return target_width, target_height, x, y


def log_timestamp(message, category="app"):
    """
    Logging cu filtrare pe categorii.
    
    Args:
        message (str): Mesajul de logat
        category (str): Categoria de log (default: "app")
    
    Exemple:
        log_timestamp("Pornire aplicație", "app")
        log_timestamp("Nivel audio: 3200", "audio")
    """
    if LOG_CONFIG.get(category, True):
        elapsed = time.time() - START_TIME
        print(f"[{elapsed:8.3f}s] {message}")


# ⭐ SETĂM CONFIG-UL PENTRU TOATE MODULELE EXTERNE
from characters import animators
from characters import base_character  # <-- Adăugați acest import
from managers import scene_manager, character_manager

animators.set_log_config(LOG_CONFIG)
base_character.set_log_config(LOG_CONFIG) # <-- Adăugați această linie
scene_manager.set_log_config(LOG_CONFIG)
character_manager.set_log_config(LOG_CONFIG)

# =================================================================================
# UTILITARE GLOBALE
# =================================================================================

def cleanup_temp_files():
    """Șterge fișierele temp_speech... orfane din folderul rădăcină."""
    log_timestamp("🧹 [CLEANUP] Se caută fișiere temporare vechi...", "cleanup")
    deleted_count = 0
    current_dir = paths.TEMP_DIR
    
    for filename in os.listdir(current_dir):
        if os.path.isfile(os.path.join(current_dir, filename)) and \
           filename.startswith("temp_speech_") and \
           filename.endswith(".mp3"):
            try:
                os.remove(os.path.join(current_dir, filename))
                log_timestamp(f"  -> Șters: {filename}", "cleanup")
                deleted_count += 1
            except Exception as e:
                log_timestamp(f"  -> ⚠️ Eroare la ștergerea {filename}: {e}", "cleanup")
    
    if deleted_count > 0:
        log_timestamp(f"✅ [CLEANUP] Curățenie finalizată. {deleted_count} fișiere șterse.", "cleanup")
    else:
        log_timestamp("✅ [CLEANUP] Niciun fișier temporar de șters.", "cleanup")

# Păstrăm configurarea API
# =============================================================================
# ▼▼▼ ÎNCĂRCARE INTELIGENTĂ .ENV (PENTRU DEZVOLTARE ȘI EXE) ▼▼▼
# =============================================================================
# Acest bloc asigură că .env este căutat/creat lângă .exe, nu într-un folder temporar.
# Chiar dacă nu e la începutul fișierului, este important să fie înaintea
# codului care folosește cheia API (de ex. genai.configure).

# Importurile necesare pentru acest bloc (pot fi mutate la începutul fișierului dacă dorești)
import sys
import os
from dotenv import load_dotenv

# Determinăm calea de bază a aplicației
if getattr(sys, 'frozen', False):
    # Dacă rulăm ca executabil "înghețat"
    application_path = os.path.dirname(sys.executable)
else:
    # Dacă rulăm ca script normal .py
    application_path = os.path.dirname(os.path.abspath(__file__))

# Construim calea completă către fișierul .env
env_path = paths.ENV_FILE   # cheia stă în ../Data/.env

# Încărcăm variabilele de mediu din calea specificată
load_dotenv(dotenv_path=env_path)

# Verificăm dacă fișierul există după încărcare, pentru a rula logica ta de "prompt"
if not os.path.exists(env_path):
    # Acest log este util pentru debugging, mai ales în versiunea .exe
    log_timestamp(f"⚠️  Fișierul .env nu a fost găsit la calea '{env_path}'. Se va solicita cheia API.", "config")
# ▲▲▲ SFÂRȘIT BLOC ÎNCĂRCARE INTELIGENTĂ ▲▲▲
# =============================================================================

def save_config(config, config_path=None):
    """Salvează configurația în fișier JSON."""
    config_path = config_path or paths.CONFIG_FILE
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        log_timestamp(f"✅ [CONFIG] Configurație salvată în '{config_path}'", "app")
    except Exception as e:
        log_timestamp(f"❌ [CONFIG] Eroare la salvare: {e}", "app")

def load_config(config_path=None):
    """Încarcă configurația din fișier JSON."""
    config_path = config_path or paths.CONFIG_FILE
    default_config = {
        "auto_calibrate_on_mic_start": False,
        "auto_start_mic_with_conversation": True,
        "conversation_without_camera": False,
        "enable_echo_cancellation": True,
        "enable_filler_sounds": False, # <-- ADAUGĂ ACEASTĂ LINIE
        "threshold": 400,
        "margin_percent": 20,
        "ask_pause_between_tiers": True,  # Întreabă copilul dacă vrea pauză între tier-uri
        "pause_duration": 2.0,
        "max_speech_duration": 15, # <-- ADAUGĂ ACEASTĂ LINIE
        "window_geometry": None,  # {"x": 50, "y": 50, "width": 1920, "height": 1080}

        "voice_recognition_threshold": 0.75,  # 75% similitudine minimă
        "ask_pause_between_tiers": False,  # Deja există

        # --- SETĂRI NOI ---
        "subtitle_font_size": 26,
        "rina_language_code": "en",
        "subtitle_mode": "original",
        "ai_model_name": "models/gemini-flash-lite-latest" # <-- ADAUGĂ ACEASTĂ LINIE
    }
    
    try:
        if os.path.exists(resource_path(config_path)):
            with open(resource_path(config_path), 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # Merge cu default pentru câmpuri noi
                default_config.update(loaded_config)
                log_timestamp(f"✅ [CONFIG] Configurație încărcată din '{config_path}'", "app")
        else:
            log_timestamp(f"⚠️ [CONFIG] Fișier config inexistent, se folosește default", "app")
    except Exception as e:
        log_timestamp(f"❌ [CONFIG] Eroare la încărcare: {e}, se folosește default", "app")
    
    return default_config

# =================================================================================
# WORKER-I (QThread) - Portare 1:1
# Aceste clase rămân aproape identice, deoarece logica lor este deja
# bine încapsulată și nu depinde de arhitectura personajelor.
# Le copiem direct din fișierul vechi.
# =================================================================================

# [COPIAȚI ȘI LIPIȚI AICI, FĂRĂ MODIFICĂRI, URMĂTOARELE CLASE DIN main_app_backup.py]:
# =================================================================================
# WORKER-I ASINCRONE
# =================================================================================


class StreamingTTSSignals(QObject):
    """
    Semnale Qt pentru comunicare thread-safe între worker-ii de streaming și UI.
    """
    sentence_audio_ready = Signal(str, float, str)  # ⭐ 3 parametri: (audio_path, duration, sentence_text)
    all_sentences_finished = Signal()
    error_occurred = Signal(str)
    
    # Semnale pentru operații pygame în main thread
    play_audio_file = Signal(str)
    audio_playback_finished = Signal(str)

class StreamingTTSManager:
    """
    Manager pentru TTS cu streaming - arhitectură producător-consumator.
    Sparge textul în propoziții, generează și redă incremental pentru latență minimă.
    """
    
    def __init__(self):
        self.signals = StreamingTTSSignals()
        
        # Cozi pentru comunicare între thread-uri
        self.tts_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        
        # Flag-uri de control
        self.is_generating = False
        self.is_playing = False
        self._stop_requested = False
        
        # Thread-uri worker
        self.generator_thread = None
        self.player_thread = None
        
        # Voce curentă
        self.current_voice = "ro-RO-EmilNeural"
        
        # ⭐ ADAUGĂ ACESTE 2 LINII NOI:
        self._current_playing_file = None
        self._playback_finished_event = None
        
        log_timestamp("🔊 [STREAMING TTS] Manager inițializat", "tts")
    
    def start_speaking(self, text, voice_id):
        """
        Pornește procesul de generare și redare streaming pentru un text.
        
        Args:
            text (str): Textul complet de generat
            voice_id (str): ID-ul vocii Edge TTS (ex: "ro-RO-EmilNeural")
        """
        if self.is_generating:
            log_timestamp("⚠️ [STREAMING TTS] Deja generez audio, opresc procesul anterior", "tts")
            self.stop_all()
            time.sleep(0.3)  # Dăm timp să se curețe
        
        self.current_voice = voice_id
        self._stop_requested = False
        
        log_timestamp(f"🔊 [STREAMING TTS] START - Text: '{text[:60]}...', Voce: {voice_id}", "tts")
        
        # Sparge textul în propoziții
        sentences = self._split_into_sentences(text)
        log_timestamp(f"🔊 [STREAMING TTS] Text spart în {len(sentences)} propoziții", "tts")
        
        # Pune toate propozițiile în coada de generare
        for sentence in sentences:
            self.tts_queue.put(sentence)
        
        # Pune sentinel pentru sfârșitul cozii
        self.tts_queue.put(None)
        
        # Pornește worker-ii
        self._start_generator_worker()
        self._start_player_worker()
    
    def _split_into_sentences(self, text):
        """Sparge textul în propoziții pentru streaming."""
        # Curățăm tag-urile de emoție
        clean_text = re.sub(r'\[EMOTION:\w+\]\s*', '', text)
        
        # Separator simplu pe bază de punctuație
        sentences = []
        current = ""
        
        for char in clean_text:
            current += char
            if char in '.!?':
                if current.strip():
                    sentences.append(current.strip())
                current = ""
        
        # Adaugă ultima bucată dacă nu se termină cu punctuație
        if current.strip():
            sentences.append(current.strip())
        
        return sentences if sentences else [clean_text]
    
    def _start_generator_worker(self):
        """Pornește thread-ul generator (producător)."""
        if self.generator_thread and self.generator_thread.is_alive():
            return
        
        self.is_generating = True
        self.generator_thread = threading.Thread(
            target=self._generator_worker,
            daemon=True,
            name="TTS-Generator"
        )
        self.generator_thread.start()
        log_timestamp("✅ [STREAMING TTS] Generator worker pornit", "tts")
    
    def _start_player_worker(self):
        """Pornește thread-ul player (consumator)."""
        if self.player_thread and self.player_thread.is_alive():
            return
        
        self.is_playing = True
        self.player_thread = threading.Thread(
            target=self._player_worker,
            daemon=True,
            name="TTS-Player"
        )
        self.player_thread.start()
        log_timestamp("✅ [STREAMING TTS] Player worker pornit", "tts")
    
    def _generator_worker(self):
        """
        Worker producător: preia text din tts_queue, generează fișiere audio
        și le pune în audio_queue.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while not self._stop_requested:
                text_chunk = self.tts_queue.get()
                
                if text_chunk is None:  # Sentinel - sfârșitul cozii
                    log_timestamp("🔊 [TTS GEN] Toate propozițiile generate, opresc generator", "tts")
                    break
                
                if text_chunk.strip():
                    log_timestamp(f"🔊 [TTS GEN] Generez: '{text_chunk[:50]}...'", "tts")
                    loop.run_until_complete(self._generate_audio_file(text_chunk))
                
                self.tts_queue.task_done()
        
        except Exception as e:  # ⭐ ACEST EXCEPT TREBUIE SĂ EXISTE!
            log_timestamp(f"❌ [TTS GEN] Eroare în generator: {e}", "tts")
            self.signals.error_occurred.emit(str(e))
        
        finally:  # ⭐ ȘI ACEST FINALLY!
            # Pune sentinel în audio_queue pentru a semnala sfârșitul
            self.audio_queue.put(None)
            self.is_generating = False
            log_timestamp("🔊 [TTS GEN] Generator oprit", "tts")
    
    async def _generate_audio_file(self, text):
        """Generează un fișier audio pentru o propoziție."""
        start_time = time.time()
        output_file = os.path.join(paths.TEMP_DIR, f"temp_speech_{int(time.time()*1000)}_{random.randint(1000,9999)}.mp3")
        
        try:
            communicate = edge_tts.Communicate(text, self.current_voice)
            await communicate.save(output_file)
            
            # Măsoară durata audio
            sound = pygame.mixer.Sound(output_file)
            duration = sound.get_length()
            
            generation_time = time.time() - start_time
            log_timestamp(f"🔊 [TTS GEN] ✅ Fișier generat în {generation_time:.2f}s, durată: {duration:.2f}s", "tts")
            
            # ⭐ Pune fișierul, durata ȘI textul în coada de redare
            self.audio_queue.put((output_file, duration, text))
        
        except Exception as e:
            log_timestamp(f"❌ [TTS GEN] Eroare la generare: {e}", "tts")
            if os.path.exists(output_file):
                os.remove(output_file)
            raise
    
    def _player_worker(self):
        """
        Worker consumator: preia fișiere audio din audio_queue,
        EMITE SEMNALE pentru redare (care va fi făcută în main thread),
        și le șterge după confirmare.
        """
        try:
            while not self._stop_requested:
                item = self.audio_queue.get()
                
                if item is None:  # Sentinel - sfârșitul cozii
                    log_timestamp("🔊 [TTS PLAY] Toate propozițiile redate, emit semnal final", "tts")
                    break
                
                audio_path, duration, sentence_text = item  # ⭐ Acum extragem și textul
                
                log_timestamp(f"▶️  [TTS PLAY] Pregătesc redare: '{audio_path}'", "tts")
                
                # Emite semnal că audio-ul e gata (pentru sincronizare) ȘI textul propoziției
                self.signals.sentence_audio_ready.emit(audio_path, duration, sentence_text)
                
                # ⭐ CRUCIAL: Nu apelăm pygame direct aici!
                # Emitem semnal pentru main thread să redea audio-ul
                self._current_playing_file = audio_path
                self._playback_finished_event = threading.Event()
                
                self.signals.play_audio_file.emit(audio_path)
                
                # Așteptăm confirmarea că redarea s-a terminat
                self._playback_finished_event.wait()
                
                log_timestamp(f"⏹️  [TTS PLAY] Redare confirmată terminată: '{audio_path}'", "tts")
                
                # Curățare fișier
                if os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        log_timestamp(f"🧹 [TTS PLAY] Fișier șters: '{audio_path}'", "cleanup")
                    except Exception as e:
                        log_timestamp(f"⚠️ [TTS PLAY] Eroare la ștergere: {e}", "cleanup")
                
                self.audio_queue.task_done()
        
        except Exception as e:
            log_timestamp(f"❌ [TTS PLAY] Eroare în player: {e}", "tts")
            self.signals.error_occurred.emit(str(e))
        
        finally:
            self.is_playing = False
            # Emite semnal că TOATE propozițiile s-au terminat
            self.signals.all_sentences_finished.emit()
            log_timestamp("🔊 [TTS PLAY] Player oprit", "tts")


    def stop_all(self):
        """Oprește toate procesele de generare și redare."""
        log_timestamp("🛑 [STREAMING TTS] STOP solicitat", "tts")
        self._stop_requested = True
        
        # Oprește redarea
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except:
            pass
        
        # ⭐ ADAUGĂ ACEST BLOC
        # Semnalizează event-ul dacă un worker așteaptă
        if self._playback_finished_event and not self._playback_finished_event.is_set():
            self._playback_finished_event.set()
        # ⭐ SFÂRȘIT BLOC
        
        # Golește cozile
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
            except:
                break
        
        while not self.audio_queue.empty():
            try:
                item = self.audio_queue.get_nowait()
                if item and item is not None:
                    audio_path, _ = item
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
            except:
                break
        
        # Așteaptă ca thread-urile să se oprească
        if self.generator_thread and self.generator_thread.is_alive():
            self.generator_thread.join(timeout=1.0)
        
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=1.0)
        
        self.is_generating = False
        self.is_playing = False
        log_timestamp("✅ [STREAMING TTS] Toate procesele oprite", "tts")



class WebcamWorker(QObject):
    frame_ready = Signal(QImage)
    finished = Signal()
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        self.last_frame = None

    def run(self):
        log_timestamp("📷 [WEBCAM] Worker pornit.", "webcam")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            log_timestamp("📷 [WEBCAM] ❌ Nu se poate deschide camera!", "webcam")
            self._is_running = False
            
        frame_count = 0
        while self._is_running:
            ret, frame = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.last_frame = rgb_image.copy()
                
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.frame_ready.emit(qt_image.copy())
                
                frame_count += 1
                if frame_count % 300 == 0:
                    log_timestamp(f"📷 [WEBCAM] Frame #{frame_count} OK", "webcam")
            time.sleep(0.03)

        cap.release()
        self.finished.emit()
        log_timestamp("📷 [WEBCAM] Worker oprit.", "webcam")

    def stop(self):
        self._is_running = False

class GeminiWorker(QObject):
    response_ready = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()
    
    def __init__(self, system_prompt, image_data, question_text, model_name):
        super().__init__()
        self.system_prompt = system_prompt
        self.image_data = image_data
        self.question_text = question_text
        self.model = genai.GenerativeModel(model_name)

    def run(self):
        log_timestamp("🤖 [GEMINI] Worker pornit.", "gemini_debug")
        try:
            log_timestamp("🤖 [GEMINI] Convertesc frame în PIL Image...", "gemini_debug")
            pil_image = Image.fromarray(self.image_data)
            
            prompt_parts = [
                self.system_prompt,
                pil_image,
                f"Utilizator: {self.question_text}"
            ]
            
            log_timestamp(f"🤖 [GEMINI] Trimit request pentru: '{self.question_text}'", "gemini_debug")
            response = self.model.generate_content(prompt_parts)
            
            if response.text:
                log_timestamp(f"🤖 [GEMINI] ✅ Răspuns: '{response.text[:100]}...'", "gemini_debug")
                self.response_ready.emit(response.text)
            else:
                log_timestamp("🤖 [GEMINI] ⚠️ Răspuns gol", "gemini_debug")
                self.error_occurred.emit("Răspuns gol de la AI.")
        except Exception as e:
            log_timestamp(f"🤖 [GEMINI] ❌ Eroare: {e}", "gemini_debug")
            self.error_occurred.emit(f"Eroare: {e}")

class GeminiWorkerTextOnly(QObject):
    """Worker pentru Gemini fără cameră - doar text"""
    response_ready = Signal(str)
    error_occurred = Signal(str)
    finished = Signal()
    
    def __init__(self, system_prompt, question_text, model_name):
        super().__init__()
        self.system_prompt = system_prompt
        self.question_text = question_text
        self.model = genai.GenerativeModel(model_name)

    def run(self):
        log_timestamp("🤖 [GEMINI TEXT-ONLY] Worker pornit.", "gemini_debug")
        try:
            prompt_parts = [
                self.system_prompt,
                f"\nUtilizator: {self.question_text}"
            ]

            log_timestamp(f"🤖 [GEMINI TEXT-ONLY] Request: '{self.question_text}'", "gemini_debug")
            response = self.model.generate_content(prompt_parts)
            
            if response.text:
                log_timestamp(f"🤖 [GEMINI TEXT-ONLY] ✅ Răspuns: '{response.text[:100]}...'", "gemini_debug")
                self.response_ready.emit(response.text)
            else:
                log_timestamp("🤖 [GEMINI TEXT-ONLY] ⚠️ Răspuns gol", "gemini_debug")
                self.error_occurred.emit("Răspuns gol de la AI.")
        except Exception as e:
            log_timestamp(f"🤖 [GEMINI TEXT-ONLY] ❌ Eroare: {e}", "gemini_debug")
            self.error_occurred.emit(f"Eroare: {e}")

class LearningSessionWorker(QObject):
    """
    Worker dedicat pentru sesiuni de învățare în Modul Profesor.
    Gestionează un singur ciclu: primește răspunsul elevului, evaluează, 
    decide următoarea acțiune și returnează feedback-ul.
    """
    response_ready = Signal(dict)  # Dict cu: outcome, text_to_speak, etc.
    error_occurred = Signal(str)
    finished = Signal()
    
    def __init__(self, mega_prompt):
        """
        Constructor MINIMAL - nu inițializăm resurse externe aici!
        
        Args:
            mega_prompt (str): Prompt-ul complet construit de MainApp
        """
        super().__init__()
        self.mega_prompt = mega_prompt
        self.model = None  # Va fi inițializat în run()
    
    def run(self):
        """
        Execuție în thread separat. Aici inițializăm modelul și facem apelul.
        """
        log_timestamp("🎓 [LEARNING] LearningSessionWorker pornit.", "app")
        try:
            # ⭐ CRUCIAL: Inițializăm modelul AICI, în thread-ul worker-ului
            log_timestamp("🎓 [LEARNING] Inițializez modelul Gemini...", "app")
            self.model = genai.GenerativeModel("gemini-flash-lite-latest")
            
            log_timestamp(f"🎓 [LEARNING] Trimit mega-prompt către AI (lungime: {len(self.mega_prompt)} caractere)", "app")
            response = self.model.generate_content(self.mega_prompt)
            
            if not response.text:
                log_timestamp("🎓 [LEARNING] ⚠️ Răspuns gol de la AI!", "app")
                self.error_occurred.emit("Răspuns gol de la AI.")
                return
            
            raw_response = response.text.strip()
            log_timestamp(f"🎓 [LEARNING] Răspuns brut de la AI: '{raw_response[:200]}...'", "app")
            
            # Parsare JSON
            # Curățăm de markdown dacă există
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.startswith("```"):
                raw_response = raw_response[3:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
            raw_response = raw_response.strip()
            
            try:
                result = json.loads(raw_response)
                log_timestamp(f"🎓 [LEARNING] ✅ JSON parsat cu succes: {result}", "app")
                self.response_ready.emit(result)
            except json.JSONDecodeError as e:
                log_timestamp(f"🎓 [LEARNING] ❌ Eroare parsare JSON: {e}", "app")
                log_timestamp(f"🎓 [LEARNING] Răspuns problematic: '{raw_response}'", "app")
                self.error_occurred.emit(f"Eroare parsare JSON: {e}")
        
        except Exception as e:
            log_timestamp(f"🎓 [LEARNING] ❌ Eroare în worker: {e}", "app")
            self.error_occurred.emit(str(e))
        
        finally:
            log_timestamp("🎓 [LEARNING] Worker își încheie execuția.", "app")
            self.finished.emit()
# =================================================================================
# AUDIO MONITORING + VOICE DETECTION
# =================================================================================

class IntentClassifierWorker(QObject):
    intent_classified = Signal(dict)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, text):
        super().__init__()
        self.text = text  # ⭐ CRUCIAL - salvăm textul!

    def run(self):
        log_timestamp("🤖 [INTENT] Worker de clasificare a intenției pornit.", "intent")
        try:
            prompt_template = """

Ești un asistent care analizează textul unui utilizator și îl clasifică. Răspunde DOAR cu un obiect JSON valid.

--- REGULĂ CRITICĂ DE BAZĂ ---
Regulile de mai jos sunt pentru textul în limba ROMÂNĂ. Dacă textul utilizatorului este într-o ALTĂ LIMBĂ (Engleză, Franceză, etc.), este aproape întotdeauna o 'conversation'. Nu încerca să aplici reguli de 'travel' sau 'summon' la text străin decât dacă este extrem de evident.
---

Categoriile posibile pentru 'intent' sunt:

1. 'travel_with_character': Utilizatorul vrea să MEARGĂ ÎMPREUNĂ către o altă scenă
   - Pattern: "[Nume], hai să mergem la [scenă]", "Mergem împreună la [scenă]"
   - Cuvinte cheie: "hai să mergem", "mergem împreună", "la [loc]"
   - Exemple: 
     * "Cucuvel, hai la școală" → {{"intent": "travel_with_character", "character": "cucuvel_owl", "scene": "scoala"}}

2. 'travel_solo': Utilizatorul SINGUR merge în altă scenă (fără alte personaje)
   - Pattern: "merg la [scenă]", "vreau să merg la [scenă]", "aș vrea să merg la [scenă]"
   - CUVINTE CHEIE: "merg" (eu singur), "vreau să merg" (eu), "ma duc" (eu)
   - IMPORTANT: Dacă EU (utilizatorul) vreau să merg → travel_solo
   - IMPORTANT: Dacă conține "împreună" sau "hai să" → travel_with_character
   - Exemple:
     * "Merg acasă" → {{"intent": "travel_solo", "scene": "acasa"}}
     * "Vreau eu să merg acasă" → {{"intent": "travel_solo", "scene": "acasa"}}
     * "Mă duc la școală" → {{"intent": "travel_solo", "scene": "scoala"}}

3. 'summon_character': Utilizatorul CHEAMĂ un personaj să VINĂ
   - Pattern: "[Nume], vino aici/și tu"
   - CUVINTE CHEIE OBLIGATORII: "vino", "hai", "cheamă", "apare"
   - IMPORTANT: Simplă adresare fără "vino" → NU e summon, e conversation!
   - Exemple: 
     * "Cucuvel, vino aici" → {{"intent": "summon_character", "character": "cucuvel_owl"}}
     * "Profesor, vino și tu" → {{"intent": "summon_character", "character": "cucuvel_owl"}}
     * "Bună ziua profesor" → {{"intent": "conversation"}} (NU e summon!)

4. 'send_character': Utilizatorul TRIMITE un personaj în altă scenă (fără el)
   - Pattern: "[Nume], mergi/du-te/pleacă la [scenă]" SAU "du-te [Nume] la [scenă]"
   - CUVINTE CHEIE OBLIGATORII: TU (personajul) + "du-te"/"mergi"/"pleacă" + destinație
   - IMPORTANT: Dacă TU (personajul) trebuie să meargă → send_character
   - IMPORTANT: Dacă EU (utilizatorul) vreau să merg → travel_solo
   - Diferența CRITICĂ:
     * "Merg acasă" (EU merg) → travel_solo ✅
     * "Du-te acasă" (TU mergi) → send_character ✅
   - Exemple:
     * "Cucuvel, du-te acasă" → {{"intent": "send_character", "character": "cucuvel_owl", "scene": "acasa"}}
     * "Du-te singur în poiană" (către speaker curent) → {{"intent": "send_character", "character": "cucuvel_owl", "scene": "poiana"}}
     * "Mergi la școală" (comandă către speaker) → {{"intent": "send_character", "character": "cucuvel_owl", "scene": "scoala"}}

5. 'conversation': Orice altceva - întrebări, comentarii, salutări, discuții
   - Include: salutări, întrebări, comentarii, adresări simple
   - Exemple:
     * "Bună ziua" → {{"intent": "conversation"}}
     * "Ce mai faci?" → {{"intent": "conversation"}}
     * "Nu am înțeles ce ai spus" → {{"intent": "conversation"}}
     * "Ce înseamnă asta?" → {{"intent": "conversation"}}

6. 'translation_request': Utilizatorul cere EXPLICIT traducerea ultimei replici folosind un cuvânt cheie specific.
   - REGULĂ STRICTĂ: Se activează DOAR dacă textul conține cuvântul "traducere" sau "tradu".
   - IMPORTANT: Fraze precum "nu am înțeles" sau "ce vrei să spui?" FĂRĂ cuvântul "traducere" sunt considerate 'conversation', NU 'translation_request'.
   - Exemple:
     * "Traducere" → {{"intent": "translation_request"}}
     * "Poți să faci o traducere, te rog?" → {{"intent": "translation_request"}}
     * "Tradu ce a spus." → {{"intent": "translation_request"}}
     * "Nu am înțeles" → {{"intent": "conversation"}}
     * "Ce înseamnă?" → {{"intent": "conversation"}}

7. 'start_learning': Utilizatorul cere să ÎNCEAPĂ o lecție/sesiune de învățare
   - Pattern: "vreau să învăț [subiect]", "hai să învățăm", "începe lecția"
   - CUVINTE CHEIE: "învăț", "învățăm", "lecție", "lecția", "începe", "hai să studiem"
   - Exemple:
     * "Vreau să învăț culorile" → {{"intent": "start_learning", "subject": "culori"}}
     * "Hai să învățăm" → {{"intent": "start_learning", "subject": ""}}
     * "Începe lecția de matematică" → {{"intent": "start_learning", "subject": "matematică"}}

8. 'exit_teacher_mode': Utilizatorul cere EXPLICIT să iasă din modul de învățare
   - Pattern: "stop", "pauză", "oprește lecția", "vreau să mă opresc"
   - CUVINTE CHEIE: "stop", "pauză", "pauza", "oprește", "opreste", "gata cu lecția"
   - IMPORTANT: Această intenție are sens DOAR în contextul unei sesiuni active de învățare
   - Exemple:
     * "Stop lecție" → {{"intent": "exit_teacher_mode"}}
     * "Pauză, te rog" → {{"intent": "exit_teacher_mode"}}
     * "Vreau să mă opresc" → {{"intent": "exit_teacher_mode"}}
     * "Gata cu învățatul" → {{"intent": "exit_teacher_mode"}}

---
PARAMETRI:

Scene valide: 'scoala', 'acasa', 'poiana', 'pajiste'

Personaje valide:
- 'cucuvel' sau 'cucuvel_owl': Profesorul Cucuvel (bufniță)
- 'rina' sau 'rina_cat': Rina (pisică)

Detectează variații: "profesor", "dom profesor", "domnul profesor" → referință la 'cucuvel_owl'
Detectează variații: "pisica", "pisico" → referință la 'rina_cat'

---
REGULI CRITICE:
1. Dacă textul conține doar SALUT/ÎNTREBARE fără "vino"/"mergi"/"hai" → conversation
2. Simplă menționare a numelui/titlului unui personaj NU înseamnă summon
3. Pentru summon trebuie EXPLICIT: "vino", "hai aici", "cheamă"
4. Pentru travel trebuie EXPLICIT: "să mergem", "hai la", "merg la"
5. Pentru send trebuie: "du-te"/"du te"/"mergi"/"pleacă" + destinație
6. Pentru translation trebuie: "traducere" sau "tradu". Orice altă formă de neînțelegere este 'conversation'.
7. Dacă e DOAR comandă de plecare (fără "împreună"/"hai să") → send către vorbitorul activ
8. Pentru start_learning trebuie: "învăț", "învățăm", "lecție" sau variații
9. Pentru exit_teacher_mode trebuie: "stop", "pauză", "oprește" în contextul învățării

---
ACUM ANALIZEAZĂ:

Text utilizator: "{text}"

Răspunde DOAR cu JSON, fără alte explicații:
"""
           
            
            prompt = prompt_template.format(text=self.text)
            
            # Generare răspuns de la AI
            model = genai.GenerativeModel("gemini-flash-lite-latest")
            response = model.generate_content(prompt)
            raw_response = response.text.strip()
            
            log_timestamp(f"🤖 [INTENT] Răspuns brut de la AI: '{raw_response}'", "intent")
            
            # Parsare JSON
            # Curățăm răspunsul de eventuale backticks sau markdown
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.startswith("```"):
                raw_response = raw_response[3:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
            raw_response = raw_response.strip()
            
            # Parse JSON
            try:
                intent_data = json.loads(raw_response)
            except json.JSONDecodeError as e:
                log_timestamp(f"🤖 [INTENT] ⚠️ Eroare parsare JSON: {e}. Fallback la conversation.", "intent")
                intent_data = {"intent": "conversation"}
            
            log_timestamp(f"🤖 [INTENT] ✅ Intenție clasificată: {intent_data}", "intent")
            
            # Emitem semnalul cu datele clasificate
            self.intent_classified.emit(intent_data)
            
        except Exception as e:
            log_timestamp(f"🤖 [INTENT] ❌ Eroare în worker-ul de intenție: {e}", "intent")
            # Fallback: tratăm ca și conversație normală
            self.error_occurred.emit(str(e))
            self.intent_classified.emit({"intent": "conversation"})
        
        finally:
            log_timestamp("🤖 [INTENT] Worker-ul de intenție și-a terminat execuția.", "intent")
            self.finished.emit()

class ContinuousVoiceWorker(QObject):
    language_lock_requested = Signal(str)
    speech_activity_changed = Signal(bool) # True = a început vorbirea, False = s-a terminat
    pause_progress_updated = Signal(int)   # Progresul clepsidrei (0-100)
    speech_time_updated = Signal(float) # <-- ADAUGĂ ACEASTĂ LINIE
    speech_timeout = Signal()  # ← ADAUGĂ ACEASTĂ LINIE AICI
    
    transcription_ready = Signal(str)
    status_changed = Signal(str)
    calibration_done = Signal(float)
    audio_level_changed = Signal(float)
    speaker_identified = Signal(str, float)  # ⭐ NOU: (nume, confidence) ⭐
    
    def __init__(self, threshold, pause_duration, margin_percent, max_speech_duration, enable_echo_cancellation):
        super().__init__()
        self._is_running = False
        self._is_muted = False
        self.enable_echo_cancellation = enable_echo_cancellation
        self.enable_speaker_identification = True # <-- ⭐ ADAUGĂ ACEASTĂ LINIE NOUĂ ⭐
        log_timestamp(f"🎤 [VAD INIT] Anulare Ecoul setată la: {self.enable_echo_cancellation}", "app") # Log de verificare
        self.current_lock_mode = 'auto'
        self.primary_language = "ro-RO"
        self.secondary_language = "ro-RO"
        
        # Parametri audio
        self.sample_rate = 16000
        self.frame_duration = 32
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)

        # Silero VAD setup
        log_timestamp("🧠 [SILERO VAD] Încărcare model neural...", "vad")
        try:
            self.vad_model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad', model='silero_vad',
                force_reload=False, onnx=False
            )
            (self.get_speech_timestamps, _, _, _, _) = utils
            log_timestamp("✅ [SILERO VAD] Model încărcat cu succes!", "vad")
        except Exception as e:
            log_timestamp(f"❌ [SILERO VAD] Eroare la încărcare: {e}", "vad")
            raise
        
        # --- BLOC MUTAT MAI SUS ---
        # Parametri detecție
        self.threshold = threshold
        self.pause_duration = pause_duration
        self.margin_percent = margin_percent
        self.max_speech_duration = max_speech_duration
        
        # Praguri Silero
        self.speech_threshold = 0.5
        self.silence_threshold = 0.3
        # --- SFÂRȘIT BLOC MUTAT ---

        # Calcule interne pe baza parametrilor
        self.silence_frames_threshold = int((self.pause_duration * 1000) / self.frame_duration)
        self.MAX_SPEECH_FRAMES = int(self.max_speech_duration * 1000 / self.frame_duration)
        
        # Buffer pentru detectare voce
        self.ring_buffer_size = int(self.sample_rate * 0.5)
        self.ring_buffer = collections.deque(maxlen=self.ring_buffer_size // self.frame_size)
        
        # State tracking
        self.is_speech_active = False
        self.frames_since_silence = 0
        
        # Acumulare audio pentru transcriere
        self.speech_frames = []
        
        # Pentru echo detection
        self.last_ai_text = ""
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        
        # --- LOG-URILE SUNT ACUM LA FINAL, CÂND TOATE VARIABILELE EXISTĂ ---
        log_timestamp("🎤 [VAD INIT] Silero VAD inițializat", "vad")
        log_timestamp(f"🎤 [VAD INIT] Sample rate: {self.sample_rate}Hz", "vad")
        log_timestamp(f"🎤 [VAD INIT] Frame duration: {self.frame_duration}ms", "vad")
        log_timestamp(f"🎤 [VAD INIT] Frame size: {self.frame_size} samples", "vad")
        log_timestamp(f"🎤 [VAD INIT] Speech threshold: {self.speech_threshold}", "vad")
        log_timestamp(f"🎤 [VAD INIT] Silence threshold: {self.silence_threshold}", "vad")
        log_timestamp(f"🎤 [VAD INIT] Silence frames threshold: {self.silence_frames_threshold} frames ({self.pause_duration:.1f}s)", "vad")
        log_timestamp(f"🎤 [VAD INIT] Max speech frames: {self.MAX_SPEECH_FRAMES} frames ({self.max_speech_duration}s)", "vad")

    
    def set_primary_language(self, lang_code):
        """Setează limba principală de ascultare."""
        if self.primary_language != lang_code:
            self.primary_language = lang_code
            log_timestamp(f"🗣️ [TRANSCRIERE] Limba primară de ascultare setată la: '{lang_code}'", "transcription")

    def set_last_ai_text(self, text):
        """Setează ultimul text spus de AI pentru detecție echo"""
        self.last_ai_text = text
        log_timestamp(f"🔊 [ECHO PROTECTION] Salvat text AI: '{text[:50]}...'", "echo")

    def set_muted(self, muted, is_ai_speaking=True):
        """Activează/dezactivează ascultarea."""
        self._is_muted = muted
        
        # ⭐ GOLEȘTE BUFFER LA UNMUTE ⭐
        if not muted:  # Când se face unmute
            self.ring_buffer.clear()
            self.speech_frames = []
            self.is_speech_active = False
            log_timestamp("🗑️ [MUTING] Buffer-ul audio a fost golit la unmute", "mute")
        # ⭐ SFÂRȘIT ⭐
        
        if muted:
            if is_ai_speaking:
                log_timestamp("🔇 [MUTING] Ascultare PAUSATĂ (AI vorbește)", "mute")
                self.status_changed.emit("🔇 Pausat (AI vorbește)")
            else:
                log_timestamp("🔇 [MUTING] Ascultare PAUSATĂ (Utilizator)", "mute")
                self.status_changed.emit("🎧 Mut (exersezi)")
        else:
            log_timestamp("🔊 [MUTING] Ascultare RELUATĂ", "mute")
            self.status_changed.emit("⚪ Aștept să vorbești...")

    def set_max_speech_duration(self, seconds):
        """Actualizează limita de timp pentru vorbire în timp real."""
        self.max_speech_duration = seconds
        self.MAX_SPEECH_FRAMES = int(seconds * 1000 / self.frame_duration)
        log_timestamp(f"🎤 [WORKER UPDATE] Durata maximă a segmentului a fost setată la {seconds}s.", "app")

    def is_echo(self, transcribed_text):
        """Verifică dacă textul transcris este echo din răspunsul AI"""
        
        # --- Verificarea comutatorului ---
        if not self.enable_echo_cancellation:
            return False # Ieșire imediată dacă funcționalitatea este dezactivată
        # ---------------------------------
        
        if not self.last_ai_text or not transcribed_text:
            return False
        
        # Normalizăm textul AI
        ai_normalized = self.last_ai_text.lower()
        ai_normalized = ''.join(c for c in ai_normalized if c.isalnum() or c.isspace())
        
        # Normalizăm textul transcris
        transcribed_normalized = transcribed_text.lower()
        transcribed_normalized = ''.join(c for c in transcribed_normalized if c.isalnum() or c.isspace())
        
        # Împărțim în cuvinte
        ai_words = set(ai_normalized.split())
        transcribed_words = transcribed_normalized.split()
        
        if len(transcribed_words) == 0:
            return False
        
        # Calculăm câte cuvinte din transcriere sunt în răspunsul AI
        common_words = sum(1 for word in transcribed_words if word in ai_words)
        similarity = common_words / len(transcribed_words)
        
        log_timestamp(f"🔍 [ECHO CHECK] Similitudine: {similarity*100:.1f}% ({common_words}/{len(transcribed_words)} cuvinte)", "echo")
        
        # Dacă >75% din cuvinte sunt în răspunsul AI → e echo
        is_echo_detected = similarity > 0.75
        
        if is_echo_detected:
            log_timestamp(f"🚫 [ECHO DETECTAT] '{transcribed_text}' similar cu AI: {similarity*100:.1f}%", "echo")
        
        return is_echo_detected

    def audio_callback(self, indata, frames, time_info, status):
        """Callback-ul audio, acum cu calcul pentru cronometru."""
        if status: log_timestamp(f"⚠️ [AUDIO] Status: {status}", "audio")
        
        audio_data = indata[:, 0].copy()
        
        rms = np.sqrt(np.mean(audio_data.astype(float)**2))
        if rms > 0:
            db_level = 20 * np.log10(rms) + 90
            self.audio_level_changed.emit(min(max(db_level * 50, 0), 10000))
        
        if self._is_muted: return
        
        audio_tensor = torch.from_numpy(audio_data).float()
        with torch.no_grad():
            speech_probability = self.vad_model(audio_tensor, self.sample_rate).item()
        
        is_speech = speech_probability > self.speech_threshold
        
        audio_int16 = (audio_data * 32767).astype(np.int16)
        self.ring_buffer.append(audio_int16)
        
        if is_speech:
            if not self.is_speech_active:
                self.is_speech_active = True
                self.speech_activity_changed.emit(True)
                self.pause_progress_updated.emit(100)
                log_timestamp("🟢 [VAD] Început vorbire detectat", "vad")
                self.frames_since_silence = 0
                self.speech_frames = list(self.ring_buffer)
                self.status_changed.emit("🔵 Vorbești...")
            else:
                self.frames_since_silence = 0
                self.speech_frames.append(audio_int16)
                self.pause_progress_updated.emit(100)
        else: # Tăcere
            if self.is_speech_active:
                self.frames_since_silence += 1
                self.speech_frames.append(audio_int16)
                progress = 100 - int(100 * self.frames_since_silence / self.silence_frames_threshold)
                self.pause_progress_updated.emit(progress)

        # --- BLOC NOU: Logică Cronometru ---
        if self.is_speech_active:
            timp_ramas = (self.MAX_SPEECH_FRAMES - len(self.speech_frames)) * self.frame_duration / 1000.0
            self.speech_time_updated.emit(timp_ramas)
        # --- SFÂRȘIT BLOC NOU ---

        # Verificare forțată a limitei de timp
        should_process_due_to_pause = self.is_speech_active and self.frames_since_silence >= self.silence_frames_threshold
        should_process_due_to_length = self.is_speech_active and len(self.speech_frames) >= self.MAX_SPEECH_FRAMES

        if should_process_due_to_pause or should_process_due_to_length:
            if should_process_due_to_length:
                log_timestamp("🔴 [VAD] Limita de timp atinsă! Se procesează forțat.", "vad")
                self.speech_timeout.emit()  # ← TIMEOUT - signal special
            else:
                log_timestamp(f"🔴 [VAD] Sfârșit vorbire (pauză).", "vad")
                self.speech_activity_changed.emit(False)  # ← PAUZĂ - signal normal
            
            self.speech_time_updated.emit(-1)
            self.process_captured_speech()
            
            self.is_speech_active = False
            self.frames_since_silence = 0
            self.speech_frames = []

    def process_captured_speech(self):
        """Procesează audio-ul capturat, cu comutare manuală NATIV/FOCUS/TRADUCERE."""
        
        # ⭐ PATCH pentru speech_recognition în PyInstaller - folosește WAV direct ⭐
        if getattr(sys, 'frozen', False):
            import speech_recognition as sr_module
            
            # Salvăm metoda originală
            original_recognize_google = sr_module.Recognizer.recognize_google
            
            def patched_recognize_google(self, audio_data, key=None, language="en-US", pfilter=0, show_all=False, with_confidence=False):
                # Convertim audio_data să folosească WAV în loc de FLAC
                wav_data = audio_data.get_wav_data(convert_rate=None, convert_width=None)
                # Creăm un nou AudioData cu aceleași setări
                patched_audio = sr_module.AudioData(wav_data, audio_data.sample_rate, audio_data.sample_width)
                # Apelăm metoda originală cu audio patchuit
                return original_recognize_google(self, patched_audio, key, language, pfilter, show_all, with_confidence)
            
            # Înlocuim metoda
            sr_module.Recognizer.recognize_google = patched_recognize_google
            log_timestamp("🔧 [PYINSTALLER] Google Speech patchuit să folosească WAV direct", "process")        
            
        if len(self.speech_frames) == 0:
            log_timestamp("⚠️ [PROCESS] Niciun frame de procesat", "process")
            return
        
        temp_path = None
        try:
            # Concatenăm toate frame-urile
            audio_data = np.concatenate(self.speech_frames)
            
            duration = len(audio_data) / self.sample_rate
            log_timestamp(f"🎵 [PROCESS] Durată captată: {duration:.2f}s ({len(audio_data)} samples)", "process")
            
            # Ignorăm clipurile prea scurte (sub 0.3s)
            if duration < 0.3:
                log_timestamp(f"⚠️ [PROCESS] Prea scurt ({duration:.2f}s) - ignorat", "process")
                return
            
            # Salvăm într-un fișier WAV temporar
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_path = temp_wav.name
                
                with wave.open(temp_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                log_timestamp(f"💾 [PROCESS] Salvat în: {temp_path}", "process")
            
            # Citim fișierul cu speech_recognition
            # Citim fișierul cu speech_recognition
            with sr.AudioFile(temp_path) as source:
                # Asigurăm rate-ul corect pentru Google (8000, 16000, sau 48000 Hz)
                audio = self.recognizer.record(source)
                
            # ⭐ FIX: Convertim audio la format acceptat de Google API când e împachetat
            if getattr(sys, 'frozen', False):
                # Convertim la 16kHz mono pentru compatibilitate maximă
                wav_data = audio.get_wav_data(convert_rate=16000, convert_width=2)
                audio = sr.AudioData(wav_data, 16000, 2)
                log_timestamp("🔧 [PYINSTALLER] Audio reconvertat la 16kHz pentru compatibilitate", "process")


            
            log_timestamp("🗣️ [TRANSCRIERE] Trimit la Google Speech API...", "transcription")
            self.status_changed.emit("🟡 Transcriu...")
            
            text = None
            
            # --- FAZA 1: Verificare Comenzi în Română ---
            try:
                log_timestamp("🗣️ [TRANSCRIERE] Verificare comenzi în Română...", "transcription")
                possible_command = self.recognizer.recognize_google(audio, language="ro-RO")
                text_lower = possible_command.strip().lower()
                if text_lower.startswith('nativ') or text_lower.startswith('domn profesor'):
                    log_timestamp("🔒 [LANG] Comanda NATIV detectată!", "transcription")
                    self.language_lock_requested.emit('nativ')
                    return
                elif text_lower.startswith('focus'):
                    log_timestamp("🎯 [LANG] Comanda FOCUS detectată!", "transcription")
                    self.language_lock_requested.emit('focus')
                    return
                elif text_lower.startswith('traducere') or text_lower.startswith('tradu'):
                    text = possible_command
                    log_timestamp("🌐 [LANG] Comanda TRADUCERE detectată, se procesează ca input.", "transcription")
            except sr.UnknownValueError:
                pass
            
            # --- FAZA 2: Transcriere Normală ---
            if text is None:
                try:
                    if self.current_lock_mode == 'focus':
                        lang_to_listen = self.primary_language
                    else:
                        lang_to_listen = self.secondary_language
                    
                    log_timestamp(f"🗣️ [TRANSCRIERE] Ascultare în modul '{self.current_lock_mode}', limba: '{lang_to_listen}'...", "transcription")
                    text = self.recognizer.recognize_google(audio, language=lang_to_listen)
                except sr.UnknownValueError:
                    log_timestamp("❌ [TRANSCRIERE] Nu s-a putut înțelege în modul activ.", "transcription")
                    self.status_changed.emit("⚠️ Nu am înțeles")
                    return
        
            if text:
                log_timestamp(f"✅ [TRANSCRIERE] Transcris: '{text}'", "transcription")
                
                if self.is_echo(text):
                    log_timestamp(f"🚫 [TRANSCRIERE] ECHO ignorat: '{text}'", "transcription")
                    return
                
                # ⭐ SPEAKER IDENTIFICATION ⭐
                identified_speaker = None
                confidence = 0.0
                
                if self.enable_speaker_identification:
                    log_timestamp("🔍 [VOICE ID] Identificare vorbitor activată. Se rulează comparația.", "voice")
                    if hasattr(self, 'voice_manager') and self.voice_manager and temp_path and os.path.exists(temp_path):
                        try:
                            threshold = self.voice_recognition_threshold if hasattr(self, 'voice_recognition_threshold') else 0.75
                            identified_speaker, confidence = self.voice_manager.identify_speaker(
                                temp_path,
                                self.family_data if hasattr(self, 'family_data') else [],
                                threshold=threshold
                            )
                            
                            if identified_speaker:
                                log_timestamp(f"✅ [VOICE ID] Identificat: {identified_speaker} ({confidence:.2%})", "voice")
                                self.speaker_identified.emit(identified_speaker, confidence)
                            else:
                                log_timestamp(f"⚠️ [VOICE ID] Necunoscut (cel mai bun: {confidence:.2%})", "voice")
                                self.speaker_identified.emit(None, 0.0)
                        except Exception as e:
                            log_timestamp(f"⚠️ [VOICE ID] Eroare identificare: {e}", "voice")
                            self.speaker_identified.emit(None, 0.0)
                else:
                    log_timestamp("🚫 [VOICE ID] Identificare vorbitor dezactivată. Se sare peste comparație.", "voice")
                    self.speaker_identified.emit(None, 0.0)
                
                self.transcription_ready.emit(text)
                
        except sr.RequestError as e:
            log_timestamp(f"❌ [TRANSCRIERE] Eroare API Google: {e}", "transcription")
            self.status_changed.emit(f"⚠️ Eroare: {e}")
        except Exception as e:
            log_timestamp(f"❌ [PROCESS] Eroare generală în procesarea audio: {e}", "process")
            import traceback
            log_timestamp(f"❌ [PROCESS] Stack trace:\n{traceback.format_exc()}", "process")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    log_timestamp(f"⚠️ [PROCESS] Eroare la ștergerea fișierului temp: {e}", "process")    

    def run(self):
        """
        Bucla principală a worker-ului.
        Pornește stream-ul audio și rămâne în listen mode continuu.
        """
        log_timestamp("🎤 [SILERO VAD WORKER] Worker pornit", "vad")
        log_timestamp(f"🎤 [SILERO VAD WORKER] Configurație:", "vad")
        log_timestamp(f"   - Sample Rate: {self.sample_rate}Hz", "vad")
        log_timestamp(f"   - Frame Duration: {self.frame_duration}ms", "vad")
        log_timestamp(f"   - Pauză pentru sfârșit: {self.pause_duration}s", "vad")
        log_timestamp(f"   - Speech Threshold: {self.speech_threshold}", "vad")
        log_timestamp(f"   - Silence Threshold: {self.silence_threshold}", "vad")
        
        self._is_running = True
        self.status_changed.emit("⚪ Aștept să vorbești...")
        
        try:
            log_timestamp("🎤 [SILERO VAD WORKER] Pornesc stream audio...", "vad")
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.frame_size,
                callback=self.audio_callback
            ):
                log_timestamp("✅ [SILERO VAD WORKER] Stream audio pornit - ascult continuu cu neural VAD", "vad")
                
                # Bucla de keep-alive - thread-ul rămâne activ
                while self._is_running:
                    sd.sleep(100)  # Sleep 100ms, lasă callback-ul să ruleze
                
                log_timestamp("🛑 [SILERO VAD WORKER] Stop requested - opresc stream", "vad")
                
        except Exception as e:
            log_timestamp(f"❌ [SILERO VAD WORKER] EROARE CRITICĂ: {e}", "vad")
            import traceback
            log_timestamp(f"❌ [SILERO VAD WORKER] Stack trace:\n{traceback.format_exc()}", "vad")
            self.status_changed.emit(f"⚠️ Eroare: {e}")
        finally:
            log_timestamp("🎤 [SILERO VAD WORKER] Worker oprit", "vad")

    def stop(self):
        """Oprește worker-ul"""
        log_timestamp("🎤 [SILERO VAD WORKER] 🛑 stop() CHEMAT - setez _is_running=False", "vad")
        self._is_running = False


# =================================================================================
# 1. Inițializare și Configurare de Bază
# (Metodele care setează starea inițială a aplicației)
# =================================================================================

class CharacterApp(QWidget):
    def __init__(self):
        super().__init__()

        # --- BLOC NOU DE VERIFICARE A CHEII API ---
        from PySide6.QtWidgets import QMessageBox
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            log_timestamp("⚠️ [API KEY] Cheia GOOGLE_API_KEY nu a fost găsită. Se cere utilizatorului.", "app")
            api_key = self._prompt_for_api_key()

        if not api_key:
            # Dacă utilizatorul tot nu a introdus o cheie, afișăm o eroare fatală și închidem
            QMessageBox.critical(self, "Eroare Critică", "Aplicația nu poate funcționa fără o cheie API Google Gemini validă. Programul se va închide.")
            # Ieșim elegant din constructor
            QTimer.singleShot(0, self.close)
            return
        
        # Configurăm API-ul DOAR dacă avem o cheie validă
        try:
            genai.configure(api_key=api_key)
            log_timestamp("✅ [API KEY] Google Gemini API a fost configurat cu succes.", "app")
        except Exception as e:
            QMessageBox.critical(self, "Eroare de Configurare", f"Cheia API nu este validă sau a apărut o eroare: {e}")
            QTimer.singleShot(0, self.close)
            return
        # --- SFÂRȘITUL BLOCULUI NOU ---

        self.dpi_scaler = DPIScaler(QApplication.instance())
        log_timestamp("🚀 [APP INIT] Pornire aplicație - Arhitectură Modulară.")
        self.setWindowTitle("Teatru Digital Interactiv")

        # --- ADAUGAȚI ACEST BLOC ---
        self.CULORI_SEMAFOR = {
            "rosu_aprins": "background-color: #FF0000;",
            "rosu_stins": "background-color: #4A0000;",
            "verde_aprins": "background-color: #00FF00;",
            "verde_stins": "background-color: #004A00;",
            "portocaliu_aprins": "#FFA500",
            "portocaliu_stins": "#5A3A00"
        }
        # --- SFÂRȘIT BLOC NOU ---

        # --- HARTĂ LIMBI PENTRU RINA ---
        self.RINA_LANGUAGES = {
            "Engleză":    {"code": "en", "voice": "en-GB-SoniaNeural"},
            "Germană":    {"code": "de", "voice": "de-DE-KatjaNeural"},
            "Italiană":   {"code": "it", "voice": "it-IT-ElsaNeural"},
            "Franceză":   {"code": "fr", "voice": "fr-FR-DeniseNeural"},
            "Spaniolă":   {"code": "es", "voice": "es-ES-ElviraNeural"},
            "Rusă":       {"code": "ru", "voice": "ru-RU-SvetlanaNeural"},
            "Greacă":     {"code": "el", "voice": "el-GR-NestorasNeural"},
            "Japoneză":   {"code": "ja", "voice": "ja-JP-NanamiNeural"},
            "Coreeană":   {"code": "ko", "voice": "ko-KR-SunHiNeural"} 
        }
        # ------------------------------------
        
        # ⭐ ÎNCĂRCARE CONFIG DIN FIȘIER
        self.config = load_config()
        
        # ⭐ SETARE GEOMETRIE FEREASTRĂ DIN CONFIG
        saved_geom = self.config.get("window_geometry")
        
        if saved_geom and "scale_factor" in saved_geom:
            saved_scale = saved_geom["scale_factor"]
            current_scale = self.dpi_scaler.scale_factor
            
            if abs(saved_scale - current_scale) < 0.05:
                self.setGeometry(saved_geom["x"], saved_geom["y"], 
                                saved_geom["width"], saved_geom["height"])
                log_timestamp(f"🪟 [WINDOW] Geometrie restaurată: {saved_geom['x']}, {saved_geom['y']}, "
                            f"{saved_geom['width']}x{saved_geom['height']}", "app")
            else:
                width, height, x, y = self.dpi_scaler.get_optimal_window_size()
                self.setGeometry(x, y, width, height)
                log_timestamp(f"🪟 [WINDOW] Geometrie recalculată: {x}, {y}, {width}x{height}", "app")
        else:
            width, height, x, y = self.dpi_scaler.get_optimal_window_size()
            self.setGeometry(x, y, width, height)
            log_timestamp(f"🪟 [WINDOW] Geometrie optimă calculată: {x}, {y}, {width}x{height}", "app")

        # --- Starea Aplicației ---
        self.conversation_state = 'INACTIVE'
        self.is_muted = False
        self.is_speaking = False
        self.is_thinking = False
        self.last_audio_file_path = None 
        self.initial_ai_model = self.config.get("ai_model_name") 
        self.viseme_queue = []
        self.greeted_users = {}
        self.conversation_log = []
        self.MAX_LOG_ENTRIES = 10


        # ⭐ Logging conversație în fișier ⭐
        self.conversation_log_file = None
        self.conversation_logs_folder = Path(paths.CONVERSATION_LOGS_DIR)   # în ../Data
        self.conversation_logs_folder.mkdir(exist_ok=True)
        self.conversation_log_filename_base = None  # ⭐ NOU - pentru reutilizare
        self.conversation_log_backup = None         # ⭐ NOU - backup memorie
        
        self.voice_print_manager = VoicePrintManager()

        self.active_speaker_id = "cucuvel_owl"
        self.last_user_text = ""  
        self.last_character_speeches = {}
        self.pending_speaker_return = None

        self.waiting_for_travel_clarification = False
        self.pending_travel_data = None
        self.clarification_timeout_timer = QTimer(self)
        self.clarification_timeout_timer.setSingleShot(True)
        self.clarification_timeout_timer.timeout.connect(self._handle_clarification_timeout)

        self.pending_move_after_tts = None
        self.language_lock = 'auto'

        # ====================================================================
        # ⭐⭐ ADAUGĂ ACEST BLOC NOU PENTRU STAREA DE ÎNVĂȚARE ⭐⭐
        # ====================================================================
        # Starea principală a aplicației: 'CONVERSATION' sau 'AWAITING_STUDENT_NAME'
        self.app_state = 'CONVERSATION' 
        # Stochează datele intenției 'start_learning' în timp ce așteptăm un nume
        self.pending_learning_intent_data = None
        # ====================================================================

        # =================================================================================
        # VARIABILE PENTRU SISTEMUL DE ÎNVĂȚARE (MODUL PROFESOR)
        # =================================================================================
        
        # Stare sistem
        self.teacher_mode_active = False
        self.pending_first_question = False
        self.current_student_name = None
        self.current_domain_id = None
        self.current_tier_id = None
        
        # Date curriculum
        self.available_domains = {}
        self.current_curriculum = None
        self.current_tier_data = None
        
        # Tracking răspunsuri în sesiune
        self.session_failed_questions = []
        self.current_question_id = None
        self.current_question_attempt = 0
        
        # Thread management pentru learning
        self.learning_thread = None
        self.learning_worker = None
        
        # Managementul scenei înainte și după lecție
        self.scene_before_lesson = None

        # Resurse pentru tabla virtuală
        self.blackboard_rect = QRect(350, 150, 700, 450) # Coordonate exemplu. Va trebui să le ajustezi!
        self.chalk_font = None # Va fi încărcat mai târziu
        
        # UI Elements
        self.exit_teacher_button = None
        
        # --- LINIA LIPSA ESTE AICI ---
        self.app_state = 'CONVERSATION' # Stări: 'CONVERSATION', 'AWAITING_DOMAIN_CHOICE'
        # --- SFÂRȘIT LINIE LIPSA ---

        self.current_speaker = None
        self.gaze_states = {}

        # --- Inițializare Manageri ---
        log_timestamp("🧠 [APP INIT] Se inițializează managerii...")
        self.scene_manager = SceneManager(config_path=resource_path("scenes/scene_configs.json"))
        self.character_manager = CharacterManager(characters_root_folder=resource_path("characters"))
        self._apply_saved_character_settings()
        log_timestamp("✅ [APP INIT] Manageri inițializați.")
        
        self.character_layers = {}
        self.all_animators = []

        # --- Parametri din Config ---
        self.threshold = self.config["threshold"]
        self.pause_duration = self.config["pause_duration"]
        self.max_speech_duration = self.config["max_speech_duration"]
        self.margin_percent = self.config["margin_percent"]
        self.voice_enabled = False
        
        # --- Inițializare Worker-i ---
        self.webcam_worker, self.webcam_thread = None, None
        self.gemini_worker, self.gemini_thread = None, None
        self.tts_worker, self.tts_thread = None, None
        self.voice_worker, self.voice_thread = None, None
        self.intent_worker, self.intent_thread = None, None
        
        # --- Inițializare UI ---
        log_timestamp("🎨 [APP INIT] Se construiește interfața grafică...")
        self.init_ui()
        self.echo_cancellation_checkbox.setChecked(self.config.get("enable_echo_cancellation", True))

        # --- APLICAREA CONFIGURĂRILOR INIȚIALE PENTRU UI ---
        
        # 1. Limba pentru Rina
        saved_code = self.config.get("rina_language_code", "en")
        for name, details in self.RINA_LANGUAGES.items():
            if details["code"] == saved_code:
                self.rina_language_combo.setCurrentText(name)
                break
        
        # 2. Subtitrări
        font_size = self.config.get("subtitle_font_size", 26)
        self.subtitle_font_slider.setValue(font_size)
        self.subtitle_font_label.setText(f"Mărime font: {font_size}px")
        self._update_subtitle_style()
        
        subtitle_mode = self.config.get("subtitle_mode", "original")
        if subtitle_mode == "latin (fonetic)":
            self.subtitle_mode_combo.setCurrentIndex(1)
        elif subtitle_mode == "combinat":
            self.subtitle_mode_combo.setCurrentIndex(2)
        else:
            self.subtitle_mode_combo.setCurrentIndex(0)
            
        # 3. Furnizor TTS
        provider = self.config.get("tts_provider", "microsoft")
        if provider == "google":
            self.tts_provider_combo.setCurrentIndex(1)
        else:
            self.tts_provider_combo.setCurrentIndex(0)

        # 4. Setarea Modelului AI
        saved_model = self.config.get("ai_model_name", "models/gemini-flash-lite-latest")
        index = self.ai_model_combo.findText(saved_model)
        if index != -1:
            self.ai_model_combo.setCurrentIndex(index)
        

        # 5. Încărcarea pozițiilor pentru sliderele de voce
        self._load_slider_positions_from_config()
        
        # 6. Setarea stării pentru bifa de Speaker ID
        enable_speaker_id = self.config.get("enable_speaker_identification", True)
        self.enable_speaker_id_checkbox.setChecked(enable_speaker_id)

        # ---------------------------

        log_timestamp("✅ [APP INIT] Interfață grafică construită.")
        
        # --- Conectare Semnale Manageri ---
        log_timestamp("🔗 [APP INIT] Se conectează semnalele managerilor...")
        self.scene_manager.scene_changed.connect(self.on_scene_changed)
        self.character_manager.character_added_to_stage.connect(self.on_character_added)
        self.character_manager.character_removed_from_stage.connect(self.on_character_removed)
        log_timestamp("✅ [APP INIT] Semnale conectate.")
        
        # --- Timere ---
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.update_synced_animation)
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._idle_animation)
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.animate_thinking)
        
        # --- Inițializare Pygame ---
        log_timestamp("🔊 [PYGAME] Se inițializează mixer-ul audio...")
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            log_timestamp("✅ [PYGAME] Mixer inițializat cu succes.")
        except Exception as e:
            log_timestamp(f"❌ [PYGAME] Eroare la inițializarea mixer-ului: {e}")
        
        # --- Inițializare Streaming TTS Manager ---
        log_timestamp("🔊 [STREAMING TTS] Se inițializează manager-ul de streaming TTS...")
        self.streaming_tts = StreamingTTSManager()
        self.streaming_tts.signals.sentence_audio_ready.connect(self.on_sentence_audio_ready)
        self.streaming_tts.signals.all_sentences_finished.connect(self.on_all_sentences_finished)
        self.streaming_tts.signals.error_occurred.connect(self.on_streaming_tts_error)
        self.streaming_tts.signals.play_audio_file.connect(self.on_play_audio_file)  # ⭐ NOU


        log_timestamp("✅ [STREAMING TTS] Manager inițializat și conectat", "app")
        
        # Variabile pentru gestionarea sincronizării per-propoziție
        self.sentence_count = 0
        self.current_sentence_index = 0
        self.full_text_for_animation = ""
        self.pending_tts_callback = None  

        # ⭐ Variabile pentru redare asincronă pygame
        self.pygame_check_timer = QTimer(self)
        self.pygame_check_timer.timeout.connect(self._check_pygame_playback)
        self.current_playing_audio = None
        # --- Sfârșit Inițializare Streaming TTS ---
        
        # --- Încărcare date familie la pornire ---
        self._load_family_data()     
        self._discover_available_domains()

        # --- Încărcare date familie la pornire ---
        self._load_family_data()     
        self._discover_available_domains()   
        # --- Stare Inițială ---
        log_timestamp("🎬 [APP INIT] Se setează starea inițială a scenei...")
        self.scene_manager.set_scene("acasa")
        self.character_manager.add_character_to_stage("cucuvel_owl")
        self.character_manager.add_character_to_stage("rina_cat")
        
        self.update_ui_for_state()

        from PySide6.QtGui import QFontDatabase
        font_id = QFontDatabase.addApplicationFont(resource_path("assets/fonts/Chalkboard-Regular.ttf"))
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.chalk_font = QFont(font_family)
            log_timestamp(f"✅ [FONT] Font-ul 'cretă' ('{font_family}') a fost încărcat cu succes.", "app")
        else:
            log_timestamp("❌ [FONT] Eroare la încărcarea font-ului 'cretă'. Se va folosi un font de sistem.", "app")
            self.chalk_font = QFont() # Folosim un font default ca fallback

        # --- BLOC NOU: Încărcare resurse custom (FONT) ---
        font_id = QFontDatabase.addApplicationFont(resource_path("assets/fonts/Chalkboard-Regular.ttf"))
        if font_id != -1:
            self.chalkboard_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.chalk_font = QFont(self.chalkboard_font_family)
            log_timestamp(f"✅ [FONT] Font-ul 'cretă' ('{self.chalkboard_font_family}') a fost încărcat cu succes.", "app")
        else:
            log_timestamp("❌ [FONT] Eroare la încărcarea font-ului 'cretă'. Se va folosi un font de sistem.", "app")
            self.chalkboard_font_family = "Arial"
            self.chalk_font = QFont("Arial")
        # --- SFÂRȘIT BLOC NOU ---

        # ⭐ DEBUG FINAL: Rezumat dimensiuni
        if LOG_CONFIG.get("ui_debug", False):
            window_geom = self.geometry()
            log_timestamp("="*60, "ui_debug")
            log_timestamp("🔍 REZUMAT FINAL DIMENSIUNI", "ui_debug")
            log_timestamp("="*60, "ui_debug")
            log_timestamp(f"  - Geometrie Fereastră: {window_geom.x()},{window_geom.y()} {window_geom.width()}x{window_geom.height()}", "ui_debug")
            log_timestamp(f"  - Dimensiune Scenă: {self.scene_container.width()}x{self.scene_container.height()}", "ui_debug")
            log_timestamp(f"  - Ecran Disponibil: {self.dpi_scaler.screen_width}x{self.dpi_scaler.screen_height}", "ui_debug")
            log_timestamp(f"  - Factor Scalare: {self.dpi_scaler.scale_factor}", "ui_debug")
            log_timestamp("  ---------------------------", "ui_debug")
            log_timestamp("  🧮 VERIFICARE ÎNCADRARE:", "ui_debug")
            log_timestamp(f"     - Fereastra în Ecran: {window_geom.width() <= self.dpi_scaler.screen_width} (L), {window_geom.height() <= self.dpi_scaler.screen_height} (Î)", "ui_debug")
            log_timestamp(f"     - Scena în Fereastră: {self.scene_container.width() <= window_geom.width()} (L), {self.scene_container.height() <= window_geom.height()} (Î)", "ui_debug")
            log_timestamp("="*60, "ui_debug")

        log_timestamp("✅ [APP INIT] Inițializare completă. Aplicația este gata.")

    def _load_family_data(self):
        """Încarcă datele familiei din family.json."""
        self.family_data = []
        family_file_path = paths.FAMILY_FILE   # în ../Data
        
        if os.path.exists(family_file_path):
            try:
                with open(family_file_path, "r", encoding="utf-8") as f:
                    self.family_data = json.load(f)
                log_timestamp(f"👨‍👩‍👧‍👦 [FAMILY LOAD] Datele familiei încărcate din family.json.", "config")
            except json.JSONDecodeError:
                log_timestamp("⚠️ [FAMILY LOAD] Eroare la citirea family.json. Fișierul ar putea fi corupt.", "config")
        else:
            log_timestamp("ℹ️ [FAMILY LOAD] Fișierul family.json nu a fost găsit. Se pornește cu o listă goală.", "config")
        
        self._populate_family_list()

    def _save_family_data(self):
        """Salvează datele curente ale familiei în family.json."""
        family_file_path = paths.FAMILY_FILE   # în ../Data
        try:
            log_timestamp(f"💾 [FAMILY SAVE] Se salvează datele familiei în: {family_file_path}", "config")
            with open(family_file_path, "w", encoding="utf-8") as f:
                json.dump(self.family_data, f, indent=2, ensure_ascii=False)
            log_timestamp("✅ [FAMILY SAVE] Salvarea family.json a reușit.", "config")
        except Exception as e:
            log_timestamp(f"❌ [FAMILY SAVE] Eroare la salvarea family.json: {e}", "config")

    def _discover_available_domains(self):
        """
        Scanează folderul curriculum/ și descoperă toate domeniile de învățare disponibile.
        (VERSIUNE FINALĂ ȘI ROBUSTĂ PENTRU PARSARE)
        """
        log_timestamp("🔍 [CURRICULUM] Scanez folderul curriculum/ pentru domenii...", "app")
        
        curriculum_path = Path(resource_path("curriculum"))
        if not curriculum_path.exists():
            log_timestamp("⚠️ [CURRICULUM] Folderul curriculum/ nu există!", "app")
            return
        
        self.available_domains = {}
        for domain_folder in curriculum_path.iterdir():
            if not domain_folder.is_dir(): continue
            
            domain_id = domain_folder.name
            curriculum_file = domain_folder / "curriculum.json"
            if not curriculum_file.exists(): continue

            try:
                with open(curriculum_file, "r", encoding="utf-8") as f:
                    domain_data = json.load(f)
                
                if not all(k in domain_data for k in ["domain_id", "domain_name", "tiers"]):
                    log_timestamp(f"⚠️ [CURRICULUM] Domeniu '{domain_id}' are curriculum.json invalid. Ignorat.", "app")
                    continue
                
                for tier_info in domain_data["tiers"]:
                    tier_id = tier_info["tier_id"]
                    tier_prompt_path = domain_folder / "prompts" / f"{tier_id}.txt"
                    
                    tier_info["questions"] = []
                    if not tier_prompt_path.exists():
                        log_timestamp(f"⚠️ [CURRICULUM] Fișier lipsă: {tier_prompt_path}", "app")
                        continue

                    with open(tier_prompt_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "=== ÎNTREBĂRI ===" not in content:
                        continue

                    questions_section = content.split("=== ÎNTREBĂRI ===")[1].strip()
                    
                    # --- NOUA LOGICĂ DE PARSARE, MULT MAI ROBUSTĂ ---
                    # Împărțim fișierul într-un bloc pentru fiecare întrebare
                    question_blocks = re.split(r'\n\d+\.\s', '\n' + questions_section)[1:]

                    for i, block in enumerate(question_blocks, 1):
                        question_data = {"id": f"q{i}"}
                        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
                        
                        task_lines = []
                        for line in lines:
                            if line.startswith("Sarcina:"):
                                task_lines.append(line.split(":", 1)[1].strip())
                            elif line.startswith("display:"):
                                question_data["display"] = line.split(":", 1)[1].strip()
                            elif line.startswith("|"):
                                question_data["correct_answers"] = [ans.strip() for ans in line[1:].split(',')]
                            elif not line.startswith("["): # Ignorăm tag-urile [verbal] etc.
                                task_lines.append(line)
                        
                        question_data["text"] = " ".join(task_lines)
                        tier_info["questions"].append(question_data)
                    # --- SFÂRȘIT LOGICĂ NOUĂ ---

                    log_timestamp(f"  -> Încărcate {len(tier_info['questions'])} întrebări pentru {domain_id}/{tier_id}", category="curriculum")

                self.available_domains[domain_id] = domain_data
                log_timestamp(f"✅ [CURRICULUM] Domeniu încărcat: '{domain_data['domain_name']}' ({domain_id})", category="curriculum")
            
            except Exception as e:
                log_timestamp(f"❌ [CURRICULUM] Eroare la încărcarea domeniului '{domain_id}': {e}", "app")
        
        log_timestamp(f"🔍 [CURRICULUM] Total domenii disponibile: {len(self.available_domains)}", "app")

    def _apply_saved_character_settings(self):
        """Aplică setările specifice personajelor (ex: limba) încărcate din config."""
        log_timestamp("⚙️ [CONFIG] Se aplică setările salvate pentru personaje...", "app")
        
        saved_code = self.config.get("rina_language_code", "en")
        
        for lang_name, lang_details in self.RINA_LANGUAGES.items():
            if lang_details["code"] == saved_code:
                rina_char = self.character_manager.get_character("rina_cat")
                if rina_char:
                    rina_char.set_language(lang_details["code"], lang_details["voice"])
                break

    def _load_slider_positions_from_config(self):
        """Setează pozițiile inițiale ale slider-elor din config."""
        self.threshold_slider.setValue(self.config["threshold"])
        self.margin_slider.setValue(self.config["margin_percent"])
        self.pause_slider.setValue(int(self.config["pause_duration"] * 10))
        self.max_speech_slider.setValue(self.config["max_speech_duration"])
        
        # ⭐ THRESHOLD VOCE ⭐
        voice_threshold = self.config.get("voice_recognition_threshold", 0.75)
        self.voice_threshold_slider.setValue(int(voice_threshold * 100))
        # ⭐ SFÂRȘIT ⭐
        
        if self.config.get("ask_pause_between_tiers", True):
            self.pause_between_tiers_combo.setCurrentText("DA - Întreabă copilul")
        else:
            self.pause_between_tiers_combo.setCurrentText("NU - Continuă automat")

    def _prompt_for_api_key(self):
        """
        Deschide o fereastră de dialog care cere utilizatorului să introducă cheia API.
        Salvează cheia într-un fișier .env nou și o returnează.
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Cheie API Necesară")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)

        # Adaugă instrucțiuni
        info_label = QLabel(
            "Bine ai venit! Pentru a putea vorbi cu personajele,\n"
            "programul are nevoie de o cheie API Google Gemini.\n\n"
            "Te rog, introdu cheia ta în câmpul de mai jos."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Adaugă câmpul de text
        key_input = QLineEdit()
        key_input.setPlaceholderText("Lipește aici cheia API (ex: AIzaSy...)")
        layout.addWidget(key_input)

        # Adaugă butonul OK
        ok_button = QPushButton("Salvează și Continuă")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)

        # Afișează dialogul și așteaptă
        if dialog.exec() == QDialog.DialogCode.Accepted:
            api_key = key_input.text().strip()
            if api_key:
                try:
                    # Salvează cheia în fișierul .env
                    with open(paths.ENV_FILE, "w") as f:
                        f.write(f"GOOGLE_API_KEY={api_key}\n")
                    log_timestamp("✅ [API KEY] Cheia a fost salvată în fișierul .env.", "app")
                    return api_key
                except Exception as e:
                    QMessageBox.critical(self, "Eroare", f"Nu am putut salva fișierul .env: {e}")
                    return None
            else:
                QMessageBox.warning(self, "Atenție", "Nu a fost introdusă nicio cheie.")
                return None
        
        # Utilizatorul a închis fereastra
        return None


# =================================================================================
# 2. Construcția Interfeței Grafice (UI)
# (Metodele care creează și populează widget-urile)
# =================================================================================


    def init_ui(self):
        log_timestamp("🎨 [UI] Construire interfață principală...")
        main_layout = QHBoxLayout(self)
        
        # --- Coloana Stângă (Control și Chat) ---
        self.tabs = QTabWidget()
        conversation_tab = QWidget()
        conv_layout = QHBoxLayout(conversation_tab)
        left_column = QVBoxLayout()
        
        # Widget-ul pentru webcam
        self.webcam_label = QLabel("Camera oprită.")
        self.webcam_label.setFixedSize(320, 240)
        self.webcam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.webcam_label.setStyleSheet("background-color: black; color: white; border: 2px solid gray;")
        
        # Crearea butoanelor
        self.conversation_button = QPushButton("🚀 Start Conversație")
        self.conversation_button.clicked.connect(self.toggle_conversation_state)
        
        self.mute_button = QPushButton("🎤 Mut")
        self.mute_button.clicked.connect(self.toggle_mute_state)
        self.mute_button.setEnabled(False)
        self.mute_button.setStyleSheet("background-color: #f0ad4e;")
        
        self.repeat_button = QPushButton("🔁 Repetă")
        self.repeat_button.clicked.connect(self.repeat_last_audio)
        self.repeat_button.setEnabled(False)
        
        # Rândul 1: butoane principale
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.addWidget(self.conversation_button)
        main_buttons_layout.addWidget(self.mute_button)
        main_buttons_layout.addWidget(self.repeat_button)
        
        # Rândul 2: buton oprire lecție
        self.exit_teacher_button = QPushButton("🛑 Oprește Lecția")
        self.exit_teacher_button.clicked.connect(self.exit_teacher_mode)
        self.exit_teacher_button.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        self.exit_teacher_button.setVisible(False)
        
        lesson_button_layout = QHBoxLayout()
        lesson_button_layout.addWidget(self.exit_teacher_button)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Apasă 'Start'...")
        self.text_input.returnPressed.connect(self.send_to_ai)
        
        # Asamblarea coloanei stângi
        left_column.addWidget(self.webcam_label, stretch=0)
        left_column.addLayout(main_buttons_layout)
        left_column.addLayout(lesson_button_layout)

        left_column.addWidget(self.chat_history, stretch=1)
        left_column.addWidget(self.text_input, stretch=0)
        
        # --- Coloana Dreaptă (Scena Vizuală) ---
        right_column = QVBoxLayout()
        self.scene_container = QWidget()
        
        # ⭐ SCALARE SCENE DIMENSIONS
        BASE_SCENE_WIDTH = 1400
        BASE_SCENE_HEIGHT = 900
        SCENE_WIDTH = self.dpi_scaler.scaled(BASE_SCENE_WIDTH)
        SCENE_HEIGHT = self.dpi_scaler.scaled(BASE_SCENE_HEIGHT)
        
        if LOG_CONFIG.get("ui_debug", False):
            log_timestamp("="*60, "ui_debug")
            log_timestamp("📐 CALCUL DIMENSIUNI CONTAINER SCENĂ", "ui_debug")
            log_timestamp("="*60, "ui_debug")
            log_timestamp(f"  - Dimensiuni de bază: {BASE_SCENE_WIDTH}x{BASE_SCENE_HEIGHT}", "ui_debug")
            log_timestamp(f"  - Factor de scalare: {self.dpi_scaler.scale_factor}", "ui_debug")
            log_timestamp(f"  - Dimensiuni scalate: {SCENE_WIDTH}x{SCENE_HEIGHT}", "ui_debug")
            log_timestamp(f"  - Calcul: {BASE_SCENE_WIDTH}/{self.dpi_scaler.scale_factor:.2f} = {SCENE_WIDTH}", "ui_debug")
            log_timestamp("="*60, "ui_debug")
        
        self.SCENE_WIDTH = SCENE_WIDTH
        self.SCENE_HEIGHT = SCENE_HEIGHT
        self.scene_container.setMinimumSize(SCENE_WIDTH, SCENE_HEIGHT)
        
        self.background_label = QLabel(self.scene_container)
        self.background_label.setGeometry(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
        
        # --- Tabla virtuală ---
        self.blackboard_labels = []
        for i in range(15):
            label = QLabel(self.scene_container) 
            label.hide()
            self.blackboard_labels.append(label)
        
        # === SISTEM CALIBRARE TABLĂ ===
        self.calibration_mode = False
        self.calibration_point = QPoint(700, 400)
        self.calibration_saved = []
        
        # ⭐ SCALARE CALIBRATION BUTTON
        cal_x = self.dpi_scaler.scaled(1050)
        cal_y = self.dpi_scaler.scaled(10)
        cal_w = self.dpi_scaler.scaled(300)
        cal_h = self.dpi_scaler.scaled(50)
        
        self.calibration_button = QPushButton("🎯 ACTIVEAZĂ CALIBRARE TABLĂ", self.scene_container)
        self.calibration_button.clicked.connect(self._activate_calibration)
        self.calibration_button.setStyleSheet("background-color: orange; font-weight: bold; font-size: 14px;")
        self.calibration_button.setGeometry(cal_x, cal_y, cal_w, cal_h)
        self.calibration_button.raise_()
        self.calibration_button.hide()  # ❌ Ascunde butonul
        #self.calibration_button.show()  # ✅ Arată butonul
        
        log_timestamp(f"Buton calibrare: ({cal_x}, {cal_y}, {cal_w}x{cal_h})", "ui_debug")
        
        right_column.addWidget(self.scene_container)
        
        # --- CREARE SISTEM SEMAFOR ---
        # ⭐ SCALARE TOATE DIMENSIUNILE SEMAFOR
        semafor_img_height = self.dpi_scaler.scaled(240)
        semafor_labels_height = self.dpi_scaler.scaled(40)
        semafor_width = self.dpi_scaler.scaled(135)
        semafor_total_height = semafor_img_height + semafor_labels_height
        semafor_x_pos = self.dpi_scaler.scaled(10)
        semafor_y_pos = self.dpi_scaler.scaled(10)
        
        log_timestamp(f"Dimensiuni semafor: {semafor_width}x{semafor_total_height} at ({semafor_x_pos}, {semafor_y_pos})", "ui_debug")
        
        self.semafor_container = QWidget(self.scene_container)
        self.semafor_container.setGeometry(semafor_x_pos, semafor_y_pos, semafor_width, semafor_total_height)
        
        self.semafor_bg_label = QLabel(self.semafor_container)
        # ⭐ SCALEAZĂ PIXMAP-ul!
        semafor_pixmap = QPixmap(resource_path("assets/ui/semafor_fundal.png"))
        scaled_semafor = semafor_pixmap.scaled(
            semafor_width, 
            semafor_img_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.semafor_bg_label.setPixmap(scaled_semafor)
        self.semafor_bg_label.setGeometry(0, 0, semafor_width, semafor_img_height)

        log_timestamp(f"Fundal semafor scalat: {semafor_pixmap.width()}x{semafor_pixmap.height()} -> {semafor_width}x{semafor_img_height}", "ui_debug")
        
        light_diameter = self.dpi_scaler.scaled(55)
        radius = light_diameter // 2
        light_x_offset = (semafor_width - light_diameter) // 2
        rosu_y_pos = self.dpi_scaler.scaled(20)
        portocaliu_y_pos = self.dpi_scaler.scaled(94)
        verde_y_pos = self.dpi_scaler.scaled(168)
        
        self.semafor_rosu_widget = QWidget(self.semafor_container)
        self.semafor_rosu_widget.setGeometry(light_x_offset, rosu_y_pos, light_diameter, light_diameter)
        self.semafor_rosu_widget.setStyleSheet(f"border-radius: {radius}px;")
        
        self.semafor_verde_widget = QWidget(self.semafor_container)
        self.semafor_verde_widget.setGeometry(light_x_offset, verde_y_pos, light_diameter, light_diameter)
        self.semafor_verde_widget.setStyleSheet(f"border-radius: {radius}px;")
        
        self.cronometru_label = QLabel(self.semafor_verde_widget)
        self.cronometru_label.setGeometry(0, 0, light_diameter, light_diameter)
        self.cronometru_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cronometru_label.setStyleSheet("background-color: transparent; color: black; font-size: 28px; font-weight: bold;")
        self.cronometru_label.hide()
        
        self.clepsidra_container = QWidget(self.semafor_container)
        self.clepsidra_container.setGeometry(light_x_offset, portocaliu_y_pos, light_diameter, light_diameter)
        
        self.clepsidra_continut = QLabel(self.clepsidra_container)
        self.clepsidra_continut.setGeometry(0, 0, light_diameter, light_diameter)
        self.clepsidra_continut.setStyleSheet(f"background-color: transparent; border-radius: {radius}px;")
        
        self.clepsidra_masca = QLabel(self.clepsidra_container)
        self.clepsidra_masca.setGeometry(0, 0, light_diameter, 0)
        self.clepsidra_masca.setStyleSheet(f"background-color: {self.CULORI_SEMAFOR['portocaliu_stins']}; border-top-left-radius: {radius}px; border-top-right-radius: {radius}px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;")
        
        self.clepsidra_contur = QLabel(self.clepsidra_container)
        self.clepsidra_contur.setGeometry(0, 0, light_diameter, light_diameter)
        self.clepsidra_contur.setStyleSheet(f"background-color: transparent; border: 2px solid #222; border-radius: {radius}px;")
        
        self.clepsidra_container.hide()

        # ⭐ PUNE FUNDALUL DEASUPRA WIDGET-URILOR COLORATE
        self.semafor_bg_label.raise_()  # Fundalul cu găuri trebuie SUS!

        self.semafor_container.hide()
        self.semafor_container.raise_()

        log_timestamp("Fundal semafor ridicat (z-order corect)", "ui_debug")

        
        self.mod_nativ_label = QLabel("NATIV", self.semafor_container)
        self.mod_nativ_label.setGeometry(0, semafor_img_height, semafor_width, 20)
        self.mod_nativ_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.mod_focus_label = QLabel("FOCUS", self.semafor_container)
        self.mod_focus_label.setGeometry(0, semafor_img_height + 20, semafor_width, 20)
        self.mod_focus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.style_mod_aprins = "color: white; font-weight: bold; font-size: 14px;"
        self.style_mod_stins = "color: #555; font-size: 14px;"
        self.mod_nativ_label.raise_()
        self.mod_focus_label.raise_()
        
        # --- SUBTITLE (jos) ---
        # ⭐ SCALARE SUBTITLE
        subtitle_width = int(SCENE_WIDTH * 0.8)
        bottom_subtitle_height = self.dpi_scaler.scaled(120)
        bottom_subtitle_x = int((SCENE_WIDTH - subtitle_width) / 2)
        bottom_subtitle_y = SCENE_HEIGHT - bottom_subtitle_height - self.dpi_scaler.scaled(20)
        
        log_timestamp(f"Poziție subtitrare: {subtitle_width}x{bottom_subtitle_height} at ({bottom_subtitle_x}, {bottom_subtitle_y})", "ui_debug")
        
        self.subtitle_scroll_area = QScrollArea(self.scene_container)
        self.subtitle_scroll_area.setGeometry(bottom_subtitle_x, bottom_subtitle_y, subtitle_width, bottom_subtitle_height)
        self.subtitle_scroll_area.setWidgetResizable(True)
        self.subtitle_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.subtitle_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.subtitle_scroll_area.setStyleSheet("QScrollArea { background: rgba(0, 0, 0, 0.5); border-radius: 10px; border: none; }")
        
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)
        self.subtitle_label.setStyleSheet("QLabel { background: transparent; color: white; padding: 10px; }")
        self.subtitle_scroll_area.setWidget(self.subtitle_label)
        self.subtitle_scroll_area.hide()
        
        # --- TRANSLATION (sus) ---
        # ⭐ SCALARE TRANSLATION
        translation_width = int(SCENE_WIDTH * 0.7)
        translation_height = self.dpi_scaler.scaled(120)
        translation_x = self.semafor_container.geometry().right() + self.dpi_scaler.scaled(20)
        translation_y = self.dpi_scaler.scaled(20)
        
        log_timestamp(f"Poziție traducere: {translation_width}x{translation_height} at ({translation_x}, {translation_y})", "ui_debug")
        
        self.translation_scroll_area = QScrollArea(self.scene_container)
        self.translation_scroll_area.setGeometry(translation_x, translation_y, translation_width, translation_height)
        self.translation_scroll_area.setWidgetResizable(True)
        self.translation_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.translation_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.translation_scroll_area.setStyleSheet("QScrollArea { background: rgba(0, 0, 0, 0.5); border-radius: 10px; border: none; }")
        
        self.translation_label = QLabel()
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.translation_label.setWordWrap(True)
        self.translation_label.setStyleSheet("QLabel { background: transparent; color: white; padding: 10px; font-size: 22px; }")
        self.translation_scroll_area.setWidget(self.translation_label)
        self.translation_scroll_area.hide()
        
        # --- Asamblare Finală ---
        conv_layout.addLayout(left_column, 0)
        conv_layout.addLayout(right_column, 1)
        
        general_tab = self.create_general_settings_tab()
        voice_tab = self.create_voice_settings_tab()
        family_tab = self.create_family_settings_tab()
        
        self.tabs.addTab(conversation_tab, "💬 Conversație")
        self.tabs.addTab(family_tab, "👨‍👩‍👧‍👦 Familie")
        self.tabs.addTab(general_tab, "⚙️ Setări Generale")
        self.tabs.addTab(voice_tab, "🎤 Setări Voce")
        
        main_layout.addWidget(self.tabs)
        
        log_timestamp("🎨 [UI] Interfață construită.")
        
        # ⭐⭐⭐ DEBUGGING COMPLET DIMENSIUNI ⭐⭐⭐
        if LOG_CONFIG.get("ui_debug", False):
            QApplication.processEvents()
            
            log_timestamp("="*80, "ui_debug")
            log_timestamp("🔍 ANALIZĂ COMPLETĂ DIMENSIUNI DUPĂ CONSTRUIRE UI", "ui_debug")
            log_timestamp("="*80, "ui_debug")
            
            window_geom = self.geometry()
            log_timestamp(f"  1️⃣  FEREASTRĂ PRINCIPALĂ: x={window_geom.x()}, y={window_geom.y()}, w={window_geom.width()}, h={window_geom.height()}", "ui_debug")
            
            scene_geom = self.scene_container.geometry()
            log_timestamp(f"  2️⃣  CONTAINER SCENĂ:  x={scene_geom.x()}, y={scene_geom.y()}, w={scene_geom.width()}, h={scene_geom.height()} (Setat: {self.SCENE_WIDTH}x{self.SCENE_HEIGHT})", "ui_debug")
            
            bg_geom = self.background_label.geometry()
            log_timestamp(f"  3️⃣  FUNDAL SCENĂ:      x={bg_geom.x()}, y={bg_geom.y()}, w={bg_geom.width()}, h={bg_geom.height()}", "ui_debug")
            
            sem_geom = self.semafor_container.geometry()
            log_timestamp(f"  4️⃣  SEMAFOR:          x={sem_geom.x()}, y={sem_geom.y()}, w={sem_geom.width()}, h={sem_geom.height()}", "ui_debug")
            
            sub_geom = self.subtitle_scroll_area.geometry()
            log_timestamp(f"  5️⃣  SUBTITRARE:       x={sub_geom.x()}, y={sub_geom.y()}, w={sub_geom.width()}, h={sub_geom.height()}", "ui_debug")
            
            trans_geom = self.translation_scroll_area.geometry()
            log_timestamp(f"  6️⃣  TRADUCERE:        x={trans_geom.x()}, y={trans_geom.y()}, w={trans_geom.width()}, h={trans_geom.height()}", "ui_debug")

            log_timestamp("  7️⃣  VERIFICĂRI CRITICE:", "ui_debug")
            scene_fits_window = (self.scene_container.width() <= self.width() and self.scene_container.height() <= self.height())
            log_timestamp(f"     - Scena încape în fereastră? {'DA' if scene_fits_window else 'NU'}", "ui_debug")
            
            window_fits_screen = (window_geom.width() <= self.dpi_scaler.screen_width and window_geom.height() <= self.dpi_scaler.screen_height)
            log_timestamp(f"     - Fereastra încape pe ecran? {'DA' if window_fits_screen else 'NU'}", "ui_debug")
            log_timestamp("="*80, "ui_debug")

    def create_general_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # --- BLOC COMPLET REVIZUIT: Grup pentru Modelul AI cu Buton Apply ---
        ai_group = QGroupBox("🧠 Model Inteligență Artificială")
        ai_layout = QFormLayout(ai_group)
        
        self.ai_model_combo = QComboBox()
        
        successful_models = [
            "models/gemini-2.5-flash-preview-09-2025", "models/gemini-2.5-flash-lite",
            "models/gemini-2.5-flash-lite-preview-09-2025", "models/gemini-flash-latest",
            "models/gemini-2.5-flash-lite-preview-06-17", "models/gemini-2.5-flash-image-preview",
            "models/gemini-flash-lite-latest", "models/gemini-2.5-flash-image",
            "models/gemma-3-27b-it", "models/gemini-2.0-flash-exp",
            "models/gemma-3n-e2b-it", "models/gemma-3n-e4b-it",
            "models/gemini-2.0-flash-thinking-exp-1219", "models/gemini-2.5-flash-preview-05-20",
            "models/gemma-3-1b-it", "models/gemini-2.0-flash-thinking-exp-01-21",
            "models/gemini-2.5-flash", "models/gemma-3-4b-it", "models/gemma-3-12b-it",
            "models/gemini-2.0-flash-lite-001", "models/gemini-2.0-flash-lite-preview-02-05",
            "models/gemini-2.0-flash-lite", "models/gemini-robotics-er-1.5-preview",
            "models/gemini-2.0-flash-thinking-exp", "models/gemini-2.5-pro",
            "models/gemini-pro-latest", "models/gemini-2.5-pro-preview-05-06",
            "models/gemini-2.0-flash-lite-preview", "models/gemini-2.5-pro-preview-06-05",
            "models/gemini-2.0-flash-001", "models/gemini-2.5-pro-preview-03-25",
            "models/gemini-2.0-flash", "models/learnlm-2.0-flash-experimental"
        ]
        self.ai_model_combo.addItems(successful_models)
        
        # Conectăm schimbarea la o funcție care activează butonul
        self.ai_model_combo.currentTextChanged.connect(self.on_settings_changed)
        
        ai_layout.addRow("Selectează Model:", self.ai_model_combo)

        # Creăm butonul Apply, inițial dezactivat
        self.apply_button = QPushButton("✅ Apply Changes")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.apply_general_settings)
        ai_layout.addRow(self.apply_button)
        
        layout.addWidget(ai_group)
        # --- SFÂRȘIT BLOC REVIZUIT ---

        # --- Grup pentru Furnizor Voce ---
        tts_group = QGroupBox("🎙️ Furnizor Voce (TTS)")
        tts_layout = QFormLayout(tts_group)
        self.tts_provider_combo = QComboBox()
        self.tts_provider_combo.addItems(["Microsoft Edge (Rapid și Gratuit)", "Google Cloud (Calitate Superioară)"])
        self.tts_provider_combo.currentTextChanged.connect(self.on_tts_provider_changed)
        tts_layout.addRow("Serviciu TTS:", self.tts_provider_combo)
        layout.addWidget(tts_group)

        # --- Grup pentru Limba Personajelor ---
        lang_group = QGroupBox("🌍 Limba Personajelor")
        lang_layout = QFormLayout(lang_group)
        self.rina_language_combo = QComboBox()
        self.rina_language_combo.addItems(self.RINA_LANGUAGES.keys())
        self.rina_language_combo.currentTextChanged.connect(self.on_rina_language_changed)
        lang_layout.addRow("Limba pentru Rina:", self.rina_language_combo)
        layout.addWidget(lang_group)

        # --- Grup pentru Subtitrări ---
        subtitle_group = QGroupBox("📝 Setări Subtitrări")
        subtitle_layout = QFormLayout(subtitle_group)
        
        # --- BLOC NOU: Meniu Dropdown pentru Mod Subtitrare ---
        self.subtitle_mode_combo = QComboBox()
        self.subtitle_mode_combo.addItems(["Original", "Latin (Fonetic)", "Combinat"])
        self.subtitle_mode_combo.currentTextChanged.connect(self.on_subtitle_mode_changed)
        subtitle_layout.addRow("Mod afișare subtitrare:", self.subtitle_mode_combo)
        # --- SFÂRȘIT BLOC NOU ---
        
        self.subtitle_font_slider = QSlider(Qt.Orientation.Horizontal)
        self.subtitle_font_slider.setRange(18, 40)
        self.subtitle_font_slider.valueChanged.connect(self.on_subtitle_font_size_changed)
        self.subtitle_font_label = QLabel()
        subtitle_layout.addRow("Mărime font:", self.subtitle_font_slider)
        subtitle_layout.addRow(self.subtitle_font_label)
        layout.addWidget(subtitle_group)

        learning_group = QGroupBox("📚 Setări Învățare")
        learning_layout = QFormLayout(learning_group)
        
        self.pause_between_tiers_combo = QComboBox()
        self.pause_between_tiers_combo.addItems(["DA - Întreabă copilul", "NU - Continuă automat"])
        self.pause_between_tiers_combo.currentTextChanged.connect(self.on_pause_between_tiers_changed)
        learning_layout.addRow("Pauză de gândire după nivel:", self.pause_between_tiers_combo)
        
        pause_info_label = QLabel("💡 Dacă alegi 'NU', Cucuvel va trece automat la următorul nivel fără să întrebe.")
        pause_info_label.setStyleSheet("font-size: 10px; color: #666; font-style: italic;")
        pause_info_label.setWordWrap(True)
        learning_layout.addWidget(pause_info_label)
        
        layout.addWidget(learning_group)
        
        layout.addStretch()
        return widget

    def create_family_settings_tab(self):
        """
        Tab-ul pentru gestionarea membrilor familiei și a progresului lor de învățare.
        """
        widget = QWidget()
        main_layout = QHBoxLayout()
        widget.setLayout(main_layout)

        # --- Coloana Stângă: Lista de Membri și Butoane ---
        left_panel = QVBoxLayout()
        members_group = QGroupBox("Membrii Familiei")
        
        self.family_list_widget = QListWidget()
        self.family_list_widget.setMaximumHeight(200) # ⭐ LIMITĂM ÎNĂLȚIMEA LISTEI
        self.family_list_widget.currentItemChanged.connect(self.on_family_member_selected)
        
        buttons_layout = QHBoxLayout()
        self.add_member_button = QPushButton("+ Adaugă")
        self.remove_member_button = QPushButton("- Șterge")
        self.add_member_button.clicked.connect(self.add_new_family_member)
        self.remove_member_button.clicked.connect(self.remove_selected_family_member)
        buttons_layout.addWidget(self.add_member_button)
        buttons_layout.addWidget(self.remove_member_button)

        left_panel.addWidget(self.family_list_widget)
        left_panel.addLayout(buttons_layout)
        
        left_panel.addStretch() 

        members_group.setLayout(left_panel)

        # --- Coloana Dreaptă: Split în 2 secțiuni ---
        right_panel = QVBoxLayout()
        
        # === SECȚIUNEA 1: Detalii Membru (ca înainte) ===
        self.form_group = QGroupBox("Detalii Membru")
        form_layout = QFormLayout()

        self.member_name_edit = QLineEdit()
        self.member_role_combo = QComboBox()
        self.member_role_combo.addItems(["", "Tata", "Mama", "Copil", "Bunic", "Bunica", "Unchi", "Mătușă", "Alt Adult", "Animal de companie"])
        
        self.member_age_label = QLabel("Vârstă:")
        self.member_age_spinbox = QSpinBox()
        self.member_age_spinbox.setRange(0, 120)

        self.member_level_label = QLabel("Nivel (Copil):")
        self.member_level_spinbox = QSpinBox()
        self.member_level_spinbox.setRange(1, 10)

        self.member_pet_type_label = QLabel("Tip Animal:")
        self.member_pet_type_edit = QLineEdit()

        self.member_description_edit = QTextEdit()
        self.member_description_edit.setMaximumHeight(60) # ⭐ LIMITĂM ÎNĂLȚIMEA CÂMPULUI DE TEXT
        self.member_description_edit.setPlaceholderText("Ex: poartă ochelari, are părul lung și roșcat, este un câine auriu...")

        self.save_member_button = QPushButton("💾 Salvează Modificările")
        self.save_member_button.clicked.connect(self.save_family_member_details)
        
        form_layout.addRow("Nume:", self.member_name_edit)
        form_layout.addRow("Rol:", self.member_role_combo)
        form_layout.addRow(self.member_age_label, self.member_age_spinbox)
        form_layout.addRow(self.member_level_label, self.member_level_spinbox)
        form_layout.addRow(self.member_pet_type_label, self.member_pet_type_edit)
        form_layout.addRow("Semne Distinctive:", self.member_description_edit)

        # ⭐ PROFIL VOCAL ⭐
        voice_profile_layout = QVBoxLayout()
        
        self.voice_status_label = QLabel("❌ Voce neînregistrată")
        self.voice_status_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        
        voice_buttons_layout = QHBoxLayout()
        self.record_voice_button = QPushButton("🎤 Înregistrează Vocea")
        self.delete_voice_button = QPushButton("🗑️ Șterge Profil")
        self.record_voice_button.clicked.connect(self.open_voice_training_dialog)
        self.delete_voice_button.clicked.connect(self.delete_voice_profile)
        self.delete_voice_button.setVisible(False)
        
        voice_buttons_layout.addWidget(self.record_voice_button)
        voice_buttons_layout.addWidget(self.delete_voice_button)
        
        voice_profile_layout.addWidget(self.voice_status_label)
        voice_profile_layout.addLayout(voice_buttons_layout)
        
        form_layout.addRow("📊 Profil Vocal:", voice_profile_layout)
        # ⭐ SFÂRȘIT PROFIL VOCAL ⭐
        
        self.form_group.setLayout(form_layout)
        
        right_panel.addWidget(self.form_group)
        right_panel.addWidget(self.save_member_button)
        
        # === SECȚIUNEA 2: Progres Învățare (MODIFICATĂ) ===
        self.learning_progress_group = QGroupBox("📚 Progres Învățare")
        learning_layout = QHBoxLayout()
        
        # --- Panoul Stâng: Lista Domeniilor ---
        domains_panel = QVBoxLayout()
        domains_label = QLabel("Domenii Active:")
        self.domains_list_widget = QListWidget()
        self.domains_list_widget.setMaximumHeight(150) # ⭐ LIMITĂM ÎNĂLȚIMEA LISTEI
        self.domains_list_widget.currentItemChanged.connect(self.on_domain_selected)
        
        domain_buttons_layout = QHBoxLayout()
        self.add_domain_button = QPushButton("+ Adaugă Domeniu")
        self.remove_domain_button = QPushButton("- Șterge Domeniu")
        self.add_domain_button.clicked.connect(self.add_domain_to_member)
        self.remove_domain_button.clicked.connect(self.remove_domain_from_member)
        domain_buttons_layout.addWidget(self.add_domain_button)
        domain_buttons_layout.addWidget(self.remove_domain_button)
        
        domains_panel.addWidget(domains_label)
        domains_panel.addWidget(self.domains_list_widget)
        domains_panel.addLayout(domain_buttons_layout)
        
        # --- Panoul Drept: Detalii Domeniu ---
        details_panel = QVBoxLayout()
        
        tier_label = QLabel("Tier Curent:")
        self.tier_combo = QComboBox()
        self.tier_combo.currentTextChanged.connect(self.on_tier_changed_manually)
        
        progress_label = QLabel("Progres în Tier:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m întrebări")
        
        self.reset_tier_button = QPushButton("🔄 Resetează Tot Tier-ul")
        self.reset_tier_button.clicked.connect(self.reset_current_tier)
        
        self.prev_q_button = QPushButton("⏪ Întrebarea Anterioară")
        self.prev_q_button.clicked.connect(self._go_to_prev_question)
        
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.addWidget(self.prev_q_button)
        bottom_buttons_layout.addWidget(self.reset_tier_button)
        
        details_panel.addWidget(tier_label)
        details_panel.addWidget(self.tier_combo)
        details_panel.addWidget(progress_label)
        details_panel.addWidget(self.progress_bar)
        details_panel.addLayout(bottom_buttons_layout)
        details_panel.addStretch()
        
        learning_layout.addLayout(domains_panel, 1)
        learning_layout.addLayout(details_panel, 1)
        self.learning_progress_group.setLayout(learning_layout)
        
        right_panel.addWidget(self.learning_progress_group)
        right_panel.addStretch() # ⭐ ADAUGĂ UN SPAȚIU ELASTIC LA FINALUL COLOANEI DREPTE

        self.member_role_combo.currentTextChanged.connect(self.on_member_role_changed)
        
        # 1. Creăm un layout dedicat pentru coloana din stânga
        left_column_layout = QVBoxLayout()
        
        # 2. Adăugăm grupul de membri la acest layout
        left_column_layout.addWidget(members_group)
        
        # 3. Adăugăm spațiul elastic DUPĂ grup
        left_column_layout.addStretch()
        
        # 4. Adăugăm LA main_layout coloana din stânga și coloana din dreapta
        main_layout.addLayout(left_column_layout, 1)
        main_layout.addLayout(right_panel, 2)
        # ====================================================================

        # Dezactivăm formularele la început
        self.form_group.setEnabled(False)
        self.save_member_button.setEnabled(False)
        self.learning_progress_group.setEnabled(False)
        
        return widget

    def create_voice_settings_tab(self):
        # 1. Widget-ul principal și layout-ul orizontal (pe 2 coloane)
        widget = QWidget()
        main_layout = QHBoxLayout(widget)

        # 2. Creează layout-urile pentru fiecare coloană
        left_column_layout = QVBoxLayout()
        right_column_layout = QVBoxLayout()

        # ====================================================================
        # CREAREA TUTUROR GRUPURILOR DE SETĂRI (CODUL TĂU ORIGINAL)
        # ====================================================================
        
        # --- Grupul 1: Setări Automate ---
        auto_settings_group = QGroupBox("🎛️ Setări Automate")
        auto_layout = QVBoxLayout()
        
        self.auto_calibrate_checkbox = QCheckBox("🔄 Calibrare automată la pornirea microfonului")
        self.auto_calibrate_checkbox.setChecked(self.config["auto_calibrate_on_mic_start"])
        self.auto_calibrate_checkbox.stateChanged.connect(self.on_auto_calibrate_changed)
        auto_layout.addWidget(self.auto_calibrate_checkbox)
        
        self.auto_start_mic_checkbox = QCheckBox("🎤 Pornește microfonul automat la Start Conversație")
        self.auto_start_mic_checkbox.setChecked(self.config["auto_start_mic_with_conversation"])
        self.auto_start_mic_checkbox.stateChanged.connect(self.on_auto_start_mic_changed)
        auto_layout.addWidget(self.auto_start_mic_checkbox)
        
        self.no_camera_checkbox = QCheckBox("📵 Conversație fără cameră (doar text/voce)")
        self.no_camera_checkbox.setChecked(self.config["conversation_without_camera"])
        self.no_camera_checkbox.stateChanged.connect(self.on_no_camera_changed)
        auto_layout.addWidget(self.no_camera_checkbox)

        self.echo_cancellation_checkbox = QCheckBox("🔇 Anulează ecoul vocii personajelor (Recomandat)")
        self.echo_cancellation_checkbox.setToolTip(
            "Când este activat, sistemul va ignora sunetele care seamănă\n"
            "cu ultimul răspuns al personajului, prevenind buclele de răspuns.\n"
            "Dezactivați pentru jocuri cu răspunsuri repetitive (ex: da/nu)."
        )
        self.echo_cancellation_checkbox.stateChanged.connect(self.on_echo_cancellation_changed)
        auto_layout.addWidget(self.echo_cancellation_checkbox)
        
        info_label = QLabel("💡 Modul fără cameră: AI-ul nu va analiza imagini, doar răspunde la întrebări.")
        info_label.setStyleSheet("font-size: 10px; color: #666; font-style: italic; padding-left: 20px;")
        info_label.setWordWrap(True)
        auto_layout.addWidget(info_label)
        
        auto_settings_group.setLayout(auto_layout)
        
        # --- Grupul 2: Control Microfon ---
        control_group = QGroupBox("🎤 Control Microfon")
        control_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.voice_toggle_btn = QPushButton("🟢 Activează Microfon")
        self.voice_toggle_btn.setStyleSheet("background-color: #5cb85c; font-size: 14px; padding: 10px;")
        self.voice_toggle_btn.clicked.connect(self.toggle_voice)
        btn_layout.addWidget(self.voice_toggle_btn)
        
        control_layout.addLayout(btn_layout)
        
        self.voice_status_label = QLabel("⚪ Microfon oprit")
        self.voice_status_label.setStyleSheet("font-size: 14px; padding: 5px;")
        control_layout.addWidget(self.voice_status_label)
        
        control_group.setLayout(control_layout)
        
        # --- Grupul 3: Nivel Audio Live ---
        audio_group = QGroupBox("📈 Nivel Audio Live")
        audio_layout = QVBoxLayout()
        
        self.audio_meter = QProgressBar()
        self.audio_meter.setRange(0, 10000)
        self.audio_meter.setValue(0)
        self.audio_meter.setTextVisible(True)
        self.audio_meter.setFormat("Nivel: %v / 10000")
        self.audio_meter.setMinimumHeight(30)
        audio_layout.addWidget(self.audio_meter)
        
        self.threshold_indicator = QLabel("Threshold: 400")
        self.threshold_indicator.setStyleSheet("font-size: 12px; font-weight: bold; color: #d9534f;")
        audio_layout.addWidget(self.threshold_indicator)
        
        audio_group.setLayout(audio_layout)
        
        # --- Grupul 4: Setări Detectare ---
        threshold_group = QGroupBox("🎚️ Setări Detectare")
        threshold_layout = QFormLayout()
        
        threshold_container = QVBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(200, 10000)
        self.threshold_slider.setValue(400)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(1000)
        self.threshold_slider.setMinimumHeight(50)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        threshold_container.addWidget(self.threshold_slider)
        threshold_labels_layout = QHBoxLayout()
        threshold_labels_layout.setContentsMargins(0, 0, 0, 0)
        gradation_values = [200, 2000, 4000, 6000, 8000, 10000]
        for val in gradation_values:
            label = QLabel(str(val))
            label.setStyleSheet("font-size: 9px; color: #666;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            threshold_labels_layout.addWidget(label)
        threshold_container.addLayout(threshold_labels_layout)
        self.threshold_label = QLabel("400")
        self.threshold_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #d9534f;")
        self.threshold_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold_layout.addRow("Threshold Detectare:", threshold_container)
        threshold_layout.addRow("Valoare Curentă:", self.threshold_label)
        
        margin_container = QVBoxLayout()
        self.margin_slider = QSlider(Qt.Orientation.Horizontal)
        self.margin_slider.setRange(0, 50)
        self.margin_slider.setValue(20)
        self.margin_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.margin_slider.setTickInterval(10)
        self.margin_slider.setMinimumHeight(40)
        self.margin_slider.valueChanged.connect(self.on_margin_changed)
        margin_container.addWidget(self.margin_slider)
        margin_labels_layout = QHBoxLayout()
        for val in [0, 10, 20, 30, 40, 50]:
            label = QLabel(f"{val}%")
            label.setStyleSheet("font-size: 9px; color: #666;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            margin_labels_layout.addWidget(label)
        margin_container.addLayout(margin_labels_layout)
        self.margin_label = QLabel("+20%")
        self.margin_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f0ad4e;")
        self.margin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold_layout.addRow("Marjă Siguranță:", margin_container)
        threshold_layout.addRow("", self.margin_label)
        
        pause_container = QVBoxLayout()
        self.pause_slider = QSlider(Qt.Orientation.Horizontal)
        self.pause_slider.setRange(5, 30)
        self.pause_slider.setValue(8)
        self.pause_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.pause_slider.setTickInterval(5)
        self.pause_slider.setMinimumHeight(40)
        self.pause_slider.valueChanged.connect(self.on_pause_changed)
        pause_container.addWidget(self.pause_slider)
        pause_labels_layout = QHBoxLayout()
        for val in [5, 10, 15, 20, 25, 30]:
            label = QLabel(f"{val/10:.1f}s")
            label.setStyleSheet("font-size: 9px; color: #666;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pause_labels_layout.addWidget(label)
        pause_container.addLayout(pause_labels_layout)
        self.pause_label = QLabel("0.8 sec")
        self.pause_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #5bc0de;")
        self.pause_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold_layout.addRow("Durată Pauză:", pause_container)
        threshold_layout.addRow("", self.pause_label)

        max_speech_container = QVBoxLayout()
        self.max_speech_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_speech_slider.setRange(10, 30)
        self.max_speech_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.max_speech_slider.setTickInterval(5)
        self.max_speech_slider.setMinimumHeight(40)
        self.max_speech_slider.valueChanged.connect(self.on_max_speech_changed)
        max_speech_container.addWidget(self.max_speech_slider)
        max_speech_labels_layout = QHBoxLayout()
        for val in [10, 15, 20, 25, 30]:
            label = QLabel(f"{val}s")
            label.setStyleSheet("font-size: 9px; color: #666;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            max_speech_labels_layout.addWidget(label)
        max_speech_container.addLayout(max_speech_labels_layout)
        self.max_speech_label = QLabel("15 sec")
        self.max_speech_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #337ab7;")
        self.max_speech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold_layout.addRow("Durată Max. Segment:", max_speech_container)
        threshold_layout.addRow("", self.max_speech_label)
        
        threshold_group.setLayout(threshold_layout)
        
        # --- Grupul 5: Setări Recunoaștere Voce ---
        voice_recog_group = QGroupBox("🎤 Setări Recunoaștere Voce")
        voice_recog_layout = QFormLayout()
        
        self.enable_speaker_id_checkbox = QCheckBox("Activare Identificare Vorbitor")
        self.enable_speaker_id_checkbox.setToolTip(
            "Când este activat, sistemul încearcă să identifice cine vorbește pe baza profilului vocal.\n"
            "Dezactivarea poate reduce timpul de procesare după ce termini de vorbit."
        )
        self.enable_speaker_id_checkbox.stateChanged.connect(self.on_enable_speaker_id_changed)
        voice_recog_layout.addRow(self.enable_speaker_id_checkbox)
        
        voice_threshold_container = QVBoxLayout()
        
        self.voice_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.voice_threshold_slider.setRange(1, 95)  # <-- ⭐ MODIFICARE AICI: Începe de la 1%
        self.voice_threshold_slider.setValue(75)  # Lasăm valoarea default tot la 75%
        self.voice_threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.voice_threshold_slider.setTickInterval(5)
        self.voice_threshold_slider.setMinimumHeight(40)
        self.voice_threshold_slider.valueChanged.connect(self.on_voice_threshold_changed)
        voice_threshold_container.addWidget(self.voice_threshold_slider)
        voice_threshold_labels_layout = QHBoxLayout()
        for val in [10, 30, 50, 70, 90]: 
            label = QLabel(f"{val}%")
            label.setStyleSheet("font-size: 9px; color: #666;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            voice_threshold_labels_layout.addWidget(label)
        voice_threshold_container.addLayout(voice_threshold_labels_layout)
        self.voice_threshold_label = QLabel("75%")
        self.voice_threshold_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #5cb85c;")
        self.voice_threshold_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_label_recog = QLabel("Similitudine minimă pentru identificare voce")
        info_label_recog.setStyleSheet("font-size: 11px; color: #666; font-style: italic;")
        
        voice_recog_layout.addRow("Threshold Recunoaștere:", voice_threshold_container)
        voice_recog_layout.addRow("Valoare Curentă:", self.voice_threshold_label)
        voice_recog_layout.addRow("", info_label_recog)
        
        voice_recog_group.setLayout(voice_recog_layout)

        # ====================================================================
        # DISTRIBUIREA GRUPURILOR ÎN CELE DOUĂ COLOANE
        # ====================================================================
        
        # --- Coloana din Stânga ---
        left_column_layout.addWidget(auto_settings_group)
        left_column_layout.addWidget(control_group)
        left_column_layout.addWidget(audio_group)
        left_column_layout.addWidget(voice_recog_group)
        left_column_layout.addStretch() # Adaugă un spațiu elastic la final

        # --- Coloana din Dreapta ---
        right_column_layout.addWidget(threshold_group)
        right_column_layout.addStretch() # Adaugă un spațiu elastic la final

        # ====================================================================
        # ADAUGAREA COLOANELOR LA LAYOUT-UL PRINCIPAL
        # ====================================================================
        main_layout.addLayout(left_column_layout, 1) # Coloana stângă este mai îngustă
        main_layout.addLayout(right_column_layout, 2) # Coloana dreaptă este mai lată

        return widget


# =================================================================================
# 3. Ciclul de Viață al Aplicației și Evenimente de Bază
# (Pornire, oprire, închidere, actualizare UI generală)
# =================================================================================


    def toggle_conversation_state(self):
        if self.conversation_state == 'INACTIVE':
            self.conversation_state = 'ACTIVE'
            log_timestamp("=" * 70)
            log_timestamp("💬 [APP] === CONVERSAȚIE ACTIVATĂ ===")
            
            # ⭐ Creează fișier nou de log ⭐
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.conversation_log_filename_base = f"conversatie_{timestamp}"  # ⭐ Salvăm basename
            log_filename = self.conversation_logs_folder / f"{self.conversation_log_filename_base}.txt"
            self.conversation_log_file = open(log_filename, "w", encoding="utf-8")
            self.conversation_log_file.write(f"=== CONVERSAȚIE ÎNCEPUTĂ: {timestamp} ===\n\n")
            log_timestamp(f"📝 [LOG] Fișier creat: {log_filename}")
            
            log_timestamp("🧠 [MEMORIE] Se resetează memoria de saluturi.")
            self.greeted_users = {}
            
            # NOU: Resetăm și jurnalul conversației
            log_timestamp("📓 [LOG] Se resetează jurnalul conversației.")
            self.conversation_log = []

            self._start_idle_animations() # "Trezește" personajele

            if not self.config["conversation_without_camera"]:
                self.start_webcam()
            if self.config["auto_start_mic_with_conversation"] and not self.voice_enabled:
                QTimer.singleShot(200, self.toggle_voice)
            
        else: # Când se apasă "Oprește Conversație"
            self.conversation_state = 'INACTIVE'
            log_timestamp("=" * 70)
            log_timestamp("💬 [APP] === CONVERSAȚIE DEZACTIVATĂ ===")
            
            # ⭐ Închide fișierul de log ⭐
            if self.conversation_log_file and not self.conversation_log_file.closed:
                self.conversation_log_file.write(f"\n=== CONVERSAȚIE TERMINATĂ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                self.conversation_log_file.close()
                log_timestamp("📝 [LOG] Fișier închis")
            
            # --- BLOC NOU DE ADĂUGAT ---
            # Oprește microfonul dacă este pornit
            if self.voice_enabled:
                self.toggle_voice()
            # --- SFÂRȘIT BLOC NOU ---
            
            self.stop_webcam()
            self._stop_idle_animations() # "Adoarme" personajele
        
        self.update_ui_for_state()

    def update_ui_for_state(self):
        if self.conversation_state == 'ACTIVE':
            self.conversation_button.setText("⏹️ Oprește")
            self.conversation_button.setStyleSheet("background-color: #d9534f;")
            self.text_input.setEnabled(True)
            self.text_input.setPlaceholderText("Scrie sau vorbește...")
            self.chat_history.clear()
            self.add_to_chat("Asistent", "Salut! Sunt gata de conversație.")
        else:
            self.conversation_button.setText("🚀 Start Conversație")
            self.conversation_button.setStyleSheet("background-color: #5cb85c;")
            self.text_input.setEnabled(False)
            self.text_input.setPlaceholderText("Apasă 'Start'...")
            self.webcam_label.setText("Camera oprită.")
            self.webcam_label.setStyleSheet("background-color: black; color: white; border: 2px solid gray;")

    def closeEvent(self, event):
        log_timestamp("=" * 60)
        log_timestamp("🛑 [APP] ÎNCHIDERE APLICAȚIE...")
            
        # ⭐ SALVARE GEOMETRIE FEREASTRĂ
        geom = self.geometry()
        self.config["window_geometry"] = {
            "x": geom.x(),
            "y": geom.y(),
            "width": geom.width(),
            "height": geom.height(),
            "scale_factor": self.dpi_scaler.scale_factor
        }
        log_timestamp(f"🪟 [WINDOW] Salvez geometrie: {geom.x()}, {geom.y()}, {geom.width()}x{geom.height()}", "app")
            
        # ⭐ SALVARE CONFIG COMPLET
        save_config(self.config)
        
        # ⭐ ÎNCHIDERE LOG CONVERSAȚIE
        if hasattr(self, 'conversation_log_file') and self.conversation_log_file and not self.conversation_log_file.closed:
            self.conversation_log_file.write(f"\n=== APLICAȚIE ÎNCHISĂ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            self.conversation_log_file.close()
            log_timestamp("📝 [LOG] Fișier conversație închis")
        
        # ⭐ CLEANUP STREAMING TTS ⭐
        log_timestamp("🛑 [APP] Oprire streaming TTS...", "cleanup")
        if hasattr(self, 'streaming_tts'):
            try:
                self.streaming_tts.stop_all()
                log_timestamp("✅ [APP] Streaming TTS oprit", "cleanup")
            except Exception as e:
                log_timestamp(f"⚠️ [APP] Eroare oprire streaming TTS: {e}", "cleanup")
        
        # Oprește timer-ul de verificare pygame
        if hasattr(self, 'pygame_check_timer'):
            try:
                self.pygame_check_timer.stop()
                log_timestamp("✅ [APP] Timer verificare pygame oprit", "cleanup")
            except Exception as e:
                log_timestamp(f"⚠️ [APP] Eroare oprire pygame timer: {e}", "cleanup")
        
        # Oprește mixer-ul pygame complet
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.mixer.quit()
            log_timestamp("✅ [APP] Pygame mixer oprit", "cleanup")
        except Exception as e:
            log_timestamp(f"⚠️ [APP] Eroare oprire pygame: {e}", "cleanup")
        # ⭐ SFÂRȘIT CLEANUP STREAMING TTS ⭐
        
        self.stop_webcam()
        self.stop_continuous_voice()
            
        self.idle_timer.stop()
        self.sync_timer.stop()
        self.thinking_timer.stop()
        
        log_timestamp("🛑 [APP] Oprire animatoare...")
        for animator in self.all_animators:
            animator.stop()
            
        log_timestamp("🛑 [APP] Se așteaptă oprirea thread-urilor...")
            
        if self.webcam_thread and self.webcam_thread.isRunning():
            self.webcam_thread.quit()
            self.webcam_thread.wait(2000)
        if self.gemini_thread and self.gemini_thread.isRunning():
            self.gemini_thread.quit()
            self.gemini_thread.wait(2000)
                
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.quit()
            self.tts_thread.wait(2000)
                
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.quit()
            self.voice_thread.wait(2000)
            
        log_timestamp("✅ [APP] Închidere finalizată.")
        event.accept()

    def keyPressEvent(self, event):
        """Detectează apăsări de taste pentru calibrare."""
        if not self.calibration_mode:
            return
        
        key = event.key()
        shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        
        # Logica de mișcare a punctului de calibrare
        if shift:
            if key == Qt.Key.Key_Left: self.calibration_point.setX(self.calibration_point.x() - 50)
            elif key == Qt.Key.Key_Right: self.calibration_point.setX(self.calibration_point.x() + 50)
            elif key == Qt.Key.Key_Up: self.calibration_point.setY(self.calibration_point.y() - 50)
            elif key == Qt.Key.Key_Down: self.calibration_point.setY(self.calibration_point.y() + 50)
        elif key == Qt.Key.Key_A: self.calibration_point.setX(self.calibration_point.x() - 10)
        elif key == Qt.Key.Key_D: self.calibration_point.setX(self.calibration_point.x() + 10)
        elif key == Qt.Key.Key_W: self.calibration_point.setY(self.calibration_point.y() - 10)
        elif key == Qt.Key.Key_S: self.calibration_point.setY(self.calibration_point.y() + 10)
        elif key == Qt.Key.Key_Left: self.calibration_point.setX(self.calibration_point.x() - 1)
        elif key == Qt.Key.Key_Right: self.calibration_point.setX(self.calibration_point.x() + 1)
        elif key == Qt.Key.Key_Up: self.calibration_point.setY(self.calibration_point.y() - 1)
        elif key == Qt.Key.Key_Down: self.calibration_point.setY(self.calibration_point.y() + 1)
        
        # Logica pentru acțiuni (salvare, ieșire)
        elif key == Qt.Key.Key_Space:
            coord = (self.calibration_point.x(), self.calibration_point.y())
            self.calibration_saved.append(coord)
            log_timestamp("="*60, "app")
            log_timestamp(f"✅ COORDONATĂ CALIBRARE SALVATĂ #{len(self.calibration_saved)}", "app")
            log_timestamp(f"   - X = {coord[0]}, Y = {coord[1]}", "app")
            log_timestamp(f"   - Total salvate: {len(self.calibration_saved)}/4", "app")
            if len(self.calibration_saved) == 4:
                log_timestamp("🎉 AI TOATE CELE 4 COORDONATE!", "app")
                log_timestamp(f"   1. Stânga-Sus:   {self.calibration_saved[0]}", "app")
                log_timestamp(f"   2. Dreapta-Sus:  {self.calibration_saved[1]}", "app")
                log_timestamp(f"   3. Stânga-Jos:   {self.calibration_saved[2]}", "app")
                log_timestamp(f"   4. Dreapta-Jos:  {self.calibration_saved[3]}", "app")
            log_timestamp("="*60, "app")
        
        elif key == Qt.Key.Key_Escape:
            log_timestamp("🛑 Ieșire din modul calibrare", "app")
            self.calibration_mode = False
            self._clear_blackboard()
            return # Ieșim înainte de a actualiza display-ul
        
        # Actualizăm afișajul punctului după fiecare mișcare
        self._update_calibration_display()


# =================================================================================
# 4. SLOTS: Handler-e pentru Semnale de la Widget-uri (Butoane, Slidere, etc.)
# (Metode conectate direct la interacțiunea utilizatorului cu setările)
# =================================================================================


# --- Butoane Principale ---
    def send_to_ai(self):
        question = self.text_input.text().strip()
        if not question:
            return

        self.add_to_chat("Tu (text)", question)
        self.text_input.clear()
        
        # ⭐ NOU: User vorbește (prin text)
        self.set_speaker("user")
        
        self._route_user_input(question)

    def toggle_mute_state(self):
        """Comută starea de mute a microfonului."""
        log_timestamp("🔘 [UI] Butonul MUTE a fost apăsat.", "app")
        
        self.is_muted = not getattr(self, 'is_muted', False)
        
        if self.voice_worker:
            self.voice_worker.set_muted(self.is_muted, is_ai_speaking=False)

        if self.is_muted:
            self.mute_button.setText("🎧 Ascult")
            self.mute_button.setStyleSheet("background-color: #5cb85c;")
        else:
            self.mute_button.setText("🎤 Mut")
            self.mute_button.setStyleSheet("background-color: #f0ad4e;")

    def repeat_last_audio(self):
        """Redă ultimul fișier audio generat de AI."""
        log_timestamp("🔁 [APP] Butonul 'Repetă' a fost apăsat.", "app")
        
        if hasattr(self, 'last_audio_file_path') and self.last_audio_file_path and os.path.exists(self.last_audio_file_path) and not pygame.mixer.music.get_busy():
            
            # --- MODIFICARE AICI ---
            self._update_semafor_state('rosu') # Facem semaforul ROȘU
            
            if self.voice_worker:
                self.voice_worker.set_muted(True, is_ai_speaking=True)
            
            try:
                # Creăm un QTimer care va reactiva microfonul după ce se termină sunetul
                sound = pygame.mixer.Sound(self.last_audio_file_path)
                duration_ms = int(sound.get_length() * 1000) + 200 # Durata în ms + o marjă de siguranță
                
                QTimer.singleShot(duration_ms, self.unmute_after_repeat)
                
                # Redăm sunetul
                pygame.mixer.music.load(self.last_audio_file_path)
                pygame.mixer.music.play()
                log_timestamp(f"🔁 [APP] Se repetă: {os.path.basename(self.last_audio_file_path)} (Durată: {duration_ms / 1000.0:.2f}s)", "app")
            except Exception as e:
                log_timestamp(f"❌ [APP] Eroare la redarea fișierului de repetat: {e}", "app")
                # În caz de eroare, ne asigurăm că reactivăm microfonul
                self.unmute_after_repeat()
        else:
            log_timestamp("⚠️ [APP] Niciun fișier audio de repetat sau redare în curs.", "app")

    def unmute_after_repeat(self):
        """Funcție de callback pentru a reactiva microfonul și semaforul."""
        log_timestamp("🎤 [APP] Redarea repetată s-a încheiat. Se actualizează starea.", "mute")
        
        # --- MODIFICARE AICI ---
        # Verificăm starea Mute a utilizatorului ÎNAINTE de a decide culoarea semaforului
        if not self.is_muted:
            self._update_semafor_state('verde') # Facem semaforul VERDE
            if self.voice_worker:
                self.voice_worker.set_muted(False)
        else:
            # Dacă utilizatorul este încă pe Mute manual, semaforul rămâne ROȘU
            log_timestamp("🔇 [APP] Microfonul rămâne pe mute la cererea utilizatorului.", "mute")
            self._update_semafor_state('rosu')

    def toggle_voice(self):
        if not self.voice_enabled:
            log_timestamp("=" * 70)
            log_timestamp("🎤 [APP] === ACTIVARE MICROFON ===")
            if self.config["auto_calibrate_on_mic_start"]:
                log_timestamp("🔄 [AUTO] Se rulează calibrarea sincronă înainte de pornire...")
                self.do_calibration_sync()
            
            self.voice_enabled = True
            self.voice_toggle_btn.setText("🔴 Oprește Microfon")
            self.voice_toggle_btn.setStyleSheet("background-color: #d9534f;")
            
            self.start_continuous_voice()

            # Activăm butonul Mute
            self.mute_button.setEnabled(True) 
            
            # Afișează ÎNTREGUL grup (semafor + etichete)
            self.semafor_container.show()
            
            # Setează starea inițială/vizuală corectă la pornire
            self.on_language_lock_requested('nativ') 
            self._update_semafor_state('verde')
            log_timestamp("🚦 [SEMAFOR DEBUG] Comandă AFiȘARE semafor executată.", "semafor")
        else:
            log_timestamp("=" * 70)
            log_timestamp("🎤 [APP] === DEZACTIVARE MICROFON ===")
            self.voice_enabled = False
            self.voice_toggle_btn.setText("🟢 Activează Microfon")
            self.voice_toggle_btn.setStyleSheet("background-color: #5cb85c;")

            # Resetăm și dezactivăm butonul Mute
            self.mute_button.setEnabled(False)
            self.is_muted = False
            self.mute_button.setText("🎤 Mut")
            self.mute_button.setStyleSheet("background-color: #f0ad4e;")
            if self.voice_worker:
                self.voice_worker.set_muted(False) # Asigurăm că worker-ul nu rămâne pe mute
            
            self.stop_continuous_voice()
            
            # Ascunde ÎNTREGUL grup (semafor + etichete)
            self.semafor_container.hide()
            log_timestamp("🚦 [SEMAFOR DEBUG] Comandă ASCUNDERE semafor executată.", "semafor")


# --- Setări Generale ---
    def on_settings_changed(self):
        """Activează butonul 'Apply' dacă setările curente diferă de cele salvate."""
        current_model = self.ai_model_combo.currentText()
        
        # Comparam modelul selectat acum cu cel salvat la pornire
        if current_model != self.initial_ai_model:
            self.apply_button.setEnabled(True)
            self.apply_button.setText("✅ Apply Changes *") # Marcaj vizual
        else:
            self.apply_button.setEnabled(False)
            self.apply_button.setText("✅ Apply Changes")

    def apply_general_settings(self):
        """Salvează noile setări și resetează starea butonului."""
        log_timestamp("⚙️ [SETTINGS] Se aplică noile setări generale...", "app")
        
        # Preluăm noua valoare din ComboBox
        new_model = self.ai_model_combo.currentText()
        
        # 1. Actualizăm dicționarul din memorie
        self.config["ai_model_name"] = new_model
        
        # 2. Salvăm noua stare ca fiind cea "inițială" pentru comparații viitoare
        self.initial_ai_model = new_model
        
        # 3. Salvăm configurația completă pe disc
        save_config(self.config)
        
        # 4. Dezactivăm butonul Apply și eliminăm marcajul vizual
        self.apply_button.setEnabled(False)
        self.apply_button.setText("✅ Apply Changes")
        
        log_timestamp(f"🧠 [CONFIG] Model AI actualizat la: '{new_model}'")

    def on_ai_model_changed(self, model_name):
            """Salvează noul model AI selectat în config."""
            if model_name: # Ne asigurăm că nu este un string gol
                self.config["ai_model_name"] = model_name
                save_config(self.config)
                log_timestamp(f"🧠 [CONFIG] Model AI setat la: '{model_name}'")

    def on_tts_provider_changed(self, text):
        if "Google" in text:
            provider = "google"
        else:
            provider = "microsoft"
        
        self.config["tts_provider"] = provider
        save_config(self.config)
        log_timestamp(f"⚙️ [CONFIG] Furnizor TTS setat la: '{provider}'", "app")

    def on_rina_language_changed(self, language_name):
        """Apelată când utilizatorul selectează o nouă limbă pentru Rina."""
        if language_name not in self.RINA_LANGUAGES:
            return

        lang_details = self.RINA_LANGUAGES[language_name]
        lang_code = lang_details["code"]
        voice_id = lang_details["voice"]

        rina_char = self.character_manager.get_character("rina_cat")
        if rina_char:
            success = rina_char.set_language(lang_code, voice_id)
            if success:
                self.config["rina_language_code"] = lang_code
                save_config(self.config)
                log_timestamp(f"✅ [CONFIG] Limba pentru Rina a fost salvată: '{lang_code}'", "app")
                
                # --- BLOCUL DE RESETARE A FOST COMPLET ELIMINAT ---

    def on_subtitle_mode_changed(self, mode):
        """Salvează noul mod de subtitrare în config."""
        self.config["subtitle_mode"] = mode.lower() # salvăm ca "original", "latin (fonetic)", "combinat"
        save_config(self.config)
        log_timestamp(f"⚙️ [CONFIG] Mod subtitrare setat la: '{mode}'")

    def on_subtitle_font_size_changed(self, value):
        """Apelată când slider-ul pentru mărimea fontului este mișcat."""
        self.config["subtitle_font_size"] = value
        save_config(self.config)
        self._update_subtitle_style()
        self.subtitle_font_label.setText(f"Mărime font: {value}px")

    def on_pause_between_tiers_changed(self, text):
        """Callback când se schimbă setarea pentru pauza între tier-uri."""
        if "DA" in text:
            self.config["ask_pause_between_tiers"] = True
        else:
            self.config["ask_pause_between_tiers"] = False
        
        save_config(self.config)
        status = "activată" if self.config["ask_pause_between_tiers"] else "dezactivată"
        log_timestamp(f"⚙️ [CONFIG] Pauză între tier-uri {status}", "app")


# --- Setări Voce ---
    def on_auto_calibrate_changed(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.config["auto_calibrate_on_mic_start"] = enabled
        save_config(self.config)  # ⭐ ADAUGĂ ACEASTĂ LINIE
        log_timestamp(f"⚙️ [CONFIG] Calibrare auto: {enabled}")

    def on_auto_start_mic_changed(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.config["auto_start_mic_with_conversation"] = enabled
        save_config(self.config)  # ⭐ ADAUGĂ ACEASTĂ LINIE
        log_timestamp(f"⚙️ [CONFIG] Pornire auto microfon: {enabled}")

    def on_no_camera_changed(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.config["conversation_without_camera"] = enabled
        save_config(self.config)  # ⭐ ADAUGĂ ACEASTĂ LINIE
        log_timestamp(f"⚙️ [CONFIG] Conversație fără cameră: {enabled}")

    def on_echo_cancellation_changed(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.config["enable_echo_cancellation"] = enabled
        save_config(self.config)
        log_timestamp(f"⚙️ [CONFIG] Anulare ecou: {enabled}")
        
        if self.voice_worker:
            self.voice_worker.enable_echo_cancellation = enabled
            log_timestamp("🎤 [WORKER UPDATE] Setarea de ecou a fost actualizată în timp real.", "app")

    def on_threshold_changed(self, value):
        self.threshold = value
        self.config["threshold"] = value # Adaugă valoarea în dicționarul de config
        save_config(self.config) # Salvează pe disc
        self.threshold_label.setText(f"{value}")
        self.threshold_indicator.setText(f"Threshold: {value}")
        log_timestamp(f"🎚️ [THRESHOLD] Modificat manual și salvat: {value}")
        
    def on_margin_changed(self, value):
        self.margin_percent = value
        self.config["margin_percent"] = value
        save_config(self.config)
        self.margin_label.setText(f"+{value}%")
        log_timestamp(f"📊 [MARJĂ] Modificată și salvată: +{value}%")
        
    def on_pause_changed(self, value):
        self.pause_duration = value / 10.0
        # Atenție: salvăm valoarea brută a slider-ului (ex: 20), nu valoarea calculată (2.0)
        self.config["pause_duration"] = self.pause_duration 
        save_config(self.config)
        self.pause_label.setText(f"{self.pause_duration:.1f} sec")
        log_timestamp(f"⏱️ [PAUZĂ] Modificată și salvată: {self.pause_duration:.1f}s")

    def on_max_speech_changed(self, value):
        self.max_speech_duration = value
        self.config["max_speech_duration"] = value
        save_config(self.config)
        self.max_speech_label.setText(f"{value} sec")
        
        if self.voice_worker:
            self.voice_worker.set_max_speech_duration(value)
            
        log_timestamp(f"⏱️ [DURATĂ MAX] Modificată și salvată: {value}s")

    def on_enable_speaker_id_changed(self, state):
        """Handler pentru schimbarea stării bifei de identificare a vorbitorului."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.config["enable_speaker_identification"] = enabled
        save_config(self.config)
        log_timestamp(f"⚙️ [CONFIG] Identificare vorbitor setată la: {enabled}", "voice")
        
        # Actualizează worker-ul de voce în timp real, dacă rulează
        if self.voice_worker:
            self.voice_worker.enable_speaker_identification = enabled
            log_timestamp("🎤 [WORKER UPDATE] Setarea de Speaker ID a fost actualizată în timp real.", "voice")

    def on_voice_threshold_changed(self, value):
        """Handler pentru schimbarea threshold-ului de recunoaștere voce."""
        threshold = value / 100.0  # Convertim din procente în 0.0-1.0
        self.config["voice_recognition_threshold"] = threshold
        save_config(self.config)
        self.voice_threshold_label.setText(f"{value}%")
        log_timestamp(f"⚙️ [CONFIG] Threshold recunoaștere voce: {threshold:.2f}", "voice")
        
        # Actualizează worker-ul activ
        if self.voice_worker:
            self.voice_worker.voice_recognition_threshold = threshold
            log_timestamp("🎤 [WORKER UPDATE] Threshold recunoaștere actualizat în timp real.", "voice")


# --- Setări Familie ---
    
    def on_family_member_selected(self, current_item, previous_item):
        """
        Apelată când un membru este selectat din listă.
        Actualizează atât formularul de detalii, cât și panoul de progres învățare.
        """
        if not current_item:
            self.form_group.setEnabled(False)
            self.save_member_button.setEnabled(False)
            self.learning_progress_group.setEnabled(False)
            return

        self.form_group.setEnabled(True)
        self.save_member_button.setEnabled(True)
        self.learning_progress_group.setEnabled(True)
        
        index = current_item.data(Qt.UserRole)
        member = self.family_data[index]

        # Populăm formularul de detalii (ca înainte)
        self.member_name_edit.setText(member.get("name", ""))
        self.member_role_combo.setCurrentText(member.get("role", ""))
        self.member_age_spinbox.setValue(member.get("age", 0))
        self.member_level_spinbox.setValue(member.get("level", 1))
        self.member_pet_type_edit.setText(member.get("type", ""))
        self.member_description_edit.setPlainText(member.get("description", ""))
        
        # ⭐ UPDATE STATUS VOCE ⭐
        voice_profile = member.get("voice_profile", {})
        has_profile = voice_profile.get("has_profile", False)
        
        if has_profile:
            trained_date = voice_profile.get("trained_date", "necunoscut")
            self.voice_status_label.setText(f"✅ Voce înregistrată ({trained_date})")
            self.voice_status_label.setStyleSheet("color: #5cb85c; font-weight: bold;")
            self.delete_voice_button.setVisible(True)
            self.record_voice_button.setText("🔄 Re-înregistrează")
        else:
            self.voice_status_label.setText("❌ Voce neînregistrată")
            self.voice_status_label.setStyleSheet("color: #d9534f; font-weight: bold;")
            self.delete_voice_button.setVisible(False)
            self.record_voice_button.setText("🎤 Înregistrează Vocea")
        # ⭐ SFÂRȘIT UPDATE ⭐

        # Actualizăm vizibilitatea câmpurilor pe baza rolului
        self.on_member_role_changed(member.get("role", ""))
        
        # === NOU: Populăm panoul de progres învățare ===
        self._populate_learning_progress_panel(member)

    def on_member_role_changed(self, role):
        """Ascunde/afișează câmpurile specifice în funcție de rol."""
        is_child = (role == "Copil")
        is_pet = (role == "Animal de companie")
        is_human = not is_pet

        self.member_age_label.setVisible(is_human)
        self.member_age_spinbox.setVisible(is_human)
        
        self.member_level_label.setVisible(is_child)
        self.member_level_spinbox.setVisible(is_child)
        
        self.member_pet_type_label.setVisible(is_pet)
        self.member_pet_type_edit.setVisible(is_pet)

    def add_new_family_member(self):
        """Adaugă un nou membru gol și îl selectează."""
        new_member = {"name": "Nume Nou", "role": "", "age": 0, "level": 1, "type": "", "description": ""}
        self.family_data.append(new_member)
        self._populate_family_list()
        self.family_list_widget.setCurrentRow(len(self.family_data) - 1)

    def remove_selected_family_member(self):
        """Șterge membrul selectat curent."""
        current_item = self.family_list_widget.currentItem()
        if not current_item:
            return
            
        index = current_item.data(Qt.UserRole)
        del self.family_data[index]
        self._save_family_data()
        self._populate_family_list()

    def save_family_member_details(self):
        """Salvează detaliile din formular pentru membrul selectat."""
        current_item = self.family_list_widget.currentItem()
        if not current_item:
            return
            
        index = current_item.data(Qt.UserRole)
        
        member = self.family_data[index]
        member["name"] = self.member_name_edit.text()
        member["role"] = self.member_role_combo.currentText()
        
        if member["role"] == "Animal de companie":
            member["type"] = self.member_pet_type_edit.text()
        else:
            member["age"] = self.member_age_spinbox.value()
        
        if member["role"] == "Copil":
            member["level"] = self.member_level_spinbox.value()
            
        member["description"] = self.member_description_edit.toPlainText()
        
        self._save_family_data()
        self._populate_family_list() # Reîmprospătăm lista pentru a afișa noul nume/rol
        self.family_list_widget.setCurrentRow(index)

    def open_voice_training_dialog(self):
        """Deschide dialogul de training voce pentru membrul selectat."""
        current_item = self.family_list_widget.currentItem()
        if not current_item:
            return
        
        index = current_item.data(Qt.UserRole)
        member = self.family_data[index]
        member_name = member.get("name", "")
        
        dialog = VoiceTrainingDialog(member_name, self.voice_print_manager, self)
        if dialog.exec() == QDialog.Accepted:
            # Salvează profilul în family.json
            if "voice_profile" not in member:
                member["voice_profile"] = {}
            
            member["voice_profile"]["has_profile"] = True
            member["voice_profile"]["trained_date"] = datetime.now().strftime("%d.%m.%Y")
            
            self._save_family_data()
            
            # Reîncarcă datele în UI
            self.on_family_member_selected(current_item, None)
            
            log_timestamp(f"✅ [VOICE] Profil vocal salvat pentru {member_name}", "voice")
    
    def delete_voice_profile(self):
        """Șterge profilul vocal al membrului selectat."""
        current_item = self.family_list_widget.currentItem()
        if not current_item:
            return
        
        index = current_item.data(Qt.UserRole)
        member = self.family_data[index]
        member_name = member.get("name", "")
        
        # Confirmare
        reply = QMessageBox.question(
            self,
            "Confirmare Ștergere",
            f"Sigur vrei să ștergi profilul vocal al lui {member_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Șterge fișierul
            self.voice_print_manager.delete_voice_profile(member_name)
            
            # Șterge din JSON
            if "voice_profile" in member:
                member["voice_profile"]["has_profile"] = False
            
            self._save_family_data()
            
            # Reîncarcă UI
            self.on_family_member_selected(current_item, None)
            
            log_timestamp(f"🗑️ [VOICE] Profil vocal șters pentru {member_name}", "voice")

    def add_domain_to_member(self):
        """
        Deschide un dialog pentru a adăuga un nou domeniu de învățare pentru membrul selectat.
        """
        from PySide6.QtWidgets import QInputDialog
        
        current_item = self.family_list_widget.currentItem()
        if not current_item:
            return
        
        member_index = current_item.data(Qt.UserRole)
        member = self.family_data[member_index]
        
        # Verificăm ce domenii NU sunt deja adăugate
        existing_domains = set(member.get("learning_progress", {}).keys())
        available_to_add = []
        
        for domain_id, domain_data in self.available_domains.items():
            if domain_id not in existing_domains:
                available_to_add.append((domain_data["domain_name"], domain_id))
        
        if not available_to_add:
            log_timestamp("⚠️ [LEARNING UI] Nu există domenii noi de adăugat!", "app")
            return
        
        # Afișăm dialogul
        domain_names = [name for name, _ in available_to_add]
        selected_name, ok = QInputDialog.getItem(
            self,
            "Adaugă Domeniu de Învățare",
            f"Selectează un domeniu pentru {member.get('name')}:",
            domain_names,
            0,
            False
        )
        
        if not ok or not selected_name:
            return
        
        # Găsim domain_id-ul corespunzător
        selected_domain_id = None
        for name, domain_id in available_to_add:
            if name == selected_name:
                selected_domain_id = domain_id
                break
        
        if not selected_domain_id:
            return
        
        # Adăugăm domeniul în progresul membrului
        if "learning_progress" not in member:
            member["learning_progress"] = {}
        
        # Inițializăm cu primul tier
        domain_data = self.available_domains[selected_domain_id]
        first_tier_id = domain_data["tiers"][0]["tier_id"]
        
        member["learning_progress"][selected_domain_id] = {
            "current_tier": first_tier_id,
            "completed_questions": []
        }
        
        self._save_family_data()
        self._populate_learning_progress_panel(member)
        
        log_timestamp(f"✅ [LEARNING UI] Domeniu '{selected_name}' adăugat pentru '{member.get('name')}'", "app")

    def remove_domain_from_member(self):
        """
        Șterge domeniul selectat din progresul membrului.
        """
        current_domain_item = self.domains_list_widget.currentItem()
        if not current_domain_item:
            return
        
        current_member_item = self.family_list_widget.currentItem()
        if not current_member_item:
            return
        
        member_index = current_member_item.data(Qt.UserRole)
        member = self.family_data[member_index]
        
        domain_id = current_domain_item.data(Qt.UserRole)
        
        # Ștergem domeniul
        if "learning_progress" in member and domain_id in member["learning_progress"]:
            del member["learning_progress"][domain_id]
            self._save_family_data()
            self._populate_learning_progress_panel(member)
            
            log_timestamp(f"🗑️ [LEARNING UI] Domeniu '{domain_id}' șters pentru '{member.get('name')}'", "app")

    def on_domain_selected(self, current_item, previous_item):
        """
        Apelată când un domeniu este selectat din lista de domenii a membrului.
        Actualizează combo-ul de tier-uri și bara de progres.
        """
        if not current_item:
            self.tier_combo.clear()
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(1)
            return
        
        domain_id = current_item.data(Qt.UserRole)
        
        # Obținem membrul curent
        current_list_item = self.family_list_widget.currentItem()
        if not current_list_item:
            return
        
        member_index = current_list_item.data(Qt.UserRole)
        member = self.family_data[member_index]
        
        # Obținem datele despre domeniu
        if domain_id not in self.available_domains:
            log_timestamp(f"⚠️ [LEARNING UI] Domeniu '{domain_id}' nu mai există în sistem!", "app")
            return
        
        domain_data = self.available_domains[domain_id]
        member_progress = member.get("learning_progress", {}).get(domain_id, {})
        
        # Populăm combo-ul cu tier-urile
        self.tier_combo.blockSignals(True)  # Blocăm semnalele temporar
        self.tier_combo.clear()
        
        for tier_info in domain_data["tiers"]:
            tier_id = tier_info["tier_id"]
            tier_name = tier_info["tier_name"]
            self.tier_combo.addItem(tier_name, tier_id)
        
        # Setăm tier-ul curent al membrului
        current_tier_id = member_progress.get("current_tier", "")
        if current_tier_id:
            index = self.tier_combo.findData(current_tier_id)
            if index >= 0:
                self.tier_combo.setCurrentIndex(index)
        
        self.tier_combo.blockSignals(False)  # Reactivăm semnalele
        
        # Actualizăm bara de progres
        self._update_progress_bar_for_domain(domain_id, member)
        
        log_timestamp(f"📚 [LEARNING UI] Domeniu selectat: '{domain_data['domain_name']}', Tier curent: '{current_tier_id}'", "app")

    def on_tier_changed_manually(self, tier_name):
        """
        Apelată când utilizatorul schimbă manual tier-ul din combo box.
        Resetează automat progresul la noul tier.
        """
        if not tier_name:
            return
        
        # Verificăm dacă e o schimbare reală (nu doar populare UI)
        current_domain_item = self.domains_list_widget.currentItem()
        if not current_domain_item:
            return
        
        current_member_item = self.family_list_widget.currentItem()
        if not current_member_item:
            return
        
        domain_id = current_domain_item.data(Qt.UserRole)
        member_index = current_member_item.data(Qt.UserRole)
        member = self.family_data[member_index]
        
        new_tier_id = self.tier_combo.currentData()
        if not new_tier_id:
            return
        
        # Verificăm dacă e diferit de tier-ul curent
        current_tier_id = member.get("learning_progress", {}).get(domain_id, {}).get("current_tier", "")
        
        if new_tier_id == current_tier_id:
            return  # Nu e o schimbare reală
        
        # Actualizăm tier-ul și resetăm progresul
        if "learning_progress" not in member:
            member["learning_progress"] = {}
        
        if domain_id not in member["learning_progress"]:
            member["learning_progress"][domain_id] = {}
        
        member["learning_progress"][domain_id]["current_tier"] = new_tier_id
        member["learning_progress"][domain_id]["completed_questions"] = []
        
        self._save_family_data()
        self._update_progress_bar_for_domain(domain_id, member)
        
        log_timestamp(f"🔄 [LEARNING UI] Tier schimbat manual la '{tier_name}' pentru '{member.get('name')}'", "app")

    def reset_current_tier(self):
        """
        Resetează progresul pentru tier-ul curent al membrului.
        """
        current_domain_item = self.domains_list_widget.currentItem()
        if not current_domain_item:
            return
        
        current_member_item = self.family_list_widget.currentItem()
        if not current_member_item:
            return
        
        domain_id = current_domain_item.data(Qt.UserRole)
        member_index = current_member_item.data(Qt.UserRole)
        member = self.family_data[member_index]
        
        # Resetăm completed_questions
        if "learning_progress" in member and domain_id in member["learning_progress"]:
            member["learning_progress"][domain_id]["completed_questions"] = []
            self._save_family_data()
            self._update_progress_bar_for_domain(domain_id, member)
            
            log_timestamp(f"🔄 [LEARNING UI] Tier resetat pentru '{member.get('name')}' în domeniul '{domain_id}'", "app")

    def _go_to_prev_question(self):
        """Elimină ultima întrebare din lista de întrebări completate pentru membrul selectat."""
        member_item = self.family_list_widget.currentItem()
        domain_item = self.domains_list_widget.currentItem()
        if not member_item or not domain_item: 
            return

        member_index = member_item.data(Qt.UserRole)
        member = self.family_data[member_index]
        domain_id = domain_item.data(Qt.UserRole)
        
        progress = member.get("learning_progress", {}).get(domain_id)
        if not progress or not progress.get("completed_questions"):
            log_timestamp("INFO [UI]: Nu există nicio întrebare completată pentru a da înapoi.", "app")
            return

        # Eliminăm ultima întrebare din listă
        removed_question = progress["completed_questions"].pop()
        log_timestamp(f"UI: Întrebarea '{removed_question}' a fost eliminată din progres.", "app")
        
        self._save_family_data()
        self._update_progress_bar_for_domain(domain_id, member) # Actualizăm vizual progresul


# =================================================================================
# 5. SLOTS: Handler-e pentru Semnale de la Workeri și Manageri
# (Metode care reacționează la evenimente din background)
# =================================================================================


# --- Semnale de la Manageri ---

    def on_scene_changed(self, scene_id, scene_data):
        log_timestamp(f"🌆 [UI SCENE] Primit semnal de schimbare scenă la '{scene_id}'.", "scene")
        
        # Calea din JSON este: "Backgrounds/acasa.png"
        relative_bg_path = scene_data.get("background_image")
        
        if relative_bg_path:
            # resource_path o va transforma în D:\...\Aarici\Backgrounds\acasa.png
            bg_path = resource_path(relative_bg_path)
            
            if os.path.exists(bg_path):
                bg_pixmap = QPixmap(bg_path)
                
                if bg_pixmap.isNull():
                    log_timestamp(f"  ❌ EROARE: QPixmap nu a putut încărca imaginea de la '{bg_path}'.", "app")
                    self.background_label.clear()
                    self.background_label.setStyleSheet("background-color: red;")
                    return

                scaled_pixmap = bg_pixmap.scaled(
                    self.SCENE_WIDTH, self.SCENE_HEIGHT,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                
                self.background_label.setPixmap(scaled_pixmap)
                self.background_label.setGeometry(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
                log_timestamp(f"  ✅ Fundal actualizat: {bg_path}", "scene")
            else:
                log_timestamp(f"  ⚠️ AVERTISMENT: Imagine de fundal negăsită la '{bg_path}'", "scene")
                self.background_label.clear()
                self.background_label.setStyleSheet("background-color: darkgray;")
        else:
            log_timestamp(f"  ⚠️ AVERTISMENT: Scena '{scene_id}' nu are imagine de fundal.", "scene")
            self.background_label.clear()
            self.background_label.setStyleSheet("background-color: darkgray;")

        log_timestamp(f"  ✅ Procesare schimbare scenă finalizată în UI.", "scene")

    def on_character_added(self, character):
        """
        Slot executat când CharacterManager emite 'character_added_to_stage'.
        Creează dinamic layerele (QLabels) pentru noul personaj și stochează
        pixmap-ul original, ne-scalat, pentru fiecare layer.
        """
        log_timestamp(f"🎭 [UI CHAR] Primit semnal de adăugare personaj: '{character.display_name}'.", "character")
        if character.id in self.character_layers:
            log_timestamp(f"  ⚠️ Personajul '{character.id}' are deja layere create. Se reutilizează.", "character")
            if self.scene_manager.current_scene_id:
                scene_config = character.get_config_for_scene(self.scene_manager.current_scene_id)
                if scene_config:
                    char_layers = self.character_layers.get(character.id)
                    self._position_character_layers(character, char_layers, scene_config)
                    for layer in char_layers.values():
                        layer.show()
                else:
                    log_timestamp(f"  ⚠️ Nu are config pentru scena curentă - se ascunde", "character")
                    for layer in self.character_layers[character.id].values():
                        layer.hide()
            return

        log_timestamp(f"  🔨 Se creează layerele vizuale pentru '{character.id}' pe baza 'components'...", "character")
        
        components = character.components
        parts = components.get("parts", {})
        z_order = components.get("z_order", [])
        
        if not parts or not z_order:
            log_timestamp(f"  ❌ EROARE: 'parts' sau 'z_order' lipsesc din config.json pentru '{character.id}'!", "character")
            return

        char_layers = {}
        for part_name in z_order:
            image_file = parts.get(part_name)
            if not image_file:
                log_timestamp(f"    ⚠️ Avertisment: Numele de parte '{part_name}' din z_order nu a fost găsit în 'parts'.", "character")
                continue
                
            image_path = os.path.join(character.assets_path, image_file)
            if not os.path.exists(image_path):
                log_timestamp(f"    ⚠️ Avertisment: Asset-ul '{image_file}' lipsește pentru '{character.id}'.", "character")
                continue
                
            layer = QLabel(self.scene_container)
            layer.original_pixmap = QPixmap(image_path)
            layer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            char_layers[part_name] = layer
        
        self.character_layers[character.id] = char_layers
        log_timestamp(f"  ✅ Au fost create {len(char_layers)} layere pentru '{character.id}'.", "character")
        

        # ⭐ LINIE NOUĂ CRITICĂ - SETEAZĂ current_scene_id!
        character.current_scene_id = self.scene_manager.current_scene_id
        log_timestamp(f"  🎯 [EMOTION SETUP] Setez current_scene_id = '{self.scene_manager.current_scene_id}' pentru '{character.id}'", "emotion")


        # ⭐ SCHIMBARE CRITICĂ: SETĂM POZIȚIA ÎNAINTE DE A PORNI ANIMATOARELE!
        if self.scene_manager.current_scene_id:
            scene_config = character.get_config_for_scene(self.scene_manager.current_scene_id)
            if scene_config:
                # ⭐ 1. MAI ÎNTÂI poziționăm layerele
                self._position_character_layers(character, char_layers, scene_config)
                
                # ⭐ 2. APOI pornim animatoarele
                log_timestamp(f"🛠️ [ANIM] Asamblare animatoare pentru '{character.id}'...", "character")
                character.setup_animators(char_layers, self.dpi_scaler)  # ✅ Pasează dpi_scaler!
        
                # --- BLOC NOU DE ADĂUGAT AICI ---
                # Dacă conversația nu a început încă, punem personajul în stare de "somn"
                if self.conversation_state == 'INACTIVE':
                    log_timestamp(f"🌙 [APP INIT] Conversație inactivă. Se setează starea 'sleeping' pentru {character.id}", "app")
                    for animator in character.animators:
                        if isinstance(animator, (BreathingAnimator, BlinkingAnimator)):
                            animator.stop() # Oprim respirația și clipitul
                    
                    emotion_animator = next((anim for anim in character.animators if isinstance(anim, EmotionAnimator)), None)
                    if emotion_animator:
                        emotion_animator.set_emotion('sleeping')
                # --- SFÂRȘIT BLOC NOU ---

                # 3. Arătăm layerele
                for layer in char_layers.values():
                    layer.show()
            else:
                log_timestamp(f"  ⚠️ Nu are config pentru scena curentă - se ascunde", "character")
                for layer in char_layers.values():
                    layer.hide()

    def on_character_removed(self, character_id):
        log_timestamp(f"🎬 [UI CHAR] Primit semnal de eliminare personaj: '{character_id}'.", "character")
        
        character = self.character_manager.get_character(character_id)
        if character and character.animators:
            log_timestamp(f"🛑 [ANIM] Oprire și curățare animatoare pentru '{character_id}'...", "character")
            for animator in character.animators:
                animator.stop()
                if animator in self.all_animators:
                    self.all_animators.remove(animator)
                animator.deleteLater()
            character.animators = []

        if character_id in self.character_layers:
            for layer_widget in self.character_layers[character_id].values():
                layer_widget.deleteLater()
            del self.character_layers[character_id]


# --- Semnale de la Worker-ul de Voce ---
    def handle_voice_transcription(self, text):
        log_timestamp(f"💬 [APP] Voce primită: '{text}'", "app")
        
        # ⭐ MODIFICAT: Folosește identificarea vocii dacă există ⭐
        speaker_name = getattr(self, 'last_identified_speaker_name', None)

        confidence = getattr(self, '_last_speaker_confidence', 0.0)
        
        if speaker_name and confidence > 0:
            # Badge cu identificare
            display_name = f"{speaker_name} (voce)"
            self.add_to_chat(display_name, text, voice_identified=True, confidence=confidence)
        else:
            # Fără identificare
            self.add_to_chat("Tu (voce)", text)
        
        # Resetează pentru următorul input
        # COMENTAT: self._last_identified_speaker = None
        # COMENTAT: self._last_speaker_confidence = 0.0
        # ⭐ SFÂRȘIT MODIFICARE ⭐
        
        # User vorbește
        self.set_speaker("user")
        
        if self.conversation_state == 'ACTIVE':
            self._route_user_input(text)
 
    def handle_speaker_identification(self, speaker_name, confidence):
        """
        Handler pentru identificarea vorbitorului prin voce.
        Dacă nu recunoaște vocea, încearcă fallback cu video recognition.
        
        Args:
            speaker_name: Numele identificat sau None
            confidence: Procentul de siguranță (0.0-1.0)
        """
        if speaker_name:
            # Succes - voce identificată
            log_timestamp(f"✅ [SPEAKER ID] Voce identificată: {speaker_name} ({confidence:.2%})", "voice")
            self.last_identified_speaker_name = speaker_name
            self._last_speaker_confidence = confidence
            
            # Verifică dacă input-ul e "vreau să învăț" pentru auto-start
            # (verificarea se va face în _route_user_input când vine transcrierea)
        else:
            # Fallback la video recognition
            log_timestamp("⚠️ [SPEAKER ID] Voce necunoscută. Încerc video recognition...", "voice")
            
            # Verifică dacă avem persoane detectate în ultimul frame
            if hasattr(self, 'detected_persons') and self.detected_persons:
                if len(self.detected_persons) == 1:
                    # O singură persoană în cadru - folosim pe ea
                    person_name = self.detected_persons[0]
                    log_timestamp(f"✅ [SPEAKER ID] Fallback video: {person_name} (unic în cadru)", "voice")
                    self._last_identified_speaker = person_name
                    self._last_speaker_confidence = 0.5  # Confidence redusă pentru fallback
                else:
                    # Mai multe persoane - ambiguitate
                    log_timestamp(f"⚠️ [SPEAKER ID] Fallback video: Ambiguu - {len(self.detected_persons)} persoane în cadru", "voice")
                    # Vom întreba în _handle_learning_ambiguity dacă e "vreau să învăț"
                    self._last_identified_speaker = None
                    self._last_speaker_confidence = 0.0
            else:
                # Nicio persoană în cadru sau video disabled
                log_timestamp("⚠️ [SPEAKER ID] Fallback video: Nicio persoană detectată", "voice")
                self._last_identified_speaker = None
                self._last_speaker_confidence = 0.0

    def on_language_lock_requested(self, mode):
        """Schimbă modul de ascultare și actualizează UI-ul."""
        if self.language_lock != mode:
            self.language_lock = mode
            if self.voice_worker:
                self.voice_worker.current_lock_mode = mode
            
            if mode == 'nativ':
                log_timestamp("🔒 [LANG] Modul de ascultare blocat pe Română (NATIV).", "app")
                self.update_voice_status("🗣️ Mod NATIV (RO)")
                self.mod_nativ_label.setStyleSheet(self.style_mod_aprins)
                self.mod_focus_label.setStyleSheet(self.style_mod_stins)
                log_timestamp("🚦 [SEMAFOR DEBUG] Aplicat stil APRINS pe NATIV, STINS pe FOCUS.", "semafor")
            else: # focus
                log_timestamp("🎯 [LANG] Modul de ascultare setat pe FOCUS (Limbă Străină).", "app")
                self.update_voice_status("🗣️ Mod FOCUS")
                self.mod_nativ_label.setStyleSheet(self.style_mod_stins)
                self.mod_focus_label.setStyleSheet(self.style_mod_aprins)
                log_timestamp("🚦 [SEMAFOR DEBUG] Aplicat stil STINS pe NATIV, APRINS pe FOCUS.", "semafor")

    def update_voice_status(self, status):
        self.voice_status_label.setText(status)
        
    def update_audio_meter(self, level):
        """Actualizează nivelul audio FĂRĂ logging periodic când categoria e dezactivată"""
        self.current_audio_level = level
        display_level = int(min(max(level, 0), 10000))
        self.audio_meter.setValue(display_level)
        
        if level > self.threshold:
            self.audio_meter.setStyleSheet("QProgressBar::chunk { background-color: #5cb85c; }")
            status = "🟢 PESTE"
        else:
            self.audio_meter.setStyleSheet("QProgressBar::chunk { background-color: #f0ad4e; }")
            status = "🟡 SUB"
        
        # Logging periodic DOAR dacă categoria "audio" e activată
        if not hasattr(self, '_last_audio_log_time'):
            self._last_audio_log_time = time.time()
            
        if time.time() - self._last_audio_log_time >= 2.0:
            log_timestamp(
                f"📊 [AUDIO] Nivel: {level:.0f} | Threshold: {self.threshold} | "
                f"Status: {status} | Diferență: {level - self.threshold:+.0f}",
                "audio"  # ⭐ ADĂUGAT CATEGORIA
            )
            self._last_audio_log_time = time.time()


# --- Semnale de la Worker-ul de Webcam ---
    def update_webcam_feed(self, image):
        # Convertim QImage la QPixmap pentru a-l afișa
        pixmap = QPixmap.fromImage(image)
        self.webcam_label.setPixmap(pixmap.scaled(
            self.webcam_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))


# --- Semnale de la Worker-ii AI (Gemini) ---
    def handle_ai_response(self, response_text, speaking_character_id):
        # --- BLOC DE DEBUGGING ---
        log_timestamp("🐞 [DEBUG] PAS 1: Intrat în handle_ai_response.", "app")
        
        log_timestamp(f"✅ [APP] Răspuns AI (brut): '{response_text[:120]}...'", "app")
        
        self.subtitle_scroll_area.hide()
        self.translation_scroll_area.hide()
        
        self.stop_thinking()
        
        log_timestamp("🐞 [DEBUG] PAS 2: Obținere personaj.", "app")
        speaking_character = self.character_manager.get_character(speaking_character_id)
        if not speaking_character:
            self.speech_finished()
            return
            
        emotion = "neutral"
        original_text = ""
        translation_text = ""
        
        log_timestamp("🐞 [DEBUG] PAS 3: Se intră în blocul try...except pentru parsare JSON.", "app")
        try:
            start_index = response_text.find('{')
            end_index = response_text.rfind('}')
            if start_index != -1 and end_index != -1:
                json_string = response_text[start_index : end_index + 1]
                response_data = json.loads(json_string)
                emotion = response_data.get("emotion", "neutral")
                original_text = response_data.get("original", "")
                translation_text = response_data.get("translation", "")
                log_timestamp(f"✅ [JSON PARSE] Emoție: '{emotion}', Original: '{original_text[:50]}...'", "app")
            else:
                raise ValueError("Nu s-a găsit un obiect JSON valid în răspuns.")

        except (json.JSONDecodeError, ValueError) as e:
            log_timestamp(f"⚠️ [JSON PARSE] Eroare la parsare: {e}. Tratăm răspunsul ca text simplu.", "app")
            original_text = self._extract_and_apply_emotion(response_text, speaking_character_id)
            emotion = getattr(self, 'last_extracted_emotion', 'neutral')

        log_timestamp("🐞 [DEBUG] PAS 4: Verificare text original.", "app")
        if not original_text:
            log_timestamp("⚠️ [APP] Textul original este gol. Se anulează redarea.", "app")
            self.speech_finished()
            return

        log_timestamp("🐞 [DEBUG] PAS 5: Se aplică emoția.", "app")
        if 'response_data' in locals():
            self._apply_emotion(emotion, speaking_character_id)

        self.last_character_speeches[speaking_character_id] = original_text

        # --- BLOCUL DE ACTUALIZARE A LIMBII PENTRU FOCUS (PE CARE L-AM OMIS) ---
        if self.voice_worker:
            lang_code_map = {
                "en": "en-US", "ro": "ro-RO", "de": "de-DE",
                "fr": "fr-FR", "it": "it-IT", "es": "es-ES", "ru": "ru-RU",
                "el": "el-GR", "ja": "ja-JP", "ko": "ko-KR"
            }
            short_code = speaking_character.language.split('-')[0]
            full_code_for_stt = lang_code_map.get(short_code, "ro-RO")
            
            self.voice_worker.set_primary_language(full_code_for_stt)
            log_timestamp(f"🎤 [FOCUS] Limba de ascultare pentru Focus a fost actualizată la: '{full_code_for_stt}'.", "app")
        # --- SFÂRȘIT BLOC ---

        log_timestamp("🐞 [DEBUG] PAS 6: Se actualizează memoria de saluturi.", "app")
        if speaking_character_id not in self.greeted_users:
            self.greeted_users[speaking_character_id] = []
        
        persoane_salutate_anterior = self.greeted_users[speaking_character_id]
        nume_cunoscute = [m.get("name") for m in getattr(self, "family_data", []) if m.get("name")]
        
        for nume in nume_cunoscute:
            if nume in original_text and nume not in persoane_salutate_anterior:
                log_timestamp(f"🧠 [MEMORIE] AI l-a identificat și salutat pe '{nume}'. Se adaugă la memorie.", "memory")
                self.greeted_users[speaking_character_id].append(nume)

        self.conversation_log.append({"role": "ai", "content": original_text, "speaker_id": speaking_character_id})
        while len(self.conversation_log) > self.MAX_LOG_ENTRIES:
            self.conversation_log.pop(0)

        log_timestamp("🐞 [DEBUG] PAS 7: Se pregătesc subtitrările.", "app")

        log_timestamp("🐞 [DEBUG] PAS 7.1: Setare text_to_display_bottom", "app")
        text_to_display_bottom = original_text

        log_timestamp("🐞 [DEBUG] PAS 7.2: Check dacă e rina_cat", "app")
        if speaking_character_id == "rina_cat":
            log_timestamp("🐞 [DEBUG] PAS 7.3: E rina, citesc config", "app")
            subtitle_mode = self.config.get("subtitle_mode", "original")
            lang_code = speaking_character.language.split('-')[0]
            
            log_timestamp("🐞 [DEBUG] PAS 7.4: Check limbă specială", "app")
            if lang_code in ['el', 'ru', 'ja', 'ko']:
                log_timestamp("🐞 [DEBUG] PAS 7.5: Limbă specială detectată", "app")
                if subtitle_mode == "latin (fonetic)":
                    text_to_display_bottom = self._transliterate_text(original_text, lang_code)
                elif subtitle_mode == "combinat":
                    transliterated = self._transliterate_text(original_text, lang_code)
                    text_to_display_bottom = (f"<div style='font-size: 26px;'>{transliterated}</div>"
                                              f"<div style='font-size: 16px; color: #ccc;'>[{original_text}]</div>")

        log_timestamp("🐞 [DEBUG] PAS 7.6: Înainte de setText", "app")
        self.subtitle_label.setText(text_to_display_bottom)
        log_timestamp("🐞 [DEBUG] PAS 7.7: După setText", "app")
        try:
            self.subtitle_label.adjustSize()
            log_timestamp("🐞 [DEBUG] PAS 7.8: După adjustSize", "app")
        except RuntimeError as e:
            log_timestamp(f"⚠️ [DEBUG] adjustSize() a dat crash: {e} - skip", "app")

        self.subtitle_scroll_area.show()
        log_timestamp("🐞 [DEBUG] PAS 7.9: După show", "app")

        self.subtitle_scroll_area.raise_()
        log_timestamp("🐞 [DEBUG] PAS 7.10: După raise", "app")

        if translation_text:
            log_timestamp("🐞 [DEBUG] PAS 7.11: Procesare translation", "app")
            self.translation_label.setText(translation_text)
            try:
                self.translation_label.adjustSize()
            except RuntimeError:
                pass
            self.translation_scroll_area.show()
            self.translation_scroll_area.raise_()
            log_timestamp("🐞 [DEBUG] PAS 7.12: Translation gata", "app")

        log_timestamp("🐞 [DEBUG] PAS 7 COMPLET", "app")

        log_timestamp("🐞 [DEBUG] PAS 8: Se adaugă la chat.", "app")
        self.add_to_chat(speaking_character.display_name, original_text)
        if translation_text:
            self.add_to_chat(f"({speaking_character.display_name} - Tradus)", translation_text)
        
        if self.voice_worker:
            self.voice_worker.set_last_ai_text(original_text)
        
        # --- BLOC NOU: Ștergerea fișierului audio anterior ---
        if hasattr(self, 'last_audio_file_path') and self.last_audio_file_path and os.path.exists(self.last_audio_file_path):
            try:
                os.remove(self.last_audio_file_path)
                log_timestamp(f"🧹 [CLEANUP] Fișierul audio vechi a fost șters: {self.last_audio_file_path}", "cleanup")
            except Exception as e:
                log_timestamp(f"⚠️ [CLEANUP] Eroare la ștergerea fișierului vechi: {e}", "cleanup")
        # --- SFÂRȘIT BLOC NOU ---

        log_timestamp("🐞 [DEBUG] PAS 9: Se pregătește pornirea TTS STREAMING.", "app")
        self._start_streaming_tts(original_text, speaking_character.voice_id, speaking_character_id)
        log_timestamp("🐞 [DEBUG] PAS 10: S-a terminat handle_ai_response.", "app")

    def handle_ai_error(self, error_message):
        log_timestamp(f"❌ [APP EROARE AI] {error_message}", "app")
        self.stop_thinking()
        self.add_to_chat("Sistem", error_message)
        self.enable_all_actions()
        if self.voice_worker:
            self.voice_worker.set_muted(False)

    def _handle_visual_validation_response(self, json_string):
        """
        Procesează răspunsul de la worker-ul de validare (true/false)
        și pasează rezultatul către worker-ul pedagogic (LearningAgentWorker).
        """
        try:
            result = json.loads(json_string)
            success = result.get("success", False)
            reason = result.get("reason", "Motiv necunoscut.")
            log_timestamp(f"👁️ [VALIDARE] Rezultat primit: Succes = {success}. Motiv: {reason}", "app")

            # Acum, transformăm acest rezultat într-un "răspuns" text pentru
            # logica pedagogică pe care am construit-o deja.
            # Simulăm un răspuns de la copil.
            simulated_answer = "corect" if success else "greșit"
            
            # Apelăm metoda existentă care se ocupă de logica de învățare
            self._process_student_answer(simulated_answer)

        except json.JSONDecodeError as e:
            log_timestamp(f"❌ [VALIDARE] Eroare la parsarea JSON-ului de validare: {e}", "app")
            # În caz de eroare, presupunem că a fost greșit și repetăm
            self._process_student_answer("eroare de validare")

    def _on_video_speaker_analysis_complete(self, json_string, intent_data):
        """Procesează răspunsul de la worker-ul de analiză video."""
        try:
            # Curățăm JSON-ul de posibile markdown-uri
            if "```json" in json_string:
                json_string = json_string.split("```json")[1].strip()
            if "```" in json_string:
                json_string = json_string.replace("```", "").strip()

            result = json.loads(json_string)
            identified_names = result.get("identified_persons", [])
            log_timestamp(f"✅ [LEARNING ROUTER] Analiză video completă. Persoane identificate: {identified_names}", "app")

            if len(identified_names) == 1:
                # Cazul 2: O singură persoană recunoscută
                student_name = identified_names[0]
                self.start_learning_session(student_name, intent_data.get("subject"))
            elif len(identified_names) > 1:
                # Cazul 4: Mai multe persoane recunoscute -> Ambiguitate
                self.app_state = 'AWAITING_STUDENT_NAME'
                self.pending_learning_intent_data = intent_data
                self._start_tts("[EMOTION:curious] Văd că sunteți mai mulți aici. Care dintre voi dorește să înceapă o lecție?")
            else: # len == 0
                # Cazul "nimeni recunoscut"
                self.app_state = 'AWAITING_STUDENT_NAME'
                self.pending_learning_intent_data = intent_data
                self._start_tts("[EMOTION:curious] Văd pe cineva, dar nu te recunosc. Cum te cheamă?")
        
        except (json.JSONDecodeError, KeyError) as e:
            log_timestamp(f"❌ [LEARNING ROUTER] Eroare la parsarea răspunsului video: {e}. Se cere numele.", "app")
            self.app_state = 'AWAITING_STUDENT_NAME'
            self.pending_learning_intent_data = intent_data
            self._start_tts("[EMOTION:confuz] Hmm, am o problemă cu vederea. Spune-mi, te rog, numele tău.")


# --- Semnale pentru Semafor & Sincronizare TTS ---
    def on_speech_activity_changed(self, is_speaking):
        """Actualizează semaforul când utilizatorul începe sau termină de vorbit."""
        
        if is_speaking:
            self._update_semafor_state('verde')
        else:
            self._update_semafor_state('rosu')  # ← SCHIMBĂ ÎN ROȘU!

    def on_pause_progress_updated(self, progress):
        """Actualizează clepsidra când utilizatorul face o pauză."""
        if progress < 100:
            self._update_semafor_state('pauza', progress)
        else:
            self._update_semafor_state('verde')

    def on_speech_time_updated(self, timp_ramas):
        """Actualizează textul cronometrului din becul verde."""
        if timp_ramas >= 0:
            if not self.cronometru_label.isVisible():
                self.cronometru_label.show()
            self.cronometru_label.setText(str(int(timp_ramas)))
        else: # Valoare negativă semnalează ascunderea
            self.cronometru_label.hide()

    def on_speech_timeout(self):
        """Când cronometrul expiră - setează semafor roșu direct."""
        self._update_semafor_state('rosu')

    def on_audio_ready(self, audio_path, actual_duration):
        log_timestamp(f"🎬 [SYNC] ✅ AUDIO GATA! Durată: {actual_duration:.2f}s. Pornesc animația pentru '{self.speaking_character_id}'.", "sync")
        
        # --- BLOC NOU: Salvăm calea și activăm butonul ---
        self.last_audio_file_path = audio_path
        self.repeat_button.setEnabled(True)
        # --- SFÂRȘIT BLOC NOU ---
        
        self.set_speaker(self.speaking_character_id)
        
        self.estimated_speech_duration = actual_duration
        self.speech_start_time = time.time()
        self.sync_timer.start(30)


    def on_sentence_audio_ready(self, audio_path, duration, sentence_text):
        """
        Callback apelat când o propoziție individuală este gata de redat.
        Generează vizeme pentru această propoziție și pornește animația de lip-sync.
        """
        self.current_sentence_index += 1
        log_timestamp(f"🎬 [STREAMING SYNC] Propoziție {self.current_sentence_index}/{self.sentence_count} gata", "sync")
        log_timestamp(f"🎬 [STREAMING SYNC] Text: '{sentence_text[:50]}...', durată: {duration:.2f}s", "sync")
        
        # Salvează calea audio pentru butonul de repeat (ultima propoziție)
        self.last_audio_file_path = audio_path
        
        # ⭐ CRUCIAL: Generează vizeme DOAR pentru această propoziție
        self.generate_viseme_queue_for_text(sentence_text)
        self.total_viseme_count = len(self.viseme_queue)
        self.last_displayed_frame = -1
        
        log_timestamp(f"🎬 [STREAMING SYNC] Generate {self.total_viseme_count} vizeme pentru propoziția curentă", "sync")
        
        # Pornește sync_timer pentru această propoziție
        self.estimated_speech_duration = duration
        self.speech_start_time = time.time()
        self.sync_timer.start(30)  # Verifică la fiecare 30ms

    def on_all_sentences_finished(self):
        """
        Callback apelat când TOATE propozițiile au fost redate.
        Acest lucru este echivalentul apelului final al lui speech_finished().
        """
        log_timestamp("🏁 [STREAMING TTS] Toate propozițiile terminate", "tts")
        
        # Oprește sync_timer
        self.sync_timer.stop()
        
        # Resetează contoarele
        self.sentence_count = 0
        self.current_sentence_index = 0
        
        # Verifică dacă există un callback pending (din modul profesor)
        if self.pending_tts_callback is not None:
            log_timestamp("🎓 [STREAMING TTS] Callback personalizat detectat, se apelează", "tts")
            callback = self.pending_tts_callback
            self.pending_tts_callback = None  # Resetăm înainte de apel
            
            # Apelează callback-ul personalizat (care va gestiona tot)
            callback()
        else:
            # Flux normal - apelează speech_finished()
            log_timestamp("🏁 [STREAMING TTS] Flux normal, apel speech_finished()", "tts")
            self.speech_finished()

    def on_streaming_tts_error(self, error_message):
        """Gestionează erorile din streaming TTS."""
        log_timestamp(f"❌ [STREAMING TTS] Eroare: {error_message}", "tts")
        self.streaming_tts.stop_all()
        self.is_speaking = False
        self.speech_finished()


    def on_play_audio_file(self, audio_path):
        """
        Funcție apelată în main thread pentru a reda un fișier audio cu pygame.
        Folosește QTimer pentru verificare asincronă, fără blocare.
        """
        try:
            log_timestamp(f"🎵 [MAIN THREAD] Încep redare pygame: '{audio_path}'", "tts")
            
            # Salvează fișierul curent
            self.current_playing_audio = audio_path
            
            # Încarcă și pornește redarea
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Pornește timer-ul de verificare (verifică la fiecare 50ms)
            self.pygame_check_timer.start(50)
            
        except Exception as e:
            log_timestamp(f"❌ [MAIN THREAD] Eroare la pornire redare: {e}", "tts")
            self.current_playing_audio = None
            # Semnalizează eroarea către worker
            if hasattr(self.streaming_tts, '_playback_finished_event') and self.streaming_tts._playback_finished_event:
                self.streaming_tts._playback_finished_event.set()

    def _check_pygame_playback(self):
        """
        Verifică periodic dacă redarea pygame s-a terminat.
        Apelată de QTimer, rulează în main thread fără blocare.
        """
        try:
            if not pygame.mixer.music.get_busy():
                # Redarea s-a terminat!
                self.pygame_check_timer.stop()
                
                audio_path = self.current_playing_audio
                self.current_playing_audio = None
                
                # Curățare pygame
                pygame.mixer.music.unload()
                
                log_timestamp(f"✅ [MAIN THREAD] Redare terminată: '{audio_path}'", "tts")
                
                # Semnalizează worker-ului că am terminat
                if hasattr(self.streaming_tts, '_playback_finished_event') and self.streaming_tts._playback_finished_event:
                    self.streaming_tts._playback_finished_event.set()
        
        except Exception as e:
            log_timestamp(f"❌ [MAIN THREAD] Eroare verificare redare: {e}", "tts")
            self.pygame_check_timer.stop()
            self.current_playing_audio = None
            # Tot semnalizăm pentru a nu bloca worker-ul
            if hasattr(self.streaming_tts, '_playback_finished_event') and self.streaming_tts._playback_finished_event:
                self.streaming_tts._playback_finished_event.set()

# =================================================================================
# 6. Managementul Worker-ilor și Proceselor de Background
# (Metodele care pornesc și opresc thread-urile)
# =================================================================================


    def start_webcam(self):
        log_timestamp("📷 [APP] Pornire webcam...")
        self.webcam_thread = QThread()
        self.webcam_worker = WebcamWorker()
        self.webcam_worker.moveToThread(self.webcam_thread)
        self.webcam_worker.frame_ready.connect(self.update_webcam_feed)
        self.webcam_thread.started.connect(self.webcam_worker.run)
        self.webcam_thread.finished.connect(self.webcam_thread.quit)
        # ... restul conexiunilor pentru cleanup
        self.webcam_thread.start()

    def stop_webcam(self):
        if self.webcam_worker:
            log_timestamp("📷 [APP] Cerere de oprire webcam trimisă...", "webcam")
            self.webcam_worker.stop()
        
        if self.webcam_thread and self.webcam_thread.isRunning():
            self.webcam_thread.quit()
            if not self.webcam_thread.wait(2000): # Așteaptă maxim 2 secunde
                log_timestamp("⚠️ [APP] Thread-ul webcam nu s-a oprit la timp. Se termină forțat.", "webcam")
                self.webcam_thread.terminate() # Soluție de urgență
            log_timestamp("📷 [APP] ✅ Thread-ul webcam s-a oprit.", "webcam")

        # ====================================================================
        # ⭐⭐ ACESTEA SUNT LINIILE CRUCIALE LIPSĂ ⭐⭐
        # Resetăm variabilele pentru a permite o nouă pornire curată
        # ====================================================================
        self.webcam_worker = None
        self.webcam_thread = None
            
    def start_continuous_voice(self):
        log_timestamp("🎤 [APP] Pornire voice worker...")
        self.voice_thread = QThread()
        
        echo_setting = self.config.get("enable_echo_cancellation", True)
        speaker_id_setting = self.config.get("enable_speaker_identification", True) # <-- ⭐ ADAUGĂ ACEASTĂ LINIE ⭐
        
        self.voice_worker = ContinuousVoiceWorker(
            self.threshold, 
            self.pause_duration, 
            self.margin_percent, 
            self.max_speech_duration,
            enable_echo_cancellation=echo_setting
        )
        self.voice_worker.enable_speaker_identification = speaker_id_setting # <-- ⭐ ȘI ACEASTĂ LINIE ⭐
        
        self.voice_worker.language_lock_requested.connect(self.on_language_lock_requested)
        self.voice_worker.speech_activity_changed.connect(self.on_speech_activity_changed)
        self.voice_worker.pause_progress_updated.connect(self.on_pause_progress_updated)
        self.voice_worker.speech_time_updated.connect(self.on_speech_time_updated)
        self.voice_worker.speech_timeout.connect(self.on_speech_timeout)
        
        self.voice_worker.moveToThread(self.voice_thread)
        
        self.voice_worker.transcription_ready.connect(self.handle_voice_transcription)
        self.voice_worker.status_changed.connect(self.update_voice_status)
        self.voice_worker.audio_level_changed.connect(self.update_audio_meter)
        self.voice_worker.speaker_identified.connect(self.handle_speaker_identification)  # ⭐ NOU ⭐
        
        # ⭐ Setăm referințe pentru voice worker ⭐
        self.voice_worker.voice_manager = self.voice_print_manager
        self.voice_worker.family_data = self.family_data
        self.voice_worker.voice_recognition_threshold = self.config.get("voice_recognition_threshold", 0.75)
        # ⭐ SFÂRȘIT ⭐
        
        self.voice_thread.started.connect(self.voice_worker.run)
        self.voice_thread.start()

    def stop_continuous_voice(self):
        if self.voice_worker:
            log_timestamp("🎤 [APP] Cerere de oprire pentru worker-ul de voce...", "app")
            self.voice_worker.stop()

        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.quit()
            if self.voice_thread.wait(3000):
                log_timestamp("🎤 [APP] ✅ Thread-ul de voce s-a oprit.", "app")
            else:
                log_timestamp("🎤 [APP] ⚠️ Thread-ul de voce nu s-a oprit la timp.", "app")
        
        # ====================================================================
        # ⭐⭐ ACESTEA SUNT LINIILE CRUCIALE LIPSĂ ⭐⭐
        # Resetăm variabilele pentru a permite o nouă pornire curată
        # ====================================================================
        self.voice_worker = None
        self.voice_thread = None

    def do_calibration_sync(self):
        """Calibrare sincronă - se execută ÎNAINTE de pornirea worker-ului"""
        log_timestamp("=" * 70)
        log_timestamp("🔄 [CALIBRARE] === START CALIBRARE SINCRONĂ ===")
        log_timestamp("🔄 [CALIBRARE] Stai în liniște 3 secunde...")
        
        try:
            log_timestamp("🔄 [CALIBRARE] Creez recognizer...")
            recognizer = sr.Recognizer()
            
            log_timestamp("🔄 [CALIBRARE] Încerc să deschid microfonul...")
            with sr.Microphone() as source:
                log_timestamp("🔄 [CALIBRARE] ✅ Microfon deschis cu succes!")
                log_timestamp("🔄 [CALIBRARE] Ascult zgomotul de fundal...")
                
                # Actualizare UI
                if hasattr(self, 'calibration_result'):
                    self.calibration_result.setText("🔊 Calibrare în curs (3 sec)...")
                QApplication.processEvents()
                
                recognizer.adjust_for_ambient_noise(source, duration=3)
                
                noise_level = recognizer.energy_threshold
                suggested_threshold = int(noise_level * (1 + self.margin_percent/100))
                
                log_timestamp("=" * 70)
                log_timestamp("✅ [CALIBRARE] === REZULTATE CALIBRARE ===")
                log_timestamp(f"📊 [CALIBRARE] Zgomot detectat: {noise_level:.0f}")
                log_timestamp(f"📊 [CALIBRARE] Marjă configurată: +{self.margin_percent}%")
                log_timestamp(f"📊 [CALIBRARE] Threshold recomandat: {suggested_threshold}")
                log_timestamp(f"📊 [CALIBRARE] Threshold vechi: {self.threshold}")
                
                final_threshold = min(suggested_threshold, 10000)
                if final_threshold != suggested_threshold:
                    log_timestamp(f"⚠️ [CALIBRARE] Threshold limitat la maxim: 10000")
                
                log_timestamp(f"📊 [CALIBRARE] Setez threshold la: {final_threshold}")
                self.threshold_slider.setValue(final_threshold)
                
                log_timestamp(f"📊 [CALIBRARE] ✅ Threshold NOU setat: {final_threshold}")
                log_timestamp("=" * 70)
                
                # Actualizare UI
                if hasattr(self, 'calibration_result'):
                    self.calibration_result.setText(
                        f"✅ Calibrare completă!\n"
                        f"Zgomot: {noise_level:.0f}\n"
                        f"Threshold: {final_threshold}"
                    )
                
                diff = final_threshold - noise_level
                log_timestamp(f"💡 [CALIBRARE] Diferență față de zgomot: +{diff:.0f} ({self.margin_percent}%)")
                
        except Exception as e:
            error_msg = f"Eroare calibrare: {e}"
            log_timestamp(f"❌ [CALIBRARE] {error_msg}")
            log_timestamp(f"❌ [CALIBRARE] Tip eroare: {type(e).__name__}")
            import traceback
            log_timestamp(f"❌ [CALIBRARE] Stack trace:\n{traceback.format_exc()}")
            
            if hasattr(self, 'calibration_result'):
                self.calibration_result.setText(f"⚠️ {error_msg}")
        finally:
            log_timestamp("=" * 70)


# =================================================================================
# 7. Logica Centrală de Rutare și Procesare a Input-ului
# (Creierul aplicației, care decide ce să facă)
# =================================================================================


    def _route_user_input(self, text):
        """
        Punctul de intrare pentru orice input de la utilizator. (VERSIUNE EXTINSĂ)
        """
        log_timestamp(f"🚦 [ROUTER] Se analizează input-ul: '{text}'", "router")
        self.last_user_text = text

        # ====================================================================
        # ⭐⭐ MODIFICARE CRUCIALĂ AICI ⭐⭐
        # Verificăm dacă suntem într-o stare de așteptare a unui răspuns specific
        # ====================================================================
        if self.app_state == 'AWAITING_STUDENT_NAME':
            log_timestamp("🚦 [ROUTER] Stare: Așteptare nume student. Se procesează răspunsul...", "app")
            self._handle_student_name_response(text)
            return # Oprim procesarea normală
        # ====================================================================

        # --- BLOC NOU DE INTERCEPTARE ---
        # Verificăm dacă suntem în modul profesor și dacă s-a spus comanda "Gata!"
        text_lower = text.strip().lower()
        if self.teacher_mode_active and text_lower in ["gata", "gata gata"]:
            log_timestamp("📸 [VALIDARE] Comanda 'Gata!' detectată. Se declanșează validarea vizuală.", "app")
            self._trigger_visual_validation()
            return # Oprim orice altă procesare

        if self.teacher_mode_active:
            log_timestamp("🚦 [ROUTER] Stare: În modul Profesor. Se procesează ca răspuns de la elev...", "app")
            self._process_student_answer(text)
            return
        
        log_timestamp("🚦 [ROUTER] Stare: Conversație normală. Se rulează logica standard.", "router")
        self._validate_active_speaker()

        if self.waiting_for_travel_clarification:
            log_timestamp("🚦 [ROUTER] În waiting state pentru clarificare călătorie.", "router")
            self._handle_travel_clarification_response(text)
            return

        if self._check_and_switch_speaker(text):
            return

        if self.intent_thread is not None:
            try:
                if self.intent_thread.isRunning():
                    log_timestamp("🧹 [ROUTER] Curăț intent thread vechi care încă rulează...", "router")
                    self.intent_thread.quit()
                    self.intent_thread.wait(500)
            except RuntimeError:
                pass
        
        self.intent_thread = None
        self.intent_worker = None

        log_timestamp("🚦 [ROUTER] Se clasifică intenția...", "router")
        self.intent_thread = QThread()
        self.intent_worker = IntentClassifierWorker(text)
        self.intent_worker.moveToThread(self.intent_thread)
        
        self.intent_worker.intent_classified.connect(self._handle_intent_classification)
        self.intent_worker.error_occurred.connect(lambda err: log_timestamp(f"🚦 [ROUTER] Eroare la clasificare: {err}", "router"))
        
        self.intent_worker.finished.connect(self.intent_thread.quit)
        self.intent_worker.finished.connect(self.intent_worker.deleteLater)
        self.intent_thread.finished.connect(self.intent_thread.deleteLater)
        
        self.intent_thread.started.connect(self.intent_worker.run)
        self.intent_thread.start()

    def _handle_intent_classification(self, intent_data):
        """
        Slot care primește rezultatul de la IntentClassifierWorker și execută acțiunea.
        Deleagă logica specifică către funcții specializate.
        """
        intent = intent_data.get("intent")
        log_timestamp(f"🎯 [ROUTER] Intent detectat: '{intent}' | Data: {intent_data}", "router")

        # ========================================================================
        # CAZUL 1: Suntem în Modul Profesor
        # ========================================================================
        if self.teacher_mode_active:
            if intent == "exit_teacher_mode":
                self.exit_teacher_mode()
            else: # Orice altceva este un răspuns de la elev
                self._process_student_answer(self.last_user_text)
            return

        # ========================================================================
        # CAZURILE PENTRU MODUL CONVERSAȚIE NORMALĂ
        # ========================================================================
        
        if intent == "start_learning":
            # Delegăm toată logica complexă către noua funcție
            self._handle_start_learning_intent(intent_data)
        
        elif intent == "exit_teacher_mode":
            log_timestamp("⚠️ [ROUTER] Comandă 'exit_teacher_mode' ignorată (nu suntem în Modul Profesor).", "router")
            # Nu facem nimic, pur și simplu ignorăm.
        
        elif intent == "travel_with_character":
            self._handle_travel_with_character(intent_data) # O funcție ajutătoare nouă pentru claritate

        elif intent == "travel_solo":
            self._execute_travel_solo(intent_data.get("scene"))

        elif intent == "summon_character":
            self._handle_summon_character(intent_data) # O funcție ajutătoare nouă

        elif intent == "send_character":
            self._handle_send_character(intent_data) # O funcție ajutătoare nouă
        
        elif intent == "translation_request":
            self._handle_translation_request()
        
        else: # Cazul default este "conversation"
            self.process_question(self.last_user_text, self.active_speaker_id)

    def process_question(self, question, target_character_id):
        # --- Citim model_name la începutul funcției ---
        model_name = self.config.get("ai_model_name", "models/gemini-flash-lite-latest")
        log_timestamp(f"🤖 [GEMINI] Se va folosi modelul: {model_name}", "gemini_debug")

        if not question or self.is_speaking or self.is_thinking:
            log_timestamp(f"⚠️ [APP] Întrebare ignorată (stare ocupată: speaking={self.is_speaking}, thinking={self.is_thinking})", "app")
            return

        if target_character_id not in self.character_manager.active_characters:
            log_timestamp(f"🔇 [PROCESS] Personaj '{target_character_id}' nu e pe scenă → SILENCE", "app")
            return

        target_character = self.character_manager.get_character(target_character_id)
        if not target_character:
            log_timestamp(f"❌ [APP] Nu am găsit personajul țintă '{target_character_id}'!", "app")
            self.add_to_chat("Sistem", f"Eroare: personajul {target_character_id} nu există.")
            return
        
        # ====================================================================
        # ⭐⭐ AICI ESTE MODIFICAREA CRUCIALĂ ⭐⭐
        # Construim prefixul pentru prompt pe baza identității vocale
        # ====================================================================
        question_prefix = "Utilizator: " # Prefixul default

        # Folosim getattr pentru a accesa în siguranță atributul, chiar dacă nu a fost setat
        speaker_name = getattr(self, '_last_identified_speaker', None)

        if speaker_name:
            question_prefix = f"Utilizator (identificat prin voce ca fiind {speaker_name}): "
            log_timestamp(f"🎤 [PROMPT] Adaug la prompt identitatea vocală: {speaker_name}", "voice")
            # Important: Golim variabila după ce am folosit-o, pentru a nu o aplica la replici viitoare
            self._last_identified_speaker = None 
        
        # Combinăm prefixul cu întrebarea originală
        final_question_for_ai = question_prefix + question
        # ====================================================================

        log_timestamp(f"🤖 [APP] === PROCESARE ÎNTREBARE PENTRU '{target_character_id}' ===", "app")
        
        self.conversation_log.append({"role": "user", "content": question}) # Păstrăm întrebarea curată în log
        
        self.is_thinking = True
        self.disable_all_actions()
        self._update_semafor_state('rosu')

        if self.voice_worker:
            log_timestamp("🔇 [MUTE] Microfonul este pus în pauză pe durata gândirii și vorbirii.", "mute")
            self.voice_worker.set_muted(True, is_ai_speaking=True)

        if self.config.get("enable_filler_sounds", True):
            self.play_filler_sound(target_character)
        
        self.thinking_timer.start(500)

        # --- CONSTRUIREA DINAMICĂ A PROMPT-ULUI ---
        system_prompt_base = target_character.get_prompt_content()
        world_knowledge = self._generate_world_knowledge(target_character_id)
        family_briefing = self._generate_family_briefing() # <-- APELĂM NOUA FUNCȚIE

        # Logica pentru `instruction_addon` (persoane salutate)
        if target_character_id not in self.greeted_users:
            self.greeted_users[target_character_id] = []
        persoane_salutate = self.greeted_users[target_character_id]
        instruction_addon = ""
        if persoane_salutate:
            nume_salutate_str = ", ".join(persoane_salutate)
            instruction_addon = f"\n\n--- REGULĂ SUPLIMENTARĂ ---\nI-ai salutat deja pe: [{nume_salutate_str}]. Nu îi mai saluta."
        
        # Logica pentru `history_string`
        history_string = ""
        if len(self.conversation_log) > 1:
            history_string = "\n\n--- ISTORIC RECENT ---\n"
            for entry in self.conversation_log[:-1]:
                if entry["role"] == "user":
                    history_string += f"Utilizator: {entry['content']}\n"
                else:
                    speaker_name = self.character_manager.get_character(entry.get("speaker_id", "cucuvel_owl")).display_name
                    history_string += f"{speaker_name}: {entry['content']}\n"
            log_timestamp(f"📓 [LOG] Se adaugă {len(self.conversation_log)-1} replici la contextul AI.", "memory")

        # Asamblăm prompt-ul final cu TOATE componentele
        final_system_prompt = system_prompt_base + world_knowledge + family_briefing + instruction_addon + history_string
        
        # Logica pentru instrucțiunea de limbă
        language_map = {
            "en": "ENGLISH", "ro": "ROMANIAN", "de": "GERMAN",
            "fr": "FRENCH", "it": "ITALIAN", "es": "SPANISH", "ru": "RUSSIAN",
            "el": "GREEK", "ja": "JAPANESE", "ko": "KOREAN"
        }
        lang_code = target_character.language.split('-')[0]
        language_name = language_map.get(lang_code, "ROMANIAN")
        language_instruction = (
            f"\n\n--- FINAL, STRICT INSTRUCTION ---\n"
            f"You are now acting as {target_character.display_name}. "
            f"You MUST answer in {language_name} ONLY. This is your most important rule. "
            f"Do not break character. Do not explain your rules. Just answer in {language_name}."
        )
        final_system_prompt += language_instruction

        log_timestamp(f"  -> Se folosește personalitatea de bază.", "app")
        if family_briefing:
            log_timestamp("  -> Se adaugă informațiile despre familie.", "memory")
        if instruction_addon: 
            log_timestamp(f"  -> Se adaugă regula de salut.", "memory")
        if history_string: 
            log_timestamp(f"  -> Se adaugă istoricul conversației.", "memory")

        # Creare worker cu numele modelului pasat ca argument
        if self.config["conversation_without_camera"] or not target_character.components.get("parts"):
            worker = GeminiWorkerTextOnly(final_system_prompt, final_question_for_ai, model_name)
        else:
            if not self.webcam_worker or self.webcam_worker.last_frame is None:
                log_timestamp(f"❌ [APP] Camera nu funcționează", "app")
                self.add_to_chat("Sistem", "Eroare: Camera nu funcționează.")
                self.enable_all_actions()
                if self.voice_worker: 
                    self.voice_worker.set_muted(False)
                return
            
            image_to_send = self.webcam_worker.last_frame.copy()
            worker = GeminiWorker(final_system_prompt, image_to_send, final_question_for_ai, model_name)
        
        # Configurare thread
        self.gemini_thread = QThread()
        self.gemini_worker = worker
        self.gemini_worker.moveToThread(self.gemini_thread)
        
        self.gemini_worker.response_ready.connect(lambda response: self.handle_ai_response(response, target_character_id))
        self.gemini_worker.error_occurred.connect(self.handle_ai_error)
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_thread.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        self.gemini_thread.started.connect(self.gemini_worker.run)
        
        self.gemini_thread.start()

    def speech_finished(self):
        # --- GARDĂ DE SIGURANȚĂ PENTRU A PREVENI APELURI DUBLE ---
        if not self.is_speaking and not self.is_thinking:
            return

        # --- MODIFICARE: Nu mai ascundem subtitrările la final ---
        # self.subtitle_scroll_area.hide()  <-- COMENTAT SAU ȘTERS
        # self.translation_scroll_area.hide() <-- COMENTAT SAU ȘTERS
        
        # Doar resetăm scrollbar-ul la poziția de start pentru data viitoare
        #self.subtitle_scroll_area.verticalScrollBar().setValue(0)
        
        # --- SFÂRȘIT MODIFICARE ---
        
        # ... restul funcției rămâne neschimbat ...
        if self.voice_enabled:
            self._update_semafor_state('verde') # Revine la VERDE
        # --- SFÂRȘIT BLOC ---
        
        # ⭐ PASUL 1: Resetare flag-uri de stare
        self.is_speaking = False
        self.is_thinking = False
        log_timestamp("🔓 [STATE] Flag-uri resetate: speaking=False, thinking=False", "cleanup")
        
        # ⭐⭐⭐ CURĂȚARE STREAMING TTS (sistem nou)
        # Nu mai avem tts_worker/tts_thread, dar oprim streaming-ul dacă mai rulează
        if hasattr(self, 'streaming_tts') and (self.streaming_tts.is_generating or self.streaming_tts.is_playing):
            log_timestamp("🧹 [CLEANUP] Opresc streaming TTS dacă încă rulează", "cleanup")
            self.streaming_tts.stop_all()

        
        # ⭐⭐⭐ ACUM verificăm pending questions
        if hasattr(self, 'pending_first_question') and self.pending_first_question:
            self.pending_first_question = False
            log_timestamp("🎓 [LEARNING] TTS bun venit terminat. Pun prima întrebare...", "app")
            QTimer.singleShot(500, self._ask_next_question)
            
            if self.voice_worker and not self.is_muted:
                self.voice_worker.set_muted(False)
            
            return  # Acum e sigur să returnăm
        
        if hasattr(self, 'pending_next_question') and self.pending_next_question:
            self.pending_next_question = False
            log_timestamp("🎓 [LEARNING] TTS feedback terminat. Pun următoarea întrebare...", "app")
            QTimer.singleShot(500, self._ask_next_question)
            
        
            return
        
        # ⭐ NOU: Verifică dacă trebuie să avansăm automat la următorul tier ⭐
        if hasattr(self, 'auto_advance_to_next_tier') and self.auto_advance_to_next_tier:
            self.auto_advance_to_next_tier = False
            log_timestamp("🎓 [LEARNING] TTS completare terminat. Avansez automat la următorul tier...", "app")
            QTimer.singleShot(1000, self._advance_to_next_tier)
            return
        
        # ⭐ PASUL 2: UNMUTE microfonul (cu verificare inteligentă)
        if self.voice_worker:
            # Reactivăm ascultarea DOAR dacă utilizatorul NU este pe modul MUTE MANUAL
            if not self.is_muted:
                log_timestamp("🔊 [UNMUTE] Microfonul este reactivat automat.", "mute")
                self.voice_worker.set_muted(False)
            else:
                log_timestamp("🔇 [UNMUTE] Microfonul RĂMÂNE pe mute la cererea utilizatorului.", "mute")
        
        # ⭐ PASUL 2.1: Revenire la speaker original după traducere
        if self.pending_speaker_return:
            log_timestamp(f"🔄 [TRANSLATION] Revin la speaker-ul original: '{self.pending_speaker_return}'", "router")
            self.active_speaker_id = self.pending_speaker_return
            self.pending_speaker_return = None
        # ⭐ PASUL 2.3: RESET GAZE (ADAUGĂ AICI!)
        self.set_speaker(None)  # Toți privesc în față
        
        # ⭐ PASUL 2.5: EXECUTĂM MUTAREA AMÂNATĂ DACĂ EXISTĂ
        if self.pending_move_after_tts:
            move_data = self.pending_move_after_tts
            self.pending_move_after_tts = None  # Resetăm
            
            log_timestamp(f"🚀 [SEND] Execut mutarea amânată: '{move_data['char_id']}' → '{move_data['destination']}'", "router")
            
            success, error = self.character_manager.move_character_silent(
                move_data['char_id'], 
                move_data['destination']
            )
            
            if success:
                log_timestamp(f"✅ [SEND] '{move_data['char_id']}' mutat cu succes în '{move_data['destination']}'", "router")
                log_timestamp(f"📊 [SEND] Personaje active DUPĂ mutare: {list(self.character_manager.active_characters.keys())}", "router")
                
                # Dacă pleacă speaker-ul, fallback
                if move_data['char_id'] == self.active_speaker_id:
                    self._handle_speaker_left()
            else:
                log_timestamp(f"❌ [SEND] Eroare la mutare amânată: {error}", "router")
        
        # ⭐ PASUL 3: Cleanup cu protecție try-except
        log_timestamp("🧹 [CLEANUP] Se marchează pentru ștergere și se resetează referințele TTS.", "cleanup")
        
        # Curățare thread și worker Gemini
        log_timestamp("🧹 [CLEANUP] Curățare thread și worker Gemini...", "cleanup")
        if self.gemini_worker is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Marchează gemini_worker pentru ștergere", "cleanup")
                self.gemini_worker.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.gemini_worker = None
        
        if self.gemini_thread is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Oprește și marchează gemini_thread pentru ștergere", "cleanup")
                self.gemini_thread.quit()
                self.gemini_thread.wait(1000)
                self.gemini_thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.gemini_thread = None
        
        # Curățare thread și worker Intent
        log_timestamp("🧹 [CLEANUP] Curățare thread și worker Intent...", "cleanup")
        if self.intent_worker is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Marchează intent_worker pentru ștergere", "cleanup")
                self.intent_worker.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.intent_worker = None
        
        if self.intent_thread is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Oprește și marchează intent_thread pentru ștergere", "cleanup")
                self.intent_thread.quit()
                self.intent_thread.wait(1000)
                self.intent_thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.intent_thread = None
        
        # ⭐ Curățare thread și worker TTS
        log_timestamp("🧹 [CLEANUP] Curățare thread și worker TTS...", "cleanup")
        if self.tts_worker is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Marchează tts_worker pentru ștergere", "cleanup")
                self.tts_worker.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.tts_worker = None
        
        if self.tts_thread is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Oprește și marchează tts_thread pentru ștergere", "cleanup")
                self.tts_thread.quit()
                self.tts_thread.wait(1000)
                self.tts_thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.tts_thread = None
        
        # ⭐⭐⭐ NOU: Curățare thread și worker Learning
        log_timestamp("🧹 [CLEANUP] Curățare thread și worker Learning...", "cleanup")
        if self.learning_worker is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Marchează learning_worker pentru ștergere", "cleanup")
                self.learning_worker.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.learning_worker = None
        
        if self.learning_thread is not None:
            try:
                log_timestamp("🧹 [CLEANUP] - Oprește și marchează learning_thread pentru ștergere", "cleanup")
                self.learning_thread.quit()
                self.learning_thread.wait(1000)
                self.learning_thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.learning_thread = None
        
        log_timestamp(f"✅ [CLEANUP] Cleanup complet finalizat!", "cleanup")
        
        # ⭐ RE-ENABLE TEXT INPUT ȘI ALTE CONTROALE
        self.enable_all_actions()
        log_timestamp(f"🔓 [UI] Controale re-activate - text input disponibil", "cleanup")
   
    def add_to_chat(self, user, message, voice_identified=False, confidence=0.0):
        """
        Adaugă un mesaj în fereastra de chat și face scroll automat în jos.
        
        Args:
            user: Numele vorbitorului
            message: Textul mesajului
            voice_identified: Dacă True, adaugă badge de identificare vocală
            confidence: Procentul de siguranță al identificării (0.0-1.0)
        """
        # ⭐ BADGE IDENTIFICARE VOCE ⭐
        if voice_identified and confidence > 0:
            badge = f"<span style='background-color: #5cb85c; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;'>🎤 {confidence:.0%}</span> "
            self.chat_history.append(f"{badge}<b>{user}:</b> {message}")
        else:
            self.chat_history.append(f"<b>{user}:</b> {message}")
        # ⭐ SFÂRȘIT BADGE ⭐
        
        # Scrie în fișierul de log
        if self.conversation_log_file and not self.conversation_log_file.closed:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.conversation_log_file.write(f"[{timestamp}] {user}: {message}\n")
            self.conversation_log_file.flush()
        
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())
        
    
# =================================================================================
# 8. Logica Specifică pentru Intenții (Handlers)
# (Metodele care execută acțiunile decise de ruter)
# =================================================================================


# --- Handlers pentru Navigare & Personaje ---
    def _check_and_switch_speaker(self, text):
        """
        Verifică dacă textul conține cuvinte cheie pentru a schimba vorbitorul activ.
        MODIFICAT: Răspunde dacă personajul menționat nu e pe scenă.
        Returnează True dacă s-a făcut o schimbare SAU s-a generat un răspuns, altfel False.
        """
        log_timestamp("🎤 [SPEAKER SWITCH] Se verifică dacă se schimbă vorbitorul...", "router")
        text_lower = text.lower()

        speaker_keywords = {
            "cucuvel_owl": ["cucuvel", "profesore", "domn profesor", "bufnițovici", "bufnita"],
            "rina_cat": ["rina", "nina", "irina", "pisico", "pisica"]
        }

        characters_on_stage_ids = self.character_manager.active_characters.keys()

        for char_id, keywords in speaker_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if char_id in characters_on_stage_ids:
                        # ✅ PERSONAJ PE SCENĂ - switch normal
                        if self.active_speaker_id == char_id:
                            log_timestamp(f"🎤 [SPEAKER SWITCH] Adresare către vorbitorul deja activ ('{char_id}'). Nu se schimbă nimic.", "router")
                            return False
                        else:
                            log_timestamp(f"🎤 [SPEAKER SWITCH] COMANDĂ DETECTATĂ! Trecem la '{char_id}'.", "router")
                            
                            new_speaker = self.character_manager.get_character(char_id)
                            confirmation_prompt = ""
                            if new_speaker.language.startswith("en"):
                                confirmation_prompt = "Say a short confirmation phrase, in your personality, to let the user know you are now listening. For example: 'I'm here!', 'Yes?', or 'I'm listening!'"
                            else:
                                confirmation_prompt = "Spune o frază scurtă de confirmare, în personalitatea ta, că acum asculți tu. De exemplu: 'Ascult!', 'Sunt aici!' sau 'Da, spune-mi!'."
                            
                            self.active_speaker_id = char_id
                            self.process_question(confirmation_prompt, self.active_speaker_id)
                            
                            return True
                    else:
                        # ❌ PERSONAJ ABSENT - cineva răspunde sau silence
                        log_timestamp(f"🔇 [SPEAKER SWITCH] '{char_id}' menționat dar NU e pe scenă", "router")
                        
                        # Verificăm dacă avem un speaker activ pe scenă care poate răspunde
                        if self.active_speaker_id and self.active_speaker_id in characters_on_stage_ids:
                            # CASE 7 & 10: Speaker-ul răspunde despre personaj absent
                            char_absent = self.character_manager.get_character(char_id)
                            speaker = self.character_manager.get_character(self.active_speaker_id)
                            
                            log_timestamp(f"💬 [SPEAKER] '{self.active_speaker_id}' răspunde despre '{char_id}' absent", "router")
                            
                            # Detectăm dacă e comandă send (du-te, mergi, etc.)
                            is_send_command = any(word in text_lower for word in ["du-te", "du te", "mergi", "pleacă", "pleaca"])
                            
                            if is_send_command:
                                # CASE 10: Comandă send către absent
                                if speaker.language.startswith("en"):
                                    absence_prompt = f"Tell the user politely that {char_absent.display_name} is not here, so you cannot send them anywhere."
                                else:
                                    absence_prompt = f"Spune politicos utilizatorului că {char_absent.display_name} nu e aici, deci nu îl poți trimite nicăieri."
                            else:
                                # CASE 7: Întrebare/conversație cu absent
                                if speaker.language.startswith("en"):
                                    absence_prompt = f"Tell the user politely that {char_absent.display_name} is not here right now."
                                else:
                                    absence_prompt = f"Spune politicos utilizatorului că {char_absent.display_name} nu e aici acum."
                            
                            self.process_question(absence_prompt, self.active_speaker_id)
                            return True
                        else:
                            # CASE 5: Nimeni pe scenă → SILENCE complet
                            log_timestamp(f"🔇 [SPEAKER] Nimeni pe scenă să răspundă → SILENCE", "router")
                            return False
        
        log_timestamp("🎤 [SPEAKER SWITCH] Nicio comandă de schimbare a vorbitorului detectată.", "router")
        return False

    def _handle_speaker_left(self):
        """
        Gestionează situația când speaker-ul activ pleacă din scenă.
        CASE 3: Verifică dacă mai e cineva → switch, altfel None
        """
        log_timestamp(f"👋 [SPEAKER] Speaker-ul '{self.active_speaker_id}' a plecat din scenă", "router")
        
        active_chars = list(self.character_manager.active_characters.keys())
        
        if len(active_chars) > 0:
            # Mai e cineva → switch
            self.active_speaker_id = active_chars[0]
            char = self.character_manager.get_character(self.active_speaker_id)
            log_timestamp(f"🔄 [SPEAKER] Auto-switch la '{self.active_speaker_id}' ({char.display_name})", "router")
        else:
            # Nimeni → None
            self.active_speaker_id = None
            log_timestamp(f"🔇 [SPEAKER] Nu mai e nimeni → speaker = None (doar summon/travel funcționează)", "router")

    def _handle_arrival_greeting(self):
        """
        CASE 8: Când ajungi într-o scenă cu natives, te salută automat.
        CASE 9: Dacă e goală, speaker = None.
        """
        active_chars = list(self.character_manager.active_characters.keys())
        
        log_timestamp(f"🏠 [ARRIVAL] Verificare greeting pentru {len(active_chars)} personaje...", "router")
        
        if len(active_chars) == 0:
            # Scenă goală
            self.active_speaker_id = None
            log_timestamp(f"🏜️ [ARRIVAL] Scenă goală → speaker = None", "router")
            return
        
        # Găsim primul native (care nu era cu noi)
        native_greeter = None
        current_scene = self.scene_manager.current_scene_id
        
        for char_id in active_chars:
            char = self.character_manager.get_character(char_id)
            
            # ⭐ FIX: Folosim char.home_scene, care este numele corect al atributului
            log_timestamp(f"🔍 [ARRIVAL] Verific '{char_id}': home_scene={char.home_scene}, current_scene={current_scene}", "router")
            
            # E native aici (home_scene = scena curentă)?
            if char.home_scene == current_scene:
                native_greeter = char_id
                log_timestamp(f"✅ [ARRIVAL] GĂSIT native greeter: '{char_id}'", "router")
                break
        
        if native_greeter:
            # Native găsit → salută
            self.active_speaker_id = native_greeter
            char = self.character_manager.get_character(native_greeter)
            
            log_timestamp(f"👋 [ARRIVAL] Native '{native_greeter}' te salută în '{current_scene}'", "router")
            
            if char.language.startswith("en"):
                greeting_prompt = "Greet the user warmly as they arrive in your home. Say something like 'Welcome back!' or 'Hello there!'"
            else:
                greeting_prompt = "Salută călduros utilizatorul care vine în casa ta. Spune ceva ca 'Bine ai venit înapoi!' sau 'Salut!'"
            
            self.process_question(greeting_prompt, native_greeter)
        else:
            # Nu e native, dar e cineva → switch la primul
            self.active_speaker_id = active_chars[0]
            log_timestamp(f"🔄 [ARRIVAL] Niciun native, switch la '{self.active_speaker_id}' (prim disponibil)", "router")

    def _handle_travel_with_character(self, intent_data):
        """Gestionează logica pentru intenția 'travel_with_character'."""
        char_id = intent_data.get("character")
        destination = intent_data.get("scene")
        
        log_timestamp(f"🚶 [TRAVEL_WITH] Procesare: user + personaj → '{destination}'", "router")
        
        current_scene = self.scene_manager.current_scene_id
        if destination == current_scene:
            log_timestamp(f"🔄 [TRAVEL_WITH] Destinația este scena curentă. Se convertește în SUMMON.", "router")
            if char_id:
                self._handle_summon_character({"character": char_id})
            return

        if char_id:
            char = self.character_manager.get_character(char_id)
            if not (char and char_id in self.active_characters and char.can_leave_home and destination in char.scene_configs):
                log_timestamp(f"🔇 [TRAVEL_WITH] Condiții neîndeplinite pentru '{char_id}'. Anulare.", "router")
                return
            self._execute_travel_with_characters(destination, [char_id])
        else:
            active_chars = list(self.character_manager.active_characters.keys())
            if not active_chars:
                self._execute_travel_solo(destination)
                return

            candidates = [c for c in self.get_active_characters_list() if c.can_leave_home and destination in c.scene_configs]
            
            if len(candidates) <= 1:
                traveler_ids = [c.id for c in candidates]
                self._execute_travel_with_characters(destination, traveler_ids)
            else:
                self._ask_for_travel_clarification(destination, candidates)

    def _execute_travel_with_characters(self, destination, character_ids):
        log_timestamp(f"🚶 [EXEC WITH] User + {character_ids} → '{destination}'", "router")
        log_timestamp(f"📊 [EXEC WITH] Personaje active ÎNAINTE: {list(self.character_manager.active_characters.keys())}", "router")
        
        # 1. Schimbă scena
        self.scene_manager.set_scene(destination)
        
        # 2. Curăță UI
        self.character_manager.clear_active_characters()
        log_timestamp(f"📊 [EXEC WITH] Personaje active DUPĂ clear: []", "router")
        
        # 3. Adaugă personajele călătoare
        for char_id in character_ids:
            char = self.character_manager.get_character(char_id)
            if char:
                char.current_scene_id = destination
                self.character_manager.add_character_to_stage(char_id)
                log_timestamp(f"✅ [EXEC WITH] '{char_id}' adăugat manual în '{destination}'", "router")
        
        # 4. Încarcă natives și visitors
        self.character_manager.sync_characters_for_scene(destination, self.scene_manager)
        log_timestamp(f"📊 [EXEC WITH] Personaje active DUPĂ sync: {list(self.character_manager.active_characters.keys())}", "router")
        
        # ⭐ 5. CHECKPOINT 4: Auto-greeting de la natives (dacă găsim)
        self._handle_arrival_greeting()

        # ⭐ 6. Re-calculate gaze pentru noua scenă
        self.update_all_gazes()

    def _execute_travel_solo(self, destination):
        log_timestamp(f"🚶 [EXEC SOLO] User merge SOLO → '{destination}'", "router")
        log_timestamp(f"📊 [EXEC SOLO] Personaje active ÎNAINTE: {list(self.character_manager.active_characters.keys())}", "router")
        
        # 1. Schimbă scena
        self.scene_manager.set_scene(destination)
        
        # 2. Curăță UI
        self.character_manager.clear_active_characters()
        log_timestamp(f"📊 [EXEC SOLO] Personaje active DUPĂ clear: []", "router")
        
        # 3. Încarcă natives și visitors
        self.character_manager.sync_characters_for_scene(destination, self.scene_manager)
        log_timestamp(f"📊 [EXEC SOLO] Personaje active DUPĂ sync: {list(self.character_manager.active_characters.keys())}", "router")
        
        # ⭐ 4. CHECKPOINT 4: Auto-greeting de la natives
        self._handle_arrival_greeting()

        # ⭐ 5. Re-calculate gaze pentru noua scenă
        self.update_all_gazes()

    def _handle_summon_character(self, intent_data):
        """Gestionează logica pentru intenția 'summon_character'."""
        char_id = intent_data.get("character")
        char = self.character_manager.get_character(char_id)
        current_scene = self.scene_manager.current_scene_id

        if not (char and char_id not in self.active_characters and char.can_be_summoned and current_scene in char.scene_configs):
            log_timestamp(f"🔇 [SUMMON] Condiții neîndeplinite pentru chemarea lui '{char_id}'. Anulare.", "router")
            return
        
        log_timestamp(f"✅ [SUMMON] Chemare validă: '{char_id}' → '{current_scene}'", "router")
        self.character_manager.add_character_to_stage(char_id)
        
        if char.language.startswith("en"):
            arrival_prompt = "Confirm cheerfully that you've arrived. Say a short greeting."
        else:
            arrival_prompt = "Confirmă vesel că ai venit. Spune un salut scurt."
        
        self.active_speaker_id = char_id
        self.process_question(arrival_prompt, char_id)

    def _handle_send_character(self, intent_data):
        """Gestionează logica pentru intenția 'send_character'."""
        char_id = intent_data.get("character")
        destination = intent_data.get("scene")
        
        if char_id not in self.active_characters:
            log_timestamp(f"🔇 [SEND] '{char_id}' nu este pe scenă. Anulare.", "router")
            return
            
        char = self.character_manager.get_character(char_id)
        
        # Generăm un răspuns de refuz dacă oricare condiție nu e îndeplinită
        refusal_prompt = None
        if not char.can_leave_home:
            refusal_prompt = "Explică politicos de ce nu poți părăsi această scenă."
        elif destination not in self.scene_manager.scenes:
            refusal_prompt = f"Explică politicos că nu cunoști locul numit '{destination}'."
        elif destination not in char.scene_configs:
            refusal_prompt = f"Explică de ce nu poți merge la '{destination}'."
        elif char.current_scene_id == destination:
            refusal_prompt = f"Spune vesel că ești deja la {destination}."
        
        if refusal_prompt:
            log_timestamp(f"❌ [SEND] Trimitere refuzată. Motiv: {refusal_prompt}", "router")
            if not char.language.startswith("ro"):
                refusal_prompt = f"Translate this to {char.language}: {refusal_prompt}"
            self.process_question(refusal_prompt, char_id)
            return
            
        # Dacă toate condițiile trec, programăm plecarea
        self.pending_move_after_tts = {'char_id': char_id, 'destination': destination}
        destination_name = self.scene_manager.get_scene_data(destination).get('name', destination)
        
        departure_prompt = f"Spune un rămas bun scurt, deoarece pleci spre {destination_name}."
        if not char.language.startswith("ro"):
            departure_prompt = f"Translate this to {char.language}: {departure_prompt}"
        
        self.active_speaker_id = char_id
        self.process_question(departure_prompt, char_id)

    def _handle_translation_request(self):
        """
        Gestionează cererea de traducere/explicare a ultimei replici.
        
        Flow:
        1. Găsește ultima replică a speaker-ului activ
        2. Găsește un translator (personaj RO pe scenă)
        3. Translator explică în română
        4. Auto-switch înapoi la speaker-ul original
        
        VERSIUNE COMPLETĂ - COPY-PASTE DIRECT
        """
        log_timestamp("🌐 [TRANSLATION] Căutare replică de tradus...", "router")
        
        # Validare 1: Avem un speaker activ?
        if not self.active_speaker_id:
            log_timestamp("🔇 [TRANSLATION] Nu există speaker activ - SILENCE", "router")
            return
        
        # Validare 2: Speaker-ul e pe scenă?
        if self.active_speaker_id not in self.character_manager.active_characters:
            log_timestamp(f"🔇 [TRANSLATION] Speaker '{self.active_speaker_id}' nu e pe scenă - SILENCE", "router")
            return
        
        # Validare 3: Avem o replică de tradus?
        if self.active_speaker_id not in self.last_character_speeches:
            log_timestamp(f"🔇 [TRANSLATION] Nu avem nicio replică salvată de la '{self.active_speaker_id}' - SILENCE", "router")
            return
        
        original_text = self.last_character_speeches[self.active_speaker_id]
        original_speaker = self.character_manager.get_character(self.active_speaker_id)
        
        log_timestamp(f"📝 [TRANSLATION] Replică de tradus: '{original_text[:50]}...'", "router")
        
        # Căutăm un translator (personaj RO pe scenă, diferit de speaker)
        translator_id = None
        for char_id in self.character_manager.active_characters:
            char = self.character_manager.get_character(char_id)
            if char.language.startswith("ro") and char_id != self.active_speaker_id:
                translator_id = char_id
                log_timestamp(f"✅ [TRANSLATION] Translator găsit: '{translator_id}'", "router")
                break
        
        # Validare 4: Avem translator disponibil?
        if not translator_id:
            log_timestamp("🔇 [TRANSLATION] Nu există translator (personaj RO) pe scenă - SILENCE", "router")
            return
        
        # Construim prompt pentru translator
        translator = self.character_manager.get_character(translator_id)
        
        if original_speaker.language.startswith("en"):
            # Speaker vorbește EN → traducem în RO
            prompt = (
                f"Utilizatorul nu a înțeles ultima replică a lui {original_speaker.display_name} "
                f"care a spus în engleză: '{original_text}'. "
                f"Explică-i în română, simplu și clar, ce a vrut să spună. "
                f"Începe cu: '{original_speaker.display_name} a spus că...' sau similar."
            )
        else:
            # Speaker vorbește altceva → explicăm simplu
            prompt = (
                f"Utilizatorul nu a înțeles ultima replică a lui {original_speaker.display_name}: "
                f"'{original_text}'. Explică-i mai simplu ce a vrut să spună."
            )
        
        log_timestamp(f"🌐 [TRANSLATION] Prompt către translator: '{prompt[:80]}...'", "router")
        
        # Salvăm speaker-ul original pentru revenire după traducere
        self.pending_speaker_return = self.active_speaker_id
        log_timestamp(f"💾 [TRANSLATION] Salvez speaker original: '{self.pending_speaker_return}'", "router")
        
        # Switch temporar la translator
        self.active_speaker_id = translator_id
        log_timestamp(f"🔄 [TRANSLATION] Switch temporar la translator: '{translator_id}'", "router")
        
        # Procesăm traducerea
        self.process_question(prompt, translator_id)

    def _ask_for_travel_clarification(self, destination, candidates):
        """
        Pune o întrebare de clarificare prin vorbitorul activ când există ambiguitate.
        Intră în waiting state pentru răspuns.
        
        Args:
            destination (str): Scena destinație
            candidates (list): Lista de character objects care sunt candidați
        """
        log_timestamp(f"❓ [CLARIFY] Se cere clarificare pentru călătoria la '{destination}'", "router")
        
        # Salvăm datele călătoriei
        self.pending_travel_data = {
            'destination': destination,
            'candidates': candidates,
            'candidate_ids': [char.id for char in candidates]
        }
        
        # Intrăm în waiting state
        self.waiting_for_travel_clarification = True
        
        # Pornim timeout de 15 secunde
        self.clarification_timeout_timer.start(15000)
        log_timestamp(f"⏱️ [CLARIFY] Timeout de 15s pornit", "router")
        
        # Generăm întrebarea
        intrebare = self._generate_clarification_question(destination, candidates)
        
        # Trimitem întrebarea prin vorbitorul activ
        log_timestamp(f"❓ [CLARIFY] Întrebare: '{intrebare}'", "router")
        self.process_question(intrebare, self.active_speaker_id)

    def _handle_travel_clarification_response(self, text):
        """
        Interpretează răspunsul user-ului la întrebarea de clarificare călătorie.
        
        Logica SIMPLĂ (KISS):
        - Dacă răspunsul conține cuvinte clare pentru "toți" → toți merg
        - ORICE ALTCEVA (ambiguu, off-topic, neclar) → doar vorbitorul activ merge (FALLBACK)
        
        Args:
            text (str): Răspunsul user-ului
        """
        log_timestamp(f"💬 [CLARIFY] Procesare răspuns: '{text}'", "router")
        
        # Oprим timeout-ul
        self.clarification_timeout_timer.stop()
        
        # Extragem datele călătoriei
        destination = self.pending_travel_data['destination']
        candidates = self.pending_travel_data['candidates']
        candidate_ids = self.pending_travel_data['candidate_ids']
        
        # Resetăm state-ul
        self.waiting_for_travel_clarification = False
        self.pending_travel_data = None
        
        # Interpretare răspuns - SIMPLU cu fallback clar
        text_lower = text.lower()
        
        # Cuvinte cheie pentru "toți"
        cuvinte_toti = ["toți", "toti", "da", "și", "si", "amândoi", "amandoi", 
                        "toată", "toata", "lumea", "împreună", "impreuna", "cu toții"]
        
        # Verificăm dacă răspunsul conține cuvinte pentru "toți"
        raspuns_toti = any(cuv in text_lower for cuv in cuvinte_toti)
        
        if raspuns_toti:
            # TOȚI MERG
            log_timestamp(f"✅ [CLARIFY] Răspuns CLAR: TOȚI merg la '{destination}'", "router")
            log_timestamp(f"📊 [CLARIFY] Personaje care merg: {[self.active_speaker_id] + candidate_ids}", "router")
            
            # Toți candidații + vorbitorul activ
            all_travelers = [self.active_speaker_id] + candidate_ids
            self._execute_travel_with_characters(destination, all_travelers)
        
        else:
            # FALLBACK: DOAR VORBITORUL ACTIV (indiferent de răspuns)
            log_timestamp(f"⚠️ [CLARIFY] Răspuns AMBIGUU/OFF-TOPIC → FALLBACK: doar vorbitorul activ", "router")
            log_timestamp(f"📊 [CLARIFY] Merge doar: '{self.active_speaker_id}'", "router")
            
            self._execute_travel_with_characters(destination, [self.active_speaker_id])
    
    def _handle_clarification_timeout(self):
        """
        Handler pentru timeout când user-ul nu răspunde la întrebarea de clarificare.
        Fallback: doar vorbitorul activ merge.
        """
        log_timestamp(f"⏱️ [CLARIFY] TIMEOUT! User nu a răspuns în 15s", "router")
        
        if not self.waiting_for_travel_clarification or not self.pending_travel_data:
            return
        
        destination = self.pending_travel_data['destination']
        
        # Resetăm state-ul
        self.waiting_for_travel_clarification = False
        self.pending_travel_data = None
        
        # FALLBACK: doar vorbitorul activ
        log_timestamp(f"⚠️ [CLARIFY] FALLBACK din timeout → doar vorbitorul activ merge", "router")
        self._execute_travel_with_characters(destination, [self.active_speaker_id])


# --- Handlers pentru Modul Învățare ---
    def _handle_start_learning_intent(self, intent_data):
        """
        Punctul central de decizie pentru începerea unei sesiuni de învățare.
        Implementează ierarhia: Voce > Video > Întrebare.
        """
        log_timestamp("🎓 [LEARNING ROUTER] Se procesează intenția 'start_learning'...", "app")
        
        # Pasul 1: Verificare prioritară - Recunoaștere Vocală
        if self._last_identified_speaker:
            student_name = self._last_identified_speaker
            log_timestamp(f"✅ [LEARNING ROUTER] Identificare prin voce reușită: '{student_name}'", "app")
            self.start_learning_session(student_name, intent_data.get("subject"))
            return

        # Pasul 2: Verificare Opțiune "Fără Cameră"
        if self.config.get("conversation_without_camera", False):
            log_timestamp("🚫 [LEARNING ROUTER] Vocea a eșuat și camera este dezactivată. Se cere numele.", "app")
            self.app_state = 'AWAITING_STUDENT_NAME'
            self.pending_learning_intent_data = intent_data
            self._start_tts("[EMOTION:curious] Cine dorește să învețe? Spune-mi, te rog, numele tău.")
            return

        # Pasul 3: Fallback la Analiza Video
        log_timestamp("🎥 [LEARNING ROUTER] Vocea a eșuat, se încearcă identificarea video...", "app")
        self._get_speaker_from_video(intent_data)

    def _get_speaker_from_video(self, intent_data):
        """Pornește un worker Gemini pentru a identifica persoanele din cadru."""
        if not self.webcam_worker or self.webcam_worker.last_frame is None:
            log_timestamp("❌ [LEARNING ROUTER] Camera nu funcționează. Se anulează identificarea video.", "app")
            self.app_state = 'AWAITING_STUDENT_NAME'
            self.pending_learning_intent_data = intent_data
            self._start_tts("[EMOTION:curious] Camera mea nu funcționează. Spune-mi, te rog, numele tău.")
            return
            
        family_briefing = self._generate_family_briefing()
        video_prompt = (
            f"Ești un asistent de recunoaștere facială. Analizează imaginea și informațiile despre familie. "
            f"Răspunde DOAR cu un obiect JSON valid care conține o listă cu numele persoanelor pe care le recunoști. "
            f"Exemplu: {{\"identified_persons\": [\"Andrei\", \"Maria\"]}} sau {{\"identified_persons\": []}}.\n\n"
            f"{family_briefing}"
        )
        
        image_to_send = self.webcam_worker.last_frame.copy()
        model_name = self.config.get("ai_model_name", "models/gemini-flash-lite-latest")

        self.gemini_worker = GeminiWorker(video_prompt, image_to_send, "", model_name)
        self.gemini_thread = QThread()
        self.gemini_worker.moveToThread(self.gemini_thread)

        # Conectăm la un handler special care va continua logica
        self.gemini_worker.response_ready.connect(
            lambda response: self._on_video_speaker_analysis_complete(response, intent_data)
        )
        self.gemini_worker.error_occurred.connect(self.handle_ai_error)
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        
        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_thread.start()
        log_timestamp("🚀 [LEARNING ROUTER] Worker-ul de analiză video a fost pornit.", "app")

    def _handle_student_name_response(self, text):
        """Gestionează răspunsul text după ce am întrebat cine vrea să învețe."""
        student_name_guess = text.strip()
        
        # Căutăm un nume similar în lista familiei
        found_member = next((m for m in self.family_data if student_name_guess.lower() in m.get("name", "").lower()), None)
        
        if found_member:
            student_name = found_member["name"]
            domain_id = self.pending_learning_intent_data.get("subject")
            log_timestamp(f"✅ [LEARNING ROUTER] Nume confirmat: '{student_name}'. Se pornește sesiunea.", "app")
            self.start_learning_session(student_name, domain_id)
        else:
            log_timestamp(f"❌ [LEARNING ROUTER] Numele '{student_name_guess}' nu a fost găsit în familie. Se întreabă din nou.", "app")
            self._start_tts(f"[EMOTION:confuz] Scuze, nu am găsit numele '{student_name_guess}' în lista mea. Poți să repeți, te rog?")
            # Rămânem în starea AWAITING_STUDENT_NAME
            
        # Resetăm starea doar dacă am găsit un nume
        if found_member:
            self.app_state = 'CONVERSATION'
            self.pending_learning_intent_data = None

    def start_learning_session(self, student_name, domain_id):
        """
        Inițiază o sesiune de învățare pentru un student și un domeniu specific.
        Include teleportarea automată la școală.
        """
        log_timestamp(f"🎓 [LEARNING] Inițiere sesiune pentru '{student_name}' cu domeniul specificat: '{domain_id}'", "app")

        # Găsește membrul familie mai întâi
        student_member = next((m for m in self.family_data if m.get("name", "").lower() == student_name.lower()), None)
        if not student_member:
            error_msg = f"[EMOTION:confuz] Nu te găsesc în lista mea, {student_name}. Ești sigur că ți-ai spus numele corect?"
            log_timestamp(f"❌ [LEARNING] Student '{student_name}' nu găsit în family.json", "app")
            QTimer.singleShot(100, lambda: self._start_tts(error_msg))
            return

        # ====================================================================
        # NOUA LOGICĂ PENTRU SELECȚIA DOMENIULUI
        # ====================================================================
        
        # Verificăm dacă studentul are vreun domeniu de învățare configurat
        learning_progress = student_member.get("learning_progress", {})
        if not learning_progress:
            error_msg = f"[EMOTION:neutral] {student_name}, se pare că nu ai niciun domeniu de învățare configurat. Te rog, roagă un adult să te ajute să adaugi unul din setări."
            log_timestamp(f"❌ [LEARNING] Student '{student_name}' nu are domenii de învățare configurate.", "app")
            QTimer.singleShot(100, lambda: self._start_tts(error_msg))
            return
        
        # Dacă nu s-a specificat un domeniu (ex: din "vreau să învăț"), îl alegem noi
        if not domain_id:
            log_timestamp("⚠️ [LEARNING] Niciun domeniu specificat. Se alege automat primul domeniu disponibil pentru student.", "app")
            # Alegem primul domeniu din lista de progres a studentului
            domain_id = list(learning_progress.keys())[0]
        
        # Verificare finală, după ce ne-am asigurat că avem un domain_id
        if domain_id not in self.available_domains:
            error_msg = f"[EMOTION:confuz] Hmm, nu găsesc domeniul '{domain_id}'. Poate nu mai este instalat?"
            log_timestamp(f"❌ [LEARNING] Domeniu inexistent: '{domain_id}'", "app")
            QTimer.singleShot(100, lambda: self._start_tts(error_msg))
            return
        
        # ====================================================================
        # DE AICI, CODUL CONTINUĂ CA ÎNAINTE
        # ====================================================================

        # Logica de teleportare
        if self.scene_manager.current_scene_id != "scoala":
            self.scene_before_lesson = self.scene_manager.current_scene_id
            log_timestamp(f"✈️ [TELEPORT] Teleportare la școală din '{self.scene_before_lesson}'...", "app")
            self._execute_travel_with_characters("scoala", ["cucuvel_owl"])
        else:
            self.scene_before_lesson = "scoala"

        # Verificăm și inițializăm progresul (deși ar trebui să existe deja)
        if domain_id not in learning_progress:
            if "learning_progress" not in student_member: student_member["learning_progress"] = {}
            first_tier_id = self.available_domains[domain_id]["tiers"][0]["tier_id"]
            student_member["learning_progress"][domain_id] = {"current_tier": first_tier_id, "completed_questions": []}
            self._save_family_data()
        
        # Setăm variabilele de stare
        self.teacher_mode_active = True
        
        # SALVARE CONTEXT CONVERSAȚIE LIBERĂ
        self.conversation_log_backup = self.conversation_log.copy()
        log_timestamp(f"💾 [LOG] Salvat backup memorie: {len(self.conversation_log_backup)} replici", "memory")
        
        # Închide log-ul conversației libere
        if self.conversation_log_file and not self.conversation_log_file.closed:
            self.conversation_log_file.write(f"\n--- INTRARE ÎN MODUL ÎNVĂȚARE ({datetime.now().strftime('%H:%M:%S')}) ---\n")
            self.conversation_log_file.close()
            log_timestamp("📝 [LOG] Închis fișier conversație liberă", "app")
        
        self.current_student_name = student_name
        self.current_domain_id = domain_id
        self.current_tier_id = student_member["learning_progress"][domain_id]["current_tier"]
        self.current_curriculum = self.available_domains[domain_id]
        self.session_failed_questions = []
        
        # Deschide log pentru învățare (acum avem tier_id corect)
        if self.conversation_log_filename_base:
            learning_log_name = f"{self.conversation_log_filename_base}_INVATARE_{student_name}_{self.current_tier_id}.txt"
            learning_log_path = self.conversation_logs_folder / learning_log_name
            self.conversation_log_file = open(learning_log_path, "w", encoding="utf-8")
            self.conversation_log_file.write(f"=== SESIUNE ÎNVĂȚARE ===\n")
            self.conversation_log_file.write(f"Student: {student_name}\n")
            self.conversation_log_file.write(f"Domeniu: {domain_id}\n")
            self.conversation_log_file.write(f"Tier: {self.current_tier_id}\n")
            self.conversation_log_file.write(f"Început: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            log_timestamp(f"📝 [LOG] Deschis log învățare: {learning_log_name}", "app")
        
        # Găsim și stocăm datele specifice tier-ului curent
        self.current_tier_data = next((t for t in self.current_curriculum.get("tiers", []) if t.get("tier_id") == self.current_tier_id), None)
        if not self.current_tier_data:
            log_timestamp(f"❌ [LEARNING] Nu am putut găsi datele pentru tier-ul '{self.current_tier_id}'! Se anulează lecția.", "app")
            self.exit_teacher_mode()
            return
            
        self.exit_teacher_button.setVisible(True)
        
        tier_name = self.current_tier_data.get("tier_name", "acest nivel")
        welcome_msg = f"[EMOTION:happy] Salut, {student_name}! Bine ai venit la {tier_name}. Hai să începem!"

        self.pending_first_question = True

        QTimer.singleShot(1000, lambda: self._start_tts(welcome_msg))

    def exit_teacher_mode(self):
        """
        Ieșire din Modul Profesor. Teleportează la pajiște după confirmarea vocală.
        """
        log_timestamp("🛑 [LEARNING] Ieșire din Modul Profesor solicitată.", "app")
        
        if not self.teacher_mode_active:
            log_timestamp("⚠️ [LEARNING] Nu suntem în Modul Profesor. Ignorăm comanda.", "app")
            return
        
        if hasattr(self, 'learning_thread') and self.learning_thread is not None:
            try:
                if self.learning_thread.isRunning():
                    log_timestamp("🧹 [LEARNING] Oprire COMPLETĂ learning_thread...", "cleanup")
                    self.learning_thread.quit()
                    if not self.learning_thread.wait(3000):
                        log_timestamp("⚠️ [LEARNING] Thread nu răspunde - terminare forțată", "cleanup")
                        self.learning_thread.terminate()
                        self.learning_thread.wait(1000)
                    log_timestamp("✅ [LEARNING] Thread oprit cu succes", "cleanup")
            except Exception as e:
                log_timestamp(f"⚠️ [LEARNING] Eroare oprire thread: {e}", "cleanup")
        
        if hasattr(self, 'learning_worker') and self.learning_worker is not None:
            try:
                self.learning_worker.deleteLater()
            except:
                pass
            self.learning_worker = None
        
        # ⭐ RESTAURARE CONTEXT CONVERSAȚIE LIBERĂ ⭐
        # Închide log-ul de învățare
        if self.conversation_log_file and not self.conversation_log_file.closed:
            self.conversation_log_file.write(f"\n=== SESIUNE TERMINATĂ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            self.conversation_log_file.close()
            log_timestamp("📝 [LOG] Închis fișier învățare")
        
        # Restaurează memoria conversației libere
        if self.conversation_log_backup is not None:
            self.conversation_log = self.conversation_log_backup.copy()
            self.conversation_log_backup = None
            log_timestamp(f"💾 [LOG] Restaurat backup memorie: {len(self.conversation_log)} replici")
        
        # Redeschide log-ul conversației libere în append mode
        if self.conversation_log_filename_base:
            log_filename = self.conversation_logs_folder / f"{self.conversation_log_filename_base}.txt"
            self.conversation_log_file = open(log_filename, "a", encoding="utf-8")
            self.conversation_log_file.write(f"\n--- REVENIRE ÎN CONVERSAȚIE LIBERĂ ({datetime.now().strftime('%H:%M:%S')}) ---\n\n")
            log_timestamp(f"📝 [LOG] Redeschis log conversație liberă (append mode)")
        # ⭐ SFÂRȘIT RESTAURARE ⭐
        
        self.teacher_mode_active = False
        self.pending_first_question = False
        self.pending_next_question = False
        student_name_for_farewell = self.current_student_name or "prietene"
        self.current_student_name = None
        self.current_domain_id = None
        self.current_tier_id = None
        self.current_curriculum = None
        self.current_tier_data = None
        self.session_failed_questions = []
        self.current_question_id = None
        self.current_question_attempt = 0
        
        self.exit_teacher_button.setVisible(False)
        self._clear_blackboard()
        
        confirmation_text = f"[EMOTION:happy] O treabă excelentă, {student_name_for_farewell}! Acum hai să luăm o pauză binemeritată pe pajiște!"
        log_timestamp(f"🎓 [LEARNING] Ieșire completă din Modul Profesor. Mesaj: '{confirmation_text}'", "app")
        
        QTimer.singleShot(100, lambda: self._start_tts(confirmation_text, on_finish_slot=self._teleport_to_meadow))

    def _process_student_answer(self, answer_text):
        """
        Procesează răspunsul unui student în Modul Profesor.
        Construiește mega-prompt-ul și trimite la LearningSessionWorker.
        
        Args:
            answer_text (str): Răspunsul dat de student
        """
        log_timestamp(f"🎓 [LEARNING] Procesez răspuns: '{answer_text}'", "app")
        
        # Verificăm dacă așteptăm decizia de continuare tier
        if hasattr(self, 'waiting_for_tier_decision') and self.waiting_for_tier_decision:
            log_timestamp("🎓 [LEARNING] Așteptăm decizie de continuare tier", "app")
            
            # Analizăm răspunsul pentru DA/NU
            answer_lower = answer_text.lower()
            
            if any(word in answer_lower for word in ["da", "yes", "continuă", "continua", "hai", "vreau"]):
                log_timestamp("✅ [LEARNING] Student vrea să continue", "app")
                if self.next_tier_available:
                    self._advance_to_next_tier()
                else:
                    completion_msg = "[EMOTION:happy] Perfect! Dar ai terminat deja toate nivelurile!"
                    QTimer.singleShot(100, lambda: self._start_tts(completion_msg))
                    self.exit_teacher_mode()
                return
            
            elif any(word in answer_lower for word in ["nu", "no", "pauză", "pauza", "stop", "oprește", "opreste"]):
                log_timestamp("🛑 [LEARNING] Student vrea pauză. Se inițiază secvența de ieșire.", "app")
                
                # --- AICI ESTE REPARAȚIA ---
                # Apelăm direct funcția de ieșire. Nu mai avem nevoie de mesaje separate sau timere multiple.
                self.exit_teacher_mode()
                # --- SFÂRȘIT REPARAȚIE ---
                
                return
            
            else:
                # Răspuns ambiguu - repetăm întrebarea
                clarify_msg = "[EMOTION:curious] Nu am înțeles. Vrei să continui sau preferi o pauză?"
                QTimer.singleShot(100, lambda: self._start_tts(clarify_msg))
                return
        
        # Procesare normală - evaluare răspuns la întrebare
        mega_prompt = self._build_mega_prompt(answer_text)
        
        # Curățare thread-uri vechi
        if self.learning_thread:
            try:
                if self.learning_thread.isRunning():
                    log_timestamp("🧹 [LEARNING] Opresc thread vechi de învățare...", "cleanup")
                    self.learning_worker = None
                    self.learning_thread.quit()
                    self.learning_thread.wait(2000)
            except RuntimeError:
                # Thread-ul a fost deja șters
                log_timestamp("🧹 [LEARNING] Thread deja șters - continuăm", "cleanup")
                pass
            finally:
                self.learning_thread = None
                self.learning_worker = None
        
        # Creare worker și thread nou
        log_timestamp("🎓 [LEARNING] Creez LearningSessionWorker...", "app")
        
        self.learning_worker = LearningSessionWorker(mega_prompt)
        self.learning_thread = QThread()
        
        self.learning_worker.moveToThread(self.learning_thread)
        
        # Conectare semnale
        self.learning_thread.started.connect(self.learning_worker.run)
        self.learning_worker.response_ready.connect(self._handle_learning_response)
        self.learning_worker.error_occurred.connect(self._handle_learning_error)
        self.learning_worker.finished.connect(self.learning_thread.quit)
        self.learning_worker.finished.connect(self.learning_worker.deleteLater)
        self.learning_thread.finished.connect(self.learning_thread.deleteLater)
        
        # Pornire thread
        self.learning_thread.start()
        log_timestamp("🎓 [LEARNING] Thread de învățare pornit", "app")

    def _handle_tier_completion(self):
        """Gestionează finalizarea unui tier și programează întrebarea de continuare."""
        log_timestamp("🏆 [LEARNING] Tier completat! Se pregătește întrebarea de continuare.", "app")

        # CURĂȚENIA A FOST MUTATĂ! Această funcție NU mai face curățenie.
        # Rolul ei este doar de a decide ce urmează.
        
        current_tier_index = next((i for i, t in enumerate(self.current_curriculum["tiers"]) if t["tier_id"] == self.current_tier_id), -1)
        
        if current_tier_index == -1:
            QTimer.singleShot(100, self.exit_teacher_mode)
            return
        
        has_next_tier = (current_tier_index + 1) < len(self.current_curriculum["tiers"])

        if has_next_tier:
            next_tier = self.current_curriculum["tiers"][current_tier_index + 1]
            
            # Verifică setarea: să întrebe sau nu despre pauză
            ask_pause = self.config.get("ask_pause_between_tiers", True)
            
            if ask_pause:
                # COMPORTAMENT VECHI: Întreabă copilul
                completion_msg = f"[EMOTION:proud] Bravo, {self.current_student_name}! Ai terminat acest nivel! Vrei să continui cu următorul nivel: '{next_tier['tier_name']}', sau preferi să faci o pauză?"
                self.waiting_for_tier_decision = True
                self.next_tier_available = True
                self.pending_next_tier_id = next_tier["tier_id"]
                
                # Programăm TTS-ul cu întrebarea
                QTimer.singleShot(100, lambda: self._start_tts(completion_msg))
            else:
                # COMPORTAMENT NOU: Avansează direct fără să întrebe
                completion_msg = f"[EMOTION:proud] Bravo, {self.current_student_name}! Ai terminat acest nivel! Acum mergem mai departe la '{next_tier['tier_name']}'!"
                self.waiting_for_tier_decision = False
                self.next_tier_available = True
                self.pending_next_tier_id = next_tier["tier_id"]
                self.auto_advance_to_next_tier = True  # ⭐ SETĂM FLAG
                
                # Programăm TTS
                QTimer.singleShot(100, lambda: self._start_tts(completion_msg))
        else:
            # Ultimul tier din curriculum
            completion_msg = f"[EMOTION:proud] Felicitări, {self.current_student_name}! Ai terminat toate nivelurile din acest domeniu! Ești grozav!"
            self.waiting_for_tier_decision = False
            
            # Programăm TTS-ul final
            QTimer.singleShot(100, lambda: self._start_tts(completion_msg))

    def _ask_next_question(self):
        """
        Selectează, AFIȘEAZĂ (dacă e cazul) și pune următoarea întrebare nerezolvată.
        """
        log_timestamp("❓ [LEARNING] Se caută următoarea întrebare...", "app")
        
        if not self.teacher_mode_active:
            log_timestamp("⚠️ [LEARNING] Nu suntem în Modul Profesor. Anulare.", "app")
            return
        
        student_member = next((m for m in self.family_data if m.get("name") == self.current_student_name), None)
        if not student_member:
            log_timestamp("❌ [LEARNING] Studentul nu a fost găsit în family.json! Se oprește lecția.", "app")
            self.exit_teacher_mode()
            return

        progress_data = student_member.get("learning_progress", {}).get(self.current_domain_id, {})
        completed_questions = progress_data.get("completed_questions", [])
        
        # ⭐ LOG DE DEPANARE #1: Verificăm ce date avem înainte de a căuta
        log_timestamp(f"🕵️ [DEBUG] Date pentru căutare: Student='{self.current_student_name}', Tier='{self.current_tier_id}', Întrebări completate='{completed_questions}'", "app")
        
        questions_in_tier = self.current_tier_data.get("questions", [])
        
        # ⭐ LOG DE DEPANARE #2: Verificăm dacă avem întrebări în tier-ul curent
        log_timestamp(f"🕵️ [DEBUG] Total întrebări găsite în self.current_tier_data: {len(questions_in_tier)}", "app")

        next_question = None
        for q in questions_in_tier:
            q_id = q.get("id")
            if q_id and q_id not in completed_questions and q_id not in self.session_failed_questions:
                next_question = q
                break
        
        # ⭐ LOG DE DEPANARE #3: Verificăm rezultatul căutării
        if next_question:
            log_timestamp(f"🕵️ [DEBUG] REZULTAT: Am găsit următoarea întrebare: ID='{next_question.get('id')}'", "app")
        else:
            log_timestamp(f"🕵️ [DEBUG] REZULTAT: NU am găsit nicio întrebare validă de pus.", "app")

        if not next_question:
            log_timestamp("✅ [LEARNING] Toate întrebările din acest tier au fost abordate! Se finalizează.", "app")
            self._handle_tier_completion()
            return
            
        self.current_question_id = next_question["id"]
        self.current_question_attempt = 0
        
        if "display" in next_question and next_question["display"]:
            log_timestamp(f"칠판 [BLACKBOARD] Afișez: '{next_question['display']}'", "app")
            self._display_on_blackboard(next_question["display"])
        else:
            self._clear_blackboard()

        question_text = f"[EMOTION:curious] {next_question['text']}"
        log_timestamp(f"❓ [LEARNING] Se pune întrebarea: ID={self.current_question_id}", "app")
        
        QTimer.singleShot(150, lambda: self._start_tts(question_text))

    def _handle_learning_response(self, response_dict):
        """
        Procesează răspunsul AI-ului din LearningSessionWorker.
        (VERSIUNE CORECTATĂ PENTRU FINAL DE TIER)
        """
        log_timestamp(f"🎓 [LEARNING] Răspuns primit: {response_dict}", "app")
        
        outcome = response_dict.get("outcome")
        text_to_speak = response_dict.get("text_to_speak", "")
        
        if not text_to_speak:
            log_timestamp("❌ [LEARNING] Răspuns fără text! Se deblochează UI.", "app")
            self.enable_all_actions() # Deblocăm UI-ul dacă AI-ul nu răspunde
            return

        # --- Variabilă pentru callback-ul de final ---
        on_finish_callback = None

        # Procesăm outcome-ul
        if outcome == "correct":
            log_timestamp("✅ [LEARNING] Răspuns corect!", "app")
            self._update_progress_with_correct_answer() # Folosim funcția ajutătoare
            self.pending_next_question = True
            log_timestamp("⏳ [LEARNING] Următoarea întrebare va fi pusă după feedback", "app")
        
        elif outcome == "incorrect_retry":
            log_timestamp("⚠️ [LEARNING] Răspuns greșit - prima încercare", "app")
            self.current_question_attempt += 1
        
        elif outcome == "incorrect_skip":
            log_timestamp("❌ [LEARNING] Răspuns greșit - a doua încercare. Skip.", "app")
            if self.current_question_id not in self.session_failed_questions:
                self.session_failed_questions.append(self.current_question_id)
            self.pending_next_question = True
            log_timestamp("⏳ [LEARNING] Următoarea întrebare va fi pusă după feedback", "app")

        elif outcome == "tier_finished":
            log_timestamp("🏆 [LEARNING] Tier completat!", "app")
            self._update_progress_with_correct_answer()
            # Setăm callback-ul. Atât.
            on_finish_callback = self._handle_tier_completion
            log_timestamp("⏳ [LEARNING] Întrebarea de continuare va fi pusă după felicitări.", "app")
            # --- SFÂRȘIT MODIFICARE ---
        
        # Rostim feedback-ul, pasând callback-ul (care va fi None pentru majoritatea cazurilor)
        QTimer.singleShot(100, lambda: self._start_tts(text_to_speak, on_finish_slot=on_finish_callback))

    def _handle_learning_error(self, error_message):
        """
        Gestionează erorile din LearningSessionWorker.
        
        Args:
            error_message (str): Mesajul de eroare
        """
        log_timestamp(f"❌ [LEARNING] Eroare în worker: {error_message}", "app")
        
        error_msg = "[EMOTION:confuz] Hmm, am avut o problemă tehnică. Hai să încercăm din nou!"
        QTimer.singleShot(100, lambda: self._start_tts(error_msg))

    def _advance_to_next_tier(self):
        """
        Avansează studentul la următorul tier și resetează progresul.
        """
        log_timestamp("⬆️ [LEARNING] Avansare la tier următor...", "app")
        
        # Găsim studentul
        student_member = None
        student_index = None
        for i, member in enumerate(self.family_data):
            if member.get("name", "") == self.current_student_name:
                student_member = member
                student_index = i
                break
        
        if not student_member:
            log_timestamp("❌ [LEARNING] Student dispărut!", "app")
            self.exit_teacher_mode()
            return
        
        # Actualizăm tier-ul curent și resetăm completed_questions
        new_tier_id = self.pending_next_tier_id
        student_member["learning_progress"][self.current_domain_id]["current_tier"] = new_tier_id
        student_member["learning_progress"][self.current_domain_id]["completed_questions"] = []
        
        self._save_family_data()
        
        # Actualizăm variabilele de stare
        self.current_tier_id = new_tier_id
        self.session_failed_questions = []
        
        # Găsim noul tier_data
        for tier_info in self.current_curriculum["tiers"]:
            if tier_info["tier_id"] == new_tier_id:
                self.current_tier_data = tier_info
                break
        
        self.waiting_for_tier_decision = False
        
        log_timestamp(f"✅ [LEARNING] Avans la tier '{new_tier_id}' efectuat!", "app")
        
        # Mesaj de confirmare și prima întrebare
        transition_msg = f"[EMOTION:happy] Perfect! Începem cu {self.current_tier_data['tier_name']}!"

        # ⭐ Setăm flag pentru prima întrebare din noul tier
        self.pending_first_question = True
        log_timestamp("⏳ [LEARNING] Prima întrebare din noul tier va fi pusă după TTS", "app")

        QTimer.singleShot(100, lambda: self._start_tts(transition_msg))

    def _teleport_to_meadow(self):
        """
        Callback apelat după TTS-ul de final de lecție.
        Orchestrează o tranziție sigură către pajiște, cu curățenie completă.
        """
        log_timestamp("✈️ [TELEPORT] Se pregătește tranziția către pajiște...", "app")
        
        if hasattr(self, 'learning_thread') and self.learning_thread is not None:
            try:
                if self.learning_thread.isRunning():
                    log_timestamp("🧹 [TELEPORT] Oprire finală learning_thread...", "cleanup")
                    self.learning_thread.quit()
                    self.learning_thread.wait(2000)
            except Exception as e:
                log_timestamp(f"⚠️ [TELEPORT] Eroare oprire thread: {e}", "cleanup")
        
        self.teacher_mode_active = False
        self.pending_first_question = False
        self.pending_next_question = False
        self.current_student_name = None
        self.current_domain_id = None
        self.current_tier_id = None
        self.current_curriculum = None
        self.current_tier_data = None
        self.session_failed_questions = []
        self.current_question_id = None
        self.current_question_attempt = 0
        
        log_timestamp("✅ [TELEPORT] Stare învățare resetată complet.", "app")
        
        QTimer.singleShot(100, lambda: self._execute_travel_with_characters("pajiste", ["cucuvel_owl"]))
        QTimer.singleShot(1500, self.speech_finished)
        QTimer.singleShot(2000, self._final_conversation_reset)
        
        log_timestamp("✅ [TELEPORT] Tranziție programată. Sistemul va fi gata în ~2 secunde.", "app")        

    def _final_conversation_reset(self):
        """
        Resetare finală și verificată a stării conversației după teleportare.
        """
        log_timestamp("🔄 [RESET] Verificare finală și resetare stare conversație...", "app")
        
        self.is_speaking = False
        self.is_thinking = False
        self.teacher_mode_active = False
        self.pending_first_question = False
        self.pending_next_question = False
        
        active_workers = []
        if self.gemini_worker is not None:
            active_workers.append("gemini")
        if self.learning_worker is not None:
            active_workers.append("learning")
        if self.intent_worker is not None:
            active_workers.append("intent")
        
        if active_workers:
            log_timestamp(f"⚠️ [RESET] Worker-i încă activi: {active_workers} - curățare forțată", "cleanup")
            
            if self.gemini_worker:
                try:
                    self.gemini_worker.deleteLater()
                except:
                    pass
                self.gemini_worker = None
            
            if self.learning_worker:
                try:
                    self.learning_worker.deleteLater()
                except:
                    pass
                self.learning_worker = None
            
            if self.intent_worker:
                try:
                    self.intent_worker.deleteLater()
                except:
                    pass
                self.intent_worker = None
        
        active_threads = []
        if self.gemini_thread and self.gemini_thread.isRunning():
            active_threads.append("gemini")
        if self.learning_thread and self.learning_thread.isRunning():
            active_threads.append("learning")
        if self.intent_thread and self.intent_thread.isRunning():
            active_threads.append("intent")
        
        if active_threads:
            log_timestamp(f"⚠️ [RESET] Thread-uri încă active: {active_threads} - oprire forțată", "cleanup")
            
            if self.gemini_thread and self.gemini_thread.isRunning():
                try:
                    self.gemini_thread.quit()
                    self.gemini_thread.wait(1000)
                except:
                    pass
            
            if self.learning_thread and self.learning_thread.isRunning():
                try:
                    self.learning_thread.quit()
                    self.learning_thread.wait(1000)
                except:
                    pass
            
            if self.intent_thread and self.intent_thread.isRunning():
                try:
                    self.intent_thread.quit()
                    self.intent_thread.wait(1000)
                except:
                    pass
        
        try:
            self.subtitle_scroll_area.hide()
            self.translation_scroll_area.hide()
            self.subtitle_scroll_area.verticalScrollBar().setValue(0)
        except Exception as e:
            log_timestamp(f"⚠️ [RESET] Eroare resetare UI: {e}", "cleanup")
        
        self.enable_all_actions()
        
        if self.voice_worker and not self.is_muted:
            self.voice_worker.set_muted(False)
            log_timestamp("🔊 [RESET] Microfon reactivat și pregătit pentru conversație.", "mute")
        
        # ⭐⭐⭐ ADAUGĂ AICI - RE-CREARE WIDGET-URI SUBTITRĂRI ⭐⭐⭐
        log_timestamp("🔄 [RESET] Re-creare widget-uri subtitrări...", "app")
        
        try:
            self.subtitle_scroll_area.deleteLater()
            self.translation_scroll_area.deleteLater()
        except:
            pass
        
        subtitle_width = int(1820 * 0.8)
        subtitle_height = 150
        subtitle_x = int((1820 - subtitle_width) / 2)
        subtitle_y = 1080 - subtitle_height - 20
        
        self.subtitle_scroll_area = QScrollArea(self.scene_container)
        self.subtitle_scroll_area.setGeometry(subtitle_x, subtitle_y, subtitle_width, subtitle_height)
        self.subtitle_scroll_area.setWidgetResizable(True)
        self.subtitle_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.subtitle_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.subtitle_scroll_area.setStyleSheet("QScrollArea { background: rgba(0, 0, 0, 0.5); border-radius: 10px; border: none; }")
        
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)
        self.subtitle_label.setStyleSheet("QLabel { background: transparent; color: white; padding: 10px; }")
        self.subtitle_scroll_area.setWidget(self.subtitle_label)
        self.subtitle_scroll_area.hide()
        
        translation_width = int(1820 * 0.7)
        translation_height = 120
        translation_x = self.semafor_container.geometry().right() + 20
        translation_y = 20
        
        self.translation_scroll_area = QScrollArea(self.scene_container)
        self.translation_scroll_area.setGeometry(translation_x, translation_y, translation_width, translation_height)
        self.translation_scroll_area.setWidgetResizable(True)
        self.translation_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.translation_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.translation_scroll_area.setStyleSheet("QScrollArea { background: rgba(0, 0, 0, 0.5); border-radius: 10px; border: none; }")
        
        self.translation_label = QLabel()
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.translation_label.setWordWrap(True)
        self.translation_label.setStyleSheet("QLabel { background: transparent; color: white; padding: 10px; font-size: 22px; }")
        self.translation_scroll_area.setWidget(self.translation_label)
        self.translation_scroll_area.hide()
        
        log_timestamp("✅ [RESET] Widget-uri subtitrări re-create cu succes", "app")
        # ⭐⭐⭐ SFÂRȘIT ADĂUGARE ⭐⭐⭐
        
        log_timestamp("✅ [RESET] Sistem COMPLET resetat și verificat - gata pentru conversație normală!", "app")


# =================================================================================
# 9. Logica Vizuală și de Animație
# (Metodele care se ocupă de randare, poziționare și mișcare)
# =================================================================================


# --- Animație și Stare Personaje ---
    def _start_idle_animations(self):
        log_timestamp("☀️ [ANIM] Se repornesc animațiile de idle...", "animator")
        for char in self.character_manager.get_active_characters_list():
            # Repornire animatoare
            for animator in char.animators:
                if isinstance(animator, (BreathingAnimator, BlinkingAnimator)):
                    animator.start()

            # Revenire la emoția neutră
            emotion_animator = next((anim for anim in char.animators if isinstance(anim, EmotionAnimator)), None)
            if emotion_animator:
                emotion_animator.reset_to_neutral()

    def _stop_idle_animations(self):
        log_timestamp("🌙 [ANIM] Se opresc animațiile de idle...", "animator")
        for char in self.character_manager.get_active_characters_list():
            # Oprire animatoare
            for animator in char.animators:
                if isinstance(animator, (BreathingAnimator, BlinkingAnimator)):
                    animator.stop()
            
            # Forțare ochi închiși (dacă are config)
            emotion_animator = next((anim for anim in char.animators if isinstance(anim, EmotionAnimator)), None)
            if emotion_animator:
                emotion_animator.set_emotion('sleeping') # Presupunem că există o emoție "sleeping"

    def stop_thinking(self):
        self.thinking_timer.stop()
        self.is_thinking = False
        # TODO: Aici vom reseta animația de gândire pentru personajul specific
        
    def animate_thinking(self):
        # TODO: Vom implementa o animație de gândire care se aplică personajului care gândește
        pass
        
    def _update_all_animations(self):
            characters_to_update = [
                char for char_id, char in self.character_manager.active_characters.items()
                if char_id in self.character_layers
            ]
            current_scene_id = self.scene_manager.current_scene_id

            for character in characters_to_update:
                try:
                    character_layers = self.character_layers[character.id]
                    # Pasăm acum și scena curentă
                    character.update(character_layers, current_scene_id)
                except Exception as e:
                    log_timestamp(f"❌ [ANIM ERROR] Eroare la actualizarea animației pentru '{character.id}': {e}")
    
    def _idle_animation(self):
        """Metodă placeholder pentru animații idle viitoare."""
        # Deocamdată nu face nimic, dar este necesară pentru a nu crăpa.
        pass

    def _position_character_layers(self, character, layers, scene_config):
        """Funcție ajutătoare pentru a scala și a poziționa layerele unui personaj."""
        scale_raw = scene_config.get("scale", 0.3)
        scale = scale_raw / self.dpi_scaler.scale_factor
        pos_raw = scene_config.get("pos", QPoint(0, 0))
        
        scale_ratio = scale / scale_raw
        
        # Log-uri de debug pentru scalare și poziție
        if LOG_CONFIG.get("ui_debug", False):
            log_timestamp(f"🔍 [SCALE] '{character.id}': raw={scale_raw} → scaled={scale:.3f} (ratio={scale_ratio:.3f})", "ui_debug")        
            log_timestamp("="*60, "ui_debug")
            log_timestamp(f"📍 POZIȚIONARE: '{character.id}'", "ui_debug")
            log_timestamp("="*60, "ui_debug")
            log_timestamp(f"  - Poziție raw (din config): {pos_raw} (tip: {type(pos_raw).__name__})", "ui_debug")
            log_timestamp(f"  - Factor scalare DPI: {self.dpi_scaler.scale_factor}", "ui_debug")
            log_timestamp(f"  - Scalare finală personaj: {scale:.3f}", "ui_debug")
        
        # Scalare poziție pentru DPI
        if isinstance(pos_raw, QPoint):
            pos_orig = (pos_raw.x(), pos_raw.y())
            base_pos = QPoint(self.dpi_scaler.scaled(pos_raw.x()), self.dpi_scaler.scaled(pos_raw.y()))
        elif isinstance(pos_raw, (list, tuple)) and len(pos_raw) >= 2:
            pos_orig = (pos_raw[0], pos_raw[1])
            base_pos = QPoint(self.dpi_scaler.scaled(pos_raw[0]), self.dpi_scaler.scaled(pos_raw[1]))
        else:
            pos_orig = (0, 0)
            base_pos = QPoint(0, 0)
        
        if LOG_CONFIG.get("ui_debug", False):
            log_timestamp(f"  - Poziție originală: {pos_orig}", "ui_debug")
            log_timestamp(f"  - Poziție scalată (bază): ({base_pos.x()}, {base_pos.y()})", "ui_debug")
            log_timestamp(f"  - Dimensiune scenă: {self.scene_container.width()}x{self.scene_container.height()}", "ui_debug")
            if base_pos.x() > self.scene_container.width() or base_pos.y() > self.scene_container.height():
                log_timestamp("  - ⚠️ ATENȚIE: Poziția de bază este în afara scenei!", "ui_debug")
            log_timestamp("="*60, "ui_debug")

        part_offsets = character.components.get("part_offsets", {})
        
        if character.id == "rina_cat":
            log_timestamp(f"📍 [UI POS] Setez poziție Rina: {base_pos}, scale={scale}", "position")
        
        z_order = character.components.get("z_order", [])
        
        for part_name in z_order:
            layer = layers.get(part_name)
            if not layer or not hasattr(layer, 'original_pixmap'):
                continue
            
            original_pixmap = layer.original_pixmap
            if not original_pixmap or original_pixmap.isNull():
                continue
            
            scaled_pixmap = original_pixmap.scaled(
                round(original_pixmap.width() * scale),
                round(original_pixmap.height() * scale),
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            layer.setPixmap(scaled_pixmap)
            layer.setFixedSize(scaled_pixmap.size())
            
            offset = part_offsets.get(part_name, [0, 0])
            
            if isinstance(offset, QPoint):
                offset_x_raw = offset.x()
                offset_y_raw = offset.y()
                offset_x = round(offset_x_raw * scale_ratio)
                offset_y = round(offset_y_raw * scale_ratio)
            elif isinstance(offset, (list, tuple)) and len(offset) >= 2:
                offset_x_raw = offset[0]
                offset_y_raw = offset[1]
                offset_x = round(offset_x_raw * scale_ratio)
                offset_y = round(offset_y_raw * scale_ratio)
            else:
                offset_x_raw, offset_y_raw, offset_x, offset_y = 0, 0, 0, 0
            
            # Logging offset-uri doar la prima rulare a debug-ului
            if LOG_CONFIG.get("ui_debug", False) and not hasattr(self, '_offset_debug_logged'):
                if character.id == "cucuvel_owl" and part_name in ["aripa_stanga", "ochi", "gura"]:
                    log_timestamp(f"  -> 🔍 [OFFSET] '{part_name}': raw=({offset_x_raw}, {offset_y_raw}) × ratio={scale_ratio:.3f} → scaled=({offset_x}, {offset_y})", "ui_debug")
            
            final_x = base_pos.x() + offset_x
            final_y = base_pos.y() + offset_y
            final_pos = QPoint(final_x, final_y)
            
            if LOG_CONFIG.get("position", False) and not hasattr(self, '_pos_debug_logged'):
                if character.id == "cucuvel_owl" and part_name in ["aripa_stanga", "ochi", "gura"]:
                    log_timestamp(f"📍 [POS DEBUG] '{part_name}': base=({base_pos.x()}, {base_pos.y()}), offset=({offset_x}, {offset_y}), final=({final_x}, {final_y})", "position")
            
            layer.move(final_pos)
            layer.raise_()
        
        # Marchează că am făcut debug pentru a nu mai afișa la fiecare mișcare
        if not hasattr(self, '_pos_debug_logged'):
            self._pos_debug_logged = True
            self._offset_debug_logged = True
        
        # Anunță breathing animator că pozițiile s-au schimbat
        for animator in character.animators:
            if isinstance(animator, BreathingAnimator):
                animator.refresh_positions()
                break
                
    def _update_character_for_scene(self, character, scene_id):
        """
        Funcție ajutătoare care actualizează vizibilitatea și poziția
        unui singur personaj în funcție de o scenă dată.
        """
        character.current_scene_id = scene_id
        char_layers = self.character_layers.get(character.id)
        if not char_layers:
            return

        scene_config = character.get_config_for_scene(scene_id)
        
        if scene_config:
            log_timestamp(f"    -> Repoziționez '{character.id}' la {scene_config['pos']} cu scara {scene_config['scale']}")
            self._position_character_layers(character, char_layers, scene_config)
            for layer in char_layers.values():
                layer.show()
        else:
            log_timestamp(f"    -> '{character.id}' nu are configurație pentru '{scene_id}'. Se ascunde.")
            for layer in char_layers.values():
                layer.hide()


# --- Sistemul Gaze (Privire) ---
    def set_speaker(self, speaker_id):
        """
        Setează speaker-ul activ și actualizează TOATE privirile.
        
        Args:
            speaker_id: "user" sau character_id sau None
        """
        if self.current_speaker == speaker_id:
            return  # Deja setat, nu facem nimic
        
        self.current_speaker = speaker_id
        
        if speaker_id:
            log_timestamp(f"🗣️ [GAZE] Speaker nou: '{speaker_id}'", "gaze")
        else:
            log_timestamp(f"🗣️ [GAZE] Speaker resetat (nimeni)", "gaze")
        
        self.update_all_gazes()

    def update_all_gazes(self):
        """
        Actualizează direcția privirii pentru TOATE personajele active.
        """
        if not self.current_speaker:
            log_timestamp(f"👀 [GAZE] Nimeni nu vorbește → toți privesc 'centru'", "gaze")
            for char_id in self.character_manager.active_characters:
                self.set_character_gaze(char_id, "centru")
            return
        
        scene_id = self.scene_manager.current_scene_id
        log_timestamp(f"👀 [GAZE] Speaker: '{self.current_speaker}' → actualizare toate privirile", "gaze")
        
        for char_id in self.character_manager.active_characters:
            direction = self.calculate_gaze_direction(
                observer_id=char_id,
                speaker_id=self.current_speaker,
                scene_id=scene_id
            )
            self.set_character_gaze(char_id, direction)
            
    def set_character_gaze(self, char_id, direction):
        """
        Schimbă asset-ul pentru pupile unui personaj + salvează starea.
        VERSIUNE COMPLETĂ - COPY-PASTE DIRECT
        
        Args:
            char_id: ID-ul personajului
            direction: "stanga" | "centru" | "dreapta"  ⭐ NOTĂ: schimbat de la "left/center/right"
        """
        char = self.character_manager.get_character(char_id)
        char_layers = self.character_layers.get(char_id)
        
        if not char or not char_layers:
            return
        
        # ⭐ SALVĂM STAREA PENTRU BLINKING ANIMATOR
        char.current_gaze_direction = direction
        
        # Verificăm config gaze tracking
        gaze_config = char.components.get("visual_states", {}).get("gaze_tracking")
        if not gaze_config or not gaze_config.get("enabled"):
            return
        
        target_part = gaze_config.get("target_part")
        direction_file = gaze_config.get("directions", {}).get(direction)
        
        if not target_part or not direction_file:
            return
        
        # Schimbăm asset-ul
        target_layer = char_layers.get(target_part)
        if target_layer:
            new_pixmap_path = os.path.join(char.assets_path, direction_file)
            if os.path.exists(new_pixmap_path):
                original_pixmap = QPixmap(new_pixmap_path)
                
                scene_id = self.scene_manager.current_scene_id
                scene_config = char.get_config_for_scene(scene_id)
                if scene_config:
                    scale_raw = scene_config.get("scale", 0.3)
                    scale = scale_raw / self.dpi_scaler.scale_factor  # ⭐ Scalare DPI!

                    scaled_pixmap = original_pixmap.scaled(
                        round(original_pixmap.width() * scale),  # ⭐ round()!
                        round(original_pixmap.height() * scale),  # ⭐ round()!
                        Qt.AspectRatioMode.KeepAspectRatio,  # ⭐
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    target_layer.setPixmap(scaled_pixmap)
                    target_layer.setFixedSize(scaled_pixmap.size())
                    
                    self.gaze_states[char_id] = direction
                    log_timestamp(f"👀 [GAZE] '{char_id}' privește '{direction}'", "gaze")

    def get_character_scene_position(self, char_id, scene_id):
        """
        Citește poziția unui personaj din config pentru o scenă.
        
        Returns:
            QPoint(x, y) sau None dacă nu există
        """
        char = self.character_manager.get_character(char_id)
        if not char:
            log_timestamp(f"❌ [GAZE POS] Personaj '{char_id}' nu există!", "gaze")
            return None
        
        scene_config = char.get_config_for_scene(scene_id)
        if not scene_config:
            log_timestamp(f"❌ [GAZE POS] '{char_id}' nu are config pentru '{scene_id}'!", "gaze")
            return None
        
        pos = scene_config.get("pos")
        log_timestamp(f"🔍 [GAZE POS] '{char_id}' în '{scene_id}': pos raw = {pos} (type: {type(pos)})", "gaze")
        
        # ⭐ CAZUL 1: Deja e QPoint (cel mai comun după prima inițializare)
        if isinstance(pos, QPoint):
            log_timestamp(f"✅ [GAZE POS] '{char_id}' poziție (QPoint direct): QPoint({pos.x()}, {pos.y()})", "gaze")
            return pos
        
        # ⭐ CAZUL 2: Listă din JSON
        if isinstance(pos, list) and len(pos) >= 2:
            result = QPoint(pos[0], pos[1])
            log_timestamp(f"✅ [GAZE POS] '{char_id}' poziție (convertit din listă): QPoint({result.x()}, {result.y()})", "gaze")
            return result
        
        # ⭐ CAZUL 3: Dict (backup)
        if isinstance(pos, dict):
            result = QPoint(pos.get("x", 0), pos.get("y", 0))
            log_timestamp(f"✅ [GAZE POS] '{char_id}' poziție (dict): QPoint({result.x()}, {result.y()})", "gaze")
            return result
        
        log_timestamp(f"❌ [GAZE POS] '{char_id}' format poziție necunoscut: {pos}", "gaze")
        return None

    def calculate_gaze_direction(self, observer_id, speaker_id, scene_id):
        """
        Calculează direcția privirii pentru un observator.
        
        Args:
            observer_id: ID-ul personajului care observă
            speaker_id: "user" sau character_id care vorbește
            scene_id: Scena curentă
        
        Returns:
            "stanga" | "centru" | "dreapta"  ⭐ NOTĂ: schimbat de la "left/center/right"
        """
        log_timestamp(f"🔍 [GAZE CALC] observer='{observer_id}', speaker='{speaker_id}', scene='{scene_id}'", "gaze")
        
        # REGULA 1: Dacă user-ul vorbește → toți în față
        if speaker_id == "user":
            log_timestamp(f"  → REGULA 1: User vorbește → 'centru'", "gaze")
            return "centru"
        
        # REGULA 2: Dacă te uiți la tine însuți → în față
        if observer_id == speaker_id:
            log_timestamp(f"  → REGULA 2: Se uită la el însuși → 'centru'", "gaze")
            return "centru"
        
        # REGULA 3: Calculăm poziția relativă
        observer_pos = self.get_character_scene_position(observer_id, scene_id)
        speaker_pos = self.get_character_scene_position(speaker_id, scene_id)
        
        if not observer_pos or not speaker_pos:
            log_timestamp(f"  → ❌ Lipsesc poziții! observer_pos={observer_pos}, speaker_pos={speaker_pos} → 'centru'", "gaze")
            return "centru"
        
        log_timestamp(f"  → Poziții: observer x={observer_pos.x()}, speaker x={speaker_pos.x()}", "gaze")
        
        # Threshold de 100px pentru diferențiere
        diff = speaker_pos.x() - observer_pos.x()
        log_timestamp(f"  → Diferență X: {diff}px", "gaze")
        
        if speaker_pos.x() < observer_pos.x() - 100:
            log_timestamp(f"  → REGULA 3A: Speaker la stânga → 'stanga'", "gaze")
            return "stanga"
        elif speaker_pos.x() > observer_pos.x() + 100:
            log_timestamp(f"  → REGULA 3B: Speaker la dreapta → 'dreapta'", "gaze")
            return "dreapta"
        else:
            log_timestamp(f"  → REGULA 3C: Speaker aproape → 'centru'", "gaze")
            return "centru" 


# --- Sistemul Tabla (Blackboard) ---
    def _clear_blackboard(self):
        """Ascunde toate elementele de pe tabla virtuală."""
        for label in self.blackboard_labels:
            label.hide()

    def _display_on_blackboard(self, display_string):
        """
        Manager principal - clasifică automat elementele și decide layout-ul.
        Suportă: doar imagini, doar text, sau MIX (imagini + text pe același rând).
        """
        self._clear_blackboard()
        
        if not display_string:
            return
        
        # Parse și clasificare
        elements = [e.strip() for e in display_string.split(',')]
        images = [e for e in elements if e.lower().endswith('.png')]
        text_items = [e for e in elements if not e.lower().endswith('.png')]
        
        log_timestamp(f"칠판 Display: {len(images)} imagini, {len(text_items)} texte", "app")
        
        if images and text_items:
            # MIX: afișează totul pe ACELAȘI rând, în ordinea din string
            self._display_mixed_inline(elements)
        elif images:
            # Doar imagini
            self._display_images_only(images)
        else:
            # Doar text
            self._display_text_only(text_items)

    def _display_mixed_inline(self, elements):
        """
        Afișare MIX INLINE: imagini și text pe ACELAȘI rând, în ordine.
        Ex: mar.png, +, mar.png → 🍎 + 🍎
        """
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QFontMetrics
        from pathlib import Path
        
        BLACKBOARD_RECT = QRect(550, 170, 450, 210)
        PADDING = self.dpi_scaler.scaled(10)
        SPACING = self.dpi_scaler.scaled(15)
        
        util_width = BLACKBOARD_RECT.width() - (2 * PADDING)
        util_height = BLACKBOARD_RECT.height() - (2 * PADDING)
        
        MATH_SYMBOLS = {'-', '+', '=', '×', '÷', '→', '<', '>', '≤', '≥', '?'}
        
        # === PASUL 1: Încarcă imagini și identifică text ===
        element_data = []
        total_image_width = 0
        max_image_height = 0
        
        for elem in elements:
            if elem.lower().endswith('.png'):
                path = Path(resource_path(f"assets/blackboard/objects/{img_filename}"))
                if path.exists():
                    pixmap = QPixmap(str(path))
                    if not pixmap.isNull():
                        element_data.append({
                            'type': 'image',
                            'pixmap': pixmap,
                            'width': pixmap.width(),
                            'height': pixmap.height()
                        })
                        total_image_width += pixmap.width()
                        max_image_height = max(max_image_height, pixmap.height())
            else:
                element_data.append({
                    'type': 'text',
                    'text': elem,
                    'is_math': elem.strip() in MATH_SYMBOLS
                })
        
        if not element_data:
            return
        
        # === PASUL 2: Calculează scalare pentru imagini ===
        # Presupunem că textul va ocupa ~30% din lățime per element
        estimated_text_width = sum(30 for e in element_data if e['type'] == 'text')
        total_estimated_width = total_image_width + estimated_text_width
        
        if len(element_data) > 1:
            total_estimated_width += SPACING * (len(element_data) - 1)
        
        scale_w = util_width / total_estimated_width if total_estimated_width > util_width else 1.0
        scale_h = util_height / max_image_height if max_image_height > util_height else 1.0
        scale = min(scale_w, scale_h, 1.0)
        
        # === PASUL 3: Calculează font bazat pe înălțime SCALATĂ ===
        final_row_height = max_image_height * scale
        text_font_size = int(final_row_height * 0.50)  # 50% din înălțimea scalată
        text_font_size = max(20, min(text_font_size, 150))
        
        text_font = self.chalk_font if self.chalk_font else QFont("Arial")
        text_font.setPointSize(text_font_size)
        text_metrics = QFontMetrics(text_font)
        
        # Calculează dimensiuni reale text
        total_width = 0
        for elem in element_data:
            if elem['type'] == 'image':
                elem['final_width'] = int(elem['width'] * scale)
                elem['final_height'] = int(elem['height'] * scale)
            else:
                text_rect = text_metrics.boundingRect(elem['text'])
                elem['final_width'] = text_rect.width()
                elem['final_height'] = text_rect.height()
            
            total_width += elem['final_width']
        
        if len(element_data) > 1:
            total_width += SPACING * (len(element_data) - 1)
        
        # VERIFICARE: Dacă tot depășește, rescalează totul
        if total_width > util_width:
            adjustment_scale = util_width / total_width
            log_timestamp(f"⚠️ Blackboard overflow, rescalare: {adjustment_scale:.2f}", "app")
            
            # Rescalează tot
            for elem in element_data:
                elem['final_width'] = int(elem['final_width'] * adjustment_scale)
                elem['final_height'] = int(elem['final_height'] * adjustment_scale)
            
            # Recalculează font
            text_font_size = int(text_font_size * adjustment_scale)
            text_font_size = max(12, text_font_size)
            text_font.setPointSize(text_font_size)
            
            total_width = util_width
        
        log_timestamp(f"칠판 Scale: {scale:.2f}, Font: {text_font_size}pt", "app")       




        # === PASUL 4: Calculează poziție start (centrat) ===
        current_x = BLACKBOARD_RECT.left() + PADDING + (util_width - total_width) / 2
        base_y = BLACKBOARD_RECT.top() + PADDING + util_height / 2
        
        # === PASUL 5: Afișează toate elementele ===
        label_index = 0
        
        for elem in element_data:
            if label_index >= len(self.blackboard_labels):
                break
            
            label = self.blackboard_labels[label_index]
            
            if elem['type'] == 'image':
                # Afișează imagine
                scaled_pixmap = elem['pixmap'].scaled(
                    elem['final_width'], elem['final_height'],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                y_pos = base_y - elem['final_height'] / 2
                
                label.setGeometry(
                    int(current_x), 
                    int(y_pos), 
                    elem['final_width'], 
                    elem['final_height']
                )
                label.setPixmap(scaled_pixmap)
                label.setStyleSheet("background-color: transparent;")
                label.show()
                label.raise_()
                
                current_x += elem['final_width'] + SPACING
                
            else:
                # Afișează text
                y_offset = 0
                if elem.get('is_math', False):
                    y_offset = -int(elem['final_height'] * 0.15)
                
                y_pos = base_y - elem['final_height'] / 2 + y_offset
                
                label.setGeometry(
                    int(current_x), 
                    int(y_pos), 
                    elem['final_width'] + 5, 
                    elem['final_height']
                )
                label.setText(elem['text'])
                label.setFont(text_font)
                label.setStyleSheet(
                    f"color: white; font-weight: bold; background-color: transparent; "
                    f"font-family: '{self.chalkboard_font_family}';"
                )
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.show()
                label.raise_()
                
                current_x += elem['final_width'] + SPACING
            
            label_index += 1
        
        QApplication.processEvents()

    def _display_mixed_on_blackboard(self, images, text_items):
        """
        Afișare MIX: imagini în partea de sus, text în partea de jos.
        Layout automat pe 2 zone.
        """
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QFontMetrics
        
        BLACKBOARD_RECT = QRect(550, 170, 450, 210)
        PADDING = self.dpi_scaler.scaled(10)
        VERTICAL_SPLIT = 0.6  # 60% pentru imagini, 40% pentru text
        
        # ZONA 1: Imagini (sus - 60%)
        img_height = int((BLACKBOARD_RECT.height() - PADDING * 3) * VERTICAL_SPLIT)
        img_rect = QRect(
            BLACKBOARD_RECT.left() + PADDING,
            BLACKBOARD_RECT.top() + PADDING,
            BLACKBOARD_RECT.width() - PADDING * 2,
            img_height
        )
        
        # ZONA 2: Text (jos - 40%)
        text_height = BLACKBOARD_RECT.height() - img_height - PADDING * 3
        text_rect = QRect(
            BLACKBOARD_RECT.left() + PADDING,
            img_rect.bottom() + PADDING,
            BLACKBOARD_RECT.width() - PADDING * 2,
            text_height
        )
        
        # Afișează imaginile în zona de sus
        self._render_images_in_rect(images, img_rect, 0)
        
        # Afișează textul în zona de jos
        label_offset = len(images)
        self._render_text_in_rect(text_items, text_rect, label_offset)

    def _display_images_only(self, images):
        """Afișare doar imagini - folosește toată tabla."""
        from PySide6.QtCore import QRect
        
        BLACKBOARD_RECT = QRect(550, 170, 450, 210)
        PADDING = self.dpi_scaler.scaled(5)
        
        img_rect = QRect(
            BLACKBOARD_RECT.left() + PADDING,
            BLACKBOARD_RECT.top() + PADDING,
            BLACKBOARD_RECT.width() - PADDING * 2,
            BLACKBOARD_RECT.height() - PADDING * 2
        )
        
        self._render_images_in_rect(images, img_rect, 0)

    def _display_text_only(self, text_items):
        """Afișare doar text - folosește toată tabla."""
        from PySide6.QtCore import QRect
        
        BLACKBOARD_RECT = QRect(550, 170, 450, 210)
        PADDING = self.dpi_scaler.scaled(10)
        
        text_rect = QRect(
            BLACKBOARD_RECT.left() + PADDING,
            BLACKBOARD_RECT.top() + PADDING,
            BLACKBOARD_RECT.width() - PADDING * 2,
            BLACKBOARD_RECT.height() - PADDING * 2
        )
        
        self._render_text_in_rect(text_items, text_rect, 0)

    def _render_images_in_rect(self, images, rect, label_start_index):
        """
        Randează o listă de imagini într-un QRect dat.
        Suportă multiple rânduri automat.
        """
        from pathlib import Path
        
        MAX_ITEMS_PER_ROW = 6
        SPACING_H = self.dpi_scaler.scaled(10)
        SPACING_V = self.dpi_scaler.scaled(5)
        
        rows = [images[i:i + MAX_ITEMS_PER_ROW] for i in range(0, len(images), MAX_ITEMS_PER_ROW)]
        num_rows = len(rows)
        
        if num_rows == 0:
            return
        
        row_height = (rect.height() - (SPACING_V * (num_rows - 1))) / num_rows
        label_index = label_start_index
        
        for row_idx, row_files in enumerate(rows):
            pixmaps = []
            total_width = 0
            max_height = 0
            
            for filename in row_files:
                path = Path(resource_path(f"assets/blackboard/objects/{filename}"))
                if path.exists():
                    pixmap = QPixmap(str(path))
                    if not pixmap.isNull():
                        pixmaps.append(pixmap)
                        total_width += pixmap.width()
                        max_height = max(max_height, pixmap.height())
            
            if not pixmaps:
                continue
            
            # Calculează scalare
            total_with_spacing = total_width + SPACING_H * (len(pixmaps) - 1)
            scale_w = rect.width() / total_with_spacing if total_with_spacing > rect.width() else 1.0
            scale_h = row_height / max_height if max_height > row_height else 1.0
            scale = min(scale_w, scale_h)
            
            # Calculează poziție start (centrat)
            final_width = (total_width * scale) + (SPACING_H * (len(pixmaps) - 1))
            current_x = rect.left() + (rect.width() - final_width) / 2
            
            # Afișează fiecare imagine
            for pixmap in pixmaps:
                if label_index >= len(self.blackboard_labels):
                    break
                
                label = self.blackboard_labels[label_index]
                
                scaled_w = round(pixmap.width() * scale)
                scaled_h = round(pixmap.height() * scale)
                scaled_pixmap = pixmap.scaled(
                    scaled_w, scaled_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                y_offset = row_idx * (row_height + SPACING_V)
                y_pos = rect.top() + y_offset + (row_height - scaled_h) / 2
                
                label.setGeometry(int(current_x), int(y_pos), scaled_w, scaled_h)
                label.setPixmap(scaled_pixmap)
                label.setStyleSheet("background-color: transparent;")
                label.show()
                label.raise_()
                
                current_x += scaled_w + SPACING_H
                label_index += 1
        
        QApplication.processEvents()

    def _render_text_in_rect(self, text_items, rect, label_start_index):
        """
        Randează o listă de text într-un QRect dat.
        Auto-ajustează fontul pentru a încăpea.
        ÎMBUNĂTĂȚIT: Aliniază corect simbolurile matematice.
        """
        from PySide6.QtGui import QFontMetrics
        
        if not text_items:
            return
        
        # Simboluri care necesită ajustare verticală
        MATH_SYMBOLS = {'-', '+', '=', '×', '÷', '→', '<', '>', '≤', '≥'}
        
        font = self.chalk_font if self.chalk_font else QFont("Arial")
        spacing = 20
        
        # Auto-ajustare font
        font_size = 150
        while font_size > 10:
            font.setPointSize(font_size)
            metrics = QFontMetrics(font)
            
            total_width = sum(metrics.boundingRect(item).width() for item in text_items)
            max_height = max(metrics.boundingRect(item).height() for item in text_items)
            
            if len(text_items) > 1:
                total_width += spacing * (len(text_items) - 1)
            
            if total_width <= rect.width() and max_height <= rect.height():
                break
            
            font_size -= 5
        
        log_timestamp(f"🎨 Blackboard text font: {font_size}px", "app")
        
        # Calculează poziții
        item_widths = [QFontMetrics(font).boundingRect(item).width() + 12 for item in text_items]
        total_width = sum(item_widths) + (spacing * (len(text_items) - 1) if len(text_items) > 1 else 0)
        
        current_x = rect.left() + (rect.width() - total_width) / 2
        item_height = QFontMetrics(font).height()
        base_y = rect.top() + (rect.height() - item_height) / 2
        
        # Afișează fiecare text
        for i, text in enumerate(text_items):
            label_idx = label_start_index + i
            if label_idx >= len(self.blackboard_labels):
                break
            
            label = self.blackboard_labels[label_idx]
            item_width = item_widths[i]
            
            # AJUSTARE VERTICALĂ pentru simboluri matematice
            y_pos = base_y
            is_math_symbol = text.strip() in MATH_SYMBOLS
            
            if is_math_symbol:
                # Ridică simbolurile matematice cu 15% din înălțimea fontului
                vertical_offset = -int(item_height * 0.15)
                y_pos += vertical_offset
            
            # Padding: 12px lateral + 12px SUS pentru diacritice
            safe_width = int(item_width + 24)  # 12px stânga + 12px dreapta
            safe_height = int(item_height + 12)  # 12px doar sus
            adjusted_y = int(y_pos - 12)  # Ridică cu 12px
            
            label.setGeometry(int(current_x), adjusted_y, safe_width, safe_height)

            label.setText(text)
            label.setFont(font)
            label.setStyleSheet(
                f"color: white; font-weight: bold; background-color: transparent; "
                f"font-family: '{self.chalkboard_font_family}';"
            )
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.show()
            label.raise_()
            
            current_x += item_width + spacing
        
        QApplication.processEvents()


# --- Calibrare Tablă ---
    def _activate_calibration(self):
        """Activează modul de calibrare."""
        self.calibration_mode = True
        self.calibration_saved = []
        
        # Înlocuirea blocului de print() cu log_timestamp()
        log_timestamp("="*60, "app")
        log_timestamp("🎯 MOD CALIBRARE TABLĂ ACTIVAT!", "app")
        log_timestamp("   Mergi la scena 'școală' și folosește tastele săgeți pentru a muta punctul.", "app")
        log_timestamp("   Apasă [Spațiu] pentru a salva o coordonată și [Esc] pentru a ieși.", "app")
        log_timestamp("="*60, "app")

    def _update_calibration_display(self):
        """Actualizează poziția punctului de calibrare."""
        if not self.calibration_mode:
            return
        
        label = self.blackboard_labels[0]
        x = self.calibration_point.x()
        y = self.calibration_point.y()
        
        label.setText("●")
        label.setStyleSheet("color: red; font-size: 50px; background-color: yellow;")
        label.setGeometry(x, y, 50, 50)
        label.show()
        label.raise_()
        
        # Înlocuirea blocului de print() cu log_timestamp()
        log_timestamp("="*40, "app")
        log_timestamp(f"📍 COORDONATE CURENTE PUNCT:", "app")
        log_timestamp(f"   X = {x}", "app")
        log_timestamp(f"   Y = {y}", "app")
        log_timestamp("="*40, "app")


# --- Sincronizare Audio-Vizuală (TTS & Vizeme) ---
    def start_sync_process(self, worker_instance, text_for_animation, speaking_character_id, on_finish_slot=None):
        """
        ⚠️ DEPRECATED: Această funcție este păstrată pentru backwards compatibility,
        dar NU ar trebui folosită pentru cod nou. Folosește _start_streaming_tts() în loc.
        """
        log_timestamp("⚠️ [DEPRECATED] start_sync_process() este apelată - consideră folosirea _start_streaming_tts()", "sync")
        
        if self.tts_thread is not None:
            try:
                if self.tts_thread.isRunning():
                    log_timestamp("⚠️ [SYNC] Un ciclu TTS anterior încă rula. Se anulează și se curăță.", "sync")
                    self.tts_thread.quit()
                    self.tts_thread.wait(500)
            except RuntimeError:
                log_timestamp("⚠️ [SYNC] Thread TTS deja șters.", "sync")
                pass
            self.tts_thread = None
        
        self.is_speaking = True
        self.speaking_character_id = speaking_character_id
        self.disable_all_actions()
        
        self.generate_viseme_queue_for_text(text_for_animation)
        
        self.total_viseme_count = len(self.viseme_queue)
        self.last_displayed_frame = -1
        
        self.tts_thread = QThread()
        self.tts_worker = worker_instance
        self.tts_worker.moveToThread(self.tts_thread)
        
        self.tts_worker.audio_ready.connect(self.on_audio_ready)
        self.tts_thread.started.connect(self.tts_worker.run)
        
        self.tts_worker.finished.connect(self.tts_thread.quit)
        self.tts_worker.finished.connect(self.tts_worker.deleteLater)
        self.tts_thread.finished.connect(self.tts_thread.deleteLater)
        if on_finish_slot:
            log_timestamp("🔗 [SYNC] Se conectează callback-ul de finalizare customizat.", "sync")
            self.tts_worker.finished.connect(on_finish_slot)
        else:
            log_timestamp("🔗 [SYNC] Se conectează handler-ul de finalizare default (speech_finished).", "sync")
            self.tts_worker.finished.connect(self.speech_finished)
        
        self.tts_thread.start()

    def _start_streaming_tts(self, text, voice_id, speaking_character_id):
        """
        Pornește sistemul de streaming TTS pentru un text.
        Această funcție înlocuiește logica veche start_sync_process + TTSWorker.
        
        Args:
            text (str): Textul complet de generat
            voice_id (str): ID-ul vocii Edge TTS
            speaking_character_id (str): ID-ul personajului care vorbește
        """
        log_timestamp(f"🎬 [STREAMING TTS] START pentru '{speaking_character_id}'", "sync")
        
        # 1. Setează flag-uri și stare
        self.is_speaking = True
        self.speaking_character_id = speaking_character_id
        self.full_text_for_animation = text
        
        # 2. Dezactivează controalele UI
        self.disable_all_actions()
        
        # 3. Mute microfonul și setează semaforul roșu (CONSTRÂNGERE #2)
        if self.voice_worker:
            log_timestamp("🔇 [STREAMING TTS] Microfonul este pus pe MUTE", "mute")
            self.voice_worker.set_muted(True)
        
        self._update_semafor_state('rosu')
        log_timestamp("🚦 [STREAMING TTS] Semafor setat pe ROȘU", "semafor")
        
        # 4. Setează speaker-ul (pentru gaze/animații)
        self.set_speaker(speaking_character_id)
        

        
        # 6. Numără propozițiile pentru tracking
        sentences = self.streaming_tts._split_into_sentences(text)
        self.sentence_count = len(sentences)
        self.current_sentence_index = 0
        log_timestamp(f"🎬 [STREAMING TTS] Text spart în {self.sentence_count} propoziții", "sync")
        
        # 7. Pornește procesul de streaming
        self.streaming_tts.start_speaking(text, voice_id)
        log_timestamp("✅ [STREAMING TTS] Proces pornit, prima propoziție va începe imediat", "sync")    



    def update_synced_animation(self):
        if not self.is_speaking or self.estimated_speech_duration <= 0:
            self.sync_timer.stop()
            return
        
        # Calculăm progresul PROPOZIȚIEI CURENTE (0.0 - 1.0)
        elapsed = time.time() - self.speech_start_time
        current_sentence_progress = min(elapsed / self.estimated_speech_duration, 1.0)
        
        # Calculăm progresul GLOBAL pe tot textul
        if self.sentence_count > 0:
            completed_sentences = self.current_sentence_index - 1
            global_progress = (completed_sentences + current_sentence_progress) / self.sentence_count
            global_progress = max(0.0, min(1.0, global_progress))
        else:
            global_progress = current_sentence_progress
        
        # Vizeme (folosește progresul LOCAL)
        target_frame = int(current_sentence_progress * self.total_viseme_count)
        if target_frame > self.last_displayed_frame:
            actual_frame = min(target_frame, self.total_viseme_count - 1)
            for i in range(self.last_displayed_frame + 1, actual_frame + 1):
                if i < len(self.viseme_queue):
                    vizem = self.viseme_queue[i]
                    self.set_character_viseme(self.speaking_character_id, vizem)
            self.last_displayed_frame = actual_frame
        
        # Scrolling (folosește progresul GLOBAL)
        scrollbar = self.subtitle_scroll_area.verticalScrollBar()
        max_scroll_value = scrollbar.maximum()
        
        if max_scroll_value > 0:
            target_scroll_value = int(global_progress * max_scroll_value)
            scrollbar.setValue(target_scroll_value)
            

    def generate_viseme_queue_for_text(self, text):
        log_timestamp(f"🎬 [VISEME SIMPLU] Generare pentru: '{text[:50]}...'", "sync")
        self.viseme_queue.clear()
        last_viseme = "Neutru"
        
        for char in text.lower():
            if char in "aeiouăâî":
                current_viseme = "A"
            else:
                current_viseme = "Neutru"
            
            if current_viseme != last_viseme:
                self.viseme_queue.append(current_viseme)
                last_viseme = current_viseme

        if not self.viseme_queue or self.viseme_queue[-1] != "Neutru":
            self.viseme_queue.append("Neutru")

        log_timestamp(f"🎬 [VISEME SIMPLU] ✅ {len(self.viseme_queue)} vizeme generate", "sync")

    def set_character_viseme(self, character_id, vizem):
        """
        Schimbă vizema gurii pentru un personaj, folosind fișierele definite
        în secțiunea 'visual_states' > 'talking' din config.json.
        """
        character = self.character_manager.get_character(character_id)
        char_layers = self.character_layers.get(character_id)
        if not char_layers or not character:
            return

        talk_config = character.components.get("visual_states", {}).get("talking")
        if not talk_config:
            return
            
        target_part_name = talk_config.get("target_part")
        target_layer = char_layers.get(target_part_name)
        if not target_layer:
            return
        
        file_to_load = talk_config.get("open_file") if vizem == "A" else talk_config.get("closed_file")
        if not file_to_load:
            return
            
        pixmap_path = os.path.join(character.assets_path, file_to_load)
        if os.path.exists(pixmap_path):
            pixmap_to_set = QPixmap(pixmap_path)
            if hasattr(target_layer, 'original_pixmap'):
                 scaled_pixmap = pixmap_to_set.scaled(target_layer.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                 target_layer.setPixmap(scaled_pixmap)
        else:
            log_timestamp(f"⚠️ [VISEME] Nu am găsit asset-ul '{file_to_load}' pentru '{character_id}'")

    def play_filler_sound(self, character):
        """Redă un sunet de umplutură specific personajului."""
        sound_file = character.get_random_filler_sound()
        if sound_file:
            log_timestamp(f"🔊 [FILLER] Se redă sunetul de umplutură pentru '{character.id}': {os.path.basename(sound_file)}", "filler")
            try:
                pygame.mixer.Channel(1).play(pygame.mixer.Sound(sound_file))
            except Exception as e:
                log_timestamp(f"❌ [FILLER] Eroare la redarea sunetului: {e}", "filler")
        else:
            log_timestamp(f"🔊 [FILLER] Personajul '{character.id}' nu are sunete de umplutură.", "filler")

    def _start_tts(self, text, on_finish_slot=None):
        """
        Metodă simplificată pentru a porni TTS cu streaming în contextul învățării.
        Gestionează extragerea emoției și un callback opțional la finalizare.
        
        Args:
            text (str): Textul de rostit (poate include [EMOTION:...] la început)
            on_finish_slot (function, optional): O funcție de apelat după ce TTS-ul se termină.
        """
        log_timestamp(f"🔊 [TTS SIMPLE] Pornesc TTS STREAMING pentru: '{text[:50]}...'", "tts")
        
        # DEBUGGING STEP 1
        log_timestamp("🔍 STEP 1: Verificare TTS anterior", "tts_debug")
        try:
            # Oprim orice TTS anterior
            if hasattr(self, 'streaming_tts') and (self.streaming_tts.is_generating or self.streaming_tts.is_playing):
                log_timestamp("⚠️ [TTS] Un TTS anterior încă rula. Se oprește forțat.", "tts")
                self.streaming_tts.stop_all()
                time.sleep(0.2)
            log_timestamp("✅ STEP 1 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 1: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 2
        log_timestamp("🔍 STEP 2: Mute microfon", "tts_debug")
        try:
            # MUTE microfonul ÎNAINTE de a vorbi
            if self.voice_worker:
                self.voice_worker.set_muted(True, is_ai_speaking=True)
                log_timestamp("🔇 [TTS SIMPLE] Microfon mutat pentru a preveni echo", "mute")
            log_timestamp("✅ STEP 2 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 2: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 3
        log_timestamp("🔍 STEP 3: Setare semafor roșu", "tts_debug")
        try:
            # Setează semaforul pe ROȘU
            if self.voice_enabled:
                self._update_semafor_state('rosu')
                log_timestamp("🔴 [TTS SIMPLE] Semafor setat pe ROȘU", "semafor")
            log_timestamp("✅ STEP 3 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 3: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 4
        log_timestamp("🔍 STEP 4: Setare is_speaking flag", "tts_debug")
        try:
            # Marchează că vorbim
            self.is_speaking = True
            log_timestamp("✅ STEP 4 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 4: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 5
        log_timestamp("🔍 STEP 5: Extragere emoție", "tts_debug")
        try:
            # Extragem emoția dacă există
            clean_text = self._extract_and_apply_emotion(text, self.active_speaker_id)
            log_timestamp("✅ STEP 5 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 5: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 6
        log_timestamp("🔍 STEP 6: Obținere speaker character", "tts_debug")
        try:
            # Obținem caracterul care vorbește
            speaking_character = self.character_manager.get_character(self.active_speaker_id)
            if not speaking_character:
                log_timestamp("❌ [TTS SIMPLE] Nu există speaker activ! Se anulează.", "tts")
                self.speech_finished()
                return
            log_timestamp("✅ STEP 6 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 6: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 7
        log_timestamp("🔍 STEP 7: Salvare text pentru repeat", "tts_debug")
        try:
            # Salvăm textul pentru funcționalitatea "Repetă"
            self.last_character_speeches[self.active_speaker_id] = clean_text
            log_timestamp("✅ STEP 7 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 7: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 8
        log_timestamp("🔍 STEP 8: Actualizare subtitrări", "tts_debug")
        try:
            log_timestamp("🔍 STEP 8a: Verificare validitate subtitle widgets", "tts_debug")
            try:
                if hasattr(self, 'subtitle_label') and hasattr(self.subtitle_label, 'isVisible'):
                    self.subtitle_label.isVisible()
                    log_timestamp("✅ STEP 8a: Subtitle widgets sunt valide", "tts_debug")
                else:
                    log_timestamp("⚠️ STEP 8a: Subtitle widgets nu există", "tts_debug")
                    raise RuntimeError("Subtitle widgets missing")
            except (RuntimeError, AttributeError) as e:
                log_timestamp(f"⚠️ STEP 8a: Subtitle widgets invalide ({e}), se re-creează", "tts_debug")
                self._ensure_subtitle_widgets_valid()
                log_timestamp("✅ STEP 8a: Subtitle widgets recreate", "tts_debug")
            
            log_timestamp("🔍 STEP 8b: Setare text în subtitle_label", "tts_debug")
            self.subtitle_label.setText(clean_text)
            log_timestamp("✅ STEP 8b completat", "tts_debug")
            
            log_timestamp("🔍 STEP 8c: adjustSize pe subtitle_label (OMIS pentru stabilitate)", "tts_debug")
            log_timestamp("✅ STEP 8c completat (adjustSize omis)", "tts_debug")
            
            log_timestamp("🔍 STEP 8d: show și raise subtitle_scroll_area", "tts_debug")
            self.subtitle_scroll_area.show()
            self.subtitle_scroll_area.raise_()
            log_timestamp("✅ STEP 8d completat", "tts_debug")
            
            log_timestamp("✅ STEP 8 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 8: {e}", "tts_debug")
            import traceback
            log_timestamp(f"❌ Traceback: {traceback.format_exc()}", "tts_debug")
            raise
        
        # DEBUGGING STEP 10
        log_timestamp("🔍 STEP 10: Setare text pentru echo protection", "tts_debug")
        try:
            if self.voice_worker:
                self.voice_worker.set_last_ai_text(clean_text)
            log_timestamp("✅ STEP 10 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 10: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 11
        log_timestamp("🔍 STEP 11: Ștergere fișier audio vechi", "tts_debug")
        try:
            if hasattr(self, 'last_audio_file_path') and self.last_audio_file_path and os.path.exists(self.last_audio_file_path):
                try:
                    os.remove(self.last_audio_file_path)
                    log_timestamp(f"🧹 Fișier audio vechi șters: {self.last_audio_file_path}", "cleanup")
                except Exception as e:
                    log_timestamp(f"⚠️ Eroare la ștergerea fișierului vechi: {e}", "cleanup")
            log_timestamp("✅ STEP 11 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 11: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 12
        log_timestamp("🔍 STEP 12: Setare speaker pentru animații", "tts_debug")
        try:
            self.set_speaker(self.active_speaker_id)
            log_timestamp("✅ STEP 12 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 12: {e}", "tts_debug")
            raise
        
        
        # DEBUGGING STEP 13
        log_timestamp("🔍 STEP 13: Numărare propoziții", "tts_debug")
        try:
            sentences = self.streaming_tts._split_into_sentences(clean_text)
            self.sentence_count = len(sentences)
            self.current_sentence_index = 0
            log_timestamp("✅ STEP 14 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 14: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 13
        log_timestamp("🔍 STEP 14: Setare callback", "tts_debug")
        try:
            if on_finish_slot:
                log_timestamp(f"🎓 Callback personalizat setat: {on_finish_slot.__name__}", "tts")
                self.pending_tts_callback = on_finish_slot
            else:
                self.pending_tts_callback = None
            log_timestamp("✅ STEP 15 completat", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 15: {e}", "tts_debug")
            raise
        
        # DEBUGGING STEP 14
        log_timestamp("🔍 STEP 15: Pornire streaming TTS", "tts_debug")
        try:
            self.streaming_tts.start_speaking(clean_text, speaking_character.voice_id)
            log_timestamp("✅ TTS STREAMING pornit cu succes", "tts")
            log_timestamp("✅ SUCCES COMPLET!", "tts_debug")
        except Exception as e:
            log_timestamp(f"❌ EROARE la STEP 16: {e}", "tts_debug")
            raise
            
    def _update_semafor_state(self, state, progress=100):
        """Actualizează starea vizuală a semaforului (Versiunea 4, Corectată)."""
        log_timestamp(f"🚦 [SEMAFOR DEBUG] Primit comandă de actualizare. Stare: '{state}', Progres: {progress}", "semafor")
        radius = 55 // 2

        # 1. Resetează becurile Roșu și Verde la "stins"
        self.semafor_rosu_widget.setStyleSheet(f"border-radius: {radius}px; {self.CULORI_SEMAFOR['rosu_stins']}")
        self.semafor_verde_widget.setStyleSheet(f"border-radius: {radius}px; {self.CULORI_SEMAFOR['verde_stins']}")
        
        # 2. Resetează clepsidra la starea "stins" (dar o lasă vizibilă)
        self.clepsidra_container.show() # Asigură-te că este mereu vizibilă când lucrăm cu ea
        self.clepsidra_continut.setStyleSheet(f"background-color: {self.CULORI_SEMAFOR['portocaliu_stins']}; border-radius: {radius}px;")
        self.clepsidra_masca.hide()

        # 3. Aprinde lumina corectă
        if state == 'rosu':
            self.semafor_rosu_widget.setStyleSheet(f"border-radius: {radius}px; {self.CULORI_SEMAFOR['rosu_aprins']}")
        elif state == 'verde':
            self.semafor_verde_widget.setStyleSheet(f"border-radius: {radius}px; {self.CULORI_SEMAFOR['verde_aprins']}")
        elif state == 'pauza':
            # Când e pauză, becurile roșu și verde sunt stinse, deci nu mai facem nimic pentru ele aici.
            # Doar actualizăm clepsidra.
            
            # Aprinde fundalul portocaliu al clepsidrei
            self.clepsidra_continut.setStyleSheet(f"background-color: {self.CULORI_SEMAFOR['portocaliu_aprins']}; border-radius: {radius}px;")
            
            # Calculează și afișează masca
            light_diameter = 55
            mask_height = int(light_diameter * (100 - progress) / 100)
            self.clepsidra_masca.setGeometry(0, 0, light_diameter, mask_height)
            self.clepsidra_masca.show()


# =================================================================================
# 10. Metode Utilitare și de Suport
# (Funcții ajutătoare generale)
# =================================================================================

    def _generate_family_briefing(self):
        """Construiește un bloc de text cu informații despre familie pentru prompt-ul AI."""
        if not hasattr(self, 'family_data') or not self.family_data:
            # --- LOG NOU ---
            log_timestamp("ℹ️ [PROMPT GEN] Nu există date despre familie (self.family_data este goală). Nu se adaugă briefing.", "memory")
            return ""

        # --- LOG NOU ---
        log_timestamp("✅ [PROMPT GEN] Se generează briefing-ul pentru familie. Se vor trimite datele la AI.", "memory")

        briefing = "\n\n--- CUNOȘTINȚE DESPRE FAMILIA UTILIZATORULUI ---\n"
        briefing += "Aceasta este familia cu care vorbești. Sarcina ta este să recunoști acești membri în imagine și să interacționezi cu ei folosind informațiile de mai jos.\n\n"
        briefing += "**Membri Cunoscuți:**\n\n"

        for i, member in enumerate(self.family_data):
            name = member.get("name", "N/A")
            role = member.get("role", "N/A")
            description = member.get("description", "fără descriere")
            
            briefing += f"{i+1}. **Nume: {name}**\n"
            briefing += f"   - **Rol:** {role}\n"
            
            if role == "Copil":
                age = member.get("age", "N/A")
                level = member.get("level", "N/A")
                briefing += f"   - **Vârstă:** {age} ani\n"
                briefing += f"   - **Nivel:** {level}\n"
            elif role == "Animal de companie":
                pet_type = member.get("type", "N/A")
                briefing += f"   - **Tip:** {pet_type}\n"
            else: # Adult
                age = member.get("age", "N/A")
                briefing += f"   - **Vârstă:** {age} ani\n"
                
            briefing += f"   - **Descriere (indicii vizuale):** {description}\n\n"

        briefing += "**REGULI DE INTERACȚIUNE CU FAMILIA:**\n"
        briefing += "- Când vezi pe cineva pentru prima dată în conversație, salută-l pe nume.\n"
        briefing += "- Folosește semnele distinctive pentru a-i deosebi. Dacă vezi un bărbat cu ochelari, este probabil cel descris ca având ochelari.\n"
        briefing += "--- SFÂRȘIT CUNOȘTINȚE FAMILIE ---\n"
        
        return briefing

    def _generate_world_knowledge(self, current_character_id):
        """
        Generează cunoștințe despre TOȚI personajele din lume pentru AI.
        Astfel fiecare personaj știe despre ceilalți, chiar dacă nu sunt pe scenă.
        """
        knowledge = "\n\n--- CUNOȘTINȚE DESPRE LUMEA TA ---\n"
        knowledge += "Iată personajele care există în această lume (chiar dacă nu sunt aici acum):\n\n"
        
        for char_id, char in self.character_manager.available_characters.items():
            if char_id == current_character_id:
                continue  # Nu includem personajul curent
            
            # Informații de bază
            knowledge += f"📌 {char.display_name} ({char_id}):\n"
            knowledge += f"   - Casa: {char.home_scene}\n"
            
            # Unde e acum (verificăm dacă e pe scenă activă)
            if char_id in self.character_manager.active_characters:
                knowledge += f"   - Locație actuală: AICI cu tine (pe scenă)\n"
            else:
                # Verificăm în ce scenă se află (folosind scene_manager pentru tracking)
                current_scene = self.scene_manager.current_scene_id
                if char.home_scene == current_scene:
                    knowledge += f"   - Locație actuală: probabil acasă ({char.home_scene})\n"
                else:
                    knowledge += f"   - Locație actuală: nu e pe scenă (undeva în lume)\n"
            
            # Capacități
            if char.can_leave_home:
                knowledge += f"   - Poate călători în alte locuri\n"
            else:
                knowledge += f"   - Nu poate părăsi casa ({char.home_scene})\n"
            
            if char.can_be_summoned:
                knowledge += f"   - Poate fi chemat prin magie\n"
            
            knowledge += "\n"
        
        knowledge += "IMPORTANT: Dacă utilizatorul întreabă despre acești personaje, tu ȘTII despre ei!\n"
        knowledge += "Dacă nu sunt pe scenă cu tine acum, poți menționa că nu îi vezi aici.\n"
        
        return knowledge

    def _generate_clarification_question(self, destination, candidates_list):
        """
        Generează o întrebare de clarificare pentru AI când există ambiguitate.
        
        Args:
            destination (str): Scena destinație (ex: 'scoala')
            candidates_list (list): Lista de character objects care sunt candidați
        
        Returns:
            str: Întrebarea formatată pentru AI să o spună
        """
        if len(candidates_list) == 1:
            # Un singur candidat
            nume_candidat = candidates_list[0].display_name
            intrebare = f"Mergem la {destination}. Să vină și {nume_candidat} sau doar eu cu tine?"
        else:
            # Multipli candidați
            nume_lista = [char.display_name for char in candidates_list]
            if len(nume_lista) == 2:
                nume_str = f"{nume_lista[0]} și {nume_lista[1]}"
            else:
                nume_str = ", ".join(nume_lista[:-1]) + f" și {nume_lista[-1]}"
            
            intrebare = f"Mergem la {destination}. Să vină și {nume_str} sau doar eu cu tine?"
        
        return intrebare
        
    def _build_mega_prompt(self, student_answer):
        """
        Construiește mega-prompt-ul complet pentru AI în Modul Profesor.
        Acum OPTIMIZAT - nu mai include toate întrebările, doar instrucțiunile din tier_X.txt.
        
        Args:
            student_answer (str): Răspunsul dat de student
            
        Returns:
            str: Prompt-ul complet
        """
        log_timestamp("📝 [LEARNING] Construiesc mega-prompt...", "app")
        
        # Încărcăm personality de bază
        try:
            with open(resource_path("personality.txt"), "r", encoding="utf-8") as f:
                base_personality = f.read()
        except:
            base_personality = "Ești Profesorul Cucuvel, o bufniță înțeleaptă."
        
        # Încărcăm prompt-ul specific pentru tier (DOAR PARTEA PEDAGOGICĂ, fără întrebări)
        tier_prompt_path = Path(resource_path(f"curriculum/{self.current_domain_id}/prompts/{self.current_tier_id}.txt"))
        tier_instructions = ""
        try:
            with open(tier_prompt_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # ⭐ Extragem DOAR partea pedagogică (până la === ÎNTREBĂRI ===)
            if "=== ÎNTREBĂRI ===" in content:
                tier_instructions = content.split("=== ÎNTREBĂRI ===")[0].strip()
            else:
                tier_instructions = content.strip()
        except:
            tier_instructions = "Fii un profesor blând și încurajator."
        
        # Găsim studentul și progresul său
        student_member = None
        for member in self.family_data:
            learning_progress = member.get("learning_progress", {})
            if learning_progress:  # Are cel puțin un domeniu configurat
                student_member = member
                break
        
        if not student_member:
            log_timestamp("❌ [LEARNING] Student dispărut din family.json!", "app")
            return ""
        
        completed_questions = student_member["learning_progress"][self.current_domain_id]["completed_questions"]
        
        # Găsim întrebarea curentă
        current_question_obj = None
        for q in self.current_tier_data["questions"]:
            if q["id"] == self.current_question_id:
                current_question_obj = q
                break
        
        if not current_question_obj:
            log_timestamp("❌ [LEARNING] Întrebare curentă nu găsită!", "app")
            return ""
        
        # Construim mega-prompt-ul (FĂRĂ lista tuturor întrebărilor)
        prompt = f"""
    {base_personality}

    === CONTEXT: MODUL PROFESOR ACTIV ===
    În acest moment, tu (Profesorul Cucuvel) ești în MODUL PROFESOR și predai unui elev.

    **INFORMAȚII DESPRE ELEV:**
    - Nume: {self.current_student_name}
    - Vârstă: {student_member.get('age', 'N/A')} ani
    - Nivel: {student_member.get('level', 'N/A')}

    **INFORMAȚII DESPRE LECȚIE:**
    - Domeniu: {self.current_curriculum['domain_name']}
    - Tier curent: {self.current_tier_data['tier_name']}
    - Descriere tier: {self.current_tier_data.get('description', '')}

    === INSTRUCȚIUNI PEDAGOGICE ===
    {tier_instructions}

    === PROGRES ELEV ÎN ACEST TIER ===
    Total întrebări în tier: {len(self.current_tier_data['questions'])}
    Întrebări completate: {len(completed_questions)}
    Întrebări greșite în sesiunea curentă (skip-uite): {len(self.session_failed_questions)}

    === ÎNTREBAREA CURENTĂ ===
    ID întrebare: {self.current_question_id}
    Text întrebare: {current_question_obj['text']}
    Răspunsuri corecte acceptate: {', '.join(current_question_obj['correct_answers'])}
    Încercarea curentă a elevului la această întrebare: {self.current_question_attempt + 1}

    === RĂSPUNSUL ELEVULUI ===
    Elevul a răspuns: "{student_answer}"

    === SARCINA TA ===
    Analizează răspunsul elevului și decide outcome-ul pentru încercarea curentă. Urmează EXACT logica de mai jos:

    1. **Verifică corectitudinea răspunsului:**
       - Compară răspunsul elevului cu lista de răspunsuri corecte
       - Fii flexibil la variații (majuscule/minuscule, diacritice, plural/singular)
       - Acceptă sinonime apropiate

    2. **Aplică logica pedagogică:**
       
       **DACĂ răspunsul este CORECT:**
       - Outcome: "correct"
       - Laudă elevul cu entuziasm (folosind numele lui!)
       - Treci la următoarea întrebare nerezolvată
       - Dacă era ultima întrebare → outcome: "tier_finished"
       
       **DACĂ răspunsul este GREȘIT (prima încercare la această întrebare):**
       - Outcome: "incorrect_retry"
       - Încurajează elevul cu blândețe
       - Repetă întrebarea (același text, poate cu un mic indiciu)
       - NU da răspunsul corect
       
       **DACĂ răspunsul este GREȘIT (a doua încercare la această întrebare):**
       - Outcome: "incorrect_skip"
       - Fii empatic și spune că veți reveni la întrebare mai târziu
       - Treci la următoarea întrebare nerezolvată
       - NU da răspunsul corect

    3. **Returnează DOAR un obiect JSON cu următoarea structură:**

    {{
      "outcome": "correct" | "incorrect_retry" | "incorrect_skip" | "tier_finished",
      "text_to_speak": "Textul complet pe care Cucuvel trebuie să-l rostească"
    }}

    **IMPORTANT:**
    - text_to_speak trebuie să înceapă cu [EMOTION:...] (ex: [EMOTION:happy], [EMOTION:proud], [EMOTION:attentive])
    - Răspunsul tău trebuie să fie DOAR JSON-ul de mai sus, fără niciun alt text
    - Nu include explicații sau comentarii în afara JSON-ului

    **ANALIZEAZĂ ACUM ȘI RĂSPUNDE CU JSON-UL:**
    """
        
        log_timestamp(f"📝 [LEARNING] Mega-prompt construit ({len(prompt)} caractere)", "app")
        return prompt


    def _update_progress_with_correct_answer(self):
        """Funcție ajutătoare pentru a salva progresul la un răspuns corect."""
        student_member = next((m for m in self.family_data if m.get("name") == self.current_student_name), None)
        if student_member:
            progress = student_member["learning_progress"][self.current_domain_id]
            if self.current_question_id and self.current_question_id not in progress["completed_questions"]:
                progress["completed_questions"].append(self.current_question_id)
                self._save_family_data()
                log_timestamp(f"💾 [LEARNING] Întrebare {self.current_question_id} salvată ca rezolvată", "app")
        self.current_question_attempt = 0

    def _apply_emotion(self, emotion_name, character_id):
        """Funcție ajutătoare simplă pentru a aplica o emoție."""
        log_timestamp(f"🎭 [EMOTION] Se aplică emoția: '{emotion_name}' pentru '{character_id}'", "emotion")
        character = self.character_manager.get_character(character_id)
        if character:
            for animator in character.animators:
                if isinstance(animator, EmotionAnimator):
                    animator.set_emotion(emotion_name)
                    break

    def _extract_and_apply_emotion(self, response_text, character_id):
        """
        Extrage tag-ul de emoție din răspunsul AI și îl aplică.
        Această funcție va fi folosită DOAR ca fallback, dacă parsarea JSON eșuează.
        
        Returns:
            str: Răspunsul curățat (fără tag-ul de emoție)
        """
        import re
        
        # Căutăm pattern-ul [EMOTION:nume_emotie]
        emotion_pattern = r'\[EMOTION:(\w+)\]\s*'
        match = re.match(emotion_pattern, response_text)
        
        emotion_name = "neutral" # Default
        clean_text = response_text

        if match:
            emotion_name = match.group(1).lower()
            clean_text = re.sub(emotion_pattern, '', response_text, count=1).strip()
        
        log_timestamp(f"🎭 [EMOTION] Se aplică emoția: '{emotion_name}' pentru '{character_id}'", "emotion")
        
        # Aplicăm emoția
        character = self.character_manager.get_character(character_id)
        if character:
            for animator in character.animators:
                if isinstance(animator, EmotionAnimator):
                    animator.set_emotion(emotion_name)
                    break
        
        # Stocăm ultima emoție extrasă pentru cazul de fallback
        self.last_extracted_emotion = emotion_name
        return clean_text

    def _populate_family_list(self):
        """Repopulează lista vizuală cu membrii familiei."""
        self.family_list_widget.clear()
        for i, member in enumerate(self.family_data):
            display_text = f"{member.get('name', 'N/A')} ({member.get('role', 'N/A')})"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, i) # Stocăm indexul original în item
            self.family_list_widget.addItem(item)

    def _populate_learning_progress_panel(self, member):
        """
        Populează panoul de progres învățare pentru membrul dat.
        
        Args:
            member (dict): Dicționarul cu datele membrului
        """
        log_timestamp(f"📚 [LEARNING UI] Populez panoul de progres pentru '{member.get('name')}'", "app")
        
        # Golim lista de domenii
        self.domains_list_widget.clear()
        
        # Verificăm dacă membrul are learning_progress
        learning_progress = member.get("learning_progress", {})
        
        if not learning_progress:
            log_timestamp(f"📚 [LEARNING UI] Membrul '{member.get('name')}' nu are domenii de învățare.", "app")
            # Golim și panoul de detalii
            self.tier_combo.clear()
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(1)
            return
        
        # Populăm lista cu domeniile membrului
        for domain_id, progress_data in learning_progress.items():
            if domain_id not in self.available_domains:
                log_timestamp(f"⚠️ [LEARNING UI] Domeniu '{domain_id}' din progres nu mai există!", "app")
                continue
            
            domain_name = self.available_domains[domain_id]["domain_name"]
            item = QListWidgetItem(domain_name)
            item.setData(Qt.UserRole, domain_id)
            self.domains_list_widget.addItem(item)
        
        log_timestamp(f"📚 [LEARNING UI] Au fost găsite {self.domains_list_widget.count()} domenii active.", "app")

    def _update_progress_bar_for_domain(self, domain_id, member):
        """
        Actualizează bara de progres pentru domeniul și membrul specificat.
        
        Args:
            domain_id (str): ID-ul domeniului
            member (dict): Dicționarul cu datele membrului
        """
        if domain_id not in self.available_domains:
            return
        
        domain_data = self.available_domains[domain_id]
        member_progress = member.get("learning_progress", {}).get(domain_id, {})
        
        current_tier_id = member_progress.get("current_tier", "")
        completed_questions = member_progress.get("completed_questions", [])
        
        # Găsim tier-ul curent în datele domeniului
        current_tier_data = None
        for tier_info in domain_data["tiers"]:
            if tier_info["tier_id"] == current_tier_id:
                current_tier_data = tier_info
                break
        
        if not current_tier_data:
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(1)
            return
        
        # Calculăm progresul
        total_questions = len(current_tier_data["questions"])
        completed_count = len(completed_questions)
        
        self.progress_bar.setMaximum(total_questions)
        self.progress_bar.setValue(completed_count)
        
        log_timestamp(f"📊 [LEARNING UI] Progres: {completed_count}/{total_questions} întrebări completate", "app")

    def _trigger_visual_validation(self):
        """
        Pornește un worker Gemini specializat pentru a valida vizual acțiunea copilului.
        """
        if not self.webcam_worker or self.webcam_worker.last_frame is None:
            log_timestamp("❌ [VALIDARE] Camera nu funcționează. Validare anulată.", "app")
            self.add_to_chat("Sistem", "Eroare: Camera nu funcționează.")
            return

        log_timestamp("⏳ [VALIDARE] Se pregătește promptul pentru validarea vizuală...", "app")
        
        # Găsim informațiile despre întrebarea curentă
        current_question_obj = None
        for q in self.current_tier_data["questions"]:
            if q["id"] == self.current_question_id:
                current_question_obj = q
                break
        
        if not current_question_obj:
            log_timestamp("❌ [VALIDARE] Nu s-a găsit întrebarea curentă! Anulare.", "app")
            return

        # Construim promptul specializat pentru validare
        task_description = current_question_obj["text"].replace("Când ești gata, spune tare și clar GATA!", "").strip()
        expected_item = current_question_obj["correct_answers"][0] # Luăm primul răspuns ca referință

        validation_prompt = f"""
Ești un asistent AI specializat în validare vizuală, cu rol de arbitru. Fii strict, obiectiv și precis.

CONTEXT: Un copil a primit următoarea sarcină: "{task_description}"
Se așteaptă ca el să arate la cameră un obiect care este '{expected_item}'.

SARCINA TA: Analizează imaginea atașată și determină dacă acțiunea copilului este corectă. 
- Fii flexibil la nuanțe (ex: roșu deschis/închis).
- Concentrează-te pe obiectul principal prezentat de copil.
- Ignoră alte obiecte din fundal.

Răspunde DOAR cu un obiect JSON valid cu următoarea structură:
{{
  "success": true/false,
  "reason": "O scurtă explicație a deciziei tale. Ex: 'Copilul arată un obiect roșu.' sau 'Obiectul arătat este galben, nu roșu.'"
}}
"""
        
        image_to_send = self.webcam_worker.last_frame.copy()
        model_name = self.config.get("ai_model_name", "models/gemini-flash-lite-latest")

        # Pornim un worker Gemini normal, dar cu un prompt și un handler diferit
        self.gemini_worker = GeminiWorker(validation_prompt, image_to_send, "", model_name)
        self.gemini_thread = QThread()
        self.gemini_worker.moveToThread(self.gemini_thread)

        self.gemini_worker.response_ready.connect(self._handle_visual_validation_response)
        self.gemini_worker.error_occurred.connect(self.handle_ai_error) # Putem refolosi handler-ul de eroare
        self.gemini_worker.finished.connect(self.gemini_thread.quit)
        self.gemini_worker.finished.connect(self.gemini_worker.deleteLater)
        self.gemini_thread.finished.connect(self.gemini_thread.deleteLater)
        
        self.gemini_thread.started.connect(self.gemini_worker.run)
        self.gemini_thread.start()
        log_timestamp("🚀 [VALIDARE] Worker-ul de validare vizuală a fost pornit.", "app")


    def _update_subtitle_style(self):
        """Actualizează stilul CSS pentru subtitrare pe baza setărilor."""
        font_size = self.config.get("subtitle_font_size", 26)
        style = (
            f"background-color: rgba(0, 0, 0, 0.5);"
            f"color: white;"
            f"font-size: {font_size}px;"
            f"font-weight: bold;"
            f"border-radius: 10px;"
            f"padding: 10px;"
        )
        self.subtitle_label.setStyleSheet(style)

    def _transliterate_text(self, text, lang_code):
        """
        Transliterează un text dintr-un alfabet non-latin în caractere latine.
        """
        
        # ... Dicționarele GREEK_MAP și RUSSIAN_MAP rămân neschimbate ...
        GREEK_MAP = {
            'α': 'a', 'β': 'v', 'γ': 'gh', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th',
            'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p',
            'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'i', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
            'ά': 'a', 'έ': 'e', 'ή': 'i', 'ί': 'i', 'ό': 'o', 'ύ': 'i', 'ώ': 'o', 'ϊ': 'i',
            'ϋ': 'i', 'ΐ': 'i', 'ΰ': 'i', 'αι': 'e', 'ει': 'i', 'οι': 'i', 'ου': 'ou',
            'υι': 'i', 'αυ': 'av', 'ευ': 'ev', 'ηυ': 'iv', 'Α': 'A', 'Β': 'V', 'Γ': 'Gh',
            'Δ': 'D', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'I', 'Θ': 'Th', 'Ι': 'I', 'Κ': 'K', 'Λ': 'L',
            'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T',
            'Υ': 'I', 'Φ': 'F', 'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O', 'Ά': 'A', 'Έ': 'E', 'Ή': 'I',
            'Ί': 'I', 'Ό': 'O', 'Ύ': 'I', 'Ώ': 'O'
        }
        RUSSIAN_MAP = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'ye', 'ё': 'yo', 'ж': 'zh',
            'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
            'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
            'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': "'", 'э': 'e', 'ю': 'yu',
            'я': 'ya', 'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'Ye', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
            'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh',
            'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': "'", 'Э': 'E',
            'Ю': 'Yu', 'Я': 'Ya'
        }
        
        # --- BLOC NOU: Dicționar de mapare pentru Japoneză (Hiragana) ---
        JAPANESE_MAP = {
            'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
            'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
            'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
            'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
            'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
            'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
            'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
            'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
            'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
            'わ': 'wa', 'を': 'wo', 'ん': 'n',
            'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
            'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
            'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
            'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
            'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
            'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
            'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
            'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
            'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
            'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
            'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
            'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
            'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
            'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',
            'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
            'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
            '、': ', ', '。': '.', 'ー': ''
        }
        # --- SFÂRȘIT BLOC NOU ---
        
        # Selectăm dicționarul corect
        if lang_code == 'el':
            char_map = GREEK_MAP
        elif lang_code == 'ru':
            char_map = RUSSIAN_MAP
        elif lang_code == 'ja': # <-- ADAUGĂM CONDIȚIA PENTRU JAPONEZĂ
            char_map = JAPANESE_MAP
        else:
            return text

        # Facem înlocuirea
        transliterated_text = ""
        i = 0
        while i < len(text):
            # Căutăm cea mai lungă potrivire posibilă (3, 2, apoi 1 caracter)
            if i + 2 < len(text) and text[i:i+3] in char_map:
                transliterated_text += char_map[text[i:i+3]]
                i += 3
            elif i + 1 < len(text) and text[i:i+2] in char_map:
                transliterated_text += char_map[text[i:i+2]]
                i += 2
            elif text[i] in char_map:
                transliterated_text += char_map[text[i]]
                i += 1
            else:
                transliterated_text += text[i]
                i += 1
        
        return transliterated_text

    def disable_all_actions(self):
        self.text_input.setEnabled(False)
        
    def enable_all_actions(self):
        if self.conversation_state == 'ACTIVE':
            self.text_input.setEnabled(True)
            self.text_input.setFocus()
    
    def _validate_active_speaker(self):
        """
        Verifică dacă active_speaker_id e încă valid (pe scenă).
        Dacă nu, face fallback smart.
        """
        if self.active_speaker_id is None:
            return  # E ok să fie None
        
        if self.active_speaker_id not in self.character_manager.active_characters:
            # Speaker-ul nu mai e pe scenă
            active_chars = list(self.character_manager.active_characters.keys())
            
            if len(active_chars) > 0:
                # Auto-switch la primul disponibil
                self.active_speaker_id = active_chars[0]
                log_timestamp(f"🔄 [SPEAKER] Auto-switch la '{self.active_speaker_id}' (singur disponibil)", "router")
            else:
                # Nimeni pe scenă
                self.active_speaker_id = None
                log_timestamp(f"🔇 [SPEAKER] Niciun personaj pe scenă → speaker = None", "router")

    def _ensure_subtitle_widgets_valid(self):
        """Verifică și re-creează subtitle widgets dacă au devenit invalide."""
        try:
            # Test dacă widget-urile sunt încă valide
            if hasattr(self.subtitle_label, 'isVisible'):
                self.subtitle_label.isVisible()
            return True
        except RuntimeError:
            log_timestamp("⚠️ [SAFETY] Subtitle widgets invalide - se re-creează", "app")
            
            # Re-creează subtitle_scroll_area
            subtitle_width = int(SCENE_WIDTH * 0.8)
            subtitle_height = 150
            subtitle_x = int((SCENE_WIDTH - subtitle_width) / 2)
            subtitle_y = SCENE_HEIGHT - subtitle_height - 20
            
            self.subtitle_scroll_area = QScrollArea(self.scene_container)
            self.subtitle_scroll_area.setGeometry(subtitle_x, subtitle_y, subtitle_width, subtitle_height)
            self.subtitle_scroll_area.setWidgetResizable(True)
            self.subtitle_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.subtitle_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.subtitle_scroll_area.setStyleSheet("QScrollArea { background: rgba(0, 0, 0, 0.5); border-radius: 10px; border: none; }")
            
            self.subtitle_label = QLabel()
            self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.subtitle_label.setWordWrap(True)
            self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)
            self.subtitle_label.setStyleSheet("QLabel { background: transparent; color: white; padding: 10px; }")
            self.subtitle_scroll_area.setWidget(self.subtitle_label)
            self.subtitle_scroll_area.hide()
            
            # Re-creează translation_scroll_area
            translation_width = int(SCENE_WIDTH * 0.7)
            translation_height = 120
            translation_x = self.semafor_container.geometry().right() + 20
            translation_y = 20
            
            self.translation_scroll_area = QScrollArea(self.scene_container)
            self.translation_scroll_area.setGeometry(translation_x, translation_y, translation_width, translation_height)
            self.translation_scroll_area.setWidgetResizable(True)
            self.translation_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.translation_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.translation_scroll_area.setStyleSheet("QScrollArea { background: rgba(0, 0, 0, 0.5); border-radius: 10px; border: none; }")
            
            self.translation_label = QLabel()
            self.translation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.translation_label.setWordWrap(True)
            self.translation_label.setStyleSheet("QLabel { background: transparent; color: white; padding: 10px; font-size: 22px; }")
            self.translation_scroll_area.setWidget(self.translation_label)
            self.translation_scroll_area.hide()
            
            return True


# =================================================================================
# Punct de Intrare
# =================================================================================

if __name__ == "__main__":
    log_timestamp("=" * 60, "app")
    log_timestamp("🎭 TEATRU DIGITAL INTERACTIV - By Aarici Pogonici 🎭", "app")
    log_timestamp("=" * 60, "app")
    
    cleanup_temp_files()
    app = QApplication(sys.argv)
    window = CharacterApp()
    window.show()
    sys.exit(app.exec())