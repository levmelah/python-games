import time


def print_typewriter(text):
	for char in text:
		print(char, end="", flush=True)  # виводимо символ без перенесення рядка
		time.sleep(0.1)  # пауза між символами


text = input("Введіть текст: ")
print_typewriter(text)
