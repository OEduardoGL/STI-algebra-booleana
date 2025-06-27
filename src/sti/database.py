import sqlite3
import json 
from datetime import datetime

DB_NAME = 'tutor_history.db'

def inicializar_banco():
    """
    Cria o banco de dados e a tabela de histórico se não existirem.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Cria a tabela para armazenar as interações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            operacao TEXT NOT NULL, -- "Simplificação" ou "Equivalência"
            expressao_inicial TEXT NOT NULL,
            dificuldade INTEGER,
            passos INTEGER,
            regras_usadas TEXT -- Armazenaremos como um JSON
        )
    ''')

    conn.commit()
    conn.close()

def salvar_interacao(operacao, expressao, dificuldade, passos, regras):
    """
    Salva uma nova interação do aluno no banco de dados.

    Args:
        operacao (str): O tipo de operação (ex: "Simplificação").
        expressao (str): A expressão ou expressões que o aluno inseriu.
        dificuldade (int): Um número que representa a dificuldade.
        passos (int): O número de passos na simplificação.
        regras (list): Uma lista de strings com as regras utilizadas.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Usamos json.dumps para converter a lista de regras em uma string
    regras_json = json.dumps(regras, ensure_ascii=False)
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO historico (timestamp, operacao, expressao_inicial, dificuldade, passos, regras_usadas)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp_atual, operacao, expressao, dificuldade, passos, regras_json))

    conn.commit()
    conn.close()
    print(">>> Interação salva no banco de dados com sucesso!")

# Exemplo de como visualizar os dados (opcional, para testes)
def ver_historico():
    """
    Lê e imprime todo o histórico salvo no banco de dados.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM historico")
    registros = cursor.fetchall()

    if not registros:
        print("Nenhum histórico encontrado.")
        return

    for registro in registros:
        # Usamos json.loads para converter a string de volta para uma lista
        regras = json.loads(registro[6])
        print(f"""
------------------------------------
ID: {registro[0]}
Data/Hora: {registro[1]}
Operação: {registro[2]}
Expressão: {registro[3]}
Dificuldade: {registro[4]}
Passos: {registro[5]}
Regras Usadas: {', '.join(regras)}
------------------------------------
        """)
    conn.close()