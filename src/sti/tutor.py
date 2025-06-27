import re

from . import database
from .parser import parse_raw
from .formatter import format_expr
from .simplifier import simplify
from .counterexample import find_counterexample
from .truth_table import create_trutable


def run_cli():
    database.inicializar_banco()


    op = input('Escolha: (1) Simplificação ou (2) Equivalência? ')

    if op == '1':
        s = input('Digite expressão: ')
        expr = parse_raw(s)

        log = []
        simp = simplify(expr, log)


        print('\nPasso a passo da simplificação:')
        for step in log:
            print(f"- {step['rule']}: {step['details']}")
        print('Resultado final:', format_expr(simp))

        try:
            dificuldade = len(s) // 5 + len(log) # Heurística simples

            regras_usadas_para_salvar = [step['rule'] for step in log]

            database.salvar_interacao(
                operacao="Simplificação",
                expressao=s,
                dificuldade=dificuldade,
                passos=len(log),
                regras=regras_usadas_para_salvar # A sua lista log já contém exatamente o que precisamos!
            )
        except Exception as e:
            print(f"[ERRO] Não foi possível salvar a interação no banco de dados: {e}")

        choosen = input('Deseja criar a tabela verdade? [Y/N] ')
        if(choosen.strip().upper() == 'Y'):
            create_trutable(expr, simp)

    elif op == '2':
        s1 = input('Expr1: ')
        s2 = input('Expr2: ')
        expr1 = parse_raw(s1)
        expr2 = parse_raw(s2)

        log1, log2 = [], []
        result1 = simplify(expr1, log1)
        target = simplify(expr2, log2)

        ce = find_counterexample(result1, target)
        
        if ce is None:
            print('\n✓ As expressões são equivalentes.')
            print('\nComo Expr1 é simplificada:')
            for step in log1:
                print('-', step['rule'] + ':', step['details'])
            print('= ', format_expr(result1))
            
            print('\nComo Expr2 é simplificada:')
            for step in log2:
                print('-', step['rule'] + ':', step['details'])
            print('= ', format_expr(target))

        else:
            print('\n✗ As expressões NÃO são equivalentes.')
            print('\nExpr1 simplifica para:')
            for step in log1:
                print('-', step['rule'] + ':', step['details'])
            print('= ', format_expr(result1))
            
            print('\nExpr2 simplifica para:')
            for step in log2:
                print('-', step['rule'] + ':', step['details'])
            print('= ', format_expr(target))
            
            print('\nContraexemplo encontrado:', ce)

        try:
            full_expression = f"{s1} <=> {s2}"
            dificuldade = (len(s1) + len(s2)) // 5 + len(log1) + len(log2)
            regras_combinadas = {
                "regras_expr1": [step['rule'] for step in log1],
                "resultado_expr1": format_expr(result1),
                "regras_expr2": [step['rule'] for step in log2],
                "resultado_expr2": format_expr(target)
            }
            database.salvar_interacao(
                operacao="Equivalência",
                expressao=full_expression,
                dificuldade=dificuldade,
                passos=len(log1) + len(log2),
                regras=regras_combinadas
            )
        except Exception as e:
            print(f"\n[ERRO] Não foi possível salvar a interação no banco de dados: {e}")
        
        choosen = input('\nDeseja criar a tabela verdade? [Y/N] ')
        if(choosen.strip().upper() == 'Y'):
            create_trutable(expr1, expr2)

if __name__ == '__main__':

    run_cli()