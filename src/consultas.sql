-- Consultas de análise de contas a receber (data de referência: 2026-06-23)
-- Autora: Ana Paula Galdino

-- 1) Aging de recebíveis: valor em aberto por faixa de atraso
SELECT
  CASE
    WHEN julianday('2026-06-23') - julianday(f.data_vencimento) < 0 THEN '0 · A vencer'
    WHEN julianday('2026-06-23') - julianday(f.data_vencimento) <= 30 THEN '1 · 1-30 dias'
    WHEN julianday('2026-06-23') - julianday(f.data_vencimento) <= 60 THEN '2 · 31-60 dias'
    WHEN julianday('2026-06-23') - julianday(f.data_vencimento) <= 90 THEN '3 · 61-90 dias'
    ELSE '4 · 90+ dias'
  END AS faixa,
  ROUND(SUM(f.valor), 2) AS valor_aberto
FROM faturas f
LEFT JOIN pagamentos p ON p.fatura_id = f.id
WHERE p.id IS NULL
GROUP BY faixa ORDER BY faixa;

-- 2) Inadimplência por segmento (% do valor já vencido que não foi pago)
SELECT c.segmento,
  ROUND(100.0 * SUM(CASE WHEN p.id IS NULL THEN f.valor ELSE 0 END)
        / SUM(f.valor), 1) AS pct_inadimplencia
FROM faturas f
JOIN clientes c ON c.id = f.cliente_id
LEFT JOIN pagamentos p ON p.fatura_id = f.id
WHERE f.data_vencimento < '2026-06-23'
GROUP BY c.segmento ORDER BY pct_inadimplencia DESC;

-- 3) Top 10 clientes por valor em aberto
SELECT c.nome, c.segmento, ROUND(SUM(f.valor), 2) AS em_aberto
FROM faturas f
JOIN clientes c ON c.id = f.cliente_id
LEFT JOIN pagamentos p ON p.fatura_id = f.id
WHERE p.id IS NULL
GROUP BY c.id ORDER BY em_aberto DESC LIMIT 10;

-- 4) Faturado por mês
SELECT strftime('%Y-%m', data_emissao) AS mes, ROUND(SUM(valor),2) AS faturado
FROM faturas GROUP BY mes ORDER BY mes;

-- 5) Recebido por mês
SELECT strftime('%Y-%m', p.data_pagamento) AS mes, ROUND(SUM(p.valor_pago),2) AS recebido
FROM pagamentos p GROUP BY mes ORDER BY mes;

-- 6) Prazo médio de recebimento (dias) por mês de pagamento
SELECT strftime('%Y-%m', p.data_pagamento) AS mes,
  ROUND(AVG(julianday(p.data_pagamento) - julianday(f.data_emissao)), 1) AS prazo_medio_dias
FROM pagamentos p JOIN faturas f ON f.id = p.fatura_id
GROUP BY mes ORDER BY mes;

-- 7) Recebimentos no prazo vs com atraso
SELECT CASE WHEN p.data_pagamento <= f.data_vencimento THEN 'No prazo' ELSE 'Com atraso' END AS status,
  COUNT(*) AS qtd, ROUND(SUM(p.valor_pago),2) AS valor
FROM pagamentos p JOIN faturas f ON f.id = p.fatura_id
GROUP BY status;
