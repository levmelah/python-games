dog1 = "Bob"
dog2 = "Max"
dog3 = "Rex"
dog4 = "Charlie"
dog5 = "Buddy"
dog6 = "Rocky"
dog7 = "Milo"
dog8 = "Oliver"
dog9 = "Leo"
dog10 = "Teddy"

def f1(): print(dog1, "is big and white")
def f2(): print(dog2, "is small and black")
def f3(): print(dog3, "has brown fur")
def f4(): print(dog4, "has long ears")
def f5(): print(dog5, "is fluffy and cute")
def f6(): print(dog6, "has grey spots")
def f7(): print(dog7, "is very tall")
def f8(): print(dog8, "has a short tail")
def f9(): print(dog9, "is fast and gold")
def f10(): print(dog10, "looks like a bear")

[f() for f in [f1, f2, f3, f4, f5, f6, f7, f8, f9, f10]]
