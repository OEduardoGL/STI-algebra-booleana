import re
from sti.parser import parse_raw
from sti.formatter import format_expr
from sti.simplifier import simplify
from sti.counterexample import find_counterexample
from sti.truth_table import create_trutable


def run_cli():
    op = input('Escolha: (1) Simplificação ou (2) Equivalência? ')
    if op == '1':
        s = input('Digite expressão: ')
        expr = parse_raw(s)
        log = []
        simp = simplify(expr, log)
        print('\nPasso a passo da simplificação:')
        for step in log:
            print('-', step)
        print('Resultado final:', format_expr(simp))
        choosen = input('Deseja criar a tabela verdade? [Y/N] ')

        if(choosen.strip().upper() == 'Y'):
            create_trutable(expr, simp)

    elif op == '2':
        s1 = input('Expr1: ')
        s2 = input('Expr2: ')
        expr1 = parse_raw(s1)
        expr2 = parse_raw(s2)
        log2 = []
        target = simplify(expr2, log2)
        log1 = []
        result1 = simplify(expr1, log1)
        if result1 == target:
            print('\n✓ As expressões são equivalentes.')
            print('\nComo Expr1 chega a Expr2:')
            for step in log1:
                print('-', step)
            print('= ', format_expr(target))
            print('\nComo Expr2 é simplificado:')
            for step in log2:
                print('-', step)
            print('= ', format_expr(target))
        else:
            print('\n✗ As expressões NÃO são equivalentes.')
            print('\nExpr1 simplifica para:')
            for step in log1:
                print('-', step)
            print('= ', format_expr(result1))
            print('\nExpr2 simplifica para:')
            for step in log2:
                print('-', step)
            print('= ', format_expr(target))
            ce = find_counterexample(result1, target)
            print('Contraexemplo:', ce)
    
    
        choosen = input('Deseja criar a tabela verdade? [Y/N] ')

        if(choosen.strip().upper() == 'Y'):
            create_trutable(expr1, expr2)

if __name__ == '__main__':
    run_cli()