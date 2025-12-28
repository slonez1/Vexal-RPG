"""
Simple static GM response strategy for testing.
Produces deterministic, template-based narrative strings and
a small extracted dict containing hints for lore and time advances.
"""
from datetime import datetime

def static_get_response(prompt, gs):
    """
    Very small rule-based GM for testing:
    - If prompt contains 'solve' -> puzzle solved narrative
    - If contains 'attack'/'fight' -> short combat narration
    - If contains 'travel'/'journey' -> travel narration with a time_advance hint
    - Otherwise, echo with simple narrative text
    Returns: (narrative_str, extraction_dict)
    """
    txt = (prompt or "").lower()
    if "solve" in txt:
        narrative = f"Narrative: You solve a puzzle. A hidden passage opens near {gs.get('location','the area')}."
        extraction = {"vexal_updates": [], "persons": [], "locations": [], "time_advance": {"seconds": 10}}
        return narrative, extraction

    if any(w in txt for w in ("attack", "fight", "strike", "hit", "cast")):
        narrative = "Narrative: Combat erupted — you exchange blows. You took damage but stand firm."
        # combat is fast: suggest seconds per turn
        extraction = {"time_advance": {"scale": "combat", "seconds_per_turn": 6}, "persons": [], "locations": []}
        return narrative, extraction

    if any(w in txt for w in ("travel", "journey", "ride", "ride across", "riding")):
        narrative = "Narrative: You travel across the countryside; the road is empty and the journey passes uneventfully."
        # Travel is hours-based; LLM might suggest hours, here we give a sample
        extraction = {"time_advance": {"scale": "travel", "hours": 8}, "locations": [gs.get("location","Unknown")]}
        return narrative, extraction

    # default
    narrative = f"Narrative: Amara attempts '{prompt}'. The GM notes nothing remarkable."
    extraction = {"persons": [], "locations": [], "vexal_updates": []}
    return narrative, extraction
