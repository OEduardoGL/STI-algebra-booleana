import sqlite3
import joblib
import pandas as pd 
import numpy as np
import os

from sympy import And, Not, Or, factor, sympify # Adicione 'factor para transformar SOP -> factor' 

from . import database
from .parser import parse_raw
from .formatter import format_expr
from .simplifier import simplify, term_to_expr
from .counterexample import find_counterexample
from .truth_table import create_trutable

QUESTOES_CALIBRACAO = [
    {"expressao": "A + A", "solucao": "A", "lei": "Idempotência"},
    {"expressao": "A * ~A", "solucao": "false", "lei": "Complemento"},
    {"expressao": "A + A*B", "solucao": "A", "lei": "Absorção"},
    {"expressao": "A*B + A*~B", "solucao": "A", "lei": "Adjacência"},
    {"expressao": "~~A", "solucao": "A", "lei": "Dupla Negação"}
]

def select_ideal_question_algoritmica(usuario_id, nivel_habilidade):
    """Seleciona uma questão com base em regras e dificuldade."""
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()
    
    min_diff = int(nivel_habilidade - 1)
    max_diff = int(nivel_habilidade + 2)

    query = """
        SELECT id, expressao, solucao_simplificada, dificuldade, lei_principal FROM banco_de_questoes
        WHERE dificuldade BETWEEN ? AND ?
        AND expressao NOT IN (SELECT expressao_inicial FROM historico WHERE usuario_id = ? AND operacao = 'Tutor Inteligente')
        ORDER BY RANDOM() LIMIT 1
    """
    cursor.execute(query, (min_diff, max_diff, usuario_id))
    questao = cursor.fetchone()
    
    if not questao: # Fallback se não achar na faixa ideal
        query_fallback = """
            SELECT id, expressao, solucao_simplificada, dificuldade, lei_principal FROM banco_de_questoes
            WHERE expressao NOT IN (SELECT expressao_inicial FROM historico WHERE usuario_id = ? AND operacao = 'Tutor Inteligente')
            ORDER BY RANDOM() LIMIT 1
        """
        cursor.execute(query_fallback, (usuario_id,))
        questao = cursor.fetchone()

    conn.close()
    return {"id": questao[0], "expressao": questao[1], "solucao": questao[2], "dificuldade": questao[3], "lei": questao[4]} if questao else None

def select_ideal_question_ml(usuario_id, nivel_habilidade):
    """Seleciona uma questão usando um modelo de ML treinado."""
    model = joblib.load('modelo_tutor.pkl')
    
    conn = sqlite3.connect(database.DB_NAME)
    query = """
        SELECT id, expressao, solucao_simplificada, dificuldade, lei_principal FROM banco_de_questoes
        WHERE expressao NOT IN (SELECT expressao_inicial FROM historico WHERE usuario_id = ? AND operacao = 'Tutor Inteligente')
    """
    df_candidatas = pd.read_sql_query(query, conn, params=(usuario_id,))
    conn.close()

    if df_candidatas.empty:
        return None

    df_candidatas['nivel_habilidade'] = nivel_habilidade
    X_prever = df_candidatas[['dificuldade', 'nivel_habilidade']]
    probabilidades_acerto = model.predict_proba(X_prever)[:, 1]
    df_candidatas['prob_acerto'] = probabilidades_acerto
    
    # Busca questões na "zona ideal" de aprendizado (60% a 80% de chance de acerto)
    df_ideais = df_candidatas[(df_candidatas['prob_acerto'] >= 0.60) & (df_candidatas['prob_acerto'] <= 0.80)]
    
    if not df_ideais.empty:
        # Pega uma questão aleatória da faixa ideal
        return df_ideais.sample(n=1).to_dict('records')[0]
    else:
        # Fallback: se nenhuma estiver na faixa ideal, pega a mais próxima de 70%
        df_candidatas['dist_do_ideal'] = abs(df_candidatas['prob_acerto'] - 0.70)
        return df_candidatas.sort_values('dist_do_ideal').iloc[0].to_dict()


