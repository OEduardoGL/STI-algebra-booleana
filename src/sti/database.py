# Arquivo: src/sti/database.py (VERSÃO FINAL E CORRIGIDA)

import sqlite3
import json
from datetime import datetime

DB_NAME = 'tutor_history.db'

def inicializar_banco():
    """Cria ou atualiza todas as tabelas necessárias."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabela de usuários (sem mudanças)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE,
            nivel_habilidade REAL DEFAULT 5.0, data_criacao TEXT NOT NULL
        )
    ''')

    # Tabela de histórico (sem mudanças)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL, operacao TEXT NOT NULL, expressao_inicial TEXT NOT NULL,
            resultado_final TEXT, dificuldade INTEGER, passos INTEGER, detalhes_json TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # NOVA TABELA: Banco de Questões
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS banco_de_questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expressao TEXT NOT NULL UNIQUE,
            solucao_simplificada TEXT NOT NULL,
            dificuldade INTEGER NOT NULL,
            lei_principal TEXT -- Ex: "Adjacência", "Absorção", etc.
        )
    ''')

    conn.commit()
    conn.close()
    # Popula o banco de questões se ele estiver vazio
    seed_question_bank()

def seed_question_bank():
    """Popula o banco de questões com exemplos iniciais se estiver vazio."""
    questoes = [
        # Dificuldade 1-3 (Leis Básicas)
        ('A + A', 'A', 1, 'Idempotência'),
        ('A * 1', 'A', 1, 'Identidade'),
        ('A + 0', 'A', 1, 'Identidade'),
        ('A * ~A', 'false', 2, 'Complemento'),
        ('A + ~A', 'true', 2, 'Complemento'),
        ('~~A', 'A', 2, 'Dupla Negação'),
        ('A * 0', 'false', 1, 'Aniquilação'),
        ('A + 1', 'true', 1, 'Aniquilação'),
        ('(A*B) + (A*B)', 'A*B', 2, 'Idempotência'),
        ('A*B*~A', 'false', 3, 'Complemento/Aniquilação'),
        ('(A*~A)*(B+C)', 'false', 3, 'Complemento/Aniquilação'),

        # Dificuldade 4-7 (Leis mais usadas)
        ('A + A*B', 'A', 4, 'Absorção'),
        ('A*(A+B)', 'A', 4, 'Absorção'),
        ('A*B + A*~B', 'A', 5, 'Adjacência'),
        ('A + ~A*B', 'A+B', 6, 'Absorção Mista'),
        ('(A+B)*(A+C)', 'A+B*C', 7, 'Distributiva'),
        ('A + (A+B)', 'A+B', 3, 'Associativa/Idempotência'),
        ('(A+B)*(~A+B)', 'B', 4, 'Distributiva/Complemento'),
        ('~A*B + A*~B + A*B', '~A*B + A', 6, 'Adjacência/Absorção'),
        ('A*B*C + ~A*B*C + A*~B*C', 'B*C + A*C', 6, 'Adjacência'),
        ('(A+B)*(A+~B)', 'A', 5, 'Distributiva/Complemento'),
        ('A*B*C + ~(A*B*C)', 'true', 6, 'Complemento'),
        ('A*B + A*~B + ~A', 'true', 6, 'Adjacência/Complemento'),
        
        # Categoria: Leis de De Morgan (Foco Principal) (Dificuldade 6-9)
        ('~(A * B)', '~A + ~B', 7, 'De Morgan'),
        ('~(~A * B)', 'A + ~B', 7, 'De Morgan/Dupla Negação'),
        ('~( (A+B) * C )', '~A*~B + ~C', 8, 'De Morgan'),
        ('A + ~(A*B)', 'true', 9, 'De Morgan/Complemento'),
        ('~(A*B + C)', '~A*~C + ~B*~C', 9, 'De Morgan/Distributiva'),
        ('~(~A*~B)', 'A+B', 7, 'De Morgan'),
        ('~(A+B) + ~(A+~B)', '~A', 8, 'De Morgan/Adjacência'),
        ('~(~(A+B))', 'A+B', 7, 'Dupla Negação'),

        # Categoria: Casos Avançados e 3 Variáveis (Dificuldade 8-10)
        ('A*B + A*~C + B*C', 'A*B + A*~C', 8, 'Consenso'),
        ('A*B*C + A*B*~C + ~A*B*C', 'A*B + B*C', 9, 'Adjacência Múltipla'),
        ('A*B + ~A*C + B*C', 'A*B + ~A*C', 10, 'Consenso'),
        ('A*~B*~C + A*B*C', 'A*~B*~C + A*B*C', 8, 'Nenhuma Simplificação (Soma)'),
        ('A*~B*~C + ~A*~B*~C + ~A*B*~C + ~A*~B*C', '~A*~B + ~A*~C + ~B*~C', 9, 'Adjacência Múltipla'),
        ('A*~B*~C + A*~B*C + A*B*C + ~A*B*C + ~A*~B*C', 'A*~B + C', 9, 'Mapa de Karnaugh (Adjacência)'),
        ('A*~B*~C + A*~B*C + ~A*B*~C + ~A*B*C', 'A*~B + ~A*B', 10, 'XOR'),
        ('A*~B*C + A*B*~C + ~A*~B*~C + ~A*B*C', 'A*~B*C + A*B*~C + ~A*~B*~C + ~A*B*C', 10, 'Nenhuma Simplificação (Soma)'),
        ('A*B*~C + B*C*A + A*~B + ~A', 'true', 7, 'Tautologia'),
        ('(A+B)*(A+C)*(B+C) + ~A*~B*~C', 'A*C + B', 9, 'Distributiva/Complemento'),
        ('A*B + A*~B + ~A*B + ~A*~B', 'true', 8, 'Tautologia (K-Map Completo)'),

        # Categoria: Expressões com 4 Variáveis (Dificuldade 10+)
        ('A*B*C*D + A*B*C*~D', 'A*B*C', 10, 'Adjacência'),
        ('W*X*Y + W*X*~Y + W*~X*Y + W*~X*~Y', 'W', 10, 'Adjacência Múltipla'),
        ('A*B*~C*~D + A*B*C*~D + A*B*~C*D + A*B*C*D', 'A*B', 10, 'Adjacência Múltipla'),
        ('~A*~B*~C*~D + ~A*~B*C*~D + A*~B*~C*~D + A*~B*C*~D', '~B*~D', 10, 'Adjacência Múltipla'),
        ('A*B + C*D', 'A*B + C*D', 10, 'Nenhuma Simplificação'),
        ('W*X*Y*Z + W*X*Y*~Z + W*X*~Y*Z + W*X*~Y*~Z', 'W*X', 10, 'Adjacência Múltipla'),
        ('A*B*C + A*B*D + A*C*D + B*C*D', 'A*B*C + A*B*D + A*C*D', 10, 'Consenso (4 vars)')
    ]
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM banco_de_questoes")
    if cursor.fetchone()[0] == 0:
        print("Populando o banco de questões pela primeira vez...")
        cursor.executemany("INSERT INTO banco_de_questoes (expressao, solucao_simplificada, dificuldade, lei_principal) VALUES (?, ?, ?, ?)", questoes)
        conn.commit()
    conn.close()

def get_or_create_user(nome):
    """
    Busca um usuário pelo nome. Se não existir, cria um novo.
    Retorna o ID do usuário e um booleano indicando se é um novo usuário.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Busca o usuário
    cursor.execute("SELECT id FROM usuarios WHERE nome = ?", (nome,))
    user = cursor.fetchone()
    
    if user:
        # Usuário encontrado
        conn.close()
        return user[0], False # Retorna ID e is_new = False
    else:
        # Usuário novo, vamos criar
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO usuarios (nome, data_criacao) VALUES (?, ?)", (nome, timestamp))
        new_user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_user_id, True # Retorna novo ID e is_new = True
    
