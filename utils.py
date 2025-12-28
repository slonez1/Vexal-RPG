from copy import deepcopy

def deep_copy_state(gs):
    """Return a deepcopy of a game state dict to avoid accidental mutation."""
    return deepcopy(gs)
