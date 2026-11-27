num = input("Введіть число: ")

digits = len(num)
armstrong = sum(int(digit) ** digits for digit in num) == int(num)
if armstrong:
	print("Число", num, "є числом Армстронга.")
else:
	print("Число", num, "не є числом Армстронга.")
