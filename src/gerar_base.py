"""
Monta um banco SQLite de contas a receber (faturamento) com dados realistas,
para a análise de inadimplência. Tabelas: clientes, faturas, pagamentos.
Autora: Ana Paula Galdino
"""
import os, sqlite3, random
from datetime import date, timedelta
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("FATDB", os.path.join(BASE, "dados", "faturamento.db"))
rng = np.random.default_rng(11); random.seed(11)
HOJE = date(2026, 6, 23)

segmentos = {"Varejo": 0.18, "Atacado": 0.10, "Corporativo": 0.05}   # risco base de inadimplência
regioes = ["SP", "RJ", "MG", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
prazos = [30, 45, 60]

if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB); cur = con.cursor()
cur.executescript("""
CREATE TABLE clientes (
  id INTEGER PRIMARY KEY, nome TEXT, segmento TEXT, regiao TEXT, desde TEXT);
CREATE TABLE faturas (
  id INTEGER PRIMARY KEY, cliente_id INTEGER, data_emissao TEXT,
  data_vencimento TEXT, valor REAL, FOREIGN KEY(cliente_id) REFERENCES clientes(id));
CREATE TABLE pagamentos (
  id INTEGER PRIMARY KEY, fatura_id INTEGER, data_pagamento TEXT, valor_pago REAL,
  FOREIGN KEY(fatura_id) REFERENCES faturas(id));
""")

# Clientes
n_clientes = 180
for i in range(1, n_clientes + 1):
    seg = random.choices(list(segmentos), weights=[5, 3, 2])[0]
    reg = random.choice(regioes)
    desde = HOJE - timedelta(days=int(rng.integers(180, 2200)))
    cur.execute("INSERT INTO clientes VALUES (?,?,?,?,?)",
                (i, f"Cliente {i:03d}", seg, reg, desde.isoformat()))

# Faturas e pagamentos (24 meses)
fid = 0; pid = 0
for _ in range(2300):
    cli = int(rng.integers(1, n_clientes + 1))
    cur.execute("SELECT segmento FROM clientes WHERE id=?", (cli,))
    seg = cur.fetchone()[0]
    emissao = HOJE - timedelta(days=int(rng.integers(0, 720)))
    prazo = random.choice(prazos)
    venc = emissao + timedelta(days=prazo)
    # valor depende do segmento
    base = {"Varejo": 1500, "Atacado": 9000, "Corporativo": 32000}[seg]
    valor = round(float(rng.gamma(2.0, base / 2)) + 200, 2)
    fid += 1
    cur.execute("INSERT INTO faturas VALUES (?,?,?,?,?)",
                (fid, cli, emissao.isoformat(), venc.isoformat(), valor))
    # pagamento: probabilidade de atraso/inadimplência por segmento
    risco = segmentos[seg]
    paga = rng.random() > (risco * 0.5)        # parte vira inadimplência (não paga)
    if paga:
        # atraso: maioria no prazo, alguns atrasam
        if rng.random() < (0.65 - risco):
            dias_pg = int(rng.integers(-3, prazo))     # paga até o vencimento
        else:
            dias_pg = prazo + int(rng.integers(1, 75))  # paga com atraso
        data_pg = emissao + timedelta(days=max(1, dias_pg))
        if data_pg <= HOJE:
            pid += 1
            cur.execute("INSERT INTO pagamentos VALUES (?,?,?,?)",
                        (pid, fid, data_pg.isoformat(), valor))
con.commit()
cur.execute("SELECT COUNT(*) FROM faturas"); nf = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM pagamentos"); np_ = cur.fetchone()[0]
print(f"Banco criado: {DB}")
print(f"Clientes: {n_clientes} | Faturas: {nf} | Pagamentos: {np_}")
con.close()
