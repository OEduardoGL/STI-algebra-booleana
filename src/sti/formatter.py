from sympy import true, false
from sympy.logic.boolalg import And, Or, Not

def format_expr(expr):
    # Caso base: Símbolos, True ou False
    if expr.is_Symbol or expr in (true, false):
        return str(expr)

    # --- Lógica para o operador NOT (~) ---
    if isinstance(expr, Not):
        arg = expr.args[0]
        # Adiciona parênteses se o conteúdo for uma operação (And ou Or)
        if isinstance(arg, (And, Or)):
            return f"~({format_expr(arg)})"
        # Senão, não precisa
        return f"~{format_expr(arg)}"

    # --- Lógica para o operador AND (*) ---
    if isinstance(expr, And):
        terms = []
        for arg in expr.args:
            if isinstance(arg, Or):
                terms.append(f"({format_expr(arg)})")
            else:
                terms.append(format_expr(arg))
        return '*'.join(terms)

    # --- Lógica para o operador OR (+) ---
    if isinstance(expr, Or):
        return '+'.join(format_expr(arg) for arg in expr.args)

    # Fallback para qualquer outro caso
    return str(expr)