def run_calibration_quiz(usuario_id, nome_usuario):
    """Apresenta 5 questões iniciais para um novo usuário."""
    print(f"\nOlá, {nome_usuario}! Bem-vindo ao Tutor de Álgebra Booleana.")
    print("Para começar, vamos resolver 5 questões rápidas para conhecermos seu nível.")
    
    acertos = 0
    for i, q in enumerate(QUESTOES_CALIBRACAO):
        print(f"\n--- Questão {i+1}/5 (Lei da {q['lei']}) ---")
        print(f"Simplifique a expressão: {q['expressao']}")
        resposta_usuario_str = input("Sua resposta: ")

        try:
            expr_aluno = parse_raw(resposta_usuario_str)
            expr_gabarito = parse_raw(q['solucao'])
            
            # Compara a resposta do aluno com a solução correta
            if find_counterexample(expr_aluno, expr_gabarito) is None:
                print("✓ Correto!")
                acertos += 1
                resultado = "Correto"
            else:
                print(f"✗ Incorreto. A resposta correta é: {q['solucao']}")
                resultado = "Incorreto"

            # Salva a tentativa no histórico
            detalhes = {"gabarito": q['solucao'], "resposta_aluno": resposta_usuario_str}
            database.salvar_interacao(
                usuario_id=usuario_id, operacao="Calibracao",
                expressao_inicial=q['expressao'], resultado_final=resultado,
                dificuldade=1, passos=1, detalhes_dict=detalhes
            )

        except Exception as e:
            print(f"Erro ao processar sua resposta: {e}")
    
    print(f"\nQuiz de nivelamento finalizado! Você acertou {acertos} de 5 questões.")
    # No futuro, aqui você usaria a variável 'acertos' para definir o 'nivel_habilidade' do usuário.
    print("Agora você tem acesso ao menu principal.")

def minterm_to_expr(variables, mt_num):
    """Converte um número de minterm em uma expressão sympy."""
    from sympy.logic.boolalg import And, Not # Import local para evitar dependência circular se mover o arquivo
    lits = []
    binary_str = format(mt_num, f'0{len(variables)}b')
    # Assumindo que as variáveis estão em ordem alfabética (A, B, C...)
    for i, var in enumerate(variables):
        if binary_str[i] == '1':
            lits.append(var)
        else:
            lits.append(Not(var))
    return And(*lits)

def print_didactic_simplification(result):
    """
    Imprime o passo a passo da simplificação de forma didática e correta,
    usando um log de combinações do motor de simplificação.
    """
    regras_aplicadas = []
    
    # Lida com casos triviais como A+~A que já vêm simplificados
    if "steps" in result:
        print(result["steps"])
        return ["Simplificação Direta"]

    initial_expr = result['initial_expr']
    variables = result['variables']
    minterms_nums = result['minterms']
    final_sop = result['final_sop']

    print("\n--- Passo a Passo da Simplificação ---")
    print(f"Expressão Inicial: {format_expr(initial_expr)}\n")

    # --- PASSO 1: EXPANSÃO CANÔNICA ---
    minterm_exprs = [minterm_to_expr(variables, mt) for mt in minterms_nums]
    current_terms_set = set(minterm_exprs)
    
    print("--- Passo 1: Expansão para a Forma Canônica ---")
    regras_aplicadas.append("Expansão Canônica")
    print("Primeiro, expandimos a expressão para seus componentes fundamentais (minterms).")
    print(f"Expressão Expandida: {format_expr(Or(*current_terms_set))}\n")
    
    # --- PASSO 2: AGRUPAMENTO SEGUINDO O LOG DE COMBINAÇÕES ---
    print("--- Passo 2: Simplificação por Agrupamento ---")
    if not result.get('combination_log'):
        print("Nenhum agrupamento por adjacência foi possível.\n")
    else:
        # A nova lógica: iteramos sobre o diário de passos que o 'simplify' criou
        for step in result['combination_log']:
            # Converte os termos do passo (que estão em binário) para expressões Sympy
            before_exprs = [term_to_expr(variables, t) for t in step['before']]
            after_expr = term_to_expr(variables, step['after'])

            # Apenas mostra o passo se os termos a serem combinados ainda existem na expressão
            if all(comp in current_terms_set for comp in before_exprs):
                regras_aplicadas.append("Lei da Adjacência")
                
                print(f"Expressão Atual: {format_expr(Or(*current_terms_set))}")
                group_str = " + ".join(sorted([format_expr(t) for t in before_exprs]))
                print(f"  └─ Aplicando a Lei da Adjacência em: ({group_str})")
                print(f"     └─ Resultado: {format_expr(after_expr)}")
                
                # Atualiza a expressão: remove os termos antigos e adiciona o novo, simplificado
                current_terms_set = (current_terms_set - set(before_exprs)) | {after_expr}
                print(f"Expressão Após o Passo: {format_expr(Or(*current_terms_set))}\n")

    # --- PASSO 3: MONTAGEM FINAL ---
    print("--- Passo 3: Montagem Final e Absorção ---")
    regras_aplicadas.append("Montagem Final (Absorção)")
    print("Combinamos os termos restantes. Termos redundantes (cobertos por outros) são absorvidos implicitamente pelo algoritmo.")
    print(f"Expressão Final (Soma de Produtos): {format_expr(final_sop)}\n")
    
    # --- PASSO 4: FATORAÇÃO OPCIONAL ---
    print("--- Passo 4 (Opcional): Fatoração Adicional ---")
    factored_expr = factor(final_sop)
    if str(factored_expr) != str(final_sop):
        regras_aplicadas.append("Lei da Distributividade")
        print(f"Aplicando a Lei da Distributividade em '{format_expr(final_sop)}', podemos otimizar para:")
        print(f"Expressão Final (Fatorada): {format_expr(factored_expr)}")
    else:
        print("A expressão final não possui termos comuns para uma fatoração adicional.")
        
    return regras_aplicadas

