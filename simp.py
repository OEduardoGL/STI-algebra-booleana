from sympy import true, false
from sympy.logic.boolalg import And, Or, Not
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)
import re
from itertools import product

def simplify_manual(expr):
    if expr is true or expr is false:
        return expr
    if expr.is_Symbol:
        return expr

    # NOT
    if isinstance(expr, Not):
        inner = simplify_manual(expr.args[0])
        if isinstance(inner, Not):
            return simplify_manual(inner.args[0])
        if isinstance(inner, And):
            return simplify_manual(Or(*[Not(a) for a in inner.args]))
        if isinstance(inner, Or):
            return simplify_manual(And(*[Not(a) for a in inner.args]))
        if inner is true:
            return false
        if inner is false:
            return true
        return Not(inner)

    # AND
    if isinstance(expr, And):
        terms = []
        for a in expr.args:
            s = simplify_manual(a)
            if isinstance(s, And):
                terms.extend(s.args)
            else:
                terms.append(s)
        # DNF full distribution if product of sums
        if terms and all(isinstance(t, Or) for t in terms):
            combos = product(*(t.args for t in terms))
            products = [simplify_manual(And(*combo)) for combo in combos]
            return simplify_manual(Or(*products))
        if false in terms:
            return false
        terms = [t for t in terms if t is not true]
        for t in terms:
            if Not(t) in terms:
                return false
        # idempotent and flatten
        unique = []
        for t in terms:
            if t not in unique:
                unique.append(t)
        terms = unique
        # absorption A*(A+X) = A
        for t in terms:
            if isinstance(t, Or) and any(sub in terms for sub in t.args):
                return simplify_manual(next(sub for sub in t.args if sub in terms))
        # partial distribution
        for i, t in enumerate(terms):
            if isinstance(t, Or):
                rest = terms[:i] + terms[i+1:]
                dist = Or(*[simplify_manual(And(sub, *rest)) for sub in t.args])
                return simplify_manual(dist)
        if not terms:
            return true
        if len(terms) == 1:
            return terms[0]
        return And(*terms)

    # OR
    if isinstance(expr, Or):
        terms = []
        for a in expr.args:
            s = simplify_manual(a)
            if isinstance(s, Or):
                terms.extend(s.args)
            else:
                terms.append(s)
        if true in terms:
            return true
        terms = [t for t in terms if t is not false]
        for t in terms:
            if Not(t) in terms:
                return true
        # idempotent
        unique = []
        for t in terms:
            if t not in unique:
                unique.append(t)
        terms = unique
        # common factor rule X*Y + X*~Y = X
        if len(terms) == 2 and all(isinstance(t, And) for t in terms):
            a1, a2 = set(terms[0].args), set(terms[1].args)
            common = a1 & a2
            rem1, rem2 = a1 - common, a2 - common
            if len(rem1) == len(rem2) == 1:
                lit = next(iter(common))
                if next(iter(rem1)) == Not(next(iter(rem2))) or next(iter(rem2)) == Not(next(iter(rem1))):
                    return simplify_manual(lit)
        # subsumption
        filtered = []
        for ti in terms:
            ai = set(ti.args) if isinstance(ti, And) else {ti}
            if not any((aj := set(tj.args) if isinstance(tj, And) else {tj}).issubset(ai) and tj is not ti for tj in terms):
                filtered.append(ti)
        terms = filtered
        # consensus
        new_terms = terms.copy()
        for t1 in terms:
            for t2 in terms:
                if isinstance(t1, And) and isinstance(t2, And):
                    a1, a2 = set(t1.args), set(t2.args)
                    for lit in a1:
                        if Not(lit) in a2:
                            y, z = a1 - {lit}, a2 - {Not(lit)}
                            if len(y) == len(z) == 1:
                                cons = simplify_manual(And(*y, *z))
                                if cons in new_terms:
                                    new_terms.remove(cons)
        terms = new_terms
        # absorption
        simples = [t for t in terms if not isinstance(t, And)]
        terms = [t for t in terms if not (isinstance(t, And) and any(sub in simples for sub in t.args))]
        if not terms:
            return false
        if len(terms) == 1:
            return terms[0]
        return Or(*terms)

    return expr


def parse_and_simplify(s):
    s = (s
         .replace('⋅','&').replace('·','&').replace('.','&')
         .replace('*','&').replace('+','|')
         .replace('¬','~').replace('ˉ','~')
         .replace(' ',''))
    expr = parse_expr(s, evaluate=False,
                      transformations=standard_transformations+
                      (implicit_multiplication_application,))
    return simplify_manual(expr)


def format_expr(expr):
    if expr is true:
        return '1'
    if expr is false:
        return '0'
    if expr.is_Symbol:
        return str(expr)
    if isinstance(expr, Not):
        return f"~{format_expr(expr.args[0])}"
    if isinstance(expr, And):
        return '*'.join(format_expr(a) for a in expr.args)
    if isinstance(expr, Or):
        return '+'.join(format_expr(a) for a in expr.args)
    return str(expr)

if __name__ == '__main__':
    entrada = input('Digite a expressão booleana: ')
    simp = parse_and_simplify(entrada)
    print('Simplificada:', format_expr(simp))
