import streamlit as st

def gain_experience(exp):
    """
    Adds experience to the session game_state, distributes small skill exp,
    and handles character level-up when threshold is reached.
    This preserves the original behaviour from app.py.
    """
    gs = st.session_state.game_state
    gs["experience"] = gs.get("experience", 0) + exp
    # Level up skills based on usage
    for cat, sks in gs.get("skills", {}).items():
        for skill in sks:
            if skill in gs.setdefault("skills_exp", {}).setdefault(cat, {s: 0 for s in sks.keys()}):
                gs["skills_exp"][cat][skill] += exp // 10
    # Level up character
    if gs["experience"] >= 100:
        gs["level"] = gs.get("level", 1) + 1
        gs["hp_max"] = gs.get("hp_max", 0) + 10
        gs["stamina_max"] = gs.get("stamina_max", 0) + 5
        gs["mana_max"] = gs.get("mana_max", 0) + 5
        gs["experience"] = 0
        st.success(f"Level up! New level: {gs['level']}")
