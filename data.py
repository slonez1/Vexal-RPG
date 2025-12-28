# data.py

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2}
}

SKILL_MAP = {
    "One-Handed": "STR", "Two-Handed": "STR", "Bladed": "DEX", "Blunt": "STR",
    "Daggers": "DEX", "Axes": "STR", "Polearms": "STR", "Marksmanship": "DEX",
    "Blocking": "STR", "Heavy Armor": "CON", "Light Armor": "DEX", "Unarmed": "STR",
    "Holy": "WIS", "Arcane": "INT", "Elemental": "INT", "Illusion": "CHA",
    "Death": "INT", "Blood": "CHA", "Restoration": "WIS", "Void Navigation": "INT",
    "Stealth": "DEX", "Lockpicking": "DEX", "Pickpocket": "DEX",
    "Poisoning": "INT", "Trap Disarming": "DEX", "Shadow-Stitch": "INT",
    "Alchemy": "INT", "Blacksmithing": "STR", "Enchanting": "INT", "Survival": "WIS",
    "Athletics": "STR", "Acrobatics": "DEX", "Anatomy": "INT", "Tinkering": "INT",
    "Cooking": "WIS", "Leatherworking": "DEX",
    "Persuasion": "CHA", "Intimidation": "CHA", "Deception": "CHA",
    "Insight": "WIS", "Performance": "CHA", "Etiquette": "CHA", "Bartering": "CHA"
}

# The initial state for a new session
INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon',
    'level': 10,
    'hp': 100, 'hp_max': 250,
    'mana': 30, 'mana_max': 200,
    'stamina': 100, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0,
    'divine_favor': 95,
    'vaxel_state': "Active",
    'conditions': {"Vexal Active": "(-2 STR, -2 DEX, -2 CON, -2 INT, -2 WIS, -2 CHA)"},
    'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
    'skills': {
        'Martial': {'One-Handed': 10, 'Two-Handed': 4, 'Bladed': 7, 'Blunt': 4, 'Blocking': 5, 'Heavy Armor': 8, 'Light Armor': 3, 'Unarmed': 1, 'Marksmanship': 3, 'Polearms': 2, 'Axes': 1},
        'Mystical': {'Holy': 10, 'Arcane': 4, 'Elemental': 3, 'Restoration': 7},
        'Professional': {'Alchemy': 2, 'Enchanting': 4, 'Survival': 4, 'Athletics': 6, 'Anatomy': 3, 'Cooking': 1, 'Blacksmithing': 4},
        'Social': {'Persuasion': 3, 'Intimidation': 3, 'Insight': 10, 'Etiquette': 7, 'Bartering': 1},
        'Subterfuge': {'Stealth': 2, 'Insight': 3}
    },
    'equipment': {
        'Head': {'item': 'Blessed Circlet', 'material': 'Gold-Filigree', 'cond': 100},
        'Torso': {'item': 'Knight-Commander Plate', 'material': 'Steel', 'cond': 85},
        'Legs': {'item': 'Plated Greaves', 'material': 'Steel', 'cond': 90},
        'Hands': {'item': 'Steel Gauntlets', 'material': 'Steel', 'cond': 90},
        'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel', 'cond': 100, 'type': 'Bladed', 'dmg': '2d8'},
        'OffHand': {'item': 'Kite Shield', 'material': 'Steel', 'cond': 80}
    },
    'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Lesser Heal'],
    'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Lesser Heal': 12},
    'lore_ledger': {'Main Quest': {"Current Objective": "Enter the Spire."}}
}
