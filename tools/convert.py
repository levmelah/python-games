# -*- coding: utf-8 -*-
"""ממיר משחק pygame לגרסת דפדפן (pygbag).

מה הוא עושה:
  1. מוצא את לולאת המשחק הראשית (הלולאה שבה pygame.event.get).
  2. מכניס בתחילת הלולאה await asyncio.sleep(0) - בלי זה הדפדפן נתקע.
  3. הופך ל-async כל פונקציה שמכילה לולאה כזו, וגם כל פונקציה שקוראת לה.
  4. מוסיף await בכל קריאה לפונקציה שהפכה ל-async.
  5. עוטף את נקודת ההתחלה ב-asyncio.run.
  6. מוסיף גופן חלופי, כי בדפדפן אין גופני מערכת.
"""
import ast
import os
import re
import sys

SYSFONT_PATCH = '''

# --- pygbag: בדפדפן אין גופני מערכת, ולכן נופלים לגופן המובנה של pygame ---
# הכול בתוך try, כדי שגם אם זה נכשל המשחק עצמו ימשיך לעבוד
import pygame as _pgb_pygame

try:
    _pgb_orig_sysfont = _pgb_pygame.font.SysFont

    def _pgb_safe_sysfont(name, size, bold=False, italic=False):
        try:
            f = _pgb_orig_sysfont(name, size, bold, italic)
            if f is not None:
                return f
        except Exception:
            pass
        return _pgb_pygame.font.Font(None, int(size * 1.3))

    _pgb_pygame.font.SysFont = _pgb_safe_sysfont
except Exception as _pgb_err:
    print("pygbag: font fallback not installed:", _pgb_err)
# --- end pygbag ---
'''

AWAIT_COMMENT = "  # pygbag: מחזיר שליטה לדפדפן בכל פריים"


class Bail(Exception):
    pass


# ---------- עזרי AST ----------

def is_event_get(n):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr in ("get", "wait")
            and isinstance(n.func.value, ast.Attribute)
            and n.func.value.attr == "event")


def imports_pygame(n):
    for m in ast.walk(n):
        if isinstance(m, ast.Import) and any(a.name.split(".")[0] == "pygame"
                                             for a in m.names):
            return True
        if isinstance(m, ast.ImportFrom) and (m.module or "").split(".")[0] == "pygame":
            return True
    return False


SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def own_scope_nodes(node):
    """כל הצמתים של הצומת, בלי להיכנס לפונקציות/מחלקות מקוננות."""
    out = []
    stack = list(ast.iter_child_nodes(node))
    while stack:
        n = stack.pop()
        out.append(n)
        if not isinstance(n, SCOPE_NODES):
            stack.extend(ast.iter_child_nodes(n))
    return out


