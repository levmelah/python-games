# -*- coding: utf-8 -*-
"""בונה את התיקייה web/: לכל משחק תיקייה משלו עם main.py והקבצים שלו."""
import csv, os, shutil, sys, subprocess

ROOT = os.path.abspath(".")
WEB = os.path.join(ROOT, "web")
S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S)
import convert as C

VENDOR = os.path.join(S, "vendor")


def copy_vendor(dest):
    """מעתיק לתוך המשחק את החבילות שאנחנו אורזים (bidi + six)."""
    for name in ("bidi", "six.py"):
        src = os.path.join(VENDOR, name)
        dst = os.path.join(dest, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst,
                            ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(src, dst)

rows = list(csv.reader(open(os.path.join(S, "manifest.tsv"), encoding="utf-8"),
                       delimiter="\t"))
# ארגומנט אחד = רק המשחק הזה
if len(sys.argv) > 1:
    wanted = sys.argv[1]
    rows = [r for r in rows if r[1] == wanted]
    if not rows:
        sys.exit("אין משחק בשם %r ב-manifest.tsv" % wanted)
ok, bad = [], []
for src, slug, title, assets in rows:
    dest = os.path.join(WEB, slug)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    try:
        vendored = C.convert(os.path.join(ROOT, src),
                             os.path.join(dest, "main.py"))
    except Exception as e:
        bad.append((slug, "%s: %s" % (type(e).__name__, e)))
        continue
    if vendored:
        copy_vendor(dest)
    for spec in filter(None, assets.split(";")):
        a_src, a_dst = spec.split(">")
        s_path = os.path.join(ROOT, a_src)
        d_path = os.path.join(dest, a_dst)
        if not os.path.exists(s_path):
            bad.append((slug, "חסר קובץ: " + a_src))
            continue
        os.makedirs(os.path.dirname(d_path), exist_ok=True)
        if os.path.isdir(s_path):
            shutil.copytree(s_path, d_path)
        else:
            shutil.copy2(s_path, d_path)
    ok.append(slug)

print("הוכנו: %d" % len(ok))
for slug, why in bad:
    print("בעיה | %s | %s" % (slug, why))
