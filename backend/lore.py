# lore.py
# LLM-backed lore manager stored in streamlit session_state.
import streamlit as st
from collections import OrderedDict
import re
import json
import logging
from pathlib import Path

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
    st.session_state.lore["vexal"].setdefault("notes", []).append(text)

def add_person(name, role=None, significance=None, note=None, tags=None):
    init_lore()
    people = st.session_state.lore["persons"]
    if name not in people:
        people[name] = {"role": role or "", "significance": significance or "", "notes": [], "tags": []}
    if note:
        people[name]["notes"].append(note)
    if tags:
        # ensure list uniqueness
        for t in tags:
            if t not in people[name]["tags"]:
                people[name]["tags"].append(t)
            st.session_state.lore["tags"].add(t)

def add_location(name, description=None, tags=None):
    init_lore()
    locs = st.session_state.lore["locations"]
    if name not in locs:
        locs[name] = {"description": description or "", "discovered_at_turn": st.session_state.get("turn_count", 0), "tags": []}
    if description:
        locs[name]["description"] = description
    if tags:
        for t in tags:
            if t not in locs[name]["tags"]:
                locs[name]["tags"].append(t)
            st.session_state.lore["tags"].add(t)

# Heuristic extractor (fallback)
_name_rx = re.compile(r"\b([A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*)\b")
_common_words = {"The", "A", "An", "And", "But", "If", "When", "Where", "Because", "In", "On"}

def auto_extract_and_add(text):
    """
    Conservative heuristic: add proper-noun style tokens as potential persons/locations.
    Also check for key quest words ("Bastion", "Vexal").
    Returns a small dict describing source.
    """
    init_lore()
    if not text:
        return {"source": "heuristic"}
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

# ----------------- Static Markdown loader -----------------
def _parse_markdown_entries(text):
    """
    Parse a markdown text into a mapping:
      section_title -> list of entries
    Each entry: {"name": str, "description": str, "bullets": [str]}
    Recognizes headings starting with '## ' and entries formatted as:
      **Name** — description
      - Role: ...
      - Significance: ...
      - Tags: a, b, c
      - Notes: ...
    Returns dict.
    """
    sections = {}
    current_section = "General"
    current_entry = None

    lines = text.splitlines()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # Section header
        if line.startswith("##"):
            current_section = line[2:].strip()
            if current_section == "":
                current_section = "General"
            sections.setdefault(current_section, [])
            current_entry = None
            continue
        # Entry line: **Name** — description
        m = re.match(r'^\*\*(.+?)\*\*\s*—\s*(.+)$', line)
        if m:
            name = m.group(1).strip()
            desc = m.group(2).strip()
            entry = {"name": name, "description": desc, "bullets": []}
            sections.setdefault(current_section, []).append(entry)
            current_entry = entry
            continue
        # Bullet line
        if line.startswith("- "):
            if current_entry is not None:
                current_entry["bullets"].append(line[2:].strip())
            else:
                # stray bullet: store as a note entry
                sections.setdefault(current_section, []).append({"name": "", "description": "", "bullets": [line[2:].strip()]})
            continue
        # Plain text line: append to last entry description if present
        if current_entry is not None:
            # append to description
            current_entry["description"] = (current_entry["description"] + " " + line).strip()
        else:
            # create a catch-all entry
            sections.setdefault(current_section, []).append({"name": "", "description": line, "bullets": []})
    return sections

def _extract_tags_from_bullets(bullets):
    """
    Look for bullet patterns like 'Tags: a, b, c' and return list of tags.
    """
    tags = []
    for b in bullets:
        if b.lower().startswith("tags:"):
            rest = b.split(":", 1)[1]
            tags = [t.strip() for t in re.split(r'[,\|;]', rest) if t.strip()]
            break
    return tags

def _extract_role_significance(bullets):
    role = None
    significance = None
    notes = []
    for b in bullets:
        if b.lower().startswith("role:"):
            role = b.split(":",1)[1].strip()
        elif b.lower().startswith("significance:"):
            significance = b.split(":",1)[1].strip()
        elif b.lower().startswith("notes:"):
            notes.append(b.split(":",1)[1].strip())
        else:
            # non-labeled bullet treat as a note
            notes.append(b)
    return role, significance, notes

