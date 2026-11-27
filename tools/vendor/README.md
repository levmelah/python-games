# tools/vendor

חבילות פייתון טהור שנארזות לתוך המשחק כשהוא מכיל `import bidi`.

למה: pygbag סורק את main.py לפני שהוא מריץ אותו, ואם הוא רואה ייבוא של חבילה
שאינה אצלו - הוא מוריד ומתקין אותה מ-PyPI בזמן ריצה. ההתקנה הזו הורסת את מנהל
הווידאו של SDL, וכל `pygame.display.set_mode` שאחריה זורק
`The video driver did not add any displays` - והמשחק לא עולה בכלל.

הפתרון: לארוז כאן את החבילה, ו-convert.py הופך את הייבוא ל-`__import__`
דינמי, כך שהסורק של pygbag לא רואה אותו ולא מתקין כלום.

* `bidi/` - python-bidi 0.4.2 (LGPL, הרישיון בפנים). הגרסאות החדשות הן
  תוסף Rust ולכן לא מתאימות ל-wasm.
* `six.py` - six 1.17.0 (MIT, `six-LICENSE`), נדרש על ידי bidi 0.4.2.
