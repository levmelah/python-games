import random 

class Warrior:
    def __init__(self):
        self.name = "Samurai"
        self.health = 1000000
        self.attack_power = 20
        self.level = 1
        self.armor = 5999999999999999999999999999999999

    def attack(self, other):
        damage = random.randint(1, self.attack_power)
        other.health -= damage
        print(f"{self.name} attacks {other.name} for {damage} damage!")

    def is_alive(self):
        return self.health > 0
    
class Minotaur:
    def __init__(self):
        self.name = "Minotaur"
        self.health = 100
        self.attack_power = 40
        self.level = 1
        self.armor = 80

    def attack(self, other):
        damage = random.randint(1, self.attack_power)
        other.health -= damage
        print(f"{self.name} attacks {other.name} for {damage} damage!")

    def is_alive(self):
        return self.health > 0
    
class dragon:
    def __init__(self):
        self.name = "Dragon"
        self.health = 100
        self.attack_power = 50
        self.level = 1
        self.armor = 60

    def attack(self, other):
        damage = random.randint(1, self.attack_power)
        other.health -= damage
        print(f"{self.name} attacks {other.name} for {damage} damage!")

    def is_alive(self):
        return self.health > 0

class king:
    def __init__(self):
        self.name = "artemis"
        self.health = 60
        self.attack_power = 20
        self.level = 1
        self.armor = 100

    def attack(self, other):
        damage = random.randint(1, self.attack_power)
        other.health -= damage
        print(f"{self.name} attacks {other.name} for {damage} damage!")

    def is_alive(self):
        return self.health > 0

class Goblin:
    def __init__(self):
        self.name = "Goblin"
        self.health = 50
        self.attack_power = 5
        self.level = 1
        self.armor = 10

    def attack(self, other):
        damage = random.randint(1, self.attack_power)
        other.health -= damage
        print(f"{self.name} attacks {other.name} for {damage} damage!")

    def is_alive(self):
        return self.health > 0

class archers:
    def __init__(self):
        self.name = "Archer"
        self.health = 100
        self.attack_power = 15
        self.level = 1
        self.armor = 30

    def attack(self, other):
        damage = random.randint(1, self.attack_power)
        other.health -= damage
        print(f"{self.name} attacks {other.name} for {damage} damage!")

    def is_alive(self):
        return self.health > 0

class Game:
    def __init__(self):
        self.warrior = Warrior()
        self.archer = archers()
        self.king = king()
        self.goblin = Goblin()
        self.dragon = dragon()
        self.minotaur = Minotaur()  # אתחול המינוטאור במשחק

    def start(self):
        print("The battle begins!")
        # הלולאה רצה כל עוד לפחות גיבור אחד חי ולפחות מפלצת אחת חיה
        while (self.warrior.is_alive() or self.archer.is_alive() or self.king.is_alive()) and \
              (self.goblin.is_alive() or self.dragon.is_alive() or self.minotaur.is_alive()):
            
            # --- תור הגיבורים ---
            
            # תור הלוחם
            if self.warrior.is_alive():
                if self.goblin.is_alive():
                    self.warrior.attack(self.goblin)
                elif self.dragon.is_alive():
                    self.warrior.attack(self.dragon)
                elif self.minotaur.is_alive():
                    self.warrior.attack(self.minotaur)
                    
            # תור הקשת
            if self.archer.is_alive():
                if self.goblin.is_alive():
                    self.archer.attack(self.goblin)
                elif self.dragon.is_alive():
                    self.archer.attack(self.dragon)
                elif self.minotaur.is_alive():
                    self.archer.attack(self.minotaur)

            # תור המלך
            if self.king.is_alive():
                if self.goblin.is_alive():
                    self.king.attack(self.goblin)
                elif self.dragon.is_alive():
                    self.king.attack(self.dragon)
                elif self.minotaur.is_alive():
                    self.king.attack(self.minotaur)

            # --- תור המפלצות ---
            
            # תור הגובלין
            if self.goblin.is_alive():
                if self.warrior.is_alive():
                    self.goblin.attack(self.warrior)
                elif self.archer.is_alive():
                    self.goblin.attack(self.archer)
                elif self.king.is_alive():
                    self.goblin.attack(self.king)
                
            # תור הדרקון
            if self.dragon.is_alive():
                if self.warrior.is_alive():
                    self.dragon.attack(self.warrior)
                elif self.archer.is_alive():
                    self.dragon.attack(self.archer)
                elif self.king.is_alive():
                    self.dragon.attack(self.king)

            # תור המינוטאור
            if self.minotaur.is_alive():
                if self.warrior.is_alive():
                    self.minotaur.attack(self.warrior)
                elif self.archer.is_alive():
                    self.minotaur.attack(self.archer)
                elif self.king.is_alive():
                    self.minotaur.attack(self.king)
                
            # הדפסת מצב החיים
            print(f"{self.warrior.name} Health: {max(0, self.warrior.health)}")
            print(f"{self.archer.name} Health: {max(0, self.archer.health)}")
            print(f"{self.king.name} Health: {max(0, self.king.health)}")
            print(f"{self.goblin.name} Health: {max(0, self.goblin.health)}")
            print(f"{self.dragon.name} Health: {max(0, self.dragon.health)}")
            print(f"{self.minotaur.name} Health: {max(0, self.minotaur.health)}")
            print("-----------------------------")
            
        # בדיקת תוצאת המשחק בסיום הלולאה
        if not self.warrior.is_alive() and not self.archer.is_alive() and not self.king.is_alive():
            print("All heroes have been defeated! Game Over.")
        else:
            print("All monsters have been defeated! You win!") 


if __name__ == "__main__":
    game = Game()
    game.start()
