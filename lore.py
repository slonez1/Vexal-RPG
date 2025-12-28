# lore.py
# LLM-backed lore manager stored in streamlit session_state.
import streamlit as st
from collections import OrderedDict
import re
import json
import logging

_log = logging.getLogger("vexal.lore")

def init_lore():
    """Initialize the lore repository in session_state."""
    if "lore" not in st.session_state:
        st.session_state.lore = {
            "vexal": {
                "main_quest": "Investigate the Vexal corruption. Find and assemble fragments of the Bastion artifact to cleanse or destroy Vexal.",
                "notes": []
            },
            "persons": OrderedDict(),   # key: name -> {role, significance, notes, tags}
            "locations": OrderedDict(), # key: name -> {description, discovered_at_turn, tags}
            "factions": OrderedDict(),  # optional factions registry
            "tags": set()
        }

def add_vexal_note(text):
    init_lore()
    st.session_state.lore["vexal"]["notes"].append(text)

def add_person(name, role=None, significance=None, note=None, tags=None):
    init_lore()
    people = st.session_state.lore["persons"]
    if name not in people:
        people[name] = {"role": role or "", "significance": significance or "", "notes": [], "tags": []}
    if note:
        people[name]["notes"].append(note)
    if tags:
        people[name]["tags"].extend(t for t in tags if t not in people[name]["tags"])
        st.session_state.lore["tags"].update(tags)

def add_location(name, description=None, tags=None):
    init_lore()
    locs = st.session_state.lore["locations"]
    if name not in locs:
        locs[name] = {"description": description or "", "discovered_at_turn": st.session_state.get("turn_count", 0), "tags": []}
    if description:
        locs[name]["description"] = description
    if tags:
        locs[name]["tags"].extend(t for t in tags if t not in locs[name]["tags"])
        st.session_state.lore["tags"].update(tags)

# Heuristic extractor (fallback)
_name_rx = re.compile(r"\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*)\b")
_common_words = {"The", "A", "An", "And", "But", "If", "When", "Where", "Because", "In", "On"}

def auto_extract_and_add(text):
    """
    Conservative heuristic: add proper-noun style tokens as potential persons/locations.
    Also check for key quest words ("Bastion", "Vexal").
    """
    init_lore()
    if not text:
        return
    txt = text or ""
    if "bastion" in txt.lower():
        st.session_state.lore["vexal"]["main_quest"] = (
            "Recover the fragments of the Bastion artifact. Seek scholars and ruins that can identify fragments."
        )
        add_vexal_note("Mentioned the Bastion: " + (txt[:200] if len(txt) > 200 else txt))
    if "vexal" in txt.lower():
        add_vexal_note("Vexal referenced: " + (txt[:200] if len(txt) > 200 else txt))

    candidates = set(m.group(1) for m in _name_rx.finditer(txt))
    for cand in sorted(candidates):
        if cand in _common_words:
            continue
        if len(cand) > 2:
            # small heuristic: treat as person if patterns like "X the" exist
            if f"{cand} the" in txt or f"{cand}, the" in txt or " of " in txt:
                add_person(cand, note="Auto-extracted (heuristic).")
            else:
                add_location(cand, description="Discovered in narrative (heuristic).")

# ----------------- LLM integration -----------------
def _call_openai_chat(prompt, model="gpt-4-0613", max_tokens=800):
    """
    Try to call OpenAI ChatCompletion. Requires 'OPENAI_API_KEY' in st.secrets and openai package installed.
    """
    try:
        import openai
    except Exception as e:
        _log.debug("openai package missing: %s", e)
        raise

    api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai_api_key")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in st.secrets")
    openai.api_key = api_key
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": "You are a helpful lore extraction assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0
    )
    return resp.choices[0].message.content

def _call_google_genai_chat(prompt, model="models/chat-bison-001"):
    """
    Try to call Google Generative AI (google.generativeai). Requires GOOGLE_API_KEY in st.secrets.
    """
    try:
        import google.generativeai as genai
    except Exception as e:
        _log.debug("google.genai package missing: %s", e)
        raise

    api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("google_api_key")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in st.secrets")
    genai.configure(api_key=api_key)
    resp = genai.chat.create(model=model, messages=[{"author":"user","content":prompt}], temperature=0.0)
    return resp.last

