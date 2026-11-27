"""
גלגלו את הכדור 3D - Sky Escape
================================
גרסה תלת-ממדית של המשחק, בנויה עם מנוע Ursina (מבוסס Panda3D).
כדור מתגלגל קדימה על שביל אריחים צף בשמיים, המצלמה עוקבת מאחוריו,
ויש תאורה, שמיים, כדור עם טקסטורת "כדור חוף" שמראה את הגלגול,
מטבעות זהב מסתובבים ומכשולים אדומים מחודדים.

התקנה והפעלה:
    pip install ursina pillow
    python3 roll_the_ball_3d.py

    כל תמונות המשחק (טקסטורת הכדור, חמשת הטרול-פייסים) מוטמעות בתוך הקובץ
    הזה עצמו (base64) ונכתבות לדיסק אוטומטית בכל הפעלה - אין צורך בשום
    קובץ תמונה נפרד ואין צורך להריץ סקריפט הכנה מראש.

שליטה:
    חצים שמאלה/ימינה או A/D   - מעבר בין המסלולים
    חץ למעלה / W (מוחזק)       - האצה! בלי זה הכדור מתגלגל לאט
    רווח                        - התחלה מחדש אחרי משחק נגמר
    Esc                         - יציאה

מכשולים חדשים:
    לבה (כתום-אדום זוהר) - שקערורית בוערת שאי אפשר לעבור עליה ברגל.
    רמפה (הכחולה, משופעת) - נוסעים עליה וקופצים אוטומטית קדימה,
    בדיוק כדי לעוף מעל בור הלבה שאחריה ולנחות בשלום בצד השני.

בדיחה: ברגע שנופלים (מוות) - קופץ מיד טרול-פייס למסך לשתי שניות (הספירה
נשמרת גם אחרי ריסטארט עם רווח, לאורך כל ההרצה): נפילה 1 - רגיל,
נפילה 2 - זהב עם משקפיים, נפילה 3 - עיניים אדומות ואצבע מצביעה,
נפילה 4 - הפרצוף השחור-לבן הזועם, נפילה 5 ואילך - הפרצוף הטורקיז.
"""

import base64
import json
import math
import os
import random
from collections import deque

from ursina import (
    Ursina, Entity, Text, Sky, DirectionalLight, AmbientLight, Mesh,
    color, camera, destroy, held_keys, time, Vec3, application, window,
)

# --------------------------------------------------------------------------
# הגדרות עולם
# --------------------------------------------------------------------------
LANES = 5
LANE_WIDTH = 2.0
TRACK_HALF_WIDTH = (LANES * LANE_WIDTH) / 2.0
ROW_DEPTH = 3.0
TILE_Y = -0.25            # מרכז האריח (העליון שלו ב-y=0)
BALL_RADIUS = 0.5
BALL_START_Y = BALL_RADIUS

SPAWN_AHEAD_ROWS = 9       # כמה שורות מוכנות תמיד מראש לפני הכדור
DESPAWN_BEHIND = 2 * ROW_DEPTH

SLOW_SPEED = 2.5           # מהירות ברירת מחדל - איטית
BOOST_SPEED = 11.0         # מהירות כשמחזיקים חץ למעלה / W - מהיר!
BOOST_LERP = 6.0           # מהירות המעבר בין איטי למהיר (כדי שלא יהיה קפיצני)

JUMP_IMPULSE = 7.5         # מהירות התחלתית כלפי מעלה כשעולים על רמפה
JUMP_GRAVITY = 9.0         # כוח המשיכה בזמן קפיצה (לא קשור לנפילה בסוף המשחק)
AIRBORNE_MARGIN = 0.15     # כמה גבוה מעל הקרקע נחשבים "באוויר" (בטוחים מלבה)
LAVA_Y = TILE_Y - 1.3      # הלבה שקועה מתחת לגובה השביל הרגיל
HAZARD_MIN_GAP_ROWS = 8    # כמה שורות לפחות בין רצף רמפה+לבה אחד למשנהו

HERE = os.path.dirname(os.path.abspath(__file__))
HIGHSCORE_FILE = os.path.join(HERE, "highscore_3d.json")
BALL_TEXTURE = os.path.join(HERE, "ball_texture.png")
TROLLFACE_TEXTURE = os.path.join(HERE, "trollface.png")
TROLLFACE_GOLD_TEXTURE = os.path.join(HERE, "trollface_gold.png")  # מהנפילה השנייה ואילך
TROLLFACE_THIRD_TEXTURE = os.path.join(HERE, "trollface_third.png")  # מהנפילה השלישית ואילך
TROLLFACE_FOURTH_TEXTURE = os.path.join(HERE, "trollface_fourth.png")  # מהנפילה הרביעית ואילך
TROLLFACE_FIFTH_TEXTURE = os.path.join(HERE, "trollface_fifth.png")  # מהנפילה החמישית ואילך
TROLLFACE_DELAY = 0.0     # אחרי כמה שניות של נפילה קופץ הטרול-פייס (0 = מיד)
TROLLFACE_DURATION = 2.0  # כמה זמן הטרול-פייס נשאר על כל המסך

