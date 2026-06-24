"""
Análise de Contas a Receber e Inadimplência — SQL + Python
Lê o banco SQLite, roda as consultas e gera 6 visualizações executivas.
Autora: Ana Paula Galdino
"""
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get("FATDB", os.path.join(BASE, "dados", "faturamento.db"))
IMG = os.path.join(BASE, "imagens"); os.makedirs(IMG, exist_ok=True)
REF = "2026-06-23"
C = {"escuro": "#1f4e79", "medio": "#2e6da4", "claro": "#5b9bd5",
     "suave": "#a6c8e0", "destaque": "#4fc3f7", "cinza": "#d9d9d9", "alerta": "#c0392b"}
FONTE = "Fonte: base de contas a receber (SQLite)  ·  Análise: Ana Paula Galdino"
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans", "axes.edgecolor": "#9aa7b8",
    "axes.grid": True, "grid.color": "#eef2f7", "axes.axisbelow": True, "figure.dpi": 120,
    "savefig.bbox": "tight"})
def rodape(fig): fig.text(0.01, 0.005, FONTE, fontsize=7.5, color="#7a8aa0")
def brl(x): return f"R$ {x/1000:.0f}k" if x < 1e6 else f"R$ {x/1e6:.1f}M"

con = sqlite3.connect(DB)
def q(sql, params=()): return pd.read_sql_query(sql, con, params=params)

# 1) Aging
aging = q(f"""SELECT CASE
  WHEN julianday('{REF}')-julianday(f.data_vencimento)<0 THEN 'A vencer'
  WHEN julianday('{REF}')-julianday(f.data_vencimento)<=30 THEN '1-30'
  WHEN julianday('{REF}')-julianday(f.data_vencimento)<=60 THEN '31-60'
  WHEN julianday('{REF}')-julianday(f.data_vencimento)<=90 THEN '61-90'
  ELSE '90+' END AS faixa, SUM(f.valor) AS valor
  FROM faturas f LEFT JOIN pagamentos p ON p.fatura_id=f.id
  WHERE p.id IS NULL GROUP BY faixa""")
ordem = ["A vencer","1-30","31-60","61-90","90+"]
aging = aging.set_index("faixa").reindex(ordem).fillna(0).reset_index()
def g1():
    cores=[C["claro"]]+[C["medio"],C["medio"],C["escuro"],C["alerta"]]
    fig,ax=plt.subplots(figsize=(9,5))
    ax.bar(aging["faixa"], aging["valor"], color=cores)
    for i,v in enumerate(aging["valor"]): ax.text(i,v,f" {brl(v)}",ha="center",va="bottom",fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:brl(x)))
    venc=aging[aging.faixa!="A vencer"]["valor"].sum()
    ax.set_title(f"Aging de recebíveis — R$ {venc/1e6:.1f}M vencidos em aberto",
                 fontweight="bold",color=C["escuro"],fontsize=13,pad=10)
    ax.set_xlabel("Faixa de atraso (dias)"); ax.set_ylabel("Valor em aberto")
    rodape(fig); fig.savefig(os.path.join(IMG,"01_aging_recebiveis.png")); plt.close(fig)

# 2) Inadimplência por segmento
inad = q(f"""SELECT c.segmento,
  100.0*SUM(CASE WHEN p.id IS NULL THEN f.valor ELSE 0 END)/SUM(f.valor) AS pct
  FROM faturas f JOIN clientes c ON c.id=f.cliente_id
  LEFT JOIN pagamentos p ON p.fatura_id=f.id
  WHERE f.data_vencimento<'{REF}' GROUP BY c.segmento ORDER BY pct DESC""")
def g2():
    fig,ax=plt.subplots(figsize=(8,5))
    ax.bar(inad["segmento"], inad["pct"], color=C["escuro"])
    for i,v in enumerate(inad["pct"]): ax.text(i,v,f"{v:.1f}%",ha="center",va="bottom",fontsize=10)
    ax.set_title("Taxa de inadimplência por segmento",fontweight="bold",color=C["escuro"],fontsize=13,pad=10)
    ax.set_ylabel("% do valor vencido não pago"); ax.set_ylim(0, inad["pct"].max()*1.2)
    rodape(fig); fig.savefig(os.path.join(IMG,"02_inadimplencia_segmento.png")); plt.close(fig)

# 3) Faturado vs Recebido por mês
fat=q("SELECT strftime('%Y-%m',data_emissao) AS mes, SUM(valor) AS faturado FROM faturas GROUP BY mes")
rec=q("SELECT strftime('%Y-%m',data_pagamento) AS mes, SUM(valor_pago) AS recebido FROM pagamentos GROUP BY mes")
m=pd.merge(fat,rec,on="mes",how="outer").fillna(0).sort_values("mes")
m=m[m["mes"]>="2024-07"]
def g3():
    fig,ax=plt.subplots(figsize=(11,5)); x=range(len(m))
    ax.bar([i-0.2 for i in x], m["faturado"], 0.4, label="Faturado", color=C["escuro"])
    ax.bar([i+0.2 for i in x], m["recebido"], 0.4, label="Recebido", color=C["destaque"])
    ax.set_xticks(list(x)); ax.set_xticklabels(m["mes"], rotation=90, fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:brl(v)))
    ax.set_title("Faturado vs. Recebido por mês",fontweight="bold",color=C["escuro"],fontsize=13,pad=10)
    ax.set_ylabel("Valor"); ax.legend(frameon=True)
    rodape(fig); fig.savefig(os.path.join(IMG,"03_faturado_vs_recebido.png")); plt.close(fig)

