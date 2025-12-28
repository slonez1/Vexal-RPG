"""
Example usage for the GM orchestrator.

Create a small narrative history file (or build a Python list) and run the orchestrator to produce:
- A Memory Summary
- A GM continuation that starts with a style echo, continues the scene, and ends with a GM note.

Set OPENAI_API_KEY in your environment before running this example.
"""

from gm_orchestrator import run_gm_step

if __name__ == "__main__":
    # Example narrative history (oldest -> newest)
    narrative_history = [
        "We left at dawn. The sea smelled of iron; Lysa kept checking the torn map fragment.",
        "At midday the group argued in whispers. Tomas accused Rhett of hiding a letter.",
        "We reached the ruined mill. A black-winged crow landed on the mill's broken wheel.",
        "Mara found a scrap of paper with a half-seal; it matched the torn map.",
        "That night, Tomas did not sleep. He stared at the river like he expected it to answer."
    ]

    memory_summary, gm_output = run_gm_step(
        narrative_history,
        recent_n=4,
        summary_max_tokens=250,
        target_words=300,
        temperature=0.25,
        similarity_threshold=0.75,
        max_attempts=2
    )

    print("----- MEMORY SUMMARY -----")
    print(memory_summary)
    print("\n----- GM OUTPUT -----")
    print(gm_output)