def load_static_lore_files(file_paths=None):
    """
    Read and parse markdown files into the runtime lore repository.
    Default file list (relative to repo root):
      - lore_and_knowledge.md
      - gm_guide.md
      - narrative_directions.md
      - story_elements.md

    This function is idempotent per session (it sets st.session_state.lore_static_loaded).
    """
    init_lore()
    if st.session_state.get("lore_static_loaded"):
        _log.debug("Static lore already loaded for this session; skipping.")
        return {"loaded": False, "reason": "already_loaded"}

    default_files = ["lore_and_knowledge.md", "gm_guide.md", "narrative_directions.md", "story_elements.md"]
    files = file_paths if file_paths else default_files
    repo_root = Path(".")
    loaded_files = []
    for f in files:
        p = repo_root / f
        if not p.exists():
            _log.debug("Static lore file not found: %s", p)
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            _log.debug("Failed to read %s: %s", p, e)
            continue
        parsed = _parse_markdown_entries(text)
        # Merge parsed entries into lore
        for section, entries in parsed.items():
            sec_lower = section.strip().lower()
            # Vexal / Core / Lore sections
            if "vexal" in sec_lower or "core" in sec_lower or "lore" in sec_lower:
                for e in entries:
                    # If entry has a description and no name, treat description as a note
                    if e.get("name"):
                        # Add to vexal notes if name is "Vexal" or description contains 'bastion'
                        name = e["name"]
                        desc = e["description"]
                        if "vexal" in name.lower() or "vexal" in desc.lower() or "bastion" in desc.lower():
                            # if it's the main quest description and name is Vexal or Bastion, set main_quest if not empty
                            if "main quest" in desc.lower() or "recover" in desc.lower() or "bastion" in name.lower():
                                st.session_state.lore["vexal"]["main_quest"] = desc
                            else:
                                add_vexal_note(f"{name}: {desc}")
                        else:
                            add_vexal_note(f"{name}: {desc}")
                    for b in e.get("bullets", []):
                        add_vexal_note(b)
            elif "person" in sec_lower or "npc" in sec_lower or "people" in sec_lower:
                for e in entries:
                    name = e.get("name") or ""
                    if not name:
                        continue
                    role, significance, notes = _extract_role_significance(e.get("bullets", []))
                    tags = _extract_tags_from_bullets(e.get("bullets", []))
                    add_person(name, role=role, significance=significance, note="; ".join(notes) if notes else (e.get("description") or None), tags=tags)
            elif "location" in sec_lower or "place" in sec_lower or "site" in sec_lower or "city" in sec_lower:
                for e in entries:
                    name = e.get("name") or ""
                    if not name:
                        continue
                    desc = e.get("description") or ""
                    role, significance, notes = _extract_role_significance(e.get("bullets", []))
                    tags = _extract_tags_from_bullets(e.get("bullets", []))
                    add_location(name, description=(desc + (" " + "; ".join(notes) if notes else "")).strip(), tags=tags)
            elif "faction" in sec_lower or "order" in sec_lower:
                for e in entries:
                    name = e.get("name") or ""
                    if not name:
                        continue
                    desc = e.get("description") or ""
                    tags = _extract_tags_from_bullets(e.get("bullets", []))
                    st.session_state.lore["factions"].setdefault(name, {"description": desc, "tags": tags})
                    if tags:
                        for t in tags:
                            st.session_state.lore["tags"].add(t)
            else:
                # Generic: try to infer person/location or add to vexal notes
                for e in entries:
                    name = e.get("name")
                    desc = e.get("description", "")
                    if name:
                        # Heuristic: if description contains 'keeper','scholar','priest','captain','lord' -> person
                        if any(k in desc.lower() for k in ("scholar", "priest", "captain", "lord", "merchant", "clerk", "archiv")):
                            add_person(name, note=desc)
                        else:
                            add_location(name, description=desc)
                    else:
                        # a stray description; append as vexal note because it's general lore
                        add_vexal_note(desc)

        loaded_files.append(str(p))
    st.session_state.lore_static_loaded = True
    return {"loaded": True, "files": loaded_files}
