
# Tutor de Álgebra Booleana.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)

Uma ferramenta de linha de comando (CLI) desenvolvida em Python para auxiliar no estudo de Álgebra Booleana. Permite simplificar expressões, verificar a equivalência entre duas expressões e gerar suas respectivas tabelas-verdade. Feita, para a matéria TÓPICOS EM SISTEMAS TUTORES INTELIGENTES.

## Funcionalidades

- **Simplificação de Expressões:** Reduz uma expressão booleana à sua forma mais simples, exibindo o passo a passo.
- **Verificação de Equivalência:** Compara duas expressões e determina se são equivalentes.
  - Se não forem, apresenta um **contraexemplo** para provar a diferença.
- **Geração de Tabela-Verdade:** Gera uma tabela-verdade para visualizar os resultados de uma ou duas expressões, provando visualmente sua equivalência ou comportamento.
- **Múltiplos Operadores:** Suporta operadores comuns como `+` (OU), `*` ou `.` (E) e `~` ou `¬` (NÃO).

## Pré-requisitos

- [Python 3.8+](https://www.python.org/downloads/)
- `pip` (gerenciador de pacotes do Python, geralmente já vem com o Python)

## Instalação

1. **Clone o repositório:**
    ```bash
    git clone URL_DO_SEU_REPOSITORIO
    cd STI-algebra-booleana-main
    ```

    
2. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Como Usar

Para iniciar a ferramenta interativa, execute o script `cli.py`:

```bash
python scripts/cli.py
or python -m scripts.cli
```
Primeiramente, o programa precisará da sua conta, coloque seu nome para começar o programa, ele irá fazer 5 questões de proeficiência para determinar o nível de habilidade sua acerca do conteúdo.
O programa irá então pedir para você escolher entre as opções de Simplificação, Equivalência, Tutor Inteligente ou Sair.
Ademais, será salvo suas respostas em um banco, determinando a cada questão certa ou errada o seu nível de conhecimento, quanto mais proximo de zero (0), menor será seu conhecimento geral, e quanto mais próximo de dez (10), maior será ele.

## Exemplos de Uso

### 1. Simplificando uma Expressão

```plaintext
Escolha: (1) Simplificação, (2) Equivalência, (3) Tutor Interativo ou (4) Sair? 1
Digite expressão: A + A * B

Passo a passo da simplificação:
- Subsunção: remove termos em A + A * B
Resultado final: A

Deseja criar a tabela verdade? [Y/N] Y

Gerando Tabela-Verdade...
 A | B | A + A*B | A | (A + A*B ↔ A)
---+---+---------+---+-----------------
 V | V |    V    | V |        V
 V | F |    V    | V |        V
 F | V |    F    | F |        V
 F | F |    F    | F |        V
```

### 2. Verificando Equivalência

```plaintext
Escolha: (1) Simplificação ou (2) Equivalência? 2
Expr1: ~(A + B)
Expr2: ~A * ~B

✓ As expressões são equivalentes.

Como Expr1 chega a Expr2:
... (passos)
= ~A & ~B

Como Expr2 é simplificado:
... (passos)
= ~A & ~B

Deseja criar a tabela verdade? [Y/N] Y

Gerando Tabela-Verdade...
 A | B | ~(A + B) | ~A & ~B | (~(A + B) ↔ ~A & ~B)
---+---+----------+---------+------------------------
 V | V |    F     |    F    |           V
 V | F |    F     |    F    |           V
 F | V |    F     |    F    |           V
 F | F |    V     |    V    |           V
```

### 3. Tutor Interativo

```plaintext
Questão (Dificuldade: 2, Lei principal: Complemento)
Simplifique a expressão: A + ~A
Quando terminar, digite 'fim'. Se quiser desistir, digite 'desisto'.
----------------------------------------
Expressão Atual (A + ~A) -> Seu passo: true
✓ Passo VÁLIDO!
Expressão Atual (true) -> Seu passo: fim

```

## Arquitetura do Tutor Inteligente

---

### 🔍 Modelo Especialista (Domain/Expert Model)

É onde está **todo o conhecimento de Álgebra Booleana** — regras, leis, algoritmos.

- `src/sti/simplifier.py`:  
  Implementa Quine–McCluskey, minterms e método de Petrick.

- `src/sti/counterexample.py`:  
  Valida equivalência lógica entre expressões.

- `src/sti/parser.py` e `src/sti/formatter.py`:  
  Cuidam de leitura e formatação das expressões.

Sempre que o usuário dá um passo, o sistema recorre a esse modelo para validar, simplificar e encontrar contraexemplos.

---

### Modelo do Estudante (Student Model)

Representa o **perfil e histórico de aprendizagem do usuário**. Está implementado via:

- **Banco SQLite**
  - Tabela `usuarios`: armazena `nivel_habilidade`.
  - Tabela `historico`: armazena tentativas, acertos, erros, passos.

- **Funções em `src/sti/database.py`**
  - `get_or_create_user()`, `get_user_skill()`: recuperam dados do usuário.
  - `update_user_skill()`: atualiza o nível após cada questão.
  - `salvar_interacao()`: salva detalhes da tentativa.

- **Modelo de Machine Learning**
  - O `modelo_tutor.pkl` (treinado em `treinar_modelo.py`) aprende com o histórico para prever qual tipo de questão é ideal para o nível do aluno.

---

### Modelo Pedagógico (Pedagogical Model)

Decide **o que e como ensinar**:

- **Seleção de questões**
  - `select_ideal_question_algoritmica()` usa regras fixas.
  - `select_ideal_question_ml()` usa o modelo treinado para encontrar a melhor zona de aprendizagem.

- **Feedback e dicas**
  - O dicionário `LEIS_DIDATICAS` + lógica em `run_interactive_tutor()` (ou na view `/tutor`) fornece orientações sem dar a resposta.

- **Encerramento**
  - O sistema só aceita “fim” quando a expressão realmente chega à forma mínima.
  - “Desisto” mostra a resposta correta.

---

## Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo LICENSE para obter detalhes.
