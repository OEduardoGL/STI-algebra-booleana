
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


## Licença

Este projeto está licenciado sob a licença MIT - consulte o arquivo LICENSE para obter detalhes.
