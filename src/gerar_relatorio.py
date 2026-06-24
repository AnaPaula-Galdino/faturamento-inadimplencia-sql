import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relatorio_exec import construir
import analise_faturamento as A

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "imagens")
def img(n): return os.path.join(IMG, n)
r = A.resumo()
def brl(v): return f"R$ {v/1e6:.1f} mi" if v>=1e6 else f"R$ {v/1000:.0f} mil"

config = {
 "eyebrow": "RELATÓRIO DE CONTAS A RECEBER",
 "titulo": "Faturamento e Inadimplência",
 "subtitulo": "Análise de recebíveis a partir de uma base SQL — contas a receber, aging e DSO",
 "meta": "Ana Paula Galdino · Supervisão de Faturamento · Data Analytics (POSTECH/FIAP) · Junho de 2026",
 "fonte": "Base de contas a receber (SQLite)  ·  Análise: Ana Paula Galdino",
 "sumario": [
   f"A carteira de recebíveis soma <b>{brl(r['total_aberto'])}</b> em aberto, dos quais "
   f"<b>{brl(r['vencido'])}</b> já estão vencidos. O prazo médio de recebimento (DSO) está em "
   f"<b>{r['dso']:.0f} dias</b> e a inadimplência geral é de <b>{r['inad_geral']:.1f}%</b> do valor vencido.",
   f"O risco não está distribuído por igual: o segmento <b>{r['seg_pior']}</b> concentra a maior "
   f"inadimplência ({r['seg_pior_pct']:.1f}%). E apenas <b>{r['pct_no_prazo']:.0f}%</b> do que foi recebido "
   "entrou dentro do prazo, o que pressiona o capital de giro.",
 ],
 "kpis": [
   (brl(r['total_aberto']), "em aberto"),
   (brl(r['vencido']), "vencido"),
   (f"{r['dso']:.0f} dias", "prazo médio (DSO)"),
   (f"{r['inad_geral']:.1f}%", "inadimplência"),
 ],
 "secoes": [
   {"titulo": "1. Onde está o dinheiro parado",
    "texto": [
      "O aging mostra a saúde da carteira por faixa de atraso. O ponto de atenção é a faixa de "
      "<b>90+ dias</b>, onde o recebimento se torna improvável e costuma virar perda — é nela que a "
      "cobrança deve concentrar esforço imediato.",
      f"Por segmento, <b>{r['seg_pior']}</b> é o que mais pesa na inadimplência. Tratar esse grupo com "
      "política de crédito mais rígida e cobrança ativa tem o maior retorno.",
    ],
    "imagens": [(img("01_aging_recebiveis.png"), "Valor em aberto por faixa de atraso"),
                (img("02_inadimplencia_segmento.png"), "Inadimplência concentrada por segmento")]},
   {"titulo": "2. Ritmo de caixa",
    "texto": [
      "Comparar faturado e recebido mês a mês revela o descasamento entre venda e entrada de caixa. "
      "Quando o recebido fica sistematicamente abaixo do faturado, o capital de giro sofre.",
      f"O DSO em torno de <b>{r['dso']:.0f} dias</b> é o termômetro: reduzi-lo libera caixa sem precisar "
      "vender mais. Cada dia a menos de DSO antecipa recebimento.",
    ],
    "imagens": [(img("03_faturado_vs_recebido.png"), "Faturado frente ao efetivamente recebido"),
                (img("04_dso_mensal.png"), "Evolução do prazo médio de recebimento")]},
   {"titulo": "3. Quem e como recebe",
    "texto": [
      "A concentração da dívida em poucos clientes orienta a régua de cobrança: priorizar os maiores "
      "saldos em aberto traz o maior impacto financeiro com o menor esforço operacional.",
      f"Como só <b>{r['pct_no_prazo']:.0f}%</b> do valor entra no prazo, há espaço claro para melhorar "
      "a pontualidade — via lembretes, condições e incentivos a pagamento antecipado.",
    ],
    "imagens": [(img("05_top_devedores.png"), "Top 10 clientes por valor em aberto"),
                (img("06_prazo_vs_atraso.png"), "Parcela recebida no prazo vs. com atraso")]},
 ],
 "conclusao_titulo": "Recomendações",
 "conclusoes": [
   "<b>Foco no 90+:</b> ação de cobrança imediata e negociação na faixa mais crítica, antes que vire perda.",
   f"<b>Política por segmento:</b> crédito e cobrança mais firmes para <b>{r['seg_pior']}</b>, que puxa a inadimplência.",
   "<b>Atacar o DSO:</b> metas de redução do prazo médio liberam capital de giro sem aumentar vendas.",
   "<b>Régua de recebíveis:</b> priorizar os maiores saldos e incentivar pagamento dentro do prazo.",
 ],
}

if __name__ == "__main__":
    construir(config, os.path.join(BASE, "Analise_Executiva_Faturamento.pdf"))
