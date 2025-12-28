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
        return {}
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
    return {"source": "heuristic"}

# ----------------- LLM integration (Gemini / Google GenAI) -----------------
def _call_google_genai_chat(prompt, model=None):
    """
    Try to call Google Generative AI (Gemini) via the google.generativeai client.
    Requires GEMINI_API_KEY or GOOGLE_API_KEY in st.secrets and google.generativeai installed.
    """
    try:
        import google.generativeai as genai
    except Exception as e:
        _log.debug("google.generativeai import failed: %s", e)
        raise

    # Prefer GEMINI_API_KEY then GOOGLE_API_KEY
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("google_api_key")
    if not api_key:
        # also allow a service account JSON in secrets under GOOGLE_SERVICE_ACCOUNT
        svc = st.secrets.get("GOOGLE_SERVICE_ACCOUNT")
        if svc:
            # if a JSON string is present, configure via environment (client library can pick it up)
            # This is best-effort; if it fails we'll raise later
            import os, json as _json
            try:
                svc_path = "/tmp/streamlit_google_service_account.json"
                with open(svc_path, "w") as f:
                    f.write(svc if isinstance(svc, str) else _json.dumps(svc))
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = svc_path
            except Exception as _e:
                _log.debug("Failed to write service account: %s", _e)
                raise RuntimeError("No usable Google API credential found in secrets.")
    else:
        genai.configure(api_key=api_key)

    # choose model: prefer configured one in secrets, otherwise fallback to chat-bison
    model_name = st.secrets.get("GENAI_MODEL") or st.secrets.get("GEMINI_MODEL") or model or "models/chat-bison-001"
    # Build messages payload
    try:
        resp = genai.chat.create(model=model_name, messages=[{"author":"user","content":prompt}], temperature=0.0)
    except TypeError:
        # older/newer SDK differences
        resp = genai.generate(model=model_name, prompt=prompt)
    # extract text
    if hasattr(resp, "candidates") and resp.candidates:
        # older interface
        return resp.candidates[0].content if hasattr(resp.candidates[0], "content") else str(resp)
    if hasattr(resp, "last") and resp.last and hasattr(resp.last, "content"):
        return resp.last.content
    # fallback to string
    return str(resp)

def _parse_model_json(text):
    """Try to parse JSON returned by model; be defensive."""
    try:
        payload = text.strip()
        # remove code fence wrappers if present
        if payload.startswith("```"):
            # strip leading/trailing ``` blocks
            lines = payload.splitlines()
            # remove first and last if they are ``` markers
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            payload = "\n".join(lines)
        return json.loads(payload)
    except Exception as e:
        _log.debug("JSON parse failed: %s -- raw:%s", e, text[:400])
        return None

def llm_extract(text):
    """
    Ask an LLM (Gemini/GenAI) to extract structured lore from the text.
    Returns parsed dict or raises if provider not available.
    Expected JSON schema (example):
    {
      "persons": [{"name":"Eldon","role":"Scholar","significance":"Knows Bastion","notable_notes":["..."],"tags":["scholar"]}],
      "locations": [{"name":"Harrowfen","description":"A ruined keep","tags":["ruin"]}],
      "factions": [{"name":"Blood Cult","description":"...","tags":["cult"]}],
      "tags": ["bastion","vexal"],
      "vexal_updates": ["Found reference to bastion fragment in Harrowfen."],
      "time_advance": {"scale":"combat","seconds_per_turn":6}
    }
    """
    prompt = (
        "Extract structured lore elements from the following narrative. "
        "Return valid JSON with keys: persons, locations, factions, tags, vexal_updates, time_advance.\n\n"
        "Persons: list of objects {name, role (short), significance (short), notable_notes (list), tags (list)}\n"
        "Locations: list of objects {name, description (short), tags (list)}\n"
        "Factions: list of objects {name, description (short), tags}\n"
        "tags: list of short tags\n"
        "vexal_updates: list of short lines that update the main quest or mention Bastion/fragment clues\n"
        "time_advance: optional object e.g. {\"scale\":\"combat\",\"seconds_per_turn\":6} or {\"hours\":6} or {\"seconds\":30}\n\n"
        "Narrative:\n" + (text or "")
        + "\n\nOutput ONLY valid JSON."
    )

    # Try Google GenAI / Gemini
    try:
        resp_text = _call_google_genai_chat(prompt)
        parsed = _parse_model_json(resp_text)
        if parsed is not None:
            return parsed
    except Exception as e:
        _log.debug("GenAI/Gemini call failed: %s", e)
    # If LLM fails, raise to let caller fallback to heuristic
    raise RuntimeError("LLM extraction failed or no provider available")

def llm_extract_and_add(text):
    """
    Use an LLM (if available) to extract structured lore and add it to session_state.
    Returns the extracted dict (or heuristic dict on fallback).
    """
    init_lore()
    if not text:
        return {}
    try:
        extracted = llm_extract(text)
    except Exception as e:
        _log.debug("LLM extraction failed, falling back to heuristics: %s", e)
        extracted = auto_extract_and_add(text) or {"source": "heuristic"}

    # Merge persons
    persons = extracted.get("persons") or []
    for p in persons:
        name = p.get("name")
        role = p.get("role")
        sig = p.get("significance") or ""
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

    # Return the extraction dict so callers can access time_advance etc.
    return extracted or {"source": "heuristic"}
