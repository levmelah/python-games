import random, sys, time

print("Час перевірити свої рефлекси та перевірити, чи ви найшвидший")
print("Коли ви бачите 'DRAW', у вас є 0,3 секунди, щоб натиснути Enter.")
print("Але ви програєте, якщо натиснете Enter до того, як з'явиться <DRAW>.")
print()
input('Натисніть Enter, щоб почати...')

while True:
    print()
    print("Приготуйся...")
    time.sleep(random.randint(20, 50) / 10.0)
    print('DRAW!')
    drawTime = time.time()
    input()
    timeElapsed = time.time() - drawTime

    if timeElapsed < 0.01:
        print('You lose')
    elif timeElapsed > 0.3:
        timeElapsed = round(timeElapsed, 4)
        print('Не встиг', timeElapsed, 'секунди. Занадто повільно!')
    else:
        timeElapsed = round(timeElapsed, 4)
        print('Ти швидкий, встиг за', timeElapsed, 'секунди.')
        print('You win!')

    print('Введіть QUIT, щоб зупинити, або натисніть Enter, щоб продовжити.')
    response = input().upper()
    if response == 'QUIT':
        print('Thanks for playing!')
        sys.exit()
