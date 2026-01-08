 # CONDITION_EFFECTS is pure data (no Streamlit imports) so it can be reused freely.
CONDITION_EFFECTS = {
    "Exhausted": {
        "color": "#ff4b4b",
        "desc": "Severe fatigue reduces DEX and CON by 5",
        "type": "debuff",
        "effects": {"DEX": -5, "CON": -5, "stamina_drain": 2},
        "severity": 3
    },
    "Fatigued": {
        "color": "#ff9800",
        "desc": "Mild exhaustion reduces DEX by 3",
        "type": "debuff",
        "effects": {"DEX": -3, "stamina_drain": 1},
        "severity": 2
    },
    "Wounded": {
        "color": "#d32f2f",
        "desc": "Physical damage reduces max HP by 20",
        "type": "debuff",
        "effects": {"hp_max_penalty": -20},
        "severity": 3
    },
    "Sprained Ankle": {
        "color": "#ff9800",
        "desc": "Movement penalty reduces DEX by 2",
        "type": "debuff",
        "effects": {"DEX": -2, "movement_speed": 0.5},
        "severity": 2
    },
    "Parched": {
        "color": "#f44336",
        "desc": "Mana regeneration slowed by 50%",
        "type": "debuff",
        "effects": {"mana_regen": 0.5},
        "severity": 2
    },
    "Divine Favor": {
        "color": "#ffd700",
        "desc": "Blessed by divine power - 25% mana cost reduction",
        "type": "buff",
        "effects": {"spell_cost_multiplier": 0.75},
        "severity": 1
    },
    "Blessed": {
        "color": "#28a745",
        "desc": "Holy protection increases WIS by 3",
        "type": "buff",
        "effects": {"WIS": 3},
        "severity": 1
    },
    "Haste": {
        "color": "#00bcd4",
        "desc": "Supernatural speed increases DEX by 4",
        "type": "buff",
        "effects": {"DEX": 4, "movement_speed": 1.5},
        "severity": 1
    },
    "Vexal Active": {
        "color": "#e83e8c",
        "desc": "Corrupting influence suppresses all attributes",
        "type": "debuff",
        "effects": {"all_attrs": -2, "pool_penalty": -20},
        "severity": 4
    }
}