_EMBEDDED_ASSETS_B64 = {
    "ball_texture.png": (
        "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"
        "gg=="
    ),
    "trollface.png": (
        "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"
    ),
    "trollface_gold.png": (
        "iVBORw0KGgoAAAANSUhEUgAAANwAAAD1CAYAAAA7+Zt/AABusklEQVR42u19e1xUZf7/ey6IZygSBUlnUAGxtaC0FQ0SpAtrahbqT0u0zExtN2htd7Xv"
        "2qZm5W62u7VB37Jyu6xS6eq6+dVq6YJo4K2ysNwVFZUZTEEkDGYRZub3xznPmec885wzZwa8dj6vly9hmDlzLs/7+Xw+788NMMQQQwwxxBBDDDHEEEMM"
        "McQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHk"
        "xygm4xZcOtLqdps1/uyzCYLPuEvnV6zGLbhwwfPo/AXmouIiGTDkh3mJDnSM88rvzWxoQkVsD9gEwaN1zJK7bZaK2B6KzygWwyYznq9xqm7K8xId8Iyb"
        "gIwbbgAAX/70aR7jSRka7kIGkQkAbIKAwoJCMwCzZdM/fM/XOE0AOmhQhXn8QRqb6AmbIDSco0s1A7AA8BUU9DWZMAkZN9yAyu3bvUXFRd5WtxvSffAZ"
        "gDOkUyIBSb6vRcVF5GePHkC1ut0mmyD41m7ck/pD3a7kii2fom7/13BcdfWk1GGZVzbXVvmOHj9t+qFhHwCg8cRpk3RcS/K1Q25Se6YR9ZXH/n1M2Cv9"
        "XT6Pnr0vl99zWexgAPClDss0fb1r5wdmU8dVn5Z/9hmA70dljQIADExK9T361ELT+19WNYwZmvYZe7wQxULOt7CgkBzDV1Rc5DUAZwgLCpSsWm2u2D7f"
        "VFxcBwBkkXg1Pnfln55cbXp82QO+2fn5w/o7ElKPOGuxZesW/Ozm9NsB9Imor4TL2Qy7I9oBoFso5+VyNoOz+AkgTHZHdJfeB5ez+ZB0XPKd3va4DHN7"
        "R7edn5Z/9hUA86isUd7+jgSfPXmg6Yuqr7cUFRfVSJreZxOE73jHLSjoa5buqblk1epLynQ1AKdPYwGAyYd15uLiOq+krdRA1W/DuvX2yu3bvf9tPOkY"
        "mHTVhK93/d0DwBFzZfKNEfWVPpez2WR3REfqWNAdNGB472FAZCE/pCQoD19d2+bT2gwowJJj+oJoL0tKQqRJOnYoIG2zO6LRHpeBg1/veb9n78u/v+G2"
        "WZavd+2s7N6z1xfPPLv8mE0QjvD4hsKCQu/Frv0MwLHEwqrVlsrt2yGRFcS3YkFlswmC9/UVr2ZUbPm0/5atW7w3Zd843nZqSz8AgwD0UFvQBCAuZ7NP"
        "OjbREGYAJgooJvJ87ImxiuP0H5ikev72xL5w1dTBnthX/J6aOl3X7TzmhqflWOA51zRQx45lX1Nb/L7q2jbe3yJ0ALIJwP7eQ0ejrd32t8xRN9XMnDt7"
        "E+0fltx9tyn/nXc8BuAuQtPw0fkLTADM0s7p5bynz6PzF9gAOM6cOj629OOPeowdnZ134ssPfXZHdLzKoiHH8RENYXdEmwCYGUDBnhgrA4iAJMoxhHu+"
        "3XqNUPx+5uQO1Wtj3xvs/bS0OPdQgKvTfT/1gFbStKD8WnaDMXPu52ct3ZLfnzbvt2vyp0+rJhqv1e32XGzEi+nHBjCh+x9MjyStNFHMoEJeX/HqrRVb"
        "PrUAuL71ZFVGb8uJGwH0ZLQTKECRRUN8JDMxtYhGsET1gaOPoNBCNKjUgPTNF/UAgOMHygEA+44KiGreSRYufR5cM7M9LgP9e1sxuJ/ICsYPzMY118ep"
        "AjIYMAkQQwGhGjCP7q1iTV76nnqltemVACiDsDVm1Hs3ZOeW3HXv9M02QThdWFAY8cyzyzsuFuD9GABnKlm12pw/fRq7o6LV7e6xYd365E83bxppNnXc"
        "aju1ZZBkEvIWs2wCArDYHdFggcVqKp62ohc6Wdj7t25WLEItMHWl2B3R6HtNFgb3c8tgVANiZ0BI3w+l5qvjgo8FYUpCpEcyU63k2Zy2xP/h4b9u/MuY"
        "oWnfMeSQAbjzRXZIlLyHAthlB7d8kPLCW2sdZlPH/4uwnhl/4ssPezD3wQvAR4iDlIRIC23+sdoqmCnYrdcIxWL9ZM06AJAXWVll/VkDE02gUItXsZgJ"
        "sHMy4lBd24aUhEi0RA/H4H5u3DxlkqYm5AGRNkfVNh014FaUblOYnyriAWCqrm0zAzjZJ2PmcwW/WfzWhnXrT+ZPn9ZqAO7cg8wMKubV6nZ3e/etVaPr"
        "/rP9jmMnT+ZE1FcOZLWH3RHdnpIQaQZgsifGyuYLD1xqZiEr+7duBgAcOXBIXkShgouAhmUc9YheLannO1qihyPn5nRNDRiKj9hFwOsgGq81ZtQ7z732"
        "5iIAhzasWy/kTZrYahMErwG4s3QNBQV9LRJd76XAl3zm1PEHI6xn7o6or3TQfpfdEe1LSYj02hNjLRKw5PvgaTnG9bm0dmoCrorSnSEtdiI5GXHyz/1S"
        "0wAAjj4CBmWNDUqE6Fn833xRj4iWXXAecyu0Ky1kM7A7omU2ldWGRPudC/Dt37pZvp8a4pOAF9Eel3H8p5njHrjr3ulfb1i3vjl/+rQmA3BnR5vJxEfJ"
        "qtXX1xyoKtz2z3f6X+45Poo423ZHtEdaPCZ7YqxZS3Op+Ry0j3LkwCEF+6ZXc9GLuF9qmgyqcMw2ns/EAlQvUGlfkt00ro7x4vuoHlwt2C81TZfZGS4A"
        "Q9V2Lmdz3Zqv3bcA+DfEmKTHAFwYzCLgz7srLCg0+7DOVFxc55H+HvHLWbMmt56sGt/bcmKKy9lsphZ3hwQwsxbAaBDRQArHROMBjAaXFitJNCWh1+nz"
        "6KyvR4Od1qRqZMmZkzsUAKQ1IO0bErlv6ZKQNHAoINSp7TzVtW0WAKevvfOpP8ycO3tZYUGh9Zlnl3vo9WMALkwSpNXtHvDLWbNuuazp43kuZ3MqAzJT"
        "/4FJck4jq5F4pIHeBctmVdDZGXq015mTO2QNRft3Z5NA6QrNu3fDYgX4WABX17ah7zVZeOg3Y0MGnl42dO0rG4J93CuRKbj2zqcKZs6d/eKFxl5esIAj"
        "Sbytbnc8gAibIDil1wc98sCMh22ntsxwOZsvo03GfqlpFuKHsVqKZenCFd5xSPCa1WBk8fAAFgqpQb6LDpJrmZBaJhoxRVmwq0m/1DTED8zG0Nzb5Wv6"
        "ZM06RQiD9vWIRtdraoYKvNLXiwPO254YS7/mkZ5RU3r+n7PyJk2sA2C1CcJJsqYMwKkA7v82zrfePv5ZAUAcANsjD8z4uQQ0m0Q2eACY+qWmmXkgO2sa"
        "QVr4akwlWdjWpt0o3+XVDTDWBKWP35nFq2dxtzj3YEfFQdWYGM9nO3NyB95YtET3+7sKeDzQZaeb5XtNmZf/fnrd4ZEAztgE4bQBOBWgPTp/gaWouKhD"
        "+t36yAMznrWd2vKgy9ncXVqUHgBme2KsibfbKcmOhrBBJTGYmlkiLMAONvTUrcVogAULPKuRJyyhQwvxBS1RfbgMrJZPuX/rZk0tmHjrL5A7Ybz8fgIC"
        "WuMRmTwnDzHXze30pqAFOntiLJJjGwNA1xoz6v+ee+3NBRvWra/Jnz7tv4ZJyZiQ1O8R77616r6v//m7+S5ncwrxzwBYaKCxAOOBjH0PWYAANONsRKIc"
        "QwICumSR01qM9cMqDov/Zw4IBFlm7nBNhpJeYLQpyCNUtExfHsGhpbV5ZrEWW8gCT03jdbW24/l02elmdPQYRhMsHdW1bdak3N/+adaDcx9dMD/ZVFxc"
        "12EAjjjme9+7PCk5N8omCLkFM/L+J6K+8mppsXRIMbOA87VE9ZEXIK2VtMCkBS4eqIjwNBhLvPBAlpMRp1jQwZKQtXwtrVIYOt8zmPBibKzwNgWaPGEB"
        "ddvPl2u+pyu0HX2veOxlZu5w8TmIr3sAmMoq63fEZz/ws6LiolZQCeU/KsARul8SG4ArbIJQ9/qKVx//vGLT0oj6SgWtz2ah02YSoCxZCUbxh0uW8MxD"
        "AjAeyNQWbbC4GgEZDa6zlVsZDKA0e0lrqFNfrZA1THa6Wd6I0vMewtDc2xVmph4gh6vleJp38pw8HP/yPWJ5ENNy43OvvTnx0fkLzmtN3QWh4dasKeh2"
        "+/hnB8zOG/5gb8uJRyhq30LMKFZooLGaJxQWUI/QoApYPDpAphdgalozFCaTxNd4su+oqPGjmnfqJnEI6GjfjNZSNPAyc4ejonSnApxq2s6eGIvcmQWd"
        "jt3RviZhK+2JscjMHUmDsb26ts167Z1PzZ05d/arJatWW85XFfk5BxxF9ycB+F5S794FD059/+ruX9wAwJOZO9yi9nn65tIajOc7dbXQ4KIBxvo/WuCi"
        "a8ZYkOkBGg0u4rPoNZu1cj8/WbNOLv/hxQPp9DMCvszc4UjNewIA8MFLC2SGk2g8S1Qf3Pbz5QGhhM6ATm3z4pmW9sS+ZDPoAGDduNO86f0vD98OsdFS"
        "x48CcDQp8uj8Bb5nnl0+eMGDU/96dfcvhtkTY8/0H5jUTYtxA4Dk2EZZo5HFoQYyFiS8hatGNmgRDbzCUdbv42le3vfo0WbED0yObdQNMj1+K68ujyzq"
        "T9asw8fv71acH+++kSwT2oykfSliZu7dsJibhBBKlgovTKCl5SgwdlTXtln7ZMwsXPD4H4oLCvpazweBcj5NSiuAjrnTprxz3WXb77Inxp7JzB3ZjUda"
        "sGAr3+WVTSIeScHblbXMTD0Z82qlObwqZ7WguxrR0ZVAUyOAtIQlh3iaWg/4aOC9sWiJvOiPf/keDruvwc1TJgEQKX2GwueCjoBLL8lEtBwBHdFykmnp"
        "hVjW43x63eGrFl6d0rbs2+pz3hz3vACu5O67I/Lfead9dn7+9MuaPv7brIlCe/zQOyLIbsvGl9jdiwYbS7nnZNtlzUM0TOACU5qhLGjV8gVDIVh0LXQN"
        "sBGgEdHqY6LXbNQStZgee0zCDNJmJ+tDEjOSaLvJc/JkQNy3dEmAVqJBxxM9rSW0tBwA2bSsrm2z9kq97+HfLX+maF6iw/p8jbPjkgYccVjXbtxjr3hp"
        "9I6cbHufzNyRiHIMMfMePo8WZ8Fmd0Rjxv1ZXBKC1lBEaG1B3ltWWR8A4FDYvHCEU5cHl7NZATY9QFMzEcMVrYA6ASAPeLRFQTQWIU1obdN/YBJS857A"
        "qa9W0Gyi7NMFAx0PcLSWo/178r3S9xAtV/v0usOpNkFoaXW7z6mWs5xrE3bd+vXeVre7+0vLfl18ddx3N9425WfeKMcQxXm0N38nl9879x/WBNu9s2/G"
        "A48V4uTRahw5cAjffl6N6Bib4l+MIxnmbpejX//e6NEzBt7ufrOrR88YJCTbcdN1zejX04bDzlZUHAYSeihP/HRzG6KjI7v0ZpxuVmrC6OhI/PSaaHmH"
        "TktPhT2xL043ncaRA4fwQ1t3NP/QgejLA5tfRceIDV27RV/Z6fPqFn0lukVfiV79U9Dd0oLomMtxuum0eM5Np3HyaDXsiX1xzU9/gnF5P0XriVocdrbi"
        "sLMV7bCi1xVW7Pm0DPVHv0bmPcuQdkMKNq5cjVjzfgy+MRfuw5/iu8P70T/nN4hOGAibtRW1h1w43dSK6B/KEXPVqEBW2u2CxeaQf2alvfk7nG46Da+v"
        "Da6aBkTH2HC6qRVeXxsSkvvhsj5X4dvP/20C4Gls9sS896+qY19UVe1oKXnTur2p2XvJabhWt9u0Yd16c96kib3ffWvVGPcXT66cPCevI8oxxBpKsi9t"
        "/r1R+qLsE9DMZcCuolL/xpId1qbdAIDyXV7VzP2u0nQ87UYnKefOLJDzG3mit81DZ8iIULQe0S7kvvG03aY/3iMxiCPl50s0Gp05QsIqqhsC07aCZYNZ"
        "LZedbkb80DsUWu7b/17vWv7y24MlLXfOynfM51K9SbGPju3lpVPtibHeKMcQs9aC4IEtc4ASbKSGjAc2S1Qf1R4kxDQi/wZljUX80DtwsKEnstPNuHf2"
        "zWGRHLpZQke0DN6cjDiFr0gWIb24ee3nulK69RqhCU76PtEblfOYGxWl2wCI8bmFi8YhJyNOsWG9sWgJzpzcgXG/+RssUX1kYPUfmITS14sBADHXzcXk"
        "OXkyYMhz1bs5RDmGyOfFrgXix8cPvYOsec/V3b9wvPvWqlkkd/eSMymbv2+2lm3ZkvzuW6t+0utkyeLbpvzM2y36SgsxE4ipQGu3002tCmaRmHkLF41D"
        "r/4psqOsupt0u5yr2aJjLuf6Opcl3okBV9lRf6IFPT1f4cbROTh08DjX9Osq+ek1So05eU4eukVfKXfyosHma/8B5m6i6cialaebTiM65vIAk5K+v7oW"
        "hM0h/+OZbsTkJOamI6EnzGYrjhw4BLNZnCOSkGyH5UwTyirrcdjZigEJUVj71oeIi+2FrLseQv3Rr7F3+5dISLajR88YfPHJhxhwlR2XJd6JJEcLvv38"
        "3/D62uD5oQG9+qfoPndiVn7feIq6L6043dSKWPN+XNbnKsSa9+NInajMvq75IfHOyfcU79ix0/fEE+cGB+dSw/kAHNxeXnp3v9Q0X5RjiE+PdmPab+Pe"
        "2TdjUNZY2cQhWoyn3cLd6QdljUVHj2E4cuAQZtyfFWBGnq00q8zc4dxE6fMlwcxRetPqPzAJRw4ckqn5zNzhsllZVlmPlIRIlBT9GR+8tAC3/Xw5+qWm"
        "ye/tPzBJ1oK0pqNN2bAtCUbbUVrOG1FfOeD1Fa/eazLBV7JqteWSAlxRcZEHgMl2asvoEZnJ6NZrhIVnJtDxFNofIOwdieWEa26pxanoxdWt1wik5j0h"
        "LyKaAe1KtpItYiV+i1aPx7NtWoZjapJ72n9gkpzeRUA3LX+wAnRvvfqJDLrM3OGyhZKZOxylrxfjzMkdiHIMke+9q6auU6BLjm2U/XJyX7PTzeT+d/+8"
        "YlMB5e5cGoArLCi0AMAvZ826PyUhsk+UY4iXR9i0OPfID4DEsog/kJMRJ5pb1MPn5Vh2pRDQWZt2Y+GicbJ26wrQsfE9lv5nzclwpSta1wXTdjToCHgq"
        "SnfiyIFD6D8wCdPyB8PuiJaf41uvfoK9GxYr7i+5B6Rv56CssbpDIqzQnzvY0FPWcuR7JC1nsSfG+iLqK6+fnZ+f2+p2xwAwM0n1FyfgfBBv4mVNH0/L"
        "zB1uVgtk0jv72m3NcnNSogFirpsrF0eGzQ6G2KY7Ne8JOWZHduvOAo0FG63d9O7moWw2XQk6NeARQoUGHXEL+g9MQk62XbF5VpTuxJmTO2TznWZf92/d"
        "jBbnHsVAkhbnnk6blxwt501JiLRc1vTxEgDCucDCWQdcyarVluLiOs+HH+y4DUDmoKyxXh5Z46edxSD05JHR6JeaJpuSbEBUrwboCi1IEnT7D0ySzduu"
        "ABq9I5OF3Nm+/Vqg4/3rrLZjQUBrun6paXjzr1tx5MAh2acmm2h1bZtcrMqGAJzH3AH3gfweDHTBUts4Wq4jJSEys+jp50YC8J5txvKsz/jOnz7NBAB/"
        "f+svltuz7REIMqOMyIz7s/DmX7dyTUk9QrcWcB5zBy1GPXNyh+Z3DMoai0MblyIzdziqa7fqNi31pIapxZzCMSd5k2/IIjvY0FP2aQBImmVzQAxPz70m"
        "sTCW7Y1yDMEgKRPF03IMKQmRWF2yDwsXJcHTQggMf61fi3OPanYMGbvFgk/rM6H6dwcbepqy082++S++ci+ANRkN9b5nzmLvk7MOuHmJDt+yb6tNs/OG"
        "T+w/8CpArMI188zJIwcOySYH0Uz2xFj55pJyf72LUQ10rpo62BFaGlS3XiMQP/QOuGrqMOP+LCxbuqnTQOOxaORcta6PXBdvI6ETBgIrHxrgqqHfvZM5"
        "l21y2huJU+oBH3km9P20J/bFkQOH0C81DTmowrKlm/Di67PlGBx7fwZljZVdBUcfQb42Gmz03Ds10JH3k04A9H121TSgfJcXmT3E48QPvQPlr2ywJMea"
        "veOHe8cOvLFwZH5x0Ta8886FpeFa3W4rAM3ZXKTubdm31VcCsN444PtbpZtlVfevGvyM1Q7iC4xUPHS1G8o2lCGZJ8FARy+UYFou5rq5cNUsltnKriBQ"
        "LFF95O/srI9SUboNZeUubhaLnjaBZeUuuBIiKSBu0GwNoablyD3tP9Cf22ivbYOrpk4mVEgFBP0c9PrgwUDHW1f0xiZq/DtkX+5gQ09fdnqjeeOLGxe2"
        "ut1TDh0svSw19Y7vzkaXL92AKywotEiNWH0Art6wbv0BAKpp8TZBwLxEh+XR+QtOABg0GOgJ/9wvhXZrce6RNRrRbnXf7EZOtl0BBi1zi07lYW8wrw0D"
        "+/BCMS1bnHtwy5hh+Pj93Z3qc2lPjFVoqCjHEEDHhiJ+Vnzt6F4oqijWbuP4l4c7EzesB7APwKZOHgNYu21TwGvkuC8/fTNGZCbLG6qWC0DeY0/sq3uT"
        "Yu8fefbxQ+/AwdJtFgDen/Rx37Ly5RVPzXpw7u9xltIerTqB5pHiaARMX+s5+PM1Tg+Ki/D6ildvH9rr2GVRjiEdat/p6CPg6F6lSUYAwmsFrnYjtV7n"
        "VRCIx/LnK4ptCDbjyAn1qo2I+ko5RABEc5sIBZPMAQAq61FxeB9w/6awF3Hgz/7j86of6GGNXSH9e4uPk9wv8ruaqN3XBx/7EC8/7TcnyWZDp+axm6Oe"
        "JAG6uxv5+WBDTyRjN1w1oumcmTsSa1/Z4MvJtncr3VOWAcw9WVhQaD4bE3h0o3h2fv6dZlPHHOkzptKPP9LPkLW6MzIH4ApplrWJpv5/jJI5QNskDRUM"
        "9KIPtuBDBcLZErJpkY2r4jCQN2G0/NqGf3yoee/a4zJw27B2+fURmckBGlCrryYJfhPGUvJ9OwBYtzfkzfv9Hxf9pbCg0Er6o54LwJla3W488sCMJzZt"
        "3DgVwEAYYshZ2HyIVTB5pDiR9ciJDlXA6ZHJI5UV/Gz/Gxpw5bu8dP8Tb3a6GSvXu12ZP/9wxOTxQ453db2cRc2M3Llzp3dgvwETVhT/5X8h+l9kyGE4"
        "/0z4kc0TN0Sf1Db5f/72aBv69BPdiH//+2DYx/z2aBu+PdqGrXtbsXVvKzZvbcDmrQ3YurcVnh/Emr0ffrCgv92EI3U+uWauR89o07atTu+1Q67s8eEn"
        "3zg+r/pmbVfXy3EBt3PnTjMA35VXCL+t3r8/FWKHowj4B5yH+s8AmyG65CeDB3YacMEATsC46sMWXNnDigjvGfToGQ17Yl/Emveb937T0n5lN+e1/2/O"
        "H/f/9m+rv16zpsC6du3OLgGdSYNM6RiUYC9o/b6xCEC7BDhDDDmrMnmk6J91xqTszHfPuD8LRw4c8rpqGkzVtW3fPrf5eCpxr7rCtAwGuEdav2/8swG4"
        "80OqaJFKxE8hJAshIS52Iopc1/m+joVT4zwALF/9cMPfVqxecy8AS6vb7e0s6IJRWj5j+Z/9Bfb067/nBnHbF7zH3elffvpmuUzJL3egW68RaJ/12HnR"
        "Dl0lXVWN0VlZ9na9ZfLIaI8NW+4peu55X+Ej82Y8On9Bt1a3u70zoDMbS/78C4klkYz4cDNOuqoq4HxLe1yGave0cylrtzVb1m5rPvPM4t/eW/Tc88VF"
        "xUVnbIJg0mEhhq3hQtqp6ZG85Gc102Dh1LiA17Teb4hfdjbG4eZL9NoqDgM4/GFQk1vXcbpGIgB0PLP4t3PmTpvie+61Nx/ZsG59RN6kiWfC0XRdmrxM"
        "J8sGa4Ya6vwyQwwJBUzBQBkCIE0STnybNm4swAMzkp577c0ZNkFoaHW7ewNoCCUjxXq+bhpvQL0hPy7JHABFkbFWnWGoGivY+1lA6jz+mU0bN47FAzP+"
        "COC+DevWd8+bNNEMnSVnBmlylhaRmtOvZS6zidRaflzjoaZL5n7ZE2NhT5R/U9TrAf4eoVoaKxzzkfcZ+js4fzcB6AagY9PGjTPmTpviy5s0cbFUsNrR"
        "VYAjwzXaJYKFANCCTgazWe12KWk7epwUIBZ6Oo+5sXbbJ4FA4+zqfrbyKPf4dA7hpSB0ypWrJrDp7/kwVQn4OOdgBdC+aePG+/o9VmArKl55V0FBX0tx"
        "cZ2uJkRc0JSsWm3JmzTR/O5bqyY9Pv/ht/WSJqHs6gunxgUUSF4qpAnRcikJkTLoDjb0xEPL9oV0HD79D2wpP4HZs/iNFPdXv8h9fYFKiOF836fOaqtQ"
        "2cxwj898zgcx1bFjzO0T/t+rJSWbSFVNyBpOKrrztE5yO+66d/rmyCjbsC3v/3MqgJTSjz9yAWg50+q+B0A8/HmS/J1LxSbPHKCu4briIVwITn0mmuFy"
        "AtW10XK1dbjCxuhGZfe+ZMgPOnlZ7+Jnh0Oy64wdU6b8W6BJa4nqg6N7q+Q1SG/67GQl6XeTZPF1f////vGPtRv39P/s4dtPFBYUmoONMw4AHKE6bYJw"
        "RHrpc+mfLFOuFXIrDqM3DTg1zURnbtMgCyVckJMBLHu7/uI0l5wi8DoDNhZ0neladrFaCgQc9LgyAq6UhDiF+U56uBDLgme60hUE9kTx9+x0sb3EjPvF"
        "97z5162yaUu32ZdAZ5Z8t4iP3ln2xooa5+h5m/4RtAGRqg9H+vNtWLfeXLl9e/dnnl3+30fnL+jjO127acM/PrxWYmZ0B85D8dEuBX9Oa/RVV2m6i5VM"
        "IpstYSkB5agwnoYSO3255O5nsybGy3+TOnBRcodcE5cMfwMltisAC0Sx34t/qOPCJ+8Sz/eVDfI4M3Le0s9WiUT5GYDZz9c4Xw1mWqoCjgrqeQC0XJ92"
        "7aJ/vPVaQeYAxGUOgLfi8NnJUrmUyJOzBbqLEWyLHo5X9e0rDouWEGmJyK4FEWCCAlxaGw/d05KAjwAPAJJj/X61mtZz1TRg7SsbkJk7HJPn5CEzV+zP"
        "suxt5eYg4cD3yNj4Pzy97vD6R+cvaNLqhaLJUhYWFFqfeXZ5xCMPzFj++PyH52QOQDe7I9oDwNK5Phk/PrE7osPuLcLrvaJXE14IWrHiMLByvVs2A2mf"
        "jab86VkEORlx8jRbdgprsImo7CRd8d6J46poSY5tRHKsWQYerxEVads+eU4eJs/Jgz1xG1aX7KO1nbniMDrWbmvuuWnQwDn7a12/LyouMre63VabILTr"
        "BlxhQaH5mWeXm1e+vGLxqaqNBVLqlg9SDd2LCwejrNxlpGLp1HIuZ7O8i7NA7Op7eCGanSzY2FHRdKbRoofjET/0Dl1t+rTyR1ngEe1IzwKkgUfPHGc1"
        "3tpXNqBfapo8wjinpoHWdpaKw/AMiWlcsO7Vf7yfPOq2GgAJAPay2o4LuJJVqy2V27f7bIJw4yNj4x+xO6LPpCRERtgTY03kBOOHjkRy7HuaBEg4wpIr"
        "l0JGCg06tYXIE7GhkViI6TymLMik+3/QQnrz0/LB7qO4bVg7bht2M+dvEeckXMBjIolPR4Nt8pw8VaCpgStUM5tovKiOz3Co6qT8Oh3C4YHx6N4qcbPI"
        "HYmK0m1YOBXEtzNJblaP4r+9Pe1/Bl37QWJS8seMaybTmwGyZk2BZcqUYs8jY+O3pSRE3mhPjPUkxzZaSINQsksA/kYtaixiqPG5UN9/sfkyehejlvxy"
        "7jg89JuxAQstyjEEg1Ie4n6GjekRU/OTNevw4GOfnLd7QMxIe2IsMnNHIua6uVyA8TpKA1BoKlroeQV+kPGFNTXVjkfWOplQSybvSqAjLSD3O5vdP1Hz"
        "46wcU9IyZUqRZ3Z+fiGaPs7MTjd7OnokWZKyClQuXju+pAUsNmE51OoCmjm6kECkdk5dSaLQI3ZlCTKXgAXouSZgtMCWO7NAodVIl226XTtr8mnLToVp"
        "aG3arQAhDUBiavKARz5DpuaKY4sbUPp6MWmvJw4nOVxvzhwAj90RnZSe/9oomyBsKVm12sKOwbIypmRE/vRpHSWrVv9kV8mvls6aKCB+6B1mMrWGfdCd"
        "HZQRqqnIvv9cgU0tzcdPa0ORgKuRFsT1YUKVIyc6ztrQj7MhZHPlzf9mwUamIxHNdUQy71w1XtW1wA7tpN0RP+voByHdJJgGXlJaL/9mZL2Rey3xQ++A"
        "vWEbXDUN2FFxEJPn5GHtKxuwcKo8ZjmiraU1CgDSYm18lpKov7xJE+2tk9wdjzww4+mx2fYe8UNHdsRcN9fKMmZEzvVwQPZmhpKl0NX+Bw02+uGmJPhT"
        "1jLRrAm881lkGSrzGUx4FggNDhZshImkwXbqqxWoKN2msJqqa11c0oUrDAvMa4KbkhDJtcrsiX1lfy4wrqckojJzxdjc0b1VcPQR5PbtZBzXpqeW+AAg"
        "7bYJfMDZBMHnW7zYbBKEw6+veDXfdmrL7Zm5d3lYsNEmCD1b+8dWZsOCjWW1/Glc0bLG09J2oYrYvyQrbKCdLSGgUtPoZEHaHdG4d7boU5L5BPu3bpYp"
        "ePpYPKuCZTXTYpsQk9gTp2oaUdXQQzX5maTbAYC9tk0+Rv+BSeJ9Yfw+NdY3yjFEjstVlO7E5Dl56JeaBk/LMeQA2P3PHwoAvM/jSGRAPfLWSlOr2216"
        "5IEZE39+f1Y3qS0536ShprOcrXnXnTU/zyXYyGCKjh5J8gMUTaLIoKDrjLDTc0I18bsSfGr+NA00epItIUfOnNwhkw/0emKBSrOItBCQocELoAey083I"
        "ThcACHJ8jZybohoAYpt6caJQgzy0hKf9ebHMQVlj5Q2ionQbIVEs2enmjuraiLFXXr+s4NGnFhYXFPS1FhfXdSgAV1hQaH6+uMgzfN36awb29U4YlDXW"
        "263XCKsaHUsu4lybkOcbdNpgG8aYaHcgG++dFdCRnZkdeBFsBh5tPpFFxYYbutrsJmC0O8QWdGQW3pmTO/DJmnVy0jCtkTIHiCYqC7DyXV4uKOnZCsve"
        "plPEvBIA4+W6OvI5sZVDs/xM6Wmt9GbEm9RDtDLx31w1Ddi/dTMJF5hzsuErK//Lo61u919tgvBfmrG0AkBRcZEZgPfTzZtuvzPDbe7Wa4RqLlhF6c4A"
        "sJ0LP+p818/xCkuJCdmhYoqIr+8MOE5n71d1bRuq/7o1pM+89eon+GB3hKKnvxaLHM794dWTAcC9s8XJOFHSoEbWQmK1Gd2GnF5rxO8lJiWb+c++t+Jw"
        "vQzAnIw4LHo4HivXu5EJ/3eK/9fLoCObp5avS09YsidukzNS7lu6BMA2c3JsY0cZ4PjlrFmzAfzFJghWSEWqJgCmgoK+5uXPHox8bNKATxc+edfwmOvm"
        "iulbDEVLkjjVGLeLrYwmVLDxZnPTuyKPhCAkAGt+X8r3ikhORpzct99VUyebYFpAIyBjSaWcjDg5VqeWSdPi3CPR9l7uOiVak9V2rPWSmTvc73NJ4QR2"
        "SizRdKe+WiEPmaRnFNgTY01l5a7ap9cdTl14dUrLsm+rfTZB8JG6Hi+AuP+d2++7+5YuMXfrNUIuuyHmZOnrxVhdsk91t6FvJE3RXuwBa7UMdgI2epwS"
        "SzXzFtm5tgzOh6ldLRES7BANtUWuBjRyTNrnCyb0aDNy79lMf5op5Z0PHTagWz6oJU4THxQA7lu6BKWvFyM5ttFTvstrabxi6iO/W/7M8/MSHdbna5wd"
        "1nt63Wf628k3cE+v+xz2xK87uvUaEdBhef/WzSgrdwWAjTjDa7cFPgA67nKpgU0vGUFiSWrmL8+8PFehjs4CixdTo19PSYhT+PqsuUkDbekLx+W/0eGF"
        "+5YuCQiGk1pAwpLTJiCthQZljSXaRgSRQ0yqIKbmwqlx8voNdFXosEGsDDpiXrL+XGbuHlnL7d+6WbR4mhqRnW72LX3hhQkAnu8Y5/WhGLD2mHq5GcXw"
        "2G5rzes/MKkbqLbmxJQkhXj0jaNPlpdBUF3bdkns4LyGQOxcbt6sbTYzQqv6/WIBHfF36OesFg7gsZasJiRajbaS+qWmyeEClsXkb24Am1XSf6Cf8Jg8"
        "J0/KIImUg9MVh8WC5oVT42B3RMs+HanUB6IDgubZ6WZYm3bj+JeipiOg849c3iBvBLkzC/DGop2W7HSz1+6IznrmjsdvffSphR/94s2VFqsPYrKr8z/f"
        "nrYnBia3rn1lQ8BioXd+1owkbOK5Chd05e7NW+R6+2XSoBN3354A9IVOLmStpsVGVhzWZ8GwaXzVVAyM9ptS856QQfbBSwvkZGGxGtvPWNLJxTyhY8Rk"
        "rHA2RN+OBhgBncvpfwY80JHNgYQmjn/5ngJ05BxJiY9YjxcLoLEjJ9se8crfSzJa3e6PF16dYrZK/ht69DINko5totU3b/eyO6Jx39Ilonov3YmUBH96"
        "E73ALqaFxNarEf+UHlWrB3Qk+4YQJXq05sW0OYVCkNFAo0Gmps3YTBM/yBqZkMBxhWtDb/a09XHkwCEcOXBINPF6DENmLoDSnYqWFyQ2qJZ8z1auyMBD"
        "IOhokcxKS3JsoynqzPFbbYLwJIAOa3FxnQkAGk+cbmEdT3qnoGXG/VmyUxpsByfZ/7pSc87jIqLJHZoM4s0FVxMabMHMUjUtV3EYkqnTJg+2IIzeuUwF"
        "Y60V+rkRLcFjq3lsLg0ymmnkmY20NmPjbvT3B8Q1pZganUFCnhVZx2IxayzstW0KMzIng7+R8EJR5Njlu7wK0InZKg0KH/5gQ09z/4FJXrtj67C1T1de"
        "NXn8kP9Y5yU6TM/XOHGwof2YdPE+v33cEGBOZA4Q1fSyx9/VtTvTf7c7ojHZgXPac1Ar8VgZiwndlLRE9VEFm5p2o3d8tXOtrm3DrIkCTtW4UdUQiZSE"
        "OORkBPpFat2DtWJiejsSk+ZHavdmxv3j5Jgsr/KD3aT6D0zCoKyxCpDt3bBYUfKSnW7GwQZldTjv2kgrhrTYJixK7Kmg+ddua6ZipsoK7iMHDiE5thGu"
        "hEiFlquubQsgUNSm+PBAB0AtLcxkT+zrSUmItP1Qt+s6AP+xdozzAsXA0Kv6Wul4htbOV1G6Lay21PSuqJbsymaB0xcdqunFpvOEQ3Hr1W7BwMb6MFrX"
        "43I2o3xXJIAeuv0prddDuQfB3ktia4OyxmJQ1lhkMjmQwUBGXBUCNFGbiWb76pJ62Vwk/AAbVvJvkvXSOlJmkxBShwae0lIROz3TWs7lbJbdIp4VwSoN"
        "5fMVe48ShrSssh72xEMKjQfA9/unlrQBgDWzIRvFeAfXXnttpKumDnYEzyTX69OoPczMAdAdMggnjkduNJ1RwNNuPO2nnZQsarVwqyT09NAnGwy9k7J+"
        "cbhg6iprgV4bBHhkk6bpctpFIWVdNJ0PxKJ8VwPKKvcFsJ562yIue1vMJvGngsXJfVLUWEeyARItR8xKHtDU3AHyN/GZRiIb7yE73YyySsgZK9T6MQHH"
        "TQBgrYyN8wLAd2dsm44c+PJ/7Il9I44cOKTa4JXeDTojdB1ZV/t3/hutvmh4YOPtbizYWFNSj+hhbuXNCM2KnVQ037LkbA3nMbfM3gXrud8V95QmJdSk"
        "W68Rqo19iDZjCYXyUhFoORlxCqCFawove7seZZWkO1ic4t6I9z06rAlN7DOjfyc/i8CN4yZXR3V8pvjdWlRc5AOAouKimsFz+3WTdgEfb1F1xmnnxpty"
        "h8N+4BDKyoMXbnYFi0YTODQzpRXgZu8DL0GYzdLnVbLryTKh7y99jDelvMmcbDsyc0fKrRLuA/DNF/U4fqAcR/dWKYLRBKw5GeiSMA05n8zc4QGsHNsK"
        "gS5QZq2BsnIXXCX7YHdEy/eb1Wbs8yABcvp5qZU7LX3huAJ0SnAoQUcz09W1bTIZ05VyqOqkonjW2up2+xbMTzaPm/Vh678eu/Wz41++dyMAr6flmMWe"
        "GAtwkke1To5HTqiZTWI2wB4kx76H8l1+LdAZYPOyB2iKmnWQ9fhswbLwHX0EHDkAbghBzXTm7d68GBfrhzw081WFL3VN1lhcc/0kdPv5cswB8GXp/+H4"
        "gXIAVQxYormkjVp8TM0n47kaal0AaLDRWSfT8gcrymZ4z4m+l2Il9kmUVSr9ctIFTXnfRNARzUlnuvDiawS852rUsdUmCL6Cgr6WMUPTWqaNTjsCnM4E"
        "4CPMEQ9YREPoaeFNLpq9sWQxRzmGIB5AZo86OaYXaiUAPa2mfJeX+xDpmAsLNh5QSM95vSUv/QcmBZhOev3UoC0ZDjcHbA5ifdkm2B1bxep3icgYmns7"
        "kHu7QvN8smYd7InHFNcYjLonz58uPaI1G/HZ1GrqaNaW1rzZ6WYsfWGfahaKnFdZ7uIGnlnSjQStWaKMpG/RIYTOmpeh+OpiTZ78u++3v3vKN3PubNlP"
        "swLomJ2f/+uhl2/7IwBPdW2bJSfbrlr7xmaZqGk3YrrRRIXdEY2FT94FulcKyZGjk33VzDTebksCpmyiKp1ETS9scm6ZucNlxkwNbNoEknLB0SldWiSJ"
        "WrxKj19Laz22zz6bUR+saSpPWwXra8kDG6vZ6AoJGkg885He9FgtS0DPJjfzFAEds6SPza5flvnWOmaonASTquYFYCqrrHe9saPxKpsgtJICVG9RcRH6"
        "Dbh5A05uWwLAJmk5E5eQGOA/sJa/xqp08v9kR2DGtb8oUrzxvFIYXhdeQMzWLit3cZk8ckPpPDpycyfPyVOAnFcBwPs+rfBJR49hyE73g46llIm5xF4L"
        "KWok4s92r+eYm+paD5X1knbaJn2HMtE2WGPVYP0ged3CiK9Gb1pkfZAW50tfOM5NYGaZb/a5E7aP3YBpE5B8hrZc/KZnfQCQ6ISCrhAaBxWHgYUZ8jV4"
        "q2vbLDFp46ttgtAKwEwKUL3zEh3mx5c9cLBgRl7V1d2/uIG8OSUhUnFywVgrLRaQvE76xOsmQqQ6I3bXpjMUaI3A+oBffjpbemjvIhPNsmYjBZG0SUnX"
        "tgXb6aMcQ+QwCq3hSO4eECkzunRcSm1h06+l5o3AoKwdmOwkmej1qsH7isP1XODZHS7J3ORnuQcTLaDxQEYv+mn5g2XNRGs1rWwUNSnf5eVmu5DNK3dm"
        "AfZv3Yzq2q0yoAJzI/nsY1dW4FfXtrFrz+xyNpuGZSS9Kyk2kxzs9oybYEJxEdrabS+gOzLolgYpTGReK0ZBXut7TRaqv9mqylK2OPfID10r0M6CjY7r"
        "VJRuU2g2HthefH22/NmUhA3ydZCFT++urpqGsHrZ0yanq2aYor8hr8FpsMVNS8x1c3Hf0iHAoiVcbUdvbDzguZxAWeUm2WxLjn1P8snCMx15YGPNWpIx"
        "ctuvjgdoNB4xwyYUBOZSqodaJs8ZiW69RmBQFjCDYnRZTadK3h1uDhr24Fl4OkIInuraNjOAzxc8/ocVAMxFxUVeuk2ed+/e93onJed++NikAbtSEiKH"
        "SVrOzGo5+qJZIJI6uFvGuLHrw2ZuoPZgQ0901NQh5jq/ptDblJTstHSrBzaliXznvbNvlhf6qa9WyBtIv9Q0TaC7auowSIcm4C1Ia9NuuXkN7U/xAMV+"
        "niVd6OY2mbnDUV27VdUfpHMDecDza71opCTsVJSxqPmpeoBGLzSl+XicuzDJgA6e0DFGVmvy+nmmJEQqNg17Yl/MuD9LUU6mBbqu6DMTUJis9A9NLd2S"
        "n21174q0CYIHQIfYJq+7AIjDFTsAnP6hxy3/ALalpyREdlTXtpnJrsSCi0exsyyV2o5gbdot94Y49dUK1QuSF6GUpcDr7sQ6x2RzIH7YmZM75HQ0uyNa"
        "0fKbLhJNSYj0Z5cH0Ty0icWSLnQOH529w3tvMN+EnurCewb0ZxZmRCo6VFUcFvMc2WpsAj5gX8DAQ5JJQ+KPvIRsFmg8UoTXaoFYFbyNKvAe8tlJLTOc"
        "mPjsfdIDKj1Nqti1TIOLCbN4q2vbzL2Hjj69/OW3PwfgAHCw1e2WTEoTfJKWa2x1u3v9bOqCdRUvffzblITIy1MSIn3VtW0meiHTD1pMrPUzloR6d9U0"
        "cMFAgp/9pYqDQVnqGk4ewsfZUcm50F19yfeRG+485sYgOa0o0Cl31dTB6b5GjlmRat/+A5MCUpXUetvzAER/B51nqCe1i+4mJfdQVMwLj1PUoZG2cw/N"
        "fBUup3/AITkWPfyQHIfOFKKbtNIgBFyqi5I+fwJmYj6yz3vhonEK813PPaTNSZ52IwudWCpsV3CxJ8lOxQZMLAAWMDR7raduUY1lZj7rdTmbrVf0sC22"
        "CcIB8qJNEHy86TlXjLv1qu8+emfUCmD7byRq00IWCws6ssBIcJX8jX4/63es3daMpxfXoPRTHwbp6GfK7jzkIZOFw8bVyPs/fn83RmQmy+XvxCekAcSa"
        "MNW1bUDpTn+fQsasIhpXTUvRD4G0pQiFDVNPno2GPdEO3qzwKMcQvPj6bKx9ZYNsdYgS2BYu2PfxJtr4N7/AnjW8fiHkeSx6OB5JFNhYzaZGvATTbuTc"
        "4gdma/r+xASXrYbD/DQtuY+JRtyUBSsvGV26757q2jYrgD2vlpQ8B8AqRQG8JP4WYC0BiHvutTf/9NikATenJERen5IQ6amubbNoAYKAzuUUTRM5ITXb"
        "ruiHIlP5n/rk6lg15z3UXpSsPe1yNsuLkPihZLelE2nZ7yKaTitJW+u8WE3cFeJyNsspcIrdnkogmDwHMpEkpnUpcwp5nbB4GSdqRbc02Nh4F9nx6SA3"
        "qRVT89dYsJFzISx2sGEt11yvntPrPOZGTrYdq0uaFf4aC6LJI8Xw0LLH39XMnmLvmwZZ4nM5mzvGPPTCwt5Vi82ZDdm+fAlsCsCRRpU2QTgOqUZidn7+"
        "suraj9dKgxgDdkHF7iE9qBxq988cILWRprp90bv/rImC1LV2SFDKlSdqjWzY95BEYJezWQoD9IXzmDtsQOnRxv7E1mbVFnvJsY1yuwB24WnNkqMfPp3r"
        "GeUYgtyZQ9B/4Ga8+detMuj8C0UfieE85oY9EQEsJFmQrJlK1oFW5lEwE5IGflJaLzz2hDOo5tcitIgfmpOh3rR44VTRHK8o3aZbs7H+MK0lAXSUVdZb"
        "Y9LGvzRz7uz3AViL8Y6ig3mAhmt1u00QKwV8AD57cdE9p9C8syfty7GRfXYhkZuZkxGnWjW+dlszZk0UZC1HhKkjCkmjqbGnbMzFVVPHLbHRyupXa4vA"
        "02A0yGhqmzaRyspdKAPgcu4L8Atysu1IjlW26uadD00M0TIoaywWJvaVs294/UB48UbiA/GYSPLMWNOR9oHYNcFL+1IjjeiMlNJPfdwiZaKRaP9NTQj5"
        "Q5QAsXLI/4TE2b91sz8s5NQ2udXWGwGbZErueO61N3/ZLSbeUlRcFDAuIABwNkHwtbrlNJ3u9usm3LmrZOtHKQmR3SQQmrQWIi39UtO4NC+RletFtb/2"
        "lQ3S/GRltklno/+85kcVpTuRmTtcdYdV+6xeP0wEzGA5Q4JuExCUfpZ9DIldzAa3Vbeee0+0Hc2m2hP7IkklvshjY9UatrL1anpGcLGUP6/QWCZKyl1c"
        "sBFCjOe/saYrza7aE8WiU9G38ycf0G1C9KwnNc2WFtvkXf+lYHU5m79/ZsPe39sEod0HmIo4x+GOHKYmNx4GcPiuW9MfS8HxP0phAqveRT8iMxkfv79b"
        "9e9rtzUjJ9sOAHInJGUQOXzQ0SQObRaUVdYjO313UPNRT+oPu+D9GTTK3L9QhGbMiP+h5tOJzr72yKkoxxAMCjIrm63CViNDAPVSGtl6YO6ZWuyOfa+4"
        "DhrlrJJg5A7x3+iNgtaobKEwneVDwHbkwCFdzDFrRtLPPzvd7Cvf1cPncta747MfGJ2YlLyjsKDQYiou4o4L0ASPz7fY/HBho/lXv5pX90JBZk1KQuSA"
        "lIRIL8RuzQE0OMlBLCt36SYLHlq2Dy8uHIyV611YONT/OqkI7grQsQ1vynd55biRFjmjBTr6+mjTkddGWy8bGSo5xKtN0+Pf0EBrce7BjoqDsvahtRrN"
        "+rLpWXquR8t85F0P6WWiZ5Oir49HzBCw0XmrNEuqFvfTq9kAYOJQN8p3RXrKKuutYx564ZmZc2fvKCwo7FZUXHRG7XiqgGt1u00mk+BtdbuvBPDltXc+"
        "9eTX//zdaxK4ZNOSDpoSf8LlbEbvoaOlxfCu5o5ITIiUhEjGtByG/j06p+lEBq8BKQnK4Lyo5eJ1ma5aoAsVaOGCjCZdstPNcqdhNr6lB2Q00OiWdCzQ"
        "Fk7VBzRNZjUEsK0u2afbGgjmv+klbYJpN61YW05GHKoa0F5WWR9x3cRf/nHm3NlPFBYURmiBTRNwlFn53aPzFxx/5tnlzu3lpXdW1265U9JyJq0D3zas"
        "Xbfvs3abP4BdUboNmbkjZX/OPz4oPNARP5INvi994Tim5fdUaDoe8aFVWqMHbKEuUjbzw6/txUqEeE4Stx6A0aQIvbuzuzYp6gyWcKy2WFlWT+19dHlR"
        "sL41bMCbF39TKxUiAGM3Aj2mpCKmWhnQcbq9rLI+IiZt/AePLfnDfAARPJIkJJNSAp5XYi7bRo25s2BXyZYMAHH2xFhf/4FJJnIxofb54IFu4VQxQ4X2"
        "5/wOf3jmpaflGDUNRTlqa3XJPpkZy04XZIJDiyjhjVPiBff1UMz0Dk/CBETokUnxico+jp0FmVrNIEv5s+ar0r+ug7VpN07VuFG0sV01ZKNlEgfzcdmU"
        "LAIArfgbbU5qadxQ/DYO2DwS2D5+7rU3f71i9RpLq9vtoZRU+ICjtJ0HgHPutCkvVdduWZSd3uiJTxxpJTsIS09rZQGoybK36/HiwsEo39UgN9kkD1nM"
        "eQwNdIShIm3IM3OHIzNXOeNu2dv1qK6NRk62HdnpjchOF8SpmpxGSSzFT46h1++gNQV9LAKuDgSvVAgFYPRuzpJHdJtCHgDpur1BnGwREmJwNXjlprXB"
        "7gEdHNfbH5OVlujhivIsHhuqBTI1kow3tUcFbN6yynpL76Gjq5e//OZDAJytbrdX75rUzTgWFhTihaIik/u/bxY/NmnAgoMNPbvHS75ccmwjOpCkUN/X"
        "XB8nV3GHwv6Vlbuw8Mm78NDMV7Ho4feQlNYL9sQb4aoZBjQcClnTiaADnMf8RaWT5+TJM5qBericzXhoWTPFxvXglobwqHm15Gxe3h3tf3XIfmbnTUQ1"
        "goItfqUKI7kdsujzjB96RwAhw9bE8Z4Dr3KaLRfSCzbyPtqczWVuEXtObB8VNbCpzcvgJSRTr3vLKuvRe+jo+nHznrzFJgi1oSoV3YATc8EKLc88i1Ot"
        "MaPKXDXbb4tyDPHaAYurZphuylst4538/ZYxwxDlGIKcjDjZz8q96TMMSgCsTcTkCh10QAM8LbGS6VsnT1ahgUcy7EXNp+1/BetyTBYJMWdpc6yzRaC8"
        "mJaa+Uu3KOD5SzTQ6NpDVovQmydNOojPU8kCi8COlkMXesMjethPMvCDJ8FmnAeLt6nNOpTMWV9ZZb0XgPXXi/80PzEpubZk1eqI/OnT2s8K4Cjz0gPg"
        "94+MjR8DwBTlGKJI8O0MjU+XzpCbs7pkH1w1ot8kdm8CUHUyrJABAd7RvUq6mAYevTj0LBKeL5SSEIl+qWlw9BG4QOOBKcB0osDFyzlUAxht+pbv8sod"
        "jdU2BdJ6j/URg2lR/zlEB9wn0sOGF7fTCzaedqPZSd69C6bdeL4bbaGogS0nI46UrkWMeeiFBxOTkt8sLCi0hgq2kAFXVFzkLSjoa/7+1s+rXIuSqvdv"
        "3ZwyKGus157Y16zWvUmvEO1H6uPYBVW+y4uV651S2pPI3ImzwcITus4sO90sTVcRyzp4ffyDLRAabIoQCdPFmo0ZsXQ1vVh4BA7ra7BkCxlwqNX3km02"
        "FCrQ6PNRcw/C1WjsZ2mmkK5j5JmTofptvM1KpfzIU1ZZH9FwxQ2/njl39goA3YLR/12l4XzFxXVmFPdpmjY6rdp5zJ0ySPTjukTIDkaX09AxtbLKfYyv"
        "xe+vqFf81QFASoKybo2dEKOmkXk0MnnghLl1HjsIRx8BzoqDmuUowRhSuyMaL+bbGYAFajAtsob4sDyzUY3VVDu3cBvxqLU7mDVRUExDJXmT5PlrmeC8"
        "sim92k1tsCQFNmvvoaMr33j57ZdtgmBtdbvbbYKAcwE4ADC1ut2m2382du3RvVVjMWWSj9dMJxwZkZmMMyd3BFw4STRdXfJQQOMcf7Y6X9vo3eUIvR/K"
        "AtLsPS+Zr0SO7lX/fjUTh6/BGlBWzmcF2f6MbGcsMo9Nyz/kaTPeeZLjrt0WHtjoouWcjDjcd38cDlWdVI2D9b3uLsV5q2m3UHw3LbBJz9Unvf5D8Zsb"
        "nlj+MroBcHdmjVvD/eA90/NPub94UtfOr9d/i3IMwSdr1gUwf4SWnpY/GKtL9ila3slzwSjKWdnzXd85hbtb07u9HkDxfD96EU/LDwSYqwaqs7LJ5wjh"
        "cfzL92QtQYPNnhiLEZnJquYYm32hdf5qeZV6NBq7wEl3rxbrjSjftUHRVZmWoUxz21DIEq3noAZICewdACKGTf7lkjd2LP4MQAyAJgRJ+ugywLW63SZb"
        "d8GD/6L3lcNvcP7rn21HASSAU0UQDlO0f+tmzWRnMetkH5eap/s00oFcImwZSTiiNfgjWONWdsHmZIDrf5GZ0txr5ICMjpF16zVCJGZeeEjxnYTAcdXU"
        "yQQXTcYEM2V5fo7eqUYsa0uuK330OOSOEIEeP/QOHP/yPWXMS2pCTCwcLVEbhKn1HGntprKheMoq6yN6Dx29o+A3i//yfxvnW3plTDgmEYe+cwI4uUgV"
        "YpHqI2PjT7Y49/SLuW6ut8W5RxfgtBrhHDlwSFeGvlo2OV0MyZpmhAjRegDsotbyi3jxNzJwkq2eVnPq/TPR9AGcBZmaT0N6ddAFp0QL6Mnc54GMZiBD"
        "MR+VlocItPvu7iv76mJctQ4VVIv6ySOjFeBhQwFqswy0Nnj6+uhNWcOUNANwZ+ZOnmkThA4AHqC403xFuCZlRKvb3TE5K309gKHiycCs5siGYmrSTXCC"
        "fYaX+kODmR3ep6bh2Oa1wVg0tbgNT4uTVhPhaFC9IGN9MXauNq9vS7CNjc22CLXMiB6eUlZZj3tn3yz7j3QdWnZ6I9DUqEgupzes+5YuCbhO3nSeUJlJ"
        "NZKNdN2qOAzfmNsnLMmfPm1fYUGhpUil3OacAK6woNBrEwTf07+a9ROX2F9Sl3bTmi1XcRiwS20Xyir9r0128Ol03uKfPCcP9y0dgtLXi2Evd6lOz+wM"
        "m8Zej56BJnppczVzMVgjWrrshLT98+/qfgJJL9DkgRphAA3wp41V17bhljHDZKCRLtnsoqcHsNBAp9O4eGGVUE1JNT+Sed1XVllvyZsw2r385ZXP/WXl"
        "yjSbIOztKiY+XA1nAoDD37n/5TzmnpoaxOfSK2u3NSMlIRKLHo5X0MN0EFhNy90yZpjc9DV3JpCZuwcpr2wIe9GEClAeOPV+ntZkvBbreprI+nf8ngp2"
        "lEcgqS1AAjS1OJ7aNfN827LKerxR+iK69RqBvRsWB4wlJnPM6YXPEiUP/WasKjMZLAygZS6nxTZh/ZeCGlvtrTgM75MPjZsNwGcThCp0oVg78+HMUTd5"
        "PKdeAiBlUUjtEaprXbr8AZ6QSZY881Tt5mYOgKLpq6KtgORXdfWUVbXJLGogZIkc2l9cuGhc0MptXos51ifTY0rxngfJT+0s0OgBGumjxwEAPnhpAdek"
        "pbWbfD8ZoiSU6gi9zKR4zU1qREkHAOu48ePfmTl39uqZc2dbpH6tvvMNOC8AVH7e/sUQU0MHgAi9TCW9GLQmWSpJhrqAVns8JpJXwcxzmLW+S21sEfu+"
        "afmDxfOgFo/cyxLgNj8lZtVqqYsZAW1AoyVObZceX0WtNk0tmVjWLmHkOrJNfnMylA1qB/dzY//WzYpKcp5rQSwQunqBJUroTTRYL8tgG05abBOqGnrw"
        "eAJfWWW9CcCJvN88/mS3mHiLJ30IuhJsYQPumWeX+4qKi7Dt40+OD7kV3jMnd5AuX7pYypQE5cMJZmbOmrg7YEHxgs7+EU/6B9hPdvi7UU0eGY1bxgzD"
        "0b1VSEmIk+lo5zE37O/vVtSKkQdO5m/LWp6i6HnmIG1my7R0TUNIfogedpHdzHglJ6GYvDxShO60zWqLo3uruMF+ujvXyvVu+ViiOdsQlChRq3XTq92q"
        "GgJ9NzrmdkXqhBfGDE37z7xER0RRcVE7ulg6ZVI+8fzvrBUvjfaRBWZP3KPaFk8v08iTlevdUtqPOniOHDjEbTgb7IHQiyUlIRI3T5mENyjtKIKpLuBc"
        "q2vbMOP+LHkxsCYhnZNILxieL0N/v9burDcwz5q6NLnTGb+UTS6gi3EJeMhntK6D+IrkemZNFKT2fQ3ol5qmWqlAtH1n+4lyQjq+ssp6C4C2hU89+c1N"
        "Y8dFVm7f3o7iIlxQgBt361WmLX/PUPCrybGNKOvikyRkCm8h+c3OBm4Zf7Abb3e0yUCyJ8ZKc8bapHYPOzVp9CMHDlGV7nUBbdFp6lqfKRgdMrh4DOPK"
        "9e6QKh5CA5oYS3voN2JPR39Pga0KDarWx5NlCHMy4uT+mwBw28+Xc31XPaak1uZEx904mS9eAJaYtPHF8X36flq5fbuviOqWfN4BR+aCA2g69d3BTwDc"
        "Sk6aZ7bx2kyHKqTkg4CO9kvEaav8YSPBFhYdJFc2BA0eM6TzJY/qJI61zMFwQEZXZ4dCfHQGaAQIpMcnHYoIdq60KSn39JeENSVp8ksP2PTE3TiV3V7J"
        "dzv83Gtv/tUmCN+jE6lbZ03DWTeZTbZioS3pyp6kSMYX5RiCjpo6ebezJ/btsrGu5GaRpGXaHKw4XO+f2uMMaj6oHjsnA5pdeFlwpCTEhdwSnU46pjNc"
        "9G5INLNIQC8Gl/d1OdCIRsjJiMN9S5fIY5FpX1kNWLyNZNZEsW8M6V9DV++T4/P8Nr0t7XgbF9uTlHOfvQCspt6pf7IJwrfzEh3W52ucHRcc4DrGeYFi"
        "IOM6eyQ9zZSWKMcQxeAHOtWI1lahDsVjM0j8r9UHsJfhDNzTCwA9geRQWD9eKIE3ZKOzANMiQ2iTLycjTo6lESCogY3N3GAD7YsejsfBhp5Y9va+ALBp"
        "+W16waZFkvk3ZqV2y043e5e+cNwMoPb1jeWv37luvWXq9Gme53H2xNrZA1x9zfBO0abBYlmhAoVUDwRbWFoPLZjWkcGB5rAXurgB+cdKqc29phdSxdv1"
        "Xfbg1bqHlVWKMbQ3SsdyQaCl2XjajdS5iZkr+wIYyX6paQF+W6hg03OdvDUmxQDNP73jf/4BIKVy+/Zv8sU0xQsPcNZNIjt19PhpuGq+l8cHE7bumy/q"
        "cc31carJysSepwOfvF0+nF081N6Q9GCKhVNFs5QXrwvHD+V1gyIJwMQXZRNpuyo4H2wRsqYjCzTWl9I0IxNjQce2AEjV+Y3yZNTJI/3g44GNaFA6RzIU"
        "n1jvdUvazSdptyNHUhy/tQlC69n03bpMw6k5qBEtuwCMDerEsoPw9GTqdxaAgX+vD6p1/eUc+lPFSJUCvTjo/E61IYlnG2w8H401HWltozZ7O5jQYCOZ"
        "JGqajYCNECR+Uio0/5i3satoNy8Ay3W35m98ZEp+71/8NO771NQ7Tl1UgOvWa4SCxh3E2Y20WiHoSZc628KbUU2E17+RjeWxbfx0T87pIq2l1iyILpQl"
        "zKPdEa0KNJKxo8UOilNp+uL4lyI4CJlFNDZhTDMHEB8OqmAj60Zvq4Rg2k3NImF8t8PX3zPvfw4dLP1vUnKu91ysr06TJv3iLwfwve7PqbUWp02us6Xp"
        "ulYrij5cQOb5OTIL1TYFXvoV3a6ONh8f+f0TXKDpHXZBt2AHdio0DWm9QMxIEmvT0myd8dnU+kzy+q9I2s1q6p36xzFD01okHPguaMApDkLFYcT0pg3Y"
        "d1TAzcwNcDmbcbBBnFNtT4yVdzx2N3qj9EXs37oZy5ZuCotlPJeg1JuidjaBxssrzcmIw6KH/SWKpPqCvOeh34zldujSaz7aE2PR0SNJ8fzZ5/jiwsGy"
        "WUmySLR8tnDT2/QCUuINvEtfOG4B4OxW8N4bBT/5qXn5swc94TYFOi+AO9jQEz9hHsb+k+D6aPTuSKZx0kIoYnvinvNuXl5IEozCJ7/TdXSk/mzynDxM"
        "yxdnf5PBKbzqA7a5LD0xlAVbcmwj4hNHymwfHd7JHAB88Od4kHlvgJj9TxKSadazK8Cmt0tASkIkynd5fQDMpt6pT/4tr08LAGtxsdBxrp5jp1lKAAEz"
        "opNjG7H/ZBL1t33yDjgtCHU7Py9bt4/yYwQZCzS7I1qupia+2KmvVqCidJs8Boz4RIrRSxo9J4Npkf4Dk2SwVZRuQ3Vtm6I9AqlzI92en3799wo/MZTM"
        "/86CjbyH8t1MAI48/vzjH72begcKCwq9RWchZ/Ks+XDcv/UYhqjmnVyWkr25dBMduyMa11wfhzMnd8BVU6eIi/2YgKeV+VFd24bq2jb0vSaLS+HTk0zZ"
        "ZGh6+Ijexc5qt+x0M+Kl7mB0+/TMAf4OXMSEzcmICwAb0WqEjTzbYGO4Ay8A6xWpE15MSs7tKFm1OjJ/+rS2c/lsu9yH490cOp+SmCgdPYYhGbsVBAr9"
        "cCtKd2q2l7sUgBQsXkh3ySLa7GczH0HuhPEKkBFhxwbT2ow17dXmbWuef+5wBdgIa+vXav5Ry/fOvln212gTkq4m6WxQW49Qm5VXuof1T69cuQ5AW96k"
        "iTZMx8UHuECHum/Az6xDfeTAIeTe1AtLX/hW/juJWZGMfT6DWX/BATDcxGweIcSyiXZHtNwXhNeSnNwvHstH7qG1aTeSY0MnHegNkNQGkq7YdOEoOy9v"
        "4aJxCn+NN0IrVNGj3dg1RsgkWrv90OOWJTZBOASx6ZX3XK+VTgPu22924s6r1R9WlGMIUhI2KO3p7MHiTb8pjltd7TzmVlQCTB4Z7c8kX7REk0ghTWLP"
        "hWakzVs9Hb7YRcwSDaQbMRFaS7BAC8Ys0sc52NATybGN4jkcbpZDGnq6qJEZBESrAf7KDZEYgQw2wjCTJGeaGOmMRgsXbFSM1FtWWW+1O6Krnl658m/d"
        "e/ayAPAVFRfpLpy+YEiTyq9c6JjtDwDQwe8t5ScwKrt3gBYgN/5Q1Uk59Yv8vcW5R7F4yAgr+iGyGo+ASdGRmQEFLz5FJ1bztI2ecVV6ZhDQi4TuWkYn"
        "b5OMiJmPL4bnu604urdK7nalVsyqNlmH5zcnx5pls56+TrW6Mf/QyMYArcYSIzwTMpR4Xlf4bWpgk8qBvADQ/eqHHrMJwmmp7d05125douGu6hO4S5JY"
        "nOe7rQAmBfgP1bVtcppPdroZZZV0eUxdwE22XJmlMJ14C5/0xEgfPQ72b7YGlGjwwEdXFIRqGqr1PuH5D/1S0xA/MFsxKnf/1s2wNu1Gda3YtHWyQ3x/"
        "H9NuLHv1E9gdfuqevu5gDV3VFq090Q7guK7FK8+1a9qt0GqAP7ZGs5C8ioLOarVQwMZqN/I+yZT0uJzN1pi08f98/Mn5Jx9/cn68TRCOd3VzoLMKOOlk"
        "O1rd7l6PTRpwO8EFa4oc3VsFTJkkhwbIjRH7lAhS1+HgnbxiLzPhzMkdcvNQ1hQiN1sMrD6BU1+twNpXNshpVaT9GjsRVKvbcEv0cAzu55ZnvJHGRPQu"
        "n5IQib7XjMPgfqKmIfPmgg1cPHNyBwZljcX+rYDLuUk+t4A6spo6OCsOdorooLUcW7TLY0PlhGMpUVmNGCE9J+e82PVaLdTr412HpIF9kh/8Q/qYO5fZ"
        "BGFnYUGhGQDOB9g6reE2ffSfiJSEyGhei7f+A5MUPUbYjsor17u5gW1eu3Pe+GI2ZFBd24b7lk4K9OkWjZMDwfflPqTYxfMLlyCiZZe8QNiZ1jRgbnbs"
        "wCHhG5RVKrsDkwroT9ask3b1OgxSmblGhGgukn1PzLzJDiqX0NmMitKd3NzMUIWl9nnms3+RNgYwkB88LCieGwBVuj+cJGc9QAslBECud+kLxzvsjuiI"
        "H3rc8kz+9Gk7CwsKw57rdl4BR9JgJo8f0vrI2HjSJk8Xa0lrObY1mpq5QOqw2F4ZtP9FbjKJ4bHyyZp1MvBFcC6RmpTuUsxzo8+VBYqYGXNcXhh9rxFN"
        "3TcWLaG0ELnmPUFnZLMmr8vZDFdNZIBmCgYytSx53kIkpVJsiU52uhkHG3rK2Shq5uMtY4YpfDWa6j9bWk0P2OhYJTElAUS0x2Xs/IvYQXmgTRAOnC9T"
        "slOAW7OmwDxlSrHn9RWvZrm/eDICYtGehQeyT9ask5z/DTJLRh44KQ1RNAbiPDTnMbdqihjN+E2mNAf98AgRwy5C0hGYvNeeeAyuGgF2yheliQr63FzO"
        "ZvS9BoqmQ7SWBqDZVIjV/DwWVe9UGy2w0eclkiBxilQwmmUkVeQ88zElIVLWanpr5DoLNr3XzAEbibkdzfx/S/IBtEFqPnM+wRY24KZMKTYD8NSfODjk"
        "MsAa5RjSDk4DoZSESHz8/m7cPGUSMnOHo/qvW2VzhjCKsk922N/jkAXh0b1V/h4eVPY3qzV52oNt20cy5XnAdNU0SF246lQBQ39nTvNOHDkQKy8YOo2K"
        "ZMazvhdvo+gKkPG0WkAcjZOgQBe9EvMxKa0XSj/1yS7BjPuzFHE1XoA93Em0oWo1nu/JgM1XVlnfbndER15751NPjbv1qvqFV6f4nq9xNuECkE75cJ9v"
        "+diUf2vgOCYSGhAZyGZZ49EmDQHXsrfrsXBqHNV2IJDUKKusx6J0M3+BHVa2Dj9y4FAAiNiHWPfNVrQ4+6rkDlbB0xJLtb8TGUH6d+X7+f4Vb2qNHvM5"
        "3LYNan5MdrpZnr9GfDMabARo9Cjjx54QH5Ka+ajmU+oFWzgmshr9z4ANZZX1HrsjOvKHHrcsvuve6esrGyqE52uczefblOws4Npb3W7Ti4vuucdVsxM8"
        "7UY6eNkdW2Wz0p64DfbaNmTC31SIaDrSKpv8LN7IaPm9Bxt6wu5wK4a52x3RCgKAmDfKBxatAAXNAPKYQT+I2M80aC4Q/nH0kRhdJeQ8SNu83JvEjgGH"
        "mFQsOqzhB5oyLYtkthDz8fiX76GCSsMjDDD9fXr8uHAa3aoV1dJgkzaQDgDW1phRy//y2so/Hj9Wl5XRJ/OTCwVsndJwNkHw/e/cfqZsjuahyQbarOw/"
        "MAkpNQ1yoLussh6F4yNQRnywkdGSwx7YSLRMGmWl1X1ZraKcfZ0Mf1QzUYOZRzx/iw056Fl0XQk8euETAJV+2lMmXWiCie6YTAON1zyI1ziIns1NQkDB"
        "wNbZjtK8scVpsU2ISexJfNAOAFa7I3rHc6vXPLpi9RoTgA9xgUnIgPP5FptNpie8rW734DfmXRULwNut1whu85VBWWPlJORP1qyTZ0zTPtr6LwUUjgem"
        "FrUjE80KipwOTK/d1oycbDtyMpRmEW1WkrQxMN2ZCQDIZFBe6wEeYIKZS2rz7ngaTwsonWm1R2JnJAZIp2CRYZAEaHTeI6nA5vU0OfXVigBChJfbeja1"
        "Gs9nC9RqfrBJqVt77n/45dvTo6dFVMbO8hQVF/kuesCtXXvSDMD77lurroY4ZLxD6ziZucNRXbsVH7+/GyMyk5GZOxwVpTtl/y0TzahKiMPCqf4cPQIw"
        "MjCCaJQyZmAjAQI9KimnpkG1cJXuvpsTIoVNtCRJ5ZK/L6NzVH1XAM3atBvlpeL1nPj3cXx7yqwchzWV1miE4ncFlPjwNBrdpo/Wov0HJnU6wB2KZuOZ"
        "kIAca7MC+LwjaUpu2m0TTvkAUz4uPLBxfa/ggNtpbnW7fdMnT7z6hhTz5OG33+kTrhxmps3J/Vs3o1f/FABAd0sLvjtwAFXfnkJs7x6IvjwCXl8bTje1"
        "4soeVpxubkPJtlbcfUd/DHGYULKtFQk9gBtSRW10Q2o0rukXiW+PtuHbo22YPvoymMw2tEsY73WFFe2w4tuj4sLw/NCKG7P7o6rKvxBON7ehHVb0usIK"
        "zw+tqG0S3xcdHYnTzYG77+nmNpxubkN0tFKrNTZ7kJIQicNO8Rjk+/QKe8xeV1jR2OzB6eY2JPQAapuAhB7ax8jJiMO9Ey/H9YMjcKpVwLefV+NInU8m"
        "Qf75bxNqm0Qi5KHpSZhwkwX97SaU7/LiSJ0PH+34L4beOBQPPFaIkeOnw2Jz4MzJHdj3r1exceVq1B5yBZiOp5vbZICnpafih7buOHW8NuxGP+SYPG3G"
        "uwc8sJXv8uLNdSc6AFhPN7d93uOGP/3spZcWnyosKLSM3bnTiwtUQtZw8xIdPpsg+OZOm5IPbDdBpZdfi3OPPJHUnrgNqKzHx+/vxoz7s9B/YBJVgSxq"
        "jNUl+5CTEYeFU/2aj878J9qOFDaS4kpe92MXR8sR8481QfXuwDztFGpZDo9YUevbydNmdBD6xL+Po/dPvAFdwSaPpN/rj6MR1vG+pZMCNBqPeWT7o5Dy"
        "nFA7IYfLQLL+GquhyyrriWb7T3r+n/Pyp09r7MpZ3BcE4FrdbtOC+cm+1mfdlz82aUAyLotElGOISS32FeUQyZP+A5OQkyH6C2QABElZIqCjZ40R0JE5"
        "AuyDIqYn+7Bk01MlnkeTJ+E2dmX9xnDBpubHcdpxS4usAWXlNBDMeI1q6af0z6AIWM+4PwuDssbqAhp9r2mg6QFbZ+h+NRKIJkYosLVDzG7a/fS6w78B"
        "0ITpMF/oYAtHw5mKi+u8y59F/77XZF1r73XIB7GQL0DDuGoa5JxEknVid0SLge4Dh+Q+KFqgIzQ2obDJQyPajscYkvfToGOZVFKdEC5pQYOWtzPr8dVo"
        "EiYn246ycsi+IU3akDgmy5BmDmC1GSht5grQZnqBRuJyZNCknt4jXQm0QK3GB1vvoaO/fPrlt0cDaJO6JvtwEUhIgJvr+DkAYFjqPW2jr9rqGzNR0JzD"
        "vH/rZgzKGosoxxBk5tYBUj4kmy/oX4BK0JHOxaQNOd01OCUhLmAaCjuVxl85zZ8vTveWDDaYg57hlpNtl0kedpFwd+tEZXIAAUj80DsQ1fEZDlWdxGp6"
        "bBYnVEGEJUCINgOAlujh+NnMYRiV3Zs7FyCYRiMZQJPn5EmbYd1Z1Wq8olEeMSKBzSfF2SJi0sa/ufzlN39lE4RGXGQSEuB6TL3cjGJ45y8Yfbf7i52m"
        "jh7DPGrES3VtG/pR3ZdpLVdWWY8clV2fjICiR9nygEcASfscvCJTv1ZThhLYjA6xWaldleYmoCG+katGWfGdkxG4SCi6RUHFu6QBX9Xr39UslyH3g7P4"
        "qN/EFDK6BcOZkzs0y2XY9DHy3f/3V7GyIliepN6KhVDARm9YnOv1SBNKI65InfDYc6+tfM4mCG7f4sVm0xNPeC9ZwPmwzgQA28tLe113mfQSJWQ3tSfG"
        "orrWhaN7q7C/jyCblpm5w4HSnXA5wZ0N7V/YDbIGox8GDTzyN/+uqKwiUGsgS2sQWhNW10YDcHF7MNKaiSx20hqOhDHEcwp2B48HmKHswEo6mEx3NKNB"
        "1i81DZYrsxTNhFhtxvpcvGJOuniXtLBQa0TUlWDTQ/dTJqQHgMXuiD597Z1PLbnr3umrNqxbb211u00mQbiowAaEMC2k1e02CYIAt9vdbcGDU3de3f2L"
        "ayfPyfPGXDfXzHvgb/51q+yfZOaOlE0UAHKpTTBTjGXM2JFOvFgbrfXo1nLB+vuHS6Bo7dRaZipvPBUBGWmQSy96osUAcGvtaJDRn1Wj5eVgOFUvqDaO"
        "KpQavC40IclkUlNEn4GfPvXShpcSk5LXlqxaLeRNmnjGJggeXIRiCvG9vrUb98RWvDT6SE623ZY7s8BHZ5mwc8TIohdZyb6K5qNl5a6Auc96qGYe+NQW"
        "ttrMNd5n9IBRbyMievemCRKlWQqFmckK0WK0P8beZ60KazZLhk3vmpY/GLkzC+TjkIr2cwU2Ht1PET8el7PZAgAxaeNXrFi95kEAuBho/y4zKUtWrbbk"
        "T5/W8UPdrgkpCZHdk2MbFRkm9AQUuoiT+HJAnQw6klNJkyRa4GB9GqLd2PgV22OfHg3F21nptKxFD5tVF79/kSi1Ef1eHphYIaOaiA9H+2AAuBqMBzAt"
        "ip6XjkaDjTCQtFYLBtjOmo8hmJAyMQLg4BWpE36xYnXJvwBYCgsKfRc72EICXMX2+QCAD9a+0j4qWezpx2MoXTV1GJQ1Fv1SD6K6Vqy/Orq3Co4+/niO"
        "tWm3dLP9zKT4j99OjudTTaMWPJt+RI4x2cFfEOS72FCB3eHW9OHY0Afv97LywHo2+pqCgSuYLxZMA9HnT8+jyxwAvPy0sgpAz0TTcMGmNUI5iFaLiEkb"
        "/68Vq9dMwNclrVLYyXMu25FfEIArLq7ztrrdpkcemDESOI6OHsNUzdEW5x44+gjyHDIgGv2OuWFPVN5kQpAQ0LH0O28h8bQKOS4v3FBd26bw67QWCQ+I"
        "0DlMhN0o+qWmwUERRmrAotlEng/GAxebAcOWx7BAy8kQqX7S8uHUVyu4JmRXarUQ6X6PtBZPZc38/SuzHpy7ZMXqNf/FeWrWeqGwlD6bIPgKZuTdIJmN"
        "Jp52AxUGIG0RXM5mScuJvVDIPDHSuMeeKIKFrj5maXta+9HmmJoG9P+u/FkMtMeFdbPsiWJhKrkOYjqzvUtogBFtxQLL2rQ7qAnL803tjmjkZMTJgKY1"
        "IA9o9DSdrjAhQ8nuD8FXs562xG9cV7HvGQBf2AThvwBMrW73IAC1NkFo+VEBrtXtNgndBby9enXfXSW/ujx7ouDTQ7jQKV1shgnxgciDtyfGIgfKbsRq"
        "dD4NQlq7iAvHpWmOEpOOLFb++wK7kPFAxWp15aazOajGYjcMGmBsWcotY4bJ5U3ke9SAxrZHZ8msswE0NV+NF5tkfLWGK1InPL2mpOR5myCgsKAwgioY"
        "/c+FUjh6TllKiTDxLH/yf269zFlSmp1u9iSNX2ThpQ2x4jzmxluvfuLfnbPtqr4Q0U40g6nGDGrR+KGmVmlpSV5rBXbge7gTYHjXSANmRGayDHR6xNPR"
        "vVUBoQ5yP6blD0Zm7kjFBtHi3IOK0m1htdvTAzRezZoK0OS4msRA/mPUmDsX50+fVlVQ0NdSXFznxUWSonW2wwIWiJ25sv93br+y7HSzlwYcay4FPBAq"
        "7kb7HFoZHaQ4kueI6/EbQvG7QhV2DFSoC5cHsL7XZCF3BBTmH9FKdL9HNaDxzEde2EDPeYdbEKtmPlJajeTetmTN/P1Lsx6cuwhA3KPzFxx75tnlHZea"
        "NusM4KwAOuZOm/LadZdtn5Wdbu74yX2bAkICaoAjCyYwO0S529LxKmJ6knheV4yuCje4Ha6oZboAYkt2HsDUQMIG7um8UhZoar5aZ9scdAJohBRBTNr4"
        "j5977c050gQb+HwwmUy45IEWkg83L9GB52uc+KFhXwwuI6QHVMHF+keelmMKH41mA3m9RKprXUiRCJXM3OHIBLhVyGodrtSAGCy4rZb9Hy7Qae3DspY8"
        "gNHmKevP8fwjHtDCAVuomwibhsYDmtRUViZFeg8dfeKnmeOenDl3dvGK1WsAwNrqdntMJuFHA7aQWMpWt9s0KXOwz35TLJdUoMHlPNZHwaDR5iIBHZsZ"
        "HyjRMvAAP80uNoU9FsA20pS5nqk3Wq/rARTvO+jhHTxwqWkw3jXwOlWRBU5T/OdKq9F5o1p+mqTVvGWV+7zS+vpvTNr4dctffnORpNVIELvjXA2yv6hM"
        "ysKCQnNRcZG31e22L3hw6v6ru39hmzwnzxdz3VwTjzChAUb6XvDIhbIw41sEuGzfSD3kRbASnGDnQZ8DTcvTAzx44FJjK3nlMSyYaRCTYDnveypKtwVo"
        "yK42HXUADWWV9V7JT0NM2vgPJt7z6xezRl37vk0QPAUFfa3FxXUd+BFLUA3ng9iTf94vX7dE1VcK2RMFxeKiU7pY0Rovy6tB4+3q/oA4XZjpApvZL8bz"
        "lHGyAK0U6gKjNLkaoMRrq5O7NIcauKZBxkt/UjMbtbRlV5iPvHgaW8EQqNXqzQDMdkf0gV6p973wqyeWvGwThHYAZmnj/lGDTZeGKyjoay4urvNenfz/"
        "EkZftbVm1kTBkjR+kZy0zMuUIAFtxc6qoX30sJGhVFXzKH9yPlqAVPNJWU2q55rUslqCNTUl2lNNm51t85HHfqr5aRxS5Ez66HFfPLT0b+NtgtAAwFSy"
        "arU5f/o0DwzRp+HIpNNQhQe6YCwXr5CULIKAQDi0qrN5DXtINypXpxqwhmKq8YL3tA9Eix6QnSs/TSfQ5E7HEinyeWbu5Fl5kyZ+bRMEX2FBobWouKjD"
        "AFuYpMm3B/+O0VfFK15jxzl1VuhCUnqh8AiKYIyjdruErjtnrcA8W6bDauB+qWmK4HZXAi0cf00nIUJSskwQOx03XXn9L14ufGzBQpsg+DDdP7DTgFcY"
        "gOsY5wWKKZdO8h20epmEo+XYxUhaLagtnnCYyK4UtTHFanPZaKJFzSfTIl1CTckKZ/KOFtAoPw3wZ4r88enX3nzeJgiuR59ajHmJDvPzNU7vjyGAfdYA"
        "Z8IkAEX4xZsrTXh3obV8lxeZPerkFnhqhIkeP0cv+AgA9Zh4wcICnRV2IKSa9qKD91pJzqGQIeGYtXqBJrajE7T8NC8BWkSfgaW3Tnz49zPnzv6UxNQA"
        "dDxf4/QakOokaUK1Voh9bNKAPTnZ9r7JsY3epPGLzOwuTJMmPNKisxMyu1L0MHm8FC41QoZXRRAKyIjZSO4hb7M6G0ALotEUuY+9h44+2tZum/1qScm/"
        "yIbd6nZ7DI3WhRpOEAS8fbfNnAecBnAQQF8APp5mszbtBukjyJtko3f4w7kQvcnLdHkPwGc52USAUEDGajS9QAuFdWQ1vk5CxAMxnmaxO6LrknJ/Wzrr"
        "wbkP2wShGYC55O67TfnvvPOjDF6fVQ1HAbNj2ui0khsHfH93drrZA8AaP/QO1fouXqk/z587X+Cjwc87LzqwrhZGCNVUVPPP9MTuQgUbL4iuE2heiEWf"
        "VgC4InXC7/6ycuX/2gThFHBp9BW54AEnlU547ro1fdKo5ON/lwBnAfx5lcG6RdGgs0T14ca0goEgXHAGI24IuEKpkessyLTM785oNDXTUQfQfBLQLHZH"
        "NFpjRq0dNebOZ/OnT9slvc3c6nb7DPPxHACOZHQXFhTGWg+tqZo1UYiXWrmZSOYBW73MWzRamu5ciR7N1dUgEzeL8IAWLuBC8NFkoEmEyOZbJz78xsy5"
        "s9eSW+YDvCbAANo5NCllynfM0AHvjB/uvSs73ewp3+W1qBEiaouHBR0vJzJcAKmJnswStYTsrgRZKERIZ8mQUE3H3kNHN/80c9yjd907/TUphkaSjA3m"
        "8TwBzvpcjdMzJz9/0tDLt63NTjd3HGzoadWzU/O6V7EMn15gdI3/1rdLgKUFMOLThuKbdQXQguQ7orq2zetyNvvgZx6PXRl/1aO/emLJBzZBqJf8NKuR"
        "93ieAdfqdpsWXp1iWvZtdffHJg2oSkmITMpON3vLd3nNesBGLwxW29Eaj8Suzia4wgUay8yyBbfnC2Ra2kwNaHZH9DdSgvHHNkE4SAiRZ55dbgSuLwTA"
        "kTUFoGN2fv70y5o+fmvWRMELwEIP/QtlIXUF+IIBqitErZJdy1TUA7LO+GZEdMbRQGm0r66Mv+ovv3piySopkx8w4mkXLOBk0I0ZOuDv44d7JxHGcuV6"
        "d9gLSi1bgwUgMZW0Ks5DBaMamMSYImSNpfxM+EPkw9VmWtNlWJABUGSGSED79qeZ45bfde/0VTZB8LS63VdvWLf+YOX27e2Gn3ZhA84EwFdYUHjF8fLX"
        "Dix6OJ6sSPPK9W453akzNLYW+NTBFch80gwq+Z0HoFABFQq4usJcDAYywhCz2gwATlviV0958LEdd907/RWbILQBQMndd1vyXn/dYhOEMwYELmDAkX6B"
        "rW53ik0Qqgcl2O8cEtO4YdHD8R3SQzYR0HWpH6ZS+9aZMptQ5Wx2u+qMyVhd2+ZzOZtJXNQkabOO9o5ufx815s4/U3E0zEt0WJ+vcXpgUPwXHeAGPTp/"
        "weFnnl3ufeSBGR/YTm25ZdZEQR7uIfkOXX6yobS1CwWM4VRIdwZcWulWIZiMBDRmymys+GnmuH/ede/0j2yC8AXRdiWrViNv0kSDDLlITUq0ut3xj85f"
        "UJ9xww2ReZMmRj3ywIznbKe2TJ81USDDzuV5012t7fQCkpfJHwqY2Ek8nRWtVKtgIDtV04iqhh4kduaDcursiZi08RtvyM59Z+bc2R9Rr5sLCwph+GeX"
        "AOB4Mm10Wklvy4mpLOgAnBVtd6GLWsu9ME1GL+Obtdod0V/+0OOW5/6ycuVHNkH4ngKZ6Zlnl/tsF+F0UANwQUxLQO7qZQLgmTttSont1JapE4e6z8Qk"
        "9owgx/8xAE+rp2UwkCWl9cKhqpOsyUi0GV3RsS8mbXzZqDF3FuVPn7aPet16qcxPMwCnA3zSj1fZBOHfc6dNeetU1cZ7cjLivNLCMnN27XNqal6ImkwF"
        "ZCSvkQZZY0za+E+TEod8WPjYI6ttgtBKnl1hQaHZCFT/SE3KVrf7MkEQWkyAb3Z+fsH3e//xfE5GnCU73eyVvsfEcf4vaK3HIzeC+Y8sWaOVz6gBsu93"
        "nxC233Lzbe/8ZeXKTSTlCgDmJTosnnETjBzHHzvgKG3XH0Dju2+tuufrf/7uAQBDpKx1OXRQvssrlfT3DAt8vG5Y4fYxURuNpaftOW82uc54mSJDXxIf"
        "gC9j0sZ/5IvKeemVV35Bn5V5XqLD/FyN02Nk7RuAU/h1rW53zIZ169vyJk0cAMD5y1mz7v5+7z+W2R3RvSTgybV0BGj0IiWvAcEnlp5L0ZpBzjMXAeBQ"
        "1UkCMp+0mZAqavoD316ROuGd7j17bXzm2eVVNkEgfpgZYg2akXJlAE4XABNtglDT6nZftmHd+kF/+9Njd1/uOf6g3RF9eUpCpDc73WySdnXzqZpGWdup"
        "mF5cCQeQ4WayEKE1cxCfLKAEhpLvYtLGf9YtJv7PRcVFFczfjLxGA3Chazry86GDpT2SknP/axMEd8mq1Rlb3v/n0lNVG28lJpk9MdaTHNtIYkshnY8W"
        "GLtCtMBFNBh9HlTWh0nSUOR6fL2Hjj7V3tHtnzdk5753173TK2yCcIIGWWFBofeF4iKfYTIagOs08MiiAtABADWHDk7/9+drn50964mTmQNwDQGfZG76"
        "OGaXbjlVI+ZPqmnMUN9Hay4NwoPQ94r72Xvo6D1t7ba/3zR23Id5kybulxrwELFIgWmDyjcA13Xi84nfIbVoMBcVF/kA+Frd7t4A6p98/Nn8xmN7J5+q"
        "2vgzAAJFRngB+CT/yBQuAPUKq7VYLcoEoH0cMxF2R3Rra8yoD70+69qbxo6ryZ8+bTvzFkvJ3Xcj7/XXDSrfANy5EzICi9GI9qKnn7u9bNMrAy/3HJ8M"
        "ke2kCQvyfi8Akz0x1kxVNod9HVQvFh/xC6VCTS91bB7g2wGc2H1C+GfuLbc2dIuJL33m2eWHbIJQx9xfS2FBoVfK/jBAZgDu/AgxOaW2a4DI4JG/dfvz"
        "4iU5ta6a2yOsZ6478eWHCQAS1UgQl7PZY3dEe5nr4mpEBkz0+61ByJYWl7P5i5i08Q1en3XNTWPH7cubNPEbTg99y7xEB4Y/+QyMQRaGXDCA42k9AGYJ"
        "fB0MOHs8On9B0n8bTyabTR0/K/34o15jR2f/7MSXH/qka4jqglNoAeC1O6LNAFz//KK9bFb+BEvfq274t/OI6ZNfPz7te9KKgAWYdO4eAEaysCEXB+DY"
        "8yq5+25z/jvvEFPPy9GQvTasW+/Lnz7N9MzvluUdOLQ3GgC2bN2Cjna3fezo7HHSZ8k1evv3tpoP1Jm3f1r+2dcAzKOyRnli+/7ENCilT8vMubPXA/BK"
        "wfsfSLEmLfMSHZbna5yAmFblJf6osYwMuaSk1e02FRYUmuclOiyS6Wc+B19rnZfosEKk7M2tbrfZeBKGXKoaThcIBUGASTRHLQBg2fQPSBrIR/uErAlI"
        "rnteogOecRMgmYIe6bgAAIPgMMQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBDDDHEEEMMMcQQQwwxxBBD"
        "DDHEEEMMMcSQS0n+P5YFAmWdDqNxAAAAAElFTkSuQmCC"
    ),
    "trollface_third.png": (
        "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"
    ),
    "trollface_fourth.png": (
        "iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAYAAAA+VemSAACe9UlEQVR4nOx9e1yU1br/d2YA3aUgM0KZF2ZwRsxUZBy1knQo0NopKrdsYzJuIU8dw0Sq"
        "fY5uRPPSORkqsuuUmpCZbgVU1PyVKINiWhsGQY1dM8KgFdp2BgarrQKzfn+8s5bv3LiJ1/h+PuujzLzzXta7nvXcnwfoRje60Y1udKMb3ehGN7rRjW50"
        "oxvd6EY3utGNbnSjG93oRje60Y1udKMb3ejGXQHBnb6Bbvx+EBsbK6qrqxP069eP1NXVCUpKSto6ntTV1QkumQZa9VXbrbfpNu8pdBNw+9BV80S66DxO"
        "95OWliYAIHT8/MiRI2iDUAiAli66r9sFAQARuHu3ouvm9Z5DNwEDwrS0NCxfvpz9Dft5IQCau+pauLHwBAAQGhpKSkpK3HEXPlHS37SAW7T3HB5O0Ix/"
        "hkBsqPmByGUDBF9//Q0MNefcHi+XDSbjxo0VHBag+mJO9tlWTi0A4AGAPJygIRdzsn83RP17JGCR7V8BOEJokxj2/EPXy3Tue5Hj54afLwEA5P4PtXnR"
        "OS+8AKFAYOnQnbrB9+d/8Dn2VQmeejIUx74qEQAgRw8V+gcHj/ojbITeYDajj1iM9//2PmqqXRKJEIA1QBog9fLw+GO14ZwVLjh4V8Knj88QADCbTBBL"
        "JDCbTG3+xnbcNZHIo5b3cWMLsK1FgHO4fu0YgAYXP+W/L8qp7zv8HghYEBoaKiopKXEpKj6coAk6+vYKBMnlQgDWwbLAacaa6gG4wfFEvj7eMV7evj0B"
        "gLT8BgBo+vWa04U8vHycPhP2FMJ61Wr17iUSQiA8cq66+gJsxAMAgwIG/ftXQj75+fyFZtv1CLjF1zJYFvi4saZ6tO1YDwDWQQGDBnoKhU83/tJi9e4l"
        "Ev766y/wEjyIK1frewLwcrx+e4jkNoK+A/qcbYEe5+H4hVgiAQCYTaZGgVePr2C1fjcoYJDI7+FBR78+Vpjr4vx8aYYS8z3Ppe93AnZeKF491IEBAdEA"
        "ZOcv/NDDt3evcKlMBl1p6R25wS5GUyd+41J3vkXo7HUInImtBRxhO61hkcijbIA04HB1bW0hAKEAgh/I9auuRHAPtFMKu1txvxIwM3AoHn2xL7FWTDPW"
        "VMuFhES2tDQPa+O3LXBeLCLejt/pm1KqVFZliJJ4+3ij0dIIXbmObhwiuH4Xru6lNYJr831OHD8Jng9wp/T28YFIKESL9dauX4GPBE89rYYEVpggtPu3"
        "LRRri1H/SxOELb/im+M6eD4ggFodBoulAT4+fWCxNJDy8nKrQa+n8ySE8/xcFYk8vrcKBNpmkC9w/dpRcJsdFaOouH3P6c73GwHTxd0CAIGKIVlXGhri"
        "zSZTHx4BOr4kO91WLJFAKpNBGaKEt483AqRS1BqNaLQ0QqstgkGvv6kbVKpUUIYoMSJ4JEaHhKB3Hx8o5HL2vdlkhplYYTx1CtUNV1wu8lqjEeVnDPDt"
        "5dnh6/fuOxCSXtz6VqvV6N3HB1caLPBWjoJc6KTm3xYYrO00gpvruX/FvuwjuVCEJYuXIGPNGv6Rrb5jAP8SiTyutADrW5qu7QXA16+ZenMv4H4i4BsT"
        "79UjwkMo+gu5fu1pAHho0CPNEx4Pxa6dO512Z7lCAalUCrVajZGjghEeHg69wYDKUxXYvXs3jEYjjDU1dpxXLJFALBbD28cHUqkUALhzhKkh7uMLVzA3"
        "1KNgTwHM9WY0Wiww19ej0WJh55gxYwZGjgq2I+bbAbph8InC/cH1gNi3VUI3m8zs/2KJGLrSMpgb6tln1j5iBEoH2f/I4drfWTlNwNjYaPe51Nvb7m/L"
        "zz9j7MP9sWXTJqx9bUFrd05FcCucpZ0mgVePL0hLy96+AYOyLxn0zbB3Ud3VuB8ImLpmmgD4eXj1fIM0N71h+64FDm6hgP5yKIbJUH/FiqV/XQhF0DAE"
        "DHwEAKArLUP+7t3I3rLFiWDVYWFQhoRg5KhgKEOUEEvETjfiuFgtDTeMzj59fGBpsDgRqd5gQK3RCG2Rln02KGQ0Jj45GkGPDHLJnSgB8b+TC0UwWFvs"
        "/uXD8VhHtIcL0t/l5ebBXF+Plge9IPTqDUG9CUfLTwMAKo4esT+vC4lFrlDY/R2sCoVvL09IpQHoJQ2EVBqAQGWw3THfXPwRp09XQSYUAZYrqDX/jInK"
        "MQiUDoK8b1/oDQYsen0hCg8davM5cIOgqcEQACDw6rG/xWpdRq5fpQaRu54b3+sELIJNXBZ49QzyJCS3paV5ODi/LXX2A+CIUKlUYmRwMBotjXjt9WRG"
        "SHqDAcuWpiM/N5edWDXxSUyf9DzUajWkMpkdwepKy1BjNKJYWwxzvRmVFRUwm83t1o8pB1erwyCVBthtCmaTGaU1Rlwx1sCnjw+kT4fZEZzh8mUYT51C"
        "gFTaKrfWGwwQ9OkDed++dp9TQm0vEfOPM5vMKCoqwoLk5Ftu3aaqxnDbHE1SKQGASUe1RiOMxloYjTXw9vGBMiQEw9VhEDaYsTXnE+zaubO9l+IHg3gA"
        "aBZ49chrsVqXk+tXvwW3hu5a3fheJWB63+QhuULxoECwqPbcuTliicTLbDI1w43bwWwyITwiAvPTl7EF8VHubrwe/yIAjjNETpuG5yf/EU9MeJL9li7c"
        "Ym1xl+jB7iCWSKCZMwfqMDWUIdz9GWtqnDaQwsJCVJ6q4O6t/gbHF/v6YuQojnNRUdWRgDuDwsJC5Hyah6IvC1olXP9+gRjQX4xGiwVSqRQjg4Mh9r0h"
        "Hvf28YFMJkXlqQoYjbV8I57dHLi6Bn03CXM0dhvXdz+dx9EDX6JYq4W2qAhSmQxRM2YAACoqKjpCyABHqALb+MHq4RlOrl/9zvbdXcmN70UCphNs9fDq"
        "+QFpbkoQSyR/sL10q1yhEEqlUiZKTXj8CfxkugyDXo/wiAgU7N8HgONky9LeRt7mDyGWSJCSkoLn/xSLoEc4/cxsMkNXrkP2lmxoi4puGccJj4jAyOBg"
        "1NZfga+QwGisgbm+HmJfX0ilMvY3AMgUIzB9SjhkUimUqtEwm8yMa7sS6TsLqscWFRUhJzvbSSx1NPRR3d9xowFucEwAdvfNnUcMvcEAbZEW+/buhU6n"
        "s5vn8IgISKUyJuXQjVOuUECj0SBSk2C3QekNBuRsyWYqUGLSywDgcqNoAy3gOO8lgVePyuarv8UD+Bd4Et/dgnuNgBnn9ej5wCfk+rWXcCM4QLQ+K0tQ"
        "azSiYO9eGPR6pC9Oh8cDnliyeDEelsnxxf49UMjlMFy+DM206dCVliL6xTlIW7LIblfPWPMe8nfvvmW+YbFEAg8vH/xcV80+kysUGBkczIxhAVIprjRY"
        "mJW4rLwcG9avt+P+SpUKUqkUYl8xRgSPBADIZFIoQ5Qw1ZtditB6gwFXGiy4DAGTQswmM4w1NSgrL8fR8tOoOHrESSUIj4hghj5KrP+69gsufPs9amqM"
        "sHr1wrEv97Pj+QTn+OzqsDBm/AuQSpGUlMjuzZGYKeeNmjGDzUX+7t2orKjA9Su/YMiIEYicHomBw4bA4O+PIKEnYK5H9tp1zDIdFRODRoulvfoxBQt3"
        "FYk8zl5vuhYO4CLuMiK+1whYZCVEKB8S9HHtuXOzAFwH4AlAkJKaioFDhmPhyxoAwNZt22Cur8eC+fMhlkhQdLSYEenI4SNg0Ouxdds2RMdEM6NPYWEh"
        "VmRk4pvDX7Z5I0qVqs1jhA96wfrrdaeNIKC/HGPHK+Hj08eJu1BQLuOog/MXudFobFWcp3o/wPl86SJ+WCbHlPCn0TsgELWnSt0SG8At/qXL0iHxFUNX"
        "roO1jxiTVEp2H6crKt2Kwu4CZKjUEWIzCirkcifdnBoU6WZM70UzR4Pw8HAAnBRV+60B1d+dQcuDXhAEPYYBwY8hqOEXQOyLal0Fli9Ihq60lM0n3Zhb"
        "C+WkNgqbb7kZgKdI5PHt9aZrz+AuI+J7iYA9ADTLg4bF1ei/+zs4q7MncEN3pDvu1m3bAAAvxcdDqVKhoKCAEcCs+FkoOa5D8bFCBAx8BIbLlyHv2xcZ"
        "a97DksWL7S5IF6FMMQKDHgtCWMhwWPuIAZ9emKQY0j7/pbketd8aAADV353B6YpKpkfzDWsBUimuWCwoP2NARWmJHUHJFQqo1WGInB7JFi8FtXzX1Bhx"
        "xWJBdnZ2h3V0eh8+fQcgb/sWds3XFiyAOkyNfXv2QldeDs0cDZQhShQVFaG8vByVFRUwGo0AwJ4nKiqa+biVqtHQlZYBAGqMRs7artXaicr0OmEzpnPu"
        "JJuvly855OXmYffu3czIqFSpsCUn247wqYurWlcBWR9vCAJl3HmEIsyKn4X83Fx2rdMVldi08aNW56OgoAD5u3fTNdUslkg8LA2Ws8mL1o9f885/WHCX"
        "6MT3CgELQkNDPY4eO9bS06tnhS2ays4FQLE+KwtJSYl4oEdPAMCKlSsBcAaUKxYLMjIyUHn6NMQSMeO8L726gOnCSqUSUqkME9UTnbhDe2Gsb8DP135F"
        "Me9nE2136uPvjx6WX1GtK8ex3ftQcfQIIzilSoWoGTMQYBMvy8vLuQXP42KUk2jmzLHTN/UGA/bt2csIWKlSQa1WQx2mRvaWbDsLO72WVCrFRLUaYl9f"
        "FGuLkZ+fBwBYumwZ1GFqaIu0WLZ0KaKiovHa68nQFmmdxHhHhEdEwGg0wmw2c5KDzYilVquZEUvcxxc1RiPbBHQ6HaQyGWYvXISXY2Ywl5BUKrPzFhQW"
        "FiInfx/yNn8IAFi44h3MWfQaAM7N9KdHBiF5fjK02iLka4tgFAggJQTyvn0ZEVPi1Gq1yMjIaJULr8/MRHl5OTLWrIFYImk2m0weAq8eO5qv/vbyQ3LF"
        "vy8Z9Hc8DPNeIWAPAM0izx6voqX5b+AmzSmckBqp+C+L/4IoN6aBC6S6BknJKThfXY3/WvQ6AtQTEDh4MAAumKCH5VcAgJQQu2CDah1nlDEaa1Fbww/i"
        "4RAwajikvmLU9nkALQFSlF/8GQBQdpzjRqPHjwYARPbjiNlaU4uju/Pt/M+UmEeOCkZNjRHFWi1KjuuY3kwJsNFiQeWZc+xzygWl0gDoyssZ4dKAFWoZ"
        "prosj8sgNi4OCxYsQI3RyFxFVJpZlp7OCHfhf72NnI/WQSqTIUGjgbHhF0j79MIVC6efUrRmQ+CL0TKpFFqtFvm7d0MWPBpLl/8VAJA4+8/45vCXTIzn"
        "E3LmuvUoPHQISpUK2Xv3sPdTfe4cpg8fyX1+rBjG+gbuehIJU50Sk16GRpOA9PT0NvXixKSX4e3jTeeoCYCnwMPz3ebrV9/EXSBK3wsELABAEuYmhn66"
        "ZUshbDovXNx7xdkzkPiKMXLECDtCKCgoQFFREa7++yoe6vcQAqRSlP3rJ7y/NB1PRURizpxZgNgXXzSYUPnrVQDAyAd7QurtjSChJ4xHilB5qgJarbZN"
        "vZOPh2VyDAoMxPiwp0FkgWgKkKLx4T4o++3fQPm3AIChLVZMHPcYwgIVgLkexlOnoC3S4tNt+YwowyMiMHXaNIh9fVFrNNoRJgA70VUdpkbOlmxUVnCb"
        "DP2dCUII6k3M3cLf2OQKBTLWrQUApC9Nh660FGOfmYTX/pxgJ7pGxcQgZeFCXLZNvSs3FVVJqPW5t1QGWR9v1BqNsDRYUF5eDqPR6CQRJCa9jInqiag1"
        "GmGur0fUjBlQqkZj48ZNWDB/PgAgJTXVzo1UWFgIzewEAGBSFQAkz0/Gpo0fITHpZWRmZaLQZEK4RIK83Dy8FB+P8IgIpKeno8ZoxNq1a9s0VsoVCv47"
        "vw7AS+Dh+Xbz9atpuMNEfHcTMCECCASCzTt2PPS/S9O/Nej13nBDvCmpqVixcgX0BgPCJkxkboTMrEzoDQZk796P4j25LGxxw8c5+O/1a9AkG4SCup/x"
        "69F/oN8QBaSDH4bU2xuep77Fp7l5OPJJNgAwH7JP3wEI6C9Bo6XRpR4lVygwNWEuztfU2InHAEdoYdNjAHUESNM1CDx7oMrahCEXLkLmI0SAbDCeDhnF"
        "iKKwsBAFewqQn5/HCC48IgLPx8aj74OeqDUamVGGPit3r2bmosnZku0khvMRHhGB5NcXoGBPAXuehf/1NqT9fbFs6VJ23YX/9TY0s2agpqERteU6AMC2"
        "3QUwfmuAdy9OP/D28YFMMQIB/SU3XmGfvjhdfBjePj6YqFYDAK5YLOjtw6VeOm4oVN+fqJ6I4KjpkAtF+LJUh7cX/RVlJw9DLJHgf/7nfxH/UjwAbsN4"
        "e2EKSkqO4f8dOgSFXA5daRkiIyNhNpkQPXce0lJeg0IuZ5sB1YWpnh46PtTt/LgxdjUB8Gzx8JiJ69f+DpuE6PIEv3N4AIA8aFiUSCgiIqGoyfav3fDz"
        "8yeVtefItaYm8sabbxGRUEQ+276DXGtqImeqqkhQ0FAiEopIenoaOVNVRWLjXiD7vj1LNNXnyIgzZ8iIM2fIrBNfkH3fniWZm7aSuPhEMmbsOBKX9CpZ"
        "vfodcqaqip0rdfEqMnnys+yc9PpxSa+SrPc/IB9/nE2y3v+AfH74GFn7xXGyYftOkvq3LDJz5otkwIAB7DdBQUPJC4veJCn795OsqtNkw/adJC7pVdJ/"
        "cBCZPPlZsnr1O+RCdTW51tRErjU1kQMHD5K4pFftfj9v3ivkwMGDJOv9D8iYseNIUNBQ9tyrV79jd48ioYiEPRlKDhw8yD6fN+8VkvX+B6RffwV7js+2"
        "7yDz5r1i97t5814hdRcvkXnzXiFjxo5jn8fGveB0bHtHUNBQMnnysyQ27gWS9f4H5MSJk2T16nfszh8Xn0gOHDzI5oB/rbj4RHKmqorUXbxErjU1kdRV"
        "75KgoKHsb7oOREIR6T84iHy2fQf7LHXVu+RaUxPx8/MnJ06cJGeqqjp6/y0ioajFy7NHJW+t3hFmeDdzYCEAIvDqOUrY3LQfwMNww32pO+j/PvsEKXNe"
        "viE6FRYiQMpF/uw5chRb31+PWfGzMHthCv7fz1dR1CKEaIgvRj/wB/x69B/A57tZ6ptKOgilxvMY7N8PALB352d2nJCPh2VyvDgzAdL+vjh2rgbVZ6/j"
        "/NnLAID+EWMgExIMUPSDl4njXBfOn2cRQg/L5Bj/9DMYNGoYHpvyHH75qgyrUhfb6brKECUmqiciLCwMYonYTgcEwHS63n18sGFdJiKnR8LSYGFBGGKJ"
        "BDLFKPj2FsLbxwf5ubno90g/PP/8VMZ1wyMi8N66tdiwLpN9NvrxZ/D6a3+GTCqFRqNhlmZ1WBhmzJgBc3099u3d21H/qhPoOamLiEoOBXv3ovGXFowc"
        "PhjePj74dNundiK1WCJB9ic5kI4aBYh9cSS/AGe0RcjMyoTZZLZTpQDOoDl1+jTmH6fGy4qzZ1B5qgIvxcfb3Vf0i3OYVd4FWgCIBF49Pmm++tt/gBOt"
        "b7sofbcSsACA4PvzP/xh/Gjl92aT6RE4GK6oaEOJleo3UTEx3Pe+YpjrzeylU90wJCQEJgjxzwcewtHGS3hU6IlBDT+CePhD6g00i/vjB/NFnP6kGKbe"
        "1zAocDBKNq9xa62kRg6tVoufTA1ovj6Gfdf3IQkuX+J+FzqZ8xtf+bEaI5UPo1Zf4aQH+vcLxH8tS8Mzz4djS34etmdswMUaA/ueWsmnTpsGdZiaBXjk"
        "ZGdDV1qKFStXIiV1ETPihUdEIEGjuWFNv3wZmenLsWnjR2z+aBRaSuoiO2v807M1mP1GCmryd2PB/PnMqAYAzb81oeSb4zdNuK4gVyjg7eMDtc06rtVq"
        "2XWUKhVKjpfYicgAZ41+LD4Kf3pkEJYsXsKCQz7M2cHiAijoHBkucxusemQwzCYTSo4fR8batXbvJCU1FZUVFa09JwEgsHp4PkquX/0n7oBr6a4k4NjY"
        "WNGuXbtaxoaFLqg58/06s8l0HbxyMfy45uycHADAgEceQWxcHHK2fmK3S1OfYeWpChRri/HYmCdR29IDRV/XoSmsH172AGpralFT7YkaqwAyIUHJF6Xo"
        "+5AEQ0fJcLLoAzsicoR/v0B49xJx4ZA/cD5M397cPlN46BA8vR6Fj98odjwlaqH1a7tILD6iX5yDl+YnAT69UFxUhOKcrS51NL6l2tJgQbG2GNPi/oQt"
        "H2ZhwoxovBzDEdx3P52HyOsBkIYGu6QNGhgh7uNrt3hjFi5C6DNhyM7eg1O5m9ixnYhmumnwNxoamZW3ZzfjmPTzqJgYTNBo8HTIKGzZ8ikmhk3AJJUS"
        "kVOmMimEEvye418xA9xfVr+NzPSVEEskWLpsmZ2bjLrsHOMDeGgBIBB4eG5ovn71ddwBXfhuJGABAKSlpfX64IP/OwtggNlkInBwG/GjqyKnTAUAZOfk"
        "wFRvxpwEDcvhpcatl15dgJDAQTAREWqqPVHyRSlmzp+Kiz+XodnyCP55qgYP9BXgtLYQjzwyF782cS6fyz9u7/AD8CJ52Gf+/QJRb+oBH79ReNBzNORB"
        "Nag4Y3Z7/tGPP4PI19LwoFgA+cA+MBrP42h2Nr4qO+VyQ+GHYkbNmOEUl/xR7m4sT54Ps8kEpUqFhQsXQiaVIjs7B0ZjDc4YajD+8acwSBqIJu/BqDMU"
        "M3+rI+imdauSOtyBT8zZn+Q4+bejYmLwVMpCyLx7Y9WCVGzMzAAABD823O73Kamp0Ly9DAAX6EHdSzTNkaoKlEmY6+vdGblohtJvVg/PEeT61RrcZi58"
        "NxKwB4DmoKHDsg3ff5cAbkdzyi6KionBp9s+RfL8ZOTn50FbWWHnsAe4RZ2vLcIR7TGc0Rahd0Agjhg4Ri4TcnNvbKyCsPEPOH/2Mi7/uJ1xTMu/TgEA"
        "mq5XdenD8Tly34ck6O9HcLToiMvrjH78GUyIjwQR90OArD9k3r0Byy+4YqxhmVHu0hjFEglGDB2N0U+MtHPbyBUK/OcbizG4f19oZifAy9sX1xvrETYp"
        "Ei1/GI7zPxghk/yCY9pilxKCXKFA4y+cqudOgrgdoBv4nASNHXGNiklEenoy2/A+3fYpq9jB59b08wCpFDKZFJrZCW7VpKiYGCd1h4cWAC0tHh4zcP3a"
        "57jNbqW7jYCpkcpXJBTpAAzkfW4HuUKBYFUoKkpLkLdnNxRyOdPhKBaueAcTp/8RW9f+DcRiQsAoFSPga5XVeCzoVzSYH8DpyoO3fTFSQqYi9YP4B2p/"
        "dOas1PU08OlnQHr3QFigDJMUQ6ArLcM/zupx4fszKNi7FxqNBgDsdEZH+PcLROSUcEilAXZi4cIV7wC/NuHgF5ecxPvRjz+DC7U17G8Hn+gdBXWBpby+"
        "0IlrZmRvQYW2GCYI8XLMDEilw/BzXTUz1inkcnxZqsOfI6ey6Du+W5Aa1iaq1RgdEoLQ8ePd3QYX0ivy+M+Wpmvv4zaL0U6c7Q6Dq2fl1SMYzc2D4Cbi"
        "CuDEHINej/VZWVDI5Vj87joU7clFYtLLzFocMGo4zJcv4tjnh/Dkc/+JmmqgQctJN782mVB8CQCuwmLqcbuej6HpehUs/wIu/1hlE91c76Vmkwl5mz/E"
        "w0cOY/zTz6A2ZAQGTAxj3ILW+srIyIA6LAwAR2TiQTKEhowE6dMXAaOGA5YreFr9FEhDA8ImTIRSpYKutBSjH38G+LUJxWU/o78fwWNBPZG3/Qax1l7w"
        "x+W6w+x+7hbiBcA2qox1axH5/BQ2J4WHDiFFMwcF+/chY8170BsM2LQpE5HPTwEAZtCbpFKi8vRpjBwxwmnTM5tMkNrqoanD1K1tXAIAEAgED9v+visT"
        "/285rIQIAAg279jh6+fnf14kFFlt/rZWfXLz5r1CVq9+h4iEIrJ69TvkWlMTeSLiOdJ/cBDJOXqYpP4tiwQODCLRievIQwNnkcDAtSQwcC15aOAs8tDA"
        "WaRnz+Gd8mPeitGz53Dmk21thD0ZSt548y07nynf5xsb9wLzi5+tqyOZJ0+Sfd+eJfu+PUv8/PyZ/7ZffwXze499chLpPzjI7vrtuZe7YWS9/wFbA/wR"
        "G/cCOVNVxXzjdL6y3v+A+dbP1tWx3/r5+RM/P3+yevU7ZOyTk8jkyc+SMWPHMR97Kz5h4uXZw4C7T6K9rfBMS0sTyoOGvWKbGJdBG+5GXNKr5FpTE/ls"
        "+w7i5+dPxowdR9Z+cZzMnPkiefqp5xjR8gn4biJeOsY+OalVwhkwYAA5ceIkudbUxBbV5MnPskCTrPc/YAR9pqqK7DvxNdlSe44s2p7HFiJdsEFBQ8kT"
        "Ec+xc/v5+d/x5+/MoAEZlEBj415g382b9wo5U1VFDhw8SE6cOEn8/PxZwMfZujryxptvsTVDf8MnYBok08r1KQF3rbHkHoQnAHh49Vwj4rjv9fa+wDFj"
        "x7FoKfry4pJeJWu/OE6eiHiOjH1y0l3NefmjZ8/hZOyTk1rb8Ymfnz/pPziIiIQclzxx4iSpu3iJRSHRhTpm7DjyRMRzJDbuBbYp0PP2668gqaveJXHx"
        "iWy+2liod/UIChrKnk17uNguamv16ndYRBddH/Tvs3V1LOLO8ZyTJz9LDhw8SGLjXiCTJz/bGgFbvTx71ADoZVvLvy9O/HCCRgQA8bM1L/n5+f9bJBQ1"
        "t/fF+fn5M+Llh8+lrnqXRCeuI4+pFjDxmRLu3Uq8/NEaF/bz8yf9+iuYyEc/HzBgAHnjzbdY2COfYB3PHZf0Kkld9S7x8/Mn8+a90toCvedGUNBQcuLE"
        "Sac1QqUTSpzXmppI3cVLjHs7zlW//gpypqqKhXy2cs0mkVBE4NUj0rakb5tt6Xa11GgVF3OyiZUQj7J/fPOW2WTq2ZHfSmUyKORyFBYWImPNGqSkpiI8"
        "IgJH9x9C+RGCf5ul+OepGgCA5V+n0HS9qstdQ7cCbVnFV769GGGTIpnVNTwiAg8+2AsZa9YgMjKSldhZmp7OotMAzhK98u3FGOQ/AOdruHkxGmtue4DG"
        "rYJYIoHZbEZZeTmriWU2mRA9fQZkMik7TqfTQVdaBvXEiagxGpFgCxXl4+e6anj1eAAjg4NZeio1GrrAHakjfccJODY2VgTAOicxaZjp8mU5bhTfbhdm"
        "L1wEAEh5fSGUKhU0by/DyOBg9PEZij5qIX5tKsPlSyZGvPcDzCYT3nrrTRR9WQAAGBkcjPT0dGSsW4uomBjoSktRa6uUUV5eDpHwxmtevDgFB//fQaxd"
        "zeXchk2KROUZ9y0+7zWIxWIsWbMaq99bh9deT7YLzgBu1KQ2m0zIzs6BRqPBS/HxSEpKdFkmSf/dt1CHqQFwzCIqKtr1dSUSQfzMF70AIC0trasfyy3u"
        "OAHv2rVLAEBw7OjRGLPJ1AMdMMOLJRKEjRoBw2Wu6uTshYvwcf4B1P5owqPq8bhWyXGx+4V4xRIJVqxcCblCAbPJxNwmGWvWIHT8eEQ+P8VlwAHtfUQX"
        "KDvmt+toMD9wRwMyuhpmsxm//fQvXKzhUkjXZOew566pMbJiegCwaeNHXMy1LVc4fVk6AI7I/fsFAgAqT1XYlfj19rHvDoEblWHqYl9LPgkA6cuW3bZA"
        "jjtKwDbXUYuVEF9PoXCh7eN2GwDUYWFQyOXIXruOK0Ea/BguHDmMQdJAFO766r7jvACgKy93EvWoaLdi5UqER0QAALK3cFk0jZZGVrcqasYMWL16YfTj"
        "z0CpUmGQNBANln/e1vu/1TCbTDD9wm1Yx4uOwFhvZlKaK+Tv3g3NnDko1hYjPDyc2xzNZgwM4GpqmevrIZaI2aYJwFGMJgAElgaLafoY5U8AIBQIbpsv"
        "+I4ScD/FEBEAMmToY+MNen0v3GiF0iroBCpDQgBwJUxHRE6B0Xge5ywtqLn0AB7oK2DhkHQ3vddhNplccli6sFJSF6H+ir0aZq7nSsYC3GK98P0ZhIwY"
        "DJliBGr1FSg7edjpfPc6rly+gMSkl2E4VQbtKT3g0xvhERG4YnHur043OqORm6Ol6ekwm0xsXgr27gUARE6bBoArnk8rfdogAGBtaWl+JGFuogyA4OEE"
        "zW2jqztJwIJLBr3VSojg6q+N6WhFdJYrFIiKiWGiEA1oj9QkwGwyw2dQIMKiYwDLFQz2EaHGyjHxputV8JVcQ/0diLS6HRBLJMxAJZVxHKNGfwoA8NfV"
        "70GuUHBF68RcUoOutBQZa9Zg08aPQJqutBbfe09Dqy1C774DYTaZIMM1lBwuwoI3F3PVS3Q6u2PNJhO0Wi3M9fXQGwyIjol2qQuH2JiFrrwcI4Pt+jYJ"
        "wNltxMeOHn0LAJGfM9y2No93koCFAKxDhj4WWfdTnRKtGK9eW7AAn277FFtyshn3TUlJgbxvXxQVFeGpp9UAgM8+3oJBMhlkQoLT2kL49wuEVTjuvhKh"
        "+SgoKEDKQk7zkEqlXIlZGzce3L8vvH18cLT8NMxms93vwiMiMMOW23s/wqDXoxf+DQA4f/Y7NEsG4Ny1XwDATgym6oautJQrDniqAnm5eUiwxZXTc5lN"
        "ZtayRltUxKqG8iACYK09d242gEElJSVNuE20dScJmCwlRHi++txfwauC7wi5QsEq92uLtOwF9Pbx4RZsfT2k0gBYa2pxvroaYSHDUfJFKZquV8EqHAeh"
        "9Wt4ej0KT69Hb9dz3RaER0TA3FDPguwnqtUoKy8HwM2ZwKsXdKWlyNv8oVOWjbm+Hus2fHzb7/l2QiT0QlRMDIq+LIDM1se7kSdCS2UyJL9+oyUptSvk"
        "ZGc7idrpS7nC9lQPLtZqHfVgunb/EDR0WPb353/wA5iN576ECGi71hV1wr/x5ltk8uRnnUL9Jk9+9kZNpMWryJmqKjJz5otEJBQ5BW7cC8EbHRmOQRz0"
        "M5FQRN548y2S9f4HLGxy3rxXWo3suh/H2CcnkcxNW9l88GujiYQiVj+M/5vPDx9zG7AxZuy49sSGX/Pz8yfjn30uBQBCQ0M73oG9g7jtHDgtLU0IAP+V"
        "uf4Ri/nyZtvHLkXn8IgIKJVKZKxZg8JDh+zEn6iYGLy3bi3EEjFmxc/C2tV/xYply7Fr5048LJPjMak917nfxGi+G0mpUiElNZXpuuowNU5XVMLbxwe6"
        "8nKWNyxXKJCSmnoH7/r2wbe3EOdrLgDgDFGVpyqgVoex70cGB8Onj4/9bx7whNjXdZM4XWlpe9xtQrPJZP36SNHQ2NhYUUlJyS23Rt92Al6+fLkIQMvf"
        "N/xtgdlk6gNbWRL+MeuzsqBUqfDeurV4z1av2BEpCxdCIZdzCf22KJldO3fCv18gHg97BWeNEmaFvt+RviwdCXM0TNfNXLceBfsLoSsthdFohEajYRVC"
        "qNX1fscZA2dVFkskMOj1zJrcGiQP9YNUGnAzl/UAYPX18U7K3bsvFG6KUXQlbjcBewBoEnj1fKr23LkF4B7Q7h6UKhWSkhKhVqsxJ0GDOQkap5NERUVD"
        "qRqNvNw8loS9PjMTJcePQzpMDmvf6/Dw+gcLm7zfuK8jsrdkc201P8lBYtLLMNfXo/m6BeEREZApRiA7OxvePj5c9co5c5jx5n5xr7lCLw8B8KAnk1J8"
        "fPrYEae2qAjADZekXKFAwMBHoLPZERzRSgilI4Rmk4nIAgb9dfOOHQMAWKnUeStwOxP6uWR9wLu/f991dT/V9YAL7musqcGs+FlOHfP4RdXSl6VDbzBg"
        "QXIy+96njw9ONrbguu8gCL17grT8dnue6i4AbdwVIJVionoiAM5fyTUR42KcaY8oo/FGK5jk+XNbK9h2T8NsNkMiaIF/v0Am+qptheWBG9ZoqUwGs8kE"
        "g14PXWmZWxG6A/2hhQCaa8+de2b/rrxXAfz3kSNHPHCL4qRvFwcWABBaCfEa+uiwwrqf6pRiiYQ2UbYDDVZwjDbKzMxEwf59nK4nEaPyVIXTpP5gvojA"
        "P3J6zqXzP92yh7lbccViwUvx8YicHomRwcHMXw4ASxYvxpLFi7Fp40cwGo2IiomB6Rcriw2+30DXRuQUrpujxdLAWsLQOdEWae2IWqvVdtXlBQCsBwoK"
        "/pj6l//zLCkpseIWpRjeLgL2ANA8ZOhjqfrvvhsDoNlsMnXI2a1JSMDGjZvQaGkEABRri9l3YokE0lGjcP5aEwb27QVr49WuvPe7GolJLyM8IgIGvZ4t"
        "QM3sBNawzBXnoF0J167+611VIqerUX7GgMjpXIZfeXk5hA2cjYDOScHevSxRAeCkE5rF5Qi5QsHi0NsBEQDS0tIcXPfTyWkASGho6C0J7rgdIrQIQJM8"
        "aFhqjf67FeCKgHX4uoWHDqHw0CGmv/ERNj0GEPtiUA9PqANlKP5k383f9T2AFStXQq1WI3kB58+kKYH8PkqOMBqN0Ol09036YGuoKC2BxcaBzWYztEVa"
        "u+8Nej20RVq7ele0Haoj+BtkO0EAkBMnvpoOILekpKSDd393QAQA454KX2TzkzWJuGobnfbv0URsmrBNk7XP1tWRFxa9aVd14X4f/D5Qjj2KYuNeYMnq"
        "tIfQmaoqcuLESfL54WMkdfGqe7aETkdGR55x3rxX7HzDXTA/VpFQ9OtDckWwLaijyyXeWyZCh4aGegCwJsxNDP3hpwtrYOslg3bqAuERES5jUnU6HfJy"
        "89jfS5ctg0IuR2b6cpDGX7rm5u8R0AIG0THRLBgf4OYuMzMTkZGRCB0/HmETJmLkiBEIfmw4khcswN6dnyF6ytNIy8y6g3d/e9AB4xPrP0XhkLRgB35s"
        "fiuwAnhgYB/fjbcqQ+mWEHBaWprQ5sQm27Z9lnaxxkDQSrgkRVRMDLZu24aS48eRoNGg0WJBYtLL2LptGxMHU1JSsCw9nYUQ0ioLmzZ+BF/h76+iZ0hI"
        "CAoLC5lITNvNZG/ZAl1pKdeFYM4cqMPCWBDHpo0fIXT8eBzb/yXWZ2Vh7DOT7uQj3DWQSaUw1d+IG29NzaisqLALzXQDIQBrua5sSMLcxCC0Uib5rgH1"
        "eVkJEXh49dxgEyVarXE1Zuw4VmSM1iASCW+UiaWtJefNe8VJRKa/o9UGV69+53chGtLxxptv2YUIHjh4kM0fVTdoaCWdyw3bd7Kysv0HB5HUxavumRKy"
        "t3J8tn2HU3ilSMitzzfefIscOHjQqZxvO0aTSCgigYohm2xi9N1Wi/0GKPF+f/4H+UMDZ1XYHqDV2s5vvPkWW1j8onSUeOsuXiIff5zNiPPEiZN2Bdg+"
        "276D1F285DI2+PcwaJ9d+uy0GqWfnz95+qnnmB584sRJ1mN49ep3yGfbd5DPDx8jcfGJ5ImI50hc0qv3Rbw4LdJH/6Zz0Z7fTp78rEsCpkUT6ai7eMmp"
        "FG0ro0kkFBGPng/QxOu7k4BtxCv6/vwPQ56IeO4H/s27W3j8Jtx0VwsKGmrX1JkuPjppBw4eZARLj6cv6UxVld0mcL+P2LgX7MrI0mqM/MD9s9eusibg"
        "mZu2ktTFq0hs3Ats3j4/fIxEJ65jlTspEdzpZ7uZweeQHUnkCAoa6tIAShuuHzh4kBGzYxnaNuasWSQUNcfP1vwZYPahuwoCelOBiiEHbDd9nT8xjiU9"
        "6UTwdzzaCZ4SLz2GchH+Lug40UFBQ1m1/Tu9gG7HoHN4tq6O+Pn5k8CBQeRMVZVdl4EN23eS/H9fIRmXfiTrf7tC1v/G/T/j0o9k37dn2eJe8D9/J8o/"
        "r2cE/HsYfIKjUkx7fkeP5UuCNGOOr744jBbbb43fn/+hN9w0qu8MumonEJaUlDR7ePX8W+25c38EF+PMUqleW7AA+2zB5LQzHAAkz09mzab/uvo9zEuY"
        "aXfSfXv2Mj+nrrQU4RERrLk1NSAoVSpIpVLk5+YiLzfPzop4v0IskSA9nctRTU5O5lpmrkzBvj17kbVpCxKTXsaUBfMhFEvw888/o7IFKPtX/Y0TlH+L"
        "oS1W/PG/U1F++hw8G88BePCOPc+tAG3xOjI4GI0WC4xGI2uAxm9Nmpj0MiKnRyJ9abrT76UyGRotFrtgF9qTS61WQyqVsc9p4EzB/n34MGcH/vbuSv7v"
        "BLbfip96OqwF7TDo3k5Qzrvatts08Xe4rPc/YDrJmLHjGIeln9HdjM9d+X5e+rvPtu8gZ6qqnPydVNym1/w95L1So5+jvjZm7Dg2f2evXSUHLl5k3FdT"
        "fY5oqs+REWfOcGPrTpJ58iQJChpK4uITyYrtJWTB//z9vjBm0VYrfGmO5gbTdin0WHciNu2RRFU4x+Ooqse3PYiEN9SauouXHLlxs0gougqvHmpwxHvb"
        "yu60BgEAPCRXBIiEot9sN8kCNWLjXrBbZI7tT+gxWe9/wPrX0IVJiZFvPeVbpPmL1pGofw+DWkb5i4e1C7l2lY38f19h4jOfiDXV50hW1WmyYftOMi7s"
        "Ka4R3OJVd/y5umJQIqKMYN68V5wIzXEuKTHShmb846ihldph6PrNev8DO0bjeP0zVVX88zSLhCLi5dmDxgB3iTvpZtm4h5UQoVePP6whzU2vwSH/seLs"
        "GdaAueT4ca6MSXIyK6amVKmgDFHCXG92yj4CuLzgpKREFBYWQtzHF0rVaPZdYWEhCvYUwFxvhraoyM5hT8UfN13V70skJr2MzKxMu88MVq488XfWJgDA"
        "BQKUX/yZfe99sQHzRj+Gos1bsGzpUqegB0+vR++JVEy7UEiJBOszuXnIyc5G4aFDkCsUUKvDIJUGwFxfj9ofTfDtxWl4UmkARo4KhriPL9ZmbUKN/jSi"
        "ZsyAZs4c6Mp10BZpkbFmDZQqFUqO3wiHjJwyFYWHDuGHn37Crv1fYuHLGnZ9s8nE3sfGjZuwYP58+rNmACKZIijC8N23h9EFzcA7TcChoaGeJSUlTfGz"
        "NYu+PPj5/5hNphYAXvT7rdu2oby8HBlr1qDgwH5YGixYYNPXxBIJUlJS8KBff2z9KIsRGs0S4VfeoInoANiLeO31ZCjkcnYveoMBtUYjCvYUYETwSKjD"
        "1KzdSmud1+8nbN22DdExrrsG8An5gi3WhRJy7AMPwmo2Yfpw5yB+uUKBxl9a7vrC7wUH9iN9abrThq1UqaBWqxESEgJzfT2rdUUJ9h9n9RBe/wUymRSW"
        "Bguzn4gl9imFeoMBcxI0EPv6omA/F2evKy1D6PjxCI+IQMH+fViyeAnTgynSF6fjzbS/YOTwEXQNtwAQjYpJPPqPv/+fWigQ0BTbOwJPECIQefb4b5uI"
        "wKzOTz/1HBPvDhw8aGdyp9ZTvmhNu8DRmF5XtZ7eePMt5kQfM3acS73Z1bgf4qJp572goKFu3RV815u7wRer6Th77SoZHTfP7bXjkl696+0K/Pvz8/Mn"
        "cfGJTC1rzxpp75g37xW7eaaqG41ZcGWBdlzrIqGoyc/Pn8TP1qQCN+9S6iwHpr8jAwYM+Kbup7oxuBHrzMSIFStXwmisZVUz5AoFtMXFMNWbEfzYcMgV"
        "CixNT2ecg1qlATCL87KlSwEA2Z/ksGwSrVbLrNAjg4Mh9hXDXG/GRLWaVbA0m8zIy89nomErHdbvSsgVCvwxPg6BqicQJpNC0KcPAKBCW4xibTHy82/E"
        "g4vFYmSsW8vUDLPJ7MRFKCg3ZjDXQz2SK5nqKKmMfWYS/nv9GizX/BlSqRQlx3V3JTdWqlRI0GgQGDQcgx7payeduYLZZIap3ozKUxV2n/v08YGlwQKZ"
        "VGqnrtH5pGuKv8bUEydyJXsO7Ed4eDhCx4faSQJRMTHIzMzEyBEj6Py2ABD1e6TfifMXLqiFAkEL7gAXFgHAQ3LFMJFQ9KvI1iOVv/NMnvysXVAFtQzS"
        "Tuk0iIBaqR27zdOwtY4GFaxe/Q4Lx+SHwPFbbt7Nw8/Pnwu6OHmSZJ48SbbUniMHLl4kZ69dZVb4uouXSNb7H5CZM19kuzsNYmmvZHL22lXWH3fM2HF2"
        "llnKefed+Jps+PwgiV6VSRZ9uJOkLl5Fxjz7+l0TsdXe5627eImtJxrE0ta56dpxPD/fsu2YFUczvvhrln7OowWrSCiy+vn5tyTMTVTYwitvu0vJAwBE"
        "nj3eoGKB4yJ0JBZqTaYdz2nZ0658oUFBQ+2I3tULOHHi5F0rEtLgi30nviaZJ08STfU5sqX2HBN1+YuHRl/Nm/cKWb36HbJ69Tuk7uIllkbYEdEw5+hh"
        "cqaqyul9Hbh4kaTs30+SvyojI7buJCO27iTKP68nyj+vJ2Oeff2Wz4W74Ap3rkf+oBsaDTOlTOHAwYOsH3B778OVJ4Q/6OZHrc+O7j0qzvM+uy4Siqzy"
        "oGEpNnq65eVnGWjfl4fkiuEiznXkxH0d45L5Zn3aSPlWhOvRZAf+5uAYmkl3Ub50QIPY73QIIXWbbfj8IIuYopzScRPad+JrEpf0KiNYuki+r67tEAHT"
        "MFa+X37evFdI/8FBJP/fV0jyV2V2/uNh+cfIiK07SWz2DhKX9GqnCNNxA+UnomS9/wEjNL6flT8/rT0PjYZy9zs6Nx1taE79x+44MbW1pK5618n2Qtcl"
        "75otIqHIOmDAgLN7/qEbCEDQ2cJ3nWHdHlZC8Oijj31i+P67F9FG6UyxRIKio8VQyOXMctcW5AoFMtatRU2NkW+CbxNiiQQFBQVMD8zesgUZGRkwm0yI"
        "iomBZo4G4eHh7Pi83DwsSE7G+sxMRMdEQ1daBq1Wi+zs7DumL6/bth3S4McgFEsg9e0DudDZ368rLUON0QhzfT2SkhJb1Xnbgt5gQPBjwwFwumQvD09M"
        "mjoFvX18EKCeAL2kDyp/vVGiqOy3fwPl3wIAInwfgOzKb1iePN+lpV+pUjlFMoVHRNjsFlzli94+PhD7+kImlUKr1UJXXo7KCk43NZvN7LxRMTFYuizd"
        "rX5L9dMF8+ezd115qgK9fXyQlJSIjRs3gdpTuOM75pmgXQulMhnS1mdikso+V5ivD5ccPw5zQz0in5/Cnrlg/z5krHmPX0SwWSyReEx67o+vbs3Z8n8T"
        "nnpKVFJS0tyhm+oo6C6xt/DEQ0FBQ2mWUasVNvi7VnsTDSjHdJUZ0p4dft68V1wGjYiEN8RquoPSa/CzoqjD/nbrzHHxiUwvdcV5HcW2jorK7sYbb77F"
        "spMox6L34SoQhI64bbvJvm/PuuVmfn7+RHu4mM0lFVsddcS25oWfVuqO61KuTnVXRynjZtUmx0wl/j3R90Dj8On88QNtaFUUh8AOa9DQYUds5HVb8oRF"
        "ACDw6vmUjXCdxGfHQTOOXEWsOA5+hlJniNdx8bjTc/j5x/yJpmIcnzBup1jdHlcQXZA017crR93FS0ycpp85RnVRgs649CPZUnuOnKmqstskxz45ifTr"
        "r2Dz5qiv0rI+1C34xptvMR2eZvzwkwRaI156bf474me1TZ78rMuWPJ0dNGqQb2Oh80bXDF1LdA7pxtGKGP3d9+d/EAMQ3I5eSp5LlxIhL1H/elsPTQmy"
        "LaNBUNBQO654OwxNjmmL9JrUgNKZe6D6XHt+S/VN+vztJTTqW+9qAqbnbouzn712lZMS6uoYIfEXOSVoPuFQX39r53bM5qFrx92xt3NzpbYbGpfPj/V3"
        "vDf67ulmReei7uIlFpNNibhffwVJmJv4FADExsbe0vhoAQBYCRH26684b7sBl9yXn6vbGjelE0L/7ypZ4VYPR1GIWnfpYnTc3Wks7OTJz7LFGhv3Apk3"
        "7xVmgPls+442jST0ePr8/EQEmhZIjTqOHOyz7Tva7S7qyDhx4qSdwdFxfF9d65QkQImYvxG1VuGDbo50UJei48bmjnjvBncgzQ+mz0MZgaNaRt8p3dBo"
        "kzU+AYuEIqvAq+fjNhq7dQTMa0oWKBKKGmzE60TAcfGJbNFT4nDHfc9UVTn5ze7EcNSZDhw8yERJWsmC7qqtcQW+CNXay6cvnL8Q3QTA2/2uqyOLHAe1"
        "3jvOBRV5+w8OYkTKr5jCX7RUtKd2hNb0Yz5B083K3TNSS/vd4gKkmzZ9BrqROVq56fzR46iawiNgIvDq+eQtJ+DUv/yfBwBkZGa9FjgwiIhcVNsIChpq"
        "tyhpKparCWiLO9/uwTd80RdB/Yj0JfD1mdWr32E6HK0U4m6jouVK6WZAFys/xJTu1nUXL7ldpH5+/m1uIDdLwCKhiHxfXWtH0I6hivT/M2e+yH7Lfxa+"
        "VHPixEmyevU7bEHzjYh83bE1qcCx7tfdMuLiE9k7d5RcqEGLbmj0uAMHD/JphBLwmFtOwJt37BDZCHi6n5//dZGLQnV0wfMJ1J24Q1/y3RSrzK+7RRcW"
        "X5yli6m1czjqfVTUpeKp47F8vZtfgWT16nfc5ql2lfXZcdBFR32wbT0nNQZS6yp/A6eiMY0JoMPdtWm0FN3gHKPz7tbRms5Ovztx4iTbHOmGzydgedCw"
        "5245AVMRevOOHQEioahe5EKEzty0lS06SqDudk4XZvW7ZtDkCT6hUAML1Un5HJXvLqDWT3pc1vsftLpJ0cUqEnK7uKNu62oRt6an3syg+hnVTR03JMc5"
        "Sl31rp1k8tn2HSw01tV750dDUQlm9ep32h3eeCdGW/nmtJwRfT7+fFJCpeGv/DmwzWuTSCgiM6JjdwDAQ3LFrauVlZaWRkXo/7DpQk4idOamrXbJ5Y7h"
        "eXT066+w2/Hv1kFDPikh08VKuQ8/tpYaXlzV+qIv2tGyTV0LjmIzXxJwt7BvhRXa3ftyNegmQjcoV9Fu9wIHbWvw4/fbc7yjVZpKHvwKHTxdnpac3WEj"
        "s9tCwH9+RDqQXZyOsU9OIvtOfM0WKxWJHBcxXZBx8Yl37a7rOPhGG/6ipbqtK8MLrQRBrc1UFKfczVHcokaajsToxsa90OWGrfa8k9auS9UMRwv+vTra"
        "kiRdrRX+fLhKq01dvIoSMy05m9NZAu4Mxbt0Ns+Y+jT6gssWF4vFEEvETs2klEoljEYjACBv++3vFM/vFdte0A7vSxYvRnZ2NiJtRfVkMg07ptZoRK3R"
        "CEvDjUr9Pn18WGc8ADhyvBRGYy2mTpuGKxYL1q5di7Vr16LRYoFUKkWCRoOkpEQkJSVCV1qGsvJynK6ohFQagN4+PnBMi6RtWI1GI7bkZLeZQtdeePv4"
        "tHlMysKFTgUVtEVa7Nu719aT+PYWUEhMehlabZFdyKZYIoGHl89Npz+a67ligCODg9sVXmvQ61FYWMhCdtVhaq6oxZ4C1rv5vLGazrMQAMj1axNDQ0P7"
        "lpSUmMDRV9e3GOFx4LmuODDfXD72yUnkWpOzAet2++/45UJpOuPdzPUdOb3jTk4zYxx/156Mma7gwI6uLCpV3E5OS4vS8z/Lev8DJ+Mitf7yn4dKBh25"
        "HvUOuJp3V+9BJLS3UVDdlxZ0FAm5ghe2dclsSAKvnrTEZYdCKjsVf9n067VWv/ft7XxasUTCktDb0RTqpkB7uebt2c0aOIdNikRZebndLpqSmoqomJhb"
        "ei8dAeX0oeNDUVhYCLPJDLPJjMgpU5GxZg3MJpNTcodcocDSZcuwYf169rvOQldaBqlUykobOcJcX49aoxG60jIkz09G2ISJWLJ48W3juGKJBFOnT3Mq"
        "Hbxv716EhISw3r1KlQpGoxHJ85PR+EsL+21KSgqWLkvv0DXb0f+I9Wim81BZUQGzyWy7rhhRMTHQlZbCVG+GXKHAjz/XOJ6ihVy/2qmm1l0WQF15qgK9"
        "+3Di1wjVBACAVlvEvjebTCwrqOR4icvetV0Fbx8fpKQugkIuZz1dp08JR052NiNYpUqFqBkz2vWCbjd0paXQzE5AZGQkIiMjW22yJZVKkZSUiMozXDG2"
        "7C3ZNoJ/jy0idzCbzNCVlrHj8nfvbvO+Ip+fgsjISGza+NFtF5XNJhOuNNi/r6iYGKjVasikUrxm65Ms9vWFVCqFrlyH0PFc1pBSqYRYIoZCLu/ytbfk"
        "rTfw3rq17G+DXg9duY79rQwJAcCpWmp1GAx6PVMlYasRrXj0xUdsf3coHrozBGzl/0F3a115OZvcsFDuhs1m5wUk9uXS3hx1rXZ2Pm8XKNflw6ePD5dq"
        "aJvM9GXp0Gg00Ol08O8XCIAj6oID+53v2Q1HupUwm0zQlZa2WVlTp9MheX4ydKVlSEldhE+3fQq1Wo0lixdDPXEiNm7c5OLcZixZvAR5+fmQymTIy8/H"
        "rPhZyN6yBYWHDrVJmDdLuHKFAuuzsrA+y7m9qat1IFcoGNHVGI2MqwHcelKr1VCqRkMdpubur74e2Tk5KDlewt43f03wC7LfLJQqFfwHDmT2HrpW+OV6"
        "Ro4KZp/17juQu0eONgTg0nGFLc1lcbbDb7kI/Qf6H7FEArVNnGm0WFBzY1fpEOQKBSrPnMaKlSs79XtHZG/Zgow177G/xRIJlCHcDpy/ezfkCgXEfXwx"
        "MjgYladPY/FirjBCo8WC7C3ZSElNRWLSy+z3BQUF2Lptm9357haYTSbWLjR5fjLMJjNSUheh4MB+RE6bhlqjERlr3sPGjZuwceMmRE6ZipEjRqBg715E"
        "R0UB4Mqv5ufm3haOSuuiJSUlIjoqyk6dSklNRd6e3ez/JcePQ6lSYWRwMJJf57jrbpuUQEVho7HGrn4VRVFREQoLC6ErLwcABEil0BsM2Lhxk51keLOg"
        "ec204iWdQ3pdem36mXI4xyy8vH3tznO+9nxTZ67fESu0FQB8/Pse8/DysQCm3maTiYh9xQKA4wQjg4M7cw+InDYNgP1D3wzMJhOWLF4Mo7GWfUYT3o01"
        "NVCHhUGpGs1avFzhidGVFRX4dNunmBU/CwBtND4a5gbOGrli5UpMnT6NlRm9E1ZXd9i08SPoynVYuHAhomOimSWUFgCoNRohlcqQoNGwQoKz4mfdlvrZ"
        "tEiDpcHCCsQBwJacbOzbsxcZGRlYsXIFALDNU6kajfRl6bA0WNiz0GR/ia8YYokEOt0NUXXfnr225y3FS/Hxdtdflp5uVyCgq1B46BD0BgOmTp/GT9a3"
        "A73XyooKKG26+sjgYOTXGPiH3fJUQpaNNGbsuHqb9czKj1N1TGJwZZ2kiQN8a2BbSQ+urH0dDRLgh/k5lleh/jkaQkkDGviF+Gh0ET/K5lqTc2kWmgBx"
        "u6yy7uaHdsVozV97K8JY+eVxHDO5+JZZvh+czpdjEAw9hr4n+s4dgytcxRx05fPQLDV3x9D75Fu8x4U95WTdp96CsU9O4s/9dZFQRDy8er5to7MO1cfq"
        "qB9YCMCjsfFKOYAwcFxZ5CMZBPCsu1qtFimpi1yegOopdCdtDXQnpqVmKcRiMaJmzOgQ56BNqcQSCTasX49aoxFGoxFSqZTbGVUqJ1FMLBazz7TaImg0"
        "GgCc35PqNe+tW4sN6zJZkzZadN5VOZmuBNUVXZ2f+ojzc3M59UGpZDYHarRrzTDWWdBC/Gp1GFJSF0Gr1fKNNXbw6XPDBkKlm8pTFVDI5ZDZRM5ibbFd"
        "sXr6zs0N9dCVlsFYw1lz05em25XZ7UqYTSYYa2oglbnXm6mvmA/rr9ft/pZKpTDo9ag1GhEyYjDM9fb2oUEBgx6o1n+P0NBQlJSUoL3oiA5MAHgIBYLr"
        "56qrv7LpgS21P5oQMICT5x3FE1cPLe7DHduehZ2+LB3pLsz+ZrMZvdsRcOCIrdu2oaCggAucmKNBo8WCjDVrUHjoEJQhSqfjpbaFpDcYWEc6gLMmSmzG"
        "OIVczhz0YjFn5dy4cRMy169Hdna20znlCgWUKhW32G9Cl9YWFyNj3VooVSps3bYNiUkvuzyf2WRC4aFDjKALDx1ySbxKlQpRMTGdvie5QoGCggKo1WHw"
        "9vHmrl1fj4x1a5leSyGWiJleCIAFwNTaiF2pGo2omBhs2vgR9AYDU3/ob1JeX4jQ8ePZeqMW8Vvlnuzdp/W1RvVgPtx5N2rrr2BEMOuCQcAlMJAnnnjy"
        "CAD069fP6vKHbtBRI1YLAIx7OqzQdnHPGv1pIuW9DD5cWYPpbtsemOrNbJd1xOiQkHYtNnqMWCJBdEw0pDIZsnNyuCJ7Nv1JLJEwIgTAXACUa1HrOr13"
        "ahADOP1y7VrOhUDdGADs9GY+IqdNQ8nxEqzPzERUVHSrz+Dqu/CICMgVCmRv2YLsLdmImjED0THRyMzKREFBQacJMHP9eny67VOsz8xExdkzbRoUHa/D"
        "bSajIZUGIGGOBnqDAY0WC5QhSijkcjRaLHY+an4kF+XGfJsFtR7zrbmUMzsWyaP3U1BQgPCICIglEmzdto3d4/qsrJsibkfXlSNccWAAdm48ah8aJJNh"
        "dEgIXwIVAiDbPsn+BwDs2rWrQ1FYHSLgtLQ0AgDHDn7+rVgsvg5AoCsttdtNATCxKcT2EvigHLi9UKpGu3QttMfirVSpoJkzBwAQFcWJYrpyHcQSMTZu"
        "3ISoqGgoVSpkf5IDmVSKWfGzkJebZxcSCdzwj9J751eAzN+9G7rSUkTFxLAwSD5Kjh+/4fKQSJAwRwMAiI6JhkaTgKKjxW4Xl9pFr+Pk1xdArQ6DWq2G"
        "0WhERkYG12irsJAjoFZEPUfQBc63uEfHREMhlyMldZHb+1KqVCg6WoyomBgoVSqER0QgPDwcutIy9PbxgUIuh8RXjKXp6WyuvH18nHrwsvPZpB++WElV"
        "lN0837RUJnPaONLT05GSmgqAszxn53BhxT59fLB02TIAHGdfuHBh+yalE6AcmO8aNej1KK0xsr8pLYSFDOc2dwcXq8Cr5wO37Ab5CA0N9bAS4jFm3LgD"
        "tlCwpnnzXiFPRDznpPi7ym5xVSPLnRGL9qLpbKjeZ9t3sFpGtLgAvRb9l19Lmm/wEglvhMTRwHy+EYaGElKDGv8zapihxhY6D/xicfQYVyGnroxCIpvx"
        "jdawdrxnem53qXyuzttWNwd3GUU0TJHmAtNMJJoi6upc1Gjj7ntq5KHf89Pv6LX4lSf5/+cbkGjBP2qA5BvROmvIosZNd9+7S43lZ2hRI9uG7Tv5VVdo"
        "KGXLQ3LFIBuJ3Vo/cElJCYQCQbOXr3gXOMu0QFeuQ2jIje52ZpMJunKdy6iXYi3XHtWV3uCITRs/QuTzUzpl+qdcW1daiuzsbGi1WkRGRmLJ4sUYOXwE"
        "06GpPlKs1SIx6WUoVSomolVWVEBvsDP1w2y6IdZvWJcJs8mEzPXrGadRyOUwm8zIWLuWcUPq5H/t9WSn6CezydyqASYqKhrePj6Mw5vr61koYVJSIgoO"
        "7OckDU0Ce57s7GwUHNjfaphoSkpKmwkQYokYJcdL3IrTVJWgLh6FXO62PjUVifkRSnx4+/i4fc+60jJoZiew9yKVSpG3ZzfnRiotZS4/AAibMJG59qjR"
        "kTtH511lNHjEnUQi8RXDWFPT7nVaazTaHatUqazHjhQRAEhLS+vQvXWYgNPS0qwABH/WJByRKxRXAAiMNTWk0dJodxzVXRJ4kwhw1twli5fY+e+6GkqV"
        "CkvT07F27VqkpKZCqRqN/N277bJ5crKzkTw/GbVGIwoLC6EtKmJ6JF2wBr0eYRMmQltUBLGYW5hiiZgRZn5+Hjs/H3n5+ZioVrPFvGzpUkTFxEAhl6Oo"
        "qAjmhnqIJWJmHHH14qmRSyoNAABkZmZCbzDYdP8bRBIeHo4EjYad64rFAqVqNMLDw5GZmelSJxZLJFz/29IymwXeORDCEeEREU6RUx0pJk9FYscMNQpH"
        "e4lYImabcHZ2jt0c5efmovJUBbI/4cRlsU1cj4qJ4TLhbO+qqzwA5bb4BFdMpzWbg6MqBgCBfXo7fe7hI/bArazG4QIiAJgRHZtJKws4djXn+0zbqtDo"
        "yjfc2UHbaNDkeSrS0soKjm1V+IMmptPKh/z7pjWK+SIgv0Adf/CLs1Exl+/jpCIiHfTa/CoY/CqXVDxuTdTlZwhRkc3VnPIznmhtrrYylGgVjWtNTXbv"
        "qyODqhHufkvfCd9v3ZrqROeIqkf8uejqypWtlUam6oSrNcX3ddNYA4fKqy0ioYiMjptXYSXEB4Cwo7WhO5XMYDNmCQYrnnkHQCMAoa60lPB3SYNej7xc"
        "TjSkYXDuQBMOJrqwWncGG9avR+GhQ1yo5KkKLqSutBSvvZ4MsUTs0gctlkiQn5vLkgjSl6UjOycHK1auZO1SaXwxfS53iI6KYuJpsVaL8IgIJlpTi2tR"
        "URFMNqONXKHAp9s+ZdKKOiwME9UToQ5To6bGyCzk7jglnxPS61IJiMaeAxwXzduzm/nop06fxsIpW0N4eDgzNKWkprL31Rm48/9TQyi9by4Zw71IajaZ"
        "YK43Q1tcjPzduzFy+Ahs3LgJYgmXi56Zldll8fUyqdROdeJjqi2K0NVz8X3ddM5qjUaUnz5HP7YCgFf9uTNCgcDykFwhFAoEt84KTbF8+XJrWlqaYM07"
        "//GTsOekM7aPnXqc5tj8oOHh4Yh+cY7b89GJaY9e3BZowAZ3PjGKtcWo4VkD9QaDnR80Mellru+NycQIVVdaiuTkZABwCkgx6PV4KT4eyfOTYTQaXVrV"
        "KUGZTWbk5+ayl2yqNzNCKC8vh0Iuh6nezFwMNKRTKpUyl4nY15eJn+2F2WRmBMHzOWLqtGl2em9rOqu7Z0pJSUGjxeJkbW8LCrmcm2c3LpfRNh155Khg"
        "xx5CdqAx0uEREWi0cGGZISEhMOj1WDB/PkvDBG6E6N4MxBIJpDIZTPWuwzDpmm2vSmhpsKBGf4r+KQSAluare62ECC4Z9B1O5O90OuGRI0eEAARvvfH4"
        "crlC4fI8hYcOsRe9/r2VbndEs8kEvcGAsLCwLk0UkEoDoNUW4XRFpd3n1E+YkpqKzKxM9qId9az0penIy81z+eI2bfyIq4zRil87Lz+fux4NeG+wMK7L"
        "d7FpbK4l6q4KCQmBUjUaEl8xZFJph6ttiCViFsEUHRXF5lQmk3boPO7O7e3j06nEldaqfXB2AQk2rMt0SbxiiQThERFsbgr274NarbaLigMAzewEqCdO"
        "xKz4WSjYu7fD9+h0XTfVZSh2797tdo2wZzOZuc1eIoG5vt7uWLFE0lx74dJ3HeW8FJ0m4JKSkua0tDTB66/956Fhw0fsBReW6RRFUkYNABIx8vbsdpuL"
        "WXmqghN/xJ3rsucKOlsCPw3FlPiKcaXBAqlMhuiYaEZEYl9fLkPJYfPYtPEjp6B4R2hmJ7gVqR03DqVqNCNGSmAKuRzh4eFMRBNLJMzKzFk+2zYwtRcd"
        "9cG7g1QqdctJW0Nbudc0s8oVevTwQnp6OpalpyNyylSWdUXfKf8cBr0e+bm5XWLEchekRJGfm+t2jdD5NtbUwKDXQ6lUsmgzcBKr0NJg+cefk+efBUeL"
        "TlJsW7iphP7ly5dDKBCQEY89+h82izTgUM9nH28XVMjleG/dWpdclrqXukLsocjPzXX6rHcfHztRnYqb2uJiKJVKRMXE2OUE+/cLbFWXMptMeCk+3i59"
        "kYpwNKRQ1sYi4IPu+F0FuinSrKqugLv45rbQGjG0tbnU/VQHrVaLkcHBKDx0COqJE6ErLevSuXIFV9GE7YFcoWDeCsrEpk6b5qQrB8oH91ydvKDTbUVv"
        "tiKHNTQ0VLR8+fKLw4aP2AQXu4jjy1bI5UhJSYEj8vPzYDaZWaTSrUBefj4UcvmNMjs2TieTSploSHsIU6L9r2VpLJa3tXC8JYsXs3xcuqioa62tWFo+"
        "XBVBuFnQonldBWNNTafsFWq12i0XdjSMyRUKPCyzVx3yd+9mm4BBr0d6ejoKCwvbrCRyM6CSRnEHDXdS25oym8xYtnQpxBIJRoeEOOnKjw577KTtv51K"
        "J7zpkjpPP/20FYBgSmz0GqVK9W84VNUz6PVOBo+U1EVOQQb84I+urM7BR7FWa6czOVoVaeyurrSM1VIa85gCEl9xu0oBbdr4ETQJCYwDuwtaaA1dqUJQ"
        "mOvr7UISbxaeD/bo9G9d6cF5uXnIyMhwOu6L/Xuw5/hXWJ+VxYI2+Bys8NAhRD4/BRlr1nT6ftpCxpo1iJwy1aU01xqoYTIvPx9mkwkpKSlcU/Yb+i8R"
        "SyR44MEHiwAgNDT0zhAwtUjPnTnzp/Bnn/urWCIRAbDSoHuAi1d1RGbmDTM/DUCnhoLOFgZoC9qiIoRNmIiCPQXQGwzQaDRITk6GVCZjgfZiiRhl5eX4"
        "ua4a/v0CIZXJuPhpN6WAHFF46BA0CVxUVFv60+2C2Ne3Xembtxrm+nq7rC+9wYDk+cl4KT7ezrATFRODBI2Gsxf49ELY3DksaONWpEG2BqVK1alr0oQO"
        "yn1TUhexgBDcyEL619N/fPZrgDHCOwaB7YYwc+aLJ2wBAy38mFxXAQM0VpW2IKHxxrcjIZ4GCdBYWtqLhx+bTINRaCMyvjOfxkA7Fhegz0zbZzoGJ7gb"
        "NJa2tf5BnR00mKSreirxG7G3d9DuE7TFJi2TS+cqddW7ZPXqd0j/wUHks+07SN3FS2TD5wdJ5smTJGX//nYFBHX1oO+f37itPcOxoZnj3zSAQ6UaW+NA"
        "Qx1GV7VyIGlpaWT58uXCiOnTZpWXl39v0OsJbBX3AGDlygwkJSXa/YhmGpkb6pGUlMhE3I7ojJ0F3fGNNTXYuHETdOU6FlerLeJqJlEOWms0Mr8qFbs1"
        "c+ZgxcoV0BsMqDUakfL6QixNT0d5eTnLMaagiertuadboT5Q9xFn5b55EV08SIZao9EuTrzyVIWdZbpYq0WjxcIkFqPRCINeb6tXZi/y8kv8GI21uPxr"
        "E678dhWfrc3Ey5uyUHvkG3wZ+D3S09MxMji4QyIz9e13BtSgyk9zbA8SNBoUFhYyOwG1udCsta/KTlkv1hhI0LBhf/vmH18LJjz1lKikpKRThqwu68Wy"
        "fPlya2hoqMfcmTPPxc/WJJvN5iyzydQEW4mQn+uqMSt+FqtDRTEyOBgpry9E5ZnTUIaE4JsTX6PnH3oC4MSXW12vybHWMl/XuVHFohHRUVHQGwws4CMl"
        "JQVmkxkKuRz79uzFawsWIDommu8mYNi9ezd8+vggQCq11UdyJiKxhLMUc4H45i61rgq8egEA6n9rvW6a2WRmfuorDRZotVqW9LFv716Y6+sh8PBBjf4U"
        "lhz+0k5vbS+R0OP479ZcX48v9d+jpvEKpiyYjysVp/EHtMBwqgx9f70KTdg4FO/5HBPDJiBhjqbdBCxXKJC3ZzcWvb6wU2IwrR7TkSJ4SpUK0THRMJvM"
        "rPrl1OnToDcYEB4RgYlqNfJzc4X+/QKFo1WqMqFAQGJjY7u+E0NnYIvjFFoJ8ZoRHbvXJi7YtSF17KtD6x+dqaoiJ06ctEsV+2z7jjvefpSmpvFbp9J4"
        "XipG0vhpGhMbFDSU9OuvcIrHpeI2jXN27HZPj3cVX30zg8ZbU/GVtkulnQEnT36WxWLzW4F25TzSc9Mm4atXv0NSV73LxOez166S1L9lsfjmp5/i0lPj"
        "kl5l4qe7WmiTJz9r13ycdpCgak9nVTLagL4jv+HHutOGdnSt2OLaW0RCkVWlGvudlZA+sGX0dZbmurQbGo0mEQoETVZCooYNe0yr/+67UHCuJRHAcbiJ"
        "ajWuNHBZMzT6asO6TLz2ejKkUimrJeXTxwefbvsUoUajHSe+GbGoo6A7N3/Xj5oxA2aTGSNHBcNsMiN7S7Zd1cTIadMQNWMGevfxsQtMoMXt+c9CKxQ2"
        "WizMxZC+NB2Z69Z32TNQ0Zar4rHlls5dSmoqsrdsgTosDEbbe4uKicHshSkwGmtxvrzMViurlusd9WsTivfkIixkOPZlZrHgC/pv0Z5cqI01N7i17d7F"
        "EgmWLluGYq0Wn277lIVfUpcflSC4e1rU6TUj8W2/JBQVE8NUATrPNIw2OiYaeoMB+fl5VgAeZkvDfqFA0ACOBjvtB74loH2U/itz/ZigoKGNIq6PUgt/"
        "N46Ne4ElzPOrRdKu93SXdmVEWL36HdKvv6JLOURHOD1t/UkNRPw2ofyMpbu1/zGVBtx9zjcwufqNn58/eUQ60M4Q+PHH2SQoaCiprD1HYuNeYL1/45Je"
        "ZVlVZ6qqSOqqd8ln23eQwIFB5MDBg8Qxi629gxocU/+WRfad+Jps2L6TiITOmW2dqWBK10NHDFhBQUOd3rtjM/bUxausIqHI6ufnb0mYm/goAAHtu91Z"
        "dFlrFT6WL1/enJaW5rE6ecE/VOMen+3fL9AuzFJXWsqKrL2keYV18Vswfz6MRiML5sjOzobh8mVo5syxi94yGmvx3pq30VUIj4jAp9s+RcGB/e0yIi1Z"
        "vBiRkZHQlZahWKtlObumeo4rU/21tMYIdViYXVF4x8JxSpWKlYTpCPjncFeMjuYUO14PAJYuW2ZXLwwAol+cA7PJhEEho6GZM4cdm5KairHPTEL2Jzms"
        "F1ONvpq5dhI0GsS/FI+pCXMherg/AkapWBDLhJARKNZqUd1wBbVGIwb25+K7a380wNJgaXcivKsigF+W2vvZo+fOw0v/+bKdcc1R4mkvUmwleFwVJnSF"
        "7Oxs9t6p75dbtzc4ePGhvVYAAmmg7JuczZuqAAiXL19+R91HrcJWfkc4Izo2y7ZTOTUFp7smX1/k676OXJqOM1VVndaPqRuElgHy8/MnG7bvZPosn+O0"
        "hztMnvwsOXHiJNMlDxw8SM7W1dmVmKG1mumuTps8U32Xz9345/5s+w6W2zx58rNMR6SlhignonNBJYIxY8eR1avfITNnvsh+S/sSBwUNJftOfE0OHDxI"
        "noh4jrmZqDsv6/0P2PdvvPkWSV31LtmwfSfZd+Jrsu/E14zrna2rI09EPMf+zjx5kmRVnSapq95lebrUJpD1/gdkw/adjBuLhFwZoPZyXz8/f7uyOiIh"
        "V54mZf9+cuDiRfJExHPsPdys1NNR7uvoIqUc34Wtp8nPz5/Ez9bEUfq40zTaFph/eMy4cbtsD3zN1STwX2ZQ0FDy8cfZdt85iqOUUDojHlH/XmXtObv6"
        "V/u+PetEDK3VQnJFcHTwa2KlrnqXvVBaUIAavCprzzEjy2fbd5A33nyLERq/teVn23eQs3V1rBG4O9813YSoL5Uay+gxG7bvJJ8fPsbUkzfefIsRRuqq"
        "d8nZujqSuupdsu/bs2TD5wfJvhNfswIF9PMXFr1JFm3PI5knT5LUv2WRzE1byaLteSRl/36Ssn8/e17t4WK2OWS9/wFJXfUuKw7QkfdFN6r1OZvtjEob"
        "tu8kmSdPkg3bd3Zp21g6v+1ZW3Qe6UbN35wciLpZJBRZZ858sYxHGzeNWyJC80BiY2MBQLRtV95bUTExPwDwgousC35dKINejw/+7wOIJRLIFQrk5+ch"
        "fWk6qzJIk+9raowoKCjosO/UoNdjVvwsBD0yiJWCnb0wBbUCKwyXL7Ooq1qjEUVFRQiPiHBbX8qd+BcZGcki0KR9erGSOhkZGSwqKkAqRdAjg5C/ezcr"
        "exsglUKtViM6JhrKECXMJjNkMimC1RNhPHWKS07w9YXZZMa4ceNu3IetdSXA5Zz69PHBld+ugvhK4C0NgMHaghHBI1FbU4tnJjyO5t+aYLh8GeowNax9"
        "xAhWhULQcBnVxvPcswusOPqzBbV9HkCxVouiU6dxrpHAcKEBA4aoYKz5kXs2gQgXvj+DC0cOAwACBwfggulfAIAT35xAsVYLuUKB0SEhKN7DvTN3qXnu"
        "oJkzBwkaDT7/bBcUcjnGPjMJAPDpRxuwNXkBXo9/scvK5yhVKuYydFfSmCIqJobli9O4Z1p5k9YoA7jiBLrSUiKWSAQirx5vA0BsbGyX0N4tZ+G7du1q"
        "sRIiFAoE1d+f/+FpAIfzc3MHgmeZBpwJga+3ZH+Sg6LyM6g1GjH2mUn45vCXALhaU8ODhiFvz26ETZjYIStjfm4uCudokJSUiJKjRyFsMMMqIDD6+rGK"
        "CdTyvHXbNoSFheGrslO4aN/PBg8NegRNv15zurbZZGKJHLVGI6s2kr1lC0vmoD5jx4QPqj96+3hDLBHD0mBBdb0Z6MNtLLt370aweiIe6vcQCxZotFjs"
        "QlAtDRZcv/YbJLCiaPceBKgnoPfwIajN4qziFqsI1cbz0Db8Bpl0AJ6aMgm1NVzAwrlGgkGWX1H9eREmjnsMAs/eMDYCQu+e+KruAtADqDEQSGU/QgaA"
        "ePqAWIwI9v4DLJZfcb7yNPes2dkw6PVcQzOtFrrS0g4Vf6Mgnj44XVHJ/PIDfL3xDYDS4q86dJ62oFSpsCWH02WpHusO1G7ChyYhgVndaeaXrrQMSxYv"
        "bgHgERAgrdias2XfYQFEu3KyO5w66Aq3mgNzFxEIrJt37BANGTRAv3LNe2qlSlULjnjbNJ+bTSZkb8nGyjdeR8IcDTZmZrDgdrPJhGcinkblqQoolc6d"
        "FdoCddUEBwejmudKnxhqX8+6vLwcYokYf4qezqpAApwL6MuDX2LpsmUuDUkGvR7J85ORvWUL9u3dyxK/deXl2Lhx040yMg5xyjRwQOzri40bNzE3kLHe"
        "DMPly6isqECp/lsoQ260TJmi+TMCJj4Fg7UF5vp6/Ov6rwC4TaLWaERN4xWI+z5841oPesJYb8YFqxBHdQY0i/uDSAJgrDfD02SEweoJr/rz+L7+OvCA"
        "F374nttQzx29hHNHLwEALliFsHr1wg/nTqOyogKnT1dBUHMe56ur2fPTf2mSfkeIV65QIDHpZQiauAymH+oboTcY8FXZqVZ/0xmIJRJsyclmEXP79u6F"
        "XKFw2+6U3w8YAJYsXsJcjrRAg9lkRvKCBQQAUapUTX+aPfstoUBgfeq3Xzt1j65wWwgYAObOnNkSGxsrGjJoQPWwESOekSsU58FJAG3uRPm5ufgodzcE"
        "ffoA4MqpFh0tZgXJX4qPdxlpQ0Vwd6B+15GjgnFs9z7IvHu7PE6r1WJx+rsw2kIq1Wo1wiMiuMoUxAriK0H61hzIRznn29K2H4WHDrHE7/zcXCyYPx/q"
        "MDVr28JvN/lLM7eb9Pbx4SzzDb8g0FeM2lNnIO/bF780E5zZ/yXEEjF+qG/El6U6BPbh7v2biz/iaPlp9JFJUXTqNJp/a0KjpRHH/ml0ujfjBS6Fu6X2"
        "An4w/gjS/wFoT+lxztKCizWcKF33vR4XjDU4X3kaUsnDEPzyLQBA8Mu38Oslxva/f4aSkmMw6PVY+9oCCOpN6OXROfWOJrVwfaq4TfK115Mh9vWFt483"
        "DKfKEDZhopMURKFUqaAtLu6UVV8zZw4jXprYolY7F9YHOMmC1jgDOBGZSmtRMTEsJiB9aTp0paVNcoXCY8jQR/8zJXn+F6GhoaJdu3Z1CfcFbiMBA5w4"
        "nZaW5pGzedO5x0NDnxZLJBfAceI2H+iTte9BLBAie/d+fFnKpR1mZmWi4MD+VsvwaDQaxrEdYTaZsPjdddAWaZG3+UOYL1+ElBAnjqgrLcXa1X9Ffm4u"
        "gh8bjgCpFJs+eB8/mRpgrDiLLYfq8KW2DAOlXOcAWpPZVZUPPrRFWmxYlwkAeETShwuh9PXFI5I+AOzbnrZc/w2ChsswXL6MXh4CFqRA63FbbeL1r7/9"
        "hgDf3hD3fRiCehN++PknTFRPRMCvlwFw4aF6gwGChsu4UKrFc6EjYTx1FgAg+PE3HF27Al7159FSewHV/5Rg0DVuiQwaOQICEydiy4Q3xBXDqTLU/VTH"
        "nnPZ0qWd0kdpQMvSZcugDFEiasYMGPR6aIu0MNfX20JXTa1ycJprHDVjRoevT39jNpmR8vpCGI1G5OfnsYZ4FFybltEs3DUvN8+uBNDSZVyOcuj4UGza"
        "+FGTWCLxGjZ8xK6tOVuyQ0NDPTob8+wOt5WAAc5HHBsbK8rZvOncHyMjJyqCgozgiNjOH+a4+HWlpcjIyICg4TL+HDkVH+VyETfh4eEoOlrslKfLryS5"
        "b+9eJ18yxdolf2G7Z2r0i4hSh7UZN7tyZQaiZr6IizUGGM5zi/kH448YJJNx1S/CwxH6/CTka4tYSxdXWDB/PovUkgWPhplY0VsqYwkWhz7nqpTUnipF"
        "ea0RpE9fABxn4HRJM2rrr2Drxzm4YqwBLP9G9blaTJgRheI9n+N0RSW02iJOjC4+hkmKIZg4PQY1xIrzLQSW89X49bffMNhHhAtHvwS8OZPEAF9vDBA9"
        "BKH1awhMtTB+a8AgkQC1p0rx0/EjAACp96MY6vkbIyjHfzsCsUSC1xYsQPaWLRgdEsL86nSOCvbuRfaWLW5/T33pZvONWO6OgCvoz0lPGRkZrDAiv9Ch"
        "WCLB+qwslpAjlohRWFiIBbbihwDnL681GhH5/BToSkubxBKJZ+iEibt25+2KEwoEzSUlJV3Gee84YmNjRQCQMDdR5ufnbxRxMdMsWqtff4VTj1lq4qdu"
        "Huq75afN0ZhY6jPluyI64h+kKYRtHRcXn0his3cQ5Z/Xkw3bd5JxYU+Rfd+e5VwuJ75mLpX2uLZa823TCCmalkefke8/fmHRm2TD5wftrkl9sIEDg8jZ"
        "ujrOH2s7xs/Pn7mFnoh4jizankf6Dw4i/QcHkbFPTnK6vmPdb347nc4OGoNNff8nTpxkseLtcS9t2L6TrYMxY8exmPr2Xn/y5Ged+kS7ug711zu6i+ig"
        "z2D7u8XPz5/MiI7dZSVECEB4sxFXdyViY2O9ACB+tmambXFcF93oF0PmzXuFZG7a6rTQ6y5eskssOFtXR87W1ZFrTU12RECJuDOO/c+27yBbas/ZFezm"
        "B+PTc8bFJ5LUVe+SGX/5X5K5aSsZM3YcyTx5kkSvyuT8pO0kYP453Y1HpANbzYkNChrq5LukBenpIhszdhz5vrqW3dfq1e+QoKChZHTcPJJ58mSX+lNb"
        "e87+g4NYoH9c0qssvHbmzBfbNRcioYiMfXIS2fftWbJoex7Z9+1Z9nwdyRumhOnONx0b94JTHjV/E+VvBLbPmv38/FtmRMfu4CX3dInP964EjUaJn61J"
        "sb20FscJdNyN6aTTFxWX9CojYkrINDaW7owdJWI/P3+yPmcz2XfiaxZ3vXr1O+y8/OP69VeQRR/uZNFRqX/LItGrMsnaL46zKKb2cJRbNVw1jXPknn5+"
        "/iQuPvGW3UNc0qskLulVMvbJSWTsk5O4gBFbBNfC5Wkdfjfjwp7igm9scdC00EBHz0MDblytD8dgDMrdW9kgWmzjIl3ft5rz3nG2blPqPbZ9kp0x6bk/"
        "vm7TU1niKs3P3bhpM/tN+tJ0mE1mFOzfh6iYGORt/hCaadNhPHUK8r6cnvhyzAxUnOVqzudkZ7M43vbCbDKh5ADnb46cwlkVqTvHv18g69NrNpnwc101"
        "zh/OQ+a69RCLxQiQDeaerawMTaJBMDYCRCp16i10u+AYC7xp40fMl05hNpmQt929ntkZiCUSFnTx1IypmJDyCl7Z/gEmTInAEe0xWAOkEDaYEagY3ua5"
        "/PsFMmOkZs4c7Nmei4BRKkxSKXHsiBah40M7ZTxLXrDArlk4wNlfVqxcicysTPaZrrQMOVuykbxgQWs2EisAYWxc3CUrIYK0tDTh8uXL745c31uNh+QK"
        "L4Drt2TbzexCLqluRP/ml3Xh6y6pq951yoel2TGuRJ+2dujUVe8yMb7/4CCSuWkriUt6lf3r6jdxSa+S0XHzGAceHTePjI6bR/ad+Pq2iKh3erz917fJ"
        "mLHjWC7vgAEDyOi4eURTfY6M2LqTqRYbPj/IFz3djjfefIudi0pBNA67o+Vu3L1n/t+O+dhUgmvjPlts6/KHzTt2BOI26b13nANT1Om/bwLgkZe7c1ls"
        "XNzXcAi51Gg00GgSGBelLU4y1ryHlNRFzJ20dslfEDllKstUMZvMLGJGV66DtrjYruF2WzWfj+4/hL4PeiJ67jxcrDGg5OsTGOQ/ACVFxQgd94RT6VMA"
        "yNv8IS6WaSG6UI3tmzdB6v0oAEBbWcuipaJiYvD6B9vZ9fkWcsq17hXELFzEvAD+/QIx408xmDg9BgLvXig0mfDkc5Hw+Ne37Hjj5csQNFzG08+EwVxf"
        "3yrnpNVPJoSMgK60DL2kgVBJB6HRWItvDn/ptgVLe5GY9DJrpE45L/XjApyPd0FyMisY7wYEXJXJX1XjHv/vuTNnVsfGxgpuR6bRXUPAQoGAWAlpEQoE"
        "ps+2fzZZqVLZ+YgNej0y1q51qgq5ZPFizIqfxZWD/fokwiMiUHjoEKaPf5I1uwKAFStXoKaGi21euuxGV3e1OsyuQ70jyk4eRnl5OYiFE7GOfc6JTy1/"
        "GI7zNRcw/uln7I6nLoeLNQYsfFmDizUGXPj2c0bEtM7WoBlxCAi+EYv9ccE+JCa9jKiYGORvzb5lpXW7Gg/L5JgdHoap06ZBLJGg+bqFqyEm41xBh0tL"
        "MSHlFTwVEQnJ16cAcPHSYl9fVOsq2uzWoA4Lg5lYYWz4Bd7SAJzRFiF/924WZ97ZVjxKlQoFB/ZDKg1Afm4u5AoFMtathbm+HnqDAbrSMkROmYolixe3"
        "xzXWLFcohJOe++OMbZ9kf5IwN9GzK4M17inQYgAZmVmRtgyOFhHPMu1u8NtM8t1P1NBBxaETJ06S1avfIfPmvcJEclrupL2GrrFPTiL9+iuYKC0SckYa"
        "d21L/fz8yaIPd5IF//N30n9wEPHz8ycz/vK/JHpVJkld9S7p11/BSsqkrnqX38G9U+JgW205O5tA/0TEc3YJ8mOfnETeePMtJ/cVTT2c8Zf/JbHZO8is"
        "E1+w7w9cvEjO1tU5iaNjxo5zmr+xT05iWVWO7V5vdtRdvGTnbqKpk52Yo6s2l9G7ABAaGup5O+nlruHAFDTQIyV5fsGQoY/GiiUSK7iYaZfGABp+Z9Dr"
        "ERkZiVnxs6BWq1F5+jSiX5yD/NxcTB//JGt94q0chUhNAoarw7C/kAtKWJCcjAe9HkDR0eJ2ia9lJw/j57pqGM8aIHiwB8Y+MwkC714YOMS1McZsMuFM"
        "/sfYmbkEF2sMLGzS2ngV52tq0HzdgsPlp1BjsYJIAnDkeCnj5B3FM888g7ScHLe/VYeF2cWNK1UqTBx/45n9+wWyMMbRjz+D0Y9zEsbE6TEYKJVBPmo0"
        "nkr7K8QSCZ6YNhdhk6eANP6CGmsL+o9+kruuT28YbQEVD04YAwDw7uWF40VHgPJypC94nUU40ftM0GiwYuUKO8ljQpgaI0cFw1RvRn5+XpfVhA6PiICx"
        "pgaRkVwhifVZWQiQSllAj2PEl7uYaHDSYY9nnnnmRF7uzpUAREePHbut5XHuOgIGuJDL2NhYr22fZO+e9NwfE8QSiSdcEHBUTAwK9u9DQUEBwiMiYDaZ"
        "kJ+bi9Dx45G+NB0L5ycyy+WSxYuh/mMkqnVcmOTTUZH4KGsdsyTPe3UeAGBjZgYWrninXfdZdvIwjh3RYqB/fwyU+KGkqNjtsYWHDuHnOi7I/3pjPQZ7"
        "CxAm78e+97n+K6yNVzFA2h/nr1mwPisLS9asRvTceUhJTbVr65KY9LKd2M9vQ0L6D4RUOojpdY6ErAwJYdUSAU6k93yAm1qlSoWn/hiBtPWZeFgmx1MJ"
        "iZgQzy3yC6Z/YaBKDQAQ1hoRNj0GdYZiHDbUgVhMuHD5F9T07snVwrL8BgAY7C2A+NsqXPuuHhavB/HN4S8R+fwU5lnI/iQH6zM5Sy/xlcBw+TJTkcQS"
        "CTSzZkDQpw9q7TsadBgpqalMR09Mehnm+npoNBp2ztEhIVj0+kKXvxVLJFianm6nutk2tRYAoti4uBOfbf/sWaFA0GAlxNrZLoOdxV1JwACwa9eu66Gh"
        "oZ5bc7bsCJ0wMQ+t9F3q3ceHI2ReptCmjR8hdPx4nK6oRNFRznD1zeEv8efIqdiy5VOOkENCkLdnN5QqFQx6PTasy0RNQyMCZAFYt217q72QKPI2f4ii"
        "LwsgaLiMp6ZMYoQU0F+Oddu2I3ruPKffmE0m7MvZDNljQ1BTUQYvb19YvB6E0Lsnanr3BBH3A/GVoI9MioFPP4OBUTOwJSeb3Y9Gk4ApvF5HGevW4i8r"
        "uBJDpPEXaCv+CYGPBCmpqfi4YJ9dcL+5vp41DAe4pupqtRpiiQRp6zPRJJFCa/wBgwIDUfR1HTvu6I7dgLcIj4Q9h3MXfsM5SwsGqtSQDuyN2h/qIfDk"
        "2q1MmHEjdHSQ/8OQCUV4aqgUMhexDIqgYazNTdioEag2nseWnGysWLmSbUCkoQHnfrzc5ntwBf9+gSg4sB8hISEoPHQIK1auROT0SOhKS5lBKvrFOfjm"
        "+7NuuTtXOK+YueLkCgVq9KesAESjH3/m4mfbP5skFAga09LSOtycuytw1xIwwPmIhQIBycvdGasICjKAq2JgV1srLzcPOVuyoSstQ3h4OAoKCrBi5Up2"
        "jk0bP8Kypen4dNunWLFyJcwmE9Yu+Qu2fpyD7yvOoYZYsSWHMxpt2vgRas5+DwBoFvfHS5nrET13XpuirNlkglarhTT4MWbUkvTrAwAY+PQzrIk4Hwa9"
        "Hv8xazZ0paUY//Qz+O7SNdQYCFr+9QvOX2uCsRE4cIHLC87J2IKiGiOkUinGPjMJeUXHAJ9eTNyvJkCt+Wfueio1LliFGCSTYeCQ4TDWmzFhxo0ewY2W"
        "RqfWoL19fKAOC4OhkZP+BogfRsuv3F4pfXoixBIJfq6rxgWrEMJH/OExdBBIr2Eg/R9A7akzkD7GbVqND/eBESJIfR5AoDIE53++iDCZFEJdOValpdtd"
        "c+F/vY2AgY+g8lQFHhr0CMs0U8jlMNfXI/T5SRD06QOFXN6qZOMOUTEx0JWVIEAqxUvx8QiPiEBK6iJkb8lmx4glEkyfEo73V73r8hwrVq6E8cd6Fq9u"
        "m0NiNpla5ApFk0L+yDyhQPDL5h07RHeqttVdTcDgKnoIhQIBeWNp2myxRCKEzWRPD1iQzOXblpWXswwR6laiRJOfm4vIKVMxdfo0lBw/Dv9+gcjb/CE+"
        "+2sKivd8jhpiRd6e3fDvF4iFL2sAAB4tjSg+8g2emjEVaZmus5n40JWWonjP57hg5Ko4GGtqQH69hh9Kv0YvZRj+8w1ndwdNixskk6HnxUsI8L+Gf/1i"
        "hvWnnwFvEQb4eOL8tSaOWMS+EPhIoP28AABQ03gFf/rzHACcfknENnHcW4QqaxPg8wccrzqNoz9bUCMgrNWlVBpg1+j7dEUlrlgsEA4MgHxgH3iajJB7"
        "e0AqG8RSB+lvAeCfIiH+KRKiKawfBnr64nxNDSaEjMBAoRXeFxsgRQsCBYCUEGzfvAnR02dg2dKldoEj4RERWPTaXABcW9nePR6EvG9fyPp4Q28woGDv"
        "Xowd8hjkffsiLzevwwEmiUkv49Ntn8JYU4OwCRMhVyiQnZODjDXv2RXu18yZg2JtsUv3UFRMDAKkUqxd/Vf+x8Sg17eIJRJP1bjH47d9kl1ga2ZwxyzO"
        "dzsBU31YNHfmzBOhEya+B4f0Q2pw2LB+PYpsLVHMJjPCw8OZeAxwOmjYBE501JVxXQZ1paXIWfsuPt2cA68eD2DzJx9DLJHg9fgXAcsVqGUP48jR02gW"
        "90daZttRVGuX/IUtVLPJhJKvT+Bh/9E4uvsr1Lb0wKiYRLe/+2TJfAwWNSN0cD/IcA3nd+9EmMQPg64JERYxAADQf2BffFmqQ4AsAMbLlyENfgxiiQQW"
        "rwdBet/oGDi0xYoAsT8GSvzwT5EQvfv5sfYe5vp6SEeNYsfSzB/S+AsCB3MRZIHSQRgkDYR01GO4LhYz19dAoRUIGYaWB7nNQuQjYu61vkY9Jgf2hzT4"
        "MVgaLNi08QMuW4uX1SNXKLi60Tk5zL1nNHLNr/UGAxRyOZZnbIDZbEbG2rVInp+MRal2BNQq5AoFtm7bhsysTJhNZkRGRkIqk0FbXAxjTY2dz1iuUEDs"
        "6+uyobh/v0CkLFxol2kEAGaTqcW/X6BH6ISJu7Z9kr0rYW6i553OMLrrCRgAdu3aZQXguTtvV6p8SNAhuCiGbdDrsXbtWsaFaduTkuMlLHDDbDIhdPx4"
        "5OXno2A/53c1m0zIXfselqz+H7Q84IWPC/bdIGIAYdMnYOvfS0Fkg9pt3KLI2/whqrTH8WTYE6iuMWLW3NlOpVwpzCYT9uV+gu1/XQZBw2Xk5+biz5FT"
        "0ddcDUFNNWTevSGS+MNorMVg/34QVlYhcPBgiMVinC8rxdyIcChVKpDePdAj6EZxgLDBg3H6dBU0by/DipUr0WhphFggxNZt25hhJ0AqxSAelxULhJD0"
        "EkIq6w+pt7ddl8XRD/wBoiG+GD1+NGTevdFosUAdpobRWIuA+noE+oqRk52NzPQbagwNxqg8cxorVq5gxFtYWIjCQ4ewPiuLqxe25j0uL9tmjNy08SNm"
        "+HMEv04Z1/0vFdriYlZYPTk5GWKxGCXHSwBwgUD8+9FoNG5Lxs6Kj0J2do6j4awZgMfjj4/asTtvVxwA0ZZNG916R24X7gkCBtc8rQWA8M30tFfEEsnP"
        "cOhDDHBirHriRK6xFK8e76fbPrUrSrdg/nxkrHkPmVmZTF/O2/whp6f59EJaDlfveHnyfAhqzuPPbzyNY/80QjrjWWYQEkskzIXVGg5/8TcMllzHYG8B"
        "fjD+yOoxp+XkOFWOMOj1+Obwlyz31Wwy4dDnxSjekwvz5YuYqByD8+VlaPj5R8DnDwC4BH1B7QXIhVwu788ST3g8JIexETh/9juE9O+DHyxNOFx+ClOn"
        "T4NUGoBS82XIpFIkv74AuvJyqMY9gbCQ4ZALRQgJHMRtgPX1eLrPAwgSerIeQVK0ILKfP0Y/wF1bKJbAaDTC9FMttFqudatjPrVcoUBBQQFSUhdBbzAg"
        "LzeP1W1OX8oF1CQlJTolxreGqJgYJL++AI0WC1JSU1F0tJhtDGaTGUsWL0F+bi4j2uTkZDsxWalUYve+Iy5FZ6p2OXDmJgAe8iFBX+zO2/UiANGdsDjf"
        "8+BlLi3lpR+6dLA7xrO66nFDS4Lys5WeiHiOK6H6tyx23IbPD5KsqtNk1okvyIGLF8m4sKeISChqd3CBn58/eSLiOZK5aSvLfHlh0Ztk37dn7eKpaUqd"
        "q3Ok/i3LrtTpC4veZKViFy5PY9k4mSdPkoxLP7Kc5Px/XyFZVadJ5qat5GxdHTlw8CDJOXqYZeE8/dRzrB40zeKi16EBMHTuPtu+g5y9dpXk//sKOXvt"
        "qt3n7uKEaUYPPZb+TXNnabZZewMn6Ds7cPAgC9zhB+nQ90HL7fJydFsN0uD3h3J4FhrjXL95x47hAASbd+wQtbFUu+EKVkIEtmLx3irVWJ1tgpsdXxB9"
        "AfPmvWLXeIwGvvNfIL8BFk0bjI17gZy9dpUR05ix48iW2nMkq+o0yao6TSprz7G84I4QMj/aqP/gIFZ3mV6X1qF2dS6aJME/F63rTAP9J09+luz79izJ"
        "//cV1uLkbF0d2fftWfac/KLtdAOgdaTp93Q+HJPX6TFn6+rIvhNf2zVjc0fANB85KGgoK5jemUgzPz9/tz2JaUsbeixtoNeR1ja0gL7D51YRl5x/JWFu"
        "ogq49emB9z1oJY+MzCy1n5//VRHX7cEu1DLr/Q/Yy5g8+VlGxK5eKCX41avfsePSqavetSv8Hpf0Kjl77SpZ+8VxUll7zm5nHzN2HDlbV+cyO6m18UTE"
        "c2Tft2fZuSj3b88C5/cAok3BaeH2s9eukrN1dWTy5GdZxQpKwKmr3iU5Rw+zv2nRhO+ra+048YkTJ1n+K910+J33nn7qOSYNBAUNbfN+6XnrLl7qcEcN"
        "mrfrinhpR0t6H3wib+91XHWStI3rtk4KfwWAhLmJtzVM8r4FncgZ0bHv2RaOXcsWWp6GEjGNp6Uchi4Kx0VHW1LS73OOHrZL4KdcqbL2nFO7F7pwOro4"
        "N2zfSb6vrmUbBV3ofFHQFXFQAqSSwNt/fZv4+fmz35+tq2PiKW0lSu/5s+077CQP2mY0KGioXZsb2miOP4/8OWzvoJ0wWuPUjsfzj3NsXUIHn+vSdFGH"
        "VibtGlR0dvi8WSQUEdpJgTKObnQBbCVKPKyE9FSpxp6yTbhdJQ+qa1GC4u/g/B2bEislFj7xUJHPsS8wX6/mt4PhE3V7Rbe4+ES7a9DzUCJxV6uJ9jty"
        "vA6/TI1IKCLpi//KdHDK/Sih0qQOdy1EHDc5SkidyWl2da/ujuOXRaIbjaPIzJ8vR3vH99W1Heq55GLTbREJRc1BQUONm3fskAIQdYvOXQyeQSvWNulO"
        "jdP4XJHf6pHqdJMnP+uk99A2mPxz0KwVSuD8wefCBw4eZMR24ODBdmfPOHJZmuROReOONqieOfNF8oh0oNNGQgmWbnAd1UPpptFR4m3v4Je4oddzrEd1"
        "4sRJOxuH4/fupCB3m5Qb8b8lKGgoycjMepG/1rrR9RBYCREMGDCgXMTpwU4GLdohji4+R8KjBhb+C6XGIZGQS2njL4qPP852a92m+jafc7jrtdvewe/m"
        "d7MjNu4FO851N/Yu5hfmczRa0ZRPWqHTlVHLlbeBnzrajtEsEoqs8bM1/wl0E++thggA5EHDol3pwvxdnJbT4RtTqK7lqNNRazBd4Bu272RERAnc3Y5P"
        "OUS//grGHX4PZXTaGq01FJ88+Vk7w6NIKLLbbPnES9/BvHmv2LXvdNyY6bH03B0gXjJm3Lh9QLfee1sQGxsrshLiMXPmixUiF1yYvkT6sqmLgS9KUyMO"
        "f1HxufATEc8xqy4lUkexjv6W6pYioYvqmfGJTvWW78dBuST1rX62fQfTa6mlmNaB5qs2/HfA12sdvQfUSNmaOkPfewf6BVtFnN7bYCXENzY2tlvvvR3g"
        "VfCIsr0oJwKmi4pW3uAbo/guEv6LplZN+tm+E1/bBR84Lh4q9vHrMFNDWuriVXaL0lE/vl2ibHuu05l7ob+hvYapK8xxjmjvYz7BUYmGP9d87uvoF3dV"
        "p5lv6KMbB1VhOtA/upnffLub+95G2Liw18yZL56mL8Pdi6K6k6NVmr50/oK8UF3NPnMkaMcFyhfT+FZuvkvDsc4wNXrRTSQ27gWmr1Hu1J7FR1UBx8Hv"
        "2sAX42lZHHod/jVd6ex84xflqFnvf8D0cyqBOFqDHQe9L/o3f074bh/+efjuNHfuJH4pHP57dVfiyBXxioQiMmbcOJqqJEIXNeDuRjtARZ3NO3aMDwoa"
        "es32QtzW0XJcDFQfdhSlZ858kS3O/oODyJmqKuaecXRv1F285HK3p9zIkbM4ErJI6Gy0OVNVxRYhdZdQ8ZMO6pt2NU6cOMnEV/qMjv5Seu+fHz7Gjjtx"
        "4qTdtfhqgjsi4rcfcTXo5kelF8dnphsMn0PTZ3fc+NzpvPzrd8APTKOtLGlpaf0ACLpF5zsAKvLMiI5d0xYXdrXTU+OToyj92fYdjGjponZcaK64MJ97"
        "UW5DDVuOOjRdzK4WalvE35FBCbgzv6WSSGsE7C7UkU9Q9PeOEWSO74RuGO0lXv6cnqmq6ojhsEkkFJFAxZB1QLfV+U5CQIl46KPD/im60ebC6aXxRUvH"
        "XduxlUtQ0FBWeZLqX3RxuArvc1w4VGSkouCZqiq7yDA+cbiycNPr8Y09nRn8xIPO/J5yQ1cETInNXbgjJVjHDY36celc8Tcpflhna8TrSiemc90OFcQq"
        "Eoqax4wd928rIfck972nbrYNkF27dgGAYNyTT87CjWdzSvkym0xcQrdYjMjnp2Djxk0AgOiYaMyYMQNXLBaWZmjQ63Fg1zaIJRJobQUDIqdNAwDk797t"
        "dBP0O5pmaNDrsXHjJpZQry3SwqePD3TlXOH52gs/sTQ6Lvndvj2mWCKGt48PzCZTp1pnUlSe4or5+fTxaePIjqPGVpuMtuh0hN5gQH5uLpQqFQKkUuTl"
        "5gHganvRIgxiiYR1vdcbDJDKZKyVp+O5IqdMxaaNH0EskSAzM5OlEQJA8vxkFB46BLFEwupqtQIrANGQoY/+RSgQ1MXGxgrvVGmczuJ+ImCAeyGCCRHh"
        "VSHK0Tpwz+cyZ9NsNkOtDoNcocCC+fPZooqOiUaAVIoAqZTlEBceOsQqfxQVFbFm0AV79zoRXMIcDespS7Fs6VKWPL5v714AHCEDQO8Hetr9nhI2H8oQ"
        "rgxsrY1QOgNaByuAl5zfVWjrvvbt4Z45asYMyKRS5PAS6Yu1XL2rlJQUKORy6ErLoC3S2uVzU+gNBkRPn8HyjVNSUhjx0mbblLBTUlLYhusGLQBEIcrR"
        "3277JHs9ANG9WIz9fiNgEhsbK5g7c+avr6SmzBZLJG5r9JpNJmza+BE0Gg3kCgVeio9niebRMdEw19djxowZTo3D165dC6VqNOQKBQx6PfLy8+2+V8jl"
        "Tjs/vy2Hub4elgYLjEajE/EDNzglHyOCRwIAamqM7ZgC1zhdUQmxRAKF3LkVTEdAk/v50JWXuzxWV1oGANBqtRBLJBg5Khg1RiMjwIy1a5Gfnwe5QgHN"
        "HK6+V3Z2DqKjopzORYmXzmNi0stISV0EgJNSdKVlrASOZs4c6MrLWytFSwAQuUJx7U+zZ6eCU7/a9fzduA3gGbS2tuYb5lt3qZ7Jdw9t2L7TZTvJuouX"
        "7KzDruJ1W9O9aNQR1YVpX1uq0znqe60Zudo7aHx1Z39PdVhX3/Hjth0NV3xjFD9DzJUxkeYmu9LfHRNP+F4AvgeAn03VyqBpgv8BdBuu7kYIwMVJ9xj6"
        "6LBz1FXgzphFo7NcWZfrLl5yym6hlTX4lmp3C97VWL36HRIXn8iuy+/Q54rI6L3dLAG6spy3d9D7c7dZUQLmW9lpGiN9ZleERTclGtzi6tqumpbzN1q+"
        "QasdYZPU53vQSoinjXi7fb53ITwBIFAxZAXddVt7sdTnSXfxuouX7Kyg/FjcMWPHuY0c4hOdOysozbGl7g9Hy7WjNZcScGcs0Y5him0FW7RFwK64LP++"
        "qd+bJtq3ZhHmSy+0EbvjvbvaCPmSCN0g2tnI3SoSiq4HBQ01b96x4zGgu8LGXQvbixEkzE1U+vn5X7O9PLfBHZSD0B2cLga+SMvf3T/bvsOuo70rwnAn"
        "yo19cpKdW8Vx0Tm6T/gZNq25alyNAwcP2iXSd9aNRLlga89Ir0UDSNrghHYFAhylC9rQzPE3/CQRfpqnq7pc/Mwmyn1tovMzQLfofC9ABACBiiH7bC/Q"
        "KVvJkTNea+L0RRqt5UhQVPflf++OC7vThf38/NnidBVw0FrhAFcJ7q0Nfrok9Xt3lIvzr9+aeLt69TuMiNsKY+RvjLRWGJ94s97/gBWY41+DbpR8f7xj"
        "Sih91rj4RFZvTGQTnWdEx34A3P4ugrcKvwvxQSj0oDGureo6GWvWcJ0B9u+D2JerrRweEYFlS5eyY1asXMGKwu/bu5eVIS08dAiFhYV251OqRtuVs6Uw"
        "m0zQletYV0VHVFY4W6Ip3Fl87c9vtrNw02solUoESKXM99peXGmwsOLs/PNyfXRLb1y3vh41NUZYGiytPoNcoUCmrakZPYejdbvWaESjxYLIadNgrOG6"
        "XfCbbycnJ8NsNmPhf72N/N27YdDr7drXiMViVJSW0LrSVgAIUY425OXuXAJAcLu7CN4q3O8EbAUgGB/65GG5QvFvtOIXpli2NB0AkJ2Tg2KtFlOnTYPZ"
        "ZGLtSel3SpWK8w+bzSxo493/cS78nrLQddc7XWmpWzeHTqezI5TKUxXs2MqKCpfuJz6MNTVs0RuNtexz2mGvWFvc5jlag9lkht5gcHJ5VVZU4HRFJReo"
        "onP2Z9N5em3BAubnXbY0HXKFghEmwPnCs7dswX++sdjmazchKiaGuY0+zNmB/NxciMViFB/aC11pKcIjIjAyOJidw6DX8zfHFrlCIfrT7NnJQoHAlJaW"
        "Juqu6XzvwAMAZkTHrrfpwK2K0XwL54GDB5nLx9GAxDdi8UU8VzpqB6pBuNSpHS2rbenB/CQEfpojFV2peNraeVyFevbrryAnTpxkFSwdxWSqGrRmCear"
        "GvQ4R/cYzZDiZ3XR++GL8/TfsU9Oaq1qSbNIKCLxszWLgPtP773fOTBCQ0MBAFNio3PFEkmb7gKzycQih8LDwzE6JAQJtl6y/KANsUSMggKu0ZiUF7WV"
        "nZ3jdM70ZekdbtbN76LniPzdu1vloD59fFBuE7WpiEs5uNFohNjXF7rSUmRn50BvMLDBHcdxV8rBgRtie/N1C8rKy9H7gZ7o3ccHjZZGu+tS1aBYq3V5"
        "X47hklQ1iZweeeNapWWorKiAVlvE7j07O5tx7D/PXcDOZTaZoFSp8PHm9Ui3SU4OoD18v9mas2UtANGd7mXUjc5BZCVEFKgYsrE9xixX7hoabOHIqSgX"
        "4ddrai3hvL2Dz3Ucgx8oF3WVNE85MOV0jhbuMWPH2fmV33jzLXLixEny+eFjTOqgpWbp+fgGIlpF05X7i88VXQ2+MZBa4R3ni5/b62i0o5IDn/Ofqaqy"
        "KxXMu16LSCiy+vn5/5iWluYDQGirZnpf4b7nwAAQGxsLoUDQMv+15F2thVdS0JhnPtKXpUNXWsrCAymSkhLx1IRQZG/JRlRUtMvfAlx4n2OP4NZg0OtZ"
        "XLRjP9/KigqIfX3dxiD79PGB0WiE3mBw0rONNTWoNRqZAe3TbfkwN9Sj+rszMJvMqDxVAS2Pg+oNBjtDG2m6wri/2ewsBbjT65UqFQuR1JWWsTafSqWS"
        "cVezyYwCW6y42WRiPX3pd/v27kWCRsN6R5UcPw6Jr5hxcodrE7FE0jLpuT++unz5cktsbKzgftR7fxcEbAtS90hJnv9lvaXx/8DpxS2tibU5Dp3rwsPD"
        "IVcoWAaS2WRmxLx69f/AaDSyVp3lLizFYokYS9PTO3TfBXsKbNcptfvcoNejvLzcZdy03mBATY0RBr2eqQJ80EVOe/7+XFcNbZEWpysqoSvXwVxfD6Ox"
        "FkZjLcwms8tNwlRvRlk7rOF8cGoER6jp6emsMRzN0gIATUIC2yzkCgUTtwEgLz8fI4ODsWzpUq516/HjkMpkUE+cyJ6Jt0E2AxCIJX2/3PZJ9t7Q0FCP"
        "ezFRoT34XRCwDVYAwviXZq0RSyRXAQiVSiWh/YMdUXjokBO3jZw2je3+YomYC8wvLIRSNRrKECXM9fVcN769zoQDcEkSHeHC+fl57HqOaLQ0wmisZbqr"
        "rrQMhYWF0BZpmQ7qKt0R4JIiaIYTwGVVabVFyPk0D42WRnj7eMNcb4ap3uyUQNFosUBbpGVZVe1BeEQEszLrSstQeOgQ1Go1lEolpk7n0i+XLF5i19Vw"
        "aXo6S7ygHJ+zwHPE27uPD9QTJzKCT0lNhY9kEMB5GQRyhUL4ZnraMgDCfv363Xec93cJaoGcER37nk1nuv7Gm2+5rd7gKqDC0UJMdUgaOcRP3Heln3a0"
        "LYk7nZLWtKL3SOtUOZYFcqdfu3tmfk2tM1VVThZ0WjSusxZ1atF/4823nMrruJt3vh2AlvtxnAuejaFFJBSRGdGxWUB3cbr7EUIrIUKVamyV7eW3uIsa"
        "cpU8QLNd+O4WuhD5He7cVZPoSMe8tsa8ea+w0ELqOqI1qbvi/J9t39GRqo4uh2OFSfoZv3MkfzNxl3BB46pdhWjyIrGsIq6rwqXvz//gDU7CvO8MV3z8"
        "nkRoBqFAYH0seOSLAC7pSkutWq3W6kqUNuj1TtFVKSkpMPMqY4glYkxUqxE5ZSrCwsJYMMHpikqX1xZLxO2pFNEu5Ofn4ee66hsNwevrYdDr3Xa17yho"
        "NNTNYKqtQgkAZtxTq9Xw9vFGeHi4XfNtsUSCLTnZTufIy82DrrQU3j4+LOeXQqlSwWispedoEUskQtW4xzOHDBrQGBoa2mbgTjfuQdA42PjZmiQbN7wW"
        "FDTUZaID5a6OgQ2OVS0pJ3CXlsgfHe111NagSRdUPO/XX9El3SBuVlJwdBHRQnarV79jlyvcWpx3W61WeWVwm0VCUYtKNbbMSsh96zbqhg2UiGdEx650"
        "15aFDhqxRP89U1XFUgod/Zr8znqtpe7drGjqilj4da3vhr5H/IQF/sa2evU7TqKzq0IGbc2TQ73rZj8/f5IwN3Ei0K37/l5As5WW2xb8dZGLlEOqx/Gr"
        "SdJC6I4LlF8gvrUE/I70r71XB5+j8p+X34eZ/5kre0M7r9UsEorIgAEDiq2ECO63cMluuIcAtljptoiYtr3kp7O98eZbdqI0v/oEvwWmOyLuaDPwe224"
        "6rDwxptvOXUQdCU6u4ttdqMaWG15vk8D3dz39wa2YwcqhrztTpym9YcdE+JpS1FK1DR/lc893CXRt6Xf3cuDHwrq2NmRv3G1t4yOSOi2TWizSChqCRo6"
        "7LCVECFsUlU3fn+gRJzO48RsoVCDDNXf+EQ4efKz7DN+HyR+XK+7JPqO+oXvlcH35VJi5PdRosOxC6G7OaEbggsO3GTjvpFAN/f9vcMDAORBw5byiZhy"
        "SX5PIkd9lq8PUw7Dr9HEJ3LHBXsru97ficHfsPgVTBw5q6uADXdSyZmqKvL54WOOn7eIhCLr0EeHff39+R/80G15/t1DQK3TgYoh6XSHpwuG5tC60mvn"
        "zXuF6XJ8gxZf5HNFxI464v0wqF3A0XDl2LLG1Vy4yp2m8+pijppEQhGJn635E3D/5fp2o/OgRPy/jkR84OBBt93hx4wdx0RCfltSR53P1cK9X/RhKonw"
        "n4cStGP/Zcc5cOUfp5zbhdWedhWs+/78DxJaxPAOr5tu3A2wiWEiKyHeQx8dViniNUqjARPugg743eOpuOhY7tQdEXegm/xdOfhBL/TZKQE65vm6CjV1"
        "5LC0Ooqb8FPKfd8AurlvN5zBLQivHmr+gqHcw13gAU0651tfadlTR85yPxExX63gSxwHDh60cxsFBQ0lsXEvOAW5uHIbUS7twt3WYiPwC2lpab74HcQ8"
        "d6MToBbNMePGHbAtnGbKGVpraM3PEqKc540333KZReNOnL6XdGJXvnA+UfMJkBa1p8/tzpBHXU5u/MG0p+8m26vq5r7dcIZNrxJu3rHDPyho6DX+7i8S"
        "ug//owuSLmy+KO2o57kjYkoMXRHTfKvG5MnP2hXG46sK1BLNJ0Bq1HOcN1dE6jh3jhzYz8+/OWFu4ljcgz19u3EbQblw/GzNJJFQ1Gjb/a10kbrL+6U+"
        "S9puxN2ipgvbHRFT3/PdxJH5mxNfauBvOI5VMSlR0jlpTfel3NdNuGmzSCgiQUOHbbe9om6/bzdaBzWQyIOGzXWM1GotVPLAwYNMH6YuFBp51F5x2lE/"
        "Xr36nS5PhGhr+Pn5s+gyV6Vo+f2NREKRXZEB/jzR4gltcV9aYM+N9NEkEoqa42drpoIXRdeNbrQGQWhoqIetsuUmuojo4v6+utYt0dEKGXxOQy3YjtUU"
        "3YUVuiNmfldDd4NfYcNx0PrL/PHGm2+RN958i3y2fQeLnGpNOuDr/fxn4EdN+fn5u2xTc62piYx9cpLdHLTiNiKiG8arS9+f/+EP9N3c0ZXRjXsGAgDY"
        "vGOHN6/6g5UuWneiNDXiZL3/Acsbpl0J+QuflqrpaPMxKpJT4jtw8CAjvs70QerIdR2Jly9F8I1Z1HDlyH1d+X2pYdCNlNEkEoqsM6JjNwHdrqNudBCx"
        "sbEiKyFeM6JjV/M5AiVAd8RH/aL8ek58bstvdNbZ7oGORHU7Br+DIE32uNZkH8RBOT1fL+ZvbPQYuoHxJROHYRUJRdagoKHWzTt2yIHu1qDd6CBsAR4C"
        "KyEPBAUNvWAjYLvUw/T0tFZFXv7CdSyOR89xM0R8uwbV7/kqgSNh8kXj1rjvvHmv2Eklbrhvs0gosqpUY8uthPTE77QcVDduElRsi5+tWegqa8nVgqbj"
        "s+07WPNwVzovP1rJMevpbhmOPZEWLk9j3NiRMPlj34mv7c7D15mpe4luDG70+RY/P3+SkZk1DejOOupGJ2ElRGATpR8Y+uiwEh53sFtwrmJ9KZGeOHGS"
        "iYlabZETkfMNOh1t6N0V40xVFQthpPc6b94rdgYzvrjvqjUKf7hyOdFnpE3M6HO6cZe1iISilgEDBpy0EuKJbtdRN24GdPdPmJs4xs/P/4qI5xtuixPT"
        "Sh5UL3ZV/M4xEosatyhRdZQg6y5eYr89U1VFPtu+g6zP2cxqSVMuSBubO3b/4xMtDYNsLfiE/1vHErx8Ig8KGsqs321w3+t+fv5EHjRsFtBtvOpGFyBh"
        "biJLO+RVRXRrVXUlhlJR2hUno9yYz/WoPzY27gUSG/cCszrT4ytrz7G0PWr5bY+ryXHwXU00aMOVO4lfxIA+U1sZR3z3Eq2xTS34rXFflWrsP78//0N/"
        "dEde2aHbh9ZJWAkRvBAXJ/z7zp2SceMer9SVlvrZvrJbXP79AqErK7Fr4CWWiJGXmwefPj4Q9/GFRqOBtriYHcOH4fJlpGjm2LUdcYRcoYBUKnV5DP2O"
        "NkiTSqWYyOtHBACjQ0LQu48P+5u2NHEF2uaEf68jh4+wa4AmVyiQsW6tXdNuio0bN2HB/PkQSyRISUlBbx8fJCUlQldahtDx4x0PJwCaxBKJ16Tn/vj8"
        "tk+yP4+NjRXdr32OOoNuAr4J0MUUP1vz7JcHPz9oNpmawQusp83ToqKikZmVyYiXYuPGTYiOioKuXIeCPQXIzMp0ey3D5ctoNNaypmKnKypZgfkf6rk+"
        "vd5Croa5Wq1Gbx8fjA4JgVI1+qae8aPc3QgbNcItURcWFiLy+SlQqlRsc4iOinK5GQFA6PhQ6EpLER4RganTprFjk+cnY9PGjxwPbwbgIVMEvW747tv1"
        "oaGhHiUlJW12l+xGNzoCEQB4ePV825VBi8YHu3IN1V28xAw8tNIHPyCk7uIlsmH7TpK66l2SuWkrCzHs6rHv27Nkw/adZN+Jr8nZujr2eeamrXYF+85U"
        "VbFwTmp8as3q7jj40VWZm7ayZ3VTzKBZJBQRlWrsMSshHja7QzfDcUD3hNw86BySoY8O0+m/+y4Etk6IACdC/9eyNBzYtQ3vrVvrxMl0pWWoMRoRHRON"
        "E0e/wvadOyCVBmDq9GkQBMpQfe4c/p/+MnLnb2S/CR4uxpToMZA9NgRGYy0C+/SGdNQoyPv2dbo5s8kMY02N3WdarRbm+nqIfX1hNNZif+ERXKwxwL9f"
        "IAb0F0Ps68u1Ga2pgVLJdTE019c7tTkFgPVZWUhKSmzXREVOmYrCQ4egVKlQcryEff6S5hXkbbfrwmgFIOj3SL+vlq1ZM3nuzJn/BidOd7dJcUA3AXcB"
        "bKI0SZibqPi8oOCsrV8tSzJXqlRYuHAhao1G1rCaD73BYNdKMy8/H8VaLQQ+ErTIhgIASj74hh1v+dcpNF2vglgigYcXp7tKh8kRPyMSASFKnNEWwVxf"
        "j8qKChiNRjv99GYQHhHBCFmuUCBvz24o5HIn1cAV+DruipUrkZK6CHm5eVi7dq2rjaFFLJEI/hgZOS5n86bSbtG5G7ccvNal2bTfEl8kpCmDHXEDnThx"
        "kqSuepfEJb1K4uITSb/+CtKz53DSs+fwDlmVOzv69VeQSc8lk549h5OxT04iqYtXET8/fxIXn9hhdxbfvURVBzfXbRIJRdYx48Yd4M9rN7pxS2ELsxRa"
        "CfEZM27cEVf6MHWrtHfxn62rI2evXSX7TnxN1n5xnGzYvtOOkG8HEffsOZxMei6ZxMUnsqyis9eukrPXrnbID83vVNFGWxla5zkJvCqh3XCNbhG6ayEE"
        "p7/19PLsoW1paR4HoAW8yKGCA/tduldcwXD5Mo5oj8HYCBzd/RUGDZDiq4N/g3cvUZeJxW3Bv18gACB0vBKz09NQK7DiZMNPeOYROf70yKB2nSMvNw8v"
        "xccDALZu24Zl6enu7t8KQChXKH7cd6jwsSGDBlxBt+7bKrod4l0Lq03ku/ri7JdSAPwGblGyBaiZncB8qW1B3rcvpNIAVNcYMWiAFBe+/RxW4bjbRrye"
        "Xo+i3tQDA0Y8D03meuT17IkPWwSo6N0fjX7+MFjb547Nyc4GAETFxKC2dZ3cCgAtEK4aMmiABdz67CbeVtBNwF2MkpKS5tDQUI+czZu+Chg8eJ1YIvEE"
        "588EAJhNJiQ7NKl2B73BgEDpIITJ+2Hi4xJMmBKB4OFiyBWKW3X7DJ5ejwIAfPxGoeURGXb99ivKfvs3AGD0A39o7ad20JWWsQATZUgIsm3E7AIEgEiu"
        "UFz9/NCXh8BFXFk7/QC/E3QbCG4BbBZTT8P336WPe/xxudlkigNPlM7PzUVGSIhLizQftUYjtEVa1P5ogrHmPCym82j8pQXevW5tLD+fePtHjMHVKZwr"
        "iRJuyMP+CBd5Qi5s+z4y1q4FcMOC3Qr3bRJLJF4tEL4xZNAAfWhoqMfy5cu7Lc9toFsHvkVIS0sTLl++3Lp5x44B/5extkxXWioWSyRCs8nEpJ6S48fb"
        "FSlFfbk1RiOKtcUAAK22CGazGTaXVZfgYZkcD49Wg/QaBgBoCuuH0eO5+wt52B8AMFAABAnbR7x6gwFhEybCbDIhMell6Mp1Ln3JAJoAeAYMHrzc8P13"
        "bwsFAgE4qaVbfG4D3QR8ayEC0PKQXDH6cnV1KWwBCuD5h/kBDR2F3mBArdEIS4MFxdpi5OfntYug/fsFwruXCJHTprGgjUFqNaS+YghlAfj52q+o79mT"
        "e4De3oxoKdpDvACwZPESZKxZA4ALK3Vzb80APAIGD879lZBZlwz667bPu4m3Hegm4FsMGoQQqBiysvbcuf+GbcHS7xOTXm41BrojMJvM0JXrUHmqgiUv"
        "GI1GiH3FkEoDYK6vR0hICGRSKaQymVPwhcHawoiTb6ByJFhX3zl+xue+raAZgIciKOjMP6u+Hcn7vJt4u3FXwRMAxowb9wUvWIH5Pu+FEjp2/mmbH9jl"
        "sMVSu0rsdxXrPGbsOPPmHTvGAN1VNrpx90IIQLR5x46BKtXYb0W8Zmn86KQ7TZh8Am0Xsboh3n0nvm4X8QYFDa3fvGOHCuguUNdZdE/a7YH14QSNYO7M"
        "mRf+NHv2a0qVigZ8EIBzLWkSEu7sHfLAF5nbq+9SmE1mLF/QqpvMCs5dZHk8NHTS3JkzS0NDQz2XL1/e7TLqxt2NtLQ0DwDIyMx62RZa2CzileJx1XLz"
        "To/2cl96/BMRz7XGeemzXkqYmzga6I51vll0G7FuPzwANMuDhr1co//uQ3D+YSEAgVgiQUFBwU0n4XcF2htlRSEXivDUxOdRdvKwu0MIOKPVtZmzXkra"
        "9kn2jtDQUM+SkpKmm7zV3zW6CfjOwBNAk8izx1y0NG+CzQ8KcOVoKs+cvqM3R9EuIjbXQ963L156dQHyNn/Y2pHX5QqFl2rc4/+57ZPs92NjY7127dp1"
        "vbUfdKNtdOvAdwbNoaGhHi1N1zYrx6gOwkbQAGDQ6xE5ZWq746VvJdqj/8r79sXid9e1RrwEQLNYIvFSjXt81rZPst8HIOom3m7c6xAA8Ni8Y8eDvPRD"
        "lkMcl/TqHdd/29KD2+Euos3IyIzo2FW25+4ujdON+wYCAEhLS/tDoGLIEcfytO2tNXUnCPhaU6t1nPm+7oYZ0bHptuftJt5u3F+gVtjNO3YMnREd+3ee"
        "tdYqErquK32nCfhaE1dsoP/gIHeW5uu2II1/JcxNDLE9are1+Rageze8OyCAzScs8uzxZ7Q0b4bNTyyWSEQ5O/LwzITHu+xiHbUwU1Cd2GwyQ5OQ4KoO"
        "tRWAUCyRQD5q5J7EuYlL586cWdltbb516CbguweC2NhYz127dl2XBw3TiGDdYku9awEgXLjiHcGiP89m8cudJcLOgG/MysvNc1VRoxncWhI9LJNf/YOH"
        "KMXw3bcf2L4TgXuGbtwCdBPw3QcRgJaEuYmqw1/8vw+vXbuuBACzyWSVKxTC1xYscFmw/VYQNEtUuHwZRbv3ICc7m58OSHhDJFcoMGz4iC+mxEYvnDtz"
        "ZhUAYVpaGrojrG4tugn47oQIQIuV/P/27h+0iSgMAPj37i5paRCSJpdYSBd7aSRORarE3KghAXXqQf9AE2ihg9AiaG0Gszo4SDs5VEwotKEKLpWibhbX"
        "dKu0KmKINC1enCrSpPcc7l05j6Q2Qm1rvh88QiAJB8fle/++91FH9/kLg58/rN8HgE4wHQpgVDa42NNTM7PI7G82ZQDo6YqZF0uQffTQnFVkbAHlAfQ0"
        "wTNOZyYcvvJqLvv0OUdIFY+BRU3PvLnfJwWk3kuXC2ySaJe3VEI0qtvfnbxH5xdy9OXysn6iJWsNTVhtbtL5hZxRpFtjs8kV6wmboujd6e8feDc0nOyr"
        "d93o6GEEPtkIi2aVjUKx80Y0OltWv0XLqgrtbne1rKp1Z3aNukwAsF9d4RBoPp+nZVU1oqzNnIgvBQJAOG6tqsG0cmts5cH4xHv2PV5RFHi2uKgBIZjL"
        "i5AFDwCwUSi2R2LxSVH0Fi3rrVVrVG6g7bHvV6xRXRS9PwV766xgb52JxOK3n+RyQY3SNtN1EczhRegQ2MHxAACQGBl1ScFQqkZBsD1Tl1c7oFV5S1Fy"
        "9sBSv9+/xttapqRgaCIxMlrv+Eseu8oINUijlJjT7+5MPe4dGk6mzgW63/Acv91I5DUefrutZTV87epSJBbvS81M11psFgBAkGVZSKfTnPmPBB0/vBmn"
        "EwG9W22e6e2QgqGIp8MT3f5acrpdruugj2PN95hyDjtoP3Zfq+XvX3YonRsbHFitsdQjyLIMH7skrZTN4DIQQkeBjT+N9huNUlGj1MNeRfP7Gj/FK4rC"
        "43gWoePDAQDPuth/ehA59rn9EqjodMKb9586aKzK4VIPQgghhBBCCCGEThmcxGo+RFGUuruoVtocFNd+EULoH8AI3DwIANCziaSva2vrJtTYpQUA5JPP"
        "t17KZt6CvkaMkfiE+wU35FwbrKR4vAAAAABJRU5ErkJggg=="
    ),
    "trollface_fifth.png": (
        "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"
        "FYFcwdLi/w94//1SjRb/ZAAAAABJRU5ErkJggg=="
    ),
}


