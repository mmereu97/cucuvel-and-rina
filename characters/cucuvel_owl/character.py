# characters/cucuvel_owl/character.py

import os
import math
import random
from PySide6.QtCore import QPoint, QTimer, QObject
from PySide6.QtGui import QPixmap
from ..base_character import BaseCharacter

class CucuvelOwl(BaseCharacter):
    def __init__(self, character_folder_path):
        super().__init__(character_folder_path)
        # Orice altă logică specifică pentru Cucuvel poate veni aici

# Funcția standard care returnează o instanță a clasei
def get_character_instance(folder_path):
    return CucuvelOwl(character_folder_path=folder_path)