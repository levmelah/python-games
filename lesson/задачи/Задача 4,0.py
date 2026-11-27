num = int(input("Введіть число: "))

is_prime = True
for i in range(2, num):
	if num % i == 0:
		is_prime = False
		break

if is_prime:
	print("Число", num, "є простим.")
else:
	print("Число", num, "не є простим.")
