# characters/rina_cat/character.py

import os
import math
import random
from PySide6.QtCore import QPoint, QTimer, QObject
from PySide6.QtGui import QPixmap
from ..base_character import BaseCharacter

class RinaCat(BaseCharacter):
    def __init__(self, character_folder_path):
        super().__init__(character_folder_path)
        # Orice altă logică specifică pentru Rina poate veni aici

def get_character_instance(folder_path):
    return RinaCat(character_folder_path=folder_path)