import tkinter as tk
from tkinter import messagebox, scrolledtext

from src.sti.parser import parse_raw
from src.sti.formatter import format_expr
from src.sti.simplifier import simplify
from src.sti.counterexample import find_counterexample
from src.sti.truth_table import create_trutable


def simplificar_expressao():
    entrada = entry_expr.get()
    if not entrada.strip():
        messagebox.showwarning("Aviso", "Digite uma expressão.")
        return
    try:
        expr = parse_raw(entrada)
        log = []
        resultado = simplify(expr, log)
        output.delete("1.0", tk.END)
        output.insert(tk.END, "Passo a passo:\n")
        for passo in log:
            output.insert(tk.END, f"- {passo}\n")
        output.insert(tk.END, f"\nResultado final: {format_expr(resultado)}\n")

        if gerar_tabela_var.get():
            mostrar_tabela_verdade(expr, resultado)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao simplificar: {str(e)}")


def verificar_equivalencia():
    s1 = entry_expr1.get()
    s2 = entry_expr2.get()
    if not s1.strip() or not s2.strip():
        messagebox.showwarning("Aviso", "Digite as duas expressões.")
        return
    try:
        expr1 = parse_raw(s1)
        expr2 = parse_raw(s2)
        log1, log2 = [], []
        r1 = simplify(expr1, log1)
        r2 = simplify(expr2, log2)
        output.delete("1.0", tk.END)

        if r1 == r2:
            output.insert(tk.END, "✓ As expressões são equivalentes.\n")
        else:
            output.insert(tk.END, "✗ As expressões NÃO são equivalentes.\n")
            ce = find_counterexample(r1, r2)
            output.insert(tk.END, f"Contraexemplo: {ce}\n")

        output.insert(tk.END, "\nExpr1:\n")
        for passo in log1:
            output.insert(tk.END, f"- {passo}\n")
        output.insert(tk.END, "\nExpr2:\n")
        for passo in log2:
            output.insert(tk.END, f"- {passo}\n")

        if gerar_tabela_var.get():
            mostrar_tabela_verdade(expr1, expr2)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar equivalência: {str(e)}")


def mostrar_tabela_verdade(*expressions):
    try:
        from io import StringIO
        import sys

        buffer = StringIO()
        sys_stdout = sys.stdout
        sys.stdout = buffer

        create_trutable(*expressions)

        sys.stdout = sys_stdout
        tabela = buffer.getvalue()
        output.insert(tk.END, "\nTabela Verdade:\n")
        output.insert(tk.END, tabela)
        buffer.close()
    except Exception as e:
        output.insert(tk.END, f"\nErro ao gerar tabela verdade: {str(e)}\n")


# ========== INTERFACE ==========

janela = tk.Tk()
janela.title("Simplificador e Verificador Lógico - STI")
janela.configure(bg="#f2f2f2")  # fundo claro e suave

# Cores suaves
label_fg = "#333333"       # cinza escuro
entry_bg = "#ffffff"       # branco
entry_fg = "#222222"
button_bg = "#a0c4ff"      # azul claro
button_fg = "#000000"
output_bg = "#f8f9fa"      # quase branco
output_fg = "#1a1a1a"
highlight_color = "#0077b6"

# Layout
tk.Label(janela, text="Expressão:", bg="#f2f2f2", fg=label_fg).pack()
entry_expr = tk.Entry(janela, width=50, bg=entry_bg, fg=entry_fg, insertbackground='black')
entry_expr.pack()

gerar_tabela_var = tk.BooleanVar()
chk = tk.Checkbutton(janela, text="Gerar tabela verdade", variable=gerar_tabela_var,
                     bg="#f2f2f2", fg=label_fg, selectcolor="#f2f2f2", activebackground="#f2f2f2")
chk.pack()

tk.Button(janela, text="Simplificar", command=simplificar_expressao,
          bg=button_bg, fg=button_fg, activebackground=highlight_color).pack(pady=5)

tk.Label(janela, text="Verificar Equivalência (Expr1 vs Expr2):", bg="#f2f2f2", fg=label_fg).pack()
entry_expr1 = tk.Entry(janela, width=50, bg=entry_bg, fg=entry_fg, insertbackground='black')
entry_expr1.pack()
entry_expr2 = tk.Entry(janela, width=50, bg=entry_bg, fg=entry_fg, insertbackground='black')
entry_expr2.pack()

tk.Button(janela, text="Verificar", command=verificar_equivalencia,
          bg=button_bg, fg=button_fg, activebackground=highlight_color).pack(pady=5)

output = scrolledtext.ScrolledText(janela, width=80, height=25,
                                   bg=output_bg, fg=output_fg, insertbackground='black')
output.pack()

janela.mainloop()