def get_user_skill(usuario_id):
    """Busca o nível de habilidade atual de um usuário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nivel_habilidade FROM usuarios WHERE id = ?", (usuario_id,))
    skill = cursor.fetchone()
    conn.close()
    return skill[0] if skill else 5.0 # Retorna 5.0 como padrão

def update_user_skill(usuario_id, acertou, dificuldade_questao):
    """Atualiza o nível de habilidade do usuário com base no desempenho."""
    skill_atual = get_user_skill(usuario_id)
    if acertou:
        # Ganha mais pontos por questões difíceis
        novo_skill = skill_atual + (dificuldade_questao / 10.0)
    else:
        # Perde mais pontos por errar questões fáceis
        novo_skill = skill_atual - ((11 - dificuldade_questao) / 10.0)
    
    # Garante que o nível fique entre 1 e 10
    novo_skill = max(1.0, min(10.0, novo_skill))
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET nivel_habilidade = ? WHERE id = ?", (novo_skill, usuario_id))
    conn.commit()
    conn.close()
    print(f"(Nível de habilidade atualizado para: {novo_skill:.2f})")

def salvar_interacao(usuario_id, operacao, expressao_inicial, resultado_final, dificuldade, passos, detalhes_dict):
    """Salva uma nova interação, agora associada a um usuário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    detalhes_json_str = json.dumps(detalhes_dict, ensure_ascii=False)
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO historico (usuario_id, timestamp, operacao, expressao_inicial, resultado_final, dificuldade, passos, detalhes_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (usuario_id, timestamp_atual, operacao, expressao_inicial, resultado_final, dificuldade, passos, detalhes_json_str))

    conn.commit()
    conn.close()