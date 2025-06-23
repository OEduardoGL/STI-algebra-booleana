from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application
)

def parse_raw(s: str):
    s = (s.replace('⋅','&')
       .replace('·','&')
       .replace('.','&')
       .replace('*','&')
       .replace('+','|')
       .replace('¬','~')
       .replace('ˉ','~')
       .replace(' ','')    
    )
    expr = parse_expr(
        s, evaluate=False,
        transformations=standard_transformations +
                        (implicit_multiplication_application,)
    )
    return expr