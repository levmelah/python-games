import random

class House:
    def __init__(self):
        self.money = 500
        self.food = 150

    def info_house(self):
        print(f"House has {self.money} money and {self.food} food.")

class Human:
    def __init__(self):
        self.name = "bob"
        self.fullness = 50
        self.house = House()

    def info_human(self):
        print(f"{self.name} has {self.fullness} fullness.")
    def eat(self):
        if self.house.food > 0:
            self.house.food -= 10
            self.fullness += 10
            print(f"{self.name} eats and gains 10 fullness.")
        else:
            print(f"{self.name} is hungry but has no food.")
    def work(self):
        self.house.money += 500
        self.fullness -= 10
        print(f"{self.name} works and earns 500 money, loses 10 fullness.")
    def game(self):
        self.fullness -= 10
        print(f"{self.name} plays games and loses 10 fullness.")
    def shopping(self):
            if self.house.money >= 50:
                self.house.money -= 50
                self.house.food += 50
                print(f"{self.name} goes shopping and buys 50 food for 50 money.")
            else:
                print(f"{self.name} wants to shop but doesn't have enough money.")                             
    def act(self):
        if self.fullness <= 0:
            print(f"{self.name} has died of hunger.")
            return False
        if self.fullness < 20:
            self.eat()
        elif self.house.food < 20:
            self.shopping()
        elif self.house.money < 50:
            self.work()
        else:
            action = random.choice(['eat', 'work', 'game', 'shopping'])
            if action == 'eat':
                self.eat()
            elif action == 'work':
                self.work()
            elif action == 'game':
                self.game()
            elif action == 'shopping':
                self.shopping()
        return True         
if __name__ == "__main__":
    house = House()
    human = Human()
    for i in range(366):
        print(f"=== Day {i} ===")
        human.info_human()
        house.info_house()
        human.act()