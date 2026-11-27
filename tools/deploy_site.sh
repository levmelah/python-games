#!/bin/sh
# מעלה רק את העיצוב של דף הבית - בלי לבנות מחדש את המשחקים.
# מהיר (שניות), כי pygbag לא רץ בכלל.
#
#   sh tools/deploy_site.sh                      # הודעת commit ברירת מחדל
#   sh tools/deploy_site.sh "כרטיסים גדולים"      # עם הודעה משלך
#
# את העיצוב עורכים בתוך PAGE שב-tools/generate_site.py,
# ולא ב-docs/index.html - הקובץ הזה נוצר מחדש ונדרס בכל פעם.

set -e
cd "$(dirname "$0")/.."

MSG="$1"
[ -n "$MSG" ] || MSG="update site layout"

echo "--- 1/3  כותב מחדש את דף הבית"
python3 tools/generate_site.py

echo "--- 2/3  שומר ב-git"
git add -A
if git diff --cached --quiet; then
    echo "אין שינויים - אולי לא נשמר העריכה ב-tools/generate_site.py?"
    exit 0
fi
git commit -q -m "$MSG"
echo "נשמר: $MSG"

echo "--- 3/3  מעלה ל-GitHub"
git push origin "$(git rev-parse --abbrev-ref HEAD)"

cat <<'MSG2'

--- הועלה.
    https://levmelah.github.io/python-games/
Ctrl+Shift+R אם רואים גרסה ישנה.
MSG2
