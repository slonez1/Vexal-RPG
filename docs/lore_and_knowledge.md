# Lore & Knowledge — Starter File

Purpose
-------
This file is the authoritative, editable source of static world knowledge used by the GM LLM as context. Edit freely. Keep each entry concise (1–3 short sentences). The LLM will be given a short, prioritized selection of the most-relevant facts from this file before generating narrative responses.

Usage Notes for the LLM
-----------------------
- The GM should prepend a short "context" built from up to 5 highest-priority facts (location description, relevant NPCs, known artifacts, factions) before calling the LLM.
- Each entry below uses a one-line summary and optional bullet notes. The LLM can parse short lines directly; avoid very long paragraphs.
- Keep "tags" short (single words) so the LLM can filter by tag easily.
- Example context JSON (what the app should build and pass to the model) is included at the bottom of this file.

Formatting Conventions (please follow)
-------------------------------------
- Section headings: use H2 (##)
- Entries: use bolded Name followed by an em dash and a one-line summary.
- Optional fields under an entry: use bullets starting with `- Role:`, `- Significance:`, `- Tags:`, `- Notes:`.
- Keep each bullet 1–2 short sentences.
- Use plain English; avoid markup inside the short summaries.

Vexal Lore (Core)
-----------------
**Vexal** — A corrupting cosmic influence tied to an ancient artifact known as the Bastion.  
- Significance: Causes attribute suppression and pool penalties; central to the campaign's main quest.  
- Main Quest: Recover the fragments of the Bastion and choose to cleanse, bind, or destroy Vexal.  
- Known Clues: Mentions of "shards" or "fragments" in ruined temples, cultscribe notes, and dreams.

**The Bastion (Artifact)** — An ancient sentinel/keystone, now broken into fragments dispersed across the world.  
- Fragments: Number unknown (starter campaign: 5 fragments). Each fragment is bound to a distinct location type (ruin, shrine, battlefield, tomb, stronghold).  
- Warning: As fragments are gathered, the Vexal influence may react — increase in intensity near assembled fragments.

Persons of Interest
-------------------
**Amara Silvermoon** — Player character; a knight touched by Vexal.  
- Role: Protagonist.  
- Significance: High Divine Favor; bearer of Vexal corruption.  
- Tags: protagonist, vexal, divine

**Eldon Arkwright** — Scholar of ancient relics, expert on the Bastion.  
- Role: Quest-giver / lore source.  
- Significance: Knows locations of fragment hints; typically found in Sunlit Kingdoms libraries.  
- Tags: scholar, questgiver

**High Priestess Kara** — Cleric of the Sunlit Faith.  
- Role: Religious contact; senses Vexal taint.  
- Significance: Can detect corruption and perform partial purification rituals.  
- Tags: cleric, religion

**Captain Iren** — Mercenary leader from Harrowfen.  
- Role: Potential ally or rival; controls local bandits.  
- Significance: Holds knowledge of a fragment's last known movement.  
- Tags: mercenary, antagonist

Locations
---------
**Sunlit Capital** — The prosperous capital; political center and archive hub.  
- Tags: city, archive, polity

**Harrowfen Keep** — A ruined fortress with ritual scars and cult activity.  
- Significance: Site of whispers about a Bastion fragment.  
- Tags: ruin, dungeon

**The Bastion Ruins** — Shattered watch-tower where the Bastion once stood.  
- Notes: Dangerous, Vexal-tainted, and a late-game destination.  
- Tags: holy_site, ruin

**Wyvern Road** — Major trade route between the Sunlit Capital and the western hills.  
- Notes: Frequent travel events; suitable for "journey" scenes.  
- Tags: road, travel

Factions
--------
**Sunlit Order** — Church and knights that protect sacred knowledge.  
- Goals: Contain corruption; guard relic lore.  
- Tags: religion, order

**The Bloodriven** — Cult that embraces Vexal in pursuit of power.  
- Goals: Gather fragments to awaken an entity.  
- Tags: cult, villain

Artifacts & Items
-----------------
**Bastion Fragment (Type A)** — A shard of the Bastion; faintly hums when near other fragments.  
- Significance: Grants insight but increases Vexal pull when carried.  
- Tags: fragment, artifact

**Solari Longsword** — Hero weapon with holy runes; counters some Vexal effects.  
- Tags: weapon, holy

Rumors & Hooks
--------------
- "An old scholar in the Sunlit Capital mutters about a map burned into an urn."  
- "Bandit captains fight over a metal shard bright as dawn."  
- "A shrine north of Harrowfen weeps black sap at night."

Session Notes / Campaign State (editable during play)
----------------------------------------------------
- Last session: Amara interrogated a bandit who mentioned 'Harrowfen Keep' and a fragment trade.  
- Active Quests:
  - Recover Bastion fragments (progress: 0/5).
  - Find Eldon Arkwright (last seen in Sunlit Capital library).
- Discovered Clues:
  - "Shards resonate near holy iron." (note source: bandit interrogation)

LLM Prompt Context Example (how the app should build it)
--------------------------------------------------------
The app should assemble a small JSON-like context object from the most relevant facts before calling the LLM. Keep each fact short. Example:

```json
{
  "player_name": "Amara Silvermoon",
  "location": {"name": "Harrowfen Keep", "short_description": "A ruined fortress with ritual scars and cult activity."},
  "top_persons": [
    {"name": "Eldon Arkwright", "role": "Scholar", "note": "Researcher of the Bastion; last seen in Sunlit Capital"},
    {"name": "High Priestess Kara", "role": "Cleric", "note": "Can sense Vexal corruption"}
  ],
  "top_tags": ["vexal", "fragment", "ruin"],
  "main_quest": "Recover the fragments of the Bastion artifact to cleanse or destroy the Vexal corruption.",
  "recent_events": ["Bandit said: 'They traded a bright shard near Harrowfen.'"]
}
```

Suggested system prompt to prepend to the LLM call
-------------------------------------------------
(Place this text in gm_guide.md or use it directly in code as the system prompt.)

"You are the Game Master (GM) for an epic fantasy tabletop-style single-player RPG. Use the JSON context provided to you (player, location, persons, tags, main_quest, recent_events). Produce immersive, scene-setting narrative replies in two parts: (1) a human-facing descriptive paragraph (2–4 sentences) that advances the scene and offers 2 meaningful choices for the player; and (2) a compact JSON summary (on its own line inside triple backticks) describing any lore items discovered, any persons/locations to add to the knowledge base, and an optional time_advance hint. The JSON schema must be:

{
  "narrative_tags": ["tag1","tag2"],
  "persons": [{"name":"", "role":"", "significance":"", "tags":[""]}],
  "locations": [{"name":"", "description":"", "tags":[""]}],
  "vexal_updates": ["short sentences about Bastion/Vexal"],
  "time_advance": {"scale":"combat"|"travel"|"custom", "hours":float, "seconds":int}
}

Ensure the narrative is consistent with the context. If nothing new is found, return empty arrays and no time_advance."

Editing guidance
----------------
- Keep entries concise to avoid overloading the LLM with irrelevant tokens.
- Add new discoveries under "Session Notes" after each session so the LLM sees the latest important facts.
- Use tags consistently (e.g., 'vexal', 'fragment', 'ruin', 'scholar').

Example minimal additions you can paste quickly
----------------------------------------------
- Under Vexal Lore: add "Fragment Clues: a set of rune-inscribed stones, each fragment's rune corresponds to a different element (fire, water, earth, air, light)."
- Under Persons: add "**Mara the Cartographer** — Travel guide; knows minor roads and hidden shrines. - Tags: cartographer, travel"
- Under Locations: add "**Whitefen Village** — Small farming village near Wyvern Road; traders pass through weekly. - Tags: village, trade"

End of file
