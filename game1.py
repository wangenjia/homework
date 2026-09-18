

import copy
from flask import Flask, request, jsonify, render_template
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

def arrow_at(state, r, c):
    for a in state["arrows"]:
        if a["r"] == r and a["c"] == c:
            return a
    return None

def find_blocker(state, arrow):
    dr = DIRS[arrow["dir"]]["dr"]
    dc = DIRS[arrow["dir"]]["dc"]
    r = arrow["r"] + dr
    c = arrow["c"] + dc
    while 0 <= r < state["rows"] and 0 <= c < state["cols"]:
        hit = arrow_at(state, r, c)
        if hit:
            return hit
        r += dr
        c += dc
    return None


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

@app.route("/")
def index():
    return render_template(index.html, mimetype="text/html")


@app.route("/api/restart", methods=["POST"])
def api_restart():
    state = CURRENT.get("state")
    if not state:
        return jsonify({"ok": False, "error": "no_game"}), 400
    new_state = build_state(state["level_index"])
    CURRENT["state"] = new_state
    return jsonify({"ok": True, "state": public_state(new_state)})


@app.route("/api/next_level", methods=["POST"])
def api_next_level():
    state = CURRENT.get("state")
    if not state:
        return jsonify({"ok": False, "error": "no_game"}), 400
    nxt = state["level_index"] + 1
    if nxt >= len(LEVELS):
        nxt = 0
    new_state = build_state(nxt)
    CURRENT["state"] = new_state
    return jsonify({"ok": True, "state": public_state(new_state)})


@app.route("/api/click", methods=["POST"])
def api_click():
    state = CURRENT.get("state")
    if not state:
        return jsonify({"ok": False, "error": "no_game"}), 400

    if state["locked"]:
        return jsonify({"ok": False, "error": "locked",
                        "state": public_state(state)})

    data = request.get_json(silent=True) or {}
    r, c = data.get("r"), data.get("c")
    if r is None or c is None:
        return jsonify({"ok": False, "error": "bad_request"}), 400

    arrow = arrow_at(state, r, c)
    if arrow is None:
        return jsonify({"ok": False, "error": "empty",
                        "state": public_state(state)})

    blocker = find_blocker(state, arrow)

    if blocker is not None:
        state["mistakes_left"] -= 1
        failed = state["mistakes_left"] <= 0
        if failed:
            state["locked"] = True
        return jsonify({
            "ok":            True,
            "result":        "blocked",
            "arrow":         arrow,
            "blocker":       blocker,
            "mistakes_left": state["mistakes_left"],
            "failed":        failed,
            "state":         public_state(state),
        })

    state["arrows"] = [a for a in state["arrows"]
                       if not (a["r"] == r and a["c"] == c)]
    cleared = (len(state["arrows"]) == 0)
    completed = cleared and (state["level_index"] + 1 >= len(LEVELS))
    if cleared:
        state["locked"] = True

    return jsonify({
        "ok":          True,
        "result":      "flew",
        "arrow":       arrow,
        "arrows_left": len(state["arrows"]),
        "cleared":     cleared,
        "completed":   completed,
        "state":       public_state(state),
    })