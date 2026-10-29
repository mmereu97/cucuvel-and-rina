# characters/animators.py

import random
import math
import os
import time
from PySide6.QtCore import QObject, QTimer, QPoint, Qt
from PySide6.QtGui import QPixmap

# --- Logging cu acces direct la variabila globală ---
START_TIME = time.time()

# Variabilă globală care va fi setată de main_app
_LOG_CONFIG = None

def set_log_config(config):
    """Setează configurația de logging (apelat din main_app)"""
    global _LOG_CONFIG
    _LOG_CONFIG = config

def log_timestamp(message, category="animator"):
    """Logging cu filtrare pe categorii pentru animatori."""
    global _LOG_CONFIG
    
    # Fallback dacă config nu e setat
    if _LOG_CONFIG is None:
        _LOG_CONFIG = {"animator": True}
    
    if _LOG_CONFIG.get(category, True):
        elapsed = time.time() - START_TIME
        print(f"[{elapsed:8.3f}s] [ANIMATOR] {message}")


# --- CLASA DE BAZĂ PENTRU TOATE ANIMATOARELE ---
class BaseAnimator(QObject):
    def __init__(self, character, layers, dpi_scaler=None):
        super().__init__()
        self.character = character
        self.layers = layers
        self.dpi_scaler = dpi_scaler  # ⭐ ADĂUGAT pentru scalare DPI
    
    def start(self): 
        pass
    
    def stop(self): 
        pass

# --- ANIMATOARE SPECIFICE ---
class BreathingAnimator(BaseAnimator):
    """
    Animator pentru breathing care funcționează perfect cu offset-uri [0,0].
    Salvează pozițiile inițiale și aplică doar micro-offset-uri peste ele.
    """
    def __init__(self, character, layers, dpi_scaler=None):
        super().__init__(character, layers, dpi_scaler)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        
        # ⭐ SCALARE BREATHING AMPLITUDE
        amplitude_raw = character.components.get("breathing_amplitude", 2.0)
        if dpi_scaler:
            self.amplitude = amplitude_raw / dpi_scaler.scale_factor
            log_timestamp(f"🫁 [BREATHING] Amplitude scalat: {amplitude_raw} → {self.amplitude:.2f}", "animator")
        else:
            self.amplitude = amplitude_raw
        
        self.speed = 0.05
        self.character.animation_angle = random.uniform(0, math.pi * 2)
        
        # Salvăm pozițiile inițiale ale layerelor
        self.initial_positions = {}
        for part_name, layer in layers.items():
            self.initial_positions[part_name] = layer.pos()
        
        log_timestamp(f"🫁 [BREATHING] Animator inițializat pentru '{character.id}'", "animator")
    
    def start(self):
        self.timer.start(40)
        log_timestamp(f"▶️ [BREATHING] Start breathing pentru '{self.character.id}'", "animator")
    
    def stop(self):
        self.timer.stop()
        log_timestamp(f"⏹️ [BREATHING] Stop breathing pentru '{self.character.id}'", "animator")
    
    def update(self):
        """
        Aplică breathing ca micro-offset peste pozițiile inițiale.
        NU recalculează nimic din config - folosește doar poziția curentă!
        """
        self.character.animation_angle += self.speed
        if self.character.animation_angle > 2 * math.pi:
            self.character.animation_angle -= 2 * math.pi
        
        # ⭐ FOLOSEȘTE round() în loc de int()
        vertical_offset = round(math.sin(self.character.animation_angle) * self.amplitude)
        head_vertical_offset = round(math.sin(self.character.animation_angle) * (self.amplitude * 0.4))
        
        # DEBUG LOGGING (temporar - doar prima rulare)
        if not hasattr(self, '_debug_logged'):
            log_timestamp(f"🔄 [BREATHING] UPDATE pornit! offset={vertical_offset}, amplitude={self.amplitude}", "animator")
            log_timestamp(f"🔄 [BREATHING] Layere salvate: {list(self.initial_positions.keys())}", "animator")
            self._debug_logged = True
        
        # Grupuri de animație
        anim_groups = self.character.components.get("animation_groups", {})
        body_parts = anim_groups.get("breathing_body", [])
        head_parts = anim_groups.get("breathing_head", [])
        
        # DEBUG: Verificăm grupurile (doar prima rulare)
        if not hasattr(self, '_groups_logged'):
            log_timestamp(f"🔄 [BREATHING] Grupuri: body={body_parts}, head={head_parts}", "animator")
            self._groups_logged = True
        
        # Aplicăm breathing
        for part_name, layer in self.layers.items():
            # Obținem poziția inițială
            initial_pos = self.initial_positions.get(part_name)
            if not initial_pos:
                initial_pos = layer.pos()
                self.initial_positions[part_name] = initial_pos
            
            # Calculăm noua poziție cu breathing
            new_pos = QPoint(initial_pos)
            
            if part_name in body_parts:
                new_pos.setY(initial_pos.y() + vertical_offset)
            elif part_name in head_parts:
                new_pos.setY(initial_pos.y() + head_vertical_offset)
            
            # Mutăm layer-ul
            if layer.pos() != new_pos:
                layer.move(new_pos)
    
    def refresh_positions(self):
        """
        Actualizează pozițiile inițiale - apelat când personajul se mută în altă scenă.
        """
        for part_name, layer in self.layers.items():
            self.initial_positions[part_name] = layer.pos()
        log_timestamp(f"🔄 [BREATHING] Poziții refreshed pentru '{self.character.id}'", "animator")

