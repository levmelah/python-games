#!/bin/sh
# בונה מחדש את גרסאות הדפדפן של כל המשחקים, מההתחלה ועד docs/.
# להריץ מתיקיית הפרויקט:   sh tools/rebuild.sh
# להריץ על משחק אחד:       sh tools/rebuild.sh bowling-2

set -e
cd "$(dirname "$0")/.."
ONLY="$1"

echo "--- 1/4  מעתיק את המשחקים ל-web/ והופך אותם ל-async"
python3 tools/stage.py ${ONLY:+"$ONLY"}

echo "--- 2/4  בונה ל-WebAssembly"
ONLY="$ONLY" sh tools/build_all.sh

echo "--- 3/4  מעתיק ל-docs/"
python3 tools/publish.py

echo "--- 4/4  כותב את דף הבית"
python3 tools/generate_site.py

cat <<'MSG'

--- מוכן.
בדיקה מקומית:
    cd docs && python3 -m http.server 8222
    ואז לפתוח  http://127.0.0.1:8222/     <-- 127.0.0.1, לא localhost!

העלאה ל-GitHub:
    git add -A && git commit -m "update games" && git push
MSG