def run_interactive_tutor(usuario_id):
    nivel_habilidade_atual = database.get_user_skill(usuario_id)
    print(f"\nBuscando uma questão ideal para seu nível de habilidade ({nivel_habilidade_atual:.2f})...")

    MODEL_PATH = 'modelo_tutor.pkl'
    
    if os.path.exists(MODEL_PATH):
        print(f"\n(Usando seletor com Machine Learning para seu nível {nivel_habilidade_atual:.2f})")
        questao = select_ideal_question_ml(usuario_id, nivel_habilidade_atual)
    else:
        print(f"\n(Modelo de ML não encontrado. Usando seletor algorítmico para seu nível {nivel_habilidade_atual:.2f})")
        questao = select_ideal_question_algoritmica(usuario_id, nivel_habilidade_atual)

    if questao is None:
        print("\nParabéns! Parece que você já respondeu todas as questões disponíveis.")
        return

    s_inicial = questao['expressao']
    solucao_correta_gabarito = parse_raw(questao['solucao'])
    lei = questao['lei']

    print("-" * 40)
    print(f"Questão (Dificuldade: {questao['dificuldade']}, Lei principal: {lei})")
    print(f"Simplifique a expressão: {s_inicial}")
    print("Quando terminar, digite 'fim'. Se quiser desistir, digite 'desisto'.")
    print("-" * 40)

    expr_inicial_sympy = parse_raw(s_inicial)
    expressao_atual_sympy = expr_inicial_sympy
    expressao_atual_str = s_inicial
    passos_aluno = []

    LEIS_DIDATICAS = {
        "Idempotência": "A + A = A ou A * A = A. Unir o mesmo termo não muda o resultado.",
        "Complemento": "A + ~A = 1 e A * ~A = 0. Um termo e seu complemento anulam ou totalizam.",
        "Absorção": "A + A*B = A. O termo principal absorve o termo composto.",
        "Adjacência": "A*B + A*~B = A. Combina termos com a mesma variável principal.",
        "Dupla Negação": "~~A = A. Duas negações cancelam.",
        "Aniquilação": "A * 0 = 0 e A + 1 = 1. O neutro destrói o termo.",
        "Identidade": "A * 1 = A e A + 0 = A. O neutro mantém o termo.",
        "De Morgan": "~(A * B) = ~A + ~B e ~(A + B) = ~A * ~B. Distribui a negação trocando operações.",
        "Distributiva": "A*(B+C)=A*B+A*C. Distribui multiplicação sobre soma.",
        "Consenso": "A*B + ~A*C + B*C = A*B + ~A*C. Remove termos redundantes.",
    }

    while True:
        s_passo_aluno = input(f"Expressão Atual ({expressao_atual_str}) -> Seu passo: ")
        if s_passo_aluno.lower().strip() == 'fim':
            # choosen = input('\nDeseja criar a tabela verdade? [Y/N] ')
            # if(choosen.strip().upper() == 'Y'):
            #     create_trutable(s_inicial, expressao_atual_sympy)
            break
        elif s_passo_aluno.lower().strip() == 'desisto':
            print("\nEntendido, vamos encerrar essa questão.")
            print(f"A forma mínima correta seria: {questao['solucao']}")
            database.update_user_skill(usuario_id, False, questao['dificuldade'])
            detalhes = {"passos_do_aluno": passos_aluno, "solucao_final_aluno": expressao_atual_str, "acertou": False}
            database.salvar_interacao(
                usuario_id=usuario_id, operacao="Tutor Inteligente",
                expressao_inicial=s_inicial, resultado_final="Desistiu",
                dificuldade=questao['dificuldade'], passos=len(passos_aluno),
                detalhes_dict=detalhes
            )
            return
        try:
            passo_sympy = parse_raw(s_passo_aluno)
            if find_counterexample(expressao_atual_sympy, passo_sympy) is None:
                print("✓ Passo VÁLIDO!")
                expressao_atual_sympy = passo_sympy
                expressao_atual_str = s_passo_aluno
                passos_aluno.append(s_passo_aluno)
            else:
                print("✗ Passo INVÁLIDO!")
                print(f"Dica: Esta questão usa a Lei da {lei}.")
                for sublei in lei.split("/"):
                    explic = LEIS_DIDATICAS.get(sublei.strip(), "(sem explicação detalhada)")
                    print(f"- {sublei.strip()}: {explic}")
                print("Tente pensar em como aplicar isso na expressão para simplificá-la.\n")
        except Exception:
            print("✗ Erro de sintaxe. Verifique sua expressão.")