# 4) Prazo médio de recebimento (DSO) por mês
dso=q("""SELECT strftime('%Y-%m',p.data_pagamento) AS mes,
  AVG(julianday(p.data_pagamento)-julianday(f.data_emissao)) AS prazo
  FROM pagamentos p JOIN faturas f ON f.id=p.fatura_id GROUP BY mes ORDER BY mes""")
dso=dso[dso["mes"]>="2024-07"]
def g4():
    fig,ax=plt.subplots(figsize=(11,4.8)); xi=range(len(dso))
    ax.plot(list(xi), dso["prazo"], color=C["escuro"], marker="o", ms=4, lw=2)
    ax.fill_between(list(xi), dso["prazo"], color=C["claro"], alpha=0.3)
    media=dso["prazo"].mean()
    ax.axhline(media, color=C["alerta"], ls="--", lw=1.2, label=f"média: {media:.0f} dias")
    ax.set_xticks(list(xi)); ax.set_xticklabels(dso["mes"], rotation=90, fontsize=8)
    ax.set_title("Prazo médio de recebimento (DSO) por mês",fontweight="bold",color=C["escuro"],fontsize=13,pad=10)
    ax.set_ylabel("Dias"); ax.legend(frameon=True)
    rodape(fig); fig.savefig(os.path.join(IMG,"04_dso_mensal.png")); plt.close(fig)

# 5) Top 10 devedores
top=q("""SELECT c.nome, SUM(f.valor) AS aberto FROM faturas f
  JOIN clientes c ON c.id=f.cliente_id LEFT JOIN pagamentos p ON p.fatura_id=f.id
  WHERE p.id IS NULL GROUP BY c.id ORDER BY aberto DESC LIMIT 10""").sort_values("aberto")
def g5():
    fig,ax=plt.subplots(figsize=(9,5.4))
    ax.barh(top["nome"], top["aberto"], color=C["medio"])
    for i,v in enumerate(top["aberto"]): ax.text(v,i,f" {brl(v)}",va="center",fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:brl(x)))
    ax.set_title("Top 10 clientes por valor em aberto",fontweight="bold",color=C["escuro"],fontsize=13,pad=10)
    ax.set_xlabel("Valor em aberto")
    rodape(fig); fig.savefig(os.path.join(IMG,"05_top_devedores.png")); plt.close(fig)

# 6) Recebido no prazo vs atraso
pz=q("""SELECT CASE WHEN p.data_pagamento<=f.data_vencimento THEN 'No prazo' ELSE 'Com atraso' END AS status,
  SUM(p.valor_pago) AS valor FROM pagamentos p JOIN faturas f ON f.id=p.fatura_id GROUP BY status""")
def g6():
    fig,ax=plt.subplots(figsize=(7.5,5.4))
    cores=[C["destaque"] if s=="No prazo" else C["alerta"] for s in pz["status"]]
    w,_,at=ax.pie(pz["valor"], labels=pz["status"], autopct=lambda p:f"{p:.0f}%",
                  colors=cores, startangle=90, wedgeprops=dict(width=0.42,edgecolor="white",linewidth=2))
    for t in at: t.set_color("white"); t.set_fontweight("bold")
    ax.set_title("Recebimentos: no prazo vs. com atraso",fontweight="bold",color=C["escuro"],fontsize=13)
    rodape(fig); fig.savefig(os.path.join(IMG,"06_prazo_vs_atraso.png")); plt.close(fig)

def resumo():
    venc=aging[aging.faixa!="A vencer"]["valor"].sum()
    total_aberto=aging["valor"].sum()
    inad_geral=q(f"""SELECT 100.0*SUM(CASE WHEN p.id IS NULL THEN f.valor ELSE 0 END)/SUM(f.valor) AS pct
      FROM faturas f LEFT JOIN pagamentos p ON p.fatura_id=f.id WHERE f.data_vencimento<'{REF}'""")["pct"][0]
    no_prazo=pz.set_index("status")["valor"]
    pct_prazo=no_prazo.get("No prazo",0)/no_prazo.sum()*100
    return {"total_aberto":total_aberto,"vencido":venc,"dso":dso["prazo"].mean(),
            "inad_geral":inad_geral,"pct_no_prazo":pct_prazo,
            "seg_pior":inad.iloc[0]["segmento"],"seg_pior_pct":inad.iloc[0]["pct"]}

def main():
    for g in (g1,g2,g3,g4,g5,g6): g()
    r=resumo()
    print({k:(round(v,1) if isinstance(v,float) else v) for k,v in r.items()})
    print("Gráficos:", sorted(x for x in os.listdir(IMG) if x.startswith("0")))
    return r

if __name__=="__main__":
    main(); con.close()
