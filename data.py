# data.py
import json

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1, "Dex_Penalty": 0},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8, "Dex_Penalty": -2},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3, "Dex_Penalty": 0},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5, "Dex_Penalty": -1},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6, "Dex_Penalty": -1},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2, "Dex_Penalty": 0}
}

FEAT_LIBRARY = {
    "Aegis of Light": {"desc": "Permanent +10 Max HP and +5 Holy skill.", "hp": 10, "skill": ("Mystical", "Holy", 5)},
    "Vaxel Synchronicity": {"desc": "Reduce Arousal gain by 20% and +2 WIS.", "attr": ("WIS", 2)},
    "Bladed Dancer": {"desc": "Ignore Dex penalties from Steel and +2 DEX.", "attr": ("DEX", 2)},
    "Divine Bastion": {"desc": "+2 CON and +2 to all Saving Throws.", "attr": ("CON", 2)},
    "Scholar of the Void": {"desc": "+2 INT; unlock 'Void Navigation' skill.", "attr": ("INT", 2)},
    "Iron Lung": {"desc": "+20 Max Stamina for long engagements.", "stamina": 20},
    "Titan's Grip": {"desc": "Use Two-Handed weapons in one hand; +2 STR.", "attr": ("STR", 2)},
    "Shadow Weaver": {"desc": "Permanent +10 to Stealth; -5 to Noise.", "skill": ("Subterfuge", "Stealth", 10)}
}

INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon', 'level': 10, 'xp': 5600, 'xp_next': 5500,
    'hp': 250, 'hp_max': 250, 'mana': 200, 'mana_max': 200, 'stamina': 180, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95, 'vaxel_state': "Active", 'turn_counter': 0,
    'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
    'conditions': {"Vexal Active": "(-2 to ALL stats)"},
    'feats': [],
    'skills': {
        'Martial': {'One-Handed': 10, 'Two-Handed': 4, 'Bladed': 7, 'Heavy Armor': 8},
        'Mystical': {'Holy': 10, 'Restoration': 7},
        'Professional': {'Survival': 4, 'Athletics': 6},
        'Social': {'Insight': 10, 'Etiquette': 7},
        'Subterfuge': {'Stealth': 2}
    },
    'equipment': {
        'Head': {'item': 'Blessed Circlet', 'material': 'Gold-Filigree', 'cond': 100, 'type': 'Armor'},
        'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel', 'cond': 85, 'type': 'Armor'},
        'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel', 'cond': 100, 'type': 'Weapon', 'dmg': '2d8'},
        'OffHand': {'item': 'Kite Shield', 'material': 'Steel', 'cond': 80, 'type': 'Armor'}
    },
    'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal'],
    'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Lesser Heal': 12},
    'inventory': {'containers': {'Satchel': ['Whetstone', 'Holy Oil']}, 'currency': {'Silver': 150}},
    'prev_eff': {} # For notification tracking
}
