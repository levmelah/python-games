# -*- coding: utf-8 -*-
"""מוסיף לכל דף משחק ב-docs/ כפתור חזרה לרשימת המשחקים.

דפי המשחק נוצרים על ידי pygbag, ולכן אין בהם כפתור כזה. publish.py מריץ
את הסקריפט הזה אחרי ההעתקה ל-docs/, כך שהכפתור חוזר בכל בנייה מחדש.
ניתן להריץ גם לבד:  python3 tools/add_back_button.py
"""
import os, re, sys

MARK = "back-to-games"

SNIPPET = """
<!-- back-to-games: added by tools/add_back_button.py -->
<style>
  a#back-to-games {
    position: fixed; top: 10px; left: 10px; z-index: 2147483647;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 7px 13px 7px 11px; border-radius: 9px;
    background: #171a23eb; border: 1px solid #262b38; color: #e8eaf0;
    font: 600 14px/1 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    text-decoration: none; opacity: .72; transition: opacity .15s, border-color .15s;
  }
  a#back-to-games:hover { opacity: 1; border-color: #6ea8fe; color: #6ea8fe; }
</style>
<a id="back-to-games" href="../" title="Back to the games list">&#8592; All games</a>
"""


def add(path):
    with open(path, encoding="utf-8") as f:
        page = f.read()
    if MARK in page:
        return False
    if "</body>" not in page:
        print("אין </body> ב-%s" % path)
        return False
    page = re.sub(r"</body>", SNIPPET + "</body>", page, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return True


def main(docs=None):
    docs = docs or os.path.join(os.path.abspath("."), "docs")
    done = 0
    for slug in sorted(os.listdir(docs)):
        page = os.path.join(docs, slug, "index.html")
        if os.path.isfile(page) and add(page):
            done += 1
    print("כפתור חזרה נוסף ל-%d דפי משחק" % done)
    return done


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
