

import copy
from flask import Flask, request, jsonify, Response
app = Flask(__name__)

DIRS = {
    "up":    {"dr": -1, "dc":  0, "glyph": "↑"},
    "down":  {"dr":  1, "dc":  0, "glyph": "↓"},
    "left":  {"dr":  0, "dc": -1, "glyph": "←"},
    "right": {"dr":  0, "dc":  1, "glyph": "→"},
}

LEVELS = [
    {
        "rows": 6, "cols": 6, "mistakes": 3,
        "arrows": [
            {"r": 0, "c": 0, "dir": "right"},
            {"r": 1, "c": 1, "dir": "up"},
            {"r": 2, "c": 3, "dir": "down"},
            {"r": 3, "c": 4, "dir": "left"},
            {"r": 4, "c": 0, "dir": "right"},
            {"r": 5, "c": 2, "dir": "up"},
        ],
    },

    {
        "rows": 6, "cols": 6, "mistakes": 3,
        "arrows": [
            {"r": 0, "c": 0, "dir": "right"},
            {"r": 0, "c": 2, "dir": "up"},
            {"r": 1, "c": 0, "dir": "up"},
            {"r": 2, "c": 1, "dir": "right"},
            {"r": 2, "c": 4, "dir": "down"},
            {"r": 3, "c": 1, "dir": "down"},
            {"r": 4, "c": 3, "dir": "left"},
            {"r": 4, "c": 5, "dir": "up"},
            {"r": 5, "c": 2, "dir": "right"},
        ],
    },

    {
        "rows": 6, "cols": 6, "mistakes": 4,
        "arrows": [
            {"r": 0, "c": 3, "dir": "down"},
            {"r": 0, "c": 5, "dir": "left"},
            {"r": 1, "c": 1, "dir": "right"},
            {"r": 1, "c": 4, "dir": "up"},
            {"r": 2, "c": 0, "dir": "up"},
            {"r": 2, "c": 3, "dir": "down"},
            {"r": 3, "c": 2, "dir": "left"},
            {"r": 3, "c": 5, "dir": "up"},
            {"r": 4, "c": 0, "dir": "right"},
            {"r": 4, "c": 5, "dir": "up"},
            {"r": 5, "c": 2, "dir": "up"},
            {"r": 5, "c": 4, "dir": "right"},
        ],
    },
]

CURRENT = {"state": None}


def build_state(idx: int) -> dict:
    lv = LEVELS[idx]
    return {
        "level_index":    idx,
        "level_total":    len(LEVELS),
        "rows":           lv["rows"],
        "cols":           lv["cols"],
        "mistakes_total": lv["mistakes"],
        "mistakes_left":  lv["mistakes"],
        "arrows":         copy.deepcopy(lv["arrows"]),
        "locked":         False,
    }

def public_state(state):
    return {
        "level_index":   state["level_index"],
        "level_total":   state["level_total"],
        "rows":          state["rows"],
        "cols":          state["cols"],
        "mistakes_left": state["mistakes_left"],
        "arrows_left":   len(state["arrows"]),
        "arrows":        state["arrows"],
        "locked":        state["locked"],
    }

