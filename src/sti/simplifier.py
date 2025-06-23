from sympy import true, false
from sympy.logic.boolalg import And, Or, Not
from itertools import product
import re
from sti.formatter import format_expr

def simplify(expr, log):
    if expr is true or expr is false or expr.is_Symbol:
        return expr
    # NOT
    if isinstance(expr, Not):
        inner = simplify(expr.args[0], log)
        if isinstance(inner, Not):
            log.append(f"Involutiva: ¬(¬X) → X, onde X={format_expr(inner.args[0])}")
            return simplify(inner.args[0], log)
        if isinstance(inner, And):
            seq = '+'.join(format_expr(Not(a)) for a in inner.args)
            log.append(f"De Morgan: ¬({format_expr(expr.args[0])}) → {seq}")
            return simplify(Or(*[Not(a) for a in inner.args]), log)
        if isinstance(inner, Or):
            seq = '*'.join(format_expr(Not(a)) for a in inner.args)
            log.append(f"De Morgan: ¬({format_expr(expr.args[0])}) → {seq}")
            return simplify(And(*[Not(a) for a in inner.args]), log)
        if inner is true:
            log.append("Negação: ¬1 → 0")
            return false
        if inner is false:
            log.append("Negação: ¬0 → 1")
            return true
        return Not(inner)
    # AND
    if isinstance(expr, And):
        terms = []
        for sub in expr.args:
            s = simplify(sub, log)
            if isinstance(s, And): terms.extend(s.args)
            else: terms.append(s)
        # Nulidade
        if false in terms:
            log.append(f"Nulidade: contém 0 em {format_expr(expr)} → 0")
            return false
        # Identidade
        if true in terms:
            log.append(f"Identidade: remove 1 em {format_expr(expr)}")
            terms = [t for t in terms if t is not true]
        # Complementar
        for t in terms:
            if Not(t) in terms:
                log.append(f"Complementar: {format_expr(t)}*{format_expr(Not(t))} → 0")
                return false
        # Idempotente
        unique = []
        for t in terms:
            if t not in unique: unique.append(t)
        if len(unique) < len(terms):
            log.append(f"Idempotente: remove duplicatas em {format_expr(expr)}")
        terms = unique
        # Absorção
        for t in terms:
            if isinstance(t, Or) and any(lit in terms for lit in t.args):
                chosen = next(lit for lit in t.args if lit in terms)
                log.append(f"Absorção: {format_expr(expr)} → {format_expr(chosen)}")
                return simplify(chosen, log)
        # Distributiva parcial
        for i,t in enumerate(terms):
            if isinstance(t, Or):
                rest = terms[:i] + terms[i+1:]
                dist_terms = [simplify(And(lit, *rest), log) for lit in t.args]
                log.append(f"Distributiva: {format_expr(expr)} → " +
                           ' + '.join(format_expr(x) for x in dist_terms))
                return simplify(Or(*dist_terms), log)
        # Resultado
        if not terms:
            return true
        if len(terms) == 1:
            return terms[0]
        return And(*terms)
    # OR
    if isinstance(expr, Or):
        terms = []
        for sub in expr.args:
            s = simplify(sub, log)
            if isinstance(s, Or): terms.extend(s.args)
            else: terms.append(s)
        # Nulidade
        if true in terms:
            log.append(f"Nulidade: contém 1 em {format_expr(expr)} → 1")
            return true
        # Identidade
        if false in terms:
            log.append(f"Identidade: remove 0 em {format_expr(expr)}")
            terms = [t for t in terms if t is not false]
        # Complementar
        for t in terms:
            if Not(t) in terms:
                log.append(f"Complementar: {format_expr(t)}+{format_expr(Not(t))} → 1")
                return true
        # Idempotente
        unique = []
        for t in terms:
            if t not in unique: unique.append(t)
        if len(unique) < len(terms):
            log.append(f"Idempotente: remove duplicatas em {format_expr(expr)}")
        terms = unique
        # Fator comum (A*B + A*~B → A)
        for i in range(len(terms)):
            for j in range(i+1, len(terms)):
                t1, t2 = terms[i], terms[j]
                if isinstance(t1, And) and isinstance(t2, And):
                    a1, a2 = set(t1.args), set(t2.args)
                    common = a1 & a2
                    rem1, rem2 = a1-common, a2-common
                    if len(common)==1 and len(rem1)==1 and len(rem2)==1:
                        x1, x2 = next(iter(rem1)), next(iter(rem2))
                        if x1 == Not(x2) or x2 == Not(x1):
                            lit = next(iter(common))
                            log.append(f"Fator comum: {format_expr(t1)}+{format_expr(t2)} → {format_expr(lit)}")
                            new = [u for u in terms if u not in (t1, t2)] + [lit]
                            return simplify(Or(*new), log)
        # Absorção mista (A + ~A*X → A+X)
        for lit in [t for t in terms if t.is_Symbol]:
            for t in terms:
                if isinstance(t, And) and Not(lit) in set(t.args):
                    Xargs = [a for a in t.args if a != Not(lit)]
                    Xprod = And(*Xargs) if len(Xargs)>1 else Xargs[0]
                    log.append(f"Absorção mista: {format_expr(expr)} → {format_expr(lit)}+{format_expr(Xprod)}")
                    new_terms = [u for u in terms if u != t]
                    if Xprod not in new_terms: new_terms.append(Xprod)
                    return simplify(Or(*new_terms), log)
        # Subsunção
        filtered = []
        for ti in terms:
            ai = set(ti.args) if isinstance(ti, And) else {ti}
            subs = any((aj := set(tj.args) if isinstance(tj, And) else {tj}).issubset(ai)
                       and tj is not ti for tj in terms)
            if not subs: filtered.append(ti)
        if len(filtered) < len(terms):
            log.append(f"Subsunção: remove termos em {format_expr(expr)}")
        terms = filtered
        # Consenso
        new_terms = terms.copy()
        for t1 in terms:
            for t2 in terms:
                if isinstance(t1, And) and isinstance(t2, And):
                    a1, a2 = set(t1.args), set(t2.args)
                    for lit in a1:
                        if Not(lit) in a2:
                            y, z = a1-{lit}, a2-{Not(lit)}
                            if len(y)==len(z)==1:
                                cons = simplify(And(*y,*z), log)
                                if cons in new_terms:
                                    log.append(f"Consenso: remove {format_expr(cons)} em {format_expr(expr)}")
                                    new_terms.remove(cons)
        terms = new_terms
        # Absorção final
        simples = [t for t in terms if not isinstance(t, And)]
        final = [t for t in terms if not(isinstance(t, And)
                                         and any(lit in simples for lit in t.args))]
        if len(final) < len(terms): log.append(f"Absorção final: remove termos em {format_expr(expr)}")
        terms = final
        if not terms: return false
        if len(terms) == 1: return terms[0]
        return Or(*terms)
    return expr