def _parse_model_json(text):
    """Try to parse JSON returned by model; be defensive."""
    try:
        payload = text.strip()
        # sometimes models wrap output in ```json ... ```
        if payload.startswith("```"):
            # remove code fence
            payload = "\n".join(payload.splitlines()[1:-1]) if "\n" in payload else payload.strip("`")
        return json.loads(payload)
    except Exception as e:
        _log.debug("JSON parse failed: %s", e)
        return None

def llm_extract(text):
    """
    Ask an LLM to extract structured lore from the text.
    Returns dict with optional keys: persons, locations, factions, tags, vexal_updates
    Each of the person/location entries should be in a small dict form.
    This function is defensive: if the provider or client lib is not available, raises an error.
    """
    # short instruction: ask for JSON only
    prompt = (
        "Extract structured lore elements from the following narrative. "
        "Return valid JSON with keys: persons, locations, factions, tags, vexal_updates.\n\n"
        "Persons: list of objects {name, role (short), significance (short), notable_notes (list), tags (list)}\n"
        "Locations: list of objects {name, description (short), tags (list)}\n"
        "Factions: list of objects {name, description (short), tags}\n"
        "tags: list of short tags\n"
        "vexal_updates: list of short lines that update the main quest or mention Bastion/fragment clues\n\n"
        "Narrative:\n" + (text or "")
        + "\n\nOutput ONLY valid JSON. Be brief in descriptions."
    )

    # Try OpenAI if key present
    if st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai_api_key"):
        try:
            resp_text = _call_openai_chat(prompt)
            parsed = _parse_model_json(resp_text)
            if parsed:
                return parsed
        except Exception as e:
            _log.debug("OpenAI call failed: %s", e)

    # Try Google GenAI if key present
    if st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("google_api_key"):
        try:
            resp = _call_google_genai_chat(prompt)
            # genai returns a structured object; use its text
            resp_text = getattr(resp, "content", "") or str(resp)
            parsed = _parse_model_json(resp_text)
            if parsed:
                return parsed
        except Exception as e:
            _log.debug("Google GenAI call failed: %s", e)

    # If we reach here, no working LLM — raise to let caller fallback to heuristic
    raise RuntimeError("No LLM available or LLM extraction failed")

def llm_extract_and_add(text):
    """
    Use an LLM (if available) to extract structured lore and add it to session_state.
    Falls back to auto_extract_and_add heuristics on any failure.
    """
    init_lore()
    if not text:
        return
    try:
        extracted = llm_extract(text)
    except Exception as e:
        _log.debug("LLM extraction failed, falling back to heuristics: %s", e)
        auto_extract_and_add(text)
        return

    # Merge persons
    persons = extracted.get("persons") or []
    for p in persons:
        name = p.get("name")
        role = p.get("role")
        sig = p.get("significance") or p.get("significance", "")
        notes = p.get("notable_notes") or []
        tags = p.get("tags") or []
        if name:
            add_person(name.strip(), role=role, significance=sig, note="LLM: " + "; ".join(notes) if notes else None, tags=tags)

    # Merge locations
    locs = extracted.get("locations") or []
    for l in locs:
        name = l.get("name")
        desc = l.get("description") or ""
        tags = l.get("tags") or []
        if name:
            add_location(name.strip(), description="LLM: " + desc if desc else None, tags=tags)

    # Merge factions
    factions = extracted.get("factions") or []
    for f in factions:
        name = f.get("name")
        desc = f.get("description") or ""
        if name:
            st.session_state.lore["factions"].setdefault(name, {"description": desc, "tags": f.get("tags", [])})

    # Merge tags and vexal_updates
    tgs = extracted.get("tags") or []
    if tgs:
        st.session_state.lore["tags"].update(tgs)
    vex = extracted.get("vexal_updates") or []
    for v in vex:
        if v:
            add_vexal_note("LLM: " + v)
