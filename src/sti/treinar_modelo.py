import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib 

DB_NAME = 'tutor_history.db'

def preparar_dados_treinamento():
    """Lê o histórico e o transforma em um DataFrame para treinamento."""
    conn = sqlite3.connect(DB_NAME)
    # Usamos o pandas para ler o SQL diretamente para um DataFrame, o que é muito prático
    # Pegamos apenas as tentativas do tutor inteligente que têm um resultado claro
    query = """
        SELECT h.dificuldade, u.nivel_habilidade, h.resultado_final
        FROM historico h
        JOIN usuarios u ON h.usuario_id = u.id
        WHERE h.operacao = 'Tutor Inteligente' 
        AND h.resultado_final IN ('Correto', 'Incorreto')
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return None, None

    # Engenharia de Features: transformar dados em números
    # Nossa variável alvo (y) é se o aluno acertou ou não
    df['acertou'] = df['resultado_final'].apply(lambda x: 1 if x == 'Correto' else 0)
    
    # Nossas features (X) são as características que usamos para prever
    # Por enquanto, usaremos a dificuldade da questão e o nível do usuário
    features = df[['dificuldade', 'nivel_habilidade']]
    target = df['acertou']
    
    return features, target

print("Iniciando o processo de treinamento do modelo...")

# 1. Preparar os dados
X, y = preparar_dados_treinamento()

if X is None or y is None or len(X) < 20:
    print("Dados insuficientes para o treinamento. Use mais o tutor para gerar dados.")
else:
    # 2. Dividir os dados em conjuntos de treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # 3. Escolher e treinar o modelo
    # Regressão Logística é um ótimo ponto de partida: simples, rápido e interpretável
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # 4. Avaliar o modelo
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Modelo treinado! Acurácia no conjunto de teste: {acc:.2f}")

    # 5. Salvar o modelo treinado para ser usado pelo tutor
    joblib.dump(model, 'modelo_tutor.pkl')
    print("Modelo salvo como 'modelo_tutor.pkl'. O tutor agora pode usá-lo.")