def _write_embedded_assets():
    """
    כותב את קבצי התמונה (כדור, טרול-פייס רגיל, טרול-פייס זהב) לדיסק
    מתוך המחרוזות המוטמעות למעלה - בכל הרצה מחדש, כדי שלעולם לא יהיו
    קבצים ישנים/חסרים בתיקייה. ככה אין יותר תלות בניהול קבצים ידני.
    """
    for filename, b64_data in _EMBEDDED_ASSETS_B64.items():
        path = os.path.join(HERE, filename)
        try:
            raw = base64.b64decode(b64_data)
            with open(path, "wb") as fh:
                fh.write(raw)
        except Exception as exc:
            print(f"[roll_the_ball] אזהרה: נכשלה כתיבת {filename}: {exc}")


_write_embedded_assets()


def lane_center_x(lane_index):
    return -TRACK_HALF_WIDTH + LANE_WIDTH * (lane_index + 0.5)


def load_highscore():
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("highscore", 0)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return 0


def save_highscore(value):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"highscore": value}, f)
    except OSError:
        pass


TILE_COLORS = [color.rgb32(255, 170, 60), color.rgb32(255, 190, 100)]


def _make_ramp_wedge_mesh(half_width, height, length):
    """
    בונה גיאומטריית 'טריז' אמיתית לרמפה: שטוחה וצמודה לגובה 0 בקצה האחורי
    (הכניסה) ומטפסת בקו ישר לגובה מלא בקצה הקדמי, בלי שום 'עובי' שמתנפח
    הצידה כשמסובבים קובייה רגילה - זה מה שגרם לכדור להיראות בולע בתוך
    הרמפה. כל הפאות מוגדרות במפורש (בלי אינדוקסים) כדי שהתאורה תהיה חדה
    בקצוות, בדיוק כמו קוביה רגילה.
    """
    w = half_width
    verts = []

    def add_tri(a, b, c):
        verts.extend([a, b, c])

    # תחתית - שטוחה על הרצפה מהכניסה ועד היציאה
    add_tri((-w, 0, 0), (-w, 0, length), (w, 0, length))
    add_tri((-w, 0, 0), (w, 0, length), (w, 0, 0))
    # השיפוע העליון - מהקצה האחורי (גובה 0) לקצה הקדמי (גובה מלא)
    add_tri((-w, 0, 0), (w, 0, 0), (w, height, length))
    add_tri((-w, 0, 0), (w, height, length), (-w, height, length))
    # דופן קדמית (אנכית) בקצה שממנו קופצים
    add_tri((-w, 0, length), (-w, height, length), (w, height, length))
    add_tri((-w, 0, length), (w, height, length), (w, 0, length))
    # שני צדדים משולשים
    add_tri((-w, 0, 0), (-w, height, length), (-w, 0, length))
    add_tri((w, 0, 0), (w, 0, length), (w, height, length))

    mesh = Mesh(vertices=verts, mode="triangle")
    mesh.generate_normals()
    return mesh


class Row:
    """שורה אחת של המסלול (בעולם התלת-ממדי, לאורך ציר Z)."""

    __slots__ = ("index", "world_z", "lanes", "judged", "entities", "coin_entity")

    def __init__(self, index, lanes):
        self.index = index
        self.world_z = index * ROW_DEPTH
        self.lanes = lanes
        self.judged = False
        self.entities = []  # כל האנטיטיז שיש להשמיד כשמנקים את השורה
        self.coin_entity = None  # רפרנס ישיר למטבע (אם יש), לאיסוף נקי

    def spawn(self):
        tile_color = TILE_COLORS[self.index % 2]
        for lane_i, state in enumerate(self.lanes):
            if state == "gap":
                continue  # בור ריק - שמיים נראים דרכו, שום דבר לא מצויר

            x = lane_center_x(lane_i)

            if state == "lava":
                # בריכת לבה שקועה מתחת לגובה השביל - זוהרת, לא ניתן לדרוך עליה.
                lava = Entity(
                    model="cube",
                    color=color.rgb32(255, 90, 20),
                    scale=(LANE_WIDTH * 0.92, 0.5, ROW_DEPTH * 0.9),
                    position=(x, LAVA_Y, self.world_z),
                )
                lava.glow_pulse = random.uniform(0, 6.28)
                self.entities.append(lava)
                continue

            if state == "ramp":
                # תיקון חשוב: הקפיצה בפועל (airborne=True) מופעלת בקוד בדיוק
                # כשהכדור חוצה את *מרכז* השורה (ראו _check_collisions), לא את
                # הכניסה אליה. בנוסף, קובייה רגילה שמסובבים (rotation_x) כדי
                # לדמות שיפוע מקבלת "עובי" מנופח שבולט אחורה לתוך הכניסה -
                # זה מה שגרם לכדור להיראות בולע בתוך הרמפה. הפתרון המלא:
                # חצי ראשון של השורה נשאר קרש שטוח רגיל (הכדור עוד לא קופץ),
                # וההרמה עצמה היא גיאומטריית "טריז" אמיתית שמתחילה שטוחה
                # לגמרי (גובה 0) בדיוק במרכז השורה - מסונכרן עם רגע הקפיצה -
                # ומטפסת בקו ישר, בלי שום נפח שבולט אחורה.
                runway = Entity(
                    model="cube",
                    color=color.rgb32(70, 150, 230),
                    scale=(LANE_WIDTH * 0.92, 0.5, ROW_DEPTH * 0.5),
                    position=(x, TILE_Y, self.world_z - ROW_DEPTH * 0.25),
                )
                self.entities.append(runway)

                ramp_len = ROW_DEPTH * 0.55
                ramp_height = 1.0
                ramp = Entity(
                    model=_make_ramp_wedge_mesh(LANE_WIDTH * 0.46, ramp_height, ramp_len),
                    color=color.rgb32(70, 150, 230),
                    position=(x, 0.0, self.world_z),
                )
                # פס צהוב בקצה העליון (הרחוק) של הרמפה - "בן" של הרמפה, כדי
                # שיזוז איתה אוטומטית ויישאר תמיד בדיוק בקצה שלה.
                stripe = Entity(
                    parent=ramp,
                    model="cube",
                    color=color.rgb32(250, 220, 40),
                    scale=(LANE_WIDTH * 0.95, ramp_height * 0.3, 0.16),
                    position=(0, ramp_height * 0.85, ramp_len - 0.08),
                )
                self.entities.append(ramp)  # stripe הוא ילד של ramp - נהרס איתו אוטומטית
                continue

            tile = Entity(
                model="cube",
                color=tile_color,
                scale=(LANE_WIDTH * 0.92, 0.5, ROW_DEPTH * 0.9),
                position=(x, TILE_Y, self.world_z),
            )
            self.entities.append(tile)

            if state == "obstacle":
                ob = Entity(
                    model="diamond",
                    color=color.rgb32(210, 40, 40),
                    scale=(0.85, 1.1, 0.85),
                    position=(x, 0.45, self.world_z),
                )
                ob.spin_speed = 70
                self.entities.append(ob)
            elif state == "coin":
                coin = Entity(
                    model="sphere",
                    color=color.rgb32(255, 210, 40),
                    scale=(0.4, 0.4, 0.12),
                    position=(x, 0.55, self.world_z),
                )
                coin.spin_speed = 140
                self.entities.append(coin)
                self.coin_entity = coin

    def despawn(self):
        for e in self.entities:
            destroy(e)
        self.entities.clear()


class TrackGenerator:
    def __init__(self):
        self.next_index = 0
        self.prev_solid = set(range(LANES))
        self.rows = []
        # תור של override-ים לשורות הקרובות: כל איבר הוא dict {lane_index: state}
        # שדורס את מה שהיה נוצר אקראית עבור אותה שורה, כדי לבנות רצף רמפה->לבה->נחיתה.
        self.hazard_queue = deque()
        self.hazard_cooldown = 6  # לא לפני כמה שורות ראשונות, שיהיה זמן להתחמם
        for _ in range(3):
            self._add_safe_row()

    def _add_safe_row(self):
        row = Row(self.next_index, ["solid"] * LANES)
        self.rows.append(row)
        self.prev_solid = set(range(LANES))
        self.next_index += 1
        return row

    def _maybe_schedule_hazard(self, difficulty):
        if self.hazard_queue or self.hazard_cooldown > 0:
            return
        chance = 0.10 + 0.10 * difficulty
        if random.random() >= chance:
            return
        lane = random.randrange(LANES)
        self.hazard_queue.append({lane: "ramp"})
        self.hazard_queue.append({lane: "lava"})
        self.hazard_queue.append({lane: "solid"})  # רצפת נחיתה בטוחה
        self.hazard_cooldown = HAZARD_MIN_GAP_ROWS

    def generate_row(self, difficulty):
        if self.hazard_cooldown > 0:
            self.hazard_cooldown -= 1

        forced = self.hazard_queue.popleft() if self.hazard_queue else {}

        gap_chance = 0.15 + 0.35 * difficulty
        obstacle_chance = 0.08 + 0.20 * difficulty
        coin_chance = 0.35

        lanes = ["solid"] * LANES

        # בוחרים מסלול בטוח מובטח מבין אלה שלא נדרסים ע"י הרצף המיוחד
        safe_candidates = [i for i in self.prev_solid if i not in forced] or \
            [i for i in range(LANES) if i not in forced]
        guaranteed_safe = random.choice(safe_candidates) if safe_candidates else random.randrange(LANES)

        for i in range(LANES):
            if i == guaranteed_safe or i in forced:
                continue
            if random.random() < gap_chance:
                lanes[i] = "gap"
            elif random.random() < obstacle_chance:
                lanes[i] = "obstacle"

        for i in range(LANES):
            if lanes[i] == "solid" and i not in forced and random.random() < coin_chance:
                lanes[i] = "coin"

        for lane_i, state in forced.items():
            lanes[lane_i] = state

        if not forced:
            self._maybe_schedule_hazard(difficulty)

        row = Row(self.next_index, lanes)
        self.rows.append(row)
        self.next_index += 1
        # 'ramp' נחשב עמיד עמידה (דורכים עליו לפני הקפיצה), לכן גם הוא "בטוח" להמשכיות
        self.prev_solid = {i for i, v in enumerate(lanes) if v in ("solid", "coin", "ramp")}
        return row


