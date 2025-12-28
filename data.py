# data.py
import json

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 5, "Noise": -1, "Dex_Penalty": 0},
    "Steel":   {"DT": 5, "Weight": 45, "Noise": -8, "Dex_Penalty": -2},
    "Mithril": {"DT": 8, "Weight": 12, "Noise": -3, "Dex_Penalty": 0},
    "Aureite": {"DT": 6, "Weight": 25, "Noise": -5, "Dex_Penalty": -1},
    "Silver-Steel": {"DT": 6, "Weight": 35, "Noise": -6, "Dex_Penalty": -1},
    "Gold-Filigree": {"DT": 2, "Weight": 8, "Noise": -2, "Dex_Penalty": 0}
}

INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon', 'level': 10, 'xp': 5600, 'xp_next': 5500,
    'hp': 230, 'hp_max': 250, 'mana': 180, 'mana_max': 200, 'stamina': 160, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95, 'vaxel_state': "Active",
    'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
    'conditions': {"Vexal Active": "(-2 to ALL Attributes, -20 to Pools)"},
    'skills': {
        'Martial': {'One-Handed': 10, 'Two-Handed': 4, 'Bladed': 7, 'Blunt': 4, 'Blocking': 5, 'Heavy Armor': 8, 'Light Armor': 3, 'Marksmanship': 3},
        'Mystical': {'Holy': 10, 'Arcane': 4, 'Elemental': 3, 'Restoration': 7, 'Void Navigation': 0},
        'Professional': {'Alchemy': 2, 'Enchanting': 4, 'Survival': 4, 'Athletics': 6, 'Blacksmithing': 4},
        'Social': {'Persuasion': 3, 'Intimidation': 3, 'Insight': 10, 'Etiquette': 7},
        'Subterfuge': {'Stealth': 2, 'Lockpicking': 1, 'Trap Disarming': 1}
    },
    'equipment': {
        'Head': {'item': 'Blessed Circlet', 'material': 'Gold-Filigree', 'cond': 100, 'type': 'Armor'},
        'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel', 'cond': 85, 'type': 'Armor'},
        'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel', 'cond': 100, 'type': 'Weapon', 'dmg': '2d8'},
        'OffHand': {'item': 'Kite Shield', 'material': 'Steel', 'cond': 80, 'type': 'Armor'}
    },
    'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Consecrate Ground', 'Lesser Smite', 'Lesser Heal', 'Purify Flesh', 'Stamina Surge'],
    'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Consecrate Ground': 20, 'Lesser Smite': 10, 'Lesser Heal': 12, 'Purify Flesh': 10, 'Stamina Surge': 10},
    'inventory': {'currency': {'Silver': 150}}
}
