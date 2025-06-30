# Arquivo: src/sti/simplifier.py
# --- VERSÃO FINAL COM QUINE-MCCLUSKEY CORRETO E ROBUSTO ---

from sympy import true, false
from sympy.logic.boolalg import And, Or, Not
from itertools import combinations, chain
from collections import defaultdict
from .formatter import format_expr

# --- FUNÇÕES AUXILIARES PARA O ALGORITMO ---

def get_vars_and_minterms(expr):
    """Extrai as variáveis e os minterms (saídas verdadeiras) da expressão."""
    try:
        variables = sorted(list(expr.atoms()), key=str)
    except Exception:
        if expr is true: return [], [0]
        if expr is false: return [], []
        variables = [expr] if expr.is_Symbol else []
        
    minterms = []
    if not variables:
        return [], [0] if expr is true else []

    num_vars = len(variables)
    for i in range(2**num_vars):
        truth_values = {var: (i >> j) & 1 for j, var in enumerate(reversed(variables))}
        if expr.subs(truth_values) == True:
            minterms.append(i)
            
    return variables, minterms

def combine_terms(t1, t2):
    """Compara dois termos binários. Se diferem por um bit, combina-os."""
    diff = 0
    pos = -1
    for i in range(len(t1)):
        if t1[i] != t2[i]:
            diff += 1
            pos = i
    if diff == 1:
        return t1[:pos] + '-' + t1[pos+1:]
    return None

def term_to_expr(variables, term_str):
    """Converte uma string de termo (ex: '1-0') de volta para uma expressão sympy."""
    lits = []
    for i, char in enumerate(term_str):
        if char == '1':
            lits.append(variables[i])
        elif char == '0':
            lits.append(Not(variables[i]))
    
    if not lits: return true
    return And(*lits) if len(lits) > 1 else lits[0]

def solve_petrick(chart, uncovered_minterms, remaining_pis):
    """Resolve a cobertura usando o Método de Petrick para garantir a solução mínima."""
    if not uncovered_minterms:
        return set()
        
    P = []
    for mt in sorted(list(uncovered_minterms)):
        # Cria um termo de soma para cada minterm (ex: P1+P2)
        P.append([pi for pi in remaining_pis if pi in chart[mt]])
    
    # Expande a expressão (P1+P2)*(P3+P4) -> P1P3+P1P4+P2P3+P2P4
    while len(P) > 1:
        p1 = P.pop(0)
        p2 = P.pop(0)
        res = set()
        for i1 in p1:
            for i2 in p2:
                # Usa um conjunto para que A*A=A
                if isinstance(i1, set):
                    term = set(i1)
                else:
                    term = {i1}
                if isinstance(i2, set):
                    term.update(i2)
                else:
                    term.add(i2)
                res.add(frozenset(term)) # Usa frozenset para poder adicionar a um conjunto
        P.insert(0, list(res))

    # Encontra o termo com o menor número de implicantes
    min_len = float('inf')
    best_solution = None
    for term_set in P[0]:
        if len(term_set) < min_len:
            min_len = len(term_set)
            best_solution = term_set
            
    return set(best_solution)

# --- FUNÇÃO PRINCIPAL DO SIMPLIFICADOR ---
def simplify(expr):
    """
    Simplifica a expressão booleana usando Quine-McCluskey e retorna um 
    dicionário com todos os passos intermediários para a impressão didática.
    """
    variables, minterms = get_vars_and_minterms(expr)
    num_vars = len(variables)
    
    # Casos triviais
    if not minterms: 
        return {"final_sop": false, "steps": "Expressão resulta em Falso."}
    if len(minterms) == 2**num_vars: 
        return {"final_sop": true, "steps": "Expressão resulta em Verdadeiro."}

    # 1. Agrupar Minterms
    groups = defaultdict(list)
    for mt in minterms:
        binary_str = format(mt, f'0{num_vars}b')
        groups[binary_str.count('1')].append(binary_str)

    # --- ADICIONADO 1/3: Inicializa o log de combinações ---
    combination_log = []

    # 2. Gerar Implicantes Primos
    prime_implicants_str = set()
    current_groups = groups
    while True:
        next_groups = defaultdict(list)
        used_terms = set()
        
        sorted_keys = sorted(current_groups.keys())
        for i in range(len(sorted_keys) - 1):
            for term1 in current_groups[sorted_keys[i]]:
                for term2 in current_groups[sorted_keys[i+1]]:
                    combined = combine_terms(term1, term2)
                    if combined:
                        next_groups[combined.count('1')].append(combined)
                        used_terms.add(term1)
                        used_terms.add(term2)
                        # --- ADICIONADO 2/3: Registra o passo de combinação no log ---
                        combination_log.append({'before': sorted([term1, term2]), 'after': combined})
        
        for key in current_groups:
            for term in current_groups[key]:
                if term not in used_terms:
                    prime_implicants_str.add(term)
        
        if not next_groups: break
        current_groups = {k: sorted(list(set(v))) for k, v in next_groups.items()}

    # 3. Tabela de Cobertura
    chart = {mt: [pi for pi in prime_implicants_str if all(pi[i] == '-' or pi[i] == format(mt, f'0{num_vars}b')[i] for i in range(num_vars))] for mt in minterms}
    
    # 4. Encontrar Implicantes Essenciais
    essential_pis_str = set()
    for mt, pis in chart.items():
        if len(pis) == 1:
            essential_pis_str.add(pis[0])
    
    # 5. Cobrir e Resolver o Restante (Método de Petrick)
    covered_minterms = set()
    for pi in essential_pis_str:
        for mt in minterms:
            if pi in chart[mt]:
                covered_minterms.add(mt)
    
    uncovered_minterms = set(minterms) - covered_minterms
    final_pis_str = set(essential_pis_str)
    
    if uncovered_minterms:
        remaining_pis = prime_implicants_str - essential_pis_str
        cover_solution = solve_petrick(chart, uncovered_minterms, remaining_pis)
        final_pis_str.update(cover_solution)

    # 6. Construir a Expressão Final
    final_terms_expr = [term_to_expr(variables, pi) for pi in final_pis_str]
    final_expr = Or(*final_terms_expr) if len(final_terms_expr) > 1 else (final_terms_expr[0] if final_terms_expr else false)

    # 7. Montar o dicionário de resultados
    result_data = {
        "initial_expr": expr,
        "variables": variables,
        "minterms": minterms,
        # --- ADICIONADO 3/3: Inclui o log de combinações no resultado final ---
        "combination_log": combination_log,
        "final_sop": final_expr,
    }
    return result_data