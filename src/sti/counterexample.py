from itertools import product

def find_counterexample(e1, e2):
    syms = sorted(list(e1.free_symbols | e2.free_symbols), key=str)
    for bits in product([False, True], repeat=len(syms)):
        assign = dict(zip(syms, bits))
        if bool(e1.subs(assign)) != bool(e2.subs(assign)):
            return assign
    return None