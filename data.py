# data.py

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 0.5, "Noise": -1, "Dex_Penalty": 0},
    "Steel":   {"DT": 5, "Weight": 1.0, "Noise": -8, "Dex_Penalty": -2},
    "Mithril": {"DT": 8, "Weight": 0.1, "Noise": -3, "Dex_Penalty": 0},
    "Aureite": {"DT": 6, "Weight": 0.5, "Noise": -5, "Dex_Penalty": -1},
    "Silver-Steel": {"DT": 6, "Weight": 0.8, "Noise": -6, "Dex_Penalty": -1},
    "Gold-Filigree": {"DT": 2, "Weight": 0.4, "Noise": -2, "Dex_Penalty": 0}
}

FEAT_LIBRARY = {
    "Aegis of Light": "Permanent +10 to HP_Max and +5 to Holy Skill.",
    "Vaxel Synchronicity": "Reduce Arousal gain by 20% and +2 to WIS.",
    "Bladed Dancer": "Ignore DEX penalties from Steel armor and +2 to DEX.",
    "Divine Bastion": "+2 to CON and +2 to all Saving Throws.",
    "Scholar of the Void": "+2 to INT and unlock 'Void Navigation' skill."
}

INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon', 'level': 10, 'xp': 5600, 'xp_next': 5500, # Set high to test Level Up
    'hp': 250, 'hp_max': 250, 'mana': 200, 'mana_max': 200, 'stamina': 180, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95, 'vaxel_state': "Active", 'turn_counter': 0,
    'attributes': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 12, 'WIS': 18, 'CHA': 16},
    'conditions': {"Vexal Active": "(-2 to ALL stats)"},
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
        'MainHand': {'item': 'Solari Longsword', 'material': 'Silver-Steel', 'cond': 100, 'type': 'Bladed', 'dmg': '2d8', 'scaling': 'DEX'},
        'OffHand': {'item': 'Kite Shield', 'material': 'Steel', 'cond': 80}
    },
    'known_spells': ['Sunlight Spear', 'Holy Aegis', 'Consecrate Ground', 'Lesser Smite', 'Banish Corruption', 'Divine Radiance', 'Arcane Eye', 'Mage Hand', 'Mana Shield', 'Burst of Embers', 'Lesser Heal', 'Purify Flesh', 'Stamina Surge', 'Mend Bone', 'Cure Toxins'],
    'mana_costs': {'Sunlight Spear': 15, 'Holy Aegis': 12, 'Consecrate Ground': 20, 'Lesser Smite': 10, 'Banish Corruption': 25, 'Divine Radiance': 18, 'Arcane Eye': 5, 'Mage Hand': 2, 'Mana Shield': 15, 'Burst of Embers': 8, 'Lesser Heal': 12, 'Purify Flesh': 10, 'Stamina Surge': 10, 'Mend Bone': 15, 'Cure Toxins': 10},
    'inventory': {
        'containers': {
            'Belt Pouch': {'capacity': 5, 'items': ['Whetstone', 'Silver Key']},
            'Satchel': {'capacity': 15, 'items': ['Dried Rations', 'Holy Oil', 'Bandages']},
            'Scabbard': {'capacity': 1, 'items': []}
        },
        'currency': {'Silver': 150}
    },
    'lore_ledger': {'NPCs': {}, 'Locations': {}, 'Main Quest': {"Current Objective": "Enter the Spire."}}
}
