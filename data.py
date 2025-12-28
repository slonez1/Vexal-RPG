# data.py
import json
import copy
from datetime import datetime, timedelta

MAT_PROPS = {
    "Leather": {"DT": 1, "Weight": 5, "Noise": -1, "Dex_Penalty": 0},
    "Steel":   {"DT": 5, "Weight": 45, "Noise": -8, "Dex_Penalty": -2},
    "Mithril": {"DT": 8, "Weight": 12, "Noise": -3, "Dex_Penalty": 0},
    "Aureite": {"DT": 6, "Weight": 25, "Noise": -5, "Dex_Penalty": -1},
    "Silver-Steel": {"DT": 6, "Weight": 35, "Noise": -6, "Dex_Penalty": -1},
    "Gold-Filigree": {"DT": 2, "Weight": 8, "Noise": -2, "Dex_Penalty": 0}
}

# Spell Tiers
SPELL_TIERING = {
    "Holy": [
        {"name": "Sunlight Spear", "tier": 1, "dmg": "2d8", "mana": 15},
        {"name": "Holy Aegis", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Consecrate Ground", "tier": 1, "dmg": "0d0", "mana": 20},
        {"name": "Lesser Smite", "tier": 1, "dmg": "1d6", "mana": 10},
        {"name": "Lesser Heal", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Purify Flesh", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Stamina Surge", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Sunlight Lance", "tier": 2, "dmg": "3d8", "mana": 20},
        {"name": "Holy Ward", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Consecrate Light", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Greater Smite", "tier": 2, "dmg": "2d6", "mana": 15},
        {"name": "Greater Heal", "tier": 2, "dmg": "0d0", "mana": 20},
        {"name": "Sunlight Comet", "tier": 3, "dmg": "4d8", "mana": 30},
        {"name": "Holy Fortress", "tier": 3, "dmg": "0d0", "mana": 40},
        {"name": "Consecrate Heaven", "tier": 3, "dmg": "0d0", "mana": 50},
        {"name": "Divine Judgment", "tier": 3, "dmg": "5d8", "mana": 60}
    ],
    "Arcane": [
        {"name": "Arcane Bolt", "tier": 1, "dmg": "2d6", "mana": 10},
        {"name": "Arcane Shield", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Elemental Burst", "tier": 1, "dmg": "3d6", "mana": 20},
        {"name": "Arcane Storm", "tier": 1, "dmg": "4d6", "mana": 25},
        {"name": "Arcane Healing", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Arcane Lock", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Arcane Leap", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Arcane Nova", "tier": 2, "dmg": "5d6", "mana": 30},
        {"name": "Arcane Barrier", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Elemental Surge", "tier": 2, "dmg": "6d6", "mana": 40},
        {"name": "Arcane Rejuvenation", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Arcane Dominion", "tier": 2, "dmg": "7d6", "mana": 45},
        {"name": "Arcane Cataclysm", "tier": 3, "dmg": "8d6", "mana": 50},
        {"name": "Arcane Fortress", "tier": 3, "dmg": "0d0", "mana": 60},
        {"name": "Elemental Overload", "tier": 3, "dmg": "9d6", "mana": 65},
        {"name": "Arcane Apocalypse", "tier": 3, "dmg": "10d6", "mana": 70}
    ],
    "Elemental": [
        {"name": "Fireball", "tier": 1, "dmg": "2d8", "mana": 15},
        {"name": "Ice Shard", "tier": 1, "dmg": "2d6", "mana": 10},
        {"name": "Lightning Bolt", "tier": 1, "dmg": "3d8", "mana": 20},
        {"name": "Earthquake", "tier": 1, "dmg": "4d8", "mana": 25},
        {"name": "Healing Rain", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Wind Gust", "tier": 1, "dmg": "1d8", "mana": 10},
        {"name": "Firestorm", "tier": 2, "dmg": "5d8", "mana": 30},
        {"name": "Ice Wall", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Lightning Storm", "tier": 2, "dmg": "6d8", "mana": 40},
        {"name": "Tornado", "tier": 2, "dmg": "7d8", "mana": 45},
        {"name": "Healing Surge", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Earthquake", "tier": 2, "dmg": "8d8", "mana": 50},
        {"name": "Fire Nova", "tier": 3, "dmg": "9d8", "mana": 55},
        {"name": "Ice Fortress", "tier": 3, "dmg": "0d0", "mana": 60},
        {"name": "Lightning Dominion", "tier": 3, "dmg": "10d8", "mana": 65},
        {"name": "Elemental Apocalypse", "tier": 3, "dmg": "11d8", "mana": 70}
    ],
    "Illusion": [
        {"name": "Mimic", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Confusion", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Deception", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Hallucination", "tier": 1, "dmg": "0d0", "mana": 20},
        {"name": "Illusionary Attack", "tier": 1, "dmg": "1d6", "mana": 10},
        {"name": "Mental Barrier", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Mimicry", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Confusion Field", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Deception Wall", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Hallucination Storm", "tier": 2, "dmg": "0d0", "mana": 40},
        {"name": "Illusionary Fortress", "tier": 2, "dmg": "0d0", "mana": 45},
        {"name": "Mental Overload", "tier": 2, "dmg": "0d0", "mana": 50},
        {"name": "Mimicry Dominion", "tier": 3, "dmg": "0d0", "mana": 55},
        {"name": "Confusion Apocalypse", "tier": 3, "dmg": "0d0", "mana": 60},
        {"name": "Deception Dominion", "tier": 3, "dmg": "0d0", "mana": 65},
        {"name": "Hallucination Apocalypse", "tier": 3, "dmg": "0d0", "mana": 70}
    ],
    "Death": [
        {"name": "Necrotic Bolt", "tier": 1, "dmg": "2d6", "mana": 10},
        {"name": "Death Ward", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Soul Siphon", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Necrotic Surge", "tier": 1, "dmg": "3d6", "mana": 20},
        {"name": "Death Touch", "tier": 1, "dmg": "1d6", "mana": 10},
        {"name": "Death Field", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Necrotic Storm", "tier": 2, "dmg": "4d6", "mana": 25},
        {"name": "Death Barrier", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Soul Requiem", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Necrotic Overload", "tier": 2, "dmg": "5d6", "mana": 40},
        {"name": "Death Dominion", "tier": 2, "dmg": "0d0", "mana": 45},
        {"name": "Soul Requiem", "tier": 2, "dmg": "0d0", "mana": 50},
        {"name": "Necrotic Apocalypse", "tier": 3, "dmg": "6d6", "mana": 55},
        {"name": "Death Fortress", "tier": 3, "dmg": "0d0", "mana": 60},
        {"name": "Soul Requiem", "tier": 3, "dmg": "0d0", "mana": 65},
        {"name": "Death Dominion", "tier": 3, "dmg": "0d0", "mana": 70}
    ],
    "Blood": [
        {"name": "Blood Bolt", "tier": 1, "dmg": "2d6", "mana": 10},
        {"name": "Blood Shield", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Soul Siphon", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Blood Surge", "tier": 1, "dmg": "3d6", "mana": 20},
        {"name": "Blood Touch", "tier": 1, "dmg": "1d6", "mana": 10},
        {"name": "Blood Field", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Blood Storm", "tier": 2, "dmg": "4d6", "mana": 25},
        {"name": "Blood Barrier", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Soul Requiem", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Blood Overload", "tier": 2, "dmg": "5d6", "mana": 40},
        {"name": "Blood Dominion", "tier": 2, "dmg": "0d0", "mana": 45},
        {"name": "Soul Requiem", "tier": 2, "dmg": "0d0", "mana": 50},
        {"name": "Blood Apocalypse", "tier": 3, "dmg": "6d6", "mana": 55},
        {"name": "Blood Fortress", "tier": 3, "dmg": "0d0", "mana": 60},
        {"name": "Soul Requiem", "tier": 3, "dmg": "0d0", "mana": 65},
        {"name": "Blood Dominion", "tier": 3, "dmg": "0d0", "mana": 70}
    ],
    "Restoration": [
        {"name": "Lesser Heal", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Greater Heal", "tier": 1, "dmg": "0d0", "mana": 20},
        {"name": "Cure Disease", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Cure Poison", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Heal Wounds", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Heal Bleeding", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Heal Status", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Heal All", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Cure Disease", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Cure Poison", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Heal Wounds", "tier": 2, "dmg": "0d0", "mana": 20},
        {"name": "Heal Bleeding", "tier": 2, "dmg": "0d0", "mana": 20},
        {"name": "Heal Status", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Heal All", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Cure Disease", "tier": 3, "dmg": "0d0", "mana": 40},
        {"name": "Cure Poison", "tier": 3, "dmg": "0d0", "mana": 40},
        {"name": "Heal Wounds", "tier": 3, "dmg": "0d0", "mana": 30},
        {"name": "Heal Bleeding", "tier": 3, "dmg": "0d0", "mana": 30},
        {"name": "Heal Status", "tier": 3, "dmg": "0d0", "mana": 35},
        {"name": "Heal All", "tier": 3, "dmg": "0d0", "mana": 45}
    ],
    "Shadow": [
        {"name": "Shadow Step", "tier": 1, "dmg": "0d0", "mana": 10},
        {"name": "Dark Veil", "tier": 1, "dmg": "0d0", "mana": 15},
        {"name": "Soul Siphon", "tier": 1, "dmg": "0d0", "mana": 12},
        {"name": "Phantom Strike", "tier": 1, "dmg": "1d6", "mana": 10},
        {"name": "Shadow Cloak", "tier": 2, "dmg": "0d0", "mana": 25},
        {"name": "Void Step", "tier": 2, "dmg": "0d0", "mana": 30},
        {"name": "Soul Drain", "tier": 2, "dmg": "0d0", "mana": 35},
        {"name": "Nightmare", "tier": 2, "dmg": "0d0", "mana": 40},
        {"name": "Shadow Dominion", "tier": 3, "dmg": "0d0", "mana": 55},
        {"name": "Void Surge", "tier": 3, "dmg": "0d0", "mana": 60},
        {"name": "Soul Requiem", "tier": 3, "dmg": "0d0", "mana": 65},
        {"name": "Eclipse", "tier": 3, "dmg": "0d0", "mana": 70}
    ]
}

# Initial Game State
INITIAL_GAME_STATE = {
    'name': 'Amara Silvermoon', 'level': 10, 'xp': 5600, 'xp_next': 5500,
    'hp': 100, 'hp_max': 250, 'mana': 30, 'mana_max': 200, 'stamina': 80, 'stamina_max': 180,
    'arousal': 0, 'orgasm_count': 0, 'divine_favor': 95, 'vexal_state': "Active",
    'attributes': {'STR': 16, 'DEX': 16, 'CON': 14, 'INT': 12, 'WIS': 20, 'CHA': 18},
    'conditions': {"Vexal Active": "(-2 to ALL Attributes, -20 to Pools)"},
    'skills': {
        'Martial': {'One-Handed': 10, 'Two-Handed': 4, 'Bladed': 7, 'Blunt': 4, 'Blocking': 5, 'Heavy Armor': 8, 'Light Armor': 3, 'Marksmanship': 3},
        'Mystical': {'Holy': 10, 'Arcane': 4, 'Elemental': 3, 'Illusion': 0, 'Death': 0, 'Blood': 0, 'Restoration': 7, 'Shadow': 0},
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
    'inventory': {'currency': {'Silver': 150}},
}
