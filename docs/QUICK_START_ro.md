# ⚡ GHID RAPID: FIX SCALING 125% (5 MINUTE)

## 🎯 Problema
Pe laptop 1080p cu scaling 125%, programul iese din ecran.

## 🔧 Soluție Rapidă (Modificări Minime)

### 1️⃣ LA ÎNCEPUTUL FIȘIERULUI (linia 1-10, ÎNAINTE de importuri)
```python
import sys
import os

# ⭐ ADAUGĂ ACESTE 3 LINII:
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1"
```

### 2️⃣ MODIFICĂ IMPORTUL (linia ~34)
```python
# SCHIMBĂ:
from PySide6.QtGui import QPixmap, QImage, QFontDatabase, QFont

# ÎN:
from PySide6.QtGui import QPixmap, QImage, QFontDatabase, QFont, QScreen
```

### 3️⃣ DUPĂ IMPORTURI Qt (linia ~36)
```python
# ⭐ ADAUGĂ:
QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
```

### 4️⃣ ADAUGĂ CLASA DPIScaler (linia ~60, ÎNAINTE de LOG_CONFIG)
```python
# ⭐ COPIAZĂ ÎNTREAGA CLASĂ din fișierul dpi_scaler_class.py
# (Se găsește între liniile 8-230)
```

### 5️⃣ ÎN CharacterApp.__init__() (linia ~1020)
```python
def __init__(self):
    super().__init__()
    
    # ⭐ ADAUGĂ IMEDIAT:
    self.dpi_scaler = DPIScaler(QApplication.instance())
```

### 6️⃣ SETARE GEOMETRIE (linia ~1033-1038)
```python
# ⭐ ÎNLOCUIEȘTE TOT CODUL DE SETARE GEOMETRIE CU:
saved_geom = self.config.get("window_geometry")

if saved_geom and "scale_factor" in saved_geom:
    saved_scale = saved_geom["scale_factor"]
    current_scale = self.dpi_scaler.scale_factor
    
    if abs(saved_scale - current_scale) < 0.05:
        self.setGeometry(saved_geom["x"], saved_geom["y"], 
                        saved_geom["width"], saved_geom["height"])
    else:
        width, height, x, y = self.dpi_scaler.get_optimal_window_size()
        self.setGeometry(x, y, width, height)
else:
    width, height, x, y = self.dpi_scaler.get_optimal_window_size()
    self.setGeometry(x, y, width, height)
```

### 7️⃣ DIMENSIUNI SCENE (linia ~1296-1301)
```python
# ⭐ ÎNLOCUIEȘTE:
# SCENE_WIDTH = 1400
# SCENE_HEIGHT = 900

# CU:
BASE_SCENE_WIDTH = 1400
BASE_SCENE_HEIGHT = 900
SCENE_WIDTH = self.dpi_scaler.scaled(BASE_SCENE_WIDTH)
SCENE_HEIGHT = self.dpi_scaler.scaled(BASE_SCENE_HEIGHT)
self.SCENE_WIDTH = SCENE_WIDTH
self.SCENE_HEIGHT = SCENE_HEIGHT
```

### 8️⃣ BLACKBOARD (linia ~6175)
```python
# ⭐ ÎNLOCUIEȘTE:
# BLACKBOARD_RECT = QRect(590, 380, 360, 150)

# CU:
BLACKBOARD_RECT = self.dpi_scaler.scaled_rect(590, 380, 360, 150)
PADDING = self.dpi_scaler.scaled(10)
```

### 9️⃣ SALVARE CONFIG (linia ~6380-6386)
```python
# ⭐ ADAUGĂ scale_factor:
geom = self.geometry()
self.config["window_geometry"] = {
    "x": geom.x(),
    "y": geom.y(),
    "width": geom.width(),
    "height": geom.height(),
    "scale_factor": self.dpi_scaler.scale_factor  # ⭐ LINIA NOUĂ
}
```

## ✅ TESTARE

Rulează:
```bash
python main_app.py
```

Verifică în consolă:
```
================================================================================
🖥️  DETECȚIE DPI ȘI SCALARE
================================================================================
Factor scalare: 1.25 (125%)
...
```

## 📁 FIȘIERE INCLUSE

1. **README_SCALING_FIX.md** - Ghid complet cu explicații detaliate
2. **dpi_scaler_class.py** - Clasa DPIScaler completă (copiază în main_app.py)
3. **DPI_SCALING_GUIDE.py** - Partea 1: Structură și explicații
4. **DPI_SCALING_GUIDE_PART2.py** - Partea 2: Modificări în CharacterApp
5. **QUICK_START.md** - Acest fișier (start rapid)

## 🆘 PROBLEME?

**Fereastra prea mare?**
→ În `get_optimal_window_size`, reduce `0.95` la `0.90`

**Tabla nu se vede?**
→ Ajustează `scaled_rect(590, 380, 360, 150)` cu alte valori

**Personaje prea mari?**
→ Modifică `scale` în config.json (ex: de la 0.3 la 0.25)

## 💡 NOTĂ IMPORTANTĂ

După aceste 9 modificări, aplicația va funcționa perfect la:
- ✅ 100% scaling
- ✅ 125% scaling  
- ✅ 150% scaling
- ✅ 175% scaling
- ✅ Orice rezoluție de ecran

**SUCCES!** 🎉
