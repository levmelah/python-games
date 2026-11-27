# -*- coding: utf-8 -*-
"""בונה את docs/index.html - הדף הראשי של אוסף המשחקים."""
import csv, html, json, os, re, sys

S = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(".")
SITE = os.path.join(ROOT, "docs")

# אחרי שתיפתח החשבון ב-GitHub, צריך להחליף את הכתובת הזאת
REPO_URL = "https://github.com/levmelah/python-games/blob/main"

ENGINE_NOTE = {
    "ursina": "ursina (3D)",
    "panda3d": "Panda3D (3D)",
    "tkinter": "tkinter",
    "turtle": "turtle",
    "qt": "PySide6",
}

# אימוג'י לכל משחק. משחק שלא מופיע כאן מקבל אימוג'י לפי מילה בשם שלו,
# ואם גם זה לא עוזר - קוביית משחק.
EMOJI = {
    "abandoned-compound-cameras": "📹",
    "abandoned-compound-creepy": "🔦",
    "abandoned-compound-english": "🏚️",
    "abandoned-compound-ending": "🚪",
    "alien-invasion": "👾",
    "arkanoid": "🧱",
    "bomberman": "💣",
    "bounce-ball": "🏀",
    "bowling": "🎳",
    "bowling-2": "🎳",
    "captain-vertical": "🦸",
    "cat-coins": "🪙",
    "cockpit-racer": "✈️",
    "cockpit-racer-2": "🚀",
    "count-control": "🔢",
    "count-control-3d": "🧮",
    "cursor-camp": "🖱️",
    "diving-cat": "🤿",
    "doodle-war": "✏️",
    "doodle-war-2": "🖍️",
    "dungeon-roguelike": "🗝️",
    "football": "⚽",
    "garten-of-banban": "🎪",
    "garten-of-banban-2": "🎠",
    "garten-of-banban-3d": "🎡",
    "geometry-dash": "🔺",
    "guns-guns-guns": "🔫",
    "hide-and-paint": "🎨",
    "im-not-a-robot": "🤖",
    "infinite-neon-background": "🌈",
    "level-devil-god-mode": "😈",
    "level-devil-ultimate": "🔥",
    "marble-run-3d": "🔮",
    "minecraft-sandbox": "⛏️",
    "mini-mario": "🍄",
    "mini-mario-cat": "🐱",
    "mini-mario-cat-animated": "😺",
    "morph-balls": "🫧",
    "night-shift-3d": "🧸",
    "pacman": "🟡",
    "planet-destruction": "🪐",
    "platform-adventure": "🧗",
    "poppy-playtime-3d": "🎈",
    "slime-lab": "🧪",
    "smoldering-root": "🌱",
    "soldier-vs-orcs": "⚔️",
    "space-subtraction": "🛸",
    "tamagotchi": "🥚",
    "the-hollow": "🌲",
    "the-hollow-2": "🦉",
    "time-moves-when-you-move": "⏱️",
}

EMOJI_WORDS = [
    ("cat", "🐱"), ("dog", "🐶"), ("space", "🚀"), ("alien", "👾"),
    ("car", "🏎️"), ("race", "🏁"), ("ball", "⚽"), ("maze", "🌀"),
    ("puzzle", "🧩"), ("ghost", "👻"), ("zombie", "🧟"), ("robot", "🤖"),
    ("math", "➗"), ("paint", "🎨"), ("draw", "✏️"), ("snake", "🐍"),
    ("fish", "🐠"), ("dino", "🦕"), ("war", "⚔️"), ("night", "🌙"),
]

# שמונה שילובי צבעים; כל קלף מקבל אחד מהם לפי השם שלו, כך שהצבע קבוע
PALETTES = 8


def emoji_for(slug, title):
    if slug in EMOJI:
        return EMOJI[slug]
    low = (slug + " " + title).lower()
    for word, char in EMOJI_WORDS:
        if word in low:
            return char
    return "🎲"


def palette_of(slug):
    return sum(ord(c) for c in slug) % PALETTES


def pretty(path):
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"[_\-]+", " ", name).strip()
    return name


