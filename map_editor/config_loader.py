# map_editor/config_loader.py
import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.game_data import SYMBOLS_CONFIG, NPC_CONFIG, WEAPON_CONFIG