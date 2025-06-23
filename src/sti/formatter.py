from sympy import true, false
from sympy.logic.boolalg import And, Or, Not

def format_expr(expr) -> str:
    if expr is true:
        return '1'
    if expr is false:
        return '0'
    if expr.is_Symbol:
        return str(expr)
    if isinstance(expr, Not):
        return '~' + format_expr(expr.args[0])
    if isinstance(expr, And):
        return '*'.join(format_expr(a) for a in expr.args)
    if isinstance(expr, Or):
        return '+'.join(format_expr(a) for a in expr.args)
    return str(expr)