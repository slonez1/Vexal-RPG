# New file: lore.py
# Simple lore manager stored in streamlit session_state.
import streamlit as st
from collections import OrderedDict
import re

def init_lore():
    """Initialize the lore repository in session_state."""
    if "lore" not in st.session_state:
        st.session_state.lore = {
            "vexal": {
                "main_quest": "Investigate the Vexal corruption. Find and assemble fragments of the Bastion artifact to cleanse or destroy Vexal.",
                "notes": []
            },
            "persons": OrderedDict(),   # key: name -> {role, significance, notes}
            "locations": OrderedDict()  # key: name -> {description, discovered_at_turn}
        }

def add_vexal_note(text):
    init_lore()
    st.session_state.lore["vexal"]["notes"].append(text)

def add_person(name, role=None, significance=None, note=None):
    init_lore()
    people = st.session_state.lore["persons"]
    if name not in people:
        people[name] = {"role": role or "", "significance": significance or "", "notes": []}
    if note:
        people[name]["notes"].append(note)

def add_location(name, description=None):
    init_lore()
    locs = st.session_state.lore["locations"]
    if name not in locs:
        locs[name] = {"description": description or "", "discovered_at_turn": st.session_state.get("turn_count", 0)}

# Very small heuristic parser to extract names/places from narrative text.
_name_rx = re.compile(r"\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*)\b")

def auto_extract_and_add(text):
    """
    Heuristic: add obvious proper-nouns (2+ letters) as persons/locations.
    Also look for known quest keywords (Bastion, Vexal).
    """
    init_lore()
    text = text or ""
    # If mention Bastion or Vexal, ensure main quest references it
    if "bastion" in text.lower():
        st.session_state.lore["vexal"]["main_quest"] = (
            "Recover the fragments of the Bastion artifact. Seek scholars and ruins that can identify fragments."
        )
        add_vexal_note("Mentioned the Bastion in: " + (text[:200] if len(text) > 200 else text))
    if "vexal" in text.lower():
        add_vexal_note("Vexal referenced: " + (text[:200] if len(text) > 200 else text))

    # Extract candidate proper nouns
    candidates = set(m.group(1) for m in _name_rx.finditer(text))
    # Filter out common English starts and short words
    common = {"The", "A", "An", "And", "But", "If", "When", "Where", "Because", "In", "On"}
    for cand in sorted(candidates):
        if cand in common:
            continue
        # Very small heuristic: words that look like place/person
        if len(cand) > 2:
            # add to persons if followed by role-like words
            if any(w in text for w in [f"{cand} the", f"{cand}, the", f"{cand} of"]):
                add_person(cand, role="", significance="", note="Auto-extracted from narrative.")
            else:
                # also add as a location possibility
                add_location(cand, description="Discovered in narrative.")
