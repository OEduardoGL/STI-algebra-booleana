import itertools
from sympy import true
from sympy.logic.boolalg import Equivalent

from .formatter import format_expr

def _get_all_variables(*expressions):
    variables_set = set()
    for expr in expressions:
        variables_set.update(expr.free_symbols)
    return sorted(list(variables_set), key=str)

def _format_value(val):
    return 'V' if val else 'F'


def create_trutable(*expressions):
    if not expressions:
        print("Nenhuma expressão fornecida para criar a tabela-verdade.")
        return

    print("\nGerando Tabela-Verdade...")

    variables = _get_all_variables(*expressions)
    
    header = [str(v) for v in variables]
    header.extend(format_expr(e) for e in expressions)

    equivalence_expr = None
    if len(expressions) == 2:
        expr1, expr2 = expressions
        equivalence_expr = Equivalent(expr1, expr2)
        equiv_str = f"({format_expr(expr1)} ↔ {format_expr(expr2)})"
        header.append(equiv_str)

    matrix = [header]

    n_vars = len(variables)
    combinations = itertools.product([True, False], repeat=n_vars)

    for combo in combinations:
        context = dict(zip(variables, combo))
        
        bool_results = [expr.subs(context) is true for expr in expressions]
        
        formatted_row = list(map(_format_value, combo)) + list(map(_format_value, bool_results))
        
        if equivalence_expr:
            res_equiv = equivalence_expr.subs(context) is true
            formatted_row.append(_format_value(res_equiv))
        
        matrix.append(formatted_row)

    _print_matrix_formatted(matrix)

def _print_matrix_formatted(matrix):
    if not matrix:
        return
    col_widths = [max(len(str(item)) for item in col) for col in zip(*matrix)]
    header = matrix[0]
    header_line = " | ".join(header[i].center(col_widths[i]) for i in range(len(header)))
    print(header_line)
    separator_line = "-+-".join('-' * width for width in col_widths)
    print(separator_line)
    for row in matrix[1:]:
        data_line = " | ".join(str(row[i]).center(col_widths[i]) for i in range(len(row)))
        print(data_line)