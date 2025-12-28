# data.py

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1, "Dex_Penalty": 0},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8, "Dex_Penalty": -2},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3, "Dex_Penalty": 0},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5, "Dex_Penalty": -1},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6, "Dex_Penalty": -1},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2, "Dex_Penalty": 0}
}

FEATS = {
    "Iron Will": "Permanent +2 to WIS Saving Throws",
    "Great Weapon Master": "+5 Damage with Two-Handed weapons, -2 to Hit",
    "Vaxel Harmonizer": "Reduce Arousal gain by 15%",
    "Fleet of Foot": "+2 to DEX and Athletics"
}

INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon', 'level': 10, 'xp': 4500, 'xp_next': 5500,
    'hp': 250, 'hp_max': 250, 'mana': 200, 'mana_max': 200, 'stamina': 180, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95, 'vaxel_state': "Active", 'turn_counter': 0,
    'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
    'feats': [],
    'conditions': {"Vexal Active": "(-2 to all stats)"},
    'skills': {
        'Martial': {'One-Handed': 10, 'Bladed': 7, 'Heavy Armor': 8, 'Stealth': 2},
        'Mystical': {'Holy': 10, 'Restoration': 7},
        'Professional': {'Athletics': 6, 'Survival': 4},
        'Social': {'Insight': 10, 'Etiquette': 7},
        'Subterfuge': {'Stealth': 2}
    },
    'equipment': {
        'Head': {'item': 'Blessed Circlet', 'material': 'Gold-Filigree', 'cond': 100},
        'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel', 'cond': 85},
        'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel', 'cond': 100, 'type': 'Bladed', 'dmg': '2d8', 'scaling': 'DEX'},
        'OffHand': {'item': 'Kite Shield', 'material': 'Steel', 'cond': 80}
    },
    'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal'],
    'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Lesser Heal': 12},
    'lore_ledger': {'NPCs': {}, 'Locations': {}, 'Main Quest': {"Current Objective": "Enter the Spire."}}
}
