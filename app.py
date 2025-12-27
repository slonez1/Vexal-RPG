# --- 6. SOPHISTICATED UI TABS ---
tab_console, tab_char, tab_inv, tab_lore, tab_sett = st.tabs([
    "📜 CONSOLE", "👤 CHARACTER", "🎒 INVENTORY", "📖 LORE", "⚙️ SETTINGS"
])

# --- TAB 1: CONSOLE (The Game Loop) ---
with tab_console:
    # (Keep your existing Chat Display and st.chat_input logic here)
    pass

# --- TAB 2: CHARACTER (Attributes, Skills, & Spells) ---
with tab_char:
    st.header(f"✨ {gs['name']} | Level {gs['level']} Paladin")
    
    col_attr, col_skills = st.columns([1, 2])
    
    with col_attr:
        st.subheader("Attributes")
        for attr, val in gs['attributes'].items():
            st.metric(label=attr, value=val)

    with col_skills:
        st.subheader("Skill Proficiencies")
        # Organizing skills by category
        for cat, skills in gs['skills'].items():
            with st.expander(f"{cat} Skills"):
                for s_name, s_rank in skills.items():
                    # Visual rank bar for each skill
                    st.write(f"**{s_name}**")
                    st.progress(s_rank / 20, text=f"Rank {s_rank}")

    st.divider()
    st.subheader("📜 Spellbook")
    spell_cols = st.columns(2)
    for i, spell in enumerate(gs['known_spells']):
        # We can pull cost/effect from a dictionary or have Gemini describe them
        cost = gs.get('mana_costs', {}).get(spell, "??")
        with spell_cols[i % 2]:
            with st.expander(f"✨ {spell}"):
                st.caption(f"Mana Cost: {cost}")
                st.write("Mechanical Effect: *Determined by Divine Favor and Paladin Level.*")

# --- TAB 3: INVENTORY (Bags & Equipment) ---
with tab_inv:
    st.header("🎒 Equipment & Loadout")
    
    # Armor and Weapons Detail
    st.subheader("🛡️ Equipped Gear")
    armor_cols = st.columns(2)
    for i, (slot, data) in enumerate(gs['equipment'].items()):
        with armor_cols[i % 2]:
            mat = data.get('material', 'Steel')
            # Fetching properties from our MAT_PROPS logic
            props = MAT_PROPS.get(mat, {"DT": 0, "Weight": 0, "Noise": 0})
            
            st.info(f"**{slot}: {data['item']}**\n\n"
                    f"Material: {mat} | Prot: +{props['DT']} | Weight: {props['Weight']} | Noise: {props['Noise']}")

    st.divider()
    st.subheader("🧺 Containers")
    cont_cols = st.columns(len(gs['inventory']['containers']))
    for i, (name, storage) in enumerate(gs['inventory']['containers'].items()):
        with cont_cols[i]:
            st.write(f"**{name}**")
            st.caption(f"Capacity: {len(storage['items'])}/{storage['capacity']}")
            for item in storage['items']:
                st.markdown(f"- {item}")
    
    st.metric("Silver Coins", f"{gs['inventory']['currency']['Silver']} sp")

# --- TAB 4: LORE (People, Places, & Shards) ---
with tab_lore:
    st.header("📖 The Lore Ledger")
    
    lore_p, lore_l, lore_q = st.columns(3)
    
    with lore_p:
        st.subheader("Characters")
        for npc, bio in gs['lore_ledger']['NPCs'].items():
            st.write(f"**{npc}**: {bio}")
            
    with lore_l:
        st.subheader("Places")
        for loc, desc in gs['lore_ledger']['Locations'].items():
            st.write(f"**{loc}**: {desc}")

    with lore_q:
        st.subheader("🧭 Current Quest")
        quest = gs['lore_ledger']['Main Quest']
        st.success(f"**Objective:** {quest['Current Objective']}")
        st.info(f"💎 **Bastion Shards Found:** {quest['Bastion Shards']} / 7")

# --- TAB 5: SETTINGS (System Controls) ---
with tab_sett:
    st.header("⚙️ Game Settings")
    
    # Save/Load Logic
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Download Save", use_container_width=True):
            save_str = json.dumps(st.session_state.game_state, indent=4)
            st.download_button("Click to Download .json", save_str, file_name="amara_save.json")
    
    with c2:
        uploaded_file = st.file_uploader("📂 Load Save File", type="json")
        if uploaded_file:
            st.session_state.game_state = json.load(uploaded_file)
            st.success("State Loaded! Refreshing...")
            st.rerun()

    with c3:
        if st.button("🔥 HARD RESET", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.divider()
    st.subheader("🔊 Audio Diagnostics")
    st.write(f"Current Narrator: **{st.session_state.narrator}**")
    if st.button("🎵 Test Voice Connection"):
        speak("Voice systems operational, Master. The Spire awaits.")
