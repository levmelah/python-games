from tkinter import *  # імпортуємо всі інструменти з бібліотеки tkinter для створення вікон

root = Tk()                        # створюємо головне вікно програми
root.title("מחשבון")               # задаємо назву вікна
#root.resizable(False, False)       # забороняємо змінювати розмір вікна (ширина і висота)
root.configure(bg="#ff7b00")       # задаємо колір фону вікна (синій)

display_var = StringVar(value="0")  # спеціальна змінна tkinter — автоматично оновлює текст на екрані

display = Entry(root, textvariable=display_var, font=("Arial", 32, "bold"),
                bg="#FFBB00", fg="white", bd=0, justify="right",
                insertbackground="white")
# Entry — поле тексту (екран калькулятора)
# textvariable=display_var — поле пов'язане зі змінною, зміна змінної = зміна тексту
# font — шрифт Arial, розмір 32, жирний
# bg — колір фону екрана; fg="white" — білий текст
# bd=0 — без рамки; justify="right" — текст по правому краю
display.grid(row=0, column=0, columnspan=4, padx=15, pady=(15, 8), ipady=18, sticky="ew")
# grid — розміщуємо в таблиці: рядок 0, займає 4 стовпці
# padx/pady — відступи зовні; ipady=18 — висота поля; sticky="ew" — розтягуємо по ширині

expr = [""]  # список-контейнер для стану: зберігаємо "=" після обчислення

def press(val):
    # викликається при натисканні будь-якої цифри або операції (+, -, /, *)
    if display_var.get() == "0" or expr[0] == "=":
        # якщо на екрані "0" або щойно натиснули "=" — починаємо з нуля
        if val not in "0123456789":
            # натиснута операція (не цифра) — можна продовжити з попереднім результатом
            if expr[0] == "=":
                expr[0] = ""        # скидаємо стан "="
        else:
            display_var.set("")     # очищуємо екран перед введенням нової цифри
        if expr[0] == "=":
            expr[0] = ""            # скидаємо стан
    display_var.set(display_var.get() + val)  # додаємо натиснутий символ до тексту на екрані
    expr[0] = ""                    # скидаємо стан після звичайного натискання

def clear():
    # кнопка C — скидає все до нуля
    display_var.set("0")  # показуємо "0" на екрані
    expr[0] = ""          # скидаємо стан

def backspace():
    # кнопка ⌫ — видаляє останній введений символ
    cur = display_var.get()                              # отримуємо поточний текст з екрана
    display_var.set(cur[:-1] if len(cur) > 1 else "0")  # cur[:-1] = все крім останнього символу

def calculate():
    # кнопка = — обчислює математичний вираз
    try:
        result = eval(display_var.get())  # eval перетворює рядок у вираз і обчислює, наприклад "3+5*2" → 13
        display_var.set(str(result) if result != int(result) else str(int(result)))
        # якщо результат дробовий (3.5) — показуємо як є; інакше — прибираємо .0 (10.0 → 10)
    except:
        display_var.set("שגיאה")  # якщо вираз некоректний — показуємо "помилка"
    expr[0] = "="  # запам'ятовуємо що щойно було обчислення

BUTTONS = [
    # список всіх кнопок; кожен елемент: (текст, колір фону, функція при натисканні)
    ("C",   "#e06c75", clear),   # очистити все
    ("⌫",   "#e06c75", backspace),
    ("%",   "#61afef", lambda: press("%")),
    ("÷",   "#c678dd", lambda: press("/")),
    ("7",   "#3a3a52", lambda: press("7")),
    ("8",   "#14143f", lambda: press("8")),
    ("9",   "#3a3a52", lambda: press("9")),
    ("×",   "#c678dd", lambda: press("*")),
    ("4",   "#3a3a52", lambda: press("4")),
    ("5",   "#f1e647", lambda: press("5")),
    ("6",   "#ffc400a4", lambda: press("6")),
    ("−",   "#c678dd", lambda: press("-")),
    ("1",   "#3a3a52", lambda: press("1")),
    ("2",   "#3a3a52", lambda: press("2")),
    ("3",   "#3a3a52", lambda: press("3")),
    ("+",   "#c678dd", lambda: press("+")),
    ("±",   "#3a3a52", lambda: display_var.set(str(-float(display_var.get())))),
    ("0",   "#3a3a52", lambda: press("0")),
    (".",   "#3a3a52", lambda: press(".")),
    ("=",   "#98c379", calculate),
]

for i, (text, color, cmd) in enumerate(BUTTONS):
    # enumerate — дає порядковий номер i та значення (text, color, cmd) для кожної кнопки
    r, c = divmod(i, 4)  # divmod(i, 4) → обчислює рядок r і стовпець c (4 кнопки в рядку)
    btn = Button(root, text=text, font=("Arial", 20, "bold"),
                 bg=color, fg="white", activebackground=color,
                 activeforeground="white", bd=0, relief=FLAT,
                 width=4, height=2, command=cmd, cursor="hand2")
    # Button — кнопка; text — напис; bg — фон; fg="white" — білий текст
    # activebackground — колір кнопки при натисканні
    # bd=0, relief=FLAT — без рамки, плоский вигляд
    # command=cmd — функція яка викликається при кліку
    # cursor="hand2" — курсор-рука при наведенні мишки
    btn.grid(row=r+1, column=c, padx=5, pady=5)  # розміщуємо кнопку в таблиці (рядок+1, бо рядок 0 — екран)
    btn.bind("<Enter>", lambda e, b=btn, cl=color: b.config(bg=cl + "cc"))  # при наведенні мишки — світліший колір
    btn.bind("<Leave>", lambda e, b=btn, cl=color: b.config(bg=cl))         # при відведенні — повертаємо колір

root.mainloop()  # запускаємо головний цикл — вікно залишається відкритим і чекає на дії користувача
