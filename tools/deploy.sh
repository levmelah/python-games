#!/bin/sh
# פקודה אחת: בונה מחדש את גרסאות הדפדפן, שומר ב-git ומעלה ל-GitHub Pages.
#
#   sh tools/deploy.sh                 # כל המשחקים
#   sh tools/deploy.sh bowling-2       # רק משחק אחד, הרבה יותר מהר
#   sh tools/deploy.sh bowling-2 "תיקון הניקוד"     # עם הודעת commit משלך
#
# האתר: https://levmelah.github.io/python-games/

set -e
cd "$(dirname "$0")/.."

ONLY="$1"
MSG="$2"
if [ -z "$MSG" ]; then
    if [ -n "$ONLY" ]; then MSG="update $ONLY"; else MSG="update games"; fi
fi

# --- 1  בנייה מחדש (stage -> pygbag -> docs -> index.html)
sh tools/rebuild.sh ${ONLY:+"$ONLY"}

# --- 2  שמירה ב-git
echo
echo "--- 5/6  שומר ב-git"
git add -A
if git diff --cached --quiet; then
    echo "אין שינויים לשמור."
else
    git commit -q -m "$MSG"
    echo "נשמר: $MSG"
fi

# --- 3  העלאה ל-GitHub
echo "--- 6/6  מעלה ל-GitHub"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push -u origin "$BRANCH"

cat <<'MSG2'

--- הועלה.
האתר מתעדכן תוך דקה-שתיים:
    https://levmelah.github.io/python-games/

אם הדף מראה גרסה ישנה - Ctrl+Shift+R (רענון בלי cache).
MSG2
