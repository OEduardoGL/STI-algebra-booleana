from sympy import true, false
from sympy.logic.boolalg import And, Or, Not, BooleanFunction
from itertools import combinations, chain
from collections import defaultdict
from .formatter import format_expr

# --- FUNÇÕES AUXILIARES PARA O ALGORITMO ---

def get_vars_and_minterms(expr):
    """Extrai as variáveis e os minterms (saídas verdadeiras da tabela-verdade) da expressão."""
    variables = sorted(list(expr.atoms()), key=str)
    minterms = []
    
    # Itera por todas as combinações da tabela-verdade
    for i in range(2**len(variables)):
        # Monta a substituição (ex: {A: True, B: False})
        truth_values = {}
        temp_i = i
        for var in reversed(variables):
            truth_values[var] = (temp_i % 2 == 1)
            temp_i //= 2
        
        # Se a expressão for verdadeira para esta combinação, é um minterm
        if expr.subs(truth_values) is true:
            minterms.append(i)
            
    return variables, minterms

def combine_terms(t1, t2):
    """Compara dois termos. Se eles diferem por um bit, combina-os."""
    diff_count = 0
    diff_index = -1
    for i in range(len(t1)):
        if t1[i] != t2[i]:
            diff_count += 1
            diff_index = i
    
    if diff_count == 1:
        new_term = list(t1)
        new_term[diff_index] = '-'
        return "".join(new_term)
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
    if len(lits) == 1: return lits[0]
    return And(*lits)

def simplify(expr, log):
    # 1. Obter Variáveis e Minterms
    variables, minterms = get_vars_and_minterms(expr)
    num_vars = len(variables)
    
    if not minterms: return false # Se não há saídas verdadeiras, o resultado é Falso
    if len(minterms) == 2**num_vars: return true # Se todas as saídas são verdadeiras, o resultado é Verdadeiro

    log.append({'rule': 'Minterms', 'details': f"Variáveis: {', '.join(map(str, variables))}, Minterms: {minterms}"})

    # 2. Agrupar Minterms pelo número de '1's
    groups = defaultdict(list)
    for mt in minterms:
        # Converte o minterm para binário, ex: 5 -> '0101'
        binary_str = format(mt, f'0{num_vars}b')
        groups[binary_str.count('1')].append(binary_str)

    # 3. Gerar Implicantes Primos
    prime_implicants = set()
    
    current_groups = groups
    while True:
        next_groups = defaultdict(list)
        used_terms = set()
        
        # Compara grupos adjacentes
        sorted_keys = sorted(current_groups.keys())
        for i in range(len(sorted_keys) - 1):
            key1, key2 = sorted_keys[i], sorted_keys[i+1]
            for term1 in current_groups[key1]:
                for term2 in current_groups[key2]:
                    combined = combine_terms(term1, term2)
                    if combined:
                        next_groups[combined.count('1')].append(combined)
                        used_terms.add(term1)
                        used_terms.add(term2)
        
        # Adiciona termos que não puderam ser combinados (são implicantes primos)
        for key in current_groups:
            for term in current_groups[key]:
                if term not in used_terms:
                    prime_implicants.add(term)
        
        if not next_groups:
            break
        
        # Remove duplicatas nos próximos grupos
        for key in next_groups:
            next_groups[key] = sorted(list(set(next_groups[key])))
        
        current_groups = next_groups

    log.append({'rule': 'Implicantes Primos', 'details': ', '.join(map(str, prime_implicants))})

    # 4. Tabela de Cobertura (Prime Implicant Chart)
    chart = defaultdict(list)
    for mt in minterms:
        binary_mt = format(mt, f'0{num_vars}b')
        for pi in prime_implicants:
            # Verifica se o implicante primo "cobre" o minterm
            covers = all(pi[i] == '-' or pi[i] == binary_mt[i] for i in range(num_vars))
            if covers:
                chart[mt].append(pi)
    
    # 5. Encontrar a Cobertura Mínima
    # Primeiro, encontra os Implicantes Essenciais
    essential_pis = set()
    for mt in chart:
        if len(chart[mt]) == 1:
            essential_pis.add(chart[mt][0])
    
    log.append({'rule': 'Implicantes Essenciais', 'details': ', '.join(map(str, essential_pis))})

    # Cobre os minterms com os implicantes essenciais
    covered_minterms = set()
    for pi in essential_pis:
        for mt in minterms:
            binary_mt = format(mt, f'0{num_vars}b')
            if all(pi[i] == '-' or pi[i] == binary_mt[i] for i in range(num_vars)):
                covered_minterms.add(mt)
    
    uncovered_minterms = set(minterms) - covered_minterms
    
    # Se ainda faltar cobrir minterms, resolve com os implicantes restantes (Petrick's Method simplificado)
    final_pis = set(essential_pis)
    if uncovered_minterms:
        remaining_pis = prime_implicants - essential_pis
        
        # Encontra a melhor combinação de implicantes restantes para cobrir o que falta
        # (Esta é uma versão simplificada, para casos mais complexos, um algoritmo recursivo é necessário)
        # Para a maioria dos casos de sala de aula, isso é suficiente.
        
        # Ordena os implicantes restantes por quantos novos minterms eles cobrem
        pi_coverage = {pi: sum(1 for mt in uncovered_minterms if pi in chart[mt]) for pi in remaining_pis}
        sorted_pis = sorted(remaining_pis, key=lambda p: pi_coverage[p], reverse=True)
        
        temp_uncovered = set(uncovered_minterms)
        for pi in sorted_pis:
            if not temp_uncovered: break
            # Se o implicante cobre algum minterm que ainda falta, adicione-o
            if any(pi in chart[mt] for mt in temp_uncovered):
                final_pis.add(pi)
                for mt in list(temp_uncovered):
                    if pi in chart[mt]:
                        temp_uncovered.remove(mt)


    # 6. Construir a Expressão Final
    final_terms_expr = [term_to_expr(variables, pi) for pi in final_pis]
    
    if not final_terms_expr: return false
    final_expr = Or(*final_terms_expr)

    log.append({'rule': 'Resultado Final', 'details': format_expr(final_expr)})

    return final_expr