def run_cli():
    database.inicializar_banco()

    print("="*40)
    print(" Tutor Interativo de Álgebra Booleana ")
    print("="*40)
    nome = input("Por favor, digite seu nome de usuário: ").strip()

    usuario_id, is_new = database.get_or_create_user(nome)

    if is_new:
        run_calibration_quiz(usuario_id, nome)
    else:
        print(f"\nBem-vindo(a) de volta, {nome}!")

    while True:
        print("\n--- Menu Principal ---")
        op = input('Escolha: (1) Simplificação, (2) Equivalência, (3) Tutor Interativo ou (4) Sair? ')

        if op == '1':
            s = input('Digite expressão: ')
            expr = parse_raw(s)

            result_data = simplify(expr)
            regras_aplicadas = print_didactic_simplification(result_data)

            simp_expr = result_data['final_sop']
            resultado_final_str = format_expr(simp_expr)

            try:
                # Lógica de dificuldade e passos
                num_vars = len(result_data.get('variables', []))
                num_minterms = len(result_data.get('minterms', []))
                num_final_terms = len(simp_expr.args) if isinstance(simp_expr, Or) else 1
                dificuldade = (num_vars * 3) + (num_minterms - num_final_terms)
                
                # Monta o dicionário de detalhes para a operação de Simplificação
                detalhes_dict = {"regras_aplicadas": regras_aplicadas}

                database.salvar_interacao(
                    operacao="Simplificação",
                    expressao_inicial=s,
                    resultado_final=resultado_final_str,
                    dificuldade=dificuldade,
                    passos=len(regras_aplicadas),
                    detalhes_dict=detalhes_dict
                )
            except Exception as e:
                print(f"\n[ERRO] Não foi possível salvar a interação no banco de dados: {e}")

            choosen = input('Deseja criar a tabela verdade? [Y/N] ')
            if(choosen.strip().upper() == 'Y'):
                create_trutable(expr, simp_expr)
            pass

        elif op == '2':
            s1 = input('Expr1: ')
            s2 = input('Expr2: ')
            expr1 = parse_raw(s1)
            expr2 = parse_raw(s2)

            result_data1 = simplify(expr1)
            result_data2 = simplify(expr2)
            result1_expr = result_data1['final_sop']
            result2_expr = result_data2['final_sop']

            ce = find_counterexample(result1_expr, result2_expr)
            veredicto = "Equivalentes" if ce is None else "Não Equivalentes"
            
            print(f'\n✓ {veredicto}.')
            if ce: print(f'  (Contraexemplo: {ce})')

            print("\n" + "="*15 + " Análise da Expr1 " + "="*15)
            regras_expr1 = print_didactic_simplification(result_data1)
            
            print("\n" + "="*15 + " Análise da Expr2 " + "="*15)
            regras_expr2 = print_didactic_simplification(result_data2)

            try:
                # Lógica de dificuldade e passos
                dificuldade1 = (len(result_data1.get('variables', [])) * 3) + (len(result_data1.get('minterms', [])) - (len(result1_expr.args) if isinstance(result1_expr, Or) else 1))
                dificuldade2 = (len(result_data2.get('variables', [])) * 3) + (len(result_data2.get('minterms', [])) - (len(result2_expr.args) if isinstance(result2_expr, Or) else 1))
                
                # Monta o dicionário de detalhes para a operação de Equivalência
                detalhes_dict = {
                    "analise_expr1": {"resultado": format_expr(result1_expr), "regras": regras_expr1},
                    "analise_expr2": {"resultado": format_expr(result2_expr), "regras": regras_expr2}
                }

                database.salvar_interacao(
                    operacao="Equivalência",
                    expressao_inicial=f"{s1} <=> {s2}",
                    resultado_final=veredicto,
                    dificuldade=(dificuldade1 + dificuldade2),
                    passos=(len(regras_expr1) + len(regras_expr2)),
                    detalhes_dict=detalhes_dict
                )
            except Exception as e:
                print(f"\n[ERRO] Não foi possível salvar a interação no banco de dados: {e}")
            
            choosen = input('\nDeseja criar a tabela verdade? [Y/N] ')
            if(choosen.strip().upper() == 'Y'):
                create_trutable(expr1, expr2)
            pass
        
        elif op == '3':
            run_interactive_tutor(usuario_id)

        elif op == '4':
            print("Ate a proxima!")
            break
            
        else:
            print("Opção inválida, tente novamente.")

if __name__ == '__main__':

    run_cli()
