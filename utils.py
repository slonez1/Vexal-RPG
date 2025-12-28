from typing import List
import numpy as np

def cosine_similarity(a: List[float], b: List[float]) -> float:
    a_arr = np.array(a, dtype=float)
    b_arr = np.array(b, dtype=float)
    if a_arr.size == 0 or b_arr.size == 0:
        return 0.0
    denom = (np.linalg.norm(a_arr) * np.linalg.norm(b_arr))
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)

def average_sentence_length(text: str) -> float:
    # crude approximation
    import re
    sentences = re.split(r'[.!?]+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0
    words = [len(s.split()) for s in sentences]
    return sum(words) / len(words)
