# -*- coding: utf-8 -*-
"""מוסיף לכל דף משחק ב-docs/ כפתורי מגע למסך, כדי שאפשר יהיה לשחק בטלפון.

הכפתורים לכל משחק מוגדרים ב-tools/controls.tsv. לחיצה על כפתור שולחת
אירוע מקלדת אמיתי ל-canvas, ולכן המשחק עצמו לא צריך שינוי.

הכפתורים מוצגים רק במכשירי מגע. אפשר לכפות אותם עם ?pad=1 בכתובת,
ולכבות עם ?pad=0 - שימושי לבדיקה במחשב.

publish.py מריץ את הסקריפט אחרי ההעתקה ל-docs/, כך שהכפתורים חוזרים
בכל בנייה מחדש. ניתן להריץ גם לבד:  python3 tools/touch_controls.py
"""
import json
import os
import re
import sys

START = "<!-- touch-controls: added by tools/touch_controls.py -->"
END = "<!-- /touch-controls -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)

PADS = {
    "arrows4": [("←", "Left", "l"), ("↑", "Up", "u"),
                ("↓", "Down", "d"), ("→", "Right", "r")],
    "arrows_lr": [("←", "Left", "l"), ("→", "Right", "r")],
    "arrows_ud": [("↑", "Up", "u"), ("↓", "Down", "d")],
    "none": [],
}


def read_controls(path):
    """קורא את tools/controls.tsv ומחזיר {slug: {"pad": ..., "actions": [...]}}"""
    conf = {}
    with open(path, encoding="utf-8") as f:
        for num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                print("controls.tsv שורה %d: חסר טאב - %r" % (num, line))
                continue
            slug, pad = parts[0].strip(), parts[1].strip()
            if pad not in PADS:
                print("controls.tsv שורה %d: pad לא מוכר %r" % (num, pad))
                continue
            actions = []
            for item in (parts[2] if len(parts) > 2 else "").split("|"):
                item = item.strip()
                if not item:
                    continue
                if "=" not in item:
                    print("controls.tsv שורה %d: %r אינו Label=Key" % (num, item))
                    continue
                label, key = item.split("=", 1)
                actions.append([label.strip(), key.strip()])
            conf[slug] = {"pad": pad, "actions": actions}
    return conf


ASSET = "touch-controls.js"

