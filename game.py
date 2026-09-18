# -*- coding: utf-8 -*-
"""
箭头大逃亡 —— 单文件版（Python Flask + 内嵌 HTML）
运行：
    pip install flask
    python game.py
然后浏览器打开 http://127.0.0.1:5000
"""

import copy
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ============================================================
# 1. 方向定义
# ============================================================
DIRS = {
    "up":    {"dr": -1, "dc":  0, "glyph": "↑"},
    "down":  {"dr":  1, "dc":  0, "glyph": "↓"},
    "left":  {"dr":  0, "dc": -1, "glyph": "←"},
    "right": {"dr":  0, "dc":  1, "glyph": "→"},
}

# ============================================================
# 2. 关卡数据
# ============================================================
LEVELS = [
    # 第 1 关：教学关，所有箭头都能直接飞出
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
    # 第 2 关：出现依赖链
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
    # 第 3 关：多段依赖链
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

# 全局对局状态（单人作业足够用）
CURRENT = {"state": None}


# ============================================================
# 3. 逻辑函数
# ============================================================
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


# ============================================================
# 4. 路由
# ============================================================
@app.route("/")
def index():
    return render_template(index.html, mimetype="text/html")


@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json(silent=True) or {}
    try:
        idx = int(data.get("index", 0))
    except (TypeError, ValueError):
        idx = 0
    if idx < 0 or idx >= len(LEVELS):
        idx = 0
    CURRENT["state"] = build_state(idx)
    return jsonify({"ok": True, "state": public_state(CURRENT["state"])})


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




# ============================================================
# 6. 启动
# ============================================================
if __name__ == "__main__":
    # 启动前自检：确认每一关都有箭头
    for i, lv in enumerate(LEVELS):
        assert lv["arrows"], "第 " + str(i + 1) + " 关没有箭头！"
    total = sum(len(lv["arrows"]) for lv in LEVELS)
    print("=" * 52)
    print("  箭头大逃亡已启动")
    print("  共", len(LEVELS), "个关卡，共", total, "个箭头")
    print("  请打开： http://127.0.0.1:5000")
    print("=" * 52)
    app.run(host="0.0.0.0", port=5000, debug=True)