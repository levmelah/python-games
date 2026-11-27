# -*- coding: utf-8 -*-
"""מעתיק את תוצאות הבנייה של כל משחק לתוך docs/ - התיקייה ש-GitHub Pages מגישה."""
import os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_back_button

ROOT = os.path.abspath(".")          # .../game
WEB = os.path.join(ROOT, "web")
DOCS = os.path.join(ROOT, "docs")

slugs = sorted(d for d in os.listdir(WEB)
               if os.path.isfile(os.path.join(WEB, d, "build", "web", "index.html")))

for slug in slugs:
    src = os.path.join(WEB, slug, "build", "web")
    dst = os.path.join(DOCS, slug)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

os.makedirs(DOCS, exist_ok=True)
# .nojekyll - אחרת GitHub Pages מתעלם מקבצים שמתחילים בקו תחתון
open(os.path.join(DOCS, ".nojekyll"), "w").close()
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "playable.txt"),
     "w", encoding="utf-8").write("\n".join(slugs) + "\n")

# דפי pygbag נוצרים בלי כפתור חזרה, ולכן מוסיפים אותו כאן בכל בנייה
add_back_button.main(DOCS)
print("הועתקו ל-docs/: %d משחקים" % len(slugs))
