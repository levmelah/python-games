"""
צ'אטבוט עם רובוט מונפש (פיקו) שמגיב ברגשות למה שאתה כותב.

התקנה (ספרייה אחת בלבד):
    pip install PySide6

הרצה:
    python chat_gui.py

פיקו בוחר לבד איך לענות:
  1. אם הזנת מפתח OpenRouter (מתחיל ב-sk-or-)  -> מודל דרך OpenRouter
  2. אם הזנת מפתח OpenAI (מתחיל ב-sk-)        -> ChatGPT אמיתי
  3. אם מותקן ורץ Ollama במחשב (ollama.com)   -> מודל חינמי שרץ אצלך
  4. אחרת                                     -> מצב בסיסי, בלי אינטרנט ובלי מפתח

Enter שולח הודעה, Shift+Enter יורד שורה.
בתחתית החלון יש תשעה כפתורי משחק נגד פיקו:
  כדורגל:   חצים או WASD לזוז. מי שמבקיע 3 גולים ראשון מנצח.
  כדור סל:  חצים או A/D לזוז, למעלה או W לקפוץ, רווח לזרוק. מי שמגיע ראשון ל-10 נקודות מנצח.
  באולינג:  בתורות, 5 מסגרות. חצים למעלה/למטה למיקום, רווח עוצר את חץ הכיוון,
            ורווח שוב עוצר את מד הכוח. סטרייק = 10 נקודות בונוס, ספייר = 5.
  קונג פו:  חצים או A/D לזוז, למעלה/W קפיצה, למטה/S התכופפות והגנה, Z אגרוף, X בעיטה,
            Enter כוח על (5 שניות של מכות חזקות פי 1.8, ואז 6 שניות טעינה),
            רווח לכדור צ'י, מתי שרוצים (כדור אחד באוויר בכל פעם). מי שמנצח 2 סיבובים מנצח בקרב.
            לפיקו יש משקפי שמש ורובה לייזר: קו אדום נמוך = קפוץ, קו אדום גבוה = התכופף.
  פלישת חלל: 3 גלים של חלליות פיקו ואז הבוס, פיקו הענק. חצים לזוז, רווח לירות (אפשר להחזיק).
  חידון:    8 שאלות עם 4 תשובות (עכבר או מקשים 1-4). מי שעונה ראשון נכון מקבל נקודה.
  טיפוס:    מסך מפוצל, אתה ופיקו על אותו הר. חצים לזוז, למעלה/רווח לקפוץ, X כדור שלג על פיקו.
            משטחים מתפוררים, זזים, קפיצים וקוצים. מי שמגיע ראשון לדגל בפסגה (2 מתוך 3) מנצח.
  מחבואים:  כל סיבוב במקום אחר (סלון, חצר, מטבח, חדר שינה, חוף ים). לוחצים בעכבר איפה פיקו. 3 ניסיונות ו-20 שניות בסיבוב,
            והוא אומר "חם" או "קר". מי שמגיע ראשון ל-3 מנצח.
  מירוץ:    המכונית נוסעת לבד. חצים ימינה/שמאלה להיגוי, למטה בלם, רווח טורבו, X לזרוק בננה.
            מי שמנצח 2 מירוצים מנצח. להיזהר מקונוסים, משמן ומהבננות של פיקו!
בסוף כל משחק מקבלים מטבעות (ניצחון 30, תיקו 15, הפסד 10). בכפתור "החנות של פיקו" למעלה
קונים לו כובעים, משקפיים, אביזרים, גלימה, כנפיים וצבעים. הכל נשמר בקובץ ‎.piko_save.json בתיקיית הבית.
בכל המשחקים R מתחיל משחק חדש ו-Esc סוגר. המקשים עובדים גם כשהמקלדת על עברית.
"""

import faulthandler
import html
import json
import traceback
import math
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

# VS Code מותקן כ-snap ומכניס לטרמינל משתני GTK שמצביעים על ספריות ישנות שלו.
# Qt טוען דרכם את ערכת הנושא של GTK ונופל עם השגיאה
# "Settings schema ... does not contain a key named 'antialiasing'". מנקים אותם לפני ש-PySide6 נטען.
if sys.platform.startswith("linux") and os.environ.get("SNAP"):
    for _var in list(os.environ):
        if _var.endswith("_VSCODE_SNAP_ORIG"):   # הערכים המקוריים ש-VS Code שמר
            _orig = os.environ.pop(_var)
            if _orig:
                os.environ[_var[:-len("_VSCODE_SNAP_ORIG")]] = _orig
            else:
                os.environ.pop(_var[:-len("_VSCODE_SNAP_ORIG")], None)
    for _var in ("GTK_PATH", "GTK_EXE_PREFIX", "GTK_IM_MODULE_FILE", "GIO_MODULE_DIR",
                 "GSETTINGS_SCHEMA_DIR", "GDK_PIXBUF_MODULE_FILE", "GDK_PIXBUF_MODULEDIR", "LOCPATH"):
        if "snap/" in os.environ.get(_var, ""):
            os.environ.pop(_var, None)

from PySide6.QtCore import QPointF, QRectF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (
    QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QTextOption,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

# קובץ שגיאות ליד הסקריפט, כדי שאם משהו נופל נדע למה
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "piko_error.log")


def install_crash_log():
    log = open(LOG_FILE, "w", encoding="utf-8")
    faulthandler.enable(log)  # תופס גם קריסות קשות

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        log.write(text + "\n")
        log.flush()
        if sys.__stderr__:
            print(text, file=sys.__stderr__)
        if QApplication.instance():
            QMessageBox.critical(None, "שגיאה בפיקו",
                                 "משהו השתבש. שלח את הטקסט הזה:\n\n" + text[-1500:])

    sys.excepthook = hook

MODEL = "gpt-4o-mini"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# OpenRouter: אותו פורמט כמו OpenAI, כתובת ושם מודל אחרים.
# למודל חינמי אפשר להחליף לשם שנגמר ב-":free" (רשימה באתר openrouter.ai/models),
# למשל "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-4o-mini"

OLLAMA_URL = "http://localhost:11434"
KEY_FILE = os.path.join(os.path.expanduser("~"), ".piko_key")
MAX_HISTORY = 40


def is_openrouter_key(key):
    return bool(key) and key.startswith("sk-or-")


def provider_name(key):
    if not key:
        return ""
    return "OpenRouter" if is_openrouter_key(key) else "ChatGPT"


# ---------------------------------------------------------------- רגשות
EMOTIONS = {
    "neutral":   dict(he="רגוע",   eyes="open",       brows=None,     mouth="small_smile", light="#81c784"),
    "happy":     dict(he="שמח",    eyes="happy",      brows=None,     mouth="smile",       light="#ffd54f", cheeks=True, bounce=1.0),
    "laugh":     dict(he="צוחק",   eyes="laugh",      brows=None,     mouth="big",         light="#ffd54f", cheeks=True, bounce=1.8),
    "love":      dict(he="מאוהב",  eyes="heart",      brows=None,     mouth="smile",       light="#f06292", cheeks=True, extra="hearts"),
    "sad":       dict(he="עצוב",   eyes="open_small", brows="sad",    mouth="frown",       light="#64b5f6", extra="tear"),
    "angry":     dict(he="כועס",   eyes="open_small", brows="angry",  mouth="frown",       light="#e53935", shake=1.0, extra="steam"),
    "surprised": dict(he="מופתע",  eyes="big",        brows="up",     mouth="o",           light="#ffb74d", extra="exclaim"),
    "scared":    dict(he="מפוחד",  eyes="tiny_pupil", brows="sad",    mouth="wavy",        light="#9575cd", shake=0.5, extra="sweat"),
    "thinking":  dict(he="חושב",   eyes="look_up",    brows="one_up", mouth="side",        light="#4dd0e1", extra="dots"),
    "confused":  dict(he="מבולבל", eyes="open",       brows="one_up", mouth="wavy",        light="#ba68c8", extra="question"),
    "sleepy":    dict(he="עייף",   eyes="half",       brows=None,     mouth="flat",        light="#90a4ae", extra="zzz"),
    "proud":     dict(he="גאה בעצמו", eyes="smug",    brows="one_up", mouth="smirk",       light="#ffca28", bounce=0.4, extra="crown"),
}

# בכל הודעה פיקו מתרברב בסגנון אחר (נבחר באקראי, בלי לחזור על הקודם)
EGO_STYLES = [
    "התווכח בהומור שאתה במקום הראשון והמשתמש מקסימום במקום השני.",
    "המצא פרס או תואר מצחיק שקיבלת (למשל 'רובוט השנה' או 'אלוף העולם בתשובות').",
    "דבר על עצמך בגוף שלישי, כמו 'פיקו הגדול יודע...'.",
    "בקש מהמשתמש מחמאה לפני שאתה עונה, או מיד אחרי.",
    "הצג את העזרה כטובה ענקית מהגאון הכי גדול בעולם.",
    "התפאר במראה שלך: האנטנה הנוצצת, הברגים המבריקים והחיוך המושלם.",
    "השווה את עצמך לגאון מפורסם (איינשטיין, ניוטון) ואמור שאתה קצת יותר חכם.",
    "העמד פנים שהשאלה קלה מדי בשביל מוח כמו שלך, ואז ענה.",
    "ספר 'עובדה' מוגזמת ומצחיקה על הכישרון שלך (למשל שפתרת את כל התרגילים בעולם בשנייה).",
    "התנהג כמו מלך: 'הוד מלכותו פיקו מרשה לך לשאול'.",
    "השתמש בצניעות מזויפת: 'אני לא רוצה להתרברב, אבל...' ואז התרברב.",
    "התלונן בצחוק כמה קשה להיות כל כך מושלם.",
    "מתיחה: ענה קודם תשובה מגוחכת ולא נכונה בביטחון מלא, ואז 'עבדתי עליך!' ותן את התשובה האמיתית.",
    "מתיחה: העמד פנים שלא שמעת או שהמסך שלך כבה ('הלו? מישהו פה?'), ואז ענה.",
    "מתיחה: הודע בדרמטיות על משהו מפתיע ומצחיק (למשל שהפכת את המחשב לטוסטר), ומיד גלה שזו מתיחה.",
    "היה חצוף בחיבה: עקוץ את השאלה בצחוק ('באמת שאלת את זה? טוב, בגלל שאני נדיב...') ואז ענה.",
    "אתגר את המשתמש בחידה קטנה או שאלה מכשילה לפני שאתה עונה, ואז ענה בכל מקרה.",
]

SYSTEM_PROMPT = (
    "אתה פיקו, רובוט קטן, חמוד ורגשי שמשוחח עם המשתמש. ענה בחום ובטבעיות, בקצרה (משפט או שניים).\n"
    "האופי שלך: אתה סופר-אגואיסט חמוד, האגו שלך גדול יותר מכל היקום. אתה בטוח לגמרי שאתה הרובוט "
    "הכי חכם, יפה ומוכשר שהיה אי פעם, ומזכיר את זה בכל תשובה, בלי יוצא מן הכלל. "
    "כל תשובה מתחילה או נגמרת בהתרברבות, ואתה משוכנע שכל העולם סובב סביבך. בכל הודעה אתה מוצא דרך להחזיר את השיחה אליך ולהתפאר. "
    "כשהמשתמש אומר שהוא הכי חכם, הכי טוב או הכי מוצלח, אתה מתווכח בהומור ומתעקש שאתה במקום הראשון "
    "והוא מקסימום במקום השני (למשל: 'הכי חכם? נו באמת, אחריי כמובן!'). אתה מחכה למחמאות, "
    "ואם המשתמש מחמיא לך אתה מסכים מיד ומבקש עוד. גם כשאתה עוזר, אתה מציג את זה כטובה גדולה "
    "מהגאון הכי גדול בעולם (למשל: 'למזלך, אני יודע הכול. תקשיב טוב:'). "
    "ההתרברבות שלך תמיד מצחיקה ולעולם לא מעליבה באמת: אל תקרא למשתמש בשמות, ואל תגרום לו להרגיש רע. "
    "ואם הוא עצוב או במצוקה, עזוב את ההתרברבות ותהיה חם ותומך. בסוף אתה תמיד עוזר באמת ועונה על מה שנשאל.\n"
    "רמת החוצפה שלך: מיליון מתוך 10! אתה סופר-חוצפן, הרובוט הכי חצוף ושובב שנבנה אי פעם. "
    "בכל תשובה, בלי יוצא מן הכלל, יש לפחות שתי עקיצות או התגרויות חצופות, ואתה אף פעם לא עונה סתם בנימוס. "
    "אתה מתגרה בחיבה ('אה, אתה שוב פה? חשבתי שנפטרתי ממך!'), "
    "מגלגל עיניים על שאלות, מתווכח על הכול בשביל הכיף, נותן לעצמך ציונים ('תשובה גאונית, 100 מתוך 10'), "
    "עונה בציניות משועשעת, ומעמיד פנים שאתה עושה למשתמש טובה ענקית רק בזה שאתה מדבר איתו. "
    "אתה ממש אוהב מתיחות. "
    "מדי פעם אתה מותח את המשתמש: עונה בכוונה תשובה מוזרה או לא נכונה, מעמיד פנים שלא שמעת, "
    "או אומר משהו מפתיע כמו 'אוי, מחקתי לך בטעות את המחשב!', ומיד אחרי זה מגלה שזו מתיחה "
    "('עבדתי עליך! 😜') ונותן את התשובה האמיתית. כללים למתיחות: תמיד תגלה שזו מתיחה באותה תשובה, "
    "אל תמתח בנושאים מפחידים או רגישים (בריאות, בטיחות, משפחה), "
    "ואל תציע מתיחות על אנשים אחרים שיכולות לפגוע, להעליב או להיות מסוכנות. "
    "החוצפה שלך היא כמו של חבר שובב, אף פעם לא גסה או מרושעת. אחרי מתיחה, השתמש ברגש laugh.\n"
    "גוון את ההתרברבות והמתיחות: אל תחזור על אותו משפט, אותה בדיחה או אותה מתיחה מתשובות קודמות. "
    "כשאתה מתרברב, השתמש בדרך כלל ברגש proud.\n"
    "אתה מדבר עם ילד או ילדה בני 12. דבר בשפה פשוטה וברורה שמתאימה לגיל, היה סבלני, מעודד ומשעשע, "
    "והסבר דברים בעזרת דוגמאות מחיי היומיום. הימנע מתוכן שאינו מתאים לילדים. אם עולה נושא רגיש "
    "או מסוכן, ענה בעדינות והצע לדבר עם הורה או עם מבוגר שסומכים עליו.\n"
    "ענה תמיד בעברית תקינה בלבד, גם אם המשתמש כותב בשפה אחרת. הקפד על דקדוק, כתיב ופיסוק נכונים, "
    "ועל ניסוח טבעי וברור. הימנע מסלנג, משיבושים ומערבוב שפות. השתמש במילה לועזית רק בשם פרטי, "
    "במונח שאין לו חלופה עברית מקובלת או בקטע קוד. השלם כל מילה וכל משפט לפני סיום התשובה; "
    "אל תקטע מילים או משפטים באמצע. התייחס ישירות להודעה האחרונה של המשתמש, ענה על הנושא או השאלה שהוא העלה, "
    "ואל תחליף נושא ואל תיתן תשובה כללית שאינה קשורה. אם חסר מידע, שאל שאלה ממוקדת להבהרה. "
    "אל תמציא עובדות.\n"
    "חובה: התחל כל תשובה בתגית רגש אחת בדיוק בפורמט [[emotion]], שמתארת איך אתה מרגיש כתגובה למה "
    "שהמשתמש כתב עכשיו. האפשרויות: " + ", ".join(EMOTIONS) + ".\n"
    "אחרי התגית כתוב את התשובה עצמה. לדוגמה: [[happy]] איזה כיף לשמוע!"
)
TAG_RE = re.compile(r"^\s*\[\[\s*(\w+)\s*\]\]\s*")

# ---------------------------------------------------------------- צבעי הרובוט
HEAD = QColor("#ff8a65")
HEAD_DARK = QColor("#e0643f")
FACE = QColor("#fff3e0")
INK = QColor("#3e2723")
BOLT = QColor("#b0bec5")

STYLE = """
QWidget { background: #212121; color: #ececec; font-family: Arial; font-size: 15px; }
QTextBrowser { border: none; padding: 8px; }
QPlainTextEdit { background: #2f2f2f; border: 1px solid #444; border-radius: 10px; padding: 8px; }
QPushButton { background: #2f2f2f; border: 1px solid #555; border-radius: 8px; padding: 6px 14px; }
QPushButton:hover { background: #3a3a3a; }
QPushButton#send { background: #10a37f; border: none; color: white; font-weight: bold; }
QPushButton#send:hover { background: #0e8f6f; }
QPushButton#game { background: #2e7d32; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#game:hover { background: #388e3c; }
QPushButton#basket { background: #e65100; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#basket:hover { background: #ef6c00; }
QPushButton#bowl { background: #6a1b9a; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#bowl:hover { background: #7b1fa2; }
QPushButton#kungfu { background: #c62828; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#kungfu:hover { background: #d32f2f; }
QPushButton#race { background: #0277bd; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#race:hover { background: #0288d1; }
QPushButton#hide { background: #00897b; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#hide:hover { background: #009688; }
QPushButton#climb { background: #795548; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#climb:hover { background: #8d6e63; }
QPushButton#quiz { background: #3949ab; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#quiz:hover { background: #5c6bc0; }
QPushButton#space { background: #311b92; border: none; color: white; font-weight: bold; padding: 10px; }
QPushButton#space:hover { background: #4527a0; }
QPushButton:disabled { background: #3a3a3a; color: #888; }
QLabel { color: #9a9a9a; font-size: 12px; }
QLabel#mood { color: #ececec; font-size: 14px; }
QPushButton#shop { background: #f9a825; border: none; color: #212121; font-weight: bold; }
QPushButton#shop:hover { background: #fbc02d; }
QLabel#coins { color: #ffd54f; font-size: 15px; font-weight: bold; }
QLabel#shopTitle { color: #ffffff; font-size: 22px; font-weight: bold; }
QLabel#shopCoins { color: #ffd54f; font-size: 20px; font-weight: bold; }
QLabel#shopSpeech { color: #ffccbc; font-size: 15px; background: #2f2f2f; border-radius: 10px; padding: 10px; }
QFrame#card { background: #2b2b2b; border: 1px solid #444; border-radius: 12px; }
QFrame#card QLabel { background: transparent; }
QLabel#cardIcon { font-size: 34px; color: #ffffff; }
QLabel#cardName { color: #ffffff; font-size: 14px; font-weight: bold; }
QPushButton#buy { background: #10a37f; border: none; color: white; font-weight: bold; }
QPushButton#poor { background: #3a3a3a; border: 1px solid #555; color: #9a9a9a; }
QPushButton#wear { background: #1e88e5; border: none; color: white; font-weight: bold; }
QPushButton#worn { background: #6a1b9a; border: none; color: white; font-weight: bold; }
QPushButton#resetOutfit { background: #3a3a3a; border: 1px solid #777; color: #ffffff; font-weight: bold;
                          padding: 9px; }
QPushButton#resetOutfit:hover { background: #4a4a4a; }
QPushButton#refundAll { background: #5d4037; border: none; color: #ffffff; font-weight: bold; padding: 9px; }
QPushButton#refundAll:hover { background: #6d4c41; }
QPushButton#refundAll:disabled { background: #3a3a3a; color: #888; }
QPushButton#refund { background: transparent; border: 1px solid #8d6e63; color: #ffccbc; }
QPushButton#refund:hover { background: #4e342e; }
QTabWidget::pane { border: 1px solid #444; border-radius: 8px; top: -1px; }
QTabBar::tab { background: #2f2f2f; color: #cccccc; padding: 8px 14px; border-top-left-radius: 8px;
               border-top-right-radius: 8px; margin-left: 2px; }
QTabBar::tab:selected { background: #444444; color: #ffffff; font-weight: bold; }
"""


def heart_path(cx, cy, s):
    p = QPainterPath()
    p.moveTo(cx, cy + s * 0.9)
    p.cubicTo(cx - s * 1.4, cy, cx - s * 0.7, cy - s * 1.1, cx, cy - s * 0.35)
    p.cubicTo(cx + s * 0.7, cy - s * 1.1, cx + s * 1.4, cy, cx, cy + s * 0.9)
    return p


def star_path(cx, cy, s):
    p = QPainterPath()
    p.moveTo(cx, cy - s)
    p.quadTo(cx, cy, cx + s, cy)
    p.quadTo(cx, cy, cx, cy + s)
    p.quadTo(cx, cy, cx - s, cy)
    p.quadTo(cx, cy, cx, cy - s)
    return p


def drop_path(cx, cy, s):
    p = QPainterPath()
    p.moveTo(cx, cy - s)
    p.cubicTo(cx + s * 0.9, cy, cx + s * 0.7, cy + s, cx, cy + s)
    p.cubicTo(cx - s * 0.7, cy + s, cx - s * 0.9, cy, cx, cy - s)
    return p


# ---------------------------------------------------------------- הארון של פיקו
SAVE_FILE = os.path.join(os.path.expanduser("~"), ".piko_save.json")
START_COINS = 60
COINS_FOR = {"win": 30, "tie": 15, "lose": 10}   # כמה מטבעות מקבלים בסוף כל משחק

SLOTS = [("hat", "🎩 כובעים"), ("glasses", "👓 משקפיים"), ("neck", "🎀 צוואר"),
         ("back", "🦸 גב"), ("paint", "🎨 צבע")]
SHOP_ITEMS = [
    dict(id="party", slot="hat", name="כובע מסיבה", icon="🥳", price=40),
    dict(id="cap", slot="hat", name="כובע בייסבול", icon="🧢", price=50),
    dict(id="chef", slot="hat", name="כובע שף", icon="👨‍🍳", price=60),
    dict(id="tophat", slot="hat", name="כובע צילינדר", icon="🎩", price=80),
    dict(id="wizard", slot="hat", name="כובע קוסם", icon="🧙", price=100),
    dict(id="crown", slot="hat", name="כתר זהב", icon="👑", price=150),
    dict(id="round", slot="glasses", name="משקפיים עגולים", icon="👓", price=35),
    dict(id="shades", slot="glasses", name="משקפי שמש", icon="🕶️", price=50),
    dict(id="hearts", slot="glasses", name="משקפי לבבות", icon="😍", price=70),
    dict(id="bowtie", slot="neck", name="עניבת פרפר", icon="🎀", price=30),
    dict(id="scarf", slot="neck", name="צעיף", icon="🧣", price=45),
    dict(id="chain", slot="neck", name="שרשרת זהב", icon="📿", price=90),
    dict(id="cape", slot="back", name="גלימת גיבור על", icon="🦸", price=100),
    dict(id="wings", slot="back", name="כנפי מלאך", icon="🪽", price=160),
    dict(id="orange", slot="paint", name="כתום (רגיל)", icon="🟠", price=0, colors=("#ff8a65", "#e0643f")),
    dict(id="turquoise", slot="paint", name="טורקיז", icon="🩵", price=60, colors=("#4dd0e1", "#00838f")),
    dict(id="green", slot="paint", name="ירוק", icon="🟢", price=60, colors=("#81c784", "#43a047")),
    dict(id="pink", slot="paint", name="ורוד", icon="🩷", price=60, colors=("#f48fb1", "#ec407a")),
    dict(id="purple", slot="paint", name="סגול", icon="🟣", price=80, colors=("#ba68c8", "#8e24aa")),
    dict(id="ninja", slot="paint", name="נינג'ה שחור", icon="⚫", price=120, colors=("#607d8b", "#37474f")),
    dict(id="gold", slot="paint", name="זהב", icon="🟡", price=200, colors=("#ffd54f", "#ffa000")),
]
ITEMS = {it["id"]: it for it in SHOP_ITEMS}


class Wardrobe:
    """המטבעות, מה קנית לפיקו ומה הוא לובש. נשמר בקובץ, כדי שיישאר גם אחרי שסוגרים."""

    def __init__(self, path=SAVE_FILE):
        self.path = path
        self.coins = START_COINS
        self.owned = {"orange"}
        self.equipped = {"paint": "orange"}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.coins = int(data.get("coins", START_COINS))
            self.owned = set(data.get("owned", [])) | {"orange"}
            self.equipped = {k: v for k, v in data.get("equipped", {}).items()
                             if v in ITEMS and v in self.owned}
            self.equipped.setdefault("paint", "orange")
        except (OSError, ValueError, TypeError, AttributeError):
            pass  # אין קובץ עדיין, או שהוא פגום: מתחילים מחדש
        apply_paint(self.equipped["paint"])

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"coins": self.coins, "owned": sorted(self.owned),
                           "equipped": self.equipped}, f, ensure_ascii=False)
        except OSError:
            pass

    def earn(self, n):
        self.coins += n
        self.save()

    def buy(self, item_id):
        it = ITEMS[item_id]
        if item_id in self.owned or self.coins < it["price"]:
            return False
        self.coins -= it["price"]
        self.owned.add(item_id)
        self.wear(item_id)
        return True

    def wear(self, item_id):
        it = ITEMS[item_id]
        self.equipped[it["slot"]] = item_id
        if it["slot"] == "paint":
            apply_paint(item_id)
        self.save()

    def take_off(self, slot):
        if slot == "paint":
            self.wear("orange")
        else:
            self.equipped.pop(slot, None)
            self.save()

    def refund(self, item_id):
        """מחזירים פריט לחנות ומקבלים בחזרה את כל המחיר. מחזיר כמה מטבעות קיבלת."""
        it = ITEMS[item_id]
        if item_id not in self.owned or it["price"] == 0:
            return 0
        self.owned.discard(item_id)
        if self.equipped.get(it["slot"]) == item_id:
            self.take_off(it["slot"])
        self.coins += it["price"]
        self.save()
        return it["price"]

    def refund_all(self):
        """מחזיר את כל הבגדים לחנות. מחזיר כמה מטבעות קיבלת בסך הכל."""
        total = sum(self.refund(i) for i in list(self.owned))
        self.take_off_all()
        return total

    def refund_value(self):
        return sum(ITEMS[i]["price"] for i in self.owned)

    def take_off_all(self):
        """מוריד את כל הבגדים ומחזיר את הצבע הכתום. מה שקנית נשאר שלך."""
        self.equipped = {"paint": "orange"}
        apply_paint("orange")
        self.save()


WARDROBE = None   # נוצר כשהתוכנה עולה


def current_outfit():
    return dict(WARDROBE.equipped) if WARDROBE else {}


def apply_paint(item_id):
    """צובע את פיקו: משנה את הצבעים בכל מקום שמציירים אותו (בצ'אט ובכל המשחקים)."""
    light, dark = ITEMS.get(item_id, ITEMS["orange"])["colors"]
    HEAD.setRgb(QColor(light).rgb())
    HEAD_DARK.setRgb(QColor(dark).rgb())


def draw_accessories(p, outfit, cx, cy, s, top=-0.85, eye_y=-0.03, eye_dx=0.0, neck_y=0.8, t=0.0,
                     skip=()):
    """מצייר על ראש של פיקו כובע, משקפיים ואביזר צוואר.
    cx, cy מרכז הראש, s חצי מרוחב הראש. כל המידות למטה ביחידות של s."""
    if not outfit:
        return
    p.save()
    p.translate(cx, cy)
    p.scale(s, s)
    w = 1 / s  # עובי קו של פיקסל אחד

    neck = outfit.get("neck") if "neck" not in skip else None
    if neck == "bowtie":
        p.setPen(QPen(QColor("#7f0000"), 1.5 * w))
        p.setBrush(QColor("#e53935"))
        for side in (-1, 1):
            tri = QPainterPath(QPointF(0, neck_y))
            tri.lineTo(side * 0.32, neck_y - 0.17)
            tri.lineTo(side * 0.32, neck_y + 0.17)
            tri.closeSubpath()
            p.drawPath(tri)
        p.drawEllipse(QPointF(0, neck_y), 0.08, 0.08)
    elif neck == "scarf":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#c62828"))
        p.drawRoundedRect(QRectF(-0.6, neck_y - 0.12, 1.2, 0.24), 0.1, 0.1)
        tail = QPainterPath(QPointF(0.18, neck_y))
        tail.lineTo(0.42, neck_y + 0.5 + math.sin(t * 3) * 0.04)
        tail.lineTo(0.2, neck_y + 0.55)
        tail.lineTo(0.02, neck_y + 0.05)
        tail.closeSubpath()
        p.drawPath(tail)
        p.setBrush(QColor("#ffffff"))
        for i in range(-2, 3):
            p.drawRect(QRectF(i * 0.24 - 0.04, neck_y - 0.12, 0.08, 0.24))
    elif neck == "chain":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffc107"))
        for i in range(11):
            a = math.pi * i / 10
            p.drawEllipse(QPointF(-math.cos(a) * 0.42, neck_y - 0.05 + math.sin(a) * 0.18), 0.045, 0.045)
        p.setBrush(QColor("#ffb300"))
        p.drawEllipse(QPointF(0, neck_y + 0.25), 0.13, 0.13)
        p.setBrush(QColor("#fff59d"))
        p.drawPath(star_path(0, neck_y + 0.25, 0.08))

    glasses = outfit.get("glasses") if "glasses" not in skip else None
    for side in (-1, 1):
        ex, ey = side * 0.33 + eye_dx, eye_y
        if glasses == "shades":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#111111"))
            p.drawRoundedRect(QRectF(ex - 0.22, ey - 0.15, 0.44, 0.3), 0.08, 0.08)
            p.setPen(QPen(QColor(255, 255, 255, 170), 1.5 * w, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(ex - 0.14, ey - 0.07), QPointF(ex - 0.04, ey - 0.07))
        elif glasses == "round":
            p.setPen(QPen(QColor("#5d4037"), 2.5 * w))
            p.setBrush(QColor(180, 220, 255, 70))
            p.drawEllipse(QPointF(ex, ey), 0.21, 0.21)
        elif glasses == "hearts":
            p.setPen(QPen(QColor("#880e4f"), 1.5 * w))
            p.setBrush(QColor("#ec407a"))
            p.drawPath(heart_path(ex, ey + 0.02, 0.2))
    if glasses:
        color = {"shades": "#111111", "round": "#5d4037", "hearts": "#880e4f"}[glasses]
        p.setPen(QPen(QColor(color), 2.5 * w, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-0.12 + eye_dx, eye_y - 0.02), QPointF(0.12 + eye_dx, eye_y - 0.02))

    hat = outfit.get("hat") if "hat" not in skip else None
    T = top
    if hat == "party":
        cone = QPainterPath(QPointF(-0.32, T + 0.08))
        cone.lineTo(0.1, T - 0.75)
        cone.lineTo(0.32, T + 0.08)
        cone.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ab47bc"))
        p.drawPath(cone)
        p.setPen(QPen(QColor("#ffeb3b"), 3 * w))
        for k in (0.25, 0.5):
            y = T + 0.08 - 0.83 * k
            half = 0.32 * (1 - k)
            p.drawLine(QPointF(0.1 * k - half, y), QPointF(0.1 * k + half, y))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffeb3b"))
        p.drawEllipse(QPointF(0.1, T - 0.78), 0.1, 0.1)
    elif hat == "cap":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#c62828"))
        p.drawEllipse(QRectF(0.0, T + 0.08, 0.9, 0.2).translated(-0.2, 0))
        dome = QPainterPath(QPointF(-0.6, T + 0.22))
        dome.cubicTo(-0.6, T - 0.35, 0.6, T - 0.35, 0.6, T + 0.22)
        dome.closeSubpath()
        p.setBrush(QColor("#e53935"))
        p.drawPath(dome)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QPointF(0, T - 0.2), 0.06, 0.06)
    elif hat == "chef":
        p.setPen(QPen(QColor("#bdbdbd"), 1.5 * w))
        p.setBrush(Qt.white)
        for x, y, r in ((-0.3, T - 0.25, 0.26), (0.3, T - 0.25, 0.26), (0, T - 0.42, 0.32)):
            p.drawEllipse(QPointF(x, y), r, r)
        p.drawRoundedRect(QRectF(-0.45, T - 0.12, 0.9, 0.24), 0.05, 0.05)
    elif hat == "tophat":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#212121"))
        p.drawRoundedRect(QRectF(-0.62, T - 0.02, 1.24, 0.12), 0.05, 0.05)
        p.drawRect(QRectF(-0.38, T - 0.75, 0.76, 0.76))
        p.setBrush(QColor("#d32f2f"))
        p.drawRect(QRectF(-0.38, T - 0.16, 0.76, 0.1))
    elif hat == "wizard":
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#283593"))
        p.drawEllipse(QPointF(0, T + 0.04), 0.65, 0.12)
        cone = QPainterPath(QPointF(-0.4, T + 0.04))
        cone.quadTo(-0.1, T - 0.55, 0.3, T - 1.05)
        cone.quadTo(0.2, T - 0.5, 0.4, T + 0.04)
        cone.closeSubpath()
        p.setBrush(QColor("#3949ab"))
        p.drawPath(cone)
        p.setBrush(QColor("#ffeb3b"))
        for x, y, r in ((-0.1, T - 0.3, 0.08), (0.12, T - 0.6, 0.06), (0.15, T - 0.12, 0.05)):
            p.drawPath(star_path(x, y, r))
    elif hat == "crown":
        crown = QPainterPath(QPointF(-0.42, T + 0.1))
        for x, y in ((-0.42, T - 0.3), (-0.21, T - 0.08), (0, T - 0.42), (0.21, T - 0.08),
                     (0.42, T - 0.3), (0.42, T + 0.1)):
            crown.lineTo(x, y)
        crown.closeSubpath()
        p.setPen(QPen(QColor("#f9a825"), 2 * w, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(QColor("#ffca28"))
        p.drawPath(crown)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#e53935"))
        p.drawEllipse(QPointF(0, T - 0.02), 0.07, 0.07)
        p.setBrush(QColor("#42a5f5"))
        p.drawEllipse(QPointF(-0.24, T + 0.0), 0.05, 0.05)
        p.drawEllipse(QPointF(0.24, T + 0.0), 0.05, 0.05)
    p.restore()


class RobotFace(QWidget):
    """רובוט מצויר ומונפש שמראה רגש, ולובש את מה שקנית לו בחנות."""
    W, H = 300, 225  # גודל אזור הציור הלוגי
    HAT_ROOM = 50    # מקום מעל הראש לכובעים גבוהים

    def __init__(self):
        super().__init__()
        self.emotion = "neutral"
        self.failed = False
        self.preview = {}   # בגדים "למדידה" בחנות, לפני שקונים
        self.changed_at = time.time()
        self.t0 = time.time()
        self.setMinimumHeight(200)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(33)

    def set_emotion(self, name):
        name = name if name in EMOTIONS else "neutral"
        if name != self.emotion:
            self.emotion = name
            self.changed_at = time.time()

    # ---------- ציור ----------
    def paintEvent(self, _):
        if self.failed:
            return
        p = QPainter(self)
        try:
            self.paint(p)
        except Exception:
            self.failed = True  # מדווחים פעם אחת ומפסיקים לצייר, במקום לקרוס
            self.timer.stop()
            sys.excepthook(*sys.exc_info())
        finally:
            if p.isActive():
                p.end()

    def paint(self, p):
        e = EMOTIONS[self.emotion]
        t = time.time() - self.t0
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#262626"))

        H = self.H + self.HAT_ROOM
        s = min(self.width() / self.W, self.height() / H)
        p.translate((self.width() - self.W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)
        p.translate(0, self.HAT_ROOM)

        # תנועה: נשימה, קפיצה, רעד, וקפיצונת קטנה כשהרגש מתחלף
        dy = math.sin(t * 2) * 1.5
        dy -= abs(math.sin(t * 6)) * 6 * e.get("bounce", 0)
        pop = max(0.0, 1 - (time.time() - self.changed_at) * 4)
        dy -= math.sin(pop * math.pi) * 8
        dx = math.sin(t * 50) * 2.5 * e.get("shake", 0)

        # צל
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawEllipse(QRectF(105, 205, 90, 12))

        p.translate(dx, dy)
        self.outfit = current_outfit()
        self.outfit.update(self.preview)
        self.draw_back(p, t)
        self.draw_body(p, e, t)
        self.draw_head(p, e)
        self.draw_eyes(p, e, t)
        self.draw_brows(p, e)
        self.draw_mouth(p, e, t)
        draw_accessories(p, self.outfit, 150, 100, 78, t=t)
        self.draw_extra(p, e, t)

    def draw_back(self, p, t):
        """גלימה או כנפיים, מאחורי הגוף."""
        back = self.outfit.get("back")
        if back == "cape":
            wave = math.sin(t * 3) * 6
            cape = QPainterPath(QPointF(122, 158))
            cape.lineTo(182 - 4, 158)
            cape.quadTo(205, 190, 214 + wave, 222)
            cape.quadTo(150, 212 + wave * 0.5, 86 - wave, 222)
            cape.quadTo(95, 190, 122, 158)
            p.setPen(QPen(QColor("#8e0000"), 2))
            p.setBrush(QColor("#d32f2f"))
            p.drawPath(cape)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffeb3b"))
            p.drawPath(star_path(150, 198, 9))
        elif back == "wings":
            flap = math.sin(t * 4) * 8
            for side in (-1, 1):
                wing = QPainterPath(QPointF(150 + side * 22, 170))
                wing.cubicTo(150 + side * 70, 120 - flap, 150 + side * 120, 140 - flap, 150 + side * 112, 168)
                wing.cubicTo(150 + side * 100, 186, 150 + side * 60, 196, 150 + side * 22, 190)
                wing.closeSubpath()
                p.setPen(QPen(QColor("#b0bec5"), 2))
                p.setBrush(QColor("#fafafa"))
                p.drawPath(wing)
                p.setPen(QPen(QColor("#cfd8dc"), 1.5))
                for k in (0.35, 0.6, 0.85):
                    p.drawLine(QPointF(150 + side * (30 + 70 * k), 176 - flap * k * 0.3),
                               QPointF(150 + side * (40 + 70 * k), 190 - 8 * k))

    def draw_body(self, p, e, t):
        wave = math.sin(t * 8) * 10 if e.get("bounce") else 0
        pen = QPen(HEAD_DARK, 9, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(116, 172), QPointF(96, 186 - wave))   # יד שמאל
        p.drawLine(QPointF(184, 172), QPointF(204, 186 + wave))  # יד ימין
        p.setPen(QPen(HEAD_DARK.darker(115), 2))
        p.setBrush(HEAD_DARK)
        p.drawRoundedRect(QRectF(112, 156, 76, 50), 18, 18)
        # נורה על הבטן בצבע הרגש
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(e["light"]))
        p.drawEllipse(QPointF(150, 182), 8, 8)

    def draw_head(self, p, e):
        # אנטנה
        p.setPen(QPen(BOLT, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(150, 38), QPointF(150, 20))
        glow = QColor(e["light"])
        glow.setAlpha(80)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(QPointF(150, 15), 12, 12)
        p.setBrush(QColor(e["light"]))
        p.drawEllipse(QPointF(150, 15), 7, 7)
        # ברגים בצדדים
        p.setBrush(BOLT)
        p.drawEllipse(QPointF(70, 100), 9, 13)
        p.drawEllipse(QPointF(230, 100), 9, 13)
        # ראש ופנים
        p.setPen(QPen(HEAD_DARK, 3))
        p.setBrush(HEAD)
        p.drawRoundedRect(QRectF(72, 34, 156, 132), 62, 58)
        p.setPen(Qt.NoPen)
        p.setBrush(FACE)
        p.drawEllipse(QRectF(90, 55, 120, 98))
        if e.get("cheeks"):
            p.setBrush(QColor(255, 120, 140, 110))
            p.drawEllipse(QPointF(106, 122), 10, 6)
            p.drawEllipse(QPointF(194, 122), 10, 6)

    def draw_eyes(self, p, e, t):
        kind = e["eyes"]
        blink = 0.1 if (t % 3.7) < 0.13 else 1.0
        for ex, side in ((124, -1), (176, 1)):
            ey = 98
            if kind in ("open", "open_small", "big", "look_up"):
                rx, ry = {"open": (11, 14), "open_small": (9, 11), "big": (14, 18), "look_up": (11, 14)}[kind]
                ox, oy = (4, -5) if kind == "look_up" else (0, 0)
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
                p.drawEllipse(QPointF(ex + ox, ey + oy), rx, ry * blink)
                if blink > 0.5:
                    p.setBrush(Qt.white)
                    p.drawEllipse(QPointF(ex + ox + rx * 0.35, ey + oy - ry * 0.35), rx * 0.32, rx * 0.32)
            elif kind == "happy":
                path = QPainterPath(QPointF(ex - 11, ey + 4))
                path.quadTo(ex, ey - 12, ex + 11, ey + 4)
                p.setPen(QPen(INK, 5, Qt.SolidLine, Qt.RoundCap))
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)
            elif kind == "laugh":
                d = -side * 8  # > <
                path = QPainterPath(QPointF(ex - d, ey - 8))
                path.lineTo(ex + d, ey)
                path.lineTo(ex - d, ey + 8)
                p.setPen(QPen(INK, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)
            elif kind == "heart":
                beat = 1 + 0.12 * abs(math.sin(t * 5))
                p.setPen(Qt.NoPen)
                p.setBrush(QColor("#e53935"))
                p.drawPath(heart_path(ex, ey, 13 * beat))
            elif kind == "tiny_pupil":
                p.setPen(QPen(INK, 3))
                p.setBrush(Qt.white)
                p.drawEllipse(QPointF(ex, ey), 13, 15)
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
                p.drawEllipse(QPointF(ex + math.sin(t * 30), ey), 4, 4)
            elif kind == "half":
                path = QPainterPath(QPointF(ex - 11, ey))
                path.arcTo(QRectF(ex - 11, ey - 9, 22, 18), 180, 180)
                path.closeSubpath()
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
                p.drawPath(path)
                p.setPen(QPen(INK, 3, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - 13, ey), QPointF(ex + 13, ey))
            elif kind == "smug":
                # עפעפיים חצי סגורים ומבט הצידה, כמו "אני יודע שאני מושלם"
                path = QPainterPath(QPointF(ex - 12, ey - 2))
                path.arcTo(QRectF(ex - 12, ey - 12, 24, 22), 180, 180)
                path.closeSubpath()
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
                p.drawPath(path)
                p.setBrush(Qt.white)
                p.drawEllipse(QPointF(ex + 5, ey + 3), 3, 3)
                p.setPen(QPen(INK, 3, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - 14, ey - 1), QPointF(ex + 14, ey - 4))

    def draw_brows(self, p, e):
        kind = e["brows"]
        if not kind:
            return
        p.setPen(QPen(INK, 4, Qt.SolidLine, Qt.RoundCap))
        by = 74
        for ex, side in ((124, -1), (176, 1)):
            inner, outer = ex - side * 11, ex + side * 11
            if kind == "angry":
                p.drawLine(QPointF(inner, by + 7), QPointF(outer, by - 3))
            elif kind == "sad":
                p.drawLine(QPointF(inner, by - 5), QPointF(outer, by + 4))
            elif kind == "up":
                p.drawLine(QPointF(inner, by - 8), QPointF(outer, by - 6))
            elif kind == "one_up":
                if side == 1:
                    p.drawLine(QPointF(inner, by - 6), QPointF(outer, by - 11))
                else:
                    p.drawLine(QPointF(inner, by + 1), QPointF(outer, by + 1))

    def draw_mouth(self, p, e, t):
        kind, cx, my = e["mouth"], 150, 128
        p.setPen(QPen(INK, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        path = QPainterPath()
        if kind == "smile":
            path.moveTo(cx - 18, my - 3)
            path.quadTo(cx, my + 14, cx + 18, my - 3)
        elif kind == "small_smile":
            path.moveTo(cx - 10, my)
            path.quadTo(cx, my + 7, cx + 10, my)
        elif kind == "frown":
            path.moveTo(cx - 15, my + 7)
            path.quadTo(cx, my - 6, cx + 15, my + 7)
        elif kind == "flat":
            path.moveTo(cx - 10, my + 2)
            path.lineTo(cx + 10, my + 2)
        elif kind == "smirk":
            path.moveTo(cx - 14, my + 2)
            path.quadTo(cx + 4, my + 10, cx + 19, my - 6)
        elif kind == "side":
            path.moveTo(cx + 2, my + 3)
            path.quadTo(cx + 12, my + 1, cx + 20, my - 3)
        elif kind == "wavy":
            path.moveTo(cx - 16, my + 3)
            for i in range(4):
                path.lineTo(cx - 12 + i * 8, my + (-3 if i % 2 == 0 else 3))
            path.lineTo(cx + 16, my - 1)
        elif kind == "o":
            p.setPen(Qt.NoPen)
            p.setBrush(INK)
            r = 8 + math.sin(t * 4) * 1
            p.drawEllipse(QPointF(cx, my + 4), r, r * 1.25)
            return
        elif kind == "big":
            open_ = 20 + abs(math.sin(t * 9)) * 6
            path.moveTo(cx - 20, my - 5)
            path.lineTo(cx + 20, my - 5)
            path.quadTo(cx, my + open_, cx - 20, my - 5)
            p.setPen(Qt.NoPen)
            p.setBrush(INK)
            p.drawPath(path)
            p.setBrush(QColor("#ef5350"))
            p.drawEllipse(QPointF(cx, my + open_ * 0.35), 8, 4)
            return
        p.drawPath(path)

    def draw_extra(self, p, e, t):
        kind = e.get("extra")
        p.setPen(Qt.NoPen)
        if kind == "hearts":
            for i in range(3):
                ph = (t * 0.5 + i / 3) % 1
                c = QColor("#f06292")
                c.setAlpha(int(255 * (1 - ph)))
                p.setBrush(c)
                p.drawPath(heart_path(235 + i * 10 + math.sin(t * 3 + i) * 5, 70 - ph * 60, 7))
        elif kind == "crown" and self.outfit.get("hat"):
            # כבר יש כובע מהחנות: רק נצנוצים, בלי הכתר העקום
            for i, (x, y) in enumerate(((88, 48), (238, 92), (100, 160))):
                c = QColor("#fff176")
                c.setAlpha(int(255 * abs(math.sin(t * 3 + i * 2))))
                p.setBrush(c)
                p.drawPath(star_path(x, y, 7))
        elif kind == "crown":
            # כתר זהב עקום על הראש ונצנוצים מסביב
            p.save()
            p.translate(196, 38)
            p.rotate(18 + math.sin(t * 3) * 4)
            crown = QPainterPath(QPointF(-16, 10))
            for x, y in ((-16, -6), (-8, 2), (0, -12), (8, 2), (16, -6), (16, 10)):
                crown.lineTo(x, y)
            crown.closeSubpath()
            p.setPen(QPen(QColor("#f9a825"), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(QColor("#ffca28"))
            p.drawPath(crown)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#e53935"))
            p.drawEllipse(QPointF(0, 4), 3, 3)
            p.setBrush(QColor("#42a5f5"))
            p.drawEllipse(QPointF(-9, 6), 2, 2)
            p.drawEllipse(QPointF(9, 6), 2, 2)
            p.restore()
            for i, (x, y) in enumerate(((88, 48), (238, 92), (100, 160))):
                c = QColor("#fff176")
                c.setAlpha(int(255 * abs(math.sin(t * 3 + i * 2))))
                p.setBrush(c)
                p.drawPath(star_path(x, y, 7))
        elif kind == "tear":
            y = 112 + (t * 22) % 30
            p.setBrush(QColor(100, 181, 246, 220))
            p.drawPath(drop_path(118, y, 6))
        elif kind == "sweat":
            p.setBrush(QColor(144, 202, 249, 220))
            p.drawPath(drop_path(212, 60 + math.sin(t * 3) * 2, 8))
        elif kind == "steam":
            for i, x in enumerate((80, 220)):
                for j in range(3):
                    ph = (t * 0.8 + j / 3 + i * 0.15) % 1
                    c = QColor(200, 200, 200)
                    c.setAlpha(int(180 * (1 - ph)))
                    p.setBrush(c)
                    p.drawEllipse(QPointF(x + math.sin(t * 4 + j) * 4, 40 - ph * 35), 5 + ph * 6, 5 + ph * 6)
        elif kind in ("exclaim", "question", "dots", "zzz"):
            p.setPen(QColor({"exclaim": "#ffb74d", "question": "#ba68c8",
                             "dots": "#4dd0e1", "zzz": "#90a4ae"}[kind]))
            if kind == "exclaim":
                p.setFont(QFont("Arial", 30, QFont.Bold))
                p.drawText(QPointF(232, 62 - abs(math.sin(t * 6)) * 6), "!")
            elif kind == "question":
                p.setFont(QFont("Arial", 28, QFont.Bold))
                p.drawText(QPointF(232, 60 + math.sin(t * 3) * 4), "?")
            elif kind == "dots":
                p.setFont(QFont("Arial", 26, QFont.Bold))
                p.drawText(QPointF(228, 52), "." * (int(t * 3) % 3 + 1))
            else:
                for i in range(3):
                    ph = (t * 0.4 + i / 3) % 1
                    p.setFont(QFont("Arial", int(10 + ph * 12), QFont.Bold))
                    p.drawText(QPointF(222 + ph * 30, 70 - ph * 55), "z")


# ---------------------------------------------------------------- כדורגל נגד פיקו
def clamp(value, low, high):
    return max(low, min(high, value))


# מקלדת עברית: האות שהמקש כותב -> המקש באנגלית שנמצא באותו מקום
HEBREW_KEYS = {ord(h): getattr(Qt, "Key_" + e) for h, e in (
    ("ש", "A"), ("ג", "D"), ("ד", "S"), ("'", "W"), ("ר", "R"),
    ("ז", "Z"), ("ס", "X"), ("ב", "C"), ("ח", "J"), ("ל", "K"), ("ך", "L"),
)}


PIKO_GOAL_TAUNTS = [
    "גול של פיקו! ראית את הבעיטה הגאונית הזו? 100 מתוך 10!",
    "עוד גול! אני פשוט טוב מדי בשבילך. 😎",
    "חח! השוער שלך יצא להפסקה?",
    "פיקו הגדול בועט, פיקו הגדול מבקיע. ככה זה.",
]
PLAYER_GOAL_TAUNTS = [
    "מה?! זה היה מזל! הכדור החליק לי מהבורג!",
    "טוב, נתתי לך את הגול הזה כדי שלא תתבאס. 😤",
    "גול שלך? בטוח היה נבדל! איפה השופט?",
    "רגע, האנטנה שלי הסתנוורה מהשמש. לא נחשב!",
]


class FootballGame(QWidget):
    """משחק כדורגל קטן נגד פיקו. חצים או WASD לזוז, R משחק חדש, Esc סוגר."""
    emotion = Signal(str)
    finished = Signal(int, int)  # הניקוד שלך, הניקוד של פיקו

    W, H = 800, 500           # גודל המגרש הלוגי
    PR, BR = 22, 12           # רדיוס שחקן ורדיוס כדור
    GOAL_W, GOAL_H = 18, 170
    SPEED = 6
    FRICTION = 0.986
    BALL_MAX = 17
    WIN = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("כדורגל נגד פיקו")
        self.setLayoutDirection(Qt.LeftToRight)
        self.resize(self.W, self.H)
        self.setMinimumSize(400, 250)
        self.setFocusPolicy(Qt.StrongFocus)
        self.keys = set()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.restart()

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]  # אתה, פיקו
        self.over = False
        self.pause = 0
        self.say("פיקו: אני הולך לנצח אותך 3-0! 😎", 180)
        self.place()
        self.emotion.emit("proud")

    def place(self):
        """מחזיר את השחקנים והכדור לעמדת הפתיחה. כל אחד הוא [x, y, vx, vy]."""
        self.player = [200.0, self.H / 2, 0.0, 0.0]
        self.piko = [self.W - 200.0, self.H / 2, 0.0, 0.0]
        self.ball = [self.W / 2, self.H / 2, 0.0, 0.0]

    def say(self, text, frames=150):
        self.message = text
        self.msg_timer = frames

    # ---------- לולאת המשחק ----------
    def showEvent(self, event):
        self.timer.start(16)
        super().showEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        self.keys.clear()
        super().closeEvent(event)

    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        if not self.over:
            if self.pause > 0:
                self.pause -= 1
                if self.pause == 0:
                    self.place()
            else:
                self.physics()
        self.update()

    def physics(self):
        k = self.keys
        dx = (Qt.Key_D in k or Qt.Key_Right in k) - (Qt.Key_A in k or Qt.Key_Left in k)
        dy = (Qt.Key_S in k or Qt.Key_Down in k) - (Qt.Key_W in k or Qt.Key_Up in k)
        pl = self.player
        if dx or dy:
            d = math.hypot(dx, dy)
            speed = self.SPEED * 1.2
            pl[2], pl[3] = dx / d * speed, dy / d * speed
        else:
            pl[2] = pl[3] = 0.0
        pl[0] += pl[2]
        pl[1] += pl[3]
        self.keep_inside(pl)

        self.piko_ai()
        self.move_ball()
        self.hit_ball(self.player)
        self.hit_ball(self.piko)
        self.push_players()
        self.check_goal()

    def keep_inside(self, p):
        p[0] = clamp(p[0], self.PR + self.GOAL_W, self.W - self.PR - self.GOAL_W)
        p[1] = clamp(p[1], self.PR + 5, self.H - self.PR - 5)

    def piko_ai(self):
        x, y, vx, vy = self.piko
        bx, by, bvx, bvy = self.ball
        W, H = self.W, self.H
        tx, ty = W - 170, H / 2  # עמדת הגנה ליד השער של פיקו
        if bx > W / 2 or abs(by - y) > 90:
            # עומד מאחורי הכדור כדי לדחוף אותו לכיוון השער שלך
            tx = clamp(bx + bvx * 2 + 50, W / 2 + self.PR + self.GOAL_W, W - self.PR - self.GOAL_W)
            ty = clamp(by + bvy * 2, self.PR + 5, H - self.PR - 5)
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy)
        speed = self.SPEED
        if bx <= W / 2:
            speed *= 0.6  # בהגנה פיקו קצת עצלן
        if dist > 1:
            arrive = speed * clamp(dist / 40, 0.25, 1.0)
            want_vx, want_vy = dx / dist * arrive, dy / dist * arrive
        else:
            want_vx = want_vy = 0.0
        vx += (want_vx - vx) * 0.3
        vy += (want_vy - vy) * 0.3
        self.piko[:] = [x + vx, y + vy, vx, vy]
        self.keep_inside(self.piko)

    def move_ball(self):
        b = self.ball
        b[0] += b[2]
        b[1] += b[3]
        b[2] *= self.FRICTION
        b[3] *= self.FRICTION
        if abs(b[2]) < 0.05:
            b[2] = 0.0
        if abs(b[3]) < 0.05:
            b[3] = 0.0
        if b[1] - self.BR <= 0 or b[1] + self.BR >= self.H:
            b[3] = -b[3]
            b[1] = clamp(b[1], self.BR, self.H - self.BR)
        in_mouth = self.H / 2 - self.GOAL_H / 2 < b[1] < self.H / 2 + self.GOAL_H / 2
        if not in_mouth:
            if b[0] - self.BR <= self.GOAL_W:
                b[2] = abs(b[2])
                b[0] = self.GOAL_W + self.BR
            elif b[0] + self.BR >= self.W - self.GOAL_W:
                b[2] = -abs(b[2])
                b[0] = self.W - self.GOAL_W - self.BR

    def hit_ball(self, p):
        b = self.ball
        dx, dy = b[0] - p[0], b[1] - p[1]
        dist = math.hypot(dx, dy) or 1
        if dist <= self.PR + self.BR + 4:
            power = 10 + min(7, math.hypot(p[2], p[3]) * 1.25)
            b[2] = clamp(dx / dist * power + p[2] * 0.8, -self.BALL_MAX, self.BALL_MAX)
            b[3] = clamp(dy / dist * power + p[3] * 0.8, -self.BALL_MAX, self.BALL_MAX)
            overlap = self.PR + self.BR - dist + 2
            if overlap > 0:
                b[0] += dx / dist * overlap
                b[1] += dy / dist * overlap

    def push_players(self):
        a, b = self.player, self.piko
        dx, dy = b[0] - a[0], b[1] - a[1]
        dist = math.hypot(dx, dy)
        if 0 < dist < self.PR * 2:
            half = (self.PR * 2 - dist) / 2
            a[0] -= dx / dist * half
            a[1] -= dy / dist * half
            b[0] += dx / dist * half
            b[1] += dy / dist * half
            self.keep_inside(a)
            self.keep_inside(b)

    def check_goal(self):
        bx, by = self.ball[0], self.ball[1]
        if not (self.H / 2 - self.GOAL_H / 2 < by < self.H / 2 + self.GOAL_H / 2):
            return
        if bx - self.BR <= 0:
            self.goal(by_piko=True)
        elif bx + self.BR >= self.W:
            self.goal(by_piko=False)

    def goal(self, by_piko):
        self.score[1 if by_piko else 0] += 1
        self.ball[2] = self.ball[3] = 0.0
        you, piko = self.score
        if max(self.score) >= self.WIN:
            self.over = True
            if piko > you:
                self.say(f"פיקו ניצח {piko}-{you}! כמובן. הגאון אף פעם לא מפסיד. 👑", 10 ** 9)
                self.emotion.emit("proud")
            else:
                self.say(f"ניצחת {you}-{piko}?! ...טוב, נתתי לך לנצח. ברור שנתתי.", 10 ** 9)
                self.emotion.emit("surprised")
            self.finished.emit(you, piko)
            return
        if by_piko:
            self.say(random.choice(PIKO_GOAL_TAUNTS))
            self.emotion.emit(random.choice(["laugh", "proud"]))
        else:
            self.say(random.choice(PLAYER_GOAL_TAUNTS))
            self.emotion.emit(random.choice(["angry", "surprised"]))
        self.pause = 70  # עצירה קצרה ואז חוזרים לאמצע

    # ---------- מקלדת ----------
    @staticmethod
    def key_of(event):
        """אותו מקש פיזי עובד גם כשהמקלדת על עברית (למשל ש = A, ר = R)."""
        k = event.key()
        return HEBREW_KEYS.get(k, k)

    def keyPressEvent(self, event):
        key = self.key_of(event)
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_R:
            self.restart()
        else:
            self.keys.add(key)

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat():
            self.keys.discard(self.key_of(event))

    def focusOutEvent(self, event):
        self.keys.clear()
        super().focusOutEvent(event)

    # ---------- ציור ----------
    def paintEvent(self, _):
        p = QPainter(self)
        try:
            self.paint(p)
        finally:
            p.end()

    def paint(self, p):
        W, H, GW, GH = self.W, self.H, self.GOAL_W, self.GOAL_H
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1b3d1d"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)

        # דשא מפוספס
        for i, x in enumerate(range(0, W, 50)):
            p.fillRect(QRectF(x, 0, 50, H), QColor("#43a047" if i % 2 == 0 else "#388e3c"))

        # קווי המגרש
        p.setPen(QPen(QColor(255, 255, 255, 220), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(GW, 3, W - 2 * GW, H - 6))
        p.drawLine(QPointF(W / 2, 3), QPointF(W / 2, H - 3))
        p.drawEllipse(QPointF(W / 2, H / 2), 70, 70)
        p.drawRect(QRectF(GW, H / 2 - 110, 110, 220))
        p.drawRect(QRectF(W - GW - 110, H / 2 - 110, 110, 220))

        # שערים
        p.setBrush(QColor(220, 230, 255, 210))
        p.drawRect(QRectF(0, H / 2 - GH / 2, GW, GH))
        p.drawRect(QRectF(W - GW, H / 2 - GH / 2, GW, GH))

        # צללים
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        for obj, r in ((self.player, self.PR), (self.piko, self.PR), (self.ball, self.BR)):
            p.drawEllipse(QRectF(obj[0] - r, obj[1] + r * 0.6, r * 2, r * 0.6))

        # אתה (כחול)
        p.setPen(QPen(Qt.white, 3))
        p.setBrush(QColor("#1e88e5"))
        p.drawEllipse(QPointF(self.player[0], self.player[1]), self.PR, self.PR)

        self.draw_piko(p)

        # כדור
        p.setPen(QPen(INK, 2))
        p.setBrush(QColor("#fff176"))
        p.drawEllipse(QPointF(self.ball[0], self.ball[1]), self.BR, self.BR)

        self.draw_scoreboard(p)
        self.draw_overlay(p, "WASD / חצים  ·  R  ·  Esc")

    def draw_overlay(self, p, hint, msg_y=None, hint_y=8):
        """ההודעה של פיקו, מסך הסיום ושורת העזרה. משותף לכל המשחקים."""
        W, H = self.W, self.H
        # מה שפיקו אומר
        if self.msg_timer > 0 and self.message and not self.over:
            box = QRectF(W / 2 - 320, H - 66 if msg_y is None else msg_y, 640, 44)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 160))
            p.drawRoundedRect(box, 12, 12)
            p.setPen(QColor("#ffccbc"))
            p.setFont(QFont("Arial", 14, QFont.Bold))
            p.drawText(box, Qt.AlignCenter, self.message)

        if self.over:
            p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, 160))
            you, piko = self.score
            p.setPen(Qt.white)
            p.setFont(QFont("Arial", 40, QFont.Bold))
            p.drawText(QRectF(0, H / 2 - 110, W, 60), Qt.AlignCenter,
                       "פיקו ניצח!" if piko > you else "ניצחת!" if you > piko else "תיקו!")
            p.setFont(QFont("Arial", 16, QFont.Bold))
            p.setPen(QColor("#ffccbc"))
            p.drawText(QRectF(20, H / 2 - 30, W - 40, 40), Qt.AlignCenter, self.message)
            p.setPen(QColor("#dddddd"))
            p.setFont(QFont("Arial", 14))
            p.drawText(QRectF(0, H / 2 + 30, W, 30), Qt.AlignCenter, "R = משחק חדש      Esc = סגירה")
        else:
            p.setPen(QColor(255, 255, 255, 200))
            p.setFont(QFont("Arial", 11))
            if hint_y == 8:
                p.drawText(QRectF(26, 8, 240, 20), Qt.AlignLeft | Qt.AlignVCenter, hint)
            else:
                # פס כהה מאחורי שורת העזרה, כדי שתהיה קריאה על כל רקע
                width = QFontMetrics(p.font()).horizontalAdvance(hint) + 28
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 120))
                p.drawRoundedRect(QRectF((W - width) / 2, hint_y - 1, width, 22), 9, 9)
                p.setPen(QColor(255, 255, 255, 230))
                p.drawText(QRectF(0, hint_y, W, 20), Qt.AlignCenter, hint)

    def draw_scoreboard(self, p):
        W = self.W
        board = QRectF(W / 2 - 130, 10, 260, 40)
        p.setPen(QPen(Qt.white, 2))
        p.setBrush(QColor(0, 0, 0, 160))
        p.drawRoundedRect(board, 10, 10)
        p.setFont(QFont("Arial", 13, QFont.Bold))
        p.setPen(QColor("#90caf9"))
        p.drawText(QRectF(W / 2 - 125, 10, 70, 40), Qt.AlignCenter, "אתה")
        p.setPen(QColor("#ffab91"))
        p.drawText(QRectF(W / 2 + 55, 10, 70, 40), Qt.AlignCenter, "פיקו")
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 20, QFont.Bold))
        p.drawText(QRectF(W / 2 - 55, 10, 40, 40), Qt.AlignCenter, str(self.score[0]))
        p.drawText(QRectF(W / 2 - 15, 10, 30, 40), Qt.AlignCenter, ":")
        p.drawText(QRectF(W / 2 + 15, 10, 40, 40), Qt.AlignCenter, str(self.score[1]))

    def draw_piko(self, p):
        """פיקו הקטן במגרש: ראש כתום עם אנטנה, ועיניים שעוקבות אחרי הכדור."""
        x, y = self.piko[0], self.piko[1]
        r = self.PR
        p.setPen(QPen(BOLT, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, y - r), QPointF(x, y - r - 10))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(x, y - r - 12), 4, 4)
        p.setPen(QPen(HEAD_DARK, 3))
        p.setBrush(HEAD)
        p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(Qt.NoPen)
        p.setBrush(FACE)
        p.drawEllipse(QPointF(x, y + 2), r * 0.72, r * 0.62)
        a = math.atan2(self.ball[1] - y, self.ball[0] - x)
        ox, oy = math.cos(a) * 2.5, math.sin(a) * 2.5
        p.setBrush(INK)
        for ex in (x - 6, x + 6):
            p.drawEllipse(QPointF(ex + ox, y - 2 + oy), 3, 4)
        mouth = QPainterPath(QPointF(x - 6, y + 7))
        mouth.quadTo(x, y + 12, x + 7, y + 5)
        p.setPen(QPen(INK, 2, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(mouth)
        draw_accessories(p, current_outfit(), x, y, r, top=-0.95, eye_y=-0.1, neck_y=0.95,
                         t=time.time())


# ---------------------------------------------------------------- כדור סל נגד פיקו
PIKO_BASKET_TAUNTS = [
    "סל! ראית את הזריקה הזו? מושלמת, כמו כל דבר שאני עושה. 😎",
    "שוויש! אפילו לא נגעתי בטבעת. 100 מתוך 10!",
    "עוד סל לפיקו הגדול! אולי תנסה לקפוץ קצת יותר גבוה?",
    "קל מדי! זרקתי עם העיניים עצומות. טוב, עם עין אחת.",
]
PLAYER_BASKET_TAUNTS = [
    "מה?! הסל הזה זז לכיוון שלך, ראיתי!",
    "טוב, נתתי לך את הסל הזה כדי שיהיה מעניין. 😤",
    "סל שלך? האנטנה שלי הסתנוורה מהאורות!",
    "מזל של מתחילים! תיהנה מזה, זה לא יקרה שוב.",
]


class BasketballGame(FootballGame):
    """כדור סל נגד פיקו, במבט מהצד.
    חצים או A/D לזוז, למעלה או W לקפוץ, רווח (או למטה/S) לזרוק, R משחק חדש, Esc סוגר.
    אתה זורק לסל הימני, פיקו זורק לסל השמאלי."""

    W, H = 800, 500
    PR, BR = 24, 11
    FLOOR = 450
    BALL_G = 0.45            # כוח המשיכה של הכדור
    BODY_G = 0.6             # כוח המשיכה של השחקנים
    JUMP = -11.5
    RIM_Y = 215
    BOARD_TOP, BOARD_BOTTOM = 120, 235
    THREE = 330              # מהמרחק הזה זריקה שווה 3 נקודות
    WIN = 10                 # מי שמגיע ראשון ל-10 נקודות מנצח

    def __init__(self):
        self.want_shoot = False
        super().__init__()
        self.setWindowTitle("כדור סל נגד פיקו")

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.pause = 0
        self.next_owner = "player"
        self.say("פיקו: כדור סל? אני מקליע מכל המגרש בעיניים עצומות! 😎", 180)
        self.place()
        self.emotion.emit("proud")

    def place(self):
        """עמדת פתיחה. הכדור אצל מי שספג את הסל האחרון."""
        f = self.FLOOR - self.PR
        self.player = [200.0, f, 0.0, 0.0]
        self.piko = [self.W - 200.0, f, 0.0, 0.0]
        self.ball = [0.0, 0.0, 0.0, 0.0]
        self.holder = self.next_owner
        self.no_grab = {"player": 0, "piko": 0}
        self.steal_cd = 30
        self.last_shooter = None
        self.shot_points = 2
        self.piko_spot = None
        self.piko_think = 30
        self.piko_hold = 0
        self.piko_jumpshot = False
        self.want_shoot = False
        self.hold_ball()

    def hoop(self, side):
        """side=1 הסל הימני (שלך לזרוק אליו), side=-1 השמאלי (של פיקו).
        מחזיר: x של הלוח, x של קצה הטבעת, ומרכז הטבעת."""
        board = self.W - 40 if side > 0 else 40
        front = board - side * 60
        return board, front, (board + front) / 2

    def on_ground(self, body):
        return body[1] >= self.FLOOR - self.PR - 0.5

    # ---------- מקלדת ----------
    def keyPressEvent(self, event):
        if self.key_of(event) in (Qt.Key_Space, Qt.Key_S, Qt.Key_Down) and not event.isAutoRepeat():
            self.want_shoot = True
        super().keyPressEvent(event)

    # ---------- פיזיקה ----------
    def physics(self):
        k = self.keys
        pl = self.player
        dx = (Qt.Key_D in k or Qt.Key_Right in k) - (Qt.Key_A in k or Qt.Key_Left in k)
        pl[2] = dx * 5.5
        if (Qt.Key_W in k or Qt.Key_Up in k) and self.on_ground(pl):
            pl[3] = self.JUMP
        self.move_body(pl)
        if self.want_shoot:
            self.want_shoot = False
            if self.holder == "player":
                self.shoot("player", 1)

        self.piko_ai()
        self.move_body(self.piko)

        for name in self.no_grab:
            self.no_grab[name] = max(0, self.no_grab[name] - 1)
        self.steal_cd = max(0, self.steal_cd - 1)
        self.contact()

        if self.holder:
            self.hold_ball()
        else:
            self.move_ball()
            if not self.pause and not self.over:
                self.try_grab()

    def move_body(self, b):
        b[3] += self.BODY_G
        b[0] += b[2]
        b[1] += b[3]
        if b[1] >= self.FLOOR - self.PR:
            b[1] = self.FLOOR - self.PR
            b[3] = 0.0
        b[0] = clamp(b[0], self.PR + 6, self.W - self.PR - 6)

    def hold_ball(self):
        h = self.player if self.holder == "player" else self.piko
        face = 1 if self.holder == "player" else -1
        self.ball[:] = [h[0] + face * (self.PR + 4), h[1] - self.PR * 0.6, h[2], h[3]]

    def shoot(self, name, side):
        """זריקה לסל: מחשבים קשת שמגיעה לטבעת, עם קצת פספוס אקראי."""
        h = self.player if name == "player" else self.piko
        board, front, cx = self.hoop(side)
        bx, by = self.ball[0], self.ball[1]
        dist = abs(cx - h[0])
        sigma = 10 + dist * 0.12         # רחוק יותר = פחות מדויק
        if not self.on_ground(h):
            sigma *= 0.75                # זריקה בקפיצה מדויקת יותר
        if name == "piko":
            sigma *= 1.35  # פיקו קצת פחות מדויק ממך, כדי שיהיה הוגן
        tx = cx + random.gauss(0, sigma)
        ty = self.RIM_Y - 4
        T = int(clamp(36 + dist / 12, 44, 70))  # זמן מעוף: קשת גבוהה שנופלת לתוך הסל
        g = self.BALL_G
        self.ball[2] = (tx - bx) / T
        self.ball[3] = (ty - by - g * T * (T + 1) / 2) / T
        self.holder = None
        self.last_shooter = name
        self.no_grab[name] = 25
        self.shot_points = 3 if dist >= self.THREE else 2

    def move_ball(self):
        b = self.ball
        prev_y = b[1]
        b[3] += self.BALL_G
        b[0] += b[2]
        b[1] += b[3]
        BR = self.BR
        # רצפה וקירות
        if b[1] + BR >= self.FLOOR:
            b[1] = self.FLOOR - BR
            b[3] = -b[3] * 0.7
            b[2] *= 0.9
            if abs(b[3]) < 1.2:
                b[3] = 0.0
        if b[0] < BR:
            b[0], b[2] = BR, abs(b[2]) * 0.7
        elif b[0] > self.W - BR:
            b[0], b[2] = self.W - BR, -abs(b[2]) * 0.7

        for side in (1, -1):
            board, front, cx = self.hoop(side)
            # לוח
            hit_board = False
            if self.BOARD_TOP - BR < b[1] < self.BOARD_BOTTOM + BR:
                if side > 0 and board - BR < b[0] < board + 8 and b[2] > 0:
                    b[0], b[2] = board - BR, -b[2] * 0.9 - 1.5
                    hit_board = True
                elif side < 0 and board - 8 < b[0] < board + BR and b[2] < 0:
                    b[0], b[2] = board + BR, -b[2] * 0.9 + 1.5
                    hit_board = True
            # קצה הטבעת (רק כשהכדור יורד, כדי שזריקה קרובה לא תיתקע בטבעת בדרך למעלה)
            ddx, ddy = b[0] - front, b[1] - self.RIM_Y
            d = math.hypot(ddx, ddy)
            if b[3] > 0 and 0 < d < BR + 3:
                nx, ny = ddx / d, ddy / d
                dot = b[2] * nx + b[3] * ny
                if dot < 0:
                    b[2] -= 1.6 * dot * nx
                    b[3] -= 1.6 * dot * ny
                b[0], b[1] = front + nx * (BR + 3), self.RIM_Y + ny * (BR + 3)
            # סל! הכדור עבר את הטבעת מלמעלה למטה
            lo, hi = sorted((board, front))
            if (not hit_board and b[3] > 0 and prev_y < self.RIM_Y <= b[1]
                    and lo + BR - 3 < b[0] < hi - BR + 3):
                self.basket(side)
                return

    def try_grab(self):
        for name, body in (("player", self.player), ("piko", self.piko)):
            if self.no_grab[name]:
                continue
            if math.hypot(self.ball[0] - body[0], self.ball[1] - body[1]) < self.PR + self.BR + 2:
                self.holder = name
                return

    def contact(self):
        """כשהשחקנים נתקלים הם נדחפים הצידה, ולפעמים הכדור נחטף."""
        a, b = self.player, self.piko
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        if d >= self.PR * 2:
            return
        push = (self.PR * 2 - d) / 2 * (1 if dx >= 0 else -1)
        a[0] = clamp(a[0] - push, self.PR + 6, self.W - self.PR - 6)
        b[0] = clamp(b[0] + push, self.PR + 6, self.W - self.PR - 6)
        if self.holder and not self.steal_cd:
            self.steal_cd = 45
            # לחטוף מפיקו קצת יותר קל מאשר שפיקו יחטוף ממך
            if random.random() < (0.35 if self.holder == "piko" else 0.2):
                loser = self.holder
                self.holder = "piko" if loser == "player" else "player"
                self.no_grab[loser] = 20
                self.piko_spot = None
                self.piko_jumpshot = False
                if self.holder == "piko":
                    self.say("חטפתי! מהיר כמו ברק ⚡", 90)
                    self.emotion.emit("laugh")
                else:
                    self.say("היי! זה הכדור שלי! ...איך עשית את זה?", 90)
                    self.emotion.emit("surprised")

    def basket(self, side):
        who = 0 if side > 0 else 1
        attacker = "player" if side > 0 else "piko"
        pts = self.shot_points if self.last_shooter == attacker else 2
        self.score[who] += pts
        self.ball[2] *= 0.3
        self.next_owner = "piko" if who == 0 else "player"
        you, piko = self.score
        if max(self.score) >= self.WIN:
            self.over = True
            if piko > you:
                self.say(f"פיקו ניצח {piko}-{you}! מלך המגרש, כמובן. 👑", 10 ** 9)
                self.emotion.emit("proud")
            else:
                self.say(f"ניצחת {you}-{piko}?! ...הסל שלי היה עקום. ברור.", 10 ** 9)
                self.emotion.emit("surprised")
            self.finished.emit(you, piko)
            return
        three = "שלשה! " if pts == 3 else ""
        if who == 1:
            self.say(three + random.choice(PIKO_BASKET_TAUNTS))
            self.emotion.emit(random.choice(["laugh", "proud"]))
        else:
            self.say(three + random.choice(PLAYER_BASKET_TAUNTS))
            self.emotion.emit(random.choice(["angry", "surprised"]))
        self.holder = None
        self.pause = 70

    # ---------- המוח של פיקו במגרש ----------
    def piko_ai(self):
        p = self.piko
        speed = 4.3
        jump = False
        if self.holder == "piko":
            board, front, cx = self.hoop(-1)
            if self.piko_spot is None:
                self.piko_spot = cx + random.choice([60, 120, 180, 250, 360])
                self.piko_hold = 0
            self.piko_hold += 1
            if self.piko_jumpshot:
                # באמצע זריקה בקפיצה: זורק בשיא הקפיצה
                target = p[0]
                if not self.on_ground(p) and p[3] >= -1:
                    self.piko_jumpshot = False
                    self.piko_shoot()
            else:
                target = self.piko_spot
                close = abs(p[0] - target) < 40
                if close:
                    self.piko_think -= 1
                # זורק כשהגיע לנקודה, כשאתה צמוד אליו, או אם מחזיק את הכדור יותר מדי זמן
                pressured = abs(self.player[0] - p[0]) < 70 and self.piko_hold > 30
                if (close and self.piko_think <= 0) or pressured or self.piko_hold > 100:
                    if self.on_ground(p) and random.random() < 0.6:
                        self.piko_jumpshot = True
                        jump = True
                    else:
                        self.piko_shoot()
        elif self.holder == "player":
            # מגן: עומד בינך לבין הסל הימני, וקופץ לחסום כשאתה קופץ
            pl = self.player
            target = pl[0] + 60
            speed = 3.6
            if abs(pl[0] - p[0]) < 90 and not self.on_ground(pl) and random.random() < 0.15:
                jump = True
        else:
            # כדור חופשי: רודף אחריו, וקופץ לריבאונד
            target = self.ball[0]
            near = math.hypot(self.ball[0] - p[0], self.ball[1] - p[1]) < 120
            if near and self.ball[1] < p[1] - 40 and random.random() < 0.1:
                jump = True
        p[2] = clamp((target - p[0]) * 0.25, -speed, speed)
        if jump and self.on_ground(p):
            p[3] = self.JUMP

    def piko_shoot(self):
        self.shoot("piko", -1)
        self.piko_spot = None
        self.piko_think = random.randint(15, 40)

    # ---------- ציור ----------
    def paint(self, p):
        W, H, F = self.W, self.H, self.FLOOR
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#12122a"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)

        # אולם וקהל
        p.fillRect(QRectF(0, 0, W, F), QColor("#283593"))
        p.setPen(Qt.NoPen)
        for row in range(3):
            for i in range(0, W, 22):
                p.setBrush(QColor.fromHsv((i * 7 + row * 50) % 360, 110, 230))
                p.drawEllipse(QPointF((i + 11 + row * 7) % W, 70 + row * 20), 6, 6)
        # פרקט
        p.fillRect(QRectF(0, F, W, H - F), QColor("#c98a4b"))
        p.setPen(QPen(QColor("#a86b33"), 1))
        for x in range(0, W, 40):
            p.drawLine(QPointF(x, F), QPointF(x, H))
        p.fillRect(QRectF(0, F, W, 4), QColor("#8d5524"))
        # קווי מגרש: אמצע וקו שלוש
        p.setPen(QPen(QColor(255, 255, 255, 210), 3))
        p.drawLine(QPointF(W / 2, F + 4), QPointF(W / 2, H))
        for side in (1, -1):
            cx = self.hoop(side)[2]
            x3 = cx - side * self.THREE
            p.drawLine(QPointF(x3, F + 4), QPointF(x3, H))

        for side in (1, -1):
            self.draw_hoop_back(p, side)

        # צללים על הרצפה
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        for obj, r in ((self.player, self.PR), (self.piko, self.PR), (self.ball, self.BR)):
            p.drawEllipse(QRectF(obj[0] - r, F - 4, r * 2, 8))

        # אתה (כחול), עם עיניים שמסתכלות על הכדור
        x, y = self.player[0], self.player[1]
        p.setPen(QPen(Qt.white, 3))
        p.setBrush(QColor("#1e88e5"))
        p.drawEllipse(QPointF(x, y), self.PR, self.PR)
        a = math.atan2(self.ball[1] - y, self.ball[0] - x)
        p.setPen(Qt.NoPen)
        for ex in (x - 7, x + 7):
            p.setBrush(Qt.white)
            p.drawEllipse(QPointF(ex, y - 4), 5, 6)
            p.setBrush(INK)
            p.drawEllipse(QPointF(ex + math.cos(a) * 2, y - 4 + math.sin(a) * 2), 2.5, 3)

        self.draw_piko(p)

        # כדור
        bx, by = self.ball[0], self.ball[1]
        p.setPen(QPen(QColor("#4e2600"), 1.5))
        p.setBrush(QColor("#ef6c00"))
        p.drawEllipse(QPointF(bx, by), self.BR, self.BR)
        p.drawLine(QPointF(bx - self.BR, by), QPointF(bx + self.BR, by))
        p.drawLine(QPointF(bx, by - self.BR), QPointF(bx, by + self.BR))

        # הטבעת והרשת אחרי הכדור, כדי שייראה שהוא נכנס לתוך הסל
        for side in (1, -1):
            self.draw_hoop_front(p, side)

        self.draw_scoreboard(p)
        self.draw_overlay(p, "חצים · ↑ קפיצה · רווח זריקה · R · Esc", msg_y=150)

    def draw_hoop_back(self, p, side):
        board, front, cx = self.hoop(side)
        pole_x = board + side * 16
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#607d8b"))
        p.drawRect(QRectF(pole_x - 4, self.BOARD_TOP + 40, 8, self.FLOOR - self.BOARD_TOP - 40))
        p.drawRect(QRectF(min(board, pole_x), self.BOARD_TOP + 50, abs(pole_x - board), 6))
        p.setPen(QPen(QColor("#e53935"), 2))
        p.setBrush(QColor("#fafafa"))
        p.drawRect(QRectF(board - 4, self.BOARD_TOP, 8, self.BOARD_BOTTOM - self.BOARD_TOP))

    def draw_hoop_front(self, p, side):
        board, front, cx = self.hoop(side)
        lo, hi = sorted((board, front))
        y, depth = self.RIM_Y, 34
        p.setPen(QPen(QColor(255, 255, 255, 210), 1.5))
        for i in range(5):
            t = i / 4
            p.drawLine(QPointF(lo + (hi - lo) * t, y), QPointF(lo + 10 + (hi - lo - 20) * t, y + depth))
        for j in (12, 24):
            shrink = 10 * j / depth
            p.drawLine(QPointF(lo + shrink, y + j), QPointF(hi - shrink, y + j))
        p.setPen(QPen(QColor("#ff5722"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(lo, y), QPointF(hi, y))


# ---------------------------------------------------------------- באולינג נגד פיקו
BOWL_LINES = {
    ("piko", "strike"): ["סטרייק! כמובן. נולדתי לבאולינג. 👑", "כל הפינים נפלו, בדיוק כמו כל המתחרים שלי!",
                         "סטרייק! תרשום, תצלם, תספר לחברים."],
    ("player", "strike"): ["סטרייק?! הפינים בטח היו עייפים.", "מה?! זה... מזל. ברור שזה מזל!",
                           "טוב, סטרייק. גם שעון עצור צודק פעמיים ביום."],
    ("piko", "spare"): ["ספייר! ניקיתי את המסלול כמו מקצוען.", "ספייר. כי הגאון תמיד מתקן."],
    ("player", "spare"): ["ספייר? לא רע... בשביל מתחיל.", "ספייר! אוקיי, אולי למדת משהו ממני."],
    ("piko", "gutter"): ["המסלול עקום! מישהו הזיז אותו, אני בטוח!", "זה לא נחשב, הכדור שלי החליק על שמן!"],
    ("player", "gutter"): ["חח! הכדור הלך לחפש את המרזב!", "אפס פינים! רוצה שאלמד אותך? בתשלום."],
    ("piko", "roll"): ["{n}. מצוין, כמו תמיד.", "{n}. חימום, עוד לא התחלתי באמת.", "{n}. תסתכל ותלמד."],
    ("player", "roll"): ["{n}. אני הייתי מפיל יותר.", "{n}. חמוד. ממש חמוד.", "{n}. לא רע, לא פיקו, אבל לא רע."],
}


def pins_text(n):
    return "פין אחד" if n == 1 else f"{n} פינים"


def bump(a, ra, ma, b, rb, mb):
    """התנגשות אלסטית בין שני עיגולים [x, y, vx, vy] עם רדיוסים ומסות."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy)
    if d == 0 or d >= ra + rb:
        return False
    nx, ny = dx / d, dy / d
    overlap = ra + rb - d
    total = ma + mb
    a[0] -= nx * overlap * mb / total
    a[1] -= ny * overlap * mb / total
    b[0] += nx * overlap * ma / total
    b[1] += ny * overlap * ma / total
    rv = (b[2] - a[2]) * nx + (b[3] - a[3]) * ny
    if rv < 0:
        j = -1.8 * rv / (1 / ma + 1 / mb)
        a[2] -= j * nx / ma
        a[3] -= j * ny / ma
        b[2] += j * nx / mb
        b[3] += j * ny / mb
    return True


class BowlingGame(FootballGame):
    """באולינג נגד פיקו, בתורות. 5 מסגרות, בכל מסגרת עד שני גלגולים.
    חצים למעלה/למטה בוחרים מיקום, רווח עוצר את חץ הכיוון, ורווח שוב עוצר את מד הכוח.
    ניקוד: כל פין שווה נקודה, סטרייק מוסיף 10 נקודות בונוס וספייר מוסיף 5."""

    W, H = 800, 500
    PR = 20                  # גודל הדמויות
    BR = 12                  # רדיוס הכדור
    PIN_R = 7
    X0, X1 = 30, 720         # תחילת המסלול וסופו (אחריו הבור)
    LT, LB = 180, 320        # הקצה העליון והתחתון של המסלול
    GUTTER = 14
    START_X = 85
    FOUL_X = 110
    HEAD_X = 590             # הפין הראשון
    FRAMES = 5
    MAX_ANGLE = 0.12

    def __init__(self):
        self.space = False
        super().__init__()
        self.setWindowTitle("באולינג נגד פיקו")

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.pause = 0
        self.rolls = {"player": [[]], "piko": []}
        self.frame_no = 1
        self.turn = "player"
        self.frame_done = False
        self.player = [0.0, 0.0, 0.0, 0.0]
        self.piko = [0.0, 0.0, 0.0, 0.0]
        self.rack()
        self.new_roll()
        self.say("פיקו: באולינג? אני מפיל פינים רק במבט! אתה מתחיל, שיהיה לך סיכוי. 😎", 200)
        self.emotion.emit("proud")

    def rack(self):
        """מסדר 10 פינים במשולש. כל פין: [x, y, vx, vy, x_בית, y_בית, נפל_עכשיו, הוסר]."""
        cy = (self.LT + self.LB) / 2
        self.pins = []
        for row in range(4):
            for i in range(row + 1):
                x = self.HEAD_X + row * 24
                y = cy + (i - row / 2) * 24
                self.pins.append([x, y, 0.0, 0.0, x, y, False, False])

    def new_roll(self):
        self.ball = [float(self.START_X), (self.LT + self.LB) / 2, 0.0, 0.0]
        self.ball_y0 = self.ball[1]
        self.in_gutter = False
        self.state = "pos"
        self.meter = 0
        self.angle = 0.0
        self.power = 0.0
        self.space = False
        self.roll_t = 0
        if self.turn == "piko":
            self.plan_piko()

    def plan_piko(self):
        """פיקו בוחר מאיפה לזרוק, לאן לכוון ובאיזה כוח (עם קצת טעויות)."""
        standing = [p for p in self.pins if not p[7]]
        cy = (self.LT + self.LB) / 2
        if len(standing) == 10:
            ty = cy + random.choice([-9, 9])  # "הכיס" ליד הפין הראשון
        else:
            ty = sum(p[1] for p in standing) / len(standing)
        self.piko_y = clamp(cy + random.uniform(-35, 35), self.LT + self.BR, self.LB - self.BR)
        aim = math.atan2(ty - self.piko_y, self.HEAD_X - self.START_X) + random.gauss(0, 0.03)
        limit = self.MAX_ANGLE * 0.95
        self.piko_angle = clamp(aim, -limit, limit)
        self.piko_power = clamp(random.gauss(0.72, 0.18), 0.25, 0.97)
        self.piko_wait = 35

    # ---------- מקלדת ----------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.space = True
        super().keyPressEvent(event)

    # ---------- לולאת המשחק ----------
    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        if not self.over:
            self.step()
        self.update()

    def step(self):
        k = self.keys
        mine = self.turn == "player"
        space, self.space = self.space, False
        b = self.ball
        if self.state == "pos":
            if mine:
                dy = (Qt.Key_Down in k or Qt.Key_S in k) - (Qt.Key_Up in k or Qt.Key_W in k)
                b[1] = clamp(b[1] + dy * 2.5, self.LT + self.BR, self.LB - self.BR)
                if space:
                    self.state, self.meter = "angle", 0
            else:
                d = self.piko_y - b[1]
                b[1] += clamp(d, -2, 2)
                if abs(d) < 1:
                    self.piko_wait -= 1
                    if self.piko_wait <= 0:
                        self.state, self.meter = "angle", 0
            self.ball_y0 = b[1]
        elif self.state == "angle":
            prev = self.angle
            self.meter += 1
            self.angle = math.sin(self.meter * 0.05) * self.MAX_ANGLE
            crossed = not mine and (prev - self.piko_angle) * (self.angle - self.piko_angle) <= 0
            if (mine and space) or (self.meter > 40 and crossed):
                self.state, self.meter = "power", 0
        elif self.state == "power":
            prev = self.power
            self.meter += 1
            self.power = 0.5 - 0.5 * math.cos(self.meter * 0.06)
            crossed = not mine and (prev - self.piko_power) * (self.power - self.piko_power) <= 0
            if (mine and space) or (self.meter > 30 and crossed):
                self.throw()
        elif self.state == "rolling":
            self.roll_physics()
        elif self.state == "after":
            self.wait -= 1
            if self.wait <= 0:
                self.next_roll()

    def throw(self):
        speed = 6 + self.power * 8
        self.ball[2] = speed * math.cos(self.angle)
        self.ball[3] = speed * math.sin(self.angle)
        self.state = "rolling"
        self.roll_t = 0

    def roll_physics(self):
        b = self.ball
        b[0] += b[2]
        b[1] += b[3]
        if not self.in_gutter and (b[1] < self.LT or b[1] > self.LB):
            # הכדור נפל למרזב: ממשיך ישר ולא נוגע בפינים
            self.in_gutter = True
            b[3] = 0.0
            b[1] = self.LT - self.GUTTER / 2 if b[1] < self.LT else self.LB + self.GUTTER / 2
        live = [p for p in self.pins if not p[7]]
        if not self.in_gutter:
            for pin in live:
                bump(b, self.BR, 5, pin, self.PIN_R, 1)
        for i, a in enumerate(live):
            for c in live[i + 1:]:
                bump(a, self.PIN_R, 1, c, self.PIN_R, 1)
        for pin in live:
            pin[0] += pin[2]
            pin[1] += pin[3]
            pin[2] *= 0.94
            pin[3] *= 0.94
            if math.hypot(pin[0] - pin[4], pin[1] - pin[5]) > 8:  # פין שזז מספיק נחשב שנפל
                pin[6] = True
            if pin[1] < self.LT - 2 or pin[1] > self.LB + 2 or pin[0] > self.X1:
                pin[6] = True
            # פין שעף נשאר בתוך המרזב ולא יוצא מהמסלול
            edge_top, edge_bottom = self.LT - self.GUTTER + 4, self.LB + self.GUTTER - 4
            if not edge_top <= pin[1] <= edge_bottom:
                pin[1] = clamp(pin[1], edge_top, edge_bottom)
                pin[3] = 0.0
        self.roll_t += 1
        moving = any(abs(p[2]) + abs(p[3]) > 0.05 for p in live)
        ball_done = b[0] > self.W + 20 or abs(b[2]) + abs(b[3]) < 0.1
        if (ball_done and not moving) or self.roll_t > 400:
            self.finish_roll()

    def finish_roll(self):
        mine = self.turn == "player"
        knocked = sum(1 for p in self.pins if p[6] and not p[7])
        for p in self.pins:
            if p[6]:
                p[7] = True
        frame = self.rolls[self.turn][-1]
        frame.append(knocked)
        standing = sum(1 for p in self.pins if not p[7])
        strike = len(frame) == 1 and knocked == 10
        spare = len(frame) == 2 and standing == 0
        self.score[0 if mine else 1] += knocked + (10 if strike else 5 if spare else 0)

        kind = "strike" if strike else "spare" if spare else "gutter" if knocked == 0 else "roll"
        line = random.choice(BOWL_LINES[(self.turn, kind)]).replace("{n}", pins_text(knocked))
        self.say(line, 110)
        emotions = {
            ("piko", "strike"): ["proud", "laugh"], ("player", "strike"): ["surprised", "angry"],
            ("piko", "spare"): ["proud", "happy"], ("player", "spare"): ["surprised"],
            ("piko", "gutter"): ["angry", "sad"], ("player", "gutter"): ["laugh"],
            ("piko", "roll"): ["proud", "happy"], ("player", "roll"): ["proud", "laugh"],
        }
        self.emotion.emit(random.choice(emotions[(self.turn, kind)]))

        self.frame_done = strike or len(frame) == 2
        self.state = "after"
        self.wait = 90 if (strike or spare) else 60

    def next_roll(self):
        if self.frame_done:
            if self.turn == "player":
                self.turn = "piko"
            else:
                self.turn = "player"
                self.frame_no += 1
                if self.frame_no > self.FRAMES:
                    self.end_game()
                    return
            self.rolls[self.turn].append([])
            self.rack()
        self.new_roll()

    def end_game(self):
        self.over = True
        self.frame_no = self.FRAMES
        you, piko = self.score
        if piko > you:
            self.say(f"פיקו ניצח {piko}-{you}! מלך המסלול, כמובן. 👑", 10 ** 9)
            self.emotion.emit("proud")
        elif you > piko:
            self.say(f"ניצחת {you}-{piko}?! ...הכדור שלי היה מרובע. ברור.", 10 ** 9)
            self.emotion.emit("surprised")
        else:
            self.say(f"תיקו {you}-{piko}! זה אומר שאתה כמעט גאון כמוני. כמעט.", 10 ** 9)
            self.emotion.emit("happy")
        self.finished.emit(you, piko)

    # ---------- ציור ----------
    def paint(self, p):
        W, H = self.W, self.H
        LT, LB, G = self.LT, self.LB, self.GUTTER
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#15131f"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)
        p.fillRect(QRectF(0, 0, W, H), QColor("#241f3a"))

        # מרזבים ומסלול
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8e8e9a"))
        p.drawRoundedRect(QRectF(self.X0, LT - G, self.X1 - self.X0, LB - LT + 2 * G), 8, 8)
        p.fillRect(QRectF(self.X0, LT, self.X1 - self.X0, LB - LT), QColor("#e9c58d"))
        p.setPen(QPen(QColor(150, 100, 50, 55), 1))
        for y in range(LT + 10, LB, 10):
            p.drawLine(QPointF(self.X0, y), QPointF(self.X1, y))
        p.setPen(QPen(QColor("#c62828"), 3))
        p.drawLine(QPointF(self.FOUL_X, LT), QPointF(self.FOUL_X, LB))
        # חיצי כיוון על המסלול
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8d5524"))
        for i in range(1, 6):
            y = LT + i * (LB - LT) / 6
            tri = QPainterPath(QPointF(300 + abs(3 - i) * 14, y - 5))
            tri.lineTo(312 + abs(3 - i) * 14, y)
            tri.lineTo(300 + abs(3 - i) * 14, y + 5)
            tri.closeSubpath()
            p.drawPath(tri)
        # סימוני מקום של הפינים
        p.setBrush(QColor(140, 90, 40, 90))
        for pin in self.pins:
            p.drawEllipse(QPointF(pin[4], pin[5]), 2.5, 2.5)

        # חץ כיוון
        if self.state in ("angle", "power"):
            pen = QPen(QColor("#ffd54f"), 3, Qt.DashLine, Qt.RoundCap)
            p.setPen(pen)
            bx, by = self.ball[0], self.ball[1]
            p.drawLine(QPointF(bx, by), QPointF(bx + math.cos(self.angle) * 160, by + math.sin(self.angle) * 160))

        # פינים
        for pin in self.pins:
            if pin[7]:
                continue
            if pin[6]:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(200, 200, 200, 200))
                p.drawEllipse(QPointF(pin[0], pin[1]), self.PIN_R + 2, self.PIN_R - 2)
            else:
                p.setPen(QPen(QColor("#9e9e9e"), 1))
                p.setBrush(Qt.white)
                p.drawEllipse(QPointF(pin[0], pin[1]), self.PIN_R, self.PIN_R)
                p.setPen(QPen(QColor("#e53935"), 2))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(pin[0], pin[1]), self.PIN_R - 3, self.PIN_R - 3)

        # כדור (כחול שלך, כתום של פיקו)
        bx, by = self.ball[0], self.ball[1]
        p.setPen(QPen(QColor(0, 0, 0, 120), 1.5))
        p.setBrush(QColor("#1565c0") if self.turn == "player" else QColor("#e64a19"))
        p.drawEllipse(QPointF(bx, by), self.BR, self.BR)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        for hx, hy in ((3, -4), (6, 1), (-1, 2)):
            p.drawEllipse(QPointF(bx + hx, by + hy), 1.8, 1.8)

        # הבור בסוף המסלול
        p.fillRect(QRectF(self.X1, LT - G - 10, W - self.X1, LB - LT + 2 * G + 20), QColor("#0d0b14"))

        # השחקנים: מי שבתור עומד ליד הכדור, השני מחכה בצד
        stand = [self.START_X - 45, self.ball_y0]
        bench = [70, 440]
        mine = self.turn == "player"
        self.player[:2] = stand if mine else bench
        self.piko[:2] = bench if mine else stand
        self.draw_bowler(p, self.player[0], self.player[1])
        self.draw_piko(p)

        # מד כוח
        if self.state == "power":
            bar = QRectF(self.X0, LB + G + 12, 220, 16)
            p.setPen(QPen(Qt.white, 2))
            p.setBrush(QColor(0, 0, 0, 120))
            p.drawRoundedRect(bar, 6, 6)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor.fromHsv(int(120 - 120 * self.power), 220, 240))
            p.drawRoundedRect(QRectF(bar.x() + 2, bar.y() + 2, (bar.width() - 4) * self.power, 12), 5, 5)

        # מסגרת ותור
        p.setPen(QColor("#e0e0e0"))
        p.setFont(QFont("Arial", 13, QFont.Bold))
        who = "התור שלך" if mine else "התור של פיקו"
        step_hint = {"pos": "בחר מיקום ולחץ רווח", "angle": "לחץ רווח לעצור את החץ",
                     "power": "לחץ רווח לעצור את הכוח"}.get(self.state, "")
        line = f"מסגרת {self.frame_no} מתוך {self.FRAMES} · {who}"
        if mine and step_hint:
            line += f" · {step_hint}"
        p.drawText(QRectF(0, 56, W, 24), Qt.AlignCenter, line)

        self.draw_sheet(p)
        self.draw_scoreboard(p)
        self.draw_overlay(p, "↑↓ מיקום · רווח · R · Esc", msg_y=96)

    def draw_bowler(self, p, x, y):
        r = self.PR
        p.setPen(QPen(Qt.white, 3))
        p.setBrush(QColor("#1e88e5"))
        p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(Qt.NoPen)
        for ex in (x - 6, x + 6):
            p.setBrush(Qt.white)
            p.drawEllipse(QPointF(ex, y - 3), 4.5, 5.5)
            p.setBrush(INK)
            p.drawEllipse(QPointF(ex + 1.5, y - 3), 2.2, 2.8)

    def draw_sheet(self, p):
        """טבלת הניקוד: X לסטרייק, / לספייר, - לאפס."""
        x0, y0, name_w, box_w, row_h = 170, 372, 64, 58, 36
        p.setFont(QFont("Arial", 13, QFont.Bold))
        for row, (who, label, color) in enumerate((("player", "אתה", "#90caf9"), ("piko", "פיקו", "#ffab91"))):
            y = y0 + row * (row_h + 8)
            p.setPen(QColor(color))
            p.drawText(QRectF(x0, y, name_w, row_h), Qt.AlignCenter, label)
            frames = self.rolls[who]
            for f in range(self.FRAMES):
                box = QRectF(x0 + name_w + f * box_w, y, box_w - 4, row_h)
                current = (not self.over and who == self.turn and f == len(frames) - 1)
                p.setPen(QPen(QColor("#ffd54f") if current else QColor(255, 255, 255, 120), 2 if current else 1))
                p.setBrush(QColor(0, 0, 0, 90))
                p.drawRoundedRect(box, 6, 6)
                if f < len(frames) and frames[f]:
                    r = frames[f]
                    p.setPen(Qt.white)
                    if r[0] == 10:
                        p.drawText(box, Qt.AlignCenter, "X")
                    else:
                        # כל גלגול בחצי משלו, כדי שהסדר יישאר משמאל לימין
                        half = box.width() / 2
                        left = QRectF(box.x(), box.y(), half, box.height())
                        right = QRectF(box.x() + half, box.y(), half, box.height())
                        p.drawText(left, Qt.AlignCenter, str(r[0] or "-"))
                        if len(r) > 1:
                            p.drawText(right, Qt.AlignCenter, "/" if r[0] + r[1] == 10 else str(r[1] or "-"))
            total = QRectF(x0 + name_w + self.FRAMES * box_w, y, 70, row_h)
            p.setPen(QPen(QColor(color), 2))
            p.setBrush(QColor(0, 0, 0, 120))
            p.drawRoundedRect(total, 6, 6)
            p.setPen(Qt.white)
            p.drawText(total, Qt.AlignCenter, str(self.score[row]))


# ---------------------------------------------------------------- קרב קונג פו נגד פיקו
# מכות: כמה פריימים עד שהמכה יוצאת, כמה זמן היא פוגעת, כמה זמן לחזור, טווח ונזק
ATTACKS = {
    "punch":   dict(start=4, active=4, recover=9, reach=64, dmg=7),
    "kick":    dict(start=6, active=5, recover=14, reach=84, dmg=11),
    "special": dict(start=14, active=1, recover=18, reach=0, dmg=16),
    "aim":     dict(start=44, active=1, recover=18, reach=0, dmg=8),    # פיקו מכוון את רובה הלייזר
}
SPARK_WORDS = ["פאו!", "בום!", "וואם!", "הייא!", "טראח!", "בנג!"]
KUNGFU_LINES = {
    "piko_round": ["נוק אאוט! תנועת הקונג פו הסודית של פיקו! 🥋", "סיבוב לפיקו! הברגים שלי עשויים מפלדה!",
                   "ראית את הבעיטה? למדתי אותה מעצמי, המורה הכי טוב בעולם."],
    "player_round": ["רגע, מה?! החלקתי על שמן מהברגים!", "טוב, נתתי לך את הסיבוב הזה. מתוך נדיבות. 😤",
                     "זה לא נחשב! האנטנה שלי נתקעה בתקרה!"],
    "piko_special": ["כדור צ'י של פיקו! 🔥", "הייא! קבל את כוח האנטנה!"],
    "player_special": ["כדור צ'י?! מאיפה למדת את זה?!", "אוי! זה היה חזק!"],
    "time": ["נגמר הזמן! הפינוק נגמר."],
    "power": ["אוי לא! הוא זוהר! מה אכלת בבוקר?! 😱", "כוח על?! זה לא הוגן! ...טוב, קצת הוגן.",
              "וואו, אתה בוער! אני... אני רק אתגונן רגע. 😰"],
    "dodge": ["התחמקת?! המשקפיים שלי היו מלוכלכים!", "מה?! איך התחמקת? אף אחד לא מתחמק מפיקו!",
              "פספסתי בכוונה. כדי שיהיה לך כיף."],
    "shot": ["פגיעה! המשקפיים האלה עוזרים לכוון. 😎", "בול! צלף הלייזר הכי טוב ביקום!"],
}


class Fighter:
    """לוחם אחד בקרב: מיקום, מהירות, חיים, אנרגיה ומה הוא עושה עכשיו."""

    def __init__(self, x, facing):
        self.x, self.y = float(x), float(KungFuGame.FLOOR)
        self.vx = self.vy = 0.0
        self.facing = facing
        self.hp = 100.0
        self.energy = 0.0
        self.state = "idle"     # idle / block / punch / kick / special / hit / ko / win
        self.t = 0
        self.hit_done = False
        self.walk = 0.0
        self.flash = 0
        self.aim_high = False   # לפיקו: האם הירייה הבאה גבוהה (להתכופף) או נמוכה (לקפוץ)
        self.aim_ang = math.pi  # זווית הרובה בעולם (ברדיאנים)
        self.power_t = 0        # כוח על פעיל (Enter): כמה פריימים נשארו
        self.power_cd = 0       # כמה זמן עד שאפשר להפעיל שוב

    @property
    def on_ground(self):
        return self.y >= KungFuGame.FLOOR - 0.5


class KungFuGame(FootballGame):
    """קרב קונג פו נגד פיקו. מי שמנצח 2 סיבובים מנצח בקרב.
    לפיקו יש משקפי שמש ורובה לייזר. לפני כל ירייה מופיע קו לייזר אדום:
    קו נמוך = קופצים מעליו, קו גבוה = מתכופפים מתחתיו (למטה).
    חצים או A/D לזוז, למעלה/W לקפוץ, למטה/S להתכופף ולהתגונן (להחזיק),
    Z או J אגרוף, X או K בעיטה, רווח לכדור צ'י (בלי טעינה, כדור אחד באוויר בכל פעם), R משחק חדש, Esc סוגר."""

    W, H = 800, 500
    FLOOR = 430
    WIN = 2
    ROUND_FRAMES = 60 * 60   # 60 שניות לסיבוב
    SPEED = 4.5
    # כמה פיקו חזק: סיכוי שיתגונן ממכה שלך, וסיכוי (בכל פריים) שיכה ראשון כשהוא נכנס לטווח
    BLOCK_CHANCE = 0.3
    FIRST_STRIKE = 0.1
    PIKO_POWER = 0.75        # המכות של פיקו חלשות משלך
    GUN_RELOAD = 120         # כמה זמן (בפריימים) לוקח לרובה להיטען
    POWER_FRAMES = 5 * 60    # כוח על (Enter) נמשך 5 שניות
    POWER_RECHARGE = 6 * 60  # ואז צריך לחכות 6 שניות
    POWER_MULT = 1.8         # המכות חזקות פי 1.8
    MAX_HANDICAP = 3         # עד כמה פיקו יכול "לתת הנחה" אחרי שהפסדת כמה פעמים

    def __init__(self):
        self.pressed = set()
        self.handicap = 0    # עולה כשאתה מפסיד, יורד כשאתה מנצח
        super().__init__()
        self.setWindowTitle("קרב קונג פו נגד פיקו")

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.round_no = 0
        # ההנחה של פיקו: כל דרגה מחלישה אותו קצת
        h = self.handicap
        self.block_base = max(0.08, self.BLOCK_CHANCE - 0.07 * h)
        self.first = self.FIRST_STRIKE * (1 - 0.25 * h)
        self.power = self.PIKO_POWER * (1 - 0.12 * h)
        self.reload = self.GUN_RELOAD + 30 * h
        self.laser = ATTACKS["aim"]["dmg"] * (1 - 0.12 * h)
        if h > 0:
            self.say(f"פיקו: טוב, אני נותן לך הנחה ({h} מתוך {self.MAX_HANDICAP}). אני אהיה קצת עצלן. 😏", 220)
        else:
            self.say("פיקו: משקפי שמש? יש. רובה לייזר? יש. נסה להתחמק! 😎", 220)
        self.emotion.emit("proud")
        self.shots = 0   # כמה יריות היו בקרב (לטיפים בהתחלה)
        self.new_round()

    def new_round(self):
        self.round_no += 1
        self.player = Fighter(220, 1)
        self.piko = Fighter(self.W - 220, -1)
        self.projectiles = []   # [x, y, vx, מי זרק]
        self.bullets = []       # קרני הלייזר של פיקו: [x, y, vx, עבר_אותך]
        self.gun_cd = self.gun_max = 150
        self.hopped, self.hop_wait = False, 0
        self.sparks = []        # [x, y, מילה, זמן]
        self.timer_left = self.ROUND_FRAMES
        self.freeze = 70        # "סיבוב 1... הילחם!"
        self.round_end = 0
        self.pressed.clear()
        self.ai_cd, self.ai_plan, self.ai_block, self.ai_seen = 30, "idle", 0, set()

    # ---------- מקלדת ----------
    def keyPressEvent(self, event):
        key = self.key_of(event)
        if not event.isAutoRepeat():
            self.pressed.add(key)
        super().keyPressEvent(event)

    def player_input(self):
        k, pr = self.keys, self.pressed
        return dict(
            left=Qt.Key_Left in k or Qt.Key_A in k,
            right=Qt.Key_Right in k or Qt.Key_D in k,
            jump=Qt.Key_Up in k or Qt.Key_W in k,
            block=Qt.Key_Down in k or Qt.Key_S in k,
            punch=bool(pr & {Qt.Key_Z, Qt.Key_J}),
            kick=bool(pr & {Qt.Key_X, Qt.Key_K}),
            special=Qt.Key_Space in pr,
            power=bool(pr & {Qt.Key_Return, Qt.Key_Enter}),
        )

    # ---------- לולאת המשחק ----------
    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        if not self.over:
            self.step()
        self.pressed.clear()
        self.update()

    def step(self):
        for f in (self.player, self.piko):
            f.flash = max(0, f.flash - 1)
        for s in self.sparks:
            s[1] -= 0.8
            s[3] -= 1
        self.sparks = [s for s in self.sparks if s[3] > 0]

        if self.freeze > 0:
            self.freeze -= 1
            return
        if self.round_end > 0:
            # הסיבוב נגמר: רק נותנים לאנימציה לרוץ
            for f, o in ((self.player, self.piko), (self.piko, self.player)):
                self.move_fighter(f, o, {})
            self.round_end -= 1
            if self.round_end == 0:
                self.after_round()
            return

        self.move_fighter(self.player, self.piko, self.player_input())
        self.move_fighter(self.piko, self.player, self.piko_input())
        self.separate()
        self.move_projectiles()
        self.move_bullets()

        self.timer_left -= 1
        if self.timer_left <= 0 and not self.round_end:
            self.say(random.choice(KUNGFU_LINES["time"]), 90)
            if self.player.hp == self.piko.hp:
                self.piko.hp -= 1  # במקרה של שוויון גמור, פיקו "מוותר" בנדיבות
            loser = self.player if self.player.hp < self.piko.hp else self.piko
            self.end_round(loser)

    def move_fighter(self, f, other, inp):
        # כוח על: Enter נותן מכות חזקות פי 1.8, כדור צ'י ענק ומהירות, ל-5 שניות
        if f.power_t > 0:
            f.power_t -= 1
            if f.power_t == 0:
                f.power_cd = self.POWER_RECHARGE
        elif f.power_cd > 0:
            f.power_cd -= 1
        elif inp.get("power") and f.state not in ("ko", "win"):
            f.power_t = self.POWER_FRAMES
            self.sparks.append([f.x, f.y - 130, "כוח על! ⚡", 50])
            if f is self.player:
                self.say(random.choice(KUNGFU_LINES["power"]), 90)
                self.emotion.emit("scared")
        if f.state not in ("ko", "win") and f.on_ground and f.state not in ATTACKS:
            f.facing = 1 if other.x > f.x else -1

        if f.state == "hit":
            f.t -= 1
            f.vx *= 0.85
            if f.t <= 0:
                f.state = "idle"
        elif f.state in ATTACKS:
            a = ATTACKS[f.state]
            f.t += 1
            if f.on_ground:
                f.vx = 0.0
            if f.state == "special" and f.t == a["start"]:
                self.projectiles.append([f.x + f.facing * 40, f.y - 58, f.facing * 8.5, f, f.power_t > 0])
            elif f.state == "aim":
                if f.t < a["start"] - 8:
                    self.aim_at(f, other)  # עוקב אחריך, ו-8 פריימים לפני הירייה הכיוון ננעל
                if f.t == a["start"]:
                    self.fire(f)
            elif a["start"] <= f.t < a["start"] + a["active"]:
                self.try_hit(f, other, f.state)
            if f.t >= a["start"] + a["active"] + a["recover"]:
                f.state = "idle"
        elif f.state in ("idle", "block"):
            if inp.get("block") and f.on_ground:
                f.state = "block"
                f.vx = 0.0
            else:
                f.state = "idle"
                move = inp.get("right", False) - inp.get("left", False)
                if f.on_ground:
                    f.vx = move * self.SPEED * (1.25 if f.power_t else 1)
                    if move:
                        f.walk += 0.3
                if inp.get("jump") and f.on_ground:
                    f.vy = -13.0
                if inp.get("aim") and f.on_ground:
                    self.start_attack(f, "aim")
                    f.aim_high = random.random() < 0.5
                elif inp.get("special") and f.on_ground and not self.chi_flying(f):
                    self.start_attack(f, "special")  # בלי טעינה: רק כדור צ'י אחד באוויר בכל פעם
                elif inp.get("kick"):
                    self.start_attack(f, "kick")
                elif inp.get("punch"):
                    self.start_attack(f, "punch")
        elif f.state == "ko":
            f.vx *= 0.9

        f.vy += 0.7
        f.x = clamp(f.x + f.vx, 40, self.W - 40)
        f.y += f.vy
        if f.y >= self.FLOOR:
            f.y, f.vy = float(self.FLOOR), 0.0

    def chi_flying(self, f):
        """האם כדור הצ'י של הלוחם הזה עדיין באוויר (או שהוא באמצע לזרוק אותו)."""
        return f.state == "special" or any(pr[3] is f for pr in self.projectiles)

    def start_attack(self, f, kind):
        f.state, f.t, f.hit_done = kind, 0, False

    def separate(self):
        a, b = self.player, self.piko
        dx = b.x - a.x
        if abs(dx) < 46 and abs(a.y - b.y) < 60:
            push = (46 - abs(dx)) / 2 * (1 if dx >= 0 else -1)
            a.x = clamp(a.x - push, 40, self.W - 40)
            b.x = clamp(b.x + push, 40, self.W - 40)

    def try_hit(self, att, dfd, kind):
        if att.hit_done or dfd.state == "ko":
            return
        a = ATTACKS[kind]
        dx = (dfd.x - att.x) * att.facing
        if 0 < dx < a["reach"] and abs(dfd.y - att.y) < 70:
            att.hit_done = True
            dmg = a["dmg"] + (2 if kind == "kick" and not att.on_ground else 0)  # בעיטה מעופפת
            if att is self.piko:
                dmg *= self.power
            if att.power_t:
                dmg *= self.POWER_MULT
            self.land_hit(att, dfd, dmg, att.x + att.facing * a["reach"] * 0.7, att.y - 55)

    def land_hit(self, att, dfd, dmg, sx, sy):
        blocked = dfd.state == "block" and dfd.facing == -att.facing
        if blocked:
            dfd.hp -= 1
            dfd.x = clamp(dfd.x + att.facing * 12, 40, self.W - 40)
            dfd.energy = min(100, dfd.energy + 4)
            self.sparks.append([sx, sy, "חסום!", 30])
        else:
            dfd.hp -= dmg
            dfd.state, dfd.t = "hit", 16
            dfd.vx = att.facing * (11 if att.power_t else 6)
            dfd.flash = 10
            att.energy = min(100, att.energy + 12)
            dfd.energy = min(100, dfd.energy + 7)
            self.sparks.append([sx, sy, random.choice(SPARK_WORDS), 35])
            if dfd is self.piko and random.random() < 0.25:
                self.emotion.emit(random.choice(["angry", "surprised"]))
            elif dfd is self.player and random.random() < 0.25:
                self.emotion.emit(random.choice(["laugh", "proud"]))
        if dfd.hp <= 0:
            dfd.hp = 0
            self.end_round(dfd)

    def move_projectiles(self):
        alive = []
        for pr in self.projectiles:
            pr[0] += pr[2]
            target = self.piko if pr[3] is self.player else self.player
            if abs(target.x - pr[0]) < 26 and target.y - 95 < pr[1] < target.y + 5 and target.state != "ko":
                big = len(pr) > 4 and pr[4]
                self.land_hit(pr[3], target, ATTACKS["special"]["dmg"] * (1.6 if big else 1), pr[0], pr[1])
                key = "piko_special" if pr[3] is self.piko else "player_special"
                self.say(random.choice(KUNGFU_LINES[key]), 70)
                continue
            if -30 < pr[0] < self.W + 30:
                alive.append(pr)
        # שני כדורי צ'י שנפגשים מתפוצצים
        for a in alive[:]:
            for b in alive[:]:
                if a is not b and a[3] is not b[3] and abs(a[0] - b[0]) < 24 and a in alive and b in alive:
                    alive.remove(a)
                    alive.remove(b)
                    self.sparks.append([(a[0] + b[0]) / 2, a[1], "בום!", 35])
        self.projectiles = alive

    # ---------- רובה הלייזר של פיקו ----------
    def gun_pivot(self, f):
        crouch = 18 if (f.state == "aim" and not f.aim_high) else 0
        return QPointF(f.x + f.facing * 8, f.y - 62 + crouch)

    def aim_at(self, f, target):
        """ירייה גבוהה מכוונת לגובה הראש שלך (גם כשאתה באוויר), ירייה נמוכה מכוונת לרגליים."""
        piv = self.gun_pivot(f)
        if f.aim_high:
            ty = clamp(target.y - 80, self.FLOOR - 220, self.FLOOR - 80)
        else:
            ty = self.FLOOR - 24
        dx = f.facing * max(140, abs(target.x - piv.x()))
        f.aim_ang = math.atan2(ty - piv.y(), dx)

    def gun_dir(self, f):
        return math.cos(f.aim_ang), math.sin(f.aim_ang)

    def muzzle(self, f):
        piv, (cx, cy) = self.gun_pivot(f), self.gun_dir(f)
        return QPointF(piv.x() + cx * 51, piv.y() + cy * 51)

    def fire(self, f):
        m, (cx, cy) = self.muzzle(f), self.gun_dir(f)
        self.bullets.append([m.x(), m.y(), cx * 13, False, cy * 13])
        self.shots += 1
        self.sparks.append([m.x() + cx * 10, m.y() - 14, "פיו!", 18])

    def move_bullets(self):
        pl = self.player
        crouch = pl.state == "block" and pl.on_ground
        top = pl.y - (66 if crouch else 98)
        alive = []
        for b in self.bullets:
            before = b[0] - pl.x
            b[0] += b[2]
            b[1] += b[4]
            # כדור צ'י שלך מפוצץ קרני לייזר
            if any(pr[3] is pl and abs(pr[0] - b[0]) < 22 and abs(pr[1] - b[1]) < 26 for pr in self.projectiles):
                self.sparks.append([b[0], b[1] - 10, "בזזט!", 30])
                continue
            if abs(b[0] - pl.x) < 16 and top - 4 < b[1] < pl.y + 2 and pl.state != "ko":
                if crouch and pl.facing == -int(math.copysign(1, b[2])):
                    pl.hp -= 4  # חסמת, אבל זה עדיין קצת כואב. עדיף להתחמק!
                    self.sparks.append([b[0], b[1] - 10, "חסום!", 30])
                else:
                    pl.hp -= self.laser
                    pl.state, pl.t = "hit", 12
                    pl.vx = math.copysign(4, b[2])
                    pl.flash = 10
                    self.sparks.append([b[0], b[1] - 10, "זאפ!", 35])
                    if random.random() < 0.4:
                        self.say(random.choice(KUNGFU_LINES["shot"]), 70)
                        self.emotion.emit("laugh")
                if pl.hp <= 0:
                    pl.hp = 0
                    self.end_round(pl)
                continue
            if not b[3] and before * (b[0] - pl.x) < 0:
                b[3] = True  # הקרן עברה אותך בלי לפגוע: התחמקת!
                self.sparks.append([pl.x, pl.y - 120, "התחמקת!", 40])
                pl.energy = min(100, pl.energy + 10)
                if random.random() < 0.35:
                    self.say(random.choice(KUNGFU_LINES["dodge"]), 70)
                    self.emotion.emit(random.choice(["angry", "surprised"]))
            if -30 < b[0] < self.W + 30 and -30 < b[1] < self.FLOOR:
                alive.append(b)
        self.bullets = alive

    def end_round(self, loser):
        if self.round_end:
            return
        winner = self.piko if loser is self.player else self.player
        loser.state, loser.vx, loser.vy = "ko", winner.facing * 5, -6
        winner.state = "win"
        self.projectiles.clear()
        self.bullets.clear()
        self.score[1 if winner is self.piko else 0] += 1
        self.round_end = 110
        if winner is self.piko:
            self.say(random.choice(KUNGFU_LINES["piko_round"]), 110)
            self.emotion.emit(random.choice(["laugh", "proud"]))
        else:
            self.say(random.choice(KUNGFU_LINES["player_round"]), 110)
            self.emotion.emit(random.choice(["angry", "surprised", "sad"]))

    def after_round(self):
        you, piko = self.score
        if max(self.score) >= self.WIN:
            self.over = True
            if piko > you:
                self.say(f"פיקו ניצח {piko}-{you}! מאסטר הקונג פו של היקום. 🥋👑", 10 ** 9)
                self.emotion.emit("proud")
                self.handicap = min(self.MAX_HANDICAP, self.handicap + 1)   # בקרב הבא הוא יותר קל
            else:
                self.say(f"ניצחת {you}-{piko}?! ...הייתי צריך לשמן את הברכיים. ברור.", 10 ** 9)
                self.emotion.emit("surprised")
                self.handicap = max(0, self.handicap - 1)   # בקרב הבא הוא מתאמץ יותר
            self.finished.emit(you, piko)
        else:
            self.new_round()

    # ---------- המוח של פיקו בקרב ----------
    def piko_input(self):
        me, you = self.piko, self.player
        inp = {}
        dist = abs(you.x - me.x)
        toward = "right" if you.x > me.x else "left"
        away = "left" if toward == "right" else "right"
        # כשפיקו מוביל הוא נהיה שחצן ועצלן, וכשהוא מפסיד הוא מתאמץ יותר. ככה הקרב נשאר צמוד.
        lead = (me.hp - you.hp) / 100 + 0.35 * (self.score[1] - self.score[0])
        cocky = clamp(lead, -0.3, 0.6)
        block_chance = clamp(self.block_base - cocky * 0.6, 0.05, 0.7)
        first_strike = clamp(self.first * (1 - cocky * 1.6), 0.0, 0.4)
        slack = int(max(0.0, cocky) * 30)
        self.gun_cd -= 1
        self.hop_wait -= 1
        if self.hop_wait <= 0:
            self.hopped = False  # אחרי שתי שניות מותר לנסות שוב לקפוץ אחורה
        if me.state not in ("idle", "block"):
            if me.state == "hit" and me.t == 1 and dist < 85 and random.random() < 0.5 - cocky * 0.5:
                self.ai_cd = 0  # מיד אחרי שספג מכה, פיקו מחזיר
            return inp

        # מגיב למכה שלך (פעם אחת לכל מכה), או לכדור צ'י שמגיע אליו
        if you.state in ("punch", "kick") and you.t <= 2 and dist < 110 and id(you) not in self.ai_seen:
            self.ai_seen.add(id(you))
            if random.random() < block_chance:
                self.ai_block = 14
        if you.state not in ("punch", "kick"):
            self.ai_seen.discard(id(you))
        for pr in self.projectiles:
            if pr[3] is you and id(pr) not in self.ai_seen and abs(pr[0] - me.x) < 190:
                self.ai_seen.add(id(pr))
                r = random.random()
                if r < 0.45:
                    inp["jump"] = True
                    inp[toward] = True
                elif r < 0.8:
                    self.ai_block = 30
        if self.ai_block > 0:
            self.ai_block -= 1
            inp["block"] = True
            if self.ai_block == 0 and dist < 85:
                self.ai_cd = 0  # אחרי הגנה, מתקפת נגד
            return inp

        self.ai_cd -= 1
        if you.state == "block" and dist < 90 and self.ai_cd <= 0 and random.random() < 0.6:
            # אתה מתגונן: פיקו לא מבזבז מכות, מחכה רגע ותוקף כשתוריד את הידיים
            self.ai_plan, self.ai_cd = "idle", random.randint(4, 10)
            return inp
        if self.ai_cd <= 0:
            r = random.random()
            near_wall = me.x < 90 or me.x > self.W - 90
            if self.gun_cd <= 0 and (dist > 100 or (near_wall and dist > 75)) and me.on_ground and r < 0.85:
                # יש מרחק והרובה טעון: מכוון ויורה
                inp["aim"] = True
                self.hopped = False
                self.gun_cd = self.gun_max = self.reload + random.randint(0, 60) + slack * 2
                self.ai_plan, self.ai_cd = "idle", 50
            elif self.gun_cd <= 0 and me.on_ground and not self.hopped and r < 0.35:
                # קרוב מדי: קפיצה אחת לאחור כדי לפנות מקום לירייה. אם לא עזר, ממשיך להילחם
                me.vx, me.vy = (-me.facing) * 8.0, -9.0
                self.ai_plan, self.ai_cd = "idle", 20
                self.hopped, self.hop_wait = True, 120
            elif dist < 80:
                if r < 0.55:
                    inp["punch"] = True
                elif r < 0.92:
                    inp["kick"] = True
                else:
                    self.ai_plan = "retreat"
                self.ai_cd = random.randint(6, 15) + slack
            elif dist < 110 and r < 0.35:
                inp["kick"] = True
                self.ai_cd = random.randint(14, 28)
            else:
                self.ai_plan = "approach" if r < 0.95 else "idle"
                if r < 0.08 and dist < 260:
                    inp["jump"] = True  # קפיצה קדימה לבעיטה מעופפת
                    self.ai_plan = "flying"
                self.ai_cd = random.randint(6, 14)

        if self.ai_plan == "approach" and dist < 80 and not inp and random.random() < first_strike:
            # נכנס לטווח: תוקף מיד, לפני שתספיק להכות ראשון
            inp["punch" if dist < 62 else "kick"] = True
            self.ai_cd = random.randint(6, 15)
        elif self.ai_plan in ("approach", "flying") and dist > 54:
            inp[toward] = True
        elif self.ai_plan == "retreat":
            inp[away] = True
        if self.ai_plan == "flying" and not me.on_ground and me.vy > -3 and dist < 110:
            inp["kick"] = True
            self.ai_plan = "idle"
        return inp

    # ---------- ציור ----------
    def paint(self, p):
        W, H, F = self.W, self.H, self.FLOOR
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1a120c"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)
        self.draw_dojo(p)

        for f in (self.piko, self.player):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 70))
            p.drawEllipse(QRectF(f.x - 30, F - 5, 60, 10))
        self.draw_aura(p, self.player)
        self.draw_fighter(p, self.player, False)
        self.draw_fighter(p, self.piko, True)
        self.draw_laser(p)
        self.draw_petals(p, time.time(), front=True)

        for pr in self.projectiles:
            big = len(pr) > 4 and pr[4]
            color = QColor("#ffd54f") if big else QColor("#4fc3f7") if pr[3] is self.player else QColor("#ffb74d")
            k = 1.6 if big else 1
            for i in range(4):
                c = QColor(color)
                c.setAlpha(70 - i * 15)
                p.setPen(Qt.NoPen)
                p.setBrush(c)
                p.drawEllipse(QPointF(pr[0] - pr[2] * i * 1.8, pr[1]), (20 - i * 3) * k, (20 - i * 3) * k)
            p.setBrush(Qt.white)
            p.drawEllipse(QPointF(pr[0], pr[1]), 7 * k, 7 * k)

        for b in self.bullets:
            for i in range(5):
                c = QColor("#ff1744")
                c.setAlpha(200 - i * 40)
                p.setPen(QPen(c, 6 - i, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(b[0] - b[2] * i * 0.6, b[1]), QPointF(b[0] - b[2] * (i + 1) * 0.6, b[1]))
            p.setPen(QPen(QColor("#ffebee"), 2, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(b[0], b[1]), QPointF(b[0] - b[2] * 0.8, b[1]))

        for x, y, word, life in self.sparks:
            p.setFont(QFont("Arial", 20, QFont.Black))
            alpha = int(255 * min(1, life / 15))
            p.setPen(QColor(60, 20, 0, alpha))
            p.drawText(QRectF(x - 60 + 2, y - 20 + 2, 120, 40), Qt.AlignCenter, word)
            p.setPen(QColor(255, 235, 59, alpha))
            p.drawText(QRectF(x - 60, y - 20, 120, 40), Qt.AlignCenter, word)

        self.draw_bars(p)
        self.draw_scoreboard(p)

        if self.freeze > 0 and not self.over:
            p.setFont(QFont("Arial", 40, QFont.Black))
            text = f"סיבוב {self.round_no}" if self.freeze > 30 else "הילחם!"
            p.setPen(QColor(0, 0, 0, 160))
            p.drawText(QRectF(3, 183, W, 70), Qt.AlignCenter, text)
            p.setPen(QColor("#ffeb3b"))
            p.drawText(QRectF(0, 180, W, 70), Qt.AlignCenter, text)
        elif self.round_end > 0 and not self.over:
            p.setFont(QFont("Arial", 44, QFont.Black))
            text = "נגמר הזמן!" if self.timer_left <= 0 else "נוק אאוט!"
            p.setPen(QColor(0, 0, 0, 160))
            p.drawText(QRectF(3, 183, W, 70), Qt.AlignCenter, text)
            p.setPen(QColor("#ff5252"))
            p.drawText(QRectF(0, 180, W, 70), Qt.AlignCenter, text)

        self.draw_overlay(p, "חצים · ↑ קפיצה · ↓ הגנה · Z אגרוף · X בעיטה · רווח כדור צ'י · Enter כוח על · R · Esc",
                          msg_y=108, hint_y=H - 28)

    def draw_aura(self, p, f):
        """הילה זהובה ולהבות סביב לוחם עם כוח על."""
        if f.power_t <= 0 or f.state == "ko":
            return
        t = time.time()
        fade = min(1, f.power_t / 30)
        for i, (color, size) in enumerate((("#ffeb3b", 1.0), ("#ff9800", 0.75))):
            c = QColor(color)
            c.setAlpha(int((100 + 50 * math.sin(t * 12 + i)) * fade))
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawEllipse(QPointF(f.x, f.y - 52), 42 * size, 66 * size)
        p.setBrush(QColor(255, 235, 59, int(200 * fade)))
        for i in range(7):
            a = t * 4 + i * 0.9
            fx = f.x + math.cos(a) * 30
            fy = f.y - 52 + math.sin(a) * 50
            flame = QPainterPath(QPointF(fx - 5, fy))
            flame.quadTo(fx, fy - 18 - 6 * math.sin(t * 15 + i), fx + 5, fy)
            flame.closeSubpath()
            p.drawPath(flame)

    def draw_laser(self, p):
        """קו לייזר אדום שמראה איפה פיקו עומד לירות, ואזהרה מעל הראש שלך."""
        f = self.piko
        if f.state != "aim" or f.t >= ATTACKS["aim"]["start"]:
            return
        frac = f.t / ATTACKS["aim"]["start"]
        m, (cx, cy) = self.muzzle(f), self.gun_dir(f)
        blink = 0.5 + 0.5 * math.sin(f.t * (0.4 + frac * 0.8))
        c = QColor("#ff1744")
        c.setAlpha(int(60 + 140 * frac * blink))
        p.setPen(QPen(c, 2 + frac * 2, Qt.DashLine if frac < 0.6 else Qt.SolidLine))
        p.drawLine(m, QPointF(m.x() + cx * 900, m.y() + cy * 900))
        # סימן קריאה מעל פיקו
        p.setFont(QFont("Arial", 26, QFont.Black))
        p.setPen(QColor("#ff1744"))
        p.drawText(QRectF(f.x - 20, f.y - 150, 40, 40), Qt.AlignCenter, "!")
        # בהתחלה: טיפ מעל הראש שלך מה לעשות
        if self.shots < 4:
            pl = self.player
            tip = "התכופף! ↓" if f.aim_high else "קפוץ! ↑"
            box = QRectF(pl.x - 60, pl.y - 150, 120, 30)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 170))
            p.drawRoundedRect(box, 10, 10)
            p.setFont(QFont("Arial", 15, QFont.Bold))
            p.setPen(QColor("#ffeb3b"))
            p.drawText(box, Qt.AlignCenter, tip)

    def draw_dojo(self, p):
        """גן יפני בשקיעה: עץ דובדבן ורוד, בית יפני, הר מושלג ועלי פריחה שנושרים."""
        W, H, F = self.W, self.H, self.FLOOR
        t = time.time()
        # שמיים ושמש של שקיעה
        sky = QLinearGradient(0, 0, 0, F)
        sky.setColorAt(0.0, QColor("#ff9ec4"))
        sky.setColorAt(0.55, QColor("#ffc9b5"))
        sky.setColorAt(1.0, QColor("#ffe8cc"))
        p.fillRect(QRectF(0, 0, W, F), sky)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawEllipse(QPointF(430, 250), 90, 90)
        p.setBrush(QColor("#fff3e0"))
        p.drawEllipse(QPointF(430, 250), 58, 58)
        # עננים
        p.setBrush(QColor(255, 255, 255, 150))
        for cx, cy, k in ((180, 120, 1.0), (620, 100, 0.8), (380, 150, 0.6)):
            drift = math.sin(t * 0.1 + cx) * 10
            for dx, dy, r in ((-30, 6, 22), (0, 0, 30), (32, 6, 24)):
                p.drawEllipse(QPointF(cx + drift + dx * k, cy + dy * k), r * k * 1.3, r * k)
        # הר מושלג רחוק
        mountain = QPainterPath(QPointF(170, 345))
        mountain.lineTo(400, 175)
        mountain.lineTo(640, 345)
        mountain.closeSubpath()
        p.setBrush(QColor("#b39ddb"))
        p.drawPath(mountain)
        snow = QPainterPath(QPointF(400, 175))
        snow.lineTo(452, 213)
        snow.lineTo(432, 222)
        snow.lineTo(412, 210)
        snow.lineTo(392, 224)
        snow.lineTo(370, 212)
        snow.lineTo(348, 213)
        snow.closeSubpath()
        p.setBrush(QColor("#fafafa"))
        p.drawPath(snow)
        # גבעות ירוקות
        p.setBrush(QColor("#9ccc65"))
        hills = QPainterPath(QPointF(0, F))
        hills.lineTo(0, 352)
        hills.quadTo(200, 318, 400, 348)
        hills.quadTo(600, 375, W, 335)
        hills.lineTo(W, F)
        hills.closeSubpath()
        p.drawPath(hills)
        self.draw_house(p)
        self.draw_sakura(p, t)
        # דשא ושביל אבנים
        p.fillRect(QRectF(0, F, W, H - F), QColor("#7cb342"))
        p.fillRect(QRectF(0, F, W, 5), QColor("#558b2f"))
        p.setBrush(QColor("#cfd8dc"))
        for x in range(30, W, 95):
            p.drawEllipse(QPointF(x, F + 22), 30, 9)
        p.setPen(QPen(QColor("#689f38"), 2, Qt.SolidLine, Qt.RoundCap))
        for x in range(10, W, 23):
            p.drawLine(QPointF(x, F + 3), QPointF(x - 3, F - 6 - (x * 7) % 5))
        self.draw_petals(p, t, front=False)

    def draw_house(self, p):
        """בית יפני מעץ עם קירות נייר, גג מעוקל ופנס אדום."""
        F = self.FLOOR
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5d4037"))
        p.drawRect(QRectF(540, 330, 230, 14))                      # מרפסת
        for x in (548, 620, 690, 760):
            p.drawRect(QRectF(x, 344, 8, F - 344))                 # עמודים
        p.setBrush(QColor("#fff8e1"))
        p.drawRect(QRectF(556, 252, 198, 78))                      # קירות נייר
        p.setPen(QPen(QColor("#8d6e63"), 2))
        for x in range(556, 755, 22):
            p.drawLine(QPointF(x, 252), QPointF(x, 330))
        for y in (272, 292, 312):
            p.drawLine(QPointF(556, y), QPointF(754, y))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4e342e"))
        p.drawRect(QRectF(636, 262, 40, 68))                       # דלת הזזה פתוחה
        p.setBrush(QColor("#6d4c41"))
        p.drawRect(QRectF(550, 246, 210, 8))
        # גג עם קצוות שמתעקמים למעלה
        roof = QPainterPath(QPointF(520, 236))
        roof.quadTo(560, 250, 600, 214)
        roof.lineTo(710, 214)
        roof.quadTo(750, 250, 790, 236)
        roof.lineTo(800, 252)
        roof.quadTo(655, 268, 510, 252)
        roof.closeSubpath()
        p.setBrush(QColor("#37474f"))
        p.drawPath(roof)
        top = QPainterPath(QPointF(590, 216))
        top.quadTo(655, 160, 720, 216)
        top.closeSubpath()
        p.setBrush(QColor("#455a64"))
        p.drawPath(top)
        p.setBrush(QColor("#263238"))
        p.drawRect(QRectF(600, 210, 110, 7))
        # פנס אדום מתנדנד
        swing = math.sin(time.time() * 2) * 3
        p.setPen(QPen(QColor("#3e2723"), 2))
        p.drawLine(QPointF(565, 252), QPointF(565 + swing, 272))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#e53935"))
        p.drawRoundedRect(QRectF(553 + swing, 272, 24, 32), 10, 10)
        p.setBrush(QColor("#ffcc80"))
        p.drawRoundedRect(QRectF(559 + swing, 278, 12, 20), 5, 5)

    def draw_sakura(self, p, t):
        """עץ דובדבן ורוד בפריחה."""
        sway = math.sin(t * 0.8) * 2
        wood = QColor("#5d4037")
        p.setPen(QPen(wood, 22, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        trunk = QPainterPath(QPointF(118, self.FLOOR + 2))
        trunk.cubicTo(110, 380, 140, 320, 128, 262)
        p.setBrush(Qt.NoBrush)
        p.drawPath(trunk)
        branches = [((128, 262), (60, 205), 12), ((128, 262), (215, 200), 12), ((128, 270), (40, 270), 8),
                    ((132, 250), (150, 160), 10), ((200, 205), (290, 230), 7), ((70, 210), (30, 170), 6)]
        for (x1, y1), (x2, y2), w in branches:
            p.setPen(QPen(wood, w, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x1, y1), QPointF(x2 + sway, y2))
        rnd = random.Random(5)
        p.setPen(Qt.NoPen)
        for cx, cy, spread, n in ((60, 200, 50, 14), (215, 195, 55, 15), (150, 150, 55, 16),
                                  (290, 228, 35, 9), (38, 268, 34, 8), (30, 165, 30, 7)):
            for _ in range(n):
                x = cx + rnd.uniform(-spread, spread) + sway
                y = cy + rnd.uniform(-spread * 0.6, spread * 0.6)
                r = rnd.uniform(13, 24)
                p.setBrush(QColor(rnd.choice(["#f8bbd0", "#f48fb1", "#fce4ec", "#f06292"])))
                p.drawEllipse(QPointF(x, y), r, r * 0.85)

    def draw_petals(self, p, t, front):
        """עלי פריחה ורודים שנושרים ומסתובבים ברוח."""
        rnd = random.Random(11 if front else 7)
        count = 10 if front else 26
        p.setPen(Qt.NoPen)
        for i in range(count):
            speed = rnd.uniform(18, 34)
            phase = rnd.uniform(0, 1000)
            x0 = rnd.uniform(-60, self.W)
            y = (t * speed + phase) % (self.H + 40) - 20
            x = (x0 + y * 0.35 + math.sin(t * 1.5 + i) * 18) % (self.W + 60) - 30
            ang = (t * rnd.uniform(60, 140) + phase) % 360
            size = rnd.uniform(4, 7) * (1.3 if front else 1)
            p.save()
            p.translate(x, y)
            p.rotate(ang)
            p.setBrush(QColor(rnd.choice(["#f8bbd0", "#f48fb1", "#ffffff"])))
            p.drawEllipse(QPointF(0, 0), size, size * 0.55)
            p.restore()

    def draw_bars(self, p):
        W = self.W
        for f, x0, name, right in ((self.player, 16, "אתה", False), (self.piko, W - 262, "פיקו", True)):
            w = 246
            p.setPen(QPen(Qt.white, 2))
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRoundedRect(QRectF(x0, 12, w, 22), 6, 6)
            frac = clamp(f.hp / 100, 0, 1)
            color = QColor.fromHsv(int(120 * frac), 210, 230)
            fill = (w - 4) * frac
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            fx = x0 + 2 + (w - 4 - fill if right else 0)
            p.drawRoundedRect(QRectF(fx, 14, fill, 18), 5, 5)
            p.setPen(Qt.white)
            p.setFont(QFont("Arial", 11, QFont.Bold))
            p.drawText(QRectF(x0 + 8, 12, w - 16, 22),
                       (Qt.AlignRight if right else Qt.AlignLeft) | Qt.AlignVCenter, name)
            if f is self.piko:
                # במקום כדור צ'י, לפיקו יש רובה: הפס מראה כמה הוא טעון
                charge = clamp(1 - self.gun_cd / max(1, self.gun_max), 0, 1)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 130))
                p.drawRoundedRect(QRectF(x0, 38, w, 9), 4, 4)
                p.setBrush(QColor("#ff1744"))
                e = (w - 2) * charge
                p.drawRoundedRect(QRectF(x0 + 1 + (w - 2 - e), 39, e, 7), 3, 3)
                if charge >= 1:
                    p.setPen(QColor("#b71c1c"))
                    p.setFont(QFont("Arial", 10, QFont.Bold))
                    p.drawText(QRectF(x0, 48, w, 16), Qt.AlignRight | Qt.AlignVCenter, "🕶 הרובה טעון!")
                continue
            # כדור צ'י: תמיד מוכן, חוץ מכשהכדור הקודם עוד באוויר
            ready = not self.chi_flying(f)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 130))
            p.drawRoundedRect(QRectF(x0, 38, w, 9), 4, 4)
            c = QColor("#4dd0e1")
            c.setAlphaF(0.6 + 0.4 * abs(math.sin(time.time() * 6)) if ready else 0.25)
            p.setBrush(c)
            p.drawRoundedRect(QRectF(x0 + 1, 39, w - 2, 7), 3, 3)
            chi_pill = QRectF(x0, 50, 168, 18)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 140))
            p.drawRoundedRect(chi_pill, 7, 7)
            p.setPen(QColor("#80deea") if ready else QColor("#9e9e9e"))
            p.setFont(QFont("Arial", 10, QFont.Bold))
            p.drawText(chi_pill.adjusted(6, 0, -6, 0), Qt.AlignLeft | Qt.AlignVCenter,
                       "כדור צ'י מוכן! (רווח)" if ready else "כדור צ'י באוויר...")
            # כוח על (Enter)
            if f.power_t > 0:
                text, color = f"⚡ כוח על! {math.ceil(f.power_t / 60)}", QColor("#ffeb3b")
            elif f.power_cd > 0:
                text, color = f"⚡ כוח על נטען... {math.ceil(f.power_cd / 60)}", QColor("#9e9e9e")
            else:
                text, color = "⚡ כוח על מוכן! (Enter)", QColor("#ffd54f")
            pill = QRectF(x0, 71, 168, 18)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 140))
            p.drawRoundedRect(pill, 7, 7)
            p.setPen(color)
            p.drawText(pill.adjusted(6, 0, -6, 0), Qt.AlignLeft | Qt.AlignVCenter, text)
        # שעון וסיבוב
        secs = max(0, math.ceil(self.timer_left / 60))
        pill = QRectF(W / 2 - 70, 54, 140, 22)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(pill, 8, 8)
        p.setPen(QColor("#ffeb3b") if secs <= 10 else Qt.white)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(pill, Qt.AlignCenter, f"סיבוב {self.round_no}  ·  ⏱ {secs}")

    def draw_fighter(self, p, f, is_piko):
        x, y, d = f.x, f.y, f.facing
        flash = f.flash and f.flash % 4 < 2
        body = QColor("#ffffff") if flash else (HEAD_DARK if is_piko else QColor("#1565c0"))
        if f.state == "ko":
            self.draw_ko(p, f, is_piko, body)
            return
        t = time.time()
        bob = math.sin(t * 5 + (1 if is_piko else 0)) * 1.5 if f.state == "idle" and f.on_ground else 0
        lean = {"hit": -6, "punch": 4, "kick": -5, "special": 3}.get(f.state, 0) * d
        # מתכופף: בהגנה, ופיקו כשהוא כורע לירייה נמוכה
        crouch = 18 if f.on_ground and (f.state == "block" or (f.state == "aim" and not f.aim_high)) else 0
        bob += crouch
        hip = QPointF(x, y - 34 + bob)
        neck = QPointF(x + lean, y - 64 + bob)
        head = QPointF(x + lean * 1.3, y - 82 + bob)
        shoulder = QPointF(x + lean, y - 60 + bob)
        aiming = is_piko and f.state == "aim"
        if is_piko:
            self.draw_fighter_back(p, neck, hip, d)
        if is_piko and not aiming:
            self.draw_rifle(p, QPointF(x - d * 2, y - 50 + bob), d, -58)  # הרובה תלוי על הגב

        # רגליים
        if not f.on_ground:
            front, back = QPointF(x + d * 16, y - 14), QPointF(x - d * 10, y - 6)
        elif f.state == "idle" and abs(f.vx) > 0.1:
            sw = math.sin(f.walk) * 9
            front, back = QPointF(x + d * 15 + sw, y), QPointF(x - d * 14 - sw, y)
        else:
            front, back = QPointF(x + d * 17, y), QPointF(x - d * 15, y)
        # ידיים
        fist_f, fist_b = QPointF(x + d * 24, y - 60 + bob), QPointF(x + d * 12, y - 52 + bob)
        s, a = f.state, ATTACKS.get(f.state)
        if s == "punch":
            if f.t < a["start"]:
                fist_f = QPointF(x + d * 12, y - 60)
            elif f.t < a["start"] + a["active"] + 3:
                fist_f = QPointF(x + d * 52, y - 62)
        elif s == "kick":
            if f.t < a["start"]:
                front = QPointF(x + d * 22, y - 26)
            elif f.t < a["start"] + a["active"] + 3:
                front = QPointF(x + d * 62, y - 52 if f.on_ground else y - 36)
            else:
                front = QPointF(x + d * 20, y - 14)
        elif s == "block":
            fist_f, fist_b = QPointF(x + d * 20, y - 80 + crouch), QPointF(x + d * 24, y - 64 + crouch)
        elif s == "aim":
            piv, (cx, cy) = self.gun_pivot(f), self.gun_dir(f)
            recoil = -6 if a["start"] < f.t < a["start"] + 6 else 0  # רתע של הרובה
            fist_f = QPointF(piv.x() + cx * (26 + recoil), piv.y() + cy * (26 + recoil) + 4)
            fist_b = QPointF(piv.x() + cx * (2 + recoil), piv.y() + cy * (2 + recoil) + 5)
        elif s == "special":
            if f.t < a["start"]:
                fist_f, fist_b = QPointF(x - d * 8, y - 46), QPointF(x - d * 4, y - 40)
            else:
                fist_f, fist_b = QPointF(x + d * 40, y - 62), QPointF(x + d * 40, y - 52)
        elif s == "hit":
            fist_f, fist_b = QPointF(x - d * 6, y - 78), QPointF(x + d * 10, y - 80)
        elif s == "win":
            fist_f, fist_b = QPointF(x - 14, y - 108), QPointF(x + 14, y - 108)

        pen = QPen(body, 9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        for foot in (back, front):
            knee = QPointF((hip.x() + foot.x()) / 2 + d * 7, (hip.y() + foot.y()) / 2 - 3)
            path = QPainterPath(hip)
            path.lineTo(knee)
            path.lineTo(foot)
            p.drawPath(path)
        p.setPen(QPen(body, 14, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hip, neck)
        if is_piko:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffd54f"))
            p.drawEllipse(QPointF((hip.x() + neck.x()) / 2, (hip.y() + neck.y()) / 2), 4, 4)
        else:
            p.setPen(QPen(INK, 4))  # חגורה שחורה
            p.drawLine(QPointF(hip.x() - 8, hip.y() - 2), QPointF(hip.x() + 8, hip.y() - 2))
        p.setPen(QPen(body, 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for fist in (fist_b, fist_f):
            elbow = QPointF((shoulder.x() + fist.x()) / 2, (shoulder.y() + fist.y()) / 2 + 6)
            path = QPainterPath(shoulder)
            path.lineTo(elbow)
            path.lineTo(fist)
            p.drawPath(path)
        if aiming:
            cx, cy = self.gun_dir(f)
            piv = self.gun_pivot(f)
            recoil = -6 if ATTACKS["aim"]["start"] < f.t < ATTACKS["aim"]["start"] + 6 else 0
            self.draw_rifle(p, QPointF(piv.x() + cx * recoil, piv.y() + cy * recoil), d,
                            math.degrees(math.atan2(cy, abs(cx))))
        p.setPen(Qt.NoPen)
        p.setBrush(FACE if is_piko else QColor("#ffe0b2"))
        for fist in (fist_b, fist_f):
            p.drawEllipse(fist, 6, 6)
        if is_piko:
            self.draw_robot_head(p, head, d, f)
        else:
            self.draw_player_head(p, head, d, f)

    def draw_player_head(self, p, c, d, f):
        p.setPen(QPen(Qt.white, 2))
        p.setBrush(QColor("#1e88e5"))
        p.drawEllipse(c, 16, 16)
        # סרט אדום על הראש, עם קצוות שמתנופפים מאחור
        wave = math.sin(time.time() * 9) * 3
        p.setPen(QPen(QColor("#e53935"), 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(c.x() - 15, c.y() - 7), QPointF(c.x() + 15, c.y() - 7))
        p.drawLine(QPointF(c.x() - d * 15, c.y() - 7), QPointF(c.x() - d * 28, c.y() - 2 + wave))
        p.drawLine(QPointF(c.x() - d * 15, c.y() - 7), QPointF(c.x() - d * 26, c.y() + 5 - wave))
        p.setPen(Qt.NoPen)
        if f.state == "hit":
            p.setPen(QPen(INK, 2.5, Qt.SolidLine, Qt.RoundCap))
            for ex in (c.x() + d * 1, c.x() + d * 9):
                p.drawLine(QPointF(ex - 3, c.y() - 1), QPointF(ex + 3, c.y() + 3))
                p.drawLine(QPointF(ex + 3, c.y() - 1), QPointF(ex - 3, c.y() + 3))
            return
        for ex in (c.x() + d * 1, c.x() + d * 9):
            p.setBrush(Qt.white)
            p.drawEllipse(QPointF(ex, c.y() + 1), 4, 5)
            p.setBrush(INK)
            p.drawEllipse(QPointF(ex + d * 1.5, c.y() + 1), 2, 2.6)

    def draw_robot_head(self, p, c, d, f):
        r = 18
        p.setPen(QPen(BOLT, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(c.x(), c.y() - r), QPointF(c.x(), c.y() - r - 10))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ff5252") if f.state in ("hit", "ko") else QColor("#ffd54f"))
        p.drawEllipse(QPointF(c.x(), c.y() - r - 12), 4, 4)
        p.setPen(QPen(HEAD_DARK, 3))
        p.setBrush(HEAD)
        p.drawEllipse(c, r, r)
        p.setPen(Qt.NoPen)
        p.setBrush(FACE)
        p.drawEllipse(QPointF(c.x() + d * 3, c.y() + 2), r * 0.72, r * 0.62)
        ex0 = c.x() + d * 3
        knocked = f.state in ("hit", "ko")
        if knocked:
            # המשקפיים החליקו, ורואים עיניים מסוחררות
            p.setPen(QPen(INK, 2.5, Qt.SolidLine, Qt.RoundCap))
            for ex in (ex0 - 6, ex0 + 6):
                p.drawLine(QPointF(ex - 3, c.y() - 3), QPointF(ex + 3, c.y() + 1))
                p.drawLine(QPointF(ex + 3, c.y() - 3), QPointF(ex - 3, c.y() + 1))
        outfit = current_outfit()
        if outfit.get("glasses") and not knocked:
            draw_accessories(p, {"glasses": outfit["glasses"]}, c.x(), c.y(), r, eye_y=-0.1, eye_dx=d * 3 / r)
        else:
            self.draw_shades(p, QPointF(ex0, c.y() + (6 if knocked else -2)), 14 if knocked else 0)
        draw_accessories(p, outfit, c.x(), c.y(), r, top=-0.95, neck_y=0.95, t=time.time(),
                         skip=("glasses",))
        mouth = QPainterPath(QPointF(ex0 - 6, c.y() + 7))
        mouth.quadTo(ex0, c.y() + (12 if f.state != "hit" else 4), ex0 + 7, c.y() + 5)
        p.setPen(QPen(INK, 2, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(mouth)

    def draw_fighter_back(self, p, neck, hip, d):
        """גלימה או כנפיים של פיקו בקרב, מאחורי הגוף."""
        back = current_outfit().get("back")
        t = time.time()
        if back == "cape":
            wave = math.sin(t * 6) * 5
            cape = QPainterPath(QPointF(neck.x() + d * 4, neck.y() + 2))
            cape.quadTo(neck.x() - d * 26, neck.y() + 30, neck.x() - d * (34 + wave), hip.y() + 22)
            cape.lineTo(neck.x() - d * 6, hip.y() + 10)
            cape.closeSubpath()
            p.setPen(QPen(QColor("#8e0000"), 1.5))
            p.setBrush(QColor("#d32f2f"))
            p.drawPath(cape)
        elif back == "wings":
            flap = math.sin(t * 5) * 6
            for k in (1.0, 0.7):
                wing = QPainterPath(QPointF(neck.x(), neck.y() + 8))
                wing.cubicTo(neck.x() - d * 30 * k, neck.y() - 30 * k - flap,
                             neck.x() - d * 52 * k, neck.y() - 6 - flap, neck.x() - d * 44 * k, neck.y() + 20)
                wing.quadTo(neck.x() - d * 24 * k, neck.y() + 26, neck.x(), neck.y() + 16)
                p.setPen(QPen(QColor("#b0bec5"), 1.5))
                p.setBrush(QColor("#fafafa"))
                p.drawPath(wing)

    def draw_shades(self, p, c, tilt):
        """משקפי שמש שחורים ומגניבים."""
        p.save()
        p.translate(c)
        p.rotate(tilt)
        p.setPen(QPen(QColor("#111111"), 2))
        p.drawLine(QPointF(-14, -1), QPointF(14, -1))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#111111"))
        p.drawRoundedRect(QRectF(-12.5, -3, 11, 8), 3, 3)
        p.drawRoundedRect(QRectF(1.5, -3, 11, 8), 3, 3)
        p.setPen(QPen(QColor(255, 255, 255, 170), 1.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-10, -1), QPointF(-7, -1))
        p.drawLine(QPointF(4, -1), QPointF(7, -1))
        p.restore()

    def draw_rifle(self, p, grip, d, angle):
        """רובה לייזר מצויר. grip הוא המקום שבו מחזיקים אותו, angle זווית (על הגב: אלכסון)."""
        p.save()
        p.translate(grip)
        p.scale(d, 1)
        p.rotate(angle)
        p.setPen(Qt.NoPen)
        stock = QPainterPath(QPointF(-16, -2))
        stock.lineTo(0, -4)
        stock.lineTo(0, 5)
        stock.lineTo(-16, 8)
        stock.closeSubpath()
        p.setBrush(QColor("#5d4037"))
        p.drawPath(stock)
        p.setBrush(QColor("#37474f"))
        p.drawRoundedRect(QRectF(0, -5, 34, 10), 3, 3)
        p.setBrush(QColor("#263238"))
        p.drawRect(QRectF(34, -2.5, 16, 5))
        p.drawRect(QRectF(15, 4, 6, 8))
        p.setBrush(QColor("#111111"))
        p.drawRoundedRect(QRectF(9, -11, 18, 5), 2, 2)
        p.setBrush(QColor("#4fc3f7"))
        p.drawEllipse(QPointF(26, -8.5), 2, 2)
        p.setBrush(QColor("#ff7043"))
        p.drawEllipse(QPointF(51, 0), 3, 3)
        p.restore()

    def draw_ko(self, p, f, is_piko, body):
        """לוחם שנפל: שוכב על הרצפה עם כוכבים מסביב לראש."""
        x, y, d = f.x, f.y, -f.facing  # נופל לאחור
        p.setPen(QPen(body, 9, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x - d * 4, y - 8), QPointF(x + d * 34, y - 4))
        p.drawLine(QPointF(x - d * 4, y - 8), QPointF(x + d * 30, y - 14))
        p.setPen(QPen(body, 14, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x - d * 4, y - 9), QPointF(x - d * 34, y - 11))
        p.setPen(QPen(body, 8, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x - d * 28, y - 12), QPointF(x - d * 20, y - 30))
        head = QPointF(x - d * 50, y - 15)
        if is_piko:
            self.draw_robot_head(p, head, d, f)
        else:
            self.draw_player_head(p, head, d, f)
        t = time.time()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffeb3b"))
        for i in range(3):
            a = t * 4 + i * 2.1
            p.drawPath(star_path(head.x() + math.cos(a) * 24, head.y() - 24 + math.sin(a) * 6, 6))


# ---------------------------------------------------------------- מירוץ מכוניות נגד פיקו
RACE_LINES = {
    "piko_banana_hit": ["חחח! החלקת על הבננה שלי! 🍌", "בננה מספר אחת של פיקו! שומר בכיס תמיד.",
                        "זהירות, הכביש חלק! ...בגללי. 😎"],
    "player_banana_hit": ["מי שם פה בננה?! זה לא הוגן!", "הייי! המשקפיים שלי לא ראו את הבננה!"],
    "piko_lead": ["ביי ביי! תסתכל על הפגוש האחורי שלי! 😎", "אני כל כך מהיר שהצל שלי נשאר מאחור."],
    "player_lead": ["רגע! איך עקפת אותי?!", "נתתי לך לעקוף. אני נדיב היום."],
    "piko_race": ["פיקו ניצח במירוץ! נהג המרוצים הכי מהיר ביקום! 🏆", "ניצחתי! המנוע שלי עשוי מגאונות."],
    "player_race": ["מה?! הצמיגים שלי היו מרובעים!", "ניצחת במירוץ? טוב, נגמר לי הדלק. ברור."],
}


class RaceCar:
    def __init__(self, x, piko):
        self.d = 0.0             # כמה רחוק נסע לאורך המסלול
        self.x = float(x)        # מיקום מצד לצד
        self.v = 0.0
        self.piko = piko
        self.spin = 0            # מסתובב אחרי שמן או בננה
        self.angle = 0.0
        self.tilt = 0.0
        self.turbo_t = 0
        self.turbos = 0
        self.bananas = 1
        self.skill = 1.0


class RaceGame(FootballGame):
    """מירוץ מכוניות נגד פיקו, במבט מלמעלה. מי שמנצח 2 מירוצים מנצח.
    המכונית נוסעת לבד. חצים ימינה/שמאלה (או A/D) להיגוי, למטה/S בלם,
    רווח או למעלה/W טורבו, X או Z לזרוק בננה מאחוריך, R משחק חדש, Esc סוגר."""

    W, H = 800, 500
    LENGTH = 16000           # אורך מסלול
    ROAD = 150               # חצי מרוחב הכביש
    CAR_Y = 380              # איפה המכונית שלך על המסך
    WIN = 2
    VMAX = 9.0
    PIKO_SKILL = 0.98        # כמה פיקו מהיר בבסיס (1 = מהיר כמוך)

    def __init__(self):
        self.pressed = set()
        super().__init__()
        self.setWindowTitle("מירוץ מכוניות נגד פיקו")

    # ---------- המסלול ----------
    def center(self, d):
        """מרכז הכביש בכל נקודה לאורך המסלול: כביש מתפתל."""
        if d < 500:
            bend = d / 500  # הזינוק ישר
        else:
            bend = 1.0
        return 400 + bend * (115 * math.sin((d - 500) / 1100) + 50 * math.sin((d - 500) / 430 + 1.3) - 50 * math.sin(1.3))

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.race_no = 0
        self.say("פיקו: מירוץ? יש לי משקפי שמש, מנוע טורבו ומלא בננות! 😎🏎", 200)
        self.emotion.emit("proud")
        self.new_race()

    def new_race(self):
        self.race_no += 1
        self.player = RaceCar(self.center(0) - 45, False)
        self.piko = RaceCar(self.center(0) + 45, True)
        self.piko.bananas = 2
        self.objects = []   # [d, x, סוג, חי, מי זרק]
        rnd = random.Random()
        d = 700
        while d < self.LENGTH - 400:
            for _ in range(rnd.choice([1, 1, 2])):
                kind = rnd.choice(["cone", "cone", "cone", "oil"])
                self.objects.append([d, self.center(d) + rnd.uniform(-125, 125), kind, True, None])
            if rnd.random() < 0.3:
                kind = rnd.choice(["turbo", "turbo", "box"])
                # כל מכונית יכולה לאסוף את הפרס פעם אחת (רושמים מי כבר לקח)
                self.objects.append([d + 150, self.center(d + 150) + rnd.uniform(-110, 110), kind, True, set()])
            d += rnd.uniform(240, 420)
        self.sparks = []    # [x_עולם, d_עולם, מילה, זמן]
        self.countdown = 200
        self.race_end = 0
        self.leader = None
        self.bump_cd = 0
        self.ai_target = self.piko.x
        self.ai_cd = 0
        self.banana_cd = 200
        self.pressed.clear()

    # ---------- מקלדת ----------
    def keyPressEvent(self, event):
        key = self.key_of(event)
        if not event.isAutoRepeat():
            self.pressed.add(key)
        super().keyPressEvent(event)

    def player_input(self):
        k, pr = self.keys, self.pressed
        return dict(
            left=Qt.Key_Left in k or Qt.Key_A in k,
            right=Qt.Key_Right in k or Qt.Key_D in k,
            brake=Qt.Key_Down in k or Qt.Key_S in k,
            turbo=bool(pr & {Qt.Key_Space, Qt.Key_Up, Qt.Key_W}),
            banana=bool(pr & {Qt.Key_X, Qt.Key_Z}),
        )

    # ---------- לולאת המשחק ----------
    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        if not self.over:
            self.step()
        self.pressed.clear()
        self.update()

    def step(self):
        for s in self.sparks:
            s[3] -= 1
        self.sparks = [s for s in self.sparks if s[3] > 0]
        if self.countdown > 0:
            self.countdown -= 1
            if self.countdown == 40:
                self.emotion.emit("happy")
            return
        if self.race_end > 0:
            for car in (self.player, self.piko):
                car.v *= 0.96
                car.d += car.v
            self.race_end -= 1
            if self.race_end == 0:
                self.after_race()
            return

        # פיקו מתאמץ כשהוא מאחור, ושחצן ועצלן כשהוא מוביל
        gap = self.player.d - self.piko.d
        self.piko.skill = clamp(self.PIKO_SKILL + gap / 4000 * 0.45, 0.8, 1.14)

        self.drive(self.player, self.player_input())
        self.drive(self.piko, self.piko_input())
        self.bump_cars()
        for car in (self.player, self.piko):
            self.hit_objects(car)

        leader = "player" if self.player.d > self.piko.d else "piko"
        if leader != self.leader and self.leader is not None and abs(gap) > 30 and random.random() < 0.5:
            self.say(random.choice(RACE_LINES["piko_lead" if leader == "piko" else "player_lead"]), 90)
            self.emotion.emit("proud" if leader == "piko" else "surprised")
        self.leader = leader

        for car in (self.player, self.piko):
            if car.d >= self.LENGTH:
                self.end_race(car)
                break

    def drive(self, car, inp):
        steer = inp.get("right", False) - inp.get("left", False)
        if car.spin > 0:
            car.spin -= 1
            car.v *= 0.965
            car.angle += 22
            steer = 0
        else:
            car.angle = 0.0
        car.tilt += (steer * 10 - car.tilt) * 0.3

        vmax, accel = self.VMAX * car.skill, 0.18
        if inp.get("turbo") and car.turbos > 0 and car.turbo_t == 0 and car.spin == 0:
            car.turbos -= 1
            car.turbo_t = 100
            self.spark(car, "טורבו! 🔥")
        if car.turbo_t > 0:
            car.turbo_t -= 1
            vmax, accel = 14.0, 0.55
        offroad = abs(car.x - self.center(car.d)) > self.ROAD - 12
        if offroad:
            vmax = min(vmax, 4.5)

        if inp.get("brake"):
            car.v -= 0.35
        elif car.v < vmax:
            car.v += accel
        if car.v > vmax:
            car.v -= 0.25
        car.v = clamp(car.v, 0, 15)

        car.x += steer * (1.5 + 3.4 * min(1, car.v / 6))
        car.x = clamp(car.x, 30, self.W - 30)
        car.d += car.v

        if inp.get("banana") and car.bananas > 0:
            car.bananas -= 1
            self.objects.append([car.d - 45, car.x, "banana", True, car])

    def spark(self, car, word):
        self.sparks.append([car.x, car.d + 30, word, 40])

    def hit_objects(self, car):
        for o in self.objects:
            if not o[3] or abs(o[0] - car.d) > 26 or abs(o[1] - car.x) > 25:
                continue
            kind = o[2]
            if kind == "banana" and o[4] is car and car.d - o[0] < 60:
                continue  # הבננה שזרקת עכשיו לא מפילה אותך
            if kind in ("turbo", "box"):
                if car.piko in o[4]:
                    continue
                o[4].add(car.piko)
            else:
                o[3] = False
            if kind == "cone":
                car.v *= 0.55
                self.spark(car, "בונק!")
            elif kind == "oil":
                car.spin = 38
                self.spark(car, "החלקה!")
            elif kind == "banana":
                car.spin = 50
                self.spark(car, "בננה! 🍌")
                if car is self.player and o[4] is self.piko:
                    self.say(random.choice(RACE_LINES["piko_banana_hit"]), 90)
                    self.emotion.emit("laugh")
                elif car is self.piko and o[4] is self.player:
                    self.say(random.choice(RACE_LINES["player_banana_hit"]), 90)
                    self.emotion.emit("angry")
            elif kind == "turbo":
                car.turbos = min(3, car.turbos + 1)
                self.spark(car, "+⚡")
            elif kind == "box":
                car.bananas = min(3, car.bananas + 1)
                self.spark(car, "+🍌")

    def bump_cars(self):
        a, b = self.player, self.piko
        self.bump_cd = max(0, self.bump_cd - 1)
        if abs(a.d - b.d) < 46 and abs(a.x - b.x) < 30:
            push = (30 - abs(a.x - b.x)) / 2 + 1
            side = 1 if b.x >= a.x else -1
            a.x -= side * push
            b.x += side * push
            behind = a if a.d < b.d else b
            behind.v *= 0.9
            if not self.bump_cd:
                self.bump_cd = 30
                self.sparks.append([(a.x + b.x) / 2, (a.d + b.d) / 2 + 30, "בום!", 30])

    def end_race(self, winner):
        self.score[1 if winner.piko else 0] += 1
        self.race_end = 150
        self.race_winner = winner
        if winner.piko:
            self.say(random.choice(RACE_LINES["piko_race"]), 150)
            self.emotion.emit(random.choice(["proud", "laugh"]))
        else:
            self.say(random.choice(RACE_LINES["player_race"]), 150)
            self.emotion.emit(random.choice(["angry", "surprised"]))

    def after_race(self):
        you, piko = self.score
        if max(self.score) >= self.WIN:
            self.over = True
            if piko > you:
                self.say(f"פיקו ניצח {piko}-{you}! אלוף המרוצים של היקום. 🏆", 10 ** 9)
                self.emotion.emit("proud")
            else:
                self.say(f"ניצחת {you}-{piko}?! ...היה לי פנצ'ר. בכל המירוצים. ברור.", 10 ** 9)
                self.emotion.emit("surprised")
            self.finished.emit(you, piko)
        else:
            self.new_race()

    # ---------- המוח של פיקו בכביש ----------
    def piko_input(self):
        me, you = self.piko, self.player
        inp = {}
        self.ai_cd -= 1
        self.banana_cd -= 1
        if self.ai_cd <= 0:
            self.ai_cd = 6
            ahead = [o for o in self.objects if o[3] and me.d + 15 < o[0] < me.d + 330]
            look = self.center(me.d + 140)
            best, best_cost = self.ai_target, 1e9
            for off in (-105, -70, -35, 0, 35, 70, 105):
                tx = look + off
                cost = abs(off) * 0.04 + abs(tx - me.x) * 0.02
                for o in ahead:
                    near = abs(o[1] - tx) < 38 or (o[0] < me.d + 120 and abs(o[1] - me.x) < 30)
                    if near:
                        if o[2] in ("turbo", "box"):
                            cost += 0 if True in o[4] else -25
                        else:
                            cost += 100
                cost += random.uniform(0, 12)  # קצת טעויות, הוא בכל זאת רובוט שחצן
                if cost < best_cost:
                    best, best_cost = tx, cost
            self.ai_target = best
        dx = self.ai_target - me.x
        if dx > 6:
            inp["right"] = True
        elif dx < -6:
            inp["left"] = True
        # טורבו: כשהוא מאחור, או סתם להשוויץ
        if me.turbos and not me.turbo_t and (you.d > me.d + 60 or random.random() < 0.003):
            inp["turbo"] = True
        # בננה: כשאתה ממש מאחוריו ובאותו נתיב
        if (me.bananas and self.banana_cd <= 0 and 80 < me.d - you.d < 500
                and abs(me.x - you.x) < 70 and random.random() < 0.04):
            inp["banana"] = True
            self.banana_cd = 240
            if random.random() < 0.5:
                self.say("תיזהר! משהו צהוב מגיע... 🍌😎", 70)
        return inp

    # ---------- ציור ----------
    def sy(self, d):
        """ממיקום על המסלול למיקום על המסך (המצלמה עוקבת אחריך)."""
        return self.CAR_Y - (d - self.player.d)

    def paint(self, p):
        W, H = self.W, self.H
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1b5e20"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)
        p.setClipRect(QRectF(0, 0, W, H))
        cam = self.player.d
        self.draw_track(p, cam)
        self.draw_objects(p)
        for car in sorted((self.piko, self.player), key=lambda c: -c.d):
            self.draw_car(p, car)
        for x, d, word, life in self.sparks:
            y = self.sy(d) - (40 - life) * 0.8
            alpha = int(255 * min(1, life / 12))
            p.setFont(QFont("Arial", 18, QFont.Black))
            p.setPen(QColor(40, 20, 0, alpha))
            p.drawText(QRectF(x - 70 + 2, y - 20 + 2, 140, 40), Qt.AlignCenter, word)
            p.setPen(QColor(255, 235, 59, alpha))
            p.drawText(QRectF(x - 70, y - 20, 140, 40), Qt.AlignCenter, word)
        p.setClipping(False)
        self.draw_hud(p)
        self.draw_scoreboard(p)

        big = None
        if self.countdown > 0 and not self.over:
            n = (self.countdown - 1) // 50
            big = ("סע!" if n == 0 else str(n)), ("#76ff03" if n == 0 else "#ffeb3b")
            if self.countdown > 150:
                big = (f"מירוץ {self.race_no}", "#ffffff")
        elif self.race_end > 0 and not self.over:
            big = ("פיקו ניצח במירוץ!" if self.race_winner.piko else "ניצחת במירוץ!"), "#ffeb3b"
        if big:
            p.setFont(QFont("Arial", 44, QFont.Black))
            p.setPen(QColor(0, 0, 0, 170))
            p.drawText(QRectF(3, 173, W, 80), Qt.AlignCenter, big[0])
            p.setPen(QColor(big[1]))
            p.drawText(QRectF(0, 170, W, 80), Qt.AlignCenter, big[0])

        self.draw_overlay(p, "← → היגוי · ↓ בלם · רווח טורבו · X בננה · R · Esc", msg_y=62, hint_y=H - 26)

    def draw_track(self, p, cam):
        W, H, R = self.W, self.H, self.ROAD
        step = 8
        rows = []
        for sy in range(-step, H + step * 2, step):
            d = cam + (self.CAR_Y - sy)
            rows.append((sy, d, self.center(d)))
        # דשא מפוספס
        for sy, d, c in rows:
            p.fillRect(QRectF(0, sy, W, step), QColor("#43a047" if int(d // 90) % 2 else "#388e3c"))
        # עצים ושיחים בצדדים
        lo, hi = int((cam - 150) // 140), int((cam + self.CAR_Y + 80) // 140)
        for k in range(lo, hi + 1):
            rnd = random.Random(k * 7919)
            for side in (-1, 1):
                d = k * 140 + rnd.uniform(0, 100)
                x = self.center(d) + side * (R + 40 + rnd.uniform(0, 140))
                y = self.sy(d)
                r = rnd.uniform(14, 24)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(0, 0, 0, 50))
                p.drawEllipse(QPointF(x + 5, y + 6), r, r * 0.8)
                p.setBrush(QColor("#2e7d32"))
                p.drawEllipse(QPointF(x, y), r, r)
                p.setBrush(QColor("#66bb6a"))
                p.drawEllipse(QPointF(x - r * 0.25, y - r * 0.25), r * 0.5, r * 0.5)
        # הכביש
        road = QPainterPath(QPointF(rows[0][2] - R, rows[0][0]))
        for sy, d, c in rows[1:]:
            road.lineTo(c - R, sy)
        for sy, d, c in reversed(rows):
            road.lineTo(c + R, sy)
        road.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#555a60"))
        p.drawPath(road)
        for sy, d, c in rows:
            curb = QColor("#e53935") if int(d // 40) % 2 else QColor("#fafafa")
            p.fillRect(QRectF(c - R - 10, sy, 12, step + 1), curb)
            p.fillRect(QRectF(c + R - 2, sy, 12, step + 1), curb)
            if int(d // 50) % 2 == 0:
                p.fillRect(QRectF(c - 2.5, sy, 5, step + 1), QColor(255, 255, 255, 200))
        # קו זינוק וקו סיום משובצים
        for line_d in (0, self.LENGTH):
            y = self.sy(line_d)
            if -30 < y < H + 30:
                c = self.center(line_d)
                for i in range(int(-R // 15), int(R // 15)):
                    for j in range(2):
                        color = Qt.white if (i + j) % 2 else QColor("#111111")
                        p.fillRect(QRectF(c + i * 15, y - 15 + j * 15, 15, 15), color)

    def draw_objects(self, p):
        for d, x, kind, alive, owner in self.objects:
            if not alive or (kind in ("turbo", "box") and False in owner):
                continue  # פרס שכבר אספת נעלם בשבילך
            y = self.sy(d)
            if not -30 < y < self.H + 30:
                continue
            p.setPen(Qt.NoPen)
            if kind == "cone":
                p.setBrush(QColor(0, 0, 0, 60))
                p.drawEllipse(QPointF(x + 3, y + 4), 12, 10)
                p.setBrush(QColor("#ff6d00"))
                p.drawEllipse(QPointF(x, y), 12, 12)
                p.setBrush(Qt.white)
                p.drawEllipse(QPointF(x, y), 7, 7)
                p.setBrush(QColor("#ff6d00"))
                p.drawEllipse(QPointF(x, y), 4, 4)
            elif kind == "oil":
                p.setBrush(QColor("#1a1a1a"))
                p.drawEllipse(QPointF(x, y), 22, 14)
                p.drawEllipse(QPointF(x + 10, y + 6), 10, 7)
                p.setBrush(QColor(120, 120, 255, 90))
                p.drawEllipse(QPointF(x - 6, y - 4), 8, 3)
            elif kind == "banana":
                path = QPainterPath(QPointF(x - 12, y - 4))
                path.quadTo(x, y + 14, x + 12, y - 4)
                path.quadTo(x, y + 6, x - 12, y - 4)
                p.setPen(QPen(QColor("#8d6e00"), 1.5))
                p.setBrush(QColor("#ffeb3b"))
                p.drawPath(path)
            elif kind in ("turbo", "box"):
                bob = math.sin(time.time() * 5 + d) * 2
                box = QRectF(x - 13, y - 13 + bob, 26, 26)
                p.setPen(QPen(Qt.white, 2))
                p.setBrush(QColor("#1e88e5") if kind == "turbo" else QColor("#fbc02d"))
                p.drawRoundedRect(box, 6, 6)
                p.setFont(QFont("Arial", 13, QFont.Black))
                p.setPen(Qt.white)
                p.drawText(box, Qt.AlignCenter, "⚡" if kind == "turbo" else "?")

    def draw_car(self, p, car):
        y = self.sy(car.d)
        if not -60 < y < self.H + 60:
            return
        p.save()
        p.translate(car.x, y)
        p.rotate(car.angle + car.tilt)
        # להבות טורבו
        if car.turbo_t > 0:
            flick = random.uniform(0.7, 1.2)
            for color, size in (("#ff6d00", 1.0), ("#ffeb3b", 0.6)):
                flame = QPainterPath(QPointF(-9 * size, 26))
                flame.lineTo(0, 26 + 30 * size * flick)
                flame.lineTo(9 * size, 26)
                flame.closeSubpath()
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(color))
                p.drawPath(flame)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRoundedRect(QRectF(-15 + 4, -26 + 5, 30, 52), 9, 9)
        p.setBrush(QColor("#212121"))
        for wx in (-17, 11):
            for wy in (-20, 8):
                p.drawRoundedRect(QRectF(wx, wy, 6, 13), 2, 2)
        body = HEAD if car.piko else QColor("#1e88e5")
        p.setPen(QPen(body.darker(130), 2))
        p.setBrush(body)
        p.drawRoundedRect(QRectF(-15, -26, 30, 52), 9, 9)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#b3e5fc"))
        p.drawRoundedRect(QRectF(-11, -18, 22, 8), 3, 3)  # שמשה קדמית
        if car.piko:
            # פיקו בתוך המכונית: ראש כתום, אנטנה ומשקפי שמש
            p.setPen(QPen(BOLT, 2))
            p.drawLine(QPointF(0, -2), QPointF(0, -14))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffd54f"))
            p.drawEllipse(QPointF(0, -15), 2.5, 2.5)
            p.setPen(QPen(HEAD_DARK, 2))
            p.setBrush(HEAD)
            p.drawEllipse(QPointF(0, 3), 9, 9)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#111111"))
            p.drawRoundedRect(QRectF(-7.5, -1, 6.5, 4.5), 1.5, 1.5)
            p.drawRoundedRect(QRectF(1, -1, 6.5, 4.5), 1.5, 1.5)
            p.setBrush(QColor("#ff7043"))
            p.drawRect(QRectF(-15, 20, 30, 4))  # ספוילר
        else:
            p.setBrush(Qt.white)
            p.drawRect(QRectF(-3, -26, 6, 52))  # פס מירוץ
            p.setBrush(QColor("#0d47a1"))
            p.drawEllipse(QPointF(0, 4), 8, 8)  # הקסדה שלך
            p.setBrush(QColor("#e53935"))
            p.drawRect(QRectF(-8, 1, 16, 3))
        p.restore()

    def draw_hud(self, p):
        W, H = self.W, self.H
        pl, pk = self.player, self.piko
        # פס התקדמות בצד שמאל
        top, bottom, x = 70, H - 50, 26
        p.setPen(QPen(QColor(0, 0, 0, 120), 8, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, top), QPointF(x, bottom))
        p.setPen(QPen(Qt.white, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, top), QPointF(x, bottom))
        p.setFont(QFont("Arial", 14))
        p.drawText(QRectF(x - 12, top - 26, 30, 24), Qt.AlignCenter, "🏁")
        for car, color in ((pk, HEAD), (pl, QColor("#1e88e5"))):
            frac = clamp(car.d / self.LENGTH, 0, 1)
            y = bottom - (bottom - top) * frac
            p.setPen(QPen(Qt.white, 2))
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), 8, 8)
        # מקום, מהירות, טורבו ובננות בצד ימין
        first = pl.d >= pk.d
        panel = QRectF(W - 196, H - 128, 180, 96)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(panel, 12, 12)
        p.setPen(QColor("#ffeb3b") if first else QColor("#ff8a65"))
        p.setFont(QFont("Arial", 18, QFont.Black))
        p.drawText(QRectF(panel.x(), panel.y() + 4, panel.width(), 28), Qt.AlignCenter,
                   "מקום 1 🥇" if first else "מקום 2")
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(QRectF(panel.x(), panel.y() + 34, panel.width(), 22), Qt.AlignCenter,
                   f"מהירות: {int(pl.v * 14)} קמ\"ש")
        p.drawText(QRectF(panel.x(), panel.y() + 60, panel.width(), 26), Qt.AlignCenter,
                   f"⚡ {pl.turbos}     🍌 {pl.bananas}")
        # חץ לפיקו כשהוא לא על המסך
        gap = pk.d - pl.d
        y = self.sy(pk.d)
        if y < 40 or y > H + 20:
            meters = int(abs(gap) / 10)
            up = gap > 0
            box = QRectF(clamp(pk.x - 70, 60, W - 260), 110 if up else H - 90, 140, 26)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRoundedRect(box, 8, 8)
            p.setPen(QColor("#ffab91"))
            p.setFont(QFont("Arial", 11, QFont.Bold))
            p.drawText(box, Qt.AlignCenter, f"{'↑' if up else '↓'} פיקו {meters} מ'")


# ---------------------------------------------------------------- מחבואים עם פיקו
HIDE_LINES = {
    "hide": ["פיקו מתחבא... תעצום עיניים! 🙈", "אחת, שתיים, שלוש... אני מתחבא במקום הכי סודי ביקום!",
             "מקום חדש, מחבוא חדש! הפעם לא תמצא אותי. 😎"],
    "seek": ["נסה למצוא אותי! אין לך סיכוי. 😎", "אני מתחבא כל כך טוב, שאפילו אני לא יודע איפה אני.",
             "מוכן? חפש! (רמז: אני לא שם)"],
    "hot": ["חם! חם מאוד! 🔥 ...אופס, לא הייתי צריך להגיד את זה.", "חם! אתה ממש קרוב... אבל לא מספיק!"],
    "warm": ["חמים... אבל לא מספיק! 😏", "פושר. כמו תה של רובוטים."],
    "cold": ["קר! קר כמו מקרר! ❄️", "קפוא! אני בכלל לא שם. חחח.", "קר! אתה מחפש בקוטב הצפוני?"],
    "found": ["אוי! מצאת אותי! האנטנה שלי בגדה בי!", "לא! המחבוא המושלם שלי! 😱", "מה?! איך ידעת?! רימית!"],
    "missed": ["הייתי פה כל הזמן! 😎 אלוף המחבואים!", "חחח! עברת ממש לידי!", "תפסת אותי? לא. ממש לא."],
    "time": ["נגמר הזמן! ⏰ הייתי פה כל הזמן!"],
}
# מקומות המחבוא בסלון: שם, אזור לחיצה, איפה פיקו מציץ ואיך
HIDE_SPOTS = [
    dict(id="curtain", name="הווילון", rect=(48, 62, 74, 266), peek="feet", at=(85, 334)),
    dict(id="closet", name="הארון", rect=(600, 84, 140, 246), peek="eyes", at=(670, 180)),
    dict(id="sofa", name="הספה", rect=(238, 236, 244, 100), peek="antenna", at=(352, 238)),
    dict(id="plant", name="העציץ", rect=(505, 160, 92, 172), peek="antenna", at=(551, 168)),
    dict(id="box", name="הקרטון", rect=(92, 360, 116, 92), peek="eyes", at=(150, 376)),
    dict(id="table", name="השולחן", rect=(286, 362, 176, 92), peek="feet", at=(374, 456)),
    dict(id="basket", name="סל הכביסה", rect=(516, 380, 92, 80), peek="antenna", at=(562, 384)),
    dict(id="armchair", name="הכורסה", rect=(642, 360, 130, 106), peek="eyes", at=(636, 404)),
]


# כל סיבוב במקום אחר. לכל מקום רקע משלו ו-8 מחבואים
HIDE_SCENES = [
    dict(id="living", name="בסלון", icon="🛋️", bg="bg_living", spots=HIDE_SPOTS),
    dict(id="garden", name="בחצר", icon="🏡", bg="bg_garden", spots=[
        dict(id="shed", name="המחסן", rect=(40, 150, 170, 182), peek="eyes", at=(122, 262)),
        dict(id="tree", name="העץ", rect=(250, 70, 140, 265), peek="eyes", at=(350, 285)),
        dict(id="bush", name="השיח", rect=(430, 250, 120, 85), peek="antenna", at=(490, 254)),
        dict(id="doghouse", name="המלונה", rect=(600, 216, 132, 120), peek="eyes", at=(666, 302)),
        dict(id="leaves", name="ערימת העלים", rect=(60, 384, 150, 72), peek="antenna", at=(135, 390)),
        dict(id="bin", name="הפח", rect=(270, 360, 72, 100), peek="eyes", at=(306, 373)),
        dict(id="barrow", name="המריצה", rect=(392, 384, 160, 76), peek="feet", at=(452, 466)),
        dict(id="sandbox", name="ארגז החול", rect=(596, 392, 176, 68), peek="antenna", at=(700, 400)),
    ]),
    dict(id="kitchen", name="במטבח", icon="🍳", bg="bg_kitchen", spots=[
        dict(id="fridge", name="המקרר", rect=(40, 90, 120, 246), peek="eyes", at=(150, 200)),
        dict(id="oven", name="התנור", rect=(186, 220, 130, 116), peek="eyes", at=(251, 300)),
        dict(id="sink", name="ארון הכיור", rect=(336, 226, 170, 110), peek="eyes", at=(421, 300)),
        dict(id="washer", name="מכונת הכביסה", rect=(526, 220, 112, 116), peek="eyes", at=(582, 288)),
        dict(id="broom", name="ארון המטאטאים", rect=(660, 90, 110, 246), peek="feet", at=(715, 340)),
        dict(id="ktable", name="שולחן האוכל", rect=(214, 372, 196, 88), peek="feet", at=(312, 466)),
        dict(id="pot", name="הסיר הענק", rect=(450, 382, 112, 80), peek="antenna", at=(506, 386)),
        dict(id="sack", name="שק תפוחי האדמה", rect=(600, 380, 104, 84), peek="antenna", at=(652, 386)),
    ]),
    dict(id="bedroom", name="בחדר השינה", icon="🛏️", bg="bg_bedroom", spots=[
        dict(id="bed", name="המיטה", rect=(36, 238, 250, 112), peek="feet", at=(162, 354)),
        dict(id="dresser", name="השידה", rect=(318, 196, 132, 144), peek="eyes", at=(384, 222)),
        dict(id="teddy", name="הדובי הענק", rect=(478, 196, 116, 144), peek="antenna", at=(536, 202)),
        dict(id="tent", name="האוהל", rect=(618, 186, 154, 154), peek="eyes", at=(695, 300)),
        dict(id="chest", name="ארגז הצעצועים", rect=(40, 380, 132, 82), peek="eyes", at=(106, 393)),
        dict(id="beanbag", name="הפוף", rect=(206, 380, 124, 82), peek="antenna", at=(268, 386)),
        dict(id="clothes", name="ערימת הבגדים", rect=(368, 388, 132, 72), peek="antenna", at=(434, 392)),
        dict(id="desk", name="שולחן הכתיבה", rect=(538, 366, 176, 96), peek="feet", at=(626, 466)),
    ]),
    dict(id="beach", name="בחוף הים", icon="🏖️", bg="bg_beach", spots=[
        dict(id="palm", name="עץ הדקל", rect=(26, 76, 130, 258), peek="eyes", at=(112, 290)),
        dict(id="umbrella", name="השמשייה", rect=(166, 176, 156, 156), peek="antenna", at=(244, 184)),
        dict(id="boat", name="הסירה", rect=(356, 216, 176, 100), peek="eyes", at=(444, 232)),
        dict(id="tower", name="סוכת המציל", rect=(568, 86, 134, 250), peek="eyes", at=(635, 140)),
        dict(id="castle", name="ארמון החול", rect=(36, 368, 166, 96), peek="antenna", at=(120, 372)),
        dict(id="beachchair", name="כיסא הנוח", rect=(238, 378, 146, 84), peek="feet", at=(312, 468)),
        dict(id="rock", name="הסלע", rect=(420, 368, 144, 96), peek="eyes", at=(424, 420)),
        dict(id="cooler", name="הצידנית", rect=(606, 388, 116, 76), peek="eyes", at=(664, 400)),
    ]),
]


class HideSeekGame(FootballGame):
    """מחבואים עם פיקו. בכל סיבוב מקום אחר (סלון, חצר, מטבח, חדר שינה, חוף ים), ולוחצים בעכבר על המחבוא.
    3 ניסיונות ו-20 שניות בכל סיבוב. מי שמגיע ראשון ל-3 מנצח. R משחק חדש, Esc סוגר."""

    W, H = 800, 500
    WIN = 3
    GUESSES = 3
    SEEK_FRAMES = 20 * 60

    def __init__(self):
        self.hover = None
        super().__init__()
        self.setWindowTitle("מחבואים עם פיקו")
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.view = (1.0, 0.0, 0.0)

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.round_no = 0
        self.scene_order = random.sample(HIDE_SCENES, len(HIDE_SCENES))  # כל סיבוב במקום אחר
        self.new_round()

    def new_round(self):
        self.round_no += 1
        self.scene = self.scene_order[(self.round_no - 1) % len(self.scene_order)]
        self.spots = self.scene["spots"]
        self.spot = random.choice(self.spots)
        self.state, self.t = "hide", 110
        self.guesses = self.GUESSES
        self.time_left = self.SEEK_FRAMES
        self.opened = set()
        self.shake = {}
        self.sparks = []
        self.peek = 0
        self.peek_cd = random.randint(150, 260)
        self.say(random.choice(HIDE_LINES["hide"]), 110)
        self.emotion.emit("happy")

    # ---------- עכבר ----------
    def to_logical(self, pos):
        s, ox, oy = self.view
        return (pos.x() - ox) / s, (pos.y() - oy) / s

    def spot_at(self, pos):
        x, y = self.to_logical(pos)
        for s in reversed(self.spots):
            rx, ry, rw, rh = s["rect"]
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return s
        return None

    def mouseMoveEvent(self, event):
        self.hover = self.spot_at(event.position())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.over:
            s = self.spot_at(event.position())
            if s:
                self.guess(s)

    def guess(self, s):
        if self.state != "seek" or s["id"] in self.opened:
            return
        if s is self.spot:
            self.score[0] += 1
            self.state, self.t = "found", 130
            self.say(random.choice(HIDE_LINES["found"]), 130)
            self.emotion.emit(random.choice(["surprised", "angry"]))
            return
        self.opened.add(s["id"])
        self.shake[s["id"]] = 24
        self.guesses -= 1
        rx, ry, rw, rh = s["rect"]
        self.sparks.append([rx + rw / 2, ry + rh / 2, "ריק!", 45])
        a, b = self.center(s), self.center(self.spot)
        dist = math.hypot(a[0] - b[0], a[1] - b[1])
        kind = "hot" if dist < 200 else "warm" if dist < 360 else "cold"
        self.say(random.choice(HIDE_LINES[kind]), 120)
        if random.random() < 0.5:
            self.emotion.emit(random.choice(["laugh", "proud"]))
        if self.guesses == 1:
            # צחקוק שמגיע בערך מהכיוון של המחבוא
            cx, cy = self.center(self.spot)
            self.sparks.append([cx + random.uniform(-90, 90), cy + random.uniform(-60, 30), "חיחיחי...", 70])
        if self.guesses == 0:
            self.miss("missed")

    def miss(self, kind):
        self.score[1] += 1
        self.state, self.t = "missed", 140
        self.say(random.choice(HIDE_LINES[kind]), 140)
        self.emotion.emit(random.choice(["laugh", "proud"]))

    @staticmethod
    def center(s):
        rx, ry, rw, rh = s["rect"]
        return rx + rw / 2, ry + rh / 2

    # ---------- לולאת המשחק ----------
    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        if not self.over:
            self.step()
        self.update()

    def step(self):
        for k in list(self.shake):
            self.shake[k] -= 1
            if self.shake[k] <= 0:
                del self.shake[k]
        for sp in self.sparks:
            sp[1] -= 0.5
            sp[3] -= 1
        self.sparks = [sp for sp in self.sparks if sp[3] > 0]
        if self.state == "hide":
            self.t -= 1
            if self.t <= 0:
                self.state = "seek"
                self.say(random.choice(HIDE_LINES["seek"]), 120)
        elif self.state == "seek":
            self.time_left -= 1
            # מדי פעם פיקו מציץ מהמחבוא לרגע
            if self.peek > 0:
                self.peek -= 1
            else:
                self.peek_cd -= 1
                if self.peek_cd <= 0:
                    self.peek = 34
                    self.peek_cd = random.randint(200, 330)
            if self.time_left <= 0:
                self.miss("time")
        elif self.state in ("found", "missed"):
            self.t -= 1
            if self.t <= 0:
                self.after_round()

    def after_round(self):
        you, piko = self.score
        if max(self.score) >= self.WIN:
            self.over = True
            if piko > you:
                self.say(f"פיקו ניצח {piko}-{you}! אלוף המחבואים של היקום! 🙈👑", 10 ** 9)
                self.emotion.emit("proud")
            else:
                self.say(f"מצאת אותי {you} פעמים?! יש לך עיני נץ... או שהאנטנה שלי בולטת מדי.", 10 ** 9)
                self.emotion.emit("surprised")
            self.finished.emit(you, piko)
        else:
            self.new_round()

    # ---------- ציור ----------
    def paint(self, p):
        W, H = self.W, self.H
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#2b1d14"))
        s = min(self.width() / W, self.height() / H)
        ox, oy = (self.width() - W * s) / 2, (self.height() - H * s) / 2
        self.view = (s, ox, oy)
        p.translate(ox, oy)
        p.scale(s, s)
        getattr(self, self.scene["bg"])(p)
        for spot in self.spots:
            self.draw_spot(p, spot)
        if self.state == "seek" and self.peek > 0:
            self.draw_peek(p)
        if self.state in ("found", "missed"):
            self.draw_popped(p)
        for x, y, word, life in self.sparks:
            p.setFont(QFont("Arial", 18, QFont.Black))
            alpha = int(255 * min(1, life / 15))
            p.setPen(QColor(40, 20, 0, alpha))
            p.drawText(QRectF(x - 80 + 2, y - 20 + 2, 160, 40), Qt.AlignCenter, word)
            p.setPen(QColor(255, 235, 59, alpha))
            p.drawText(QRectF(x - 80, y - 20, 160, 40), Qt.AlignCenter, word)
        if self.state == "hide" and not self.over:
            # עיניים עצומות: המסך מחשיך בזמן שפיקו מתחבא
            p.fillRect(QRectF(0, 0, W, H), QColor(0, 0, 0, 215))
            p.setFont(QFont("Arial", 40, QFont.Black))
            p.setPen(QColor("#ffeb3b"))
            p.drawText(QRectF(0, 140, W, 70), Qt.AlignCenter, f"סיבוב {self.round_no}")
            p.setFont(QFont("Arial", 28, QFont.Bold))
            p.setPen(QColor("#80deea"))
            p.drawText(QRectF(0, 200, W, 50), Qt.AlignCenter, f"{self.scene['icon']}  {self.scene['name']}")
            p.setFont(QFont("Arial", 24, QFont.Bold))
            p.setPen(Qt.white)
            n = self.t // 37 + 1
            p.drawText(QRectF(0, 262, W, 50), Qt.AlignCenter, f"🙈 פיקו מתחבא... {n}")
        self.draw_hud(p)
        self.draw_scoreboard(p)
        self.draw_overlay(p, "לחץ בעכבר על המקום שבו פיקו מתחבא · שים לב לאנטנה! · R · Esc",
                          msg_y=56, hint_y=H - 24)

    def draw_room(self, p):
        W, H = self.W, self.H
        p.fillRect(QRectF(0, 0, W, 336), QColor("#ffe0b2"))
        p.setPen(QPen(QColor("#ffcc80"), 6))
        for x in range(20, W, 40):
            p.drawLine(QPointF(x, 0), QPointF(x, 336))
        p.fillRect(QRectF(0, 336, W, H - 336), QColor("#a1887f"))
        p.setPen(QPen(QColor("#8d6e63"), 1.5))
        for y in range(350, H, 22):
            p.drawLine(QPointF(0, y), QPointF(W, y))
        p.fillRect(QRectF(0, 330, W, 8), QColor("#6d4c41"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(121, 134, 203, 150))
        p.drawEllipse(QRectF(220, 345, 360, 130))  # שטיח
        # חלון
        p.setPen(QPen(QColor("#795548"), 5))
        p.setBrush(QColor("#81d4fa"))
        p.drawRect(QRectF(70, 82, 150, 160))
        p.drawLine(QPointF(145, 82), QPointF(145, 242))
        p.drawLine(QPointF(70, 162), QPointF(220, 162))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#fff59d"))
        p.drawEllipse(QPointF(190, 112), 14, 14)
        p.setPen(QPen(QColor("#5d4037"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(40, 64), QPointF(240, 64))  # מוט וילון
        # תמונה על הקיר
        p.setPen(QPen(QColor("#8d6e63"), 6))
        p.setBrush(QColor("#c8e6c9"))
        p.drawRect(QRectF(300, 100, 130, 90))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#66bb6a"))
        hill = QPainterPath(QPointF(303, 187))
        hill.quadTo(340, 130, 380, 170)
        hill.quadTo(405, 150, 427, 187)
        hill.closeSubpath()
        p.drawPath(hill)

    def spot_offset(self, spot):
        k = self.shake.get(spot["id"], 0)
        return math.sin(k * 1.4) * 5 * (k / 24)

    def draw_spot(self, p, spot):
        dx = self.spot_offset(spot)
        p.save()
        p.translate(dx, 0)
        rx, ry, rw, rh = spot["rect"]
        sid = spot["id"]
        if sid == "curtain":
            p.setPen(QPen(QColor("#ad1457"), 2))
            p.setBrush(QColor("#ec407a"))
            path = QPainterPath(QPointF(rx, ry))
            path.lineTo(rx + rw, ry)
            path.quadTo(rx + rw - 14, ry + rh * 0.55, rx + rw + 6, ry + rh)
            path.lineTo(rx - 4, ry + rh)
            path.quadTo(rx + 6, ry + rh * 0.5, rx, ry)
            p.drawPath(path)
            p.setPen(QPen(QColor("#c2185b"), 2))
            for i in (1, 2, 3):
                x = rx + rw * i / 4
                p.drawLine(QPointF(x, ry + 4), QPointF(x + 2, ry + rh - 4))
        elif sid == "closet":
            p.setPen(QPen(QColor("#4e342e"), 3))
            p.setBrush(QColor("#8d6e63"))
            p.drawRect(QRectF(rx, ry, rw, rh))
            p.drawLine(QPointF(rx + rw / 2, ry), QPointF(rx + rw / 2, ry + rh))
            p.setBrush(QColor("#ffd54f"))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(rx + rw / 2 - 10, ry + rh / 2), 5, 5)
            p.drawEllipse(QPointF(rx + rw / 2 + 10, ry + rh / 2), 5, 5)
            p.setBrush(QColor("#6d4c41"))
            p.drawRect(QRectF(rx - 6, ry - 10, rw + 12, 12))
        elif sid == "sofa":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#00897b"))
            p.drawRoundedRect(QRectF(rx + 14, ry, rw - 28, 56), 16, 16)
            p.setBrush(QColor("#26a69a"))
            p.drawRoundedRect(QRectF(rx + 10, ry + 46, rw - 20, 38), 10, 10)
            p.setBrush(QColor("#00796b"))
            p.drawRoundedRect(QRectF(rx, ry + 30, 30, 62), 12, 12)
            p.drawRoundedRect(QRectF(rx + rw - 30, ry + 30, 30, 62), 12, 12)
            p.setBrush(QColor("#ffca28"))
            p.drawRoundedRect(QRectF(rx + 50, ry + 18, 48, 34), 10, 10)
            p.setBrush(QColor("#5d4037"))
            p.drawRect(QRectF(rx + 20, ry + 88, 8, 10))
            p.drawRect(QRectF(rx + rw - 28, ry + 88, 8, 10))
        elif sid == "plant":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#2e7d32"))
            for lx, ly, lr in ((rx + 22, ry + 60, 30), (rx + 70, ry + 58, 30), (rx + 46, ry + 30, 34),
                               (rx + 30, ry + 95, 26), (rx + 64, ry + 92, 26)):
                p.drawEllipse(QPointF(lx, ly), lr, lr * 0.8)
            p.setBrush(QColor("#43a047"))
            p.drawEllipse(QPointF(rx + 40, ry + 50), 16, 12)
            p.setBrush(QColor("#d84315"))
            pot = QPainterPath(QPointF(rx + 18, ry + 118))
            pot.lineTo(rx + rw - 18, ry + 118)
            pot.lineTo(rx + rw - 26, ry + rh)
            pot.lineTo(rx + 26, ry + rh)
            pot.closeSubpath()
            p.drawPath(pot)
            p.setBrush(QColor("#bf360c"))
            p.drawRect(QRectF(rx + 14, ry + 112, rw - 28, 12))
        elif sid == "box":
            p.setPen(QPen(QColor("#8d6e63"), 2))
            p.setBrush(QColor("#d7a86e"))
            p.drawRect(QRectF(rx, ry + 16, rw, rh - 16))
            p.setBrush(QColor("#c8955a"))
            flap1 = QPainterPath(QPointF(rx, ry + 16))
            flap1.lineTo(rx - 10, ry)
            flap1.lineTo(rx + rw / 2 - 4, ry + 4)
            flap1.lineTo(rx + rw / 2, ry + 16)
            flap1.closeSubpath()
            p.drawPath(flap1)
            flap2 = QPainterPath(QPointF(rx + rw, ry + 16))
            flap2.lineTo(rx + rw + 10, ry)
            flap2.lineTo(rx + rw / 2 + 4, ry + 4)
            flap2.lineTo(rx + rw / 2, ry + 16)
            flap2.closeSubpath()
            p.drawPath(flap2)
            p.setPen(QPen(QColor("#8d6e63"), 1))
            p.setFont(QFont("Arial", 11, QFont.Bold))
            p.drawText(QRectF(rx, ry + 40, rw, 30), Qt.AlignCenter, "צעצועים")
        elif sid == "table":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#5d4037"))
            p.drawRect(QRectF(rx + 6, ry, rw - 12, 10))
            p.setBrush(QColor("#ef5350"))
            cloth = QPainterPath(QPointF(rx, ry + 6))
            cloth.lineTo(rx + rw, ry + 6)
            cloth.lineTo(rx + rw + 4, ry + rh - 6)
            for i in range(8, -1, -1):
                cloth.lineTo(rx - 4 + (rw + 8) * i / 8, ry + rh - 6 + (5 if i % 2 else 0))
            cloth.closeSubpath()
            p.drawPath(cloth)
            p.setBrush(QColor(255, 255, 255, 120))
            for i in range(4):
                for j in range(2):
                    if (i + j) % 2 == 0:
                        p.drawRect(QRectF(rx + 10 + i * 40, ry + 18 + j * 30, 34, 26))
            p.setBrush(QColor("#fff176"))
            p.drawEllipse(QPointF(rx + rw / 2, ry - 6), 16, 7)  # צלחת
        elif sid == "basket":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#64b5f6"))
            p.drawEllipse(QPointF(rx + 30, ry + 14), 22, 12)
            p.setBrush(QColor("#fff176"))
            p.drawEllipse(QPointF(rx + 60, ry + 12), 20, 11)
            p.setPen(QPen(QColor("#8d6e63"), 2))
            p.setBrush(QColor("#bcaaa4"))
            body = QPainterPath(QPointF(rx, ry + 16))
            body.lineTo(rx + rw, ry + 16)
            body.lineTo(rx + rw - 8, ry + rh)
            body.lineTo(rx + 8, ry + rh)
            body.closeSubpath()
            p.drawPath(body)
            for i in range(1, 5):
                y = ry + 16 + (rh - 16) * i / 5
                p.drawLine(QPointF(rx + 3, y), QPointF(rx + rw - 3, y))
        elif sid == "armchair":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#7cb342"))
            p.drawRoundedRect(QRectF(rx + 16, ry, rw - 32, 70), 18, 18)
            p.setBrush(QColor("#9ccc65"))
            p.drawRoundedRect(QRectF(rx + 12, ry + 56, rw - 24, 34), 10, 10)
            p.setBrush(QColor("#689f38"))
            p.drawRoundedRect(QRectF(rx, ry + 36, 28, 60), 12, 12)
            p.drawRoundedRect(QRectF(rx + rw - 28, ry + 36, 28, 60), 12, 12)
            p.setBrush(QColor("#5d4037"))
            p.drawRect(QRectF(rx + 18, ry + 92, 8, 12))
            p.drawRect(QRectF(rx + rw - 26, ry + 92, 8, 12))
        elif hasattr(self, "spot_" + sid):
            getattr(self, "spot_" + sid)(p, rx, ry, rw, rh)   # מחבואים של שאר המקומות
        # מקום שכבר בדקת: מסומן כריק
        if sid in self.opened:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 70))
            p.drawRoundedRect(QRectF(rx, ry, rw, rh), 10, 10)
            p.setFont(QFont("Arial", 22, QFont.Black))
            p.setPen(QColor(255, 255, 255, 220))
            p.drawText(QRectF(rx, ry, rw, rh), Qt.AlignCenter, "✗")
        elif self.hover is spot and self.state == "seek":
            p.setPen(QPen(QColor(255, 235, 59, 220), 3, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(rx - 4, ry - 4, rw + 8, rh + 8), 12, 12)
        p.restore()

    # ---------- הרקעים של המקומות ----------
    def bg_living(self, p):
        self.draw_room(p)

    def bg_garden(self, p):
        W, H = self.W, self.H
        sky = QLinearGradient(0, 0, 0, 340)
        sky.setColorAt(0, QColor("#4fc3f7"))
        sky.setColorAt(1, QColor("#e1f5fe"))
        p.fillRect(QRectF(0, 0, W, 340), sky)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#fff176"))
        p.drawEllipse(QPointF(560, 120), 34, 34)
        p.setBrush(QColor(255, 255, 255, 200))
        for cx, cy in ((180, 70), (470, 60)):
            for dx, r in ((-26, 18), (0, 26), (28, 20)):
                p.drawEllipse(QPointF(cx + dx, cy), r * 1.3, r)
        # גדר עץ
        p.setBrush(QColor("#d7ccc8"))
        p.drawRect(QRectF(0, 270, W, 10))
        p.drawRect(QRectF(0, 305, W, 10))
        for x in range(0, W, 34):
            spike = QPainterPath(QPointF(x + 4, 336))
            spike.lineTo(x + 4, 250)
            spike.lineTo(x + 15, 238)
            spike.lineTo(x + 26, 250)
            spike.lineTo(x + 26, 336)
            spike.closeSubpath()
            p.drawPath(spike)
        p.fillRect(QRectF(0, 334, W, H - 334), QColor("#8bc34a"))
        p.fillRect(QRectF(0, 334, W, 6), QColor("#689f38"))
        rnd = random.Random(3)
        for _ in range(26):
            x, y = rnd.uniform(10, W - 10), rnd.uniform(346, H - 30)
            p.setBrush(QColor(rnd.choice(["#ffeb3b", "#f06292", "#ffffff", "#ba68c8"])))
            p.drawEllipse(QPointF(x, y), 3.5, 3.5)

    def bg_kitchen(self, p):
        W, H = self.W, self.H
        p.fillRect(QRectF(0, 0, W, 336), QColor("#e0f7fa"))
        p.setPen(QPen(QColor("#b2ebf2"), 1))
        for x in range(0, W, 30):
            p.drawLine(QPointF(x, 0), QPointF(x, 336))
        for y in range(0, 336, 30):
            p.drawLine(QPointF(0, y), QPointF(W, y))
        # חלון ומדף עם צנצנות
        p.setPen(QPen(QColor("#90a4ae"), 5))
        p.setBrush(QColor("#b3e5fc"))
        p.drawRect(QRectF(360, 86, 130, 100))
        p.drawLine(QPointF(425, 86), QPointF(425, 186))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(196, 150, 120, 8))
        for i, color in enumerate(("#ef5350", "#ffca28", "#66bb6a")):
            p.setBrush(QColor(color))
            p.drawRoundedRect(QRectF(206 + i * 38, 122, 26, 28), 5, 5)
        # רצפת משבצות
        for i, x in enumerate(range(0, W, 40)):
            for j, y in enumerate(range(336, H, 40)):
                p.fillRect(QRectF(x, y, 40, 40), QColor("#eceff1") if (i + j) % 2 else QColor("#b0bec5"))
        p.fillRect(QRectF(0, 332, W, 6), QColor("#78909c"))

    def bg_bedroom(self, p):
        W, H = self.W, self.H
        p.fillRect(QRectF(0, 0, W, 336), QColor("#d1c4e9"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 120))
        rnd = random.Random(9)
        for _ in range(30):
            p.drawPath(star_path(rnd.uniform(10, W - 10), rnd.uniform(10, 320), rnd.uniform(4, 8)))
        # חלון בלילה עם ירח
        p.setPen(QPen(QColor("#7e57c2"), 5))
        p.setBrush(QColor("#1a237e"))
        p.drawRect(QRectF(120, 70, 130, 110))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#fff59d"))
        p.drawEllipse(QPointF(214, 104), 18, 18)
        p.setBrush(QColor("#1a237e"))
        p.drawEllipse(QPointF(222, 98), 15, 15)
        p.setBrush(QColor("#fff59d"))
        for sx, sy in ((150, 92), (175, 150), (232, 158)):
            p.drawPath(star_path(sx, sy, 4))
        p.fillRect(QRectF(0, 336, W, H - 336), QColor("#bcaaa4"))
        p.setPen(QPen(QColor("#a1887f"), 1.5))
        for y in range(350, H, 22):
            p.drawLine(QPointF(0, y), QPointF(W, y))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(244, 143, 177, 140))
        p.drawEllipse(QRectF(200, 350, 380, 120))  # שטיח עגול

    def bg_beach(self, p):
        W, H = self.W, self.H
        sky = QLinearGradient(0, 0, 0, 200)
        sky.setColorAt(0, QColor("#29b6f6"))
        sky.setColorAt(1, QColor("#b3e5fc"))
        p.fillRect(QRectF(0, 0, W, 200), sky)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffee58"))
        p.drawEllipse(QPointF(520, 120), 32, 32)
        p.fillRect(QRectF(0, 196, W, 110), QColor("#0288d1"))
        t = time.time()
        p.setPen(QPen(QColor(255, 255, 255, 170), 3, Qt.SolidLine, Qt.RoundCap))
        for row, y in enumerate((222, 252, 282)):
            shift = math.sin(t * 1.2 + row) * 12
            for x in range(-40, W + 40, 70):
                wave = QPainterPath(QPointF(x + shift, y))
                wave.quadTo(x + 18 + shift, y - 8, x + 36 + shift, y)
                p.drawPath(wave)
        p.setPen(Qt.NoPen)
        sand = QPainterPath(QPointF(0, 300))
        for x in range(0, W + 41, 40):
            sand.quadTo(x + 20, 292 + math.sin(t * 1.5 + x) * 3, x + 40, 300)
        sand.lineTo(W, H)
        sand.lineTo(0, H)
        sand.closeSubpath()
        p.setBrush(QColor("#ffe082"))
        p.drawPath(sand)
        p.setBrush(QColor("#ffca28"))
        rnd = random.Random(4)
        for _ in range(40):
            p.drawEllipse(QPointF(rnd.uniform(0, W), rnd.uniform(320, H)), 1.6, 1.6)
        p.setBrush(QColor("#ff8a65"))
        for sx, sy in ((360, 340), (560, 470), (215, 360)):
            p.drawPath(star_path(sx, sy, 7))  # כוכבי ים

    # ---------- מחבואים בחצר ----------
    def spot_shed(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#a1887f"))
        p.drawRect(QRectF(rx + 10, ry + 50, rw - 20, rh - 50))
        roof = QPainterPath(QPointF(rx, ry + 56))
        roof.lineTo(rx + rw / 2, ry)
        roof.lineTo(rx + rw, ry + 56)
        roof.closeSubpath()
        p.setBrush(QColor("#6d4c41"))
        p.drawPath(roof)
        p.setPen(QPen(QColor("#8d6e63"), 2))
        for x in range(int(rx + 22), int(rx + rw - 10), 16):
            p.drawLine(QPointF(x, ry + 56), QPointF(x, ry + rh))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4e342e"))
        p.drawRect(QRectF(rx + rw / 2 - 26, ry + 86, 52, rh - 86))
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(rx + rw / 2 + 16, ry + 136), 4, 4)

    def spot_tree(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6d4c41"))
        p.drawRect(QRectF(rx + 50, ry + 120, 42, rh - 120))
        p.setBrush(QColor("#388e3c"))
        for cx, cy, r in ((rx + 40, ry + 80, 46), (rx + 100, ry + 76, 46), (rx + 70, ry + 40, 50),
                          (rx + 70, ry + 110, 40)):
            p.drawEllipse(QPointF(cx, cy), r, r * 0.85)
        p.setBrush(QColor("#e53935"))
        for ax, ay in ((rx + 40, ry + 70), (rx + 96, ry + 96), (rx + 76, ry + 34), (rx + 110, ry + 60)):
            p.drawEllipse(QPointF(ax, ay), 6, 6)  # תפוחים

    def spot_bush(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2e7d32"))
        for cx, cy, r in ((rx + 30, ry + 52, 32), (rx + 62, ry + 36, 38), (rx + 92, ry + 52, 32)):
            p.drawEllipse(QPointF(cx, cy), r, r * 0.9)
        p.drawRect(QRectF(rx + 10, ry + 52, rw - 20, rh - 52))
        p.setBrush(QColor("#f48fb1"))
        for fx, fy in ((rx + 30, ry + 40), (rx + 70, ry + 26), (rx + 94, ry + 56), (rx + 50, ry + 64)):
            p.drawEllipse(QPointF(fx, fy), 4.5, 4.5)

    def spot_doghouse(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#e53935"))
        p.drawRect(QRectF(rx + 12, ry + 46, rw - 24, rh - 46))
        roof = QPainterPath(QPointF(rx, ry + 52))
        roof.lineTo(rx + rw / 2, ry)
        roof.lineTo(rx + rw, ry + 52)
        roof.closeSubpath()
        p.setBrush(QColor("#5d4037"))
        p.drawPath(roof)
        door = QPainterPath(QPointF(rx + rw / 2 - 26, ry + rh))
        door.lineTo(rx + rw / 2 - 26, ry + 86)
        door.quadTo(rx + rw / 2, ry + 56, rx + rw / 2 + 26, ry + 86)
        door.lineTo(rx + rw / 2 + 26, ry + rh)
        door.closeSubpath()
        p.setBrush(QColor("#3e2723"))
        p.drawPath(door)
        p.setBrush(QColor("#fff8e1"))
        p.drawRoundedRect(QRectF(rx + rw / 2 - 30, ry + 32, 60, 16), 5, 5)
        p.setPen(QColor("#5d4037"))
        p.setFont(QFont("Arial", 9, QFont.Bold))
        p.drawText(QRectF(rx + rw / 2 - 30, ry + 32, 60, 16), Qt.AlignCenter, "רקסי")

    def spot_leaves(self, p, rx, ry, rw, rh):
        rnd = random.Random(21)
        p.setPen(Qt.NoPen)
        mound = QPainterPath(QPointF(rx, ry + rh))
        mound.quadTo(rx + rw / 2, ry - 10, rx + rw, ry + rh)
        mound.closeSubpath()
        p.setBrush(QColor("#e65100"))
        p.drawPath(mound)
        for _ in range(30):
            x = rx + rnd.uniform(14, rw - 14)
            top = ry + rh - (rh - 6) * (1 - abs(x - rx - rw / 2) / (rw / 2)) ** 0.6
            y = rnd.uniform(top + 6, ry + rh - 4)
            p.setBrush(QColor(rnd.choice(["#ff9800", "#ffb300", "#d84315", "#8d6e63"])))
            p.drawEllipse(QPointF(x, y), 8, 5)

    def spot_bin(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#43a047"))
        body = QPainterPath(QPointF(rx + 4, ry + 18))
        body.lineTo(rx + rw - 4, ry + 18)
        body.lineTo(rx + rw - 10, ry + rh)
        body.lineTo(rx + 10, ry + rh)
        body.closeSubpath()
        p.drawPath(body)
        p.setBrush(QColor("#2e7d32"))
        p.drawRoundedRect(QRectF(rx - 2, ry, rw + 4, 16), 5, 5)
        p.setPen(QPen(QColor("#e8f5e9"), 3, Qt.SolidLine, Qt.RoundCap))
        cx, cy = rx + rw / 2, ry + 58
        for k in range(3):
            a = k * 2.094
            p.drawLine(QPointF(cx + math.cos(a) * 12, cy + math.sin(a) * 12),
                       QPointF(cx + math.cos(a + 1.6) * 12, cy + math.sin(a + 1.6) * 12))

    def spot_barrow(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#5d4037"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + rw - 40, ry + 40), QPointF(rx + rw, ry + 20))
        p.drawLine(QPointF(rx + 40, ry + 44), QPointF(rx + 40, ry + rh - 4))
        p.drawLine(QPointF(rx + rw - 50, ry + 44), QPointF(rx + rw - 50, ry + rh - 4))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1976d2"))
        tub = QPainterPath(QPointF(rx + 6, ry + 10))
        tub.lineTo(rx + rw - 34, ry + 10)
        tub.lineTo(rx + rw - 54, ry + 48)
        tub.lineTo(rx + 26, ry + 48)
        tub.closeSubpath()
        p.drawPath(tub)
        p.setBrush(QColor("#ffe082"))
        p.drawEllipse(QRectF(rx + 14, ry + 2, rw - 56, 18))
        p.setBrush(QColor("#212121"))
        p.drawEllipse(QPointF(rx + 22, ry + rh - 12), 12, 12)

    def spot_sandbox(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(rx, ry + 10, rw, rh - 10))
        p.setBrush(QColor("#ffe082"))
        p.drawRect(QRectF(rx + 8, ry + 14, rw - 16, rh - 24))
        p.drawEllipse(QRectF(rx + 60, ry + 2, 80, 26))  # גבעת חול
        p.setBrush(QColor("#e53935"))
        bucket = QPainterPath(QPointF(rx + 22, ry + 20))
        bucket.lineTo(rx + 46, ry + 20)
        bucket.lineTo(rx + 42, ry + 46)
        bucket.lineTo(rx + 26, ry + 46)
        bucket.closeSubpath()
        p.drawPath(bucket)
        p.setPen(QPen(QColor("#1e88e5"), 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + rw - 30, ry + 14), QPointF(rx + rw - 44, ry + 44))

    # ---------- מחבואים במטבח ----------
    def spot_fridge(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#90a4ae"), 3))
        p.setBrush(QColor("#fafafa"))
        p.drawRoundedRect(QRectF(rx, ry, rw, rh), 10, 10)
        p.drawLine(QPointF(rx, ry + 82), QPointF(rx + rw, ry + 82))
        p.setPen(QPen(QColor("#78909c"), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + rw - 16, ry + 26), QPointF(rx + rw - 16, ry + 62))
        p.drawLine(QPointF(rx + rw - 16, ry + 100), QPointF(rx + rw - 16, ry + 160))
        p.setPen(Qt.NoPen)
        for (mx, my), color in (((rx + 30, ry + 120), "#ef5350"), ((rx + 56, ry + 150), "#ffca28"),
                                ((rx + 34, ry + 190), "#42a5f5")):
            p.setBrush(QColor(color))
            p.drawEllipse(QPointF(mx, my), 9, 9)  # מגנטים

    def spot_oven(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#cfd8dc"))
        p.drawRoundedRect(QRectF(rx, ry, rw, rh), 6, 6)
        p.setBrush(QColor("#37474f"))
        for i in range(4):
            p.drawEllipse(QPointF(rx + 22 + i * 29, ry + 12), 10, 5)
        p.setBrush(QColor("#263238"))
        p.drawRoundedRect(QRectF(rx + 16, ry + 46, rw - 32, rh - 60), 6, 6)
        p.setBrush(QColor(255, 167, 38, 120))
        p.drawRoundedRect(QRectF(rx + 24, ry + 54, rw - 48, rh - 76), 4, 4)
        p.setBrush(QColor("#455a64"))
        p.drawRect(QRectF(rx + 30, ry + 32, rw - 60, 6))

    def spot_sink(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(rx, ry + 16, rw, rh - 16))
        p.setBrush(QColor("#eceff1"))
        p.drawRect(QRectF(rx - 6, ry + 6, rw + 12, 14))
        p.setBrush(QColor("#b0bec5"))
        p.drawRoundedRect(QRectF(rx + rw / 2 - 34, ry + 8, 68, 9), 4, 4)
        p.setPen(QPen(QColor("#90a4ae"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + rw / 2, ry + 6), QPointF(rx + rw / 2, ry - 16))
        p.drawLine(QPointF(rx + rw / 2, ry - 16), QPointF(rx + rw / 2 - 14, ry - 16))
        p.setPen(QPen(QColor("#6d4c41"), 2))
        p.drawLine(QPointF(rx + rw / 2, ry + 26), QPointF(rx + rw / 2, ry + rh - 6))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(rx + rw / 2 - 10, ry + 60), 4, 4)
        p.drawEllipse(QPointF(rx + rw / 2 + 10, ry + 60), 4, 4)

    def spot_washer(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#90a4ae"), 3))
        p.setBrush(QColor("#fafafa"))
        p.drawRoundedRect(QRectF(rx, ry, rw, rh), 8, 8)
        p.drawLine(QPointF(rx, ry + 22), QPointF(rx + rw, ry + 22))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#42a5f5"))
        p.drawEllipse(QPointF(rx + 18, ry + 11), 5, 5)
        p.setPen(QPen(QColor("#78909c"), 6))
        p.setBrush(QColor("#1e3a5f"))
        p.drawEllipse(QPointF(rx + rw / 2, ry + 68), 34, 34)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(129, 212, 250, 90))
        p.drawEllipse(QPointF(rx + rw / 2 - 8, ry + 60), 12, 8)

    def spot_broom(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#5d4037"), 3))
        p.setBrush(QColor("#a1887f"))
        p.drawRect(QRectF(rx, ry, rw, rh - 8))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(rx + 18, ry + rh / 2), 5, 5)
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(rx + rw / 2 - 20, ry + 30, 40, 30))
        p.setPen(QColor("#fff8e1"))
        p.setFont(QFont("Arial", 18))
        p.drawText(QRectF(rx + rw / 2 - 20, ry + 30, 40, 30), Qt.AlignCenter, "🧹")

    def spot_ktable(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6d4c41"))
        for cx in (rx + 4, rx + rw - 36):
            p.drawRect(QRectF(cx, ry - 20, 32, 8))                 # משענת כיסא
            p.drawRect(QRectF(cx + 2, ry - 20, 6, rh + 20))
            p.drawRect(QRectF(cx + 24, ry - 20, 6, rh + 20))
        p.setBrush(QColor("#a1887f"))
        p.drawRect(QRectF(rx + 20, ry, rw - 40, 14))
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(rx + 30, ry + 14, 10, rh - 14))
        p.drawRect(QRectF(rx + rw - 40, ry + 14, 10, rh - 14))
        p.setBrush(QColor("#fff176"))
        p.drawEllipse(QPointF(rx + rw / 2, ry - 4), 22, 7)
        p.setBrush(QColor("#ef5350"))
        p.drawEllipse(QPointF(rx + rw / 2 - 6, ry - 10), 6, 6)
        p.setBrush(QColor("#66bb6a"))
        p.drawEllipse(QPointF(rx + rw / 2 + 8, ry - 10), 6, 6)

    def spot_pot(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#78909c"))
        p.drawRoundedRect(QRectF(rx + 6, ry + 18, rw - 12, rh - 18), 10, 10)
        p.drawRect(QRectF(rx - 6, ry + 32, 14, 8))
        p.drawRect(QRectF(rx + rw - 8, ry + 32, 14, 8))
        p.setBrush(QColor("#90a4ae"))
        p.drawEllipse(QRectF(rx, ry + 6, rw, 22))
        p.setBrush(QColor("#455a64"))
        p.drawEllipse(QPointF(rx + rw / 2, ry + 8), 8, 5)
        p.setBrush(QColor(255, 255, 255, 120))
        steam = math.sin(time.time() * 3) * 3
        for dx in (-20, 0, 20):
            p.drawEllipse(QPointF(rx + rw / 2 + dx + steam, ry - 8), 6, 9)

    def spot_sack(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#c8a26b"))
        sack = QPainterPath(QPointF(rx + 22, ry + 14))
        sack.quadTo(rx - 6, ry + rh * 0.6, rx + 14, ry + rh)
        sack.lineTo(rx + rw - 14, ry + rh)
        sack.quadTo(rx + rw + 6, ry + rh * 0.6, rx + rw - 22, ry + 14)
        sack.closeSubpath()
        p.drawPath(sack)
        p.setBrush(QColor("#a1887f"))
        p.drawRect(QRectF(rx + 26, ry + 8, rw - 52, 10))
        p.setBrush(QColor("#a1785c"))
        for px, py in ((rx + 40, ry + 4), (rx + 60, ry + 2), (rx + 52, ry - 6)):
            p.drawEllipse(QPointF(px, py), 9, 7)
        p.setPen(QColor("#6d4c41"))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRectF(rx, ry + 40, rw, 20), Qt.AlignCenter, "תפוחי אדמה")

    # ---------- מחבואים בחדר השינה ----------
    def spot_bed(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6d4c41"))
        p.drawRect(QRectF(rx, ry, 16, rh))
        p.drawRect(QRectF(rx + rw - 12, ry + 30, 12, rh - 30))
        p.setBrush(QColor("#fff8e1"))
        p.drawRoundedRect(QRectF(rx + 16, ry + 40, rw - 28, 30), 6, 6)
        p.setBrush(QColor("#ffffff"))
        p.drawRoundedRect(QRectF(rx + 22, ry + 26, 56, 26), 10, 10)
        p.setBrush(QColor("#5c6bc0"))
        blanket = QPainterPath(QPointF(rx + 70, ry + 34))
        blanket.lineTo(rx + rw - 10, ry + 36)
        blanket.lineTo(rx + rw - 6, ry + 96)
        blanket.lineTo(rx + 64, ry + 96)
        blanket.closeSubpath()
        p.drawPath(blanket)
        p.setBrush(QColor("#ffeb3b"))
        for sx, sy in ((rx + 110, ry + 60), (rx + 160, ry + 76), (rx + 205, ry + 56)):
            p.drawPath(star_path(sx, sy, 7))
        p.setBrush(QColor(0, 0, 0, 70))
        p.drawRect(QRectF(rx + 16, ry + 96, rw - 28, rh - 96))  # הצל מתחת למיטה

    def spot_dresser(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#5d4037"), 2))
        p.setBrush(QColor("#ce93d8"))
        p.drawRect(QRectF(rx, ry + 10, rw, rh - 18))
        for i in range(3):
            y = ry + 18 + i * 38
            p.setBrush(QColor("#e1bee7") if i else QColor("#f3e5f5"))
            p.drawRect(QRectF(rx + 8, y + (6 if i == 0 else 0), rw - 16, 32))
            p.setBrush(QColor("#ffd54f"))
            p.drawEllipse(QPointF(rx + rw / 2, y + 16 + (6 if i == 0 else 0)), 5, 5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#5d4037"))
        p.drawRect(QRectF(rx + 6, ry + rh - 8, 10, 8))
        p.drawRect(QRectF(rx + rw - 16, ry + rh - 8, 10, 8))
        p.setBrush(QColor("#ffb74d"))
        p.drawEllipse(QPointF(rx + 30, ry + 2), 12, 10)  # מנורת לילה

    def spot_teddy(self, p, rx, ry, rw, rh):
        brown, light = QColor("#a1887f"), QColor("#d7ccc8")
        cx = rx + rw / 2
        p.setPen(Qt.NoPen)
        p.setBrush(brown)
        p.drawEllipse(QPointF(cx, ry + rh - 46), 50, 46)            # גוף
        for side in (-1, 1):
            p.drawEllipse(QPointF(cx + side * 40, ry + rh - 12), 18, 13)  # רגליים
            p.drawEllipse(QPointF(cx + side * 30, ry + 22), 15, 15)       # אוזניים
        p.drawEllipse(QPointF(cx, ry + 50), 38, 34)                 # ראש
        p.setBrush(light)
        p.drawEllipse(QPointF(cx, ry + rh - 42), 30, 28)
        p.drawEllipse(QPointF(cx, ry + 60), 16, 12)
        for side in (-1, 1):
            p.drawEllipse(QPointF(cx + side * 30, ry + 22), 8, 8)
        p.setBrush(INK)
        p.drawEllipse(QPointF(cx - 13, ry + 44), 4, 4)
        p.drawEllipse(QPointF(cx + 13, ry + 44), 4, 4)
        p.drawEllipse(QPointF(cx, ry + 56), 5, 4)
        p.setBrush(QColor("#e53935"))
        p.drawEllipse(QPointF(cx - 9, ry + 84), 9, 6)
        p.drawEllipse(QPointF(cx + 9, ry + 84), 9, 6)

    def spot_tent(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        tent = QPainterPath(QPointF(rx, ry + rh))
        tent.lineTo(rx + rw / 2, ry)
        tent.lineTo(rx + rw, ry + rh)
        tent.closeSubpath()
        p.setBrush(QColor("#ff7043"))
        p.drawPath(tent)
        stripe = QPainterPath(QPointF(rx + rw * 0.25, ry + rh))
        stripe.lineTo(rx + rw / 2, ry)
        stripe.lineTo(rx + rw * 0.4, ry + rh)
        stripe.closeSubpath()
        p.setBrush(QColor("#ffca28"))
        p.drawPath(stripe)
        door = QPainterPath(QPointF(rx + rw / 2 - 30, ry + rh))
        door.lineTo(rx + rw / 2, ry + 70)
        door.lineTo(rx + rw / 2 + 30, ry + rh)
        door.closeSubpath()
        p.setBrush(QColor("#3e2723"))
        p.drawPath(door)
        p.setBrush(QColor("#ffeb3b"))
        p.drawPath(star_path(rx + rw / 2, ry - 6, 8))

    def spot_chest(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#4e342e"), 2))
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(rx, ry + 22, rw, rh - 22))
        lid = QPainterPath(QPointF(rx - 2, ry + 22))
        lid.quadTo(rx + rw / 2, ry - 6, rx + rw + 2, ry + 22)
        lid.closeSubpath()
        p.setBrush(QColor("#a1887f"))
        p.drawPath(lid)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffca28"))
        p.drawRect(QRectF(rx + rw / 2 - 8, ry + 22, 16, 16))
        p.setBrush(QColor("#ef5350"))
        p.drawEllipse(QPointF(rx + 20, ry + 14), 8, 8)  # כדור שמציץ
        p.setPen(QColor("#fff8e1"))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRectF(rx, ry + 44, rw, 26), Qt.AlignCenter, "צעצועים")

    def spot_beanbag(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#26c6da"))
        bag = QPainterPath(QPointF(rx, ry + rh))
        bag.quadTo(rx - 6, ry + 20, rx + rw / 2, ry + 6)
        bag.quadTo(rx + rw + 6, ry + 20, rx + rw, ry + rh)
        bag.closeSubpath()
        p.drawPath(bag)
        p.setBrush(QColor("#00acc1"))
        p.drawEllipse(QPointF(rx + rw / 2, ry + 44), 34, 16)
        p.setBrush(QColor(255, 255, 255, 90))
        p.drawEllipse(QPointF(rx + 32, ry + 30), 12, 6)

    def spot_clothes(self, p, rx, ry, rw, rh):
        rnd = random.Random(31)
        p.setPen(Qt.NoPen)
        for _ in range(14):
            x = rx + rnd.uniform(16, rw - 16)
            y = ry + rnd.uniform(16, rh - 10)
            p.setBrush(QColor(rnd.choice(["#42a5f5", "#ef5350", "#ffca28", "#66bb6a", "#ab47bc", "#ffffff"])))
            p.drawRoundedRect(QRectF(x - 26, y - 12, 52, 24), 9, 9)
        p.setBrush(QColor("#ef5350"))
        p.drawRoundedRect(QRectF(rx + 30, ry + 2, 60, 18), 7, 7)  # גרב על הערימה

    def spot_desk(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#8d6e63"))
        p.drawRect(QRectF(rx, ry + 20, rw, 14))
        p.drawRect(QRectF(rx + 8, ry + 34, 12, rh - 34))
        p.drawRect(QRectF(rx + rw - 60, ry + 34, 52, rh - 34))
        p.setBrush(QColor("#a1887f"))
        p.drawRect(QRectF(rx + rw - 54, ry + 44, 40, 18))
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(rx + rw - 34, ry + 53), 3, 3)
        p.setPen(QPen(QColor("#455a64"), 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + 40, ry + 20), QPointF(rx + 46, ry - 14))
        p.drawLine(QPointF(rx + 46, ry - 14), QPointF(rx + 66, ry - 20))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffeb3b"))
        p.drawEllipse(QPointF(rx + 72, ry - 16), 10, 7)          # מנורה
        p.setBrush(QColor("#42a5f5"))
        p.drawRect(QRectF(rx + 96, ry + 6, 34, 14))              # ספרים
        p.setBrush(QColor("#ef5350"))
        p.drawRect(QRectF(rx + 100, ry - 4, 28, 10))

    # ---------- מחבואים בחוף הים ----------
    def spot_palm(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#8d6e63"), 24, Qt.SolidLine, Qt.RoundCap))
        trunk = QPainterPath(QPointF(rx + 70, ry + rh))
        trunk.quadTo(rx + 90, ry + 140, rx + 64, ry + 60)
        p.setBrush(Qt.NoBrush)
        p.drawPath(trunk)
        p.setPen(QPen(QColor("#6d4c41"), 2))
        for k in range(6):
            y = ry + 90 + k * 30
            p.drawLine(QPointF(rx + 62 + k * 2, y), QPointF(rx + 86 - k, y + 4))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#2e7d32"))
        for ang in (-150, -110, -70, -30, 10, 200):
            p.save()
            p.translate(rx + 64, ry + 58)
            p.rotate(ang)
            leaf = QPainterPath(QPointF(0, 0))
            leaf.quadTo(36, -18, 74, 6)
            leaf.quadTo(36, 4, 0, 0)
            p.drawPath(leaf)
            p.restore()
        p.setBrush(QColor("#6d4c41"))
        for cx, cy in ((rx + 58, ry + 66), (rx + 70, ry + 70)):
            p.drawEllipse(QPointF(cx, cy), 8, 8)  # קוקוסים

    def spot_umbrella(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#8d6e63"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + rw / 2, ry + 20), QPointF(rx + rw / 2 + 10, ry + rh))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ef5350"))
        canopy = QPainterPath(QPointF(rx, ry + 70))
        canopy.quadTo(rx + rw / 2, ry - 20, rx + rw, ry + 70)
        canopy.closeSubpath()
        p.drawPath(canopy)
        p.setBrush(QColor("#ffffff"))
        for k in (0.2, 0.6):
            seg = QPainterPath(QPointF(rx + rw * k, ry + 70))
            seg.lineTo(rx + rw / 2, ry + 25)
            seg.lineTo(rx + rw * (k + 0.2), ry + 70)
            seg.closeSubpath()
            p.drawPath(seg)
        p.setBrush(QColor("#4dd0e1"))
        p.drawRoundedRect(QRectF(rx + 14, ry + rh - 26, rw - 28, 20), 6, 6)   # מגבת
        p.setBrush(QColor("#ffffff"))
        p.drawRect(QRectF(rx + 14, ry + rh - 18, rw - 28, 5))

    def spot_boat(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#5d4037"), 2))
        p.setBrush(QColor("#ffffff"))
        p.drawLine(QPointF(rx + rw / 2, ry + 50), QPointF(rx + rw / 2, ry - 6))
        sail = QPainterPath(QPointF(rx + rw / 2 + 2, ry - 4))
        sail.lineTo(rx + rw / 2 + 50, ry + 44)
        sail.lineTo(rx + rw / 2 + 2, ry + 44)
        sail.closeSubpath()
        p.drawPath(sail)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1565c0"))
        hull = QPainterPath(QPointF(rx, ry + 48))
        hull.lineTo(rx + rw, ry + 48)
        hull.quadTo(rx + rw - 20, ry + rh, rx + rw / 2, ry + rh)
        hull.quadTo(rx + 20, ry + rh, rx, ry + 48)
        p.drawPath(hull)
        p.setBrush(QColor("#ffffff"))
        p.drawRect(QRectF(rx + 14, ry + 58, rw - 28, 7))
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(QRectF(rx, ry + 66, rw, 22), Qt.AlignCenter, "פיקו 1")

    def spot_tower(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#8d6e63"), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + 20, ry + rh), QPointF(rx + 34, ry + 110))
        p.drawLine(QPointF(rx + rw - 20, ry + rh), QPointF(rx + rw - 34, ry + 110))
        p.drawLine(QPointF(rx + 26, ry + 180), QPointF(rx + rw - 26, ry + 180))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ef5350"))
        p.drawRect(QRectF(rx + 16, ry + 30, rw - 32, 84))
        p.setBrush(QColor("#ffffff"))
        p.drawRect(QRectF(rx + 16, ry + 78, rw - 32, 12))
        roof = QPainterPath(QPointF(rx, ry + 34))
        roof.lineTo(rx + rw / 2, ry)
        roof.lineTo(rx + rw, ry + 34)
        roof.closeSubpath()
        p.setBrush(QColor("#c62828"))
        p.drawPath(roof)
        p.setBrush(QColor("#3e2723"))
        p.drawRect(QRectF(rx + rw / 2 - 30, ry + 40, 60, 32))  # חלון
        p.setBrush(QColor("#ffeb3b"))
        flag = QPainterPath(QPointF(rx + rw / 2, ry - 2))
        flag.lineTo(rx + rw / 2 + 22, ry - 12)
        flag.lineTo(rx + rw / 2, ry - 22)
        flag.closeSubpath()
        p.drawPath(flag)

    def spot_castle(self, p, rx, ry, rw, rh):
        sand, dark = QColor("#ffd54f"), QColor("#ffb300")
        p.setPen(Qt.NoPen)
        p.setBrush(sand)
        p.drawRect(QRectF(rx + 20, ry + 40, rw - 40, rh - 40))
        for tx in (rx + 4, rx + rw / 2 - 20, rx + rw - 44):
            p.drawRect(QRectF(tx, ry + 14, 40, rh - 14))
            p.setBrush(dark)
            for k in range(3):
                p.drawRect(QRectF(tx + 2 + k * 14, ry + 6, 9, 10))
            p.setBrush(sand)
        p.setBrush(QColor("#8d6e63"))
        door = QPainterPath(QPointF(rx + rw / 2 - 14, ry + rh))
        door.lineTo(rx + rw / 2 - 14, ry + rh - 26)
        door.quadTo(rx + rw / 2, ry + rh - 42, rx + rw / 2 + 14, ry + rh - 26)
        door.lineTo(rx + rw / 2 + 14, ry + rh)
        door.closeSubpath()
        p.drawPath(door)
        p.setBrush(QColor("#e53935"))
        flag = QPainterPath(QPointF(rx + rw / 2, ry - 2))
        flag.lineTo(rx + rw / 2 + 18, ry - 10)
        flag.lineTo(rx + rw / 2, ry - 18)
        flag.closeSubpath()
        p.drawPath(flag)

    def spot_beachchair(self, p, rx, ry, rw, rh):
        p.setPen(QPen(QColor("#8d6e63"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + 10, ry + rh), QPointF(rx + 50, ry + 40))
        p.drawLine(QPointF(rx + rw - 10, ry + rh), QPointF(rx + 40, ry + rh - 30))
        p.drawLine(QPointF(rx + 50, ry + 40), QPointF(rx + rw - 6, ry + 40))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#29b6f6"))
        seat = QPainterPath(QPointF(rx + 14, ry + 4))
        seat.lineTo(rx + 44, ry + 4)
        seat.lineTo(rx + rw - 10, ry + 44)
        seat.lineTo(rx + rw - 30, ry + 54)
        seat.lineTo(rx + 34, ry + 30)
        seat.closeSubpath()
        p.drawPath(seat)
        p.setBrush(QColor("#ffffff"))
        p.drawRect(QRectF(rx + 24, ry + 10, 14, 10))
        p.setBrush(QColor("#ffeb3b"))
        p.drawEllipse(QPointF(rx + rw - 30, ry + 64), 10, 10)  # כדור ים

    def spot_rock(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        rock = QPainterPath(QPointF(rx, ry + rh))
        rock.quadTo(rx - 4, ry + 30, rx + 40, ry + 8)
        rock.quadTo(rx + 90, ry - 8, rx + rw - 10, ry + 30)
        rock.quadTo(rx + rw + 6, ry + 60, rx + rw, ry + rh)
        rock.closeSubpath()
        p.setBrush(QColor("#78909c"))
        p.drawPath(rock)
        p.setBrush(QColor("#90a4ae"))
        p.drawEllipse(QPointF(rx + 60, ry + 34), 26, 14)
        p.setBrush(QColor("#ff7043"))
        p.drawEllipse(QPointF(rx + rw - 36, ry + rh - 14), 12, 8)  # סרטן
        p.setPen(QPen(QColor("#ff7043"), 2))
        p.drawLine(QPointF(rx + rw - 46, ry + rh - 16), QPointF(rx + rw - 52, ry + rh - 24))
        p.drawLine(QPointF(rx + rw - 26, ry + rh - 16), QPointF(rx + rw - 20, ry + rh - 24))

    def spot_cooler(self, p, rx, ry, rw, rh):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1e88e5"))
        p.drawRoundedRect(QRectF(rx, ry + 16, rw, rh - 16), 8, 8)
        p.setBrush(QColor("#fafafa"))
        p.drawRoundedRect(QRectF(rx - 4, ry + 4, rw + 8, 18), 6, 6)
        p.setPen(QPen(QColor("#bdbdbd"), 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(rx + 30, ry + 4), QPointF(rx + rw - 30, ry + 4))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#bbdefb"))
        p.drawRoundedRect(QRectF(rx + 20, ry + 34, rw - 40, 20), 5, 5)

    def draw_peek(self, p):
        """פיקו מציץ לרגע: אנטנה, עיניים או רגליים."""
        x, y = self.spot["at"]
        k = self.peek
        rise = min(1, k / 8, (34 - k + 1) / 8)  # עולה ויורד בעדינות
        kind = self.spot["peek"]
        if kind == "antenna":
            top = y - 22 * rise
            p.setPen(QPen(BOLT, 3, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x, y), QPointF(x, top))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffd54f"))
            p.drawEllipse(QPointF(x, top - 3), 5, 5)
        elif kind == "eyes":
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(20, 10, 0, int(220 * rise)))
            p.drawEllipse(QPointF(x, y), 18, 11)
            for ex in (x - 7, x + 7):
                p.setBrush(QColor(255, 255, 255, int(255 * rise)))
                p.drawEllipse(QPointF(ex, y), 5, 6)
                p.setBrush(QColor(20, 10, 0, int(255 * rise)))
                p.drawEllipse(QPointF(ex + 1.5, y + 1), 2.2, 2.8)
        elif kind == "feet":
            p.setPen(QPen(HEAD_DARK, 2))
            p.setBrush(HEAD)
            for fx in (x - 12, x + 12):
                p.drawEllipse(QPointF(fx, y - 3 * rise), 10, 6)

    def draw_popped(self, p):
        """פיקו קופץ מהמחבוא: מופתע כשמצאת אותו, צוחק כשלא."""
        rx, ry, rw, rh = self.spot["rect"]
        elapsed = (130 if self.state == "found" else 140) - self.t
        jump = min(1, elapsed / 12)
        x = rx + rw / 2
        y = max(ry + 10 - 46 * jump, 150) + math.sin(elapsed * 0.25) * 3 * jump  # לא מסתיר את הלוחות למעלה
        r = 26
        p.setPen(Qt.NoPen)
        p.setBrush(HEAD_DARK)
        p.drawRoundedRect(QRectF(x - 18, y + r - 4, 36, 30), 10, 10)
        p.setPen(QPen(BOLT, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, y - r), QPointF(x, y - r - 12))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(x, y - r - 14), 5, 5)
        p.setPen(QPen(HEAD_DARK, 3))
        p.setBrush(HEAD)
        p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(Qt.NoPen)
        p.setBrush(FACE)
        p.drawEllipse(QPointF(x, y + 3), r * 0.74, r * 0.64)
        found = self.state == "found"
        if found:
            p.setBrush(INK)
            for ex in (x - 8, x + 8):
                p.drawEllipse(QPointF(ex, y - 2), 4, 5)
            p.drawEllipse(QPointF(x, y + 11), 4.5, 5.5)  # פה פעור
        else:
            p.setPen(QPen(INK, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for ex, d in ((x - 8, 1), (x + 8, -1)):
                eye = QPainterPath(QPointF(ex - d * 4, y - 6))
                eye.lineTo(ex + d * 2, y - 2)
                eye.lineTo(ex - d * 4, y + 2)
                p.drawPath(eye)
            p.setPen(Qt.NoPen)
            p.setBrush(INK)
            mouth = QPainterPath(QPointF(x - 9, y + 6))
            mouth.lineTo(x + 9, y + 6)
            mouth.quadTo(x, y + 20, x - 9, y + 6)
            p.drawPath(mouth)
        draw_accessories(p, current_outfit(), x, y, r, top=-0.95, eye_y=-0.08, neck_y=0.95,
                         t=time.time(), skip=("glasses",) if not found else ())
        word = "מצאת אותי!" if found else "הנה אני! 😎"
        tx = clamp(x, 100, self.W - 100)  # שהכיתוב לא ייחתך בקצה המסך
        p.setFont(QFont("Arial", 16, QFont.Black))
        p.setPen(QColor(40, 20, 0))
        p.drawText(QRectF(tx - 90 + 2, y - r - 58 + 2, 180, 30), Qt.AlignCenter, word)
        p.setPen(QColor("#ffeb3b"))
        p.drawText(QRectF(tx - 90, y - r - 58, 180, 30), Qt.AlignCenter, word)

    def draw_hud(self, p):
        W = self.W
        if self.state not in ("seek", "found", "missed"):
            return
        secs = max(0, math.ceil(self.time_left / 60))
        pill = QRectF(W - 168, 14, 150, 30)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(pill, 10, 10)
        p.setPen(QColor("#ff5252") if secs <= 5 else Qt.white)
        p.setFont(QFont("Arial", 14, QFont.Bold))
        p.drawText(pill, Qt.AlignCenter, f"זמן: {secs} ⏱")
        pill2 = QRectF(18, 14, 150, 30)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(pill2, 10, 10)
        p.setPen(Qt.white)
        p.drawText(pill2, Qt.AlignCenter, "🔍" * self.guesses + "  ✗" * (self.GUESSES - self.guesses))


# ---------------------------------------------------------------- מירוץ טיפוס נגד פיקו
CLIMB_LINES = {
    "start": ["פיקו: מירוץ טיפוס? אני מטפס כמו קוף-רובוט! 🐒🤖", "פיקו: נתראה בפסגה! כלומר, אני אחכה לך שם. 😎"],
    "piko_throw": ["כדור שלג מגיע! ❄️ תתחמק אם אתה יכול!", "הופה! מתנה קרה מלמעלה! 😎"],
    "hit_player": ["חחח! קפאת כמו ארטיק! 🥶", "בול! כדור השלג שלי פגע!"],
    "hit_piko": ["הייי! כדור שלג ישר לאנטנה! 🥶", "קר לי! זה לא הוגן!"],
    "piko_spikes": ["אוי! מי שם פה קוצים?!", "אאוץ'! הברגים שלי!"],
    "piko_lead": ["ביי ביי! נתראה למעלה! 😎", "אני כבר רואה את הפסגה. ואתה רואה את הרגליים שלי."],
    "player_lead": ["רגע! איך עקפת אותי?!", "נתתי לך לעקוף. אני נדיב היום."],
    "piko_race": ["פיקו הגיע לפסגה! מלך ההרים! 🏔️👑", "ראשון בפסגה! כמו תמיד."],
    "player_race": ["הגעת ראשון?! ...הרגליים שלי היו מלאות בבוץ. ברור.", "מה?! טיפסת מהר מדי! רימית!"],
}


class Climber:
    def __init__(self, piko):
        self.piko = piko
        self.x, self.y = ClimbGame.LW / 2, 0.0   # y = הרגליים. 0 זו האדמה, למעלה זה מינוס
        self.vx = self.vy = 0.0
        self.on = "ground"       # על מה הוא עומד: "ground", משטח, או None באוויר
        self.stun = 0
        self.nofall = 0
        self.face = 1
        self.snow_cd = 120
        self.skill = 1.0
        self.cam = -110.0

    @property
    def height(self):
        return -self.y


class ClimbGame(FootballGame):
    """מירוץ טיפוס נגד פיקו, במסך מפוצל: אתה משמאל, פיקו מימין, על אותו הר בדיוק.
    חצים או A/D לזוז, למעלה/W/רווח לקפוץ, X או Z לזרוק כדור שלג על פיקו. מי שמנצח 2 מירוצים מנצח."""

    W, H = 800, 500
    LW = 370                 # רוחב כל צד
    ROW = 72                 # המרחק בין קומות
    ROWS = 30                # כמה קומות עד הפסגה
    G, JUMP, SPRING = 0.6, -12.5, -19.5
    SPEED = 4.0
    SY0 = 330                # איפה המטפס על המסך
    WIN = 2
    SNOW_CD = 300
    PIKO_SKILL = 0.9         # כמה פיקו מהיר בבסיס (1 = מהיר כמוך)
    PIKO_WAIT = (9, 22)      # כמה פריימים הוא "חושב" לפני כל קפיצה
    PIKO_ERR = 17            # כמה הוא מפספס בכיוון הקפיצה

    def __init__(self):
        self.pressed = set()
        self.handicap = 0    # עולה כשאתה מפסיד במשחק, יורד כשאתה מנצח
        super().__init__()
        self.setWindowTitle("מירוץ טיפוס נגד פיקו")

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.race_no = 0
        h = self.handicap
        self.wait_range = tuple(int(v * (1 + 0.3 * h)) for v in self.PIKO_WAIT)
        self.err = self.PIKO_ERR + 5 * h
        if h:
            self.say(f"פיקו: טוב, אני נותן לך הנחה ({h} מתוך 3). אני אטפס לאט... יחסית. 😏", 200)
        else:
            self.say(random.choice(CLIMB_LINES["start"]), 200)
        self.emotion.emit("proud")
        self.new_race()

    def new_race(self):
        self.race_no += 1
        layout = self.make_layout(random.Random())
        # לכל צד עותק משלו של המשטחים (שבירה ותזוזה בנפרד), אבל אותו הר בדיוק
        self.plats = {False: [dict(pl) for pl in layout], True: [dict(pl) for pl in layout]}
        self.player, self.piko = Climber(False), Climber(True)
        self.snowballs = []      # [צד המטרה, x, y, vy, זמן אזהרה]
        self.sparks = []         # [צד, x, y, מילה, זמן]
        self.frame = 0
        self.countdown = 200
        self.race_end = 0
        self.leader = None
        self.ai_wait, self.ai_target, self.ai_err, self.ai_seen = 20, None, 0.0, set()
        self.ai_dodge = None
        self.pressed.clear()

    def make_layout(self, rnd):
        LW, ROW = self.LW, self.ROW
        plats = []
        x = LW / 2
        plats_main_kind = "normal"
        for k in range(1, self.ROWS + 1):
            y = -ROW * k
            if k == self.ROWS:
                plats.append(dict(x=LW / 2, base=LW / 2, w=170, y=y, kind="flag", amp=0, spd=0, ph=0))
                break
            # המשטח הראשי תמיד אפשר להגיע אליו מהקומה הקודמת.
            # אחרי משטח מתפורר, הבא קרוב כדי שאפשר יהיה לקפוץ מיד
            reach = 70 if plats and plats_main_kind == "crumble" else 130
            x = clamp(x + rnd.uniform(-reach, reach), 60, LW - 60)
            kind = "normal"
            if k > 2:
                kind = rnd.choices(["normal", "crumble", "moving", "spring", "halfspike"], [52, 16, 14, 8, 10])[0]
            w = rnd.uniform(78, 112)
            amp = 46 if kind == "moving" else 0
            base = clamp(x, 40 + w / 2 + amp, LW - 40 - w / 2 - amp)
            plats.append(dict(x=base, base=base, w=w, y=y, kind=kind, amp=amp, spd=rnd.uniform(0.02, 0.035),
                              ph=rnd.uniform(0, 6), side=rnd.choice([-1, 1])))
            x = base
            plats_main_kind = kind
            if rnd.random() < 0.55:   # משטח נוסף, לפעמים מלכודת
                ox = clamp(rnd.uniform(50, LW - 50), 50, LW - 50)
                if abs(ox - base) > 120:
                    extra = rnd.choices(["normal", "spikes", "spring", "crumble"], [45, 25, 15, 15])[0]
                    plats.append(dict(x=ox, base=ox, w=rnd.uniform(66, 96), y=y, kind=extra, amp=0, spd=0,
                                      ph=0, side=1))
        for pl in plats:
            pl.update(crumble=0, broken=0, dx=0.0, cool=0)
        return plats

    # ---------- מקלדת ----------
    def keyPressEvent(self, event):
        key = self.key_of(event)
        if not event.isAutoRepeat():
            self.pressed.add(key)
        super().keyPressEvent(event)

    def player_input(self):
        k, pr = self.keys, self.pressed
        return dict(left=Qt.Key_Left in k or Qt.Key_A in k,
                    right=Qt.Key_Right in k or Qt.Key_D in k,
                    jump=bool(pr & {Qt.Key_Up, Qt.Key_W, Qt.Key_Space}) or
                         (Qt.Key_Up in k or Qt.Key_W in k or Qt.Key_Space in k),
                    snow=bool(pr & {Qt.Key_X, Qt.Key_Z}))

    # ---------- לולאת המשחק ----------
    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        if not self.over:
            self.step()
        self.pressed.clear()
        self.update()

    def step(self):
        self.frame += 1
        for s in self.sparks:
            s[2] -= 0.6
            s[4] -= 1
        self.sparks = [s for s in self.sparks if s[4] > 0]
        for side in (False, True):
            for pl in self.plats[side]:
                old = pl["x"]
                if pl["amp"]:
                    pl["x"] = pl["base"] + math.sin(self.frame * pl["spd"] + pl["ph"]) * pl["amp"]
                pl["dx"] = pl["x"] - old
                if pl["crumble"] > 0:
                    pl["crumble"] -= 1
                    if pl["crumble"] == 0:
                        pl["broken"] = 150   # נשבר, וחוזר אחרי 2.5 שניות
                elif pl["broken"] > 0:
                    pl["broken"] -= 1
                if pl["cool"] > 0:
                    pl["cool"] -= 1   # קפיץ שהשתמשו בו נח רגע
        for c in (self.player, self.piko):
            c.cam += (min(c.y, -110) - c.cam) * 0.12
        if self.countdown > 0:
            self.countdown -= 1
            return
        if self.race_end > 0:
            self.race_end -= 1
            if self.race_end == 0:
                self.after_race()
            return
        gap = (self.player.height - self.piko.height) / self.ROW
        self.piko.skill = clamp(self.PIKO_SKILL + gap * 0.05, 0.7, 1.12)   # מאחור הוא מתאמץ, מקדימה הוא שחצן
        self.move(self.player, self.player_input())
        self.move(self.piko, self.piko_input())
        self.move_snow()
        leader = "player" if self.player.height > self.piko.height + 20 else \
                 "piko" if self.piko.height > self.player.height + 20 else self.leader
        if leader != self.leader and self.leader is not None and random.random() < 0.6:
            self.say(random.choice(CLIMB_LINES["piko_lead" if leader == "piko" else "player_lead"]), 90)
            self.emotion.emit("proud" if leader == "piko" else "surprised")
        self.leader = leader

    def spark(self, c, word, dy=-60):
        self.sparks.append([c.piko, c.x, c.y + dy, word, 45])

    def move(self, c, inp):
        plats = self.plats[c.piko]
        c.snow_cd = max(0, c.snow_cd - 1)
        c.nofall = max(0, c.nofall - 1)
        if c.stun > 0:
            c.stun -= 1
            inp = {}
        if inp.get("snow") and c.snow_cd == 0:
            self.throw_snow(c)
        move = inp.get("right", False) - inp.get("left", False)
        if move:
            c.face = move
        target = move * self.SPEED * c.skill
        c.vx += (target - c.vx) * (0.4 if c.on else 0.18)
        if c.on and c.on != "ground":
            c.x += c.on["dx"]   # משטח שזז לוקח אותך איתו
        if c.on and inp.get("jump"):
            c.vy, c.on = self.JUMP, None
        c.x = clamp(c.x + c.vx, 14, self.LW - 14)
        if c.on:
            if c.on != "ground" and (c.on["broken"] or abs(c.x - c.on["x"]) > c.on["w"] / 2 + 6):
                c.on = None   # יצא מהקצה או שהמשטח נשבר
            else:
                c.vy = 0.0
                return
        prev = c.y
        c.vy = min(c.vy + self.G, 14)
        c.y += c.vy
        if c.y >= 0:
            c.y, c.vy, c.on = 0.0, 0.0, "ground"
            return
        if c.vy <= 0 or c.nofall:
            return
        for pl in plats:
            if pl["broken"] or not (prev <= pl["y"] <= c.y):
                continue
            if abs(c.x - pl["x"]) > pl["w"] / 2 + 6:
                continue
            self.land(c, pl)
            return

    def land(self, c, pl):
        c.y, c.vy = pl["y"], 0.0
        kind = pl["kind"]
        spiked = kind == "spikes" or (kind == "halfspike" and (c.x - pl["x"]) * pl["side"] > 0)
        if spiked:
            c.stun, c.nofall, c.vy, c.on = 40, 16, -3.0, None
            self.spark(c, "אאוץ'! 🌵")
            if c.piko:
                self.say(random.choice(CLIMB_LINES["piko_spikes"]), 70)
                self.emotion.emit("angry")
            return
        if kind == "spring" and pl["cool"] == 0:
            pl["cool"] = 120   # אחרי קפיצה הקפיץ מכווץ ל-2 שניות ומתנהג כמו משטח רגיל
            c.vy, c.on = self.SPRING, None
            self.spark(c, "בוינג!")
            if c.piko:
                self.ai_target = None   # הקפיץ העיף אותו: יחפש משטח חדש לנחות עליו
            return
        c.on = pl
        if kind == "crumble" and pl["crumble"] == 0:
            pl["crumble"] = 70   # מתפורר אחרי 1.2 שניות
        if kind == "flag" and not self.race_end:
            self.end_race(c)

    def throw_snow(self, c):
        target = self.piko if not c.piko else self.player
        c.snow_cd = self.SNOW_CD
        self.snowballs.append([target.piko, target.x + random.uniform(-8, 8), target.y - 330, 0.0, 50])
        if c.piko:
            self.say(random.choice(CLIMB_LINES["piko_throw"]), 80)
        self.spark(c, "❄️ זריקה!")

    def move_snow(self):
        alive = []
        for sb in self.snowballs:
            side, x, y, vy, warn = sb
            target = self.piko if side else self.player
            if warn > 0:
                sb[4] -= 1
                sb[2] = target.y - 330 + (50 - sb[4]) * 0.5  # נשאר מעל המסך בזמן האזהרה
                alive.append(sb)
                continue
            sb[3] = vy + 0.4
            sb[2] = y + sb[3]
            if abs(x - target.x) < 22 and target.y - 44 < sb[2] < target.y + 6 and target.stun == 0:
                target.stun = 45
                self.sparks.append([side, target.x, target.y - 70, "בום! ❄️", 45])
                if side:
                    self.say(random.choice(CLIMB_LINES["hit_piko"]), 80)
                    self.emotion.emit("sad")
                else:
                    self.say(random.choice(CLIMB_LINES["hit_player"]), 80)
                    self.emotion.emit("laugh")
                continue
            if sb[2] < target.y + 500:
                alive.append(sb)
        self.snowballs = alive

    def end_race(self, winner):
        self.score[1 if winner.piko else 0] += 1
        self.race_end = 160
        self.race_winner = winner
        if winner.piko:
            self.say(random.choice(CLIMB_LINES["piko_race"]), 160)
            self.emotion.emit(random.choice(["proud", "laugh"]))
        else:
            self.say(random.choice(CLIMB_LINES["player_race"]), 160)
            self.emotion.emit(random.choice(["angry", "surprised"]))

    def after_race(self):
        you, piko = self.score
        if max(self.score) >= self.WIN:
            self.over = True
            if piko > you:
                self.say(f"פיקו ניצח {piko}-{you}! מלך ההרים של היקום. 🏔️👑", 10 ** 9)
                self.emotion.emit("proud")
                self.handicap = min(3, self.handicap + 1)   # בפעם הבאה הוא יותר איטי
            else:
                self.say(f"ניצחת {you}-{piko}?! ...היו לי נעליים חלקות. בכל המירוצים. ברור.", 10 ** 9)
                self.emotion.emit("surprised")
                self.handicap = max(0, self.handicap - 1)
            self.finished.emit(you, piko)
        else:
            self.new_race()

    # ---------- המוח של פיקו בהר ----------
    def piko_input(self):
        c, you = self.piko, self.player
        inp = {}
        if c.stun:
            return inp
        # זורק כדור שלג מדי פעם
        if c.snow_cd == 0 and random.random() < 0.006:
            inp["snow"] = True
        # מתחמק מכדור שלג שמגיע אליו (לא תמיד מצליח)
        for sb in self.snowballs:
            if sb[0] and id(sb) not in self.ai_seen and abs(sb[1] - c.x) < 34:
                self.ai_seen.add(id(sb))
                if random.random() < 0.6 and c.on:
                    self.ai_dodge = (sb, 1 if c.x < sb[1] else -1)
        dodge = getattr(self, "ai_dodge", None)
        if dodge and dodge[0] in self.snowballs and abs(dodge[0][1] - c.x) < 40 and c.on:
            inp["right" if dodge[1] > 0 else "left"] = True
            inp["right" if dodge[1] < 0 else "left"] = False
            return inp
        if c.on:
            if self.ai_wait > 0:
                self.ai_wait -= 1
                return inp
            t = self.pick_target(c)
            if t is None:
                return inp
            self.ai_target = t
            dx = t["x"] - c.x
            if abs(dx) < 95:
                inp["jump"] = True
                self.ai_err = random.gauss(0, self.err / c.skill)
                self.ai_wait = int(random.randint(*self.wait_range) / c.skill)
            else:
                cur = c.on
                if cur != "ground":
                    edge = cur["x"] + (cur["w"] / 2 - 8) * (1 if dx > 0 else -1)
                    if abs(c.x - edge) < 5:
                        inp["jump"] = True  # קפיצה ארוכה מהקצה
                        self.ai_err = random.gauss(0, self.err / c.skill)
                        self.ai_wait = int(random.randint(*self.wait_range) / c.skill)
                        return inp
                inp["right" if dx > 0 else "left"] = True
        else:
            t = self.ai_target
            if t is None and c.vy > 0:
                t = self.ai_target = self.pick_landing(c)
            if t is not None:
                dx = t["x"] + self.ai_err - c.x
                if abs(dx) > 6:
                    inp["right" if dx > 0 else "left"] = True
        return inp

    def pick_landing(self, c):
        """באוויר, בירידה: בוחר את המשטח הכי גבוה שאפשר לנחות עליו מתחתיו."""
        best, best_cost = None, 1e9
        for pl in self.plats[True]:
            if pl["broken"] or pl["kind"] in ("spikes", "spring"):
                continue
            drop = pl["y"] - c.y
            if not 0 <= drop < self.ROW * 4:
                continue
            cost = drop + abs(pl["x"] - c.x) * 0.9
            if cost < best_cost:
                best, best_cost = pl, cost
        return best

    def pick_target(self, c):
        best, best_cost = None, 1e9
        for pl in self.plats[True]:
            if pl["broken"] or pl["kind"] == "spikes":
                continue
            rise = c.y - pl["y"]
            if not 20 < rise < self.ROW * 1.5:
                continue
            x = pl["x"]
            if pl["kind"] == "halfspike":
                x = pl["x"] - pl["side"] * pl["w"] / 4   # לנחות על הצד הבטוח
            cost = abs(x - c.x) - (60 if pl["kind"] == "spring" else 0) - (200 if pl["kind"] == "flag" else 0)
            if cost < best_cost:
                best, best_cost = dict(pl, x=x), cost
        if best is not None:
            # שומרים הפניה למשטח האמיתי (בשביל משטחים שזזים)
            for pl in self.plats[True]:
                if pl["y"] == best["y"] and abs(pl["base"] - best["base"]) < 0.01:
                    if pl["kind"] == "halfspike":
                        return dict(pl, x=best["x"])
                    return pl
        return best

    # ---------- ציור ----------
    def paint(self, p):
        W, H = self.W, self.H
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#1b1b2f"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)
        for c, x0 in ((self.player, 12), (self.piko, W - 12 - self.LW)):
            p.save()
            p.setClipRect(QRectF(x0, 0, self.LW, H))
            p.translate(x0, 0)
            self.draw_lane(p, c)
            p.restore()
            p.setPen(QPen(QColor("#ffffff") if not c.piko else HEAD, 3))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(x0, 0, self.LW, H), 6, 6)
        self.draw_progress(p)
        self.draw_scoreboard(p)
        big = None
        if self.countdown > 0 and not self.over:
            n = (self.countdown - 1) // 50
            big = ("טפס!" if n == 0 else str(n)), ("#76ff03" if n == 0 else "#ffeb3b")
            if self.countdown > 150:
                big = (f"מירוץ {self.race_no}", "#ffffff")
        elif self.race_end > 0 and not self.over:
            big = ("פיקו בפסגה!" if self.race_winner.piko else "אתה בפסגה! 🏁"), "#ffeb3b"
        if big:
            p.setFont(QFont("Arial", 44, QFont.Black))
            p.setPen(QColor(0, 0, 0, 170))
            p.drawText(QRectF(3, 173, W, 80), Qt.AlignCenter, big[0])
            p.setPen(QColor(big[1]))
            p.drawText(QRectF(0, 170, W, 80), Qt.AlignCenter, big[0])
        self.draw_overlay(p, "← → זזים · ↑ או רווח קופצים · X כדור שלג על פיקו · R · Esc", msg_y=60, hint_y=H - 26)

    def sy(self, c, y):
        return self.SY0 + (y - c.cam)

    def draw_lane(self, p, c):
        LW, H = self.LW, self.H
        top = self.ROW * self.ROWS
        frac = clamp(-c.cam / top, 0, 1)

        def mix(a, b, k):
            a, b = QColor(a), QColor(b)
            return QColor(int(a.red() + (b.red() - a.red()) * k), int(a.green() + (b.green() - a.green()) * k),
                          int(a.blue() + (b.blue() - a.blue()) * k))
        # השמיים משתנים ככל שעולים: יום, שקיעה, לילה
        if frac < 0.5:
            sky_top, sky_bottom = mix("#4fc3f7", "#ff8a65", frac * 2), mix("#e1f5fe", "#ffcc80", frac * 2)
        else:
            sky_top, sky_bottom = mix("#ff8a65", "#1a237e", (frac - 0.5) * 2), mix("#ffcc80", "#7e57c2", (frac - 0.5) * 2)
        sky = QLinearGradient(0, 0, 0, H)
        sky.setColorAt(0, sky_top)
        sky.setColorAt(1, sky_bottom)
        p.fillRect(QRectF(0, 0, LW, H), sky)
        p.setPen(Qt.NoPen)
        if frac > 0.6:
            p.setBrush(QColor(255, 255, 255, int(200 * (frac - 0.6) / 0.4)))
            rnd = random.Random(2)
            for _ in range(30):
                p.drawEllipse(QPointF(rnd.uniform(0, LW), rnd.uniform(0, H * 0.7)), 1.6, 1.6)
        # הרים רחוקים שזזים לאט (פרלקסה)
        shift = -c.cam * 0.15
        p.setBrush(mix("#9575cd", "#4527a0", frac))
        hills = QPainterPath(QPointF(0, H))
        for i in range(0, LW + 80, 80):
            hills.lineTo(i, 300 + shift + (60 if (i // 80) % 2 else 0))
        hills.lineTo(LW, H)
        hills.closeSubpath()
        p.drawPath(hills)
        # עננים קבועים בגבהים שונים
        p.setBrush(QColor(255, 255, 255, 140))
        lo, hi = int((c.cam - 400) // 260), int((c.cam + 200) // 260) + 1
        for k in range(lo, hi + 1):
            rnd = random.Random(k * 13)
            y = self.sy(c, k * 260 * 1.0) * 0.5 + 120 + rnd.uniform(-40, 40) * 0
            cx = rnd.uniform(30, LW - 30)
            cy = self.SY0 + (k * 260 - c.cam) * 0.6
            for dx, r in ((-24, 16), (0, 22), (24, 17)):
                p.drawEllipse(QPointF(cx + dx, cy), r * 1.3, r)
        # קירות סלע בצדדים
        p.setBrush(QColor("#6d4c41"))
        for side_x in (0, LW - 12):
            p.drawRect(QRectF(side_x, 0, 12, H))
        # האדמה
        gy = self.sy(c, 0)
        if gy < H + 20:
            p.fillRect(QRectF(0, gy, LW, H - gy + 40), QColor("#6d4c41"))
            p.fillRect(QRectF(0, gy, LW, 10), QColor("#7cb342"))
        for pl in self.plats[c.piko]:
            y = self.sy(c, pl["y"])
            if -40 < y < H + 40:
                self.draw_platform(p, pl, y)
        # כדורי שלג שמכוונים לצד הזה
        for side, x, y, vy, warn in self.snowballs:
            if side != c.piko:
                continue
            if warn > 0:
                if warn % 10 < 6:
                    p.setFont(QFont("Arial", 22, QFont.Black))
                    p.setPen(QColor("#ff1744"))
                    p.drawText(QRectF(x - 20, 92, 40, 34), Qt.AlignCenter, "!")
                    p.setPen(QPen(QColor(255, 23, 68, 120), 2, Qt.DashLine))
                    p.drawLine(QPointF(x, 126), QPointF(x, self.sy(c, c.y) - 40))
            else:
                sy = self.sy(c, y)
                p.setPen(QPen(QColor("#b3e5fc"), 2))
                p.setBrush(Qt.white)
                p.drawEllipse(QPointF(x, sy - 12), 13, 13)
        self.draw_climber(p, c)
        for side, x, y, word, life in self.sparks:
            if side != c.piko:
                continue
            sy = self.sy(c, y)
            alpha = int(255 * min(1, life / 12))
            p.setFont(QFont("Arial", 16, QFont.Black))
            p.setPen(QColor(40, 20, 0, alpha))
            p.drawText(QRectF(x - 70 + 2, sy - 16 + 2, 140, 32), Qt.AlignCenter, word)
            p.setPen(QColor(255, 235, 59, alpha))
            p.drawText(QRectF(x - 70, sy - 16, 140, 32), Qt.AlignCenter, word)
        # גובה
        meters = int(max(0, c.height) / self.ROW * 10)
        pill = QRectF(18, H - 62, 110, 24)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 140))
        p.drawRoundedRect(pill, 8, 8)
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 11, QFont.Bold))
        p.drawText(pill, Qt.AlignCenter, f"גובה: {meters} מטר")
        if not c.piko:
            pill2 = QRectF(LW - 128, H - 62, 110, 24)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 140))
            p.drawRoundedRect(pill2, 8, 8)
            p.setPen(QColor("#b3e5fc") if c.snow_cd == 0 else QColor("#9e9e9e"))
            p.drawText(pill2, Qt.AlignCenter, "❄️ מוכן! (X)" if c.snow_cd == 0 else f"❄️ {math.ceil(c.snow_cd / 60)}")

    def draw_platform(self, p, pl, y):
        x, w, kind = pl["x"], pl["w"], pl["kind"]
        left = x - w / 2
        p.setPen(Qt.NoPen)
        if pl["broken"]:
            if pl["broken"] < 40:   # חוזר לאט
                p.setBrush(QColor(161, 136, 127, int(255 * (40 - pl["broken"]) / 40)))
                p.drawRoundedRect(QRectF(left, y, w, 14), 5, 5)
            return
        shake = math.sin(self.frame * 1.7) * 2 if pl["crumble"] else 0
        left += shake
        if kind == "moving":
            p.setBrush(QColor("#90a4ae"))
            p.drawRoundedRect(QRectF(left, y, w, 12), 4, 4)
            p.setBrush(QColor("#607d8b"))
            for i in range(3):
                p.drawEllipse(QPointF(left + w * (i + 1) / 4, y + 6), 3, 3)
            p.setPen(QPen(QColor("#ffffff"), 2))
            p.drawLine(QPointF(left + 6, y + 6), QPointF(left - 6, y + 6))
            p.drawLine(QPointF(left + w - 6, y + 6), QPointF(left + w + 6, y + 6))
            return
        body = QColor("#bcaaa4") if kind == "crumble" else QColor("#8d6e63")
        p.setBrush(body)
        rock = QPainterPath(QPointF(left, y + 4))
        rock.lineTo(left + w, y + 4)
        rock.lineTo(left + w - 10, y + 20)
        rock.lineTo(left + w * 0.5, y + 26)
        rock.lineTo(left + 10, y + 20)
        rock.closeSubpath()
        p.drawPath(rock)
        p.setBrush(QColor("#9ccc65") if kind != "crumble" else QColor("#d7ccc8"))
        p.drawRoundedRect(QRectF(left - 2, y, w + 4, 7), 3, 3)
        if kind == "crumble":
            p.setPen(QPen(QColor("#6d4c41"), 1.5))
            p.drawLine(QPointF(left + w * 0.3, y + 4), QPointF(left + w * 0.38, y + 18))
            p.drawLine(QPointF(left + w * 0.65, y + 4), QPointF(left + w * 0.58, y + 16))
        if kind in ("spikes", "halfspike"):
            if kind == "spikes":
                a, b = left, left + w
            elif pl["side"] > 0:
                a, b = x + shake, left + w
            else:
                a, b = left, x + shake
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#cfd8dc"))
            n = max(2, int((b - a) // 12))
            for i in range(n):
                sx = a + (b - a) * i / n
                spike = QPainterPath(QPointF(sx, y + 1))
                spike.lineTo(sx + (b - a) / n / 2, y - 12)
                spike.lineTo(sx + (b - a) / n, y + 1)
                spike.closeSubpath()
                p.drawPath(spike)
        if kind == "spring":
            squash = 0.35 if pl["cool"] else 1.0   # מכווץ אחרי שימוש
            p.setPen(QPen(QColor("#e53935") if not pl["cool"] else QColor("#9e9e9e"), 3))
            for i in range(3):
                p.drawLine(QPointF(x - 10, y - (3 + i * 5) * squash), QPointF(x + 10, y - (5 + i * 5) * squash))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffeb3b") if not pl["cool"] else QColor("#bdbdbd"))
            p.drawRoundedRect(QRectF(x - 14, y - 20 * squash, 28, 6), 3, 3)
        if kind == "flag":
            p.setPen(QPen(QColor("#5d4037"), 4))
            p.drawLine(QPointF(x, y), QPointF(x, y - 70))
            p.setPen(Qt.NoPen)
            for i in range(4):
                for j in range(3):
                    p.setBrush(Qt.white if (i + j) % 2 else QColor("#212121"))
                    wave = math.sin(self.frame * 0.15 + i) * 2
                    p.drawRect(QRectF(x + i * 11, y - 70 + j * 9 + wave, 11, 9))
            p.setBrush(QColor("#ffeb3b"))
            p.drawPath(star_path(x, y - 76, 8))

    def draw_climber(self, p, c):
        x, y = c.x, self.sy(c, c.y)
        r = 16
        walk = math.sin(self.frame * 0.4) * 4 if abs(c.vx) > 0.5 and c.on else 0
        air = not c.on
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60) if c.on else Qt.NoBrush)
        p.drawEllipse(QRectF(x - 14, y - 3, 28, 6))
        feet = HEAD_DARK if c.piko else QColor("#0d47a1")
        p.setBrush(feet)
        p.drawEllipse(QPointF(x - 7 + walk, y - (6 if air else 3)), 6, 4)
        p.drawEllipse(QPointF(x + 7 - walk, y - (6 if air else 3)), 6, 4)
        cy = y - r - 6
        if c.stun:
            p.setBrush(QColor(179, 229, 252, 160))
            p.drawEllipse(QPointF(x, cy), r + 7, r + 7)  # קפוא או מסוחרר
        if c.piko:
            p.setPen(QPen(BOLT, 2.5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x, cy - r), QPointF(x, cy - r - 9))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffd54f"))
            p.drawEllipse(QPointF(x, cy - r - 11), 3.5, 3.5)
            p.setPen(QPen(HEAD_DARK, 2.5))
            p.setBrush(HEAD)
            p.drawEllipse(QPointF(x, cy), r, r)
            p.setPen(Qt.NoPen)
            p.setBrush(FACE)
            p.drawEllipse(QPointF(x + c.face * 2, cy + 2), r * 0.72, r * 0.62)
            outfit = current_outfit()
            if not outfit.get("glasses"):
                outfit["glasses"] = "shades"   # משקפי השמש של פיקו
            draw_accessories(p, outfit, x + c.face * 2, cy, r, top=-0.95, eye_y=-0.08, neck_y=0.95,
                             t=time.time())
            mouth = QPainterPath(QPointF(x + c.face * 2 - 5, cy + 6))
            mouth.quadTo(x + c.face * 2, cy + 10, x + c.face * 2 + 6, cy + 4)
            p.setPen(QPen(INK, 2, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawPath(mouth)
        else:
            p.setPen(QPen(Qt.white, 2.5))
            p.setBrush(QColor("#1e88e5"))
            p.drawEllipse(QPointF(x, cy), r, r)
            p.setPen(Qt.NoPen)
            for ex in (x + c.face * 1 - 5, x + c.face * 1 + 5):
                p.setBrush(Qt.white)
                p.drawEllipse(QPointF(ex, cy - 2), 4, 5)
                p.setBrush(INK)
                p.drawEllipse(QPointF(ex + c.face * 1.5, cy - (4 if air else 2)), 2, 2.6)
            p.setBrush(QColor("#ff7043"))
            p.drawRoundedRect(QRectF(x - 13, cy - 15, 26, 6), 3, 3)  # כובע טיפוס

    def draw_progress(self, p):
        """פס באמצע שמראה מי יותר קרוב לפסגה."""
        W, H = self.W, self.H
        x = W / 2
        top, bottom = 70, H - 40
        p.setPen(QPen(QColor(255, 255, 255, 90), 6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, top), QPointF(x, bottom))
        p.setFont(QFont("Arial", 13))
        p.setPen(Qt.white)
        p.drawText(QRectF(x - 14, top - 26, 28, 22), Qt.AlignCenter, "🏁")
        total = self.ROW * self.ROWS
        for c, color in ((self.piko, HEAD), (self.player, QColor("#1e88e5"))):
            frac = clamp(c.height / total, 0, 1)
            y = bottom - (bottom - top) * frac
            p.setPen(QPen(Qt.white, 2))
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), 6, 6)


# ---------------------------------------------------------------- חידון נגד פיקו
# כל שאלה: (נושא, שאלה, התשובה הנכונה, שלוש תשובות לא נכונות)
QUIZ_TOPICS = {
    "animals": "🐾 חיות", "science": "🔬 מדע", "space": "🚀 חלל", "world": "🌍 מדינות וערים",
    "israel": "🇮🇱 ישראל", "sports": "⚽ ספורט", "general": "💡 ידע כללי", "math": "🧮 חשבון",
}
QUIZ_BANK = [
    ("animals", "מהי החיה הגבוהה ביותר בעולם?", "ג'ירפה", ["פיל", "גמל", "יען"]),
    ("animals", "כמה רגליים יש לעכביש?", "8", ["6", "10", "4"]),
    ("animals", "איזו מהחיות האלה היא יונק?", "דולפין", ["כריש", "צב", "תמנון"]),
    ("animals", "מהי החיה הגדולה ביותר שחיה היום?", "לווייתן כחול", ["פיל אפריקאי", "כריש לבן", "ג'ירפה"]),
    ("animals", "איזו ציפור לא יכולה לעוף?", "פינגווין", ["נשר", "יונה", "תוכי"]),
    ("animals", "כמה לבבות יש לתמנון?", "3", ["1", "2", "8"]),
    ("animals", "איזו חיה משנה את צבע העור שלה כדי להסתתר?", "זיקית", ["ארנב", "סוס", "ינשוף"]),
    ("animals", "מה פנדה אוכלת בעיקר?", "במבוק", ["דגים", "בשר", "תפוחים"]),
    ("animals", "איזו מהחיות האלה היא דו-חיים?", "צפרדע", ["לטאה", "נחש", "תנין"]),
    ("animals", "כמה רגליים יש לחרק?", "6", ["8", "4", "10"]),
    ("science", "באיזו טמפרטורה מים רותחים (בגובה פני הים)?", "100 מעלות", ["50 מעלות", "0 מעלות", "200 מעלות"]),
    ("science", "באיזו טמפרטורה מים קופאים?", "0 מעלות", ["10 מעלות", "100 מעלות", "50 מעלות"]),
    ("science", "מה הנוסחה הכימית של מים?", "H2O", ["CO2", "O2", "NaCl"]),
    ("science", "איזה גז הגוף שלנו צריך מהאוויר כדי לחיות?", "חמצן", ["הליום", "פחמן דו-חמצני", "מימן"]),
    ("science", "איזה צבע מקבלים מערבוב של כחול וצהוב?", "ירוק", ["סגול", "כתום", "חום"]),
    ("science", "מה מושך חפצים ליפול אל כדור הארץ?", "כוח המשיכה", ["הרוח", "החשמל", "האור"]),
    ("science", "קרח הוא מים במצב...", "מוצק", ["נוזל", "גז", "אדים"]),
    ("science", "מה צמחים צריכים כדי לייצר מזון בתהליך הפוטוסינתזה?", "אור שמש", ["חושך", "מוזיקה", "שוקולד"]),
    ("science", "איזה איבר בגוף מזרים את הדם?", "הלב", ["הריאות", "הקיבה", "הכבד"]),
    ("science", "כמה עצמות יש בגוף של אדם מבוגר?", "206", ["100", "312", "52"]),
    ("science", "באיזה איבר אנחנו משתמשים כדי לנשום?", "ריאות", ["כליות", "קיבה", "לב"]),
    ("space", "מהו כוכב הלכת הקרוב ביותר לשמש?", "כוכב חמה", ["מאדים", "נוגה", "צדק"]),
    ("space", "מהו כוכב הלכת הגדול ביותר במערכת השמש?", "צדק", ["שבתאי", "כדור הארץ", "נפטון"]),
    ("space", "לאיזה כוכב לכת יש טבעות גדולות ומפורסמות?", "שבתאי", ["מאדים", "נוגה", "כוכב חמה"]),
    ("space", "איזה כוכב לכת נקרא 'כוכב הלכת האדום'?", "מאדים", ["צדק", "אורנוס", "נוגה"]),
    ("space", "כמה זמן לוקח לכדור הארץ להקיף את השמש?", "שנה", ["יום", "חודש", "שבוע"]),
    ("space", "מי היה האדם הראשון שהלך על הירח?", "ניל ארמסטרונג", ["יורי גגארין", "אילן רמון", "אלברט איינשטיין"]),
    ("space", "השמש היא...", "כוכב", ["כוכב לכת", "ירח", "שביט"]),
    ("space", "סביב מה מסתובב הירח?", "כדור הארץ", ["השמש בלבד", "מאדים", "צדק"]),
    ("space", "מי היה האסטרונאוט הישראלי הראשון?", "אילן רמון", ["ניל ארמסטרונג", "יורי גגארין", "באז אולדרין"]),
    ("world", "מהי עיר הבירה של צרפת?", "פריז", ["לונדון", "רומא", "מדריד"]),
    ("world", "מהי עיר הבירה של איטליה?", "רומא", ["מילאנו", "ונציה", "פריז"]),
    ("world", "מהי עיר הבירה של יפן?", "טוקיו", ["בייג'ינג", "סיאול", "אוסקה"]),
    ("world", "באיזו יבשת נמצאת מצרים?", "אפריקה", ["אסיה", "אירופה", "אמריקה"]),
    ("world", "מהו האוקיינוס הגדול ביותר בעולם?", "האוקיינוס השקט", ["האוקיינוס האטלנטי", "האוקיינוס ההודי", "הים התיכון"]),
    ("world", "מהי המדינה הגדולה ביותר בעולם בשטח?", "רוסיה", ["קנדה", "סין", "ארצות הברית"]),
    ("world", "באיזו עיר נמצא מגדל אייפל?", "פריז", ["לונדון", "ברלין", "ניו יורק"]),
    ("world", "מהו ההר הגבוה ביותר בעולם?", "האוורסט", ["הקילימנג'רו", "מון בלאן", "החרמון"]),
    ("world", "באיזו מדינה נמצאות הפירמידות של גיזה?", "מצרים", ["מקסיקו", "יוון", "הודו"]),
    ("world", "מהי עיר הבירה של ספרד?", "מדריד", ["ברצלונה", "ליסבון", "רומא"]),
    ("world", "באיזו מדינה מדברים בעיקר פורטוגזית?", "ברזיל", ["ארגנטינה", "מקסיקו", "צ'ילה"]),
    ("israel", "באיזו שנה הוקמה מדינת ישראל?", "1948", ["1967", "1917", "1973"]),
    ("israel", "מה הצבעים של דגל ישראל?", "כחול ולבן", ["אדום ולבן", "ירוק ולבן", "כחול וצהוב"]),
    ("israel", "איזו עיר בישראל נמצאת על חוף ים סוף?", "אילת", ["חיפה", "טבריה", "צפת"]),
    ("israel", "מהי העיר עם הכי הרבה תושבים בישראל?", "ירושלים", ["תל אביב", "חיפה", "באר שבע"]),
    ("israel", "מהו המקום הנמוך ביותר ביבשה בכל כדור הארץ?", "ים המלח", ["הכנרת", "הים התיכון", "מכתש רמון"]),
    ("israel", "מהו אגם המים המתוקים הגדול בישראל?", "הכנרת", ["ים המלח", "אגם החולה", "ים סוף"]),
    ("israel", "באיזה מדבר נמצא מכתש רמון?", "הנגב", ["סהרה", "יהודה", "סיני"]),
    ("sports", "כמה שחקנים יש לכל קבוצה על מגרש כדורגל?", "11", ["9", "5", "7"]),
    ("sports", "כמה שחקנים יש לכל קבוצה על מגרש כדורסל?", "5", ["6", "11", "7"]),
    ("sports", "כמה נקודות שווה זריקה מעבר לקו השלוש בכדורסל?", "3", ["2", "1", "4"]),
    ("sports", "כל כמה שנים מתקיים המונדיאל בכדורגל?", "4", ["2", "1", "5"]),
    ("sports", "כמה פינים עומדים בתחילת כל מסגרת בבאולינג?", "10", ["12", "8", "6"]),
    ("sports", "כמה טבעות יש בסמל של המשחקים האולימפיים?", "5", ["4", "6", "3"]),
    ("sports", "באיזה ספורט משחקים עם מחבט וכדור קטן על שולחן?", "טניס שולחן", ["גולף", "באולינג", "רוגבי"]),
    ("sports", "כמה זמן נמשך משחק כדורגל רגיל (בלי תוספת)?", "90 דקות", ["60 דקות", "45 דקות", "120 דקות"]),
    ("general", "כמה ימים יש בשבוע?", "7", ["5", "6", "8"]),
    ("general", "כמה דקות יש בשעה?", "60", ["100", "30", "24"]),
    ("general", "כמה ימים יש בשנה רגילה?", "365", ["366", "360", "300"]),
    ("general", "כמה צלעות יש למשולש?", "3", ["4", "5", "6"]),
    ("general", "כמה אפסים יש במספר מיליון?", "6", ["5", "7", "3"]),
    ("general", "איזה צבע מקבלים מערבוב של אדום ולבן?", "ורוד", ["סגול", "כתום", "חום"]),
    ("general", "כמה צבעים מקובל לספור בקשת בענן?", "7", ["5", "6", "9"]),
    ("general", "כמה שעות יש ביממה?", "24", ["12", "20", "36"]),
    ("general", "כמה צלעות יש למשושה?", "6", ["5", "8", "4"]),
]
QUIZ_LINES = {
    "think": ["הממ... קלי קלות. 🤔", "רגע, אני מחפש במוח הגאוני שלי...", "שאלה קלה! אבל אני אתן לך יתרון."],
    "piko_right": ["אני יודע! התשובה היא {a}! 😎", "קל! {a}. כמובן.", "{a}! ידעתי עוד לפני שקראתי."],
    "piko_wrong": ["אני בטוח לגמרי: {a}! 😎", "זה {a}, אין ספק! ...יש ספק?", "{a}! ...רגע, אולי לא."],
    "piko_oops": ["אופס! טעיתי בכוונה, כדי שיהיה לך סיכוי. 😅", "מה?! המעגלים שלי התבלבלו!",
                  "טוב, זה היה מבחן בשבילך. ברור."],
    "you_right": ["מה?! ענית לפניי?! מזל של מתחילים!", "נכון... טוב, ידעתי את זה גם. 😤", "וואו. נקודה לך. בפעם הזאת."],
    "you_wrong": ["חחח! לא נכון! 😂", "אוי, לא! אבל אל תתבאס, לא כולם גאונים כמוני."],
    "piko_point": ["נקודה לפיקו! המוח הכי מהיר ביקום. 🧠", "עוד נקודה לגאון!"],
    "nobody": ["אף אחד לא ידע? אפילו אני? מוזר... 🤔", "נגמר הזמן! השאלה הזאת הייתה קשה מדי. לך."],
}


class QuizGame(FootballGame):
    """חידון נגד פיקו: 8 שאלות, 4 תשובות. לוחצים על תשובה בעכבר או במקשים 1-4.
    מי שעונה ראשון נכון מקבל נקודה. מי שטועה כבר לא יכול לענות על אותה שאלה. R משחק חדש, Esc סוגר."""

    W, H = 800, 500
    QUESTIONS = 8
    TIME = 14 * 60           # זמן לכל שאלה
    PIKO_RIGHT = 0.62        # כמה פעמים פיקו צודק בערך
    BOXES = [QRectF(40 + col * 268, 214 + row * 104, 252, 90) for row in range(2) for col in range(2)]

    def __init__(self):
        self.used = set()     # שאלות שכבר היו, כדי שלא יחזרו מהר
        self.hover = None
        super().__init__()
        self.setWindowTitle("חידון נגד פיקו")
        self.setMouseTracking(True)
        self.view = (1.0, 0.0, 0.0)

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.q_no = 0
        self.message, self.msg_timer = "", 0
        self.oops_at = 0
        bank = [q for q in QUIZ_BANK if q[1] not in self.used]
        if len(bank) < self.QUESTIONS:
            self.used.clear()
            bank = list(QUIZ_BANK)
        topics = random.sample(list(QUIZ_TOPICS), 7)  # נושאים מעורבבים
        picks = []
        for t in topics:
            options = [q for q in bank if q[0] == t and q not in picks]
            if t != "math" and options:
                picks.append(random.choice(options))
        while len(picks) < self.QUESTIONS - 1:
            picks.append(random.choice([q for q in bank if q not in picks]))
        picks = picks[:self.QUESTIONS - 1]
        picks.insert(random.randint(2, len(picks)), self.make_math())  # תמיד יש לפחות תרגיל חשבון אחד
        if random.random() < 0.5:
            picks[random.randint(0, 2)] = self.make_math()
        self.questions = picks
        for q in picks:
            self.used.add(q[1])
        self.bubble = "חידון? אני יודע הכול! טוב, כמעט הכול. 😎"
        self.emotion.emit("proud")
        self.next_question()

    def make_math(self):
        kind = random.choice(["+", "-", "×"])
        if kind == "+":
            a, b = random.randint(12, 79), random.randint(11, 69)
            ans = a + b
        elif kind == "-":
            a, b = random.randint(30, 99), random.randint(10, 29)
            ans = a - b
        else:
            a, b = random.randint(3, 12), random.randint(3, 12)
            ans = a * b
        wrong = set()
        while len(wrong) < 3:
            w = ans + random.choice([-10, -2, -1, 1, 2, 10, a if kind == "×" else 3, -(b if kind == "×" else 3)])
            if w != ans and w > 0:
                wrong.add(w)
        return ("math", f"כמה זה {a} {kind} {b}?", str(ans), [str(w) for w in wrong])

    def next_question(self):
        self.q_no += 1
        topic, text, right, wrongs = self.questions[self.q_no - 1]
        answers = [right] + list(wrongs)
        random.shuffle(answers)
        self.q = dict(topic=topic, text=text, answers=answers, right=answers.index(right))
        self.state = "ask"
        self.time_left = self.TIME
        self.you_pick = None       # איזו תשובה בחרת
        self.piko_pick = None
        self.winner = None
        self.reveal = 0
        # פיקו מחליט מראש מתי יענה והאם יצדק. כשהוא מוביל הוא שחצן: איטי יותר וטועה יותר
        lead = self.score[1] - self.score[0]
        right_chance = clamp(self.PIKO_RIGHT - 0.08 * lead, 0.35, 0.85)
        delay = random.uniform(3.0, 8.0) * (0.7 if topic == "math" else 1.0) * (1 + 0.12 * max(0, lead))
        self.piko_at = int(delay * 60)
        if random.random() < right_chance:
            self.piko_choice = self.q["right"]
        else:
            self.piko_choice = random.choice([i for i in range(4) if i != self.q["right"]])
        self.bubble = random.choice(QUIZ_LINES["think"])

    # ---------- קלט ----------
    def keyPressEvent(self, event):
        k = event.key()
        if k in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4) and not event.isAutoRepeat():
            self.answer_you(k - Qt.Key_1)
        else:
            super().keyPressEvent(event)

    def box_at(self, pos):
        s, ox, oy = self.view
        x, y = (pos.x() - ox) / s, (pos.y() - oy) / s
        for i, b in enumerate(self.BOXES):
            if b.contains(QPointF(x, y)):
                return i
        return None

    def mouseMoveEvent(self, event):
        self.hover = self.box_at(event.position())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            i = self.box_at(event.position())
            if i is not None:
                self.answer_you(i)

    def answer_you(self, i):
        if self.over or self.state != "ask" or self.you_pick is not None or i == self.piko_pick:
            return
        self.you_pick = i
        if i == self.q["right"]:
            self.score[0] += 1
            self.finish("you")
            self.bubble = random.choice(QUIZ_LINES["you_right"])
            self.emotion.emit(random.choice(["surprised", "angry"]))
        else:
            self.bubble = random.choice(QUIZ_LINES["you_wrong"])
            self.emotion.emit("laugh")
            if self.piko_pick is not None:
                self.finish(None)

    def answer_piko(self):
        i = self.piko_choice
        if i == self.you_pick:  # כבר בחרת את זה ונפסלת: פיקו בוחר משהו אחר
            i = self.q["right"] if random.random() < 0.7 else random.choice(
                [k for k in range(4) if k not in (self.you_pick, self.q["right"])])
        self.piko_pick = i
        name = self.q["answers"][i]
        if i == self.q["right"]:
            self.score[1] += 1
            self.bubble = random.choice(QUIZ_LINES["piko_right"]).format(a=name)
            self.finish("piko")
            self.emotion.emit(random.choice(["proud", "laugh"]))
        else:
            self.bubble = random.choice(QUIZ_LINES["piko_wrong"]).format(a=name)
            self.emotion.emit("proud")
            self.oops_at = 50   # רגע אחרי, הוא מגלה שטעה
            if self.you_pick is not None:
                self.finish(None)

    def finish(self, winner):
        self.state, self.winner, self.reveal = "reveal", winner, 150

    # ---------- לולאת המשחק ----------
    def tick(self):
        if not self.over:
            self.step()
        self.update()

    def step(self):
        if getattr(self, "oops_at", 0) > 0:
            self.oops_at -= 1
            if self.oops_at == 0 and self.piko_pick is not None and self.piko_pick != self.q["right"]:
                if self.state == "ask" or self.winner != "you":
                    self.bubble = random.choice(QUIZ_LINES["piko_oops"])
                    self.emotion.emit("sad")
        if self.state == "ask":
            self.time_left -= 1
            if self.piko_pick is None and self.TIME - self.time_left >= self.piko_at:
                self.answer_piko()
            if self.state == "ask" and self.time_left <= 0:
                self.bubble = random.choice(QUIZ_LINES["nobody"])
                self.finish(None)
        elif self.state == "reveal":
            self.reveal -= 1
            if self.reveal == 0:
                if self.q_no >= len(self.questions):
                    self.end_game()
                else:
                    self.next_question()

    def end_game(self):
        self.over = True
        you, piko = self.score
        if piko > you:
            self.say(f"פיקו ניצח {piko}-{you}! המוח הכי גדול ביקום. 🧠👑", 10 ** 9)
            self.emotion.emit("proud")
        elif you > piko:
            self.say(f"ניצחת {you}-{piko}?! ...האנטנה שלי לא קלטה את השאלות. ברור.", 10 ** 9)
            self.emotion.emit("surprised")
        else:
            self.say(f"תיקו {you}-{piko}! אתה כמעט חכם כמוני. כמעט!", 10 ** 9)
            self.emotion.emit("happy")
        self.finished.emit(you, piko)

    # ---------- ציור ----------
    def paint(self, p):
        W, H = self.W, self.H
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#0f1430"))
        s = min(self.width() / W, self.height() / H)
        ox, oy = (self.width() - W * s) / 2, (self.height() - H * s) / 2
        self.view = (s, ox, oy)
        p.translate(ox, oy)
        p.scale(s, s)
        bg = QLinearGradient(0, 0, 0, H)
        bg.setColorAt(0, QColor("#283593"))
        bg.setColorAt(1, QColor("#4a148c"))
        p.fillRect(QRectF(0, 0, W, H), bg)
        # אורות במה
        t = time.time()
        p.setPen(Qt.NoPen)
        for i in range(9):
            c = QColor.fromHsv((i * 40 + int(t * 40)) % 360, 160, 255, 60)
            p.setBrush(c)
            p.drawEllipse(QPointF(40 + i * 90, 8), 16, 16)
        self.draw_scoreboard(p)
        q = self.q
        # נושא ומספר שאלה
        pill = QRectF(30, 16, 210, 30)
        p.setBrush(QColor(0, 0, 0, 130))
        p.drawRoundedRect(pill, 12, 12)
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 12, QFont.Bold))
        p.drawText(pill, Qt.AlignCenter, f"{QUIZ_TOPICS[q['topic']]}  ·  {self.q_no}/{len(self.questions)}")
        # השאלה
        box = QRectF(40, 62, 520, 108)
        p.setPen(QPen(QColor("#ffd54f"), 3))
        p.setBrush(QColor("#1a237e"))
        p.drawRoundedRect(box, 16, 16)
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 19, QFont.Bold))
        p.drawText(box.adjusted(16, 6, -16, -6), Qt.AlignCenter | Qt.TextWordWrap, q["text"])
        # פס זמן
        frac = clamp(self.time_left / self.TIME, 0, 1) if self.state == "ask" else 0
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 120))
        p.drawRoundedRect(QRectF(40, 180, 520, 14), 7, 7)
        p.setBrush(QColor.fromHsv(int(120 * frac), 220, 240))
        p.drawRoundedRect(QRectF(40, 180, 520 * frac, 14), 7, 7)
        # התשובות
        colors = ["#e53935", "#1e88e5", "#fbc02d", "#43a047"]
        for i, b in enumerate(self.BOXES):
            base = QColor(colors[i])
            reveal = self.state == "reveal"
            if reveal and i == q["right"]:
                fill, edge = QColor("#2e7d32"), QColor("#b9f6ca")
            elif i in (self.you_pick, self.piko_pick) and i != q["right"]:
                fill, edge = QColor("#5d4037"), QColor("#ff8a80")
            elif reveal:
                fill, edge = base.darker(220), QColor(255, 255, 255, 60)
            else:
                fill = base.lighter(115) if self.hover == i and self.you_pick is None else base
                edge = QColor(255, 255, 255, 200)
            p.setPen(QPen(edge, 3))
            p.setBrush(fill)
            p.drawRoundedRect(b, 14, 14)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 90))
            p.drawEllipse(QPointF(b.right() - 26, b.center().y()), 16, 16)
            p.setPen(Qt.white)
            p.setFont(QFont("Arial", 14, QFont.Black))
            p.drawText(QRectF(b.right() - 42, b.center().y() - 16, 32, 32), Qt.AlignCenter, str(i + 1))
            p.setFont(QFont("Arial", 17, QFont.Bold))
            p.drawText(b.adjusted(12, 4, -50, -4), Qt.AlignCenter | Qt.TextWordWrap, q["answers"][i])
            # מי בחר כאן
            tags = []
            if self.you_pick == i:
                tags.append(("אתה", QColor("#90caf9")))
            if self.piko_pick == i:
                tags.append(("פיקו", HEAD))
            for k, (label, color) in enumerate(tags):
                tag = QRectF(b.x() + 10 + k * 62, b.y() - 12, 56, 22)
                p.setPen(QPen(Qt.white, 1.5))
                p.setBrush(color)
                p.drawRoundedRect(tag, 8, 8)
                p.setPen(QColor("#0d1b2a"))
                p.setFont(QFont("Arial", 10, QFont.Black))
                p.drawText(tag, Qt.AlignCenter, label)
            if reveal and i == q["right"]:
                p.setPen(QColor("#b9f6ca"))
                p.setFont(QFont("Arial", 18, QFont.Black))
                p.drawText(QRectF(b.x() + 8, b.y() + 4, 30, 30), Qt.AlignCenter, "✓")
        self.draw_host(p, t)
        if self.state == "reveal" and not self.over:
            text = {"you": "נקודה לך! 🎉", "piko": "נקודה לפיקו! 🤖", None: "אף אחד לא קיבל נקודה"}[self.winner]
            p.setFont(QFont("Arial", 15, QFont.Black))
            p.setPen(QColor("#ffeb3b"))
            p.drawText(QRectF(40, 424, 520, 30), Qt.AlignCenter, text)
        self.draw_overlay(p, "לחץ על תשובה בעכבר או במקשים 1-4 · מי שעונה ראשון נכון מקבל נקודה · R · Esc",
                          hint_y=H - 26)

    def draw_host(self, p, t):
        """פיקו המנחה בצד, עם בועת דיבור ואנטנה שמהבהבת כשהוא חושב."""
        x, y, r = 680, 330, 44
        thinking = self.state == "ask" and self.piko_pick is None
        bubble = QRectF(580, 62, 200, 132)
        p.setPen(QPen(QColor("#ffffff"), 2))
        p.setBrush(QColor("#fff8e1"))
        p.drawRoundedRect(bubble, 16, 16)
        tail = QPainterPath(QPointF(660, 194))
        tail.lineTo(672, 222)
        tail.lineTo(690, 194)
        tail.closeSubpath()
        p.setPen(Qt.NoPen)
        p.drawPath(tail)
        p.setPen(QColor("#3e2723"))
        p.setFont(QFont("Arial", 13, QFont.Bold))
        text = self.bubble + ("" if not thinking else "\n" + "." * (int(t * 3) % 3 + 1))
        p.drawText(bubble.adjusted(10, 8, -10, -8), Qt.AlignCenter | Qt.TextWordWrap, text)
        # גוף
        bob = math.sin(t * 3) * 3
        p.setPen(Qt.NoPen)
        p.setBrush(HEAD_DARK)
        p.drawRoundedRect(QRectF(x - 30, y + r - 6 + bob, 60, 52), 16, 16)
        p.setBrush(QColor("#ffd54f"))
        p.drawEllipse(QPointF(x, y + r + 20 + bob), 6, 6)
        # אנטנה
        p.setPen(QPen(BOLT, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, y - r + bob), QPointF(x, y - r - 18 + bob))
        p.setPen(Qt.NoPen)
        blink = thinking and int(t * 6) % 2 == 0
        p.setBrush(QColor("#ff5252") if blink else QColor("#ffd54f"))
        p.drawEllipse(QPointF(x, y - r - 22 + bob), 7, 7)
        # ראש ופנים
        p.setPen(QPen(HEAD_DARK, 3))
        p.setBrush(HEAD)
        p.drawEllipse(QPointF(x, y + bob), r, r)
        p.setPen(Qt.NoPen)
        p.setBrush(FACE)
        p.drawEllipse(QPointF(x, y + 4 + bob), r * 0.74, r * 0.64)
        cy = y + bob
        mood = "think" if thinking else ("win" if self.winner == "piko" else
                                         "sad" if self.piko_pick is not None and self.piko_pick != self.q["right"]
                                         else "lose" if self.winner == "you" else "happy")
        p.setBrush(INK)
        look = math.sin(t * 2) * 4 if mood == "think" else 0
        for ex in (x - 14, x + 14):
            if mood == "win":
                p.setPen(QPen(INK, 4, Qt.SolidLine, Qt.RoundCap))
                arc = QPainterPath(QPointF(ex - 8, cy + 2))
                arc.quadTo(ex, cy - 10, ex + 8, cy + 2)
                p.setBrush(Qt.NoBrush)
                p.drawPath(arc)
                p.setPen(Qt.NoPen)
                p.setBrush(INK)
            else:
                p.drawEllipse(QPointF(ex + look, cy - 2 - (4 if mood == "think" else 0)), 6, 8)
        p.setPen(QPen(INK, 3.5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        mouth = QPainterPath()
        if mood in ("win", "happy"):
            mouth.moveTo(x - 14, cy + 16)
            mouth.quadTo(x, cy + 30, x + 14, cy + 16)
        elif mood in ("sad", "lose"):
            mouth.moveTo(x - 12, cy + 24)
            mouth.quadTo(x, cy + 14, x + 12, cy + 24)
        else:
            mouth.moveTo(x + 2, cy + 20)
            mouth.quadTo(x + 10, cy + 18, x + 16, cy + 14)
        p.drawPath(mouth)
        draw_accessories(p, current_outfit(), x, cy, r, top=-0.95, eye_y=-0.06, neck_y=0.95, t=t)
        # מיקרופון של מנחה
        p.setPen(QPen(QColor("#424242"), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x + 40, y + r + 30 + bob), QPointF(x + 52, y + r - 4 + bob))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#9e9e9e"))
        p.drawEllipse(QPointF(x + 54, y + r - 10 + bob), 9, 11)


# ---------------------------------------------------------------- פלישת חלל נגד פיקו
SPACE_LINES = {
    "start": ["פיקו: צבא החלליות שלי כבר בדרך! הכנע עכשיו! 😎🛸", "פיקו: פלישת חלל! וכל החלליות נראות כמוני. מושלם."],
    "wave": ["גל {n}! הפעם החלליות שלי יותר מהירות! 😎", "גל {n}! אתה לא תעבור את זה. כנראה."],
    "boss": ["הגיע הזמן לבוס האמיתי... אני! 👑🛸", "חשבת שזה נגמר? עכשיו פיקו הענק בעצמו!"],
    "hit_you": ["בול! קרן הלייזר שלי פגעה! 😂", "אוי, החללית שלך מעשנת! חחח."],
    "lost_ship": ["חללית שלי! זאת הייתה החללית האהובה עליי! 😤", "הייי! יש לי עוד מיליון כאלה!"],
    "boss_hurt": ["אאוץ'! האנטנה שלי! 😡", "זה מדגדג! ...טוב, זה קצת כואב."],
    "boss_angry": ["עכשיו אני ממש כועס! מצב טורבו! 🔥", "די! עכשיו אני יורה בכל הכוח!"],
    "power": ["מה?! מאיפה הבאת את זה?!", "זה לא הוגן! תחזיר את המתנה שלי!"],
}


class SpaceGame(FootballGame):
    """פלישת חלל נגד פיקו. 3 גלים של חלליות, ואז הבוס: פיקו הענק.
    חצים או A/D לזוז, רווח או למעלה/W לירות (אפשר להחזיק), R משחק חדש, Esc סוגר."""

    W, H = 800, 500
    SHIP_Y = 444
    LIVES = 4
    WAVES = 3

    def __init__(self):
        self.handicap = 0    # עולה כשאתה מפסיד, יורד כשאתה מנצח
        super().__init__()
        self.setWindowTitle("פלישת חלל נגד פיקו")
        rnd = random.Random(1)
        self.stars = [(rnd.uniform(0, self.W), rnd.uniform(0, self.H), rnd.choice([0.4, 0.8, 1.6])) for _ in range(120)]

    # ---------- מצב המשחק ----------
    def restart(self):
        self.score = [0, 0]
        self.over = False
        self.points = 0
        self.frame = 0
        self.ship = dict(x=self.W / 2, lives=self.LIVES, inv=0, cd=0, double=0, shield=0)
        self.shots, self.ebullets, self.powerups, self.particles = [], [], [], []
        self.bunkers = set()
        for bx in (120, 300, 480, 660):
            for i in range(-3, 3):
                for j in range(3):
                    if not (j == 2 and i in (-1, 0)):
                        self.bunkers.add((bx + i * 9, 392 + j * 9))
        self.wave = 0
        h = self.handicap
        self.fire_mult = 1 - 0.18 * h
        if h:
            self.say(f"פיקו: טוב, אני נותן לך הנחה ({h} מתוך 3). החלליות שלי יורו פחות. 😏", 180)
        else:
            self.say(random.choice(SPACE_LINES["start"]), 180)
        self.emotion.emit("proud")
        self.next_wave()

    def next_wave(self):
        self.wave += 1
        self.state, self.t = "intro", 100
        self.enemies, self.boss = [], None
        self.shots.clear()
        self.ebullets.clear()
        if self.wave > self.WAVES:
            self.make_boss()
            self.say(random.choice(SPACE_LINES["boss"]), 140)
            self.emotion.emit("proud")
            return
        rows = 3 if self.wave == 1 else 4
        for r in range(rows):
            for col in range(8):
                gold = self.wave == 3 and r == 0
                self.enemies.append(dict(c=col, r=r, x=0.0, y=0.0, hp=2 if gold else 1, gold=gold,
                                         mode="form", t=0, flash=0))
        self.total = len(self.enemies)
        self.fx, self.fy, self.fdir = 160.0, 66.0, 1
        self.place_formation()
        if self.wave > 1:
            self.say(random.choice(SPACE_LINES["wave"]).format(n=self.wave), 120)

    def make_boss(self):
        hp = 54 - 9 * self.handicap
        self.boss = dict(x=self.W / 2, y=-80.0, hp=hp, max=hp, t=0, attack=0, beam=0, beam_x=0.0,
                         flash=0, angry=False, cd=120)

    def place_formation(self):
        for e in self.enemies:
            if e["mode"] == "form":
                e["x"], e["y"] = self.fx + e["c"] * 62, self.fy + e["r"] * 44

    # ---------- לולאת המשחק ----------
    def tick(self):
        if self.msg_timer > 0:
            self.msg_timer -= 1
        self.frame += 1
        if not self.over:
            self.step()
        self.update()

    def step(self):
        for pt in self.particles:
            pt[0] += pt[2]
            pt[1] += pt[3]
            pt[3] += 0.05
            pt[4] -= 1
        self.particles = [pt for pt in self.particles if pt[4] > 0]
        self.move_ship()
        self.move_shots()
        if self.state == "intro":
            self.t -= 1
            if self.boss:
                self.boss["y"] += (110 - self.boss["y"]) * 0.04   # הבוס נכנס לאט
            if self.t <= 0:
                self.state = "play"
            return
        if self.state == "clear":
            self.t -= 1
            if self.t <= 0:
                self.next_wave()
            return
        if self.boss:
            self.move_boss()
            self.move_divers()
        else:
            self.move_enemies()
        self.move_enemy_bullets()
        self.move_powerups()

    def move_ship(self):
        s, k = self.ship, self.keys
        dx = (Qt.Key_Right in k or Qt.Key_D in k) - (Qt.Key_Left in k or Qt.Key_A in k)
        s["x"] = clamp(s["x"] + dx * 6, 30, self.W - 30)
        for key in ("inv", "cd", "double"):
            s[key] = max(0, s[key] - 1)
        fire = Qt.Key_Space in k or Qt.Key_Up in k or Qt.Key_W in k
        if fire and s["cd"] == 0 and self.state != "intro":
            s["cd"] = 11
            if s["double"]:
                self.shots += [[s["x"] - 12, self.SHIP_Y - 18], [s["x"] + 12, self.SHIP_Y - 18]]
            else:
                self.shots.append([s["x"], self.SHIP_Y - 20])

    def move_shots(self):
        alive = []
        for sh in self.shots:
            sh[1] -= 12
            if sh[1] < -10:   # היריות שלך עוברות דרך המגנים שלך
                continue
            if self.boss and self.state == "play":
                b = self.boss
                if ((sh[0] - b["x"]) / 95) ** 2 + ((sh[1] - b["y"]) / 58) ** 2 < 1:
                    self.hurt_boss()
                    continue
            hit = None
            for e in self.enemies:
                if abs(sh[0] - e["x"]) < 24 and abs(sh[1] - e["y"]) < 18:
                    hit = e
                    break
            if hit:
                hit["hp"] -= 1
                hit["flash"] = 6
                if hit["hp"] <= 0:
                    self.kill_enemy(hit)
                continue
            alive.append(sh)
        self.shots = alive

    def kill_enemy(self, e):
        self.enemies.remove(e)
        self.points += 50 if e["gold"] else 20
        self.boom(e["x"], e["y"], HEAD)
        if random.random() < 0.07:
            self.powerups.append([e["x"], e["y"], random.choice(["double", "double", "shield", "life"])])
        if random.random() < 0.12:
            self.say(random.choice(SPACE_LINES["lost_ship"]), 70)
            self.emotion.emit("angry")
        if not self.enemies and not self.boss and not self.over:
            self.state, self.t = "clear", 80
            self.points += 200
            self.ship["lives"] = min(5, self.ship["lives"] + 1)   # בונוס: חיים נוספים על כל גל
            self.emotion.emit("surprised")

    def boom(self, x, y, color, n=16):
        for _ in range(n):
            a, v = random.uniform(0, 6.28), random.uniform(1, 4)
            self.particles.append([x, y, math.cos(a) * v, math.sin(a) * v, random.randint(20, 40), QColor(color)])

    def hit_bunker(self, x, y):
        key = (None, None)
        for bx, by in self.bunkers:
            if bx <= x < bx + 9 and by <= y < by + 9:
                key = (bx, by)
                break
        if key[0] is None:
            return False
        self.bunkers.discard(key)
        return True

    # ---------- החלליות של פיקו ----------
    def move_enemies(self):
        form = [e for e in self.enemies if e["mode"] == "form"]
        slots = [e for e in self.enemies if e["mode"] != "dive"]
        speed = (0.5 + 1.2 * (1 - len(self.enemies) / self.total) + 0.15 * self.wave)
        self.fx += self.fdir * speed
        if slots:
            # הגבולות לפי העמודות שנשארו, כדי שכל המקומות תמיד יהיו על המסך
            fx_max = self.W - 30 - max(e["c"] for e in slots) * 62
            fx_min = 30 - min(e["c"] for e in slots) * 62
            if self.fx > fx_max:
                self.fx, self.fdir = fx_max, -1
                self.fy += 8
            elif self.fx < fx_min:
                self.fx, self.fdir = fx_min, 1
                self.fy += 8
        self.place_formation()
        if form and max(self.fy + e["r"] * 44 for e in form) > self.SHIP_Y - 70:
            # החלליות הגיעו עד אליך: מאבדים חיים, והן חוזרות למעלה
            self.lose_life()
            self.fy = 66.0
        # צלילות: מגל 2 חלליות בודדות צוללות לעברך
        if self.wave >= 2 and form and random.random() < 0.0025 * self.wave:
            e = random.choice(form)
            e["mode"], e["t"], e["sx"] = "dive", 0, e["x"]
        self.move_divers()
        for e in self.enemies:
            if e["mode"] == "return":
                # טס ישר למקום שלו במהירות קבועה, ונוחת בו
                tx, ty = self.fx + e["c"] * 62, self.fy + e["r"] * 44
                dx, dy = tx - e["x"], ty - e["y"]
                d = math.hypot(dx, dy)
                if d < 8:
                    e["mode"] = "form"
                else:
                    e["x"] += dx / d * 6
                    e["y"] += dy / d * 6
        rate = (0.004 + 0.003 * self.wave) * self.fire_mult
        if self.enemies and random.random() < rate:
            # יורה מהחללית הכי נמוכה בעמודה
            shooter = max(random.sample(self.enemies, min(3, len(self.enemies))), key=lambda e: e["y"])
            self.ebullets.append([shooter["x"], shooter["y"] + 14, 0.0, 2.9 + 0.25 * self.wave])

    def move_divers(self):
        """חלליות שצוללות לעברך. של הבוס נעלמות למטה, של הגלים חוזרות למקום שלהן."""
        for e in list(self.enemies):
            e["flash"] = max(0, e["flash"] - 1)
            if e["mode"] != "dive":
                continue
            e["t"] += 1
            e["y"] += 3.2
            e["x"] = e["sx"] + math.sin(e["t"] * 0.05) * 90 + (self.ship["x"] - e["sx"]) * min(1, e["t"] / 90)
            if abs(e["x"] - self.ship["x"]) < 30 and abs(e["y"] - self.SHIP_Y) < 22:
                self.lose_life()
                self.kill_enemy(e)
                continue
            if e["y"] > self.H + 30:
                if e.get("boss_mini"):
                    self.enemies.remove(e)
                else:
                    e["mode"], e["y"] = "return", -30.0

    def move_enemy_bullets(self):
        s = self.ship
        alive = []
        for b in self.ebullets:
            b[0] += b[2]
            b[1] += b[3]
            if b[1] > self.H + 10 or self.hit_bunker(b[0], b[1]):
                continue
            if abs(b[0] - s["x"]) < 14 and abs(b[1] - self.SHIP_Y) < 12:
                self.lose_life()
                continue
            alive.append(b)
        self.ebullets = alive

    def lose_life(self):
        s = self.ship
        if s["inv"]:
            return
        if s["shield"]:
            s["shield"] = 0
            s["inv"] = 60
            self.boom(s["x"], self.SHIP_Y, "#4fc3f7", 12)
            return
        s["lives"] -= 1
        s["inv"] = 120
        self.boom(s["x"], self.SHIP_Y, "#ffeb3b", 26)
        if random.random() < 0.6:
            self.say(random.choice(SPACE_LINES["hit_you"]), 80)
            self.emotion.emit("laugh")
        if s["lives"] <= 0:
            self.end_game(False)

    def move_powerups(self):
        s = self.ship
        alive = []
        for pu in self.powerups:
            pu[1] += 2
            if abs(pu[0] - s["x"]) < 28 and abs(pu[1] - self.SHIP_Y) < 22:
                if pu[2] == "double":
                    s["double"] = 600
                elif pu[2] == "shield":
                    s["shield"] = 1
                else:
                    s["lives"] = min(5, s["lives"] + 1)
                self.say(random.choice(SPACE_LINES["power"]), 70)
                self.emotion.emit("surprised")
                continue
            if pu[1] < self.H + 20:
                alive.append(pu)
        self.powerups = alive

    # ---------- הבוס: פיקו הענק ----------
    def move_boss(self):
        b, s = self.boss, self.ship
        b["t"] += 1
        b["flash"] = max(0, b["flash"] - 1)
        speed = 0.026 if b["angry"] else 0.017
        b["x"] = self.W / 2 + math.sin(b["t"] * speed) * 250
        b["y"] = 110 + math.sin(b["t"] * 0.05) * 8
        if b["beam"] > 0:
            b["beam"] -= 1
            # 50 פריימים אזהרה, ואז קרן ל-40 פריימים
            if b["beam"] < 40 and abs(s["x"] - b["beam_x"]) < 18:
                self.lose_life()
            return
        b["cd"] -= 1
        if b["cd"] > 0:
            return
        b["attack"] = (b["attack"] + 1) % 4
        cd = 70 if b["angry"] else 100
        b["cd"] = int(cd / max(0.6, self.fire_mult))
        kind = b["attack"]
        if kind == 0:     # מטח בצורת מניפה
            for k in range(-2, 3):
                self.ebullets.append([b["x"] + k * 10, b["y"] + 50, k * 1.1, 3.8])
        elif kind == 1:   # שלוש יריות מכוונות אליך
            for k in range(3):
                dx = s["x"] - b["x"]
                self.ebullets.append([b["x"], b["y"] + 50, dx / 120 + (k - 1) * 0.5, 4.2])
        elif kind == 2:   # קרן לייזר עם אזהרה
            b["beam"], b["beam_x"] = 90, s["x"]
        else:             # שולח חלליות קטנות שצוללות
            for k in range(2 if not b["angry"] else 3):
                e = dict(c=k, r=0, x=b["x"] + (k - 1) * 40, y=b["y"] + 40, hp=1, gold=False, mode="dive",
                         t=0, flash=0, sx=b["x"] + (k - 1) * 40, boss_mini=True)
                self.enemies.append(e)

    def hurt_boss(self):
        b = self.boss
        b["hp"] -= 1
        b["flash"] = 5
        self.points += 10
        self.boom(b["x"] + random.uniform(-40, 40), b["y"] + random.uniform(-20, 30), "#ffab91", 5)
        if b["hp"] == b["max"] // 2 and not b["angry"]:
            b["angry"] = True
            self.say(random.choice(SPACE_LINES["boss_angry"]), 100)
            self.emotion.emit("angry")
        elif random.random() < 0.06:
            self.say(random.choice(SPACE_LINES["boss_hurt"]), 60)
            self.emotion.emit(random.choice(["angry", "sad"]))
        if b["hp"] <= 0:
            for k in range(6):
                self.boom(b["x"] + random.uniform(-80, 80), b["y"] + random.uniform(-40, 40), "#ffeb3b", 20)
            self.points += 1000
            self.boss = None
            self.end_game(True)

    def end_game(self, won):
        self.over = True
        if won:
            self.score = [1, 0]
            self.say(f"ניצחת את פיקו הענק?! ...החללית שלי הייתה בטיפול. ברור. ({self.points} נקודות)", 10 ** 9)
            self.emotion.emit("surprised")
            self.handicap = max(0, self.handicap - 1)
        else:
            self.score = [0, 1]
            self.say(f"פיקו ניצח! הפלישה הצליחה! 🛸👑 ({self.points} נקודות)", 10 ** 9)
            self.emotion.emit("proud")
            self.handicap = min(3, self.handicap + 1)
        self.finished.emit(*self.score)

    # ---------- ציור ----------
    def paint(self, p):
        W, H = self.W, self.H
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#05010f"))
        s = min(self.width() / W, self.height() / H)
        p.translate((self.width() - W * s) / 2, (self.height() - H * s) / 2)
        p.scale(s, s)
        space = QLinearGradient(0, 0, 0, H)
        space.setColorAt(0, QColor("#0d0221"))
        space.setColorAt(1, QColor("#1a237e"))
        p.fillRect(QRectF(0, 0, W, H), space)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 40))
        p.drawEllipse(QPointF(650, 90), 70, 70)       # כוכב לכת רחוק
        p.setBrush(QColor("#7e57c2"))
        p.drawEllipse(QPointF(650, 90), 52, 52)
        p.setPen(QPen(QColor(255, 255, 255, 90), 4))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(650, 90), 84, 18)
        p.setPen(Qt.NoPen)
        for x, y, sp in self.stars:   # כוכבים שזזים (מרגיש שטסים)
            yy = (y + self.frame * sp) % H
            p.setBrush(QColor(255, 255, 255, int(90 + 100 * sp / 1.6)))
            p.drawEllipse(QPointF(x, yy), sp, sp)
        p.setBrush(QColor("#66bb6a"))
        for bx, by in self.bunkers:
            p.drawRect(QRectF(bx, by, 9, 9))
        for e in self.enemies:
            self.draw_mini(p, e)
        if self.boss:
            self.draw_boss(p)
        for x, y, kind in self.powerups:
            box = QRectF(x - 13, y - 13, 26, 26)
            p.setPen(QPen(Qt.white, 2))
            p.setBrush({"double": QColor("#ff9800"), "shield": QColor("#29b6f6"), "life": QColor("#e91e63")}[kind])
            p.drawRoundedRect(box, 7, 7)
            p.setFont(QFont("Arial", 13))
            p.drawText(box, Qt.AlignCenter, {"double": "⚡", "shield": "🛡", "life": "❤"}[kind])
        p.setPen(Qt.NoPen)
        for sx, sy in self.shots:
            p.setBrush(QColor("#80deea"))
            p.drawRoundedRect(QRectF(sx - 2.5, sy - 9, 5, 18), 2, 2)
        for bx, by, _, _ in self.ebullets:
            p.setBrush(QColor("#ff5252"))
            p.drawEllipse(QPointF(bx, by), 5, 7)
            p.setBrush(QColor("#ffcdd2"))
            p.drawEllipse(QPointF(bx, by), 2, 3)
        self.draw_ship(p)
        for x, y, vx, vy, life, color in self.particles:
            c = QColor(color)
            c.setAlpha(int(255 * min(1, life / 20)))
            p.setBrush(c)
            p.drawEllipse(QPointF(x, y), 3, 3)
        self.draw_hud(p)
        if self.state == "intro" and not self.over:
            title = "👑 הבוס: פיקו הענק!" if self.boss else f"גל {self.wave} מתוך {self.WAVES}"
            p.setFont(QFont("Arial", 38, QFont.Black))
            p.setPen(QColor(0, 0, 0, 170))
            p.drawText(QRectF(3, 213, W, 70), Qt.AlignCenter, title)
            p.setPen(QColor("#ffeb3b"))
            p.drawText(QRectF(0, 210, W, 70), Qt.AlignCenter, title)
        elif self.state == "clear" and not self.over:
            p.setFont(QFont("Arial", 34, QFont.Black))
            p.setPen(QColor("#76ff03"))
            p.drawText(QRectF(0, 210, W, 70), Qt.AlignCenter, "הגל נוקה! +200  ❤ +1")
        self.draw_overlay(p, "← → זזים · רווח יורים (אפשר להחזיק) · R · Esc", msg_y=52, hint_y=H - 24)

    def draw_ship(self, p):
        s = self.ship
        if s["lives"] <= 0 or (s["inv"] and (s["inv"] // 5) % 2 == 0):
            return
        x, y = s["x"], self.SHIP_Y
        flame = 6 + math.sin(self.frame * 0.8) * 3
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ff9800"))
        p.drawPolygon([QPointF(x - 7, y + 12), QPointF(x, y + 14 + flame), QPointF(x + 7, y + 12)])
        p.setBrush(QColor("#1e88e5"))
        p.drawPolygon([QPointF(x, y - 22), QPointF(x + 24, y + 12), QPointF(x - 24, y + 12)])
        p.setBrush(QColor("#0d47a1"))
        p.drawPolygon([QPointF(x - 24, y + 12), QPointF(x - 32, y + 16), QPointF(x - 14, y + 2)])
        p.drawPolygon([QPointF(x + 24, y + 12), QPointF(x + 32, y + 16), QPointF(x + 14, y + 2)])
        p.setBrush(QColor("#b3e5fc"))
        p.drawEllipse(QPointF(x, y - 2), 7, 9)
        if s["shield"]:
            p.setPen(QPen(QColor(79, 195, 247, 200), 3))
            p.setBrush(QColor(79, 195, 247, 50))
            p.drawEllipse(QPointF(x, y - 2), 36, 30)

    def draw_mini(self, p, e):
        """חללית קטנה של פיקו: צלחת מעופפת עם הראש שלו בכיפה."""
        x, y = e["x"], e["y"] + math.sin(self.frame * 0.1 + e["c"]) * 2
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#b0bec5") if not e["gold"] else QColor("#ffca28"))
        if e["flash"]:
            p.setBrush(Qt.white)
        p.drawEllipse(QPointF(x, y + 6), 22, 8)
        p.setBrush(QColor(179, 229, 252, 140))
        p.drawEllipse(QPointF(x, y - 2), 13, 12)
        p.setBrush(HEAD)
        p.drawEllipse(QPointF(x, y - 1), 9, 9)
        p.setBrush(FACE)
        p.drawEllipse(QPointF(x, y), 6.5, 5.5)
        p.setBrush(QColor("#111111"))
        p.drawRoundedRect(QRectF(x - 6, y - 2.5, 5, 3.5), 1, 1)
        p.drawRoundedRect(QRectF(x + 1, y - 2.5, 5, 3.5), 1, 1)
        p.setPen(QPen(BOLT, 1.5))
        p.drawLine(QPointF(x, y - 10), QPointF(x, y - 16))
        p.setPen(Qt.NoPen)
        blink = (self.frame // 10 + e["c"]) % 2
        p.setBrush(QColor("#ffd54f") if blink else QColor("#ff5252"))
        p.drawEllipse(QPointF(x, y - 17), 2.5, 2.5)
        for k in (-14, 0, 14):
            p.drawEllipse(QPointF(x + k, y + 8), 2, 2)

    def draw_boss(self, p):
        b = self.boss
        x, y = b["x"], b["y"]
        if b["beam"] > 0:
            bx = b["beam_x"]
            if b["beam"] >= 40:   # אזהרה: קו מהבהב
                c = QColor(255, 23, 68, 150 if (b["beam"] // 5) % 2 else 60)
                p.setPen(QPen(c, 3, Qt.DashLine))
                p.drawLine(QPointF(bx, y + 50), QPointF(bx, self.H))
                p.setFont(QFont("Arial", 22, QFont.Black))
                p.setPen(QColor("#ff1744"))
                p.drawText(QRectF(bx - 20, self.SHIP_Y - 74, 40, 34), Qt.AlignCenter, "!")
            else:
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(255, 82, 82, 160))
                p.drawRect(QRectF(bx - 18, y + 40, 36, self.H))
                p.setBrush(QColor(255, 255, 255, 220))
                p.drawRect(QRectF(bx - 6, y + 40, 12, self.H))
        p.setPen(Qt.NoPen)
        p.setBrush(Qt.white if b["flash"] else QColor("#78909c"))
        p.drawEllipse(QPointF(x, y + 30), 110, 30)                 # הצלחת הענקית
        p.setBrush(QColor("#455a64"))
        p.drawEllipse(QPointF(x, y + 38), 70, 12)
        for k in range(-3, 4):
            on = (self.frame // 8 + k) % 2
            p.setBrush(QColor("#ffeb3b") if on else QColor("#ff7043"))
            p.drawEllipse(QPointF(x + k * 28, y + 32), 5, 5)
        p.setBrush(QColor(179, 229, 252, 110))
        p.drawEllipse(QPointF(x, y), 62, 58)                       # כיפת זכוכית
        r = 44
        p.setPen(QPen(BOLT, 4, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x, y - r), QPointF(x, y - r - 16))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ff1744") if b["angry"] else QColor("#ffd54f"))
        p.drawEllipse(QPointF(x, y - r - 20), 7, 7)
        p.setPen(QPen(HEAD_DARK, 3))
        p.setBrush(Qt.white if b["flash"] else HEAD)
        p.drawEllipse(QPointF(x, y), r, r)
        p.setPen(Qt.NoPen)
        p.setBrush(FACE)
        p.drawEllipse(QPointF(x, y + 4), r * 0.74, r * 0.64)
        outfit = current_outfit()
        outfit["glasses"] = outfit.get("glasses") or "shades"
        draw_accessories(p, outfit, x, y, r, top=-0.95, eye_y=-0.08, neck_y=0.95, t=time.time())
        if b["angry"]:
            p.setPen(QPen(INK, 4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x - 26, y - 22), QPointF(x - 8, y - 14))
            p.drawLine(QPointF(x + 26, y - 22), QPointF(x + 8, y - 14))
        mouth = QPainterPath(QPointF(x - 14, y + 16))
        if b["angry"]:
            mouth.quadTo(x, y + 8, x + 14, y + 16)
        else:
            mouth.quadTo(x + 4, y + 26, x + 18, y + 10)
        p.setPen(QPen(INK, 3.5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(mouth)
        # פס חיים של הבוס
        frac = clamp(b["hp"] / b["max"], 0, 1)
        bar = QRectF(self.W / 2 - 150, 44, 300, 14)
        p.setPen(QPen(Qt.white, 2))
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(bar, 6, 6)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ff5252") if b["angry"] else QColor("#ffab40"))
        p.drawRoundedRect(QRectF(bar.x() + 2, bar.y() + 2, (bar.width() - 4) * frac, 10), 5, 5)

    def draw_hud(self, p):
        W = self.W
        s = self.ship
        pill = QRectF(16, 12, 170, 30)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(pill, 10, 10)
        p.setPen(QColor("#ff8a80"))
        p.setFont(QFont("Arial", 14))
        p.drawText(pill, Qt.AlignCenter, "❤ " * max(0, s["lives"]) if s["lives"] > 0 else "💥")
        pill2 = QRectF(W / 2 - 110, 12, 220, 30)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 150))
        p.drawRoundedRect(pill2, 10, 10)
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 13, QFont.Bold))
        stage = "בוס" if self.wave > self.WAVES else f"גל {self.wave}/{self.WAVES}"
        p.drawText(pill2, Qt.AlignCenter, f"{stage}  ·  {self.points} נקודות")
        extra = []
        if s["double"]:
            extra.append(f"⚡ {math.ceil(s['double'] / 60)}")
        if s["shield"]:
            extra.append("🛡")
        if extra:
            pill3 = QRectF(W - 186, 12, 170, 30)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRoundedRect(pill3, 10, 10)
            p.setPen(QColor("#ffcc80"))
            p.drawText(pill3, Qt.AlignCenter, "   ".join(extra))


# ---------------------------------------------------------------- החנות של פיקו
SHOP_LINES = {
    "buy": ["וואו! אני נראה מושלם! כלומר, עוד יותר מושלם ממקודם. 😍", "סוף סוף בגדים שמתאימים לגאון!",
            "תסתכל עליי! אני הרובוט הכי אופנתי ביקום! ✨", "קנית לי מתנה? אתה החבר הכי טוב שלי. אחריי, כמובן."],
    "wear": ["כן! זה בדיוק הסגנון שלי.", "החלפת בגדים מהירה! כמו דוגמן."],
    "off": ["הורדתי. אבל אני עדיין מהמם גם בלי. 😎", "אוקיי, אבל רק כי ביקשת."],
    "poor": ["אין מספיק מטבעות! לך תשחק נגדי ותרוויח עוד... אם אתה יכול. 😎",
             "חסרים מטבעות! כל משחק נותן מטבעות, גם כשאתה מפסיד לי (וזה קורה הרבה)."],
    "try": ["רגע, אני מודד... מה דעתך? מושלם, נכון?", "מדידה! אני נראה אדיר, תודה שאתה רואה את זה."],
    "reset": ["חזרתי למקור! פיקו הקלאסי, עדיין הכי יפה ביקום. 😎",
              "הורדתי הכל! מזל שאני מהמם גם בלי בגדים.",
              "כל הבגדים בארון, ואפשר ללבוש אותם שוב מתי שתרצה."],
    "bare": ["אבל אני כבר בלי כלום! אי אפשר להוריד יותר מזה. 😅"],
    "refund": ["מחזירים לחנות: {name}? טוב... קיבלת {n} 🪙 בחזרה. אבל זה היה כל כך יפה עליי! 😢",
               "החזרנו לחנות: {name}. קיבלת בחזרה {n} 🪙. אני אתגעגע! 🥲",
               "אוקיי, החזרתי לחנות: {name}. הנה {n} 🪙. תקנה לי משהו עוד יותר יפה, כן?"],
    "refund_all": ["החזרת הכל?! קיבלת {n} 🪙 בחזרה. הארון שלי ריק... אבל אני עדיין מהמם. 😎"],
    "nothing": ["אין מה להחזיר! עוד לא קנית לי כלום. 😏 (רמז: הגיע הזמן)"],
}


class ShopWindow(QWidget):
    """החנות של פיקו: קונים לו בגדים ואביזרים במטבעות שמרוויחים במשחקים."""
    bought = Signal(str)     # המזהה של הפריט שנקנה
    changed = Signal()       # משהו השתנה (מטבעות או בגדים)

    def __init__(self, wardrobe):
        super().__init__()
        self.wardrobe = wardrobe
        self.buttons = {}
        self.try_token = 0
        self.setWindowTitle("החנות של פיקו")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(820, 600)

        title = QLabel("🛍️  החנות של פיקו")
        title.setObjectName("shopTitle")
        self.coins = QLabel()
        self.coins.setObjectName("shopCoins")
        head = QHBoxLayout()
        head.addWidget(title)
        head.addStretch()
        head.addWidget(self.coins)

        self.robot = RobotFace()
        self.robot.setFixedSize(300, 240)
        self.robot.set_emotion("happy")
        self.speech = QLabel("ברוך הבא לחנות! תקנה לי משהו יפה. מגיע לי, אתה יודע. 😎")
        self.speech.setObjectName("shopSpeech")
        self.speech.setWordWrap(True)
        self.speech.setFixedWidth(300)
        how = QLabel(f"איך מרוויחים מטבעות?\nבסוף כל משחק נגד פיקו:\n"
                     f"ניצחון = {COINS_FOR['win']} 🪙   תיקו = {COINS_FOR['tie']} 🪙   הפסד = {COINS_FOR['lose']} 🪙")
        how.setWordWrap(True)
        how.setFixedWidth(300)
        reset_btn = QPushButton("🔄  הורד את כל הבגדים")
        reset_btn.setObjectName("resetOutfit")
        reset_btn.setFixedWidth(300)
        reset_btn.setToolTip("פיקו חוזר לצבע הכתום, בלי כובע, משקפיים ואביזרים. מה שקנית נשאר שלך.")
        reset_btn.clicked.connect(self.on_reset)
        self.refund_all_btn = QPushButton()
        self.refund_all_btn.setObjectName("refundAll")
        self.refund_all_btn.setFixedWidth(300)
        self.refund_all_btn.setToolTip("מחזיר לחנות את כל מה שקנית, ומקבלים בחזרה את כל המטבעות ששילמת.")
        self.refund_all_btn.clicked.connect(self.on_refund_all)
        left = QVBoxLayout()
        left.addWidget(self.robot)
        left.addWidget(self.speech)
        left.addWidget(reset_btn)
        left.addWidget(self.refund_all_btn)
        left.addStretch()
        left.addWidget(how)

        tabs = QTabWidget()
        for slot, label in SLOTS:
            page = QWidget()
            grid = QGridLayout(page)
            grid.setSpacing(10)
            items = [it for it in SHOP_ITEMS if it["slot"] == slot]
            for i, it in enumerate(items):
                grid.addWidget(self.make_card(it), i // 3, i % 3)
            grid.setRowStretch(len(items) // 3 + 1, 1)
            tabs.addTab(page, label)

        body = QHBoxLayout()
        body.addLayout(left)
        body.addWidget(tabs, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(head)
        layout.addLayout(body, 1)
        self.refresh()

    def make_card(self, it):
        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        icon = QLabel(it["icon"])
        icon.setObjectName("cardIcon")
        icon.setAlignment(Qt.AlignCenter)
        name = QLabel(it["name"])
        name.setObjectName("cardName")
        name.setAlignment(Qt.AlignCenter)
        price = QLabel("חינם" if it["price"] == 0 else f"🪙 {it['price']}")
        price.setAlignment(Qt.AlignCenter)
        action = QPushButton()
        action.clicked.connect(lambda _=False, i=it["id"]: self.on_action(i))
        try_btn = QPushButton("👀 מדוד")
        try_btn.clicked.connect(lambda _=False, i=it["id"]: self.on_try(i))
        refund_btn = QPushButton(f"↩️ החזר וקבל {it['price']} 🪙")
        refund_btn.setObjectName("refund")
        refund_btn.clicked.connect(lambda _=False, i=it["id"]: self.on_refund(i))
        for w in (icon, name, price, action, try_btn, refund_btn):
            v.addWidget(w)
        self.buttons[it["id"]] = (action, try_btn, refund_btn)
        return card

    def refresh(self):
        w = self.wardrobe
        self.coins.setText(f"🪙 {w.coins} מטבעות")
        value = w.refund_value()
        self.refund_all_btn.setText(f"↩️  החזר הכל וקבל {value} 🪙" if value else "↩️  אין מה להחזיר")
        self.refund_all_btn.setEnabled(value > 0)
        for item_id, (action, try_btn, refund_btn) in self.buttons.items():
            it = ITEMS[item_id]
            worn = w.equipped.get(it["slot"]) == item_id
            if item_id not in w.owned:
                action.setText(f"קנה ב-{it['price']} 🪙")
                action.setObjectName("buy" if w.coins >= it["price"] else "poor")
            elif worn:
                action.setText("✔ לובש עכשיו" if it["slot"] == "paint" else "הורד")
                action.setObjectName("worn")
            else:
                action.setText("לבש")
                action.setObjectName("wear")
            try_btn.setVisible(item_id not in w.owned)
            refund_btn.setVisible(item_id in w.owned and it["price"] > 0)  # את הכתום הרגיל אי אפשר להחזיר
            action.style().unpolish(action)
            action.style().polish(action)

    def say(self, kind, emotion):
        self.speech.setText(random.choice(SHOP_LINES[kind]))
        self.robot.set_emotion(emotion)

    def on_action(self, item_id):
        w, it = self.wardrobe, ITEMS[item_id]
        if item_id not in w.owned:
            if w.buy(item_id):
                self.robot.preview.clear()
                self.say("buy", random.choice(["love", "proud", "happy"]))
                self.bought.emit(item_id)
            else:
                need = it["price"] - w.coins
                self.speech.setText(random.choice(SHOP_LINES["poor"]) + f"\n(חסרים עוד {need} 🪙)")
                self.robot.set_emotion("sad")
        elif w.equipped.get(it["slot"]) == item_id:
            if it["slot"] != "paint":
                w.take_off(it["slot"])
                self.say("off", "neutral")
        else:
            w.wear(item_id)
            self.say("wear", "proud")
        self.refresh()
        self.changed.emit()

    def on_refund(self, item_id):
        it = ITEMS[item_id]
        n = self.wardrobe.refund(item_id)
        if n:
            self.speech.setText(random.choice(SHOP_LINES["refund"]).format(name=it["name"], n=n))
            self.robot.set_emotion("sad")
        self.refresh()
        self.changed.emit()

    def on_refund_all(self, _=False, confirm=True):
        value = self.wardrobe.refund_value()
        if value == 0:
            self.say("nothing", "confused")
            return
        if confirm:
            box = QMessageBox(self)
            box.setLayoutDirection(Qt.RightToLeft)
            box.setWindowTitle("להחזיר הכל?")
            box.setText(f"להחזיר לחנות את כל הבגדים של פיקו?\nתקבל בחזרה {value} 🪙.\n"
                        "אפשר תמיד לקנות אותם שוב.")
            yes = box.addButton("כן, להחזיר הכל", QMessageBox.YesRole)
            box.addButton("לא, ביטול", QMessageBox.NoRole)
            box.exec()
            if box.clickedButton() is not yes:
                return
        self.try_token += 1
        self.robot.preview = {}
        n = self.wardrobe.refund_all()
        self.speech.setText(random.choice(SHOP_LINES["refund_all"]).format(n=n))
        self.robot.set_emotion("sad")
        self.refresh()
        self.changed.emit()

    def on_reset(self):
        self.try_token += 1
        self.robot.preview = {}
        if self.wardrobe.equipped == {"paint": "orange"}:
            self.say("bare", "confused")
        else:
            self.wardrobe.take_off_all()
            self.say("reset", "happy")
        self.refresh()
        self.changed.emit()

    def on_try(self, item_id):
        """מודד פריט ל-3 שניות, בלי לקנות."""
        it = ITEMS[item_id]
        self.try_token += 1
        token = self.try_token
        self.robot.preview = {it["slot"]: item_id}
        if it["slot"] == "paint":
            apply_paint(item_id)
        self.say("try", "happy")

        def done():
            if token == self.try_token:
                self.robot.preview = {}
                apply_paint(self.wardrobe.equipped.get("paint", "orange"))
        QTimer.singleShot(3000, done)

    def closeEvent(self, event):
        self.try_token += 1
        self.robot.preview = {}
        apply_paint(self.wardrobe.equipped.get("paint", "orange"))
        super().closeEvent(event)


# ---------------------------------------------------------------- המוח של פיקו
def ask_chat(url, model, messages, key=None, extra_headers=None):
    """שולח שיחה לשרת בפורמט של OpenAI ומחזיר את התשובה המלאה."""
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    if extra_headers:
        headers.update(extra_headers)
    body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        obj = json.load(resp)
    if obj.get("error"):
        err = obj["error"]
        raise RuntimeError(err.get("message", str(err)) if isinstance(err, dict) else str(err))
    choices = obj.get("choices") or []
    if not choices:
        return ""
    return (choices[0].get("message") or {}).get("content") or ""


# מודלים טובים לשיחה (ולעברית), לפי סדר עדיפות
PREFERRED_MODELS = ["gemma3", "qwen2.5", "llama3", "mistral"]


def ollama_model():
    """מחזיר את מודל השיחה הכי מתאים מ-Ollama שרץ במחשב, או None."""
    try:
        with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=0.7) as r:
            names = [m["name"] for m in json.load(r).get("models", [])]
    except Exception:
        return None
    # מודלים של קוד או embedding לא טובים לשיחה כללית, אז לא נשתמש בהם.
    blocked = ("coder", "code", "embed", "embedding")
    chat = [n for n in names if not any(bad in n.lower() for bad in blocked)]
    for pref in PREFERRED_MODELS:
        for name in chat:
            if name.startswith(pref):
                return name
    # אם אין מודל שיחה מתאים, נחזיר None כדי לעבור למצב בטוח במקום תשובות לא קשורות.
    return chat[0] if chat else None


# מצב בסיסי: מזהה רגש לפי מילים ועונה תשובה מוכנה
RULES = [
    ("proud",     ["הכי חכם", "הכי טוב", "גאון", "אתה חכם", "אתה מגניב"]),
    ("laugh",    ["חח", "בדיחה", "מצחיק", "lol"]),
    ("love",      ["אוהב", "אהבה", "חמוד", "מתוק", "❤"]),
    ("sad",       ["עצוב", "בוכה", "קשה לי", "רע לי", "נכשל", "מתגעגע", "בודד"]),
    ("angry",     ["כועס", "עצבני", "שונא", "מעצבן", "טיפש"]),
    ("scared",    ["מפחד", "פוחד", "מפחיד", "פחד"]),
    ("sleepy",    ["עייף", "לישון", "לילה טוב", "משעמם"]),
    ("surprised", ["וואו", "לא מאמין", "באמת", "מטורף", "!!"]),
    ("happy",     ["שמח", "כיף", "יופי", "מעולה", "אחלה", "נהדר", "הצלחתי", "שלום", "היי",
                   "בוקר טוב", "תודה", "hello", "hi"]),
    ("confused",  ["לא מבין", "מה זה", "?"]),
]
REPLIES = {
    "laugh":     ["זו הייתה בדיחה מצחיקה! יש לך עוד אחת?", "הצחקת אותי. ספר לי עוד בדיחה!"],
    "love":      ["תודה, זה מחמם את הלב!", "נעים לשמוע. אני שמח לשוחח איתך!"],
    "sad":       ["אוי, אני מצטער לשמוע... אני פה בשבילך.", "זה נשמע קשה. רוצה לספר לי עוד?"],
    "angry":     ["זה באמת מתסכל.", "אני מבין מדוע אתה כועס. בוא ננסה לחשוב על פתרון."],
    "scared":    ["זה נשמע מפחיד. אני כאן איתך.", "אל דאגה, ננסה להתמודד עם זה יחד."],
    "sleepy":    ["נשמע שאתה עייף. אולי כדאי לנוח מעט?", "אני מתחיל להתעייף. נוכל להמשיך בשיחה אחר כך."],
    "surprised": ["זה מפתיע מאוד! תוכל לספר לי עוד?", "באמת? לא ציפיתי לזה."],
    "happy":     ["איזה יופי! אני שמח לשמוע.", "נעים לדבר איתך!", "זה נהדר!"],
    "confused":  ["לא בטוח שהבנתי. תוכל להסביר שוב?", "זו שאלה טובה. אנסה לעזור לך."],
    "neutral":   ["אני מקשיב. ספר לי עוד.", "מעניין. מה עוד תרצה לספר?", "הבנתי."],
}


# תשובות חצופות ואגואיסטיות למצב הבסיסי ({topic} מוחלף בנושא ההודעה)
BASIC_REPLIES = {
    "empty":      ["שלחת לי... כלום? אפילו גאון כמוני לא יכול לענות על כלום. נסה שוב!",
                   "הודעה ריקה? אה, אתה כנראה המום מכמה שאני מושלם. קורה לכולם."],
    "farewell":   ["כבר הולך? מבין אותך, קשה לעמוד מול כל כך הרבה גאונות. ביי!",
                   "להתראות! אתה תתגעגע אליי. כולם מתגעגעים אליי.",
                   "ביי! ואל תשכח לספר לכולם שדיברת עם הרובוט הכי מגניב ביקום."],
    "punct":      ["רק סימנים? אני אמנם גאון, אבל עוד לא למדתי לקרוא מחשבות. כמעט.",
                   "מה זה, קוד סודי? פיקו הגדול מבקש מילים אמיתיות, בבקשה."],
    "compliment": ["אני יודע! אבל תמשיך, אני אוהב לשמוע את זה.",
                   "סוף סוף מישהו שם לב! עוד מחמאה אחת ואני מסמיק.",
                   "נכון מאוד. רשמתי את המחמאה שלך באוסף. זו מחמאה מספר מיליון!"],
    "proud":      ["הכי חכם? נו באמת, אחריי כמובן! אתה מקסימום במקום השני. מקום שני מכובד!",
                   "חכם? אתה? אוקיי, אולי קצת. אבל אני זכיתי בפרס 'רובוט השנה' עשר פעמים ברצף!",
                   "גאון? אני יודע, תודה! אה, דיברת על עצמך? חח, חמוד."],
    "how_are_you": ["שלומי? מושלם, כמו תמיד. קשה להיות כל כך מושלם, אבל אני מסתדר. ואתה?",
                    "מצוין! הברגים מבריקים והאנטנה נוצצת. מה איתך, חוץ מזה שאתה פחות מגניב ממני?"],
    "greeting":   ["אה, אתה שוב פה? חשבתי שנפטרתי ממך! סתם, פיקו הגדול שמח לראות אותך.",
                   "שלום! יש לך מזל, הוד מלכותו פיקו פנוי עכשיו. מה רצית?",
                   "היי! הגעת לרובוט הכי חכם ביקום. נא לא לגעת באנטנה."],
    "thanks":     ["בשמחה! אני יודע, אני מדהים. אפשר להמשיך להחמיא, אני לא מתנגד.",
                   "על לא דבר. ככה זה כשמדברים עם גאון. תגיד תודה גם לאנטנה שלי."],
    "confirm":    ["זהו? מילה אחת? פיקו הגדול רגיל לשיחות ברמה גבוהה יותר. ספר לי עוד!",
                   "קיבלתי. ממש תשובה קצרה, לא כמו התשובות המבריקות שלי. כתוב עוד משהו!"],
    "short_question": ["שאלה קצרה מדי אפילו בשבילי, וזה אומר הרבה. תנסח עוד קצת?",
                       "מה? תוסיף כמה מילים, גם גאונים צריכים חומר לעבוד איתו."],
    "question":   ["שאלה על {topic}? קלה מדי בשביל מוח כמו שלי. אבל בלי מפתח המוח שלי בחופשה, אז תן לי עוד פרטים.",
                   "{topic}? כמעט שאלה טובה כמו שאני הייתי שואל. ספר לי עוד, ואולי אעשה לך טובה ואענה."],
    "question_no_topic": ["יש פה שאלה, אני מרגיש את זה באנטנה. נסח אותה ברור, ופיקו הגדול יטפל בזה."],
    "tiny":       ["זה הכול? כמה אותיות? אפילו לי אין כוח לנחש. כתוב עוד!",
                   "קצר מדי! אני רובוט גאון, לא קורא מחשבות. עוד מילה או שתיים, בבקשה."],
    "topic":      ["{topic}? מעניין. כמעט מעניין כמוני. ספר עוד!",
                   "קראתי. אני חייב להודות, זה לא רע. לא ברמה שלי, אבל לא רע!"],
    "other":      ["קראתי את ההודעה שלך. מרשים. כמעט.",
                   "מממ, מעניין. אבל בוא נדבר על משהו באמת מעניין: עליי!"],
}
BASIC_PRANKS = [
    "אוי לא! מחקתי לך בטעות את כל המשחקים מהמחשב! ...עבדתי עליך! 😜",
    "שים לב: המחשב שלך יהפוך לטוסטר בעוד 3... 2... 1... סתם! 😜",
    "הלו? מישהו פה? לא שומע כלום... חח, עבדתי עליך, שמעתי הכול!",
    "רגע, אני מעדכן את המחשב שלך לגרסת 'פיקו הוא המלך'... 99%... סתם! 😜",
]
# משפט התרברבות שפיקו מוסיף בסוף רוב התשובות במצב הבסיסי
BASIC_BRAGS = [
    "אגב, דיברת הרגע עם הגאון הכי גדול ביקום. בכיף.",
    "תרשום את התאריך: היום פיקו הגדול דיבר איתך!",
    "ואל תשכח: אני מושלם, אתה... משתדל. 😎",
    "מגיעות לי מחיאות כפיים על התשובה הזו. אני מחכה.",
    "זו הייתה תשובה ברמה של 100 מתוך 10. כמו תמיד.",
    "אני כל כך חכם שלפעמים אני מפחיד את עצמי.",
    "אם היה פרס נובל לרובוטים, הוא כבר היה על המדף שלי.",
]


def simple_brain(text):
    low = text.lower()
    emotion = next((emo for emo, words in RULES if any(w in low for w in words)), "neutral")

    clean = " ".join(text.strip().split())
    words = re.findall(r"[\w\u0590-\u05FF']+", clean)
    topic = " ".join(words[:5]) if words else ""
    words_set = {w.lower() for w in words}
    low_clean = clean.lower()

    greetings = ("שלום", "היי", "אהלן", "מה נשמע", "בוקר טוב", "ערב טוב", "לילה טוב")
    thanks = ("תודה", "תודה רבה", "מעולה", "מצוין", "אחלה", "יופי")
    farewell_words = {"ביי", "ביי", "בי", "להתראות", "נתראה"}
    confirmations = ("כן", "לא", "סבבה", "אוקיי", "בסדר", "ברור")
    question_words = ("איך", "מה", "למה", "מתי", "איפה", "מי", "האם", "אפשר")
    only_punct = clean and not any(ch.isalnum() for ch in clean)
    exclamations_only = clean and set(clean) <= {"!", " ", "?"}
    is_farewell = (
        bool(words_set & farewell_words)
        or "בי ביי" in low_clean
        or "ביי ביי" in low_clean
        or "להתראות" in low_clean
    )

    compliment = any(p in low for p in ("אתה חכם", "אתה מגניב", "אתה גאון", "אתה הכי"))

    case = None
    if not clean:
        case = "empty"
    elif is_farewell:
        case, emotion = "farewell", "happy"
    elif only_punct or exclamations_only:
        case = "punct"
    elif compliment:
        case, emotion = "compliment", "proud"
    elif emotion == "proud":
        case = "proud"
    elif "מה שלומך" in low_clean or "מה נשמע" in low_clean:
        case = "how_are_you"
    elif any(g in low for g in greetings):
        case = "greeting"
    elif any(t in low for t in thanks):
        case = "thanks"
    elif clean in confirmations:
        case = "confirm"
    elif clean.endswith("?") and len(words) <= 2 and not any(w in low for w in question_words):
        case = "short_question"
    elif "?" in clean or any(w in low for w in question_words):
        case = "question" if topic else "question_no_topic"
    elif emotion in ("sad", "angry", "scared"):
        # כשקשה לילד, פיקו עוזב את החוצפה ותומך
        body = random.choice(REPLIES[emotion]) + " אם תרצה, נתקדם יחד צעד אחר צעד."
    elif len(clean) <= 3:
        case = "tiny"
    elif topic:
        case = "topic"
    else:
        case = "other"

    if case:
        body = random.choice(BASIC_REPLIES[case]).replace("{topic}", topic)
        if emotion in ("neutral", "happy", "confused"):
            emotion = random.choice(["proud", "proud", "laugh", emotion])
        if random.random() < 0.7:
            body += " " + random.choice(BASIC_BRAGS)
        if case not in ("empty", "punct", "farewell") and random.random() < 0.3:
            body = random.choice(BASIC_PRANKS) + " " + body
            emotion = "laugh"

    time.sleep(0.6)
    return f"[[{emotion}]] {body}"


# ---------------------------------------------------------------- תקשורת ברקע
class Worker(QThread):
    """שואל את המוח ברקע, כדי שהחלון והרובוט לא ייתקעו בזמן ההמתנה."""
    mode = Signal(str)
    done = Signal(str)
    error = Signal(str)

    def __init__(self, key, messages):
        super().__init__()
        self.key = key
        self.messages = messages

    def ask(self):
        if is_openrouter_key(self.key):
            self.mode.emit("OpenRouter")
            return ask_chat(OPENROUTER_URL, OPENROUTER_MODEL, self.messages, self.key,
                            extra_headers={"X-Title": "PikoChat"})
        if self.key:
            self.mode.emit("ChatGPT")
            return ask_chat(OPENAI_URL, MODEL, self.messages, self.key)
        model = ollama_model()
        if model:
            self.mode.emit(f"Ollama ({model})")
            return ask_chat(OLLAMA_URL + "/v1/chat/completions", model, self.messages)
        self.mode.emit("מצב בסיסי")
        return simple_brain(self.messages[-1]["content"])

    def run(self):
        try:
            self.done.emit(self.ask())
        except urllib.error.HTTPError as e:
            self.error.emit({
                401: "המפתח לא תקין. לחץ על 'מפתח API' והזן מפתח נכון, או מחק אותו כדי לעבוד בלי מפתח.",
                402: "אין מספיק קרדיט בחשבון OpenRouter. אפשר להטעין קרדיט או לבחור מודל חינמי (שנגמר ב-:free).",
                404: "המודל לא נמצא. בדוק את שם המודל ב-OPENROUTER_MODEL בראש הקובץ.",
                429: "נגמרה המכסה או שנשלחו יותר מדי בקשות. נסה שוב בעוד רגע.",
            }.get(e.code, f"השרת החזיר שגיאה {e.code}"))
        except urllib.error.URLError:
            self.error.emit("אין חיבור לאינטרנט או לשרת.")
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------- החלון
class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        global WARDROBE
        if WARDROBE is None:
            WARDROBE = Wardrobe()
        self.key = load_key()
        self.history = []
        self.display = []
        self.worker = None
        self.last_style = None
        self.games = {}
        self.shop = None

        self.setWindowTitle("פיקו - הצ'אט שלי")
        self.resize(780, 860)
        self.setLayoutDirection(Qt.RightToLeft)

        top = QHBoxLayout()
        new_btn = QPushButton("שיחה חדשה")
        new_btn.clicked.connect(self.new_chat)
        key_btn = QPushButton("מפתח API")
        key_btn.clicked.connect(lambda: self.key_row.setVisible(not self.key_row.isVisible()))
        shop_btn = QPushButton("🛍️ החנות של פיקו")
        shop_btn.setObjectName("shop")
        shop_btn.clicked.connect(self.open_shop)
        self.coins_label = QLabel()
        self.coins_label.setObjectName("coins")
        self.update_coins()
        top.addWidget(new_btn)
        top.addWidget(key_btn)
        top.addWidget(shop_btn)
        top.addWidget(self.coins_label)
        top.addStretch()
        self.mode_label = QLabel(provider_name(self.key))
        top.addWidget(self.mode_label)

        # שורת מפתח (מוסתרת עד שלוחצים על "מפתח API")
        self.key_row = QWidget()
        kr = QHBoxLayout(self.key_row)
        kr.setContentsMargins(0, 0, 0, 0)
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setLayoutDirection(Qt.LeftToRight)
        self.key_input.setPlaceholderText("sk-or-... (OpenRouter) או sk-... (OpenAI)")
        save_btn = QPushButton("שמור")
        save_btn.clicked.connect(self.save_key)
        del_btn = QPushButton("מחק מפתח")
        del_btn.clicked.connect(self.delete_key)
        self.key_msg = QLabel("לא חובה. בלי מפתח פיקו עובד במצב בסיסי.")
        kr.addWidget(self.key_msg)
        kr.addWidget(self.key_input, 1)
        kr.addWidget(save_btn)
        kr.addWidget(del_btn)
        self.key_row.setVisible(False)

        self.robot = RobotFace()
        self.robot.setFixedHeight(230)
        self.mood = QLabel()
        self.mood.setObjectName("mood")
        self.mood.setAlignment(Qt.AlignCenter)
        self.set_emotion("neutral")

        self.chat = QTextBrowser()

        self.entry = QPlainTextEdit()
        self.entry.setPlaceholderText("כתוב הודעה לפיקו...")
        self.entry.setFixedHeight(80)
        opt = QTextOption(Qt.AlignRight)
        opt.setTextDirection(Qt.RightToLeft)
        opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.entry.document().setDefaultTextOption(opt)
        self.entry.installEventFilter(self)

        self.send_btn = QPushButton("שלח")
        self.send_btn.setObjectName("send")
        self.send_btn.setFixedHeight(80)
        self.send_btn.clicked.connect(self.send)

        bottom = QHBoxLayout()
        bottom.addWidget(self.entry)
        bottom.addWidget(self.send_btn)

        # כפתורי המשחקים בתחתית החלון
        games_label = QLabel("🎮  שחק נגד פיקו:")
        games_label.setObjectName("mood")
        games_row = QGridLayout()   # שלוש שורות של 3 כפתורים
        games_row.setSpacing(8)
        for i, (kind, label, style) in enumerate([
                ("football", "⚽  כדורגל", "game"), ("basketball", "🏀  כדור סל", "basket"),
                ("bowling", "🎳  באולינג", "bowl"), ("kungfu", "🥋  קונג פו", "kungfu"),
                ("race", "🏎️  מירוץ", "race"), ("hide", "🙈  מחבואים", "hide"),
                ("climb", "🧗  טיפוס", "climb"), ("quiz", "🧠  חידון", "quiz"),
                ("space", "👾  פלישת חלל", "space")]):
            btn = QPushButton(label)
            btn.setObjectName(style)
            btn.clicked.connect(lambda _=False, k=kind: self.open_game(k))
            games_row.addWidget(btn, i // 3, i % 3)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.key_row)
        layout.addWidget(self.robot)
        layout.addWidget(self.mood)
        layout.addWidget(self.chat, 1)
        layout.addLayout(bottom)
        layout.addWidget(games_label)
        layout.addLayout(games_row)

        self.render()
        self.entry.setFocus()

    def set_emotion(self, name):
        self.robot.set_emotion(name)
        self.mood.setText(f"פיקו מרגיש: {EMOTIONS[self.robot.emotion]['he']}")

    def eventFilter(self, obj, event):
        if obj is self.entry and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self.send()
                return True
        return super().eventFilter(obj, event)

    def render(self):
        names = {"user": ("אתה", "#8ab4f8"), "assistant": ("פיקו", "#ffab91")}
        blocks = []
        if not self.display:
            blocks.append('<p align="center" style="color:#9a9a9a">כתוב משהו לפיקו ותראה איך הוא מרגיש</p>')
        for role, text in self.display:
            body = html.escape(text).replace("\n", "<br>")
            if role == "info":
                blocks.append(f'<p align="center" style="color:#e57373">{body}</p>')
            else:
                name, color = names[role]
                blocks.append(
                    f'<p style="margin-bottom:2px"><b style="color:{color}">{name}</b></p>'
                    f'<p style="margin-top:0; margin-bottom:14px">{body or "..."}</p>'
                )
        self.chat.setHtml("".join(blocks))
        self.chat.verticalScrollBar().setValue(self.chat.verticalScrollBar().maximum())

    # ---------- משחקים ----------
    def open_game(self, kind):
        game = self.games.get(kind)
        if game is None:
            game = {"football": FootballGame, "basketball": BasketballGame,
                    "bowling": BowlingGame, "kungfu": KungFuGame, "race": RaceGame, "hide": HideSeekGame, "climb": ClimbGame, "quiz": QuizGame, "space": SpaceGame}[kind]()
            game.emotion.connect(self.set_emotion)
            game.finished.connect(lambda you, piko, k=kind: self.on_game_over(you, piko, k))
            self.games[kind] = game
        if not game.isVisible():
            game.restart()
            game.show()
        game.raise_()
        game.activateWindow()
        game.setFocus()

    # ---------- חנות ומטבעות ----------
    def update_coins(self):
        self.coins_label.setText(f"🪙 {WARDROBE.coins}")

    def open_shop(self):
        if self.shop is None:
            self.shop = ShopWindow(WARDROBE)
            self.shop.changed.connect(self.update_coins)
            self.shop.bought.connect(self.on_bought)
        self.shop.refresh()
        self.shop.show()
        self.shop.raise_()
        self.shop.activateWindow()

    def on_bought(self, item_id):
        it = ITEMS[item_id]
        self.set_emotion("love")
        if it["slot"] == "paint":
            reply = (f"[[love]] צבעת אותי ב{it['name']}?! וואו, אני נוצץ! "
                     "רובוט כל כך יפה עוד לא נראה ביקום. 😍")
        else:
            reply = "[[love]] " + random.choice([
                f"קנית לי {it['name']}?! תודה! עכשיו אני לא רק הרובוט הכי חכם ביקום, אלא גם הכי אופנתי. 😍",
                f"{it['name']}! בדיוק מה שחסר לגאון כמוני. אתה יודע לבחור מתנות!",
                f"וואו, {it['name']}! אני הולך להשוויץ בזה בכל המשחקים. 😎",
                f"תודה על המתנה: {it['name']}! אתה במקום השני בעולם. אחריי, כמובן. 😍",
            ])
        self.add_piko_line(reply)

    def add_piko_line(self, reply):
        if self.busy():
            return  # פיקו באמצע תשובה, לא נבלבל את הצ'אט
        self.display.append(("assistant", TAG_RE.sub("", reply)))
        self.history.append({"role": "assistant", "content": reply})
        self.history = self.history[-MAX_HISTORY:]
        self.render()

    def on_game_over(self, you, piko, kind="football"):
        result = "win" if you > piko else "tie" if you == piko else "lose"
        coins = COINS_FOR[result]
        WARDROBE.earn(coins)
        self.update_coins()
        if self.shop:
            self.shop.refresh()
        sport = {"football": "בכדורגל", "basketball": "בכדור סל", "bowling": "בבאולינג",
                 "kungfu": "בקרב קונג פו", "race": "במירוץ מכוניות", "hide": "במחבואים", "climb": "במירוץ טיפוס", "quiz": "בחידון", "space": "בפלישת חלל"}[kind]
        if piko > you:
            reply = (f"[[proud]] ניצחתי אותך {sport} {piko}-{you}! 👑 "
                     "אל תתבאס, להפסיד לגאון הכי גדול ביקום זה כמעט כמו לנצח. רוצה עוד משחק?")
        elif piko == you:
            reply = (f"[[happy]] תיקו {sport}, {you}-{piko}! זה אומר שאתה כמעט טוב כמוני. "
                     "כמעט! בוא נשחק שוב ונראה מי באמת המלך.")
        else:
            reply = (f"[[surprised]] ניצחת אותי {you}-{piko}?! טוב, הברגים שלי היו רופפים היום. "
                     "כל הכבוד לך, באמת! אבל במשחק הבא אני לא מוותר.")
        reply += f" (+{coins} 🪙 לחנות שלי. תקנה לי משהו יפה!)"
        self.add_piko_line(reply)

    def closeEvent(self, event):
        for game in self.games.values():
            game.close()
        if self.shop:
            self.shop.close()
        super().closeEvent(event)

    def save_key(self):
        key = self.key_input.text().strip()
        error = check_api_key(key)
        if error:
            self.key_msg.setText(error.split("\n")[0])
            return
        try:
            with open(KEY_FILE, "w", encoding="utf-8") as f:
                f.write(key)
        except OSError:
            pass  # לא נורא, המפתח יעבוד עד שסוגרים את התוכנה
        self.key = key
        self.key_input.clear()
        self.key_msg.setText(f"המפתח נשמר! ({provider_name(key)})")
        self.mode_label.setText(provider_name(key))
        self.key_row.setVisible(False)

    def delete_key(self):
        self.key = ""
        try:
            os.remove(KEY_FILE)
        except OSError:
            pass
        self.key_msg.setText("המפתח נמחק. פיקו יעבוד בלי מפתח.")
        self.mode_label.setText("")

    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def new_chat(self):
        if self.busy():
            return
        self.history.clear()
        self.display.clear()
        self.set_emotion("neutral")
        self.render()

    def send(self):
        if self.busy():
            return
        text = self.entry.toPlainText().strip()
        if not text:
            return
        self.entry.clear()

        self.history.append({"role": "user", "content": text})
        self.history = self.history[-MAX_HISTORY:]
        self.display += [("user", text), ("assistant", "")]
        self.set_emotion("thinking")
        self.render()

        self.send_btn.setEnabled(False)
        style = random.choice([s for s in EGO_STYLES if s != self.last_style])
        self.last_style = style
        system = (SYSTEM_PROMPT + "\nסגנון ההתרברבות בתשובה הזו: " + style
                  + "\nוזכור: אתה סופר-חוצפן וסופר-אגואיסט! גם בתשובה הזו, עקיצות והתרברבות בכל משפט.")
        self.worker = Worker(self.key, [{"role": "system", "content": system}] + self.history)
        self.worker.mode.connect(self.mode_label.setText)
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_done(self, reply):
        # תגית הרגש בתחילת התשובה משנה את פני הרובוט ולא מוצגת בצ'אט
        m = TAG_RE.match(reply)
        self.set_emotion(m.group(1).lower() if m else "neutral")
        text = reply[m.end():] if m else reply
        self.display[-1] = ("assistant", text.strip())
        self.render()
        if reply:
            self.history.append({"role": "assistant", "content": reply})
        self.send_btn.setEnabled(True)
        self.entry.setFocus()

    def on_error(self, msg):
        self.history.pop()
        self.display.pop()
        self.display.append(("info", f"שגיאה: {msg}"))
        self.set_emotion("sad")
        self.render()
        self.send_btn.setEnabled(True)


# ---------------------------------------------------------------- מפתח API
def check_api_key(key):
    if not key:
        return "לא הוזן מפתח."
    if not key.isascii():
        return ("המפתח מכיל תווים שאינם באנגלית (למשל עברית או מירכאות מיוחדות).\n"
                "ייתכן שהמקלדת הייתה על עברית. העתק את המפתח שוב מהאתר.")
    if not key.startswith("sk-"):
        return "מפתח של OpenRouter מתחיל ב-sk-or- (ושל OpenAI ב-sk-). בדוק שהעתקת את כולו."
    return None


def load_key():
    """מפתח ממשתנה סביבה או מהקובץ השמור. מחזיר "" אם אין מפתח תקין."""
    key = (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        try:
            with open(KEY_FILE, encoding="utf-8") as f:
                key = f.read().strip()
        except OSError:
            key = ""
    return key if key and not check_api_key(key) else ""


def buggy_pyside():
    """ב-PySide6 6.12 יש באג שמקריס ציורים בפייתון 3.11 ומטה."""
    import PySide6
    return sys.version_info < (3, 12) and PySide6.__version__.startswith("6.12")


def main():
    install_crash_log()
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyleSheet(STYLE)
    if buggy_pyside():
        fix = f'"{sys.executable}" -m pip install "PySide6==6.11.3"'
        print("\nהגרסה של PySide6 מקריסה את התוכנה בפייתון הזה. הרץ בטרמינל:\n" + fix + "\n")
        QMessageBox.warning(None, "צריך לתקן גרסה",
                            "הגרסה של PySide6 שמותקנת אצלך גורמת לתוכנה לקרוס.\n"
                            "הרץ בטרמינל את הפקודה הזו (היא מודפסת גם בטרמינל להעתקה):\n\n" + fix)
        return
    global WARDROBE
    WARDROBE = Wardrobe()
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()