class RollingBallGame:
    def __init__(self):
        Sky(texture="sky_sunset")
        DirectionalLight(shadows=False, rotation=(45, -35, 0), color=color.rgb32(255, 244, 220))
        AmbientLight(color=color.rgba32(150, 165, 200, 90))

        camera.fov = 62

        # Ursina מחפש טקסטורות לפי שם-קובץ בתיקיית הסקריפט עצמו (asset_folder),
        # ולכן מעבירים רק את שם הקובץ, לא נתיב מוחלט.
        self.ball = Entity(
            model="sphere",
            texture="ball_texture.png" if os.path.exists(BALL_TEXTURE) else None,
            color=color.white,
            scale=BALL_RADIUS * 2,
            position=(0, BALL_START_Y, 0),
        )

        self.score_text = Text(text="Score: 0", position=(-0.63, 0.45), scale=1.6, parent=camera.ui)
        self.coin_text = Text(text="Coins: 0", position=(-0.63, 0.39), scale=1.3, parent=camera.ui)
        self.best_text = Text(
            text="Best: 0", position=(0.66, 0.45), origin=(0.5, 0.5), scale=1.3, parent=camera.ui
        )
        self.controls_hint = Text(
            text="Hold UP / W to speed up",
            position=(-0.63, -0.47),
            scale=1.0,
            color=color.rgba32(255, 255, 255, 190),
            parent=camera.ui,
        )
        self.msg_text = Text(text="", origin=(0, 0), position=(0, 0.05), scale=2.2, color=color.white)
        self.hint_text = Text(text="", origin=(0, 0), position=(0, -0.08), scale=1.2, color=color.white)

        # טרול-פייס שקופץ על כל המסך אם נופלים במשך יותר מדי זמן (בדיחה) - מוסתר כברירת מחדל.
        # התמונות עצמן מוטמעות בקוד (למעלה) ונכתבות לדיסק אוטומטית בכל הרצה,
        # אז אין יותר צורך לבדוק אם הקובץ קיים - הוא תמיד קיים ותמיד עדכני.
        self.troll_entity = Entity(
            model="quad",
            texture="trollface.png",
            parent=camera.ui,
            position=(0, 0),
            scale=0.5,
            enabled=False,
        )
        self.troll_shown = False
        self.fall_count = 0  # סופר נפילות לאורך כל ההרצה (לא מתאפס בריסטארט) - לבחירת גרסת הטרול-פייס

        self.highscore = load_highscore()
        self.clouds = []
        self._spawn_clouds_initial()

        self.reset()

    # ------------------------------------------------------------------
    def _spawn_cloud(self, z):
        side = random.choice([-1, 1])
        x = side * random.uniform(9, 18)
        y = random.uniform(2, 7)
        puff_count = random.randint(3, 5)
        group = []
        for _ in range(puff_count):
            puff = Entity(
                model="sphere",
                color=color.rgba32(255, 255, 255, 235),
                scale=random.uniform(1.4, 2.6),
                position=(
                    x + random.uniform(-1.5, 1.5),
                    y + random.uniform(-0.4, 0.4),
                    z + random.uniform(-1.5, 1.5),
                ),
            )
            group.append(puff)
        self.clouds.append((z, group))

    def _spawn_clouds_initial(self):
        for i in range(6):
            self._spawn_cloud(i * 8)

    def _update_clouds(self):
        # לייצר עננים חדשים קדימה ולנקות ישנים מאחור
        max_z = max((c[0] for c in self.clouds), default=0)
        if self.ball.z + 60 > max_z:
            self._spawn_cloud(max_z + random.uniform(6, 10))
        keep = []
        for z, group in self.clouds:
            if z - self.ball.z < -DESPAWN_BEHIND - 20:
                for e in group:
                    destroy(e)
            else:
                keep.append((z, group))
        self.clouds = keep

    # ------------------------------------------------------------------
    def reset(self):
        if hasattr(self, "track"):
            for row in self.track.rows:
                row.despawn()

        self.track = TrackGenerator()
        for row in self.track.rows:
            row.spawn()

        self.ball.position = (0, BALL_START_Y, 0)
        self.ball.rotation = (0, 0, 0)
        self.lane = LANES // 2
        self.target_lane = self.lane

        self.speed = SLOW_SPEED
        self.elapsed = 0.0
        self.difficulty = 0.0
        self.score = 0
        self.coins = 0
        self.state = "playing"
        self.game_over_timer = 0.0
        self.fall_velocity = 0.0
        self.airborne = False
        self.vertical_velocity = 0.0

        self.msg_text.text = ""
        self.hint_text.text = ""
        self.troll_entity.enabled = False
        self.troll_shown = False

        # למקם את המצלמה מיד במקום הנכון אחרי מוות/נפילה ארוכה, במקום לתת לה
        # "לטפס" לאט חזרה מלמטה - זה מה שגרם לפריים הפוך/מוזר מיד אחרי ריסטארט.
        cam_offset = Vec3(0, 3.6, -9.5)
        camera.position = Vec3(self.ball.x * 0.55, self.ball.y, self.ball.z) + cam_offset
        camera.look_at(Vec3(self.ball.x * 0.55, self.ball.y + 0.3, self.ball.z + 4))

    # ------------------------------------------------------------------
    def move_left(self):
        if self.state == "playing":
            self.target_lane = max(0, self.target_lane - 1)

    def move_right(self):
        if self.state == "playing":
            self.target_lane = min(LANES - 1, self.target_lane + 1)

    def handle_input(self, key):
        if key == "escape":
            application.quit()
        if key in ("left arrow", "a"):
            self.move_left()
        elif key in ("right arrow", "d"):
            self.move_right()
        elif key == "space" and self.state == "gameover":
            self.reset()

    # ------------------------------------------------------------------
    def _check_collisions(self):
        for row in self.track.rows:
            if row.judged:
                continue
            if row.world_z <= self.ball.z:
                row.judged = True
                state = row.lanes[self.lane]
                if state in ("gap", "obstacle"):
                    self._die()
                elif state == "lava":
                    # לבה בוערת - שורדים רק אם באוויר (קפצנו על רמפה קודם)
                    if not self.airborne or (self.ball.y - BALL_START_Y) < AIRBORNE_MARGIN:
                        self._die()
                elif state == "ramp":
                    self.airborne = True
                    self.vertical_velocity = JUMP_IMPULSE
                elif state == "coin":
                    self.coins += 1
                    if row.coin_entity is not None:
                        if row.coin_entity in row.entities:
                            row.entities.remove(row.coin_entity)
                        destroy(row.coin_entity)
                        row.coin_entity = None

    def _die(self):
        if self.state != "playing":
            return
        self.state = "gameover"
        self.fall_velocity = 1.0
        self.fall_count += 1
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)
        self.msg_text.text = "You Fell!"
        self.msg_text.color = color.white

    # ------------------------------------------------------------------
    def update(self):
        dt = time.dt

        if self.state == "playing":
            self.elapsed += dt
            self.difficulty = min(1.0, self.elapsed / 60.0)

            boosting = held_keys["up arrow"] or held_keys["w"]
            target_speed = (BOOST_SPEED if boosting else SLOW_SPEED) + 3.0 * self.difficulty
            self.speed += (target_speed - self.speed) * min(1.0, dt * BOOST_LERP)

            self.ball.z += self.speed * dt
            target_x = lane_center_x(self.target_lane)
            self.ball.x += (target_x - self.ball.x) * min(1.0, dt * 10)
            self.lane = self.target_lane

            # סיבוב הכדור בהתאם לתנועה (קדימה + הצידה) - זה מה שמראה שהוא "מתגלגל"
            self.ball.rotation_x -= (self.speed / BALL_RADIUS) * dt * (180 / math.pi)
            self.ball.rotation_z += ((target_x - self.ball.x) * -6) * dt * (180 / math.pi)

            while self.track.rows[-1].world_z < self.ball.z + SPAWN_AHEAD_ROWS * ROW_DEPTH:
                new_row = self.track.generate_row(self.difficulty)
                new_row.spawn()

            self._check_collisions()

            if self.airborne:
                self.vertical_velocity -= JUMP_GRAVITY * dt
                self.ball.y += self.vertical_velocity * dt
                if self.ball.y <= BALL_START_Y:
                    self.ball.y = BALL_START_Y
                    self.airborne = False
                    self.vertical_velocity = 0.0

            keep_rows = []
            for row in self.track.rows:
                if row.world_z - self.ball.z < -DESPAWN_BEHIND:
                    row.despawn()
                else:
                    keep_rows.append(row)
            self.track.rows = keep_rows

            self.score = int(self.ball.z * 3.3) + self.coins * 5
            self.score_text.text = f"Score: {self.score}"
            self.coin_text.text = f"Coins: {self.coins}"
            self.best_text.text = f"Best: {self.highscore}"

        else:
            self.game_over_timer += dt
            self.fall_velocity += 9.0 * dt
            self.ball.y -= self.fall_velocity * dt
            self.ball.rotation_x -= 260 * dt
            if self.game_over_timer > 0.6:
                blink = int(self.game_over_timer * 2) % 2 == 0
                self.hint_text.text = "Press SPACE to restart" if blink else ""

            # בדיחה: ברגע שנופלים (מוות) - טרול-פייס קופץ מיד למסך, נשאר
            # שתי שניות ואז נעלם. נפילה 1 = רגיל, נפילה 2 = זהב, נפילה 3 =
            # עיניים אדומות + אצבע מצביעה, נפילה 4 = הפרצוף השחור-לבן הזועם,
            # נפילה 5 ואילך = הפרצוף הטורקיז.
            if self.game_over_timer > TROLLFACE_DELAY and not self.troll_shown:
                self.troll_shown = True
                if self.fall_count >= 5:
                    texture_name, label = "trollface_fifth.png", "חמישי"
                elif self.fall_count == 4:
                    texture_name, label = "trollface_fourth.png", "רביעי"
                elif self.fall_count == 3:
                    texture_name, label = "trollface_third.png", "שלישי"
                elif self.fall_count == 2:
                    texture_name, label = "trollface_gold.png", "זהב"
                else:
                    texture_name, label = "trollface.png", "רגיל"
                self.troll_entity.texture = texture_name
                self.troll_entity.enabled = True
                print(f"[roll_the_ball] נפילה מספר {self.fall_count} -> {label}")
            elif self.troll_shown and self.game_over_timer > TROLLFACE_DELAY + TROLLFACE_DURATION:
                self.troll_entity.enabled = False

        self._update_spinners(dt)
        self._update_clouds()
        self._update_camera(dt)

    def _update_spinners(self, dt):
        for row in self.track.rows:
            for e in row.entities:
                spin = getattr(e, "spin_speed", None)
                if spin:
                    e.rotation_y += spin * dt

                pulse = getattr(e, "glow_pulse", None)
                if pulse is not None:
                    pulse += dt * 4.0
                    e.glow_pulse = pulse
                    t = 0.5 + 0.5 * math.sin(pulse)
                    e.color = color.rgb32(
                        255,
                        int(70 + 60 * t),
                        int(10 + 20 * t),
                    )

    def _update_camera(self, dt):
        cam_offset = Vec3(0, 3.6, -9.5)
        desired = Vec3(self.ball.x * 0.55, self.ball.y, self.ball.z) + cam_offset
        camera.position = camera.position + (desired - camera.position) * min(1.0, dt * 6)
        look_target = Vec3(self.ball.x * 0.55, self.ball.y + 0.3, self.ball.z + 4)
        camera.look_at(look_target)


# --------------------------------------------------------------------------
# Ursina קורא לפונקציות update()/input() האלה מתוך המודול __main__ בעצמו,
# ולכן הן חייבות להיות ברמת המודול (לא מקוננות בתוך פונקציה אחרת).
# --------------------------------------------------------------------------
game = None


def update():
    if game is not None:
        game.update()


def input(key):
    if game is not None:
        game.handle_input(key)


if __name__ == "__main__":
    app = Ursina(title="גלגלו את הכדור 3D - Sky Escape", borderless=False)
    window.color = color.rgb32(140, 190, 235)
    game = RollingBallGame()
    app.run()