def assigned_names(node):
    """שמות שהלולאה כותבת אליהם - צריכים global אחרי שנעטוף אותה בפונקציה."""
    names = set()
    for n in own_scope_nodes(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            names.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                names.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            names.add(n.name)
    return names


# ---------- הממיר ----------

class Converter:
    def __init__(self, path):
        self.path = path
        self.src = open(path, encoding="utf-8").read()
        self.lines = self.src.split("\n")
        self.tree = ast.parse(self.src)
        self.parent = {}
        for n in ast.walk(self.tree):
            for c in ast.iter_child_nodes(n):
                self.parent[c] = n
        # (class_name|None, func_name) -> FunctionDef
        self.funcs = {}
        self.func_of = {}      # FunctionDef -> key
        self.cls_of = {}       # FunctionDef -> ClassDef|None
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                p = self.parent.get(n)
                cls = p.name if isinstance(p, ast.ClassDef) else None
                key = (cls, n.name)
                self.funcs[key] = n
                self.func_of[n] = key
                self.cls_of[n] = p if isinstance(p, ast.ClassDef) else None
        # שמות מחלקות, ומשתנים שמחזיקים מופע שלהן: game = FPSGame()
        self.classes = {n.name for n in ast.walk(self.tree)
                        if isinstance(n, ast.ClassDef)}
        self.var_class = {}
        for n in ast.walk(self.tree):
            if (isinstance(n, ast.Assign) and len(n.targets) == 1
                    and isinstance(n.targets[0], ast.Name)
                    and isinstance(n.value, ast.Call)
                    and isinstance(n.value.func, ast.Name)
                    and n.value.func.id in self.classes):
                self.var_class[n.targets[0].id] = n.value.func.id
        self.edits = []        # (lineno, col, text)  -  הכנסת טקסט
        self.line_subs = []    # (lineno, regex, repl)
        self.inserts = []      # (after_lineno, text)
        self.run_line = None   # השורה שבה asyncio.run

    # --- עזרה ---
    def indent_of(self, lineno):
        line = self.lines[lineno - 1]
        return line[:len(line) - len(line.lstrip())]

    def enclosing_func(self, node):
        p = node
        while p in self.parent:
            p = self.parent[p]
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return p
            if isinstance(p, ast.ClassDef):
                return None
        return None

    # --- שלב 1: לולאות ---
    def find_loops(self):
        loops = [n for n in ast.walk(self.tree)
                 if isinstance(n, (ast.While, ast.For))
                 and any(is_event_get(m) for m in ast.walk(n))]
        outer = [L for L in loops
                 if not any(L is not M and L in list(ast.walk(M)) for M in loops)]
        if not outer:
            raise Bail("לא נמצאה לולאת משחק (pygame.event.get)")
        return outer

    # --- שלב 2: אילו פונקציות צריכות להיות async ---
    def resolve_call(self, call, in_func):
        """מחזיר את המפתח של הפונקציה שנקראת, או None אם אי אפשר לדעת."""
        f = call.func
        if isinstance(f, ast.Name):
            if (None, f.id) in self.funcs:
                return (None, f.id)
            return None
        if isinstance(f, ast.Attribute):
            v = f.value
            if isinstance(v, ast.Name) and v.id == "self" and in_func is not None:
                cls = self.cls_of.get(in_func)
                if cls is not None and (cls.name, f.attr) in self.funcs:
                    return (cls.name, f.attr)
            if isinstance(v, ast.Call) and isinstance(v.func, ast.Name):
                # Game().run()
                if (v.func.id, f.attr) in self.funcs:
                    return (v.func.id, f.attr)
            if isinstance(v, ast.Name) and (v.id, f.attr) in self.funcs:
                return (v.id, f.attr)
            if isinstance(v, ast.Name) and v.id in self.var_class:
                key = (self.var_class[v.id], f.attr)
                if key in self.funcs:
                    return key
        return None

    def compute_async(self, loops):
        need = set()
        for L in loops:
            fn = self.enclosing_func(L)
            if fn is not None:
                need.add(self.func_of[fn])
        changed = True
        while changed:
            changed = False
            for key, fn in self.funcs.items():
                if key in need:
                    continue
                for n in ast.walk(fn):
                    if isinstance(n, ast.Call) and self.resolve_call(n, fn) in need:
                        need.add(key)
                        changed = True
                        break
        return need

    # --- הפעלה ---
    def run(self):
        loops = self.find_loops()
        need = self.compute_async(loops)

        # 2a. await בתחילת כל לולאה
        # לולאה שיושבת ברמת המודול תיכנס לתוך פונקציה, ולכן תוזח ב-4 רווחים
        at_module = {id(L) for L in loops if self.enclosing_func(L) is None}
        for L in loops:
            first = L.body[0]
            ind = self.indent_of(first.lineno)
            if id(L) in at_module:
                ind = "    " + ind
            self.inserts.append((first.lineno - 1,
                                 ind + "await asyncio.sleep(0)" + AWAIT_COMMENT))

        # 2b. def -> async def
        for key in need:
            fn = self.funcs[key]
            ln = fn.lineno
            while not re.match(r"\s*(async\s+)?def\b", self.lines[ln - 1]):
                ln += 1
            self.line_subs.append((ln, r"(\s*)def\b", r"\1async def"))

        # 2c. await בכל קריאה לפונקציה async
        module_entry = []
        for n in ast.walk(self.tree):
            if not isinstance(n, ast.Call):
                continue
            host = self.enclosing_func(n)
            key = self.resolve_call(n, host)
            if key is None or key not in need:
                continue
            if host is not None and self.func_of[host] in need:
                self.edits.append((n.lineno, n.col_offset, "await "))
            elif host is None:
                module_entry.append(n)

        # 2d. נקודת ההתחלה -> asyncio.run(...)
        loops_at_module = [L for L in loops if self.enclosing_func(L) is None]
        if loops_at_module:
            if len(loops_at_module) > 1:
                raise Bail("יותר מלולאה אחת ברמת המודול")
            self.wrap_module_loop(loops_at_module[0])
        else:
            if not module_entry:
                raise Bail("לא נמצאה קריאה שמתחילה את המשחק")
            if len(module_entry) > 1:
                raise Bail("נמצאו %d נקודות התחלה" % len(module_entry))
            c = module_entry[0]
            self.edits.append((c.lineno, c.col_offset, "asyncio.run("))
            self.edits.append((c.end_lineno, c.end_col_offset, ")"))
            self.run_line = c.end_lineno

        # 2d-bis. בדפדפן asyncio.run חוזר מיד, ולכן כל פקודה שאחריה
        # תרוץ לפני שהמשחק בכלל התחיל - למשל pygame.quit() שסוגר את החלון.
        self.neutralize_after_run()

        # 2e. גופן חלופי
        host = None
        for n in self.tree.body:
            if imports_pygame(n):
                host = n
                break
        if host is None:
            raise Bail("לא נמצא import pygame")
        self.inserts.append((host.end_lineno, SYSFONT_PATCH))

        return self.apply()

    def neutralize_after_run(self):
        """מנטרל כל פקודה שרצה אחרי asyncio.run - בדפדפן היא תרוץ מוקדם מדי."""
        after = self.run_line
        for i in range(after, len(self.lines)):
            line = self.lines[i]
            body = line.strip()
            if not body or body.startswith("#"):
                continue
            if line[:1] not in (" ", "\t") and (
                    body.startswith("def ") or body.startswith("class ")
                    or body.startswith("async def ")):
                raise Bail("יש הגדרת פונקציה אחרי נקודת ההתחלה (שורה %d)" % (i + 1))
            ind = line[:len(line) - len(line.lstrip())]
            self.line_subs.append(
                (i + 1, r"^.*$",
                 lambda m, ind=ind, body=body:
                     ind + "# pygbag: " + body + "   <- לא רץ בדפדפן"))

    def wrap_module_loop(self, L):
        """מעביר לולאה שיושבת ברמת המודול לתוך async def."""
        start, end = L.lineno, L.end_lineno
        names = sorted(assigned_names(L))
        head = ["", "", "async def _pgb_main():"]
        if names:
            head.append("    # global - כי הלולאה הייתה קודם ברמת המודול")
            for i in range(0, len(names), 6):
                head.append("    global " + ", ".join(names[i:i + 6]))
        self.inserts.append((start - 1, "\n".join(head)))
        for ln in range(start, end + 1):
            if self.lines[ln - 1].strip():
                self.line_subs.append((ln, r"^", "    "))
        self.inserts.append((end, "\n\nasyncio.run(_pgb_main())"))
        self.run_line = end

    def apply(self):
        out = list(self.lines)
        # החלפות בתוך שורה (מהסוף להתחלה בכל שורה)
        for lineno, pat, repl in self.line_subs:
            out[lineno - 1] = re.sub(pat, repl, out[lineno - 1], count=1)
        by_line = {}
        for lineno, col, text in self.edits:
            by_line.setdefault(lineno, []).append((col, text))
        for lineno, items in by_line.items():
            s = out[lineno - 1]
            extra = len(s) - len(self.lines[lineno - 1])   # תיקון בגלל line_subs
            for col, text in sorted(items, key=lambda t: -t[0]):
                c = col + extra
                s = s[:c] + text + s[c:]
            out[lineno - 1] = s
        for after, text in sorted(self.inserts, key=lambda t: -t[0]):
            out.insert(after, text)
        out.insert(0, "import asyncio  # pygbag")
        res = "\n".join(out)
        compile(res, self.path, "exec")
        return res


def convert(src, dst):
    res = Converter(src).run()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(res)


if __name__ == "__main__":
    try:
        convert(sys.argv[1], sys.argv[2])
        print("OK|%s|" % sys.argv[1])
    except Bail as e:
        print("SKIP|%s|%s" % (sys.argv[1], e))
    except SyntaxError as e:
        print("FAIL|%s|תוצאה לא תקינה: %s (שורה %s)" % (sys.argv[1], e.msg, e.lineno))
    except Exception as e:
        print("FAIL|%s|%s: %s" % (sys.argv[1], type(e).__name__, e))
