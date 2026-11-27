/* touch-controls: on-screen buttons so the pygbag games are playable on a phone.
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
