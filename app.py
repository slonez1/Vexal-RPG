# --- 1. LEVEL UP LOGIC ---
def apply_level_up(attr_choice, feat_choice):
    gs = st.session_state.game_state
    # Increase Level
    gs['level'] += 1
    gs['xp'] -= gs['xp_next']
    gs['xp_next'] = int(gs['xp_next'] * 1.5) # D&D style scaling
    
    # Apply Attribute Buff
    gs['attributes'][attr_choice] += 1
    
    # Apply Feat Effects (Hardcoded logic for the library)
    if feat_choice == "Aegis of Light":
        gs['hp_max'] += 10
        gs['skills']['Mystical']['Holy'] += 5
    elif feat_choice == "Vaxel Synchronicity":
        gs['attributes']['WIS'] += 2
    elif feat_choice == "Bladed Dancer":
        gs['attributes']['DEX'] += 2
    elif feat_choice == "Divine Bastion":
        gs['attributes']['CON'] += 2
    
    # Record in history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": f"✨ **LEVEL UP!** Amara reached Level {gs['level']}. Increased {attr_choice} and gained '{feat_choice}'."
    })
    st.toast(f"Reached Level {gs['level']}!", icon="🌟")

# --- 2. THE UI MODAL (Place this at the start of the Main Page code) ---
gs = st.session_state.game_state
if gs['xp'] >= gs['xp_next']:
    with st.container(border=True):
        st.markdown("### 🌟 LEVEL UP AVAILABLE")
        st.write("Amara's experiences have forged her into something greater. Choose your path:")
        
        col_l, col_r = st.columns(2)
        with col_l:
            attr_select = st.selectbox("Increase Attribute (+1)", list(gs['attributes'].keys()))
        with col_r:
            feat_select = st.selectbox("Select a Feat", list(FEAT_LIBRARY.keys()))
            st.caption(f"Effect: {FEAT_LIBRARY[feat_select]}")
            
        if st.button("Confirm Ascension", use_container_width=True):
            apply_level_up(attr_select, feat_select)
            st.rerun()

# --- 3. UPDATED ATTACK LOGIC (Attribute Integration) ---
def execute_combat_roll():
    eff = get_effective_attributes()
    weapon = gs['equipment']['MainHand']
    
    # Scaling: Use STR for Heavy/Blunt, DEX for Bladed/Marksmanship
    stat_to_use = "DEX" if weapon['type'] in ['Bladed', 'Marksmanship', 'Daggers'] else "STR"
    stat_mod = (eff[stat_to_use] - 10) // 2
    
    # Hit: d20 + Mod + (Skill Rank / 2)
    roll = random.randint(1, 20)
    skill_rank = 0
    for cat in gs['skills'].values():
        if weapon['type'] in cat: skill_rank = cat[weapon['type']]
        
    total_hit = roll + stat_mod + (skill_rank // 2)
    
    # Damage: Weapon Dice + Mod
    d_num, d_sides = map(int, weapon['dmg'].split('d'))
    total_dmg = sum(random.randint(1, d_sides) for _ in range(d_num)) + stat_mod
    
    return total_hit, total_dmg, roll

#
