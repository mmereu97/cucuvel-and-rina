# =================================================================================
# CLASĂ DPIScaler - GATA DE COPIAT ÎN main_app.py
# =================================================================================
# Copiază această clasă în main_app.py, DUPĂ importuri, ÎNAINTE de LOG_CONFIG (linia ~60)

class DPIScaler:
    """
    Gestionează scalarea automată pentru diferite DPI-uri și rezoluții.
    
    Funcționare:
    - Detectează DPI-ul ecranului
    - Calculează factor de scalare (1.0 = 100%, 1.25 = 125%, etc.)
    - Scalează toate coordonatele și dimensiunile automat
    
    Utilizare:
        scaler = DPIScaler(QApplication.instance())
        scaled_width = scaler.scaled(1920)
        scaled_rect = scaler.scaled_rect(100, 100, 200, 150)
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
        """Detectează factorul de scalare actual."""
        try:
            # Obține ecranul principal
            primary_screen = self.app.primaryScreen()
            
            if primary_screen:
                # DPI fizic
                physical_dpi = primary_screen.physicalDotsPerInch()
                # DPI logic (după scalare)
                logical_dpi = primary_screen.logicalDotsPerInch()
                
                # Factor de scalare (ex: 125% = 1.25)
                self.scale_factor = logical_dpi / self.base_dpi
                
                # Dimensiuni ecran disponibile
                screen_geometry = primary_screen.availableGeometry()
                self.screen_width = screen_geometry.width()
                self.screen_height = screen_geometry.height()
                
                print("="*80)
                print("🖥️  DETECȚIE DPI ȘI SCALARE")
                print("="*80)
                print(f"Physical DPI: {physical_dpi:.1f}")
                print(f"Logical DPI: {logical_dpi:.1f}")
                print(f"Factor scalare: {self.scale_factor:.2f} ({self.scale_factor*100:.0f}%)")
                print(f"Rezoluție ecran disponibilă: {self.screen_width} x {self.screen_height}")
                print(f"Dimensiuni fereastră scalate automat: {self.scaled(1920)} x {self.scaled(1080)}")
                print("="*80)
            else:
                print("⚠️  Nu s-a putut detecta ecranul principal, folosesc scale_factor=1.0")
                self.scale_factor = 1.0
                self.screen_width = 1920
                self.screen_height = 1080
                
        except Exception as e:
            print(f"❌ Eroare la detectarea DPI: {e}")
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
        
        Exemple:
            scaler.scaled(100) → 125 (la 125% scaling)
            scaler.scaled(1920) → 2400 (la 125% scaling)
        """
        return int(value * self.scale_factor)
    
    def scaled_point(self, x, y):
        """
        Scalează un punct (coordonată 2D).
        
        Args:
            x, y: Coordonate originale
        
        Returns:
            QPoint scalat
        
        Exemple:
            scaler.scaled_point(100, 200) → QPoint(125, 250) (la 125%)
        """
        return QPoint(self.scaled(x), self.scaled(y))
    
    def scaled_rect(self, x, y, width, height):
        """
        Scalează un dreptunghi.
        
        Args:
            x, y: Coordonate colț stânga-sus
            width, height: Dimensiuni
        
        Returns:
            QRect scalat
        
        Exemple:
            scaler.scaled_rect(100, 100, 200, 150)
            → QRect(125, 125, 250, 188) (la 125%)
        """
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
        
        Exemple de structură config_data:
            {
                "scene_configs": {
                    "scoala": {
                        "scale": 0.3,
                        "pos": [150, 550]  ← aceasta se scalează
                    }
                }
            }
        """
        if "scene_configs" in config_data:
            for scene_id, scene_config in config_data["scene_configs"].items():
                if "pos" in scene_config and isinstance(scene_config["pos"], list):
                    original_pos = scene_config["pos"]
                    scaled_pos = [self.scaled(original_pos[0]), self.scaled(original_pos[1])]
                    scene_config["pos"] = scaled_pos
                    print(f"  📍 {scene_id}: {original_pos} → {scaled_pos}")
        
        return config_data
    
    def get_optimal_window_size(self):
        """
        Calculează dimensiunea optimă a ferestrei pentru ecranul curent.
        
        Algoritmul:
        1. Scalează dimensiunile base (1920x1080) cu factorul DPI
        2. Dacă depășește ecranul, reduce proporțional
        3. Centrează fereastra pe ecran
        
        Returns:
            (width, height, x, y) - dimensiuni și poziție
        
        Exemple:
            La 125% scaling pe 1536x864:
            → (1536, 864, 0, 0) - se potrivește exact
            
            La 150% scaling pe 1280x720:
            → (1216, 684, 32, 18) - redus și centrat
        """
        # Dimensiuni dorite base (1920x1080)
        base_width = 1920
        base_height = 1080
        
        # Calculăm dimensiuni scalate
        scaled_width = self.scaled(base_width)
        scaled_height = self.scaled(base_height)
        
        # Dacă depășește ecranul, reducem proporțional
        if scaled_width > self.screen_width or scaled_height > self.screen_height:
            # Calculăm raportul de reducere
            width_ratio = self.screen_width / scaled_width
            height_ratio = (self.screen_height - 50) / scaled_height  # -50 pentru taskbar
            
            # Folosim raportul cel mai mic pentru a încăpea totul
            ratio = min(width_ratio, height_ratio)
            
            scaled_width = int(scaled_width * ratio * 0.95)  # 95% pentru margini
            scaled_height = int(scaled_height * ratio * 0.95)
        
        # Centrăm fereastra
        x = (self.screen_width - scaled_width) // 2
        y = (self.screen_height - scaled_height) // 2
        
        # Asigură-te că nu ieșim din ecran (safety check)
        x = max(0, x)
        y = max(0, y)
        
        return scaled_width, scaled_height, x, y


# =================================================================================
# EXEMPLU DE UTILIZARE
# =================================================================================

if __name__ == "__main__":
    """
    Exemplu de testare a clasei DPIScaler.
    Rulează acest fișier pentru a vedea cum funcționează.
    """
    from PySide6.QtWidgets import QApplication
    import sys
    
    # Creează QApplication
    app = QApplication(sys.argv)
    
    # Creează DPIScaler
    scaler = DPIScaler(app)
    
    print("\n" + "="*80)
    print("EXEMPLE DE SCALARE")
    print("="*80)
    
    # Exemplu 1: Scalare valoare simplă
    print(f"\n1. Scalare dimensiune:")
    print(f"   Original: 1920px")
    print(f"   Scalat: {scaler.scaled(1920)}px")
    
    # Exemplu 2: Scalare punct
    print(f"\n2. Scalare punct:")
    point = scaler.scaled_point(150, 550)
    print(f"   Original: (150, 550)")
    print(f"   Scalat: ({point.x()}, {point.y()})")
    
    # Exemplu 3: Scalare dreptunghi
    print(f"\n3. Scalare dreptunghi (blackboard):")
    rect = scaler.scaled_rect(590, 380, 360, 150)
    print(f"   Original: QRect(590, 380, 360, 150)")
    print(f"   Scalat: QRect({rect.x()}, {rect.y()}, {rect.width()}, {rect.height()})")
    
    # Exemplu 4: Dimensiune optimă fereastră
    print(f"\n4. Dimensiune optimă fereastră:")
    width, height, x, y = scaler.get_optimal_window_size()
    print(f"   Dimensiuni: {width} x {height}")
    print(f"   Poziție: ({x}, {y})")
    
    # Exemplu 5: Scalare config
    print(f"\n5. Scalare configurație personaj:")
    config = {
        "scene_configs": {
            "scoala": {"scale": 0.3, "pos": [150, 550]},
            "acasa": {"scale": 0.35, "pos": [250, 500]}
        }
    }
    print(f"   Original: {config}")
    scaled_config = scaler.scale_config_positions(config)
    print(f"   Scalat: {scaled_config}")
    
    print("\n" + "="*80)
    print("✅ TESTARE COMPLETĂ")
    print("="*80)
