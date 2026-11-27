# -*- coding: utf-8 -*-
"""בונה את site/index.html - הדף הראשי של אוסף המשחקים."""
import csv, html, os, re, sys

S = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(".")
SITE = os.path.join(ROOT, "docs")

# אחרי שתיפתח החשבון ב-GitHub, צריך להחליף את הכתובת הזאת
REPO_URL = "https://github.com/levmelah-ship-it/python-games/blob/main"

ENGINE_NOTE = {
    "ursina": "ursina (3D)",
    "panda3d": "Panda3D (3D)",
    "tkinter": "tkinter",
    "turtle": "turtle",
    "qt": "PySide6",
}


def pretty(path):
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"[_\-]+", " ", name).strip()
    return name


def card(slug, title, subtitle):
    return (
        '      <a class="card" href="%s/">\n'
        '        <span class="thumb" aria-hidden="true">%s</span>\n'
        '        <span class="name">%s</span>\n'
        '        <span class="sub">%s</span>\n'
        '      </a>\n'
        % (html.escape(slug), html.escape(title[:1].upper() or "?"),
           html.escape(title), html.escape(subtitle))
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

    page = PAGE % {
        "n_play": len(playable),
        "n_native": len(native),
        "n_total": len(playable) + len(native),
        "cards": cards,
        "rows": rows,
    }
    os.makedirs(SITE, exist_ok=True)
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(page)
    print("docs/index.html: %d בדפדפן, %d להורדה" % (len(playable), len(native)))


PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Python Games</title>
<style>
  :root {
    --bg: #0f1117; --panel: #171a23; --line: #262b38;
    --text: #e8eaf0; --dim: #959cb0; --accent: #6ea8fe;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }
  .wrap { max-width: 1000px; margin: 0 auto; padding: 48px 16px 80px; }
  h1 { font-size: 2rem; margin: 0 0 8px; letter-spacing: -0.02em; }
  .lede { color: var(--dim); margin: 0 0 40px; max-width: 52ch; }
  h2 { font-size: 1.1rem; margin: 48px 0 6px; }
  h2 .count { color: var(--dim); font-weight: 400; }
  .hint { color: var(--dim); font-size: 0.9rem; margin: 0 0 20px; max-width: 60ch; }
  .grid {
    display: grid; gap: 12px;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  }
  .card {
    display: grid; grid-template-columns: 44px 1fr; grid-template-rows: auto auto;
    gap: 2px 12px; align-items: center;
    padding: 14px; background: var(--panel); border: 1px solid var(--line);
    border-radius: 10px; text-decoration: none; color: inherit;
  }
  .card:hover { border-color: var(--accent); }
  .thumb {
    grid-row: 1 / 3; width: 44px; height: 44px; border-radius: 8px;
    display: grid; place-items: center; font-size: 1.1rem; font-weight: 600;
    background: #22283a; color: var(--accent);
  }
  .name { font-weight: 600; font-size: 0.95rem; }
  .sub { color: var(--dim); font-size: 0.8rem; }
  ul.native { list-style: none; padding: 0; margin: 0;
    border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
  ul.native li {
    display: grid; grid-template-columns: 1fr auto auto; gap: 16px;
    align-items: center; padding: 10px 14px; background: var(--panel);
    border-top: 1px solid var(--line); font-size: 0.92rem;
  }
  ul.native li:first-child { border-top: 0; }
  ul.native .e { color: var(--dim); font-size: 0.82rem; }
  ul.native a { color: var(--accent); text-decoration: none; font-size: 0.85rem; }
  ul.native a:hover { text-decoration: underline; }
  footer { margin-top: 56px; color: var(--dim); font-size: 0.85rem; }
  @media (max-width: 520px) {
    ul.native li { grid-template-columns: 1fr auto; }
    ul.native .e { grid-column: 1; }
  }
</style>
</head>
<body>
<div class="wrap">
  <h1>Python Games</h1>
  <p class="lede">%(n_total)d games written in Python. %(n_play)d of them run
     right here in the browser &mdash; no install needed.</p>

  <h2>Play in the browser <span class="count">&middot; %(n_play)d</span></h2>
  <p class="hint">Built with pygame and compiled to WebAssembly. The first load
     takes a moment: the browser downloads Python itself.</p>
  <div class="grid">
%(cards)s  </div>

  <h2>Desktop only <span class="count">&middot; %(n_native)d</span></h2>
  <p class="hint">These use 3D engines and desktop toolkits that cannot run in a
     browser. Download the source and run it with Python.</p>
  <ul class="native">
%(rows)s  </ul>

  <footer>Written in Python with pygame, ursina, Panda3D, tkinter and turtle.</footer>
</div>
</body>
</html>
'''

if __name__ == "__main__":
    main()
