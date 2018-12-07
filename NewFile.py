import numpy as np

def p(*args):
    print(max(args))
    
k = 2
pop = [1, 2, 3, 4, 5, 6]
for vars in zip(*[pop[i::k] for i in range(k)]):
    p(*vars)
