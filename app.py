import streamlit as st
import re
import random
from data import INITIAL_GAME_STATE, MAT_PROPS, SKILL_MAP

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Vexal Engine v5", layout="wide")

if "game_state" not in st.session_state:
    st.session_state.game_state = INITIAL_GAME_STATE
if "messages" not in st.session_state: st.session_state.messages = []

# --- 2. COMBAT ROLLER LOGIC ---
def roll_dice(dice_str):
    # Parses "2d8" -> rolls 2 8-sided dice
    num, sides = map(int, dice_str.split('d'))
    return sum(random.randint(1, sides) for _ in range(num))

def execute_attack():
    gs = st.session_state.game_state
    weapon = gs['equipment']['MainHand']
    eff = get_effective_attributes()
    
    # Logic: To Hit = d20 + DEX Mod + (Skill Rank / 2)
    roll = random.randint(1, 20)
    skill_type = weapon.get('type', 'One-Handed')
    # Find skill rank in nested dict
    skill_rank = 0
    for cat in gs['skills'].values():
        if skill_type in cat: skill_rank = cat[skill_type]

    attribute_mod = (eff['DEX'] - 10) // 2
    total_hit = roll + attribute_mod + (skill_rank // 2)
    
    # Damage = Weapon Roll + STR Mod
    raw_dmg = roll_dice(weapon['dmg'])
    str_mod = (eff['STR'] - 10) // 2
    total_dmg = raw_dmg + str_mod
    
    return {
        "roll": roll,
        "total_hit": total_hit,
        "damage": total_dmg,
        "weapon": weapon['item']
    }

# --- 3. UI UTILITIES ---
def get_effective_attributes():
    gs = st.session_state.game_state
    eff = gs['attributes'].copy()
    for impact in gs['conditions'].values():
        mods = re.findall(r'([+-]\d+)\s+(STR|DEX|CON|INT|WIS|CHA)', impact.upper())
        for val, attr in mods: eff[attr] += int(val)
    return eff

def custom_bar(label, current, maximum, color):
    percent = min(100, max(0, (current / maximum) * 100))
    st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: bold; margin-bottom: 2px;">
                <span>{label}</span><span>{current}/{maximum}</span>
            </div>
            <div style="background-color: #333; border-radius: 5px; height: 10px; width: 100%;">
                <div style="background-color: {color}; width: {percent}%; height: 100%; border-radius: 5px;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    gs = st.session_state.game_state
    st.title(f"🛡️ {gs['name']}")
    
    custom_bar("❤️ HEALTH", gs['hp'], gs['hp_max'], "#ff4b4b")
    custom_bar("⚡ STAMINA", gs['stamina'], gs['stamina_max'], "#28a745")
    custom_bar("✨ MANA", gs['mana'], gs['mana_max'], "#007bff")
    
    st.markdown("<hr style='border: 1px solid #444; margin: 15px 0;'>", unsafe_allow_html=True)
    custom_bar("⚖️ DIVINE FAVOR", gs['divine_favor'], 100, "#fd7e14")
    
    st.divider()
    
    # FIXED ATTRIBUTE GRID
    eff = get_effective_attributes()
    st.markdown("<div style='text-align:center; font-size:0.7rem; font-weight:bold; margin-bottom:10px;'>ATTRIBUTES</div>", unsafe_allow_html=True)
    
    # Using columns for the grid instead of raw HTML strings to prevent code dumping
    cols = st.columns(3)
    for i, (attr, base_val) in enumerate(gs['attributes'].items()):
        current_val = eff[attr]
        diff = current_val - base_val
        
        with cols[i % 3]:
            if diff < 0:
                st.markdown(f"<div style='text-align:center; background:#1e1e1e; border:1px solid #444; border-radius:5px; padding:2px;'><div style='font-size:0.6rem; color:#888;'>{attr}</div><div style='font-size:0.9rem; font-weight:bold; color:#ff4b4b;'>{current_val}({diff})</div></div>", unsafe_allow_html=True)
            elif diff > 0:
                st.markdown(f"<div style='text-align:center; background:#1e1e1e; border:1px solid #444; border-radius:5px; padding:2px;'><div style='font-size:0.6rem; color:#888;'>{attr}</div><div style='font-size:0.9rem; font-weight:bold; color:#28a745;'>{current_val}(+{diff})</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:center; background:#1e1e1e; border:1px solid #444; border-radius:5px; padding:2px;'><div style='font-size:0.6rem; color:#888;'>{attr}</div><div style='font-size:0.9rem; font-weight:bold;'>{current_val}</div></div>", unsafe_allow_html=True)

# --- 5. TABS ---
tab_console, tab_char = st.tabs(["📜 CONSOLE", "👤 CHARACTER"])

with tab_char:
    for cat, skills in gs['skills'].items():
        with st.expander(f"{cat} Skills"):
            c = st.columns(2)
            for i, (s, val) in enumerate(skills.items()):
                c[i%2].write(f"**{s}**: {val}")

with tab_console:
    # Combat Button
    if st.button("⚔️ Attack with Solari Longsword"):
        res = execute_attack()
        st.session_state.messages.append({
            "role": "assistant", 
            "content": f"**Combat Log:** Amara swings her {res['weapon']}! \n\n **Hit:** {res['total_hit']} (Roll: {res['roll']}) | **Damage:** {res['damage']}"
        })

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
