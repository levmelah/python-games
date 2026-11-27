import tkinter as tk


def calculate_sum():
    try:
        a = float(entry_a.get())
        b = float(entry_b.get())
        result_var.set(f"Result: {a + b}")
    except ValueError:
        result_var.set("Please enter valid numbers")


root = tk.Tk()
root.title("Simple Sum Calculator")
root.geometry("320x200")
root.resizable(False, False)

frame = tk.Frame(root, padx=16, pady=16)
frame.pack(fill="both", expand=True)

tk.Label(frame, text="Enter a value:").pack(anchor="w")
entry_a = tk.Entry(frame)
entry_a.pack(fill="x", pady=(0, 10))

tk.Label(frame, text="Enter b value:").pack(anchor="w")
entry_b = tk.Entry(frame)
entry_b.pack(fill="x", pady=(0, 12))

tk.Button(frame, text="Calculate a + b", command=calculate_sum).pack(fill="x")

result_var = tk.StringVar(value="Result: -")
tk.Label(frame, textvariable=result_var, fg="#1f4d2e", font=("Arial", 11, "bold")).pack(pady=(14, 0))

root.mainloop()