def card(slug, title, subtitle):
    return (
        '      <a class="card" href="%s/" data-name="%s" style="--p: %d">\n'
        '        <span class="thumb" aria-hidden="true">%s</span>\n'
        '        <span class="name">%s</span>\n'
        '        <span class="sub">%s</span>\n'
        '        <span class="play" aria-hidden="true">PLAY &#9654;</span>\n'
        '      </a>\n'
        % (html.escape(slug), html.escape(title.lower()), palette_of(slug),
           emoji_for(slug, title), html.escape(title), html.escape(subtitle))
    )


def main():
    playable = [l.strip() for l in open(os.path.join(S, "playable.txt"),
                                        encoding="utf-8") if l.strip()]
    man = {r[1]: r for r in csv.reader(
        open(os.path.join(S, "manifest.tsv"), encoding="utf-8"), delimiter="\t")}

    cards = ""
    for slug in playable:
        row = man[slug]
        cards += card(slug, row[2], "pygame")

    native = []
    for eng, path, cap in csv.reader(
            open(os.path.join(S, "native.tsv"), encoding="utf-8"), delimiter="\t"):
        if path.startswith("lesson/"):
            continue
        native.append((eng, path, cap.strip() or pretty(path)))
    native.sort(key=lambda t: (t[0], t[2].lower()))

    rows = ""
    for eng, path, name in native:
        rows += (
            '        <li><span class="n">%s</span>'
            '<span class="e">%s</span>'
            '<a href="%s/%s">source</a></li>\n'
            % (html.escape(name), html.escape(ENGINE_NOTE.get(eng, eng)),
               REPO_URL, html.escape(path.replace(" ", "%20")))
        )

    # הצבה בתווים @@name@@ ולא ב-% , כי התבנית מלאה אחוזים של CSS
    page = PAGE
    for key, value in [
        ("n_play", len(playable)),
        ("n_native", len(native)),
        ("n_total", len(playable) + len(native)),
        ("cards", cards),
        ("rows", rows),
        ("slugs", json.dumps(playable)),
    ]:
        page = page.replace("@@%s@@" % key, str(value))
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page)
    print("docs/index.html: %d בדפדפן, %d להורדה" % (len(playable), len(native)))


PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Python Games &#127918;</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&display=swap">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#127918;</text></svg>">
<style>
  :root {
    --bg: #0b0a1f;
    --panel: #181634;
    --panel-2: #211e45;
    --line: #322c63;
    --text: #f3f1ff;
    --dim: #a9a3d4;
    --pink: #ff4fa3;
    --cyan: #3de0ff;
    --lime: #9bff5c;
    --gold: #ffd43b;
  }
  /* שמונה שילובי צבעים לקלפים */
  .card[style*="--p: 0"] { --c1: #ff4fa3; --c2: #ff8a3d; }
  .card[style*="--p: 1"] { --c1: #3de0ff; --c2: #6c5cff; }
  .card[style*="--p: 2"] { --c1: #9bff5c; --c2: #1fd6a0; }
  .card[style*="--p: 3"] { --c1: #ffd43b; --c2: #ff6b3d; }
  .card[style*="--p: 4"] { --c1: #c77dff; --c2: #ff4fa3; }
  .card[style*="--p: 5"] { --c1: #3de0ff; --c2: #9bff5c; }
  .card[style*="--p: 6"] { --c1: #ff6b6b; --c2: #c77dff; }
  .card[style*="--p: 7"] { --c1: #6c5cff; --c2: #3de0ff; }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.55 "Baloo 2", "Trebuchet MS", system-ui, -apple-system, sans-serif;
    background-image:
      radial-gradient(900px 520px at 12% -8%, #ff4fa32e, transparent 70%),
      radial-gradient(760px 480px at 88% 2%, #3de0ff2b, transparent 70%),
      radial-gradient(700px 500px at 50% 108%, #9bff5c1f, transparent 70%);
    background-attachment: fixed;
  }
  .wrap { max-width: 1120px; margin: 0 auto; padding: 40px 18px 90px; }

  /* ---------- כותרת ---------- */
  header.hero { text-align: center; padding: 18px 0 8px; }
  .badge {
    display: inline-block; padding: 6px 16px; border-radius: 999px;
    background: #ffffff14; border: 2px solid var(--line);
    font-size: .82rem; font-weight: 700; letter-spacing: .14em;
    text-transform: uppercase; color: var(--cyan);
  }
  h1 {
    font-size: clamp(2.4rem, 8vw, 4.4rem); line-height: 1.02;
    margin: 16px 0 10px; font-weight: 900; letter-spacing: -.03em;
    background: linear-gradient(94deg, var(--pink), var(--gold) 38%, var(--lime) 62%, var(--cyan));
    -webkit-background-clip: text; background-clip: text; color: transparent;
    filter: drop-shadow(0 6px 22px #ff4fa33d);
  }
  .lede { color: var(--dim); margin: 0 auto 22px; max-width: 46ch; font-size: 1.06rem; }
  .lede b { color: var(--text); }

  /* ---------- חיפוש + הגרלה ---------- */
  .tools {
    display: flex; flex-wrap: wrap; gap: 12px; justify-content: center;
    margin: 0 0 10px;
  }
  .search { position: relative; flex: 1 1 320px; max-width: 420px; }
  .search span { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); font-size: 1.1rem; }
  input#q {
    width: 100%; padding: 14px 16px 14px 46px; border-radius: 999px;
    background: var(--panel); color: var(--text);
    border: 2px solid var(--line); font: inherit; font-weight: 600;
    outline: none; transition: border-color .15s, box-shadow .15s;
  }
  input#q::placeholder { color: var(--dim); font-weight: 500; }
  input#q:focus { border-color: var(--cyan); box-shadow: 0 0 0 4px #3de0ff26; }
  button#lucky {
    padding: 14px 24px; border-radius: 999px; border: 0; cursor: pointer;
    font: inherit; font-weight: 800; color: #1a0b22;
    background: linear-gradient(94deg, var(--gold), var(--pink));
    box-shadow: 0 8px 0 #0000004d, 0 10px 26px #ff4fa345;
    transition: transform .12s, box-shadow .12s;
  }
  button#lucky:hover { transform: translateY(-2px); box-shadow: 0 10px 0 #0000004d, 0 14px 30px #ff4fa359; }
  button#lucky:active { transform: translateY(3px); box-shadow: 0 3px 0 #0000004d; }

  /* ---------- כותרות ביניים ---------- */
  h2 {
    font-size: 1.5rem; font-weight: 900; margin: 46px 0 4px;
    display: flex; align-items: center; gap: 10px; letter-spacing: -.01em;
  }
  h2 .count {
    font-size: .8rem; font-weight: 800; color: #1a0b22; background: var(--lime);
    padding: 3px 11px; border-radius: 999px; letter-spacing: .02em;
  }
  .hint { color: var(--dim); font-size: .94rem; margin: 0 0 22px; max-width: 62ch; }

  /* ---------- קלפי משחק ---------- */
  .grid {
    display: grid; gap: 16px;
    grid-template-columns: repeat(auto-fill, minmax(215px, 1fr));
  }
  .card {
    position: relative; overflow: hidden;
    display: grid; grid-template-columns: 62px 1fr; grid-template-rows: auto auto auto;
    gap: 2px 14px; align-items: center;
    padding: 16px; border-radius: 20px; text-decoration: none; color: inherit;
    background: linear-gradient(170deg, var(--panel-2), var(--panel));
    border: 2px solid var(--line);
    box-shadow: 0 6px 0 #00000038;
    transition: transform .14s ease, box-shadow .14s ease, border-color .14s ease;
  }
  .card::before {
    content: ""; position: absolute; inset: -40% -40% auto auto;
    width: 150px; height: 150px; border-radius: 50%;
    background: radial-gradient(circle, var(--c1), transparent 62%);
    opacity: .22; transition: opacity .2s;
  }
  .card:hover, .card:focus-visible {
    transform: translateY(-6px) rotate(-.6deg);
    border-color: var(--c1);
    box-shadow: 0 12px 0 #00000038, 0 16px 34px #0009;
    outline: none;
  }
  .card:hover::before { opacity: .45; }
  .card:active { transform: translateY(0) scale(.985); }
  .thumb {
    grid-row: 1 / 4; width: 62px; height: 62px; border-radius: 17px;
    display: grid; place-items: center; font-size: 1.85rem;
    background: linear-gradient(145deg, var(--c1), var(--c2));
    box-shadow: inset 0 -3px 0 #0003, 0 4px 14px #0006;
    transition: transform .22s cubic-bezier(.3,1.5,.5,1);
  }
  .card:hover .thumb { transform: scale(1.1) rotate(-8deg); }
  .name { font-weight: 800; font-size: 1.02rem; line-height: 1.2; }
  .sub { color: var(--dim); font-size: .78rem; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }
  .play {
    font-size: .74rem; font-weight: 900; letter-spacing: .1em; color: var(--c1);
    opacity: 0; transform: translateX(-6px); transition: opacity .15s, transform .15s;
  }
  .card:hover .play { opacity: 1; transform: none; }
  .empty {
    display: none; text-align: center; color: var(--dim);
    padding: 34px; border: 2px dashed var(--line); border-radius: 20px;
  }

  /* ---------- משחקים להורדה ---------- */
  details.native {
    background: #ffffff0a; border: 2px solid var(--line); border-radius: 20px;
    padding: 4px 18px; margin-top: 4px;
  }
  details.native summary {
    cursor: pointer; font-weight: 800; padding: 14px 2px; list-style: none;
  }
  details.native summary::-webkit-details-marker { display: none; }
  details.native summary::before { content: "\\25B8  "; color: var(--cyan); }
  details.native[open] summary::before { content: "\\25BE  "; }
  ul.native { list-style: none; padding: 0; margin: 0 0 14px; }
  ul.native li {
    display: grid; grid-template-columns: 1fr auto auto; gap: 14px;
    align-items: center; padding: 10px 2px; border-top: 1px solid var(--line);
    font-size: .93rem;
  }
  ul.native .n { font-weight: 700; }
  ul.native .e { color: var(--dim); font-size: .8rem; }
  ul.native a { color: var(--cyan); text-decoration: none; font-weight: 700; font-size: .85rem; }
  ul.native a:hover { text-decoration: underline; }

  footer { margin-top: 56px; text-align: center; color: var(--dim); font-size: .88rem; }

  @media (max-width: 520px) {
    .grid { grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { grid-template-columns: 1fr; grid-template-rows: auto auto auto auto; padding: 14px; }
    .thumb { grid-row: auto; margin-bottom: 6px; }
    ul.native li { grid-template-columns: 1fr auto; }
    ul.native .e { grid-column: 1; }
  }
  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
    html { scroll-behavior: auto; }
  }
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <span class="badge">@@n_total@@ games &middot; made with Python</span>
    <h1>Python Games</h1>
    <p class="lede"><b>@@n_play@@ games play right here in your browser.</b>
       Nothing to install &mdash; just pick one and go.</p>

    <div class="tools">
      <label class="search">
        <span aria-hidden="true">&#128269;</span>
        <input id="q" type="search" placeholder="Search a game&hellip;"
               autocomplete="off" aria-label="Search games">
      </label>
      <button id="lucky" type="button">&#127922; Surprise me!</button>
    </div>
  </header>

  <h2>&#127918; Play now <span class="count">@@n_play@@</span></h2>
  <p class="hint">Built with pygame and compiled to run in the browser. The first
     load takes a few seconds &mdash; the browser is downloading Python itself.</p>
  <div class="grid" id="grid">
@@cards@@  </div>
  <p class="empty" id="empty">&#129300; No game with that name. Try something else!</p>

  <h2>&#128187; Desktop only <span class="count">@@n_native@@</span></h2>
  <p class="hint">These use 3D engines and desktop toolkits that a browser cannot
     run. Download the code and start it with Python on your computer.</p>
  <details class="native">
    <summary>Show the @@n_native@@ desktop games</summary>
    <ul class="native">
@@rows@@    </ul>
  </details>

  <footer>Written in Python with pygame, ursina, Panda3D, tkinter and turtle. &#128013;</footer>
</div>

<script>
  var cards = Array.prototype.slice.call(document.querySelectorAll("#grid .card"));
  var q = document.getElementById("q");
  var empty = document.getElementById("empty");

  q.addEventListener("input", function () {
    var needle = q.value.trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var hit = !needle || c.dataset.name.indexOf(needle) !== -1;
      c.style.display = hit ? "" : "none";
      if (hit) { shown++; }
    });
    empty.style.display = shown ? "none" : "block";
  });

  var slugs = @@slugs@@;
  document.getElementById("lucky").addEventListener("click", function () {
    if (!slugs.length) { return; }
    location.href = slugs[Math.floor(Math.random() * slugs.length)] + "/";
  });
</script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
