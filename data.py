# data.py
MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1, "Dex_Penalty": 0},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8, "Dex_Penalty": -2},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3, "Dex_Penalty": 0},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5, "Dex_Penalty": -1},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6, "Dex_Penalty": -1},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2, "Dex_Penalty": 0}
}

INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon', 'level': 10, 'xp': 5600, 'xp_next': 5500,
    'hp': 230, 'hp_max': 250, 'mana': 180, 'mana_max': 200, 'stamina': 160, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95, 'vaxel_state': "Active",
    'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
    'conditions': {"Vexal Active": "(-2 to ALL Attributes, -20 to Pools)"},
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
    'inventory': {'currency': {'Silver': 150}},
    'prev_eff': {}
}