class BlinkingAnimator(BaseAnimator):
    """
    Animator universal pentru clipit - funcționează identic pentru toate personajele.
    Folosește naming convention standard: ochi_[state]_[direction].png
    
    States: deschisi, semi, inchisi
    Directions: centru, stanga, dreapta
    """
    def __init__(self, character, layers, dpi_scaler=None):
        super().__init__(character, layers, dpi_scaler)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.trigger_blink)
    
    def start(self):
        self.timer.start(random.randint(3000, 7000))
    
    def stop(self):
        self.timer.stop()
    
    def trigger_blink(self):
        """
        Execută secvența de clipit în 3 frame-uri:
        deschisi → semi → inchisi → semi → deschisi
        """
        blink_config = self.character.components.get("visual_states", {}).get("blinking")
        if not blink_config:
            self.timer.start(random.randint(3000, 7000))
            return
        
        target_part_name = blink_config.get("target_part")
        target_layer = self.layers.get(target_part_name)
        if not target_layer:
            self.timer.start(random.randint(3000, 7000))
            return
        
        # Citim timing-ul din config
        timing = blink_config.get("timing", {})
        close_duration = timing.get("close_duration", 50)
        closed_duration = timing.get("closed_duration", 100)
        open_duration = timing.get("open_duration", 50)
        
        # Citim direcția curentă de gaze
        current_gaze = getattr(self.character, 'current_gaze_direction', 'centru')
        
        log_timestamp(f"👀 [BLINK] Clipit pentru '{self.character.id}' cu privire '{current_gaze}'", "animator")
        
        # Construim secvența de 3 frame-uri
        blink_sequence = [
            {"state": "semi", "delay": 0, "duration": close_duration},
            {"state": "inchisi", "delay": close_duration, "duration": closed_duration},
            {"state": "semi", "delay": close_duration + closed_duration, "duration": open_duration},
            {"state": "deschisi", "delay": close_duration + closed_duration + open_duration, "duration": 0}
        ]
        
        # Procesăm fiecare frame
        for frame in blink_sequence:
            state = frame["state"]
            delay = frame["delay"]
            
            # Construim numele fișierului: ochi_{state}_{direction}.png
            filename = f"cap/ochi/ochi_{state}_{current_gaze}.png"
            filepath = os.path.join(self.character.assets_path, filename)
            
            # Fallback: dacă asset-ul cu direcție nu există, folosim centru
            if not os.path.exists(filepath):
                filename_fallback = f"cap/ochi/ochi_{state}_centru.png"
                filepath = os.path.join(self.character.assets_path, filename_fallback)
                
                if not os.path.exists(filepath):
                    log_timestamp(f"⚠️ [BLINK] Asset '{filename}' nu există, skip frame", "animator")
                    continue
            
            # ⭐ ÎNCĂRCARE ȘI SCALARE CORECTĂ
            # Blinking scalează la dimensiunea CURENTĂ a layer-ului (care e deja scalată corect)
            pixmap = QPixmap(filepath).scaled(
                target_layer.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Programăm swap-ul de layer
            QTimer.singleShot(delay, self._create_swap_lambda(target_layer, pixmap))
        
        # Programăm următorul clipit
        total_duration = close_duration + closed_duration + open_duration
        self.timer.start(random.randint(3000, 7000))
    
    def _create_swap_lambda(self, layer, pixmap):
        """
        Helper pentru a crea lambda-uri sigure pentru QTimer.
        Previne RuntimeError când layer-ul e șters între timp.
        """
        def safe_swap():
            try:
                if layer and not layer.isHidden():
                    layer.setPixmap(pixmap)
            except RuntimeError:
                pass
        return safe_swap


class EmotionAnimator(BaseAnimator):
    """
    Animator pentru schimbarea expresiilor emoționale ale personajelor.
    Schimbă multiple layere simultan conform emoției detectate.
    """
    def __init__(self, character, layers, dpi_scaler=None):
        super().__init__(character, layers, dpi_scaler)
        self.current_emotion = "neutral"
        self.available_expressions = character.components.get("visual_states", {}).get("expressions", {})
        
        log_timestamp(f"🎭 [EMOTION] Animator inițializat pentru '{character.id}' cu {len(self.available_expressions)} expresii", "animator")
    
    def start(self):
        """Emotion animator pornește automat odată cu personajul"""
        log_timestamp(f"🎭 [EMOTION] Emotion animator activ pentru '{self.character.id}'", "animator")
    
    def stop(self):
        """Emotion animator nu se oprește niciodată"""
        pass
    
    def set_emotion(self, emotion_name):
        """
        Setează o nouă emoție, schimbând toate layerele necesare.
        ⭐ VERSIUNE CU SCALARE DPI CORECTĂ!
        """
        log_timestamp(f"🎭 [EMOTION DEBUG] === START set_emotion('{emotion_name}') ===", "emotion")
        
        if emotion_name not in self.available_expressions:
            log_timestamp(f"⚠️ [EMOTION] Emoție necunoscută: '{emotion_name}' - folosesc 'neutral'", "emotion")
            emotion_name = "neutral"
        
        if emotion_name == self.current_emotion:
            log_timestamp(f"🎭 [EMOTION] Deja în emoția '{emotion_name}' - skip", "emotion")
            return
        
        log_timestamp(f"🎭 [EMOTION] '{self.character.id}': {self.current_emotion} → {emotion_name}", "emotion")
        
        # ===== STEP 1: Get Expression Config =====
        expression_config = self.available_expressions[emotion_name]
        log_timestamp(f"📋 [EMOTION DEBUG] Expression config pentru '{emotion_name}':", "emotion")
        for part_name, asset_path in expression_config.items():
            log_timestamp(f"   - {part_name}: {asset_path}", "emotion")
        
        # ===== STEP 2: Get Scene Config =====
        scene_config = self.character.get_config_for_scene(self.character.current_scene_id)
        
        if not scene_config:
            log_timestamp(f"⚠️ [EMOTION] Nu am scene_config - skip schimbare emoție", "emotion")
            return
        
        # ⭐⭐⭐ FIX PRINCIPAL: SCALARE SCALE PENTRU DPI ⭐⭐⭐
        scale_raw = scene_config.get("scale", 0.3)
        if self.dpi_scaler:
            scale = scale_raw / self.dpi_scaler.scale_factor
            log_timestamp(f"📏 [EMOTION DEBUG] Scale: raw={scale_raw} → scaled={scale:.3f} (DPI={self.dpi_scaler.scale_factor})", "emotion")
        else:
            scale = scale_raw
            log_timestamp(f"📏 [EMOTION DEBUG] Scale (no DPI): {scale}", "emotion")
        
        # ===== STEP 3: Change Each Layer =====
        log_timestamp(f"🔄 [EMOTION DEBUG] Începem schimbarea layerelor...", "emotion")
        success_count = 0
        
        for part_name, asset_path in expression_config.items():
            log_timestamp(f"🎯 [EMOTION DEBUG] Procesez layer '{part_name}'...", "emotion")
            
            # Check layer exists
            layer = self.layers.get(part_name)
            if not layer:
                log_timestamp(f"⚠️ [EMOTION DEBUG] Layer '{part_name}' NU EXISTĂ în self.layers!", "emotion")
                log_timestamp(f"📊 [EMOTION DEBUG] Layere disponibile: {list(self.layers.keys())}", "emotion")
                continue
            
            log_timestamp(f"✅ [EMOTION DEBUG] Layer '{part_name}' găsit", "emotion")
            
            # Check asset exists
            full_path = os.path.join(self.character.assets_path, asset_path)
            log_timestamp(f"📁 [EMOTION DEBUG] Calea completă asset: {full_path}", "emotion")
            
            if not os.path.exists(full_path):
                log_timestamp(f"❌ [EMOTION DEBUG] Asset NU EXISTĂ: {asset_path}", "emotion")
                continue
            
            log_timestamp(f"✅ [EMOTION DEBUG] Asset există", "emotion")
            
            # Load pixmap
            log_timestamp(f"🖼️ [EMOTION DEBUG] Încărcare pixmap...", "emotion")
            pixmap = QPixmap(full_path)
            
            if pixmap.isNull():
                log_timestamp(f"❌ [EMOTION DEBUG] Pixmap NULL după încărcare!", "emotion")
                continue
            
            log_timestamp(f"✅ [EMOTION DEBUG] Pixmap încărcat: {pixmap.width()}x{pixmap.height()}px", "emotion")
            
            # ⭐ SCALARE CU round() ÎN LOC DE int()
            new_width = round(pixmap.width() * scale)
            new_height = round(pixmap.height() * scale)
            log_timestamp(f"📐 [EMOTION DEBUG] Scalare: {pixmap.width()}x{pixmap.height()} → {new_width}x{new_height}", "emotion")
            
            scaled_pixmap = pixmap.scaled(
                new_width,
                new_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            log_timestamp(f"✅ [EMOTION DEBUG] Pixmap scalat: {scaled_pixmap.width()}x{scaled_pixmap.height()}px", "emotion")
            
            # Get current layer state BEFORE
            old_size = layer.size()
            old_visible = layer.isVisible()
            old_pos = layer.pos()
            
            log_timestamp(f"📊 [EMOTION DEBUG] Layer ÎNAINTE:", "emotion")
            log_timestamp(f"   - Dimensiune: {old_size.width()}x{old_size.height()}", "emotion")
            log_timestamp(f"   - Vizibil: {old_visible}", "emotion")
            log_timestamp(f"   - Poziție: ({old_pos.x()}, {old_pos.y()})", "emotion")
            
            # ⭐ UPDATE LAYER
            layer.setPixmap(scaled_pixmap)
            layer.setFixedSize(scaled_pixmap.size())
            
            # Update original pixmap pentru future rescale
            layer.original_pixmap = pixmap
            
            # Check new state AFTER
            new_size = layer.size()
            new_visible = layer.isVisible()
            new_pos = layer.pos()
            
            log_timestamp(f"📊 [EMOTION DEBUG] Layer DUPĂ:", "emotion")
            log_timestamp(f"   - Dimensiune: {new_size.width()}x{new_size.height()}", "emotion")
            log_timestamp(f"   - Vizibil: {new_visible}", "emotion")
            log_timestamp(f"   - Poziție: ({new_pos.x()}, {new_pos.y()})", "emotion")
            
            success_count += 1
            log_timestamp(f"✅ [EMOTION DEBUG] Layer '{part_name}' actualizat cu succes!", "emotion")
        
        # ===== STEP 4: Summary =====
        self.current_emotion = emotion_name
        log_timestamp(f"🎉 [EMOTION DEBUG] === FINALIZAT: {success_count}/{len(expression_config)} layere actualizate ===", "emotion")
        log_timestamp(f"✅ [EMOTION] Emoție aplicată: '{emotion_name}'", "emotion")

    def reset_to_neutral(self):
        """Resetează expresia la neutral"""
        self.set_emotion("neutral")

# Registry global pentru animatoare
ANIMATOR_REGISTRY = {
    "breathing": BreathingAnimator,
    "blinking": BlinkingAnimator,
    "emotion": EmotionAnimator,
}