# managers/character_manager.py

import os
import importlib
import time
from PySide6.QtCore import QObject, Signal
import sys # <-- ⭐ ADAUGĂ ACEASTĂ LINIE NOUĂ ⭐

# --- Logging cu variabilă globală ---
START_TIME = time.time()
_LOG_CONFIG = None

def set_log_config(config):
    """Setează configurația de logging"""
    global _LOG_CONFIG
    _LOG_CONFIG = config

def log_timestamp(message, category="character"):
    """Logging cu filtrare pentru character manager."""
    global _LOG_CONFIG
    
    if _LOG_CONFIG is None:
        _LOG_CONFIG = {"character": True}
    
    if _LOG_CONFIG.get(category, True):
        elapsed = time.time() - START_TIME
        print(f"[{elapsed:8.3f}s] {message}")

class CharacterManager(QObject):
    """
    Gestionează ciclul de viață al personajelor.
    
    Responsabilități:
    - Descoperă automat personajele disponibile din folderul 'characters'.
    - Încarcă modulele și crează instanțe pentru fiecare personaj.
    - Menține o listă cu personajele 'disponibile' și cele 'active' (pe scenă).
    - Emite semnale atunci când un personaj este adăugat sau eliminat de pe scenă,
      pentru ca interfața grafică să se poată actualiza.
    """
    # Semnale pentru a notifica UI-ul de schimbări
    character_added_to_stage = Signal(object) # Trimite instanța completă a personajului adăugat
    character_removed_from_stage = Signal(str)  # Trimite ID-ul personajului eliminat

    def __init__(self, characters_root_folder):
        """
        Inițializează managerul și pornește procesul de descoperire.

        Args:
            characters_root_folder (str): Numele folderului principal unde sunt stocate personajele.
        """
        super().__init__()
        self.root_folder = characters_root_folder
        
        # Dicționar pentru a stoca TOATE personajele încărcate cu succes
        # Format: {'cucuvel_owl': <obiect Cucuvel>, 'misty_cat': <obiect Misty>}
        self.available_characters = {}

        # Dicționar pentru a stoca doar personajele care sunt în prezent pe scenă
        self.active_characters = {}

        self._discover_and_load_characters()

    def _discover_and_load_characters(self):
        """
        Scanează folderul rădăcină, descoperă pachetele de personaje și le încarcă.
        """
        log_timestamp("🌟 [CHAR MANAGER] Pornesc descoperirea personajelor...", "character")
        
        # self.root_folder este acum calea absolută, ex: D:\...\Aarici\dist\TeatruDigital\characters
        if not os.path.exists(self.root_folder) or not os.path.isdir(self.root_folder):
            log_timestamp(f"❌ [CHAR MANAGER] EROARE CRITICĂ: Folderul rădăcină '{self.root_folder}' nu a fost găsit!", "app")
            return

        # Numele folderului rădăcină relativ, ex: "characters"
        relative_root_folder = os.path.basename(self.root_folder)

        for item_name in os.listdir(self.root_folder):
            item_path = os.path.join(self.root_folder, item_name)
            
            if os.path.isdir(item_path) and 'character.py' in os.listdir(item_path):
                log_timestamp(f"  -> Găsit pachet de personaj: '{item_name}'", "character")
                try:
                    # ====================================================================
                    # ⭐⭐ AICI ESTE REPARAȚIA ⭐⭐
                    # Construim numele modulului pentru importlib, ex: "characters.cucuvel_owl.character"
                    # ====================================================================
                    module_path = f"{relative_root_folder}.{item_name}.character"
                    
                    character_module = importlib.import_module(module_path)
                    
                    # Pasăm calea absolută la crearea instanței
                    character_instance = character_module.get_character_instance(item_path)
                    
                    char_id = character_instance.id
                    self.available_characters[char_id] = character_instance
                    log_timestamp(f"  -> ✅ Personajul '{char_id}' încărcat cu succes.", "character")

                except Exception as e:
                    log_timestamp(f"  -> ❌ EROARE la încărcarea personajului din '{item_name}': {e}", "app")
                    continue
        
        log_timestamp(f"🌟 [CHAR MANAGER] Descoperire finalizată. Total personaje disponibile: {len(self.available_characters)}", "character")

    def add_character_to_stage(self, character_id):
        """
        Adaugă un personaj pe scenă (îl face activ).

        Args:
            character_id (str): ID-ul personajului de adăugat (ex: 'cucuvel_owl').
        """
        if character_id in self.available_characters:
            if character_id not in self.active_characters:
                character_instance = self.available_characters[character_id]
                self.active_characters[character_id] = character_instance
                log_timestamp(f"🎭 [CHAR MANAGER] Personaj adăugat pe scenă: '{character_id}'", "character")
                self.character_added_to_stage.emit(character_instance)
            else:
                log_timestamp(f"🎭 [CHAR MANAGER] Personajul '{character_id}' este deja pe scenă.", "character")
        else:
            log_timestamp(f"⚠️ [CHAR MANAGER] Nu s-a putut adăuga. Personajul '{character_id}' nu există sau nu a fost încărcat.", "character")

    def remove_character_from_stage(self, character_id):
        """
        Elimină un personaj de pe scenă (îl face inactiv).

        Args:
            character_id (str): ID-ul personajului de eliminat.
        """
        if character_id in self.active_characters:
            del self.active_characters[character_id]
            log_timestamp(f"🎬 [CHAR MANAGER] Personaj eliminat de pe scenă: '{character_id}'", "character")
            self.character_removed_from_stage.emit(character_id)
        else:
            log_timestamp(f"⚠️ [CHAR MANAGER] Nu s-a putut elimina. Personajul '{character_id}' nu este pe scenă.", "character")

    def get_character(self, character_id):
        """
        Obține instanța unui personaj disponibil după ID.
        """
        return self.available_characters.get(character_id)
        
    def get_active_characters_list(self):
        """
        Returnează o listă cu toate obiectele personajelor active în prezent.
        """
        return list(self.active_characters.values())

    # ========================================================================
    # ⭐ FUNCȚII NOI PENTRU MANAGEMENT SCENE
    # ========================================================================

    def move_character_silent(self, char_id, destination_scene):
        """
        Mută personaj într-o scenă FĂRĂ să schimbe scena utilizatorului.
        Pentru comenzi de tipul "Mergi la X".
        
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        char = self.get_character(char_id)
        
        if not char:
            return False, f"Personajul '{char_id}' nu există."
        
        # Validări
        if not char.can_leave_home:
            return False, f"{char.display_name} nu poate părăsi casa."
        
        if destination_scene not in char.scene_configs:
            return False, f"{char.display_name} nu are configurație pentru scena '{destination_scene}'."
        
        # Elimină din scena curentă (UI)
        if char_id in self.active_characters:
            self.remove_character_from_stage(char_id)
        
        # Actualizează scena internă (backend)
        char.current_scene_id = destination_scene
        
        log_timestamp(f"📦 [CHAR MANAGER] '{char_id}' a fost mutat în '{destination_scene}' (background)", "character")
        return True, None

    def clear_active_characters(self):
        """
        Elimină TOATE personajele de pe scenă (doar din UI, nu din memorie).
        Folosit când user schimbă scena solo.
        """
        char_ids_to_remove = list(self.active_characters.keys())
        for char_id in char_ids_to_remove:
            self.remove_character_from_stage(char_id)
        log_timestamp(f"🧹 [CHAR MANAGER] Toate personajele au fost eliminate din UI", "character")

    def load_native_characters(self, scene_id, scene_manager):
        """
        Încarcă personajele native pentru o scenă.
        
        Args:
            scene_id (str): ID-ul scenei
            scene_manager (SceneManager): Referință la scene manager pentru a obține datele scenei
        """
        scene_data = scene_manager.get_scene_data(scene_id)
        if not scene_data:
            return
        
        native_ids = scene_data.get("native_characters", [])
        log_timestamp(f"🏠 [CHAR MANAGER] Încărcare natives pentru '{scene_id}': {native_ids}", "character")
        
        for char_id in native_ids:
            char = self.get_character(char_id)
            if char:
                # ⭐ VERIFICARE: E native aici, dar e într-adevăr în această scenă?
                if char.current_scene_id is None:
                    # La primul start, natives apar automat acasă
                    log_timestamp(f"🏠 [NATIVE] '{char_id}' nu are scenă setată → apare acasă la '{scene_id}'", "character")
                    char.current_scene_id = scene_id
                    if char_id not in self.active_characters:
                        self.add_character_to_stage(char_id)
                elif char.current_scene_id == scene_id:
                    # E deja în această scenă → apare
                    log_timestamp(f"🏠 [NATIVE] '{char_id}' e deja în '{scene_id}' → apare", "character")
                    if char_id not in self.active_characters:
                        self.add_character_to_stage(char_id)
                else:
                    # E în altă scenă → NU apare
                    log_timestamp(f"🚫 [NATIVE] '{char_id}' e în '{char.current_scene_id}', nu în '{scene_id}' → NU apare", "character")


    def load_visitors_in_scene(self, scene_id):
        """
        Încarcă personajele "vizitatori" care au fost trimise în această scenă anterior.
        ⚠️ DOAR personajele care AU config pentru această scenă!
        """
        log_timestamp(f"👥 [CHAR MANAGER] Verificare vizitatori în '{scene_id}'...", "character")
        
        for char_id, char in self.available_characters.items():
            # Verificări multiple pentru siguranță
            if char.current_scene_id == scene_id and \
               char_id not in self.active_characters and \
               scene_id in char.scene_configs:
                
                self.add_character_to_stage(char_id)
                log_timestamp(f"  ✅ Vizitator găsit: '{char_id}' era deja în '{scene_id}'", "character")


    def sync_characters_for_scene(self, scene_id, scene_manager):
        """
        La schimbarea scenei, sincronizează personajele:
        1. Natives (apar automat)
        2. Visitors (care au fost trimiși aici)
        """
        log_timestamp(f"🔄 [CHAR MANAGER] Sincronizare personaje pentru scenă '{scene_id}'", "character")
        
        # 1. Încarcă natives
        self.load_native_characters(scene_id, scene_manager)
        
        # 2. Încarcă visitors
        self.load_visitors_in_scene(scene_id)
        

    def get_characters_in_scene(self, scene_id):
        """
        Returnează lista de personaje (obiecte) care se află într-o anumită scenă.
        Include atât cei activi pe UI, cât și cei în background.
        """
        chars_in_scene = []
        for char_id, char in self.available_characters.items():
            if char.current_scene_id == scene_id:
                chars_in_scene.append(char)
        return chars_in_scene