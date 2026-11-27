#!/bin/sh
# בונה את כל המשחקים ל-WebAssembly (pygbag). יש להריץ מתיקיית הפרויקט.
# ברירת המחדל היא הפייתון של .venv-bpy, שבו מותקן pygbag.
# אפשר לבחור אחר:  PYTHON=/usr/bin/python3 sh tools/build_all.sh

if [ -z "$PYTHON" ]; then
    if [ -x ".venv-bpy/bin/python" ]; then
        PYTHON="$PWD/.venv-bpy/bin/python"
    else
        PYTHON="python3"
    fi
fi
case "$PYTHON" in
    /*) ;;                       # נתיב מלא - בסדר
    */*) PYTHON="$PWD/$PYTHON" ;;  # נתיב יחסי - נהפוך למלא, כי נעבור תיקייה
esac

"$PYTHON" -c 'import pygbag' 2>/dev/null || {
    echo "pygbag לא מותקן ב-$PYTHON   ->   $PYTHON -m pip install pygbag"
    exit 1
}

cd web || { echo "אין תיקיית web/ - קודם python3 tools/stage.py"; exit 1; }
fails=0
for d in */; do
    slug="${d%/}"
    [ -f "$slug/main.py" ] || continue
    [ -z "$ONLY" ] || [ "$ONLY" = "$slug" ] || continue
    printf '%-32s' "$slug"
    if "$PYTHON" -m pygbag --build --ume_block 0 "$slug" >/dev/null 2>&1 \
       && [ -f "$slug/build/web/index.html" ]; then
        rm -f "$slug/build/web/"*.apk   # נחוץ רק ל-itch.io, ומכפיל את הגודל
        echo "ok"
    else
        echo "FAILED"
        fails=$((fails + 1))
    fi
done
echo "נכשלו: $fails"
