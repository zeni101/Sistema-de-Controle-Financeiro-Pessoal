import sqlite3
import customtkinter as ctk
from tkinter import messagebox

# Configuração da janela
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("Meu Financeiro")
app.geometry("1100x800")
app.minsize(850, 650)

# Cores
FUNDO = "#F3F7F4"
VERDE = "#17452F"
VERDE_CLARO = "#E5F4EB"
VERMELHO = "#E85D4A"
BRANCO = "#FFFFFF"
TEXTO = "#1D2B22"

app.configure(fg_color=FUNDO)

#Banco de dados
conn = sqlite3.connect("financeiro.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS financeiro(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descricao TEXT,
        valor REAL,
        categoria TEXT
    )
""")
cursor.execute("PRAGMA table_info(financeiro)")
colunas = [coluna[1] for coluna in cursor.fetchall()]
if "categoria" not in colunas:
    cursor.execute("ALTER TABLE financeiro ADD COLUMN categoria TEXT")
conn.commit()

# Dados do sistema
receita_atual = 0.0
despesa_atual = 0.0
movimentacoes = []

def formatar_dinheiro(valor):
    valor_formatado = f"{valor:,.2f}"
    valor_formatado = valor_formatado.replace(",", "X")
    valor_formatado = valor_formatado.replace(".", ",")
    valor_formatado = valor_formatado.replace("X", ".")
    return f"R$ {valor_formatado}"

def atualizar_painel():
    saldo = receita_atual - despesa_atual

    label_receita.configure(
        text=formatar_dinheiro(receita_atual)
    )
    label_despesa.configure(
        text=formatar_dinheiro(despesa_atual)
    )
    label_saldo.configure(
        text=formatar_dinheiro(saldo)
    )

def atualizar_historico():
    # Limpa as linhas anteriores
    for widget in frame_historico.winfo_children():
        widget.destroy()

    if not movimentacoes:
        ctk.CTkLabel(
            frame_historico,
            text="Nenhuma movimentação cadastrada.",
            text_color="gray"
        ).pack(pady=20)
        return

    for item in reversed(movimentacoes):
        linha = ctk.CTkFrame(
            frame_historico,
            fg_color=BRANCO,
            corner_radius=10
        )
        linha.pack(fill="x", padx=5, pady=5)

        esquerda = ctk.CTkFrame(
            linha, fg_color="transparent"
        )
        esquerda.pack(side="left", padx=15, pady=12)

        ctk.CTkLabel(
            esquerda,
            text=item["descricao"],
            font=("Arial", 15, "bold"),
            text_color=TEXTO
        ).pack(anchor="w")

        ctk.CTkLabel(
            esquerda,
            text=f'{item["tipo"]} • {item["categoria"]}',
            text_color="gray"
        ).pack(anchor="w")

        # Botão para excluir a movimentação
        ctk.CTkButton(
            linha,
            text="X",
            width=32,
            height=32,
            fg_color=VERMELHO,
            hover_color="#A61B1B",
            command=lambda id_mov=item["id"]: excluir_movimentacao(id_mov)
        ).pack(side="right", padx=10)

        sinal = "+" if item["tipo"] == "Receita" else "-"
        cor = "#16834A" if item["tipo"] == "Receita" else VERMELHO

        ctk.CTkLabel(
            linha,
            text=f'{sinal} {formatar_dinheiro(item["valor"])}',
            font=("Arial", 14, "bold"),
            text_color=cor
        ).pack(side="right", padx=10)

def excluir_movimentacao(id_movimentacao):
    global receita_atual, despesa_atual

    confirmar = messagebox.askyesno(
        "Confirmar exclusão",
        "Deseja realmente excluir esta movimentação?"
    )

    if not confirmar:
        return

    try:
        cursor.execute(
            "DELETE FROM financeiro WHERE id = ?",
            (id_movimentacao,)
        )
        conn.commit()

    except sqlite3.Error as erro:
        messagebox.showerror(
            "Erro!",
            f"Não foi possível excluir a movimentação:\n{erro}"
        )
        return

    # Remove da lista que está na memória
    movimentacoes[:] = [
        item for item in movimentacoes
        if item["id"] != id_movimentacao
    ]
     # Recalcula receitas e despesas
    receita_atual = 0.0
    despesa_atual = 0.0

    for item in movimentacoes:
        if item["tipo"] == "Receita":
            receita_atual += item["valor"]
        elif item["tipo"] == "Despesa":
            despesa_atual += item["valor"]

    # Atualiza o painel e o histórico
    atualizar_painel()
    atualizar_historico()

def adicionar_movimentacao(tipo):
    global receita_atual, despesa_atual

    descricao = entrada_descricao.get().strip()
    valor_texto = entrada_valor.get().strip().replace(",", ".")

    if not descricao:
        messagebox.showwarning(
            "Atenção", "Preencha a descrição.")
        return
    try:
        valor = float(valor_texto)
    except ValueError:
        messagebox.showerror(
            "Erro", "Digite um valor numérico válido.")
        return   
    if valor <= 0:
        messagebox.showwarning(
            "Atenção", "O valor deve ser maior que zero."
        )
        return
    categoria = menu_categoria.get()

    #Salvar no banco de dados
    try:
        cursor.execute("""INSERT INTO financeiro(
            tipo, descricao, valor, categoria
        )
        VALUES(?,?,?,?)
        """, (tipo, descricao, valor, categoria))
        conn.commit()
        id_movimentacao = cursor.lastrowid
    except sqlite3.Error as erro:
        messagebox.showerror(
            "Erro!",
            f"Não foi possível salvar a movimentação: \n{erro}"
        )
        return
    movimentacao = {
        "id": id_movimentacao,
        "descricao": descricao,
        "valor": valor,
        "tipo": tipo,
        "categoria": categoria
    }

    movimentacoes.append(movimentacao)

    if tipo == "Receita":
        receita_atual += valor
    else:
        despesa_atual += valor

    atualizar_painel()
    atualizar_historico()

    entrada_descricao.delete(0, "end")
    entrada_valor.delete(0, "end")

def carregar_movimentacoes():
    global receita_atual, despesa_atual

    # Consultar registros salvos
    cursor.execute("""
        SELECT id, tipo, descricao, valor, categoria
        FROM financeiro
        ORDER BY id ASC
    """)
    registros = cursor.fetchall()

    movimentacoes.clear()
    receita_atual = 0.0
    despesa_atual = 0.0

    for registro in registros:
        id_mov, tipo, descricao, valor, categoria = registro

        movimentacao = {
            "id": id_mov,
            "tipo": tipo,
            "descricao": descricao,
            "valor": valor,
            "categoria": categoria or "Outros"
        }

        movimentacoes.append(movimentacao)

        if tipo == "Receita":
            receita_atual += valor
        elif tipo == "Despesa":
            despesa_atual += valor

    atualizar_painel()
    atualizar_historico()

def fechar_app():
    conn.close()
    app.destroy()

# Cabeçalho
cabecalho = ctk.CTkFrame(
    app, fg_color=BRANCO, corner_radius=0
)
cabecalho.pack(fill="x")

ctk.CTkLabel(
    cabecalho,
    text="  MEU FINANCEIRO",
    font=("Arial", 21, "bold"),
    text_color=VERDE
).pack(side="left", padx=25, pady=20)

ctk.CTkLabel(
    cabecalho,
    text="CONTROLE PESSOAL",
    text_color="gray"
).pack(side="right", padx=25)


# Conteúdo principal
conteudo = ctk.CTkFrame(app, fg_color="transparent")
conteudo.pack(fill="both", expand=True, padx=25, pady=20)

ctk.CTkLabel(
    conteudo,
    text="Visão geral",
    text_color="gray",
    font=("Arial", 13)
).pack(anchor="w")

ctk.CTkLabel(
    conteudo,
    text="Olá, veja como estão suas finanças.",
    font=("Arial", 25, "bold"),
    text_color=TEXTO
).pack(anchor="w", pady=(5, 20))


# Cartões financeiros
frame_cartoes = ctk.CTkFrame(
    conteudo, fg_color="transparent"
)
frame_cartoes.pack(fill="x", pady=(0, 20))

for coluna in range(3):
    frame_cartoes.grid_columnconfigure(coluna, weight=1)

def criar_cartao(coluna, titulo, cor_valor):
    cartao = ctk.CTkFrame(
        frame_cartoes,
        fg_color=BRANCO,
        corner_radius=15,
        height=115
    )
    cartao.grid(
        row=0, column=coluna,
        sticky="ew", padx=6
    )
    cartao.grid_propagate(False)

    ctk.CTkLabel(
        cartao,
        text=titulo,
        text_color="gray"
    ).pack(anchor="w", padx=18, pady=(17, 5))

    valor = ctk.CTkLabel(
        cartao,
        text="R$ 0,00",
        font=("Arial", 21, "bold"),
        text_color=cor_valor
    )
    valor.pack(anchor="w", padx=18)
    return valor

label_receita = criar_cartao(0, "Receitas", "#16834A")
label_despesa = criar_cartao(1, "Despesas", VERMELHO)

# Cartão especial para o saldo
cartao_saldo = ctk.CTkFrame(
    frame_cartoes,
    fg_color=VERDE,
    corner_radius=15,
    height=115
)
cartao_saldo.grid(row=0, column=2, sticky="ew", padx=6)
cartao_saldo.grid_propagate(False)

ctk.CTkLabel(
    cartao_saldo,
    text="Saldo disponível",
    text_color=BRANCO
).pack(anchor="w", padx=18, pady=(17, 5))

label_saldo = ctk.CTkLabel(
    cartao_saldo,
    text="R$ 0,00",
    font=("Arial", 21, "bold"),
    text_color=BRANCO
)
label_saldo.pack(anchor="w", padx=18)

# Formulário de lançamento
formulario = ctk.CTkFrame(
    conteudo,
    fg_color=BRANCO,
    corner_radius=15
)
formulario.pack(fill="x", pady=(0, 20))

ctk.CTkLabel(
    formulario,
    text="Adicionar transação",
    font=("Arial", 20, "bold"),
    text_color=TEXTO
).pack(anchor="w", padx=20, pady=(18, 12))

entrada_descricao = ctk.CTkEntry(
    formulario,
    placeholder_text="Descrição (ex.: Supermercado)",
    height=40
)
entrada_descricao.pack(fill="x", padx=20, pady=6)

frame_campos = ctk.CTkFrame(
    formulario, fg_color="transparent"
)
frame_campos.pack(fill="x", padx=14, pady=5)

frame_campos.grid_columnconfigure((0, 1), weight=1)

entrada_valor = ctk.CTkEntry(
    frame_campos,
    placeholder_text="Valor (ex.: 150,50)",
    height=40
)
entrada_valor.grid(
    row=0, column=0, sticky="ew", padx=6
)

menu_categoria = ctk.CTkOptionMenu(
    frame_campos,
    values=[
        "Alimentação",
        "Transporte",
        "Moradia",
        "Salário",
        "Lazer",
        "Outros"
    ],
    height=40
)
menu_categoria.grid(
    row=0, column=1, sticky="ew", padx=6
)

frame_botoes = ctk.CTkFrame(
    formulario, fg_color="transparent"
)
frame_botoes.pack(fill="x", padx=20, pady=(8, 20))

ctk.CTkButton(
    frame_botoes,
    text="+ Adicionar receita",
    fg_color="#16834A",
    hover_color="#11663A",
    height=42,
    command=lambda: adicionar_movimentacao("Receita")
).pack(side="left", fill="x", expand=True, padx=(0, 5))

ctk.CTkButton(
    frame_botoes,
    text="− Adicionar despesa",
    fg_color=VERMELHO,
    hover_color="#C94839",
    height=42,
    command=lambda: adicionar_movimentacao("Despesa")
).pack(side="left", fill="x", expand=True, padx=(5, 0))

# Histórico
ctk.CTkLabel(
    conteudo,
    text="Últimas movimentações",
    font=("Arial", 20, "bold"),
    text_color=TEXTO
).pack(anchor="w", pady=(0, 10))

frame_historico = ctk.CTkScrollableFrame(
    conteudo,
    fg_color=FUNDO,
    corner_radius=10
)
frame_historico.pack(fill="both", expand=True)

carregar_movimentacoes()
app.protocol("WM_DELETE_WINDOW", fechar_app)

app.mainloop()