JS = r"""/* touch-controls: on-screen buttons so the pygbag games are playable on a phone.
   Written by tools/touch_controls.py - edit that script, not this file. */
(function () {
  "use strict";

  var CONF = window.__TOUCH_CONTROLS__;
  if (!CONF) return;

  var q = new URLSearchParams(location.search).get("pad");
  if (q === "0") return;
  var isTouch = navigator.maxTouchPoints > 0 || "ontouchstart" in window;
  if (q !== "1" && !isTouch) return;
  if (!CONF.pad && !(CONF.actions && CONF.actions.length)) return;

  /* ---------- key name -> KeyboardEvent fields ---------- */
  var NAMED = {
    Up: ["ArrowUp", "ArrowUp", 38],
    Down: ["ArrowDown", "ArrowDown", 40],
    Left: ["ArrowLeft", "ArrowLeft", 37],
    Right: ["ArrowRight", "ArrowRight", 39],
    Space: [" ", "Space", 32],
    Enter: ["Enter", "Enter", 13],
    Esc: ["Escape", "Escape", 27],
    Shift: ["Shift", "ShiftLeft", 16],
    Ctrl: ["Control", "ControlLeft", 17],
    Tab: ["Tab", "Tab", 9],
    Backspace: ["Backspace", "Backspace", 8]
  };

  function fields(name) {
    if (NAMED[name]) {
      return { key: NAMED[name][0], code: NAMED[name][1], keyCode: NAMED[name][2] };
    }
    if (/^F([1-9]|1[0-2])$/.test(name)) {
      return { key: name, code: name, keyCode: 111 + parseInt(name.slice(1), 10) };
    }
    if (/^[a-z]$/.test(name)) {
      return {
        key: name,
        code: "Key" + name.toUpperCase(),
        keyCode: name.toUpperCase().charCodeAt(0)
      };
    }
    if (/^[A-Z]$/.test(name)) {
      return { key: name.toLowerCase(), code: "Key" + name, keyCode: name.charCodeAt(0) };
    }
    if (/^[0-9]$/.test(name)) {
      return { key: name, code: "Digit" + name, keyCode: 48 + parseInt(name, 10) };
    }
    console.warn("touch-controls: unknown key", name);
    return null;
  }

  /* ---------- send a real keyboard event to the game ---------- */
  function target() {
    return document.getElementById("canvas") || document.body || document;
  }

  function send(type, f) {
    var ev = new KeyboardEvent(type, {
      key: f.key,
      code: f.code,
      keyCode: f.keyCode,
      which: f.keyCode,
      charCode: 0,
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window
    });
    /* keyCode/which are read-only on the constructed event in some browsers */
    try {
      if (ev.keyCode !== f.keyCode) {
        Object.defineProperty(ev, "keyCode", { get: function () { return f.keyCode; } });
        Object.defineProperty(ev, "which", { get: function () { return f.keyCode; } });
      }
    } catch (e) { /* ignore */ }
    target().dispatchEvent(ev);
  }

  /* ---------- build the pad ---------- */
  var css = document.createElement("style");
  css.textContent = [
    "#touchpad{position:fixed;inset:auto 0 0 0;z-index:2147483646;display:flex;",
    "align-items:flex-end;justify-content:space-between;gap:10px;pointer-events:none;",
    "padding:0 12px calc(12px + env(safe-area-inset-bottom)) 12px;",
    "font:700 16px/1 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}",
    "#touchpad.hidden .tp-cluster{display:none}",
    ".tp-cluster{pointer-events:auto;display:grid;gap:8px;touch-action:none}",
    ".tp-dpad{grid-template-columns:repeat(3,56px);grid-template-rows:repeat(2,56px)}",
    ".tp-dpad .tp-l{grid-area:2/1}.tp-dpad .tp-u{grid-area:1/2}",
    ".tp-dpad .tp-d{grid-area:2/2}.tp-dpad .tp-r{grid-area:2/3}",
    ".tp-acts{grid-auto-flow:row dense;grid-template-columns:repeat(2,auto);justify-items:end}",
    ".tp-btn{-webkit-appearance:none;appearance:none;min-width:56px;min-height:56px;",
    "padding:0 12px;border-radius:14px;border:1px solid #ffffff2e;color:#f3f1ff;",
    "background:#181634c4;backdrop-filter:blur(3px);font:inherit;font-size:15px;",
    "display:flex;align-items:center;justify-content:center;touch-action:none;",
    "user-select:none;-webkit-user-select:none;-webkit-tap-highlight-color:transparent;",
    "box-shadow:0 2px 10px #0006;transition:transform .06s,background .06s}",
    ".tp-dpad .tp-btn{font-size:24px;padding:0}",
    ".tp-btn.on{background:#3de0ffd9;color:#0b0a1f;transform:scale(.93)}",
    "#tp-toggle{position:fixed;right:12px;top:10px;z-index:2147483647;pointer-events:auto;",
    "min-width:0;width:40px;height:40px;min-height:0;padding:0;font-size:19px;opacity:.72}",
    ""
  ].join("");
  document.head.appendChild(css);

  var pad = document.createElement("div");
  pad.id = "touchpad";

  function button(label, keyName, cls) {
    var f = fields(keyName);
    var b = document.createElement("button");
    b.className = "tp-btn" + (cls ? " tp-" + cls : "");
    b.type = "button";
    b.textContent = label;
    b.setAttribute("aria-label", label);
    if (!f) return b;

    var down = false;
    function press(e) {
      e.preventDefault();
      e.stopPropagation();
      if (down) return;
      down = true;
      b.classList.add("on");
      send("keydown", f);
    }
    function release(e) {
      if (e) { e.preventDefault(); e.stopPropagation(); }
      if (!down) return;
      down = false;
      b.classList.remove("on");
      send("keyup", f);
    }
    b.addEventListener("pointerdown", function (e) {
      /* keep the touch on this button even if the finger slides off */
      if (b.setPointerCapture) { try { b.setPointerCapture(e.pointerId); } catch (x) {} }
      press(e);
    });
    b.addEventListener("pointerup", release);
    b.addEventListener("pointercancel", release);
    b.addEventListener("lostpointercapture", function () { release(null); });
    b.addEventListener("contextmenu", function (e) { e.preventDefault(); });
    window.addEventListener("blur", function () { release(null); });
    return b;
  }

  var dpad = document.createElement("div");
  dpad.className = "tp-cluster tp-dpad";
  (CONF.pad || []).forEach(function (spec) {
    dpad.appendChild(button(spec[0], spec[1], spec[2]));
  });

  var acts = document.createElement("div");
  acts.className = "tp-cluster tp-acts";
  (CONF.actions || []).forEach(function (spec) {
    acts.appendChild(button(spec[0], spec[1]));
  });

  if (dpad.childNodes.length) pad.appendChild(dpad);
  else pad.appendChild(document.createElement("div"));
  if (acts.childNodes.length) pad.appendChild(acts);

  var toggle = document.createElement("button");
  toggle.id = "tp-toggle";
  toggle.className = "tp-btn";
  toggle.type = "button";
  toggle.title = "Show / hide the touch buttons";
  toggle.setAttribute("aria-label", "Show or hide the touch buttons");
  toggle.textContent = "⌨";
  toggle.addEventListener("click", function () {
    pad.classList.toggle("hidden");
    toggle.style.opacity = pad.classList.contains("hidden") ? ".45" : ".72";
  });

  function mount() {
    document.body.appendChild(pad);
    document.body.appendChild(toggle);
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
"""


def snippet(conf):
    data = {"pad": [list(x) for x in PADS[conf["pad"]]], "actions": conf["actions"]}
    return "%s\n<script>window.__TOUCH_CONTROLS__ = %s;</script>\n<script src=\"%s\"></script>\n%s\n" % (
        START, json.dumps(data, ensure_ascii=False), ASSET, END)


def add(path, conf):
    with open(path, encoding="utf-8") as f:
        page = f.read()
    page = BLOCK_RE.sub("", page)          # להחליף גרסה קודמת, לא לשרשר
    if "</body>" not in page:
        print("אין </body> ב-%s" % path)
        return False
    page = page.replace("</body>", snippet(conf) + "</body>", 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(os.path.dirname(path), ASSET), "w", encoding="utf-8") as f:
        f.write(JS)
    return True


def main(docs=None):
    here = os.path.dirname(os.path.abspath(__file__))
    docs = docs or os.path.join(os.path.abspath("."), "docs")
    conf = read_controls(os.path.join(here, "controls.tsv"))
    done, missing = 0, []
    for slug in sorted(os.listdir(docs)):
        page = os.path.join(docs, slug, "index.html")
        if not os.path.isfile(page):
            continue
        if slug not in conf:
            missing.append(slug)
            continue
        if add(page, conf[slug]):
            done += 1
    if missing:
        print("אין שורה ב-controls.tsv עבור: %s" % ", ".join(missing))
    print("כפתורי מגע נוספו ל-%d דפי משחק" % done)
    return done


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
