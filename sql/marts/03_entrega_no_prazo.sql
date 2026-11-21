-- Pergunta: quanto chegou no prazo?
-- Grão do resultado: a operação inteira, uma linha.
-- Denominador: pedidos delivered COM data de entrega (os 8 sem data ficam fora).
-- data_entrega é TIMESTAMP e data_entrega_prevista é DATE: o ::DATE é obrigatório,
-- senão a entrega às 15h do dia previsto vira atraso (93,2% cairia para 91,9%).
-- Chegar no dia previsto = no prazo.
SELECT count(*) AS entregues,
       sum(CASE WHEN p.data_entrega::DATE <= p.data_entrega_prevista THEN 1 ELSE 0 END) AS no_prazo,
       sum(CASE WHEN p.data_entrega::DATE >  p.data_entrega_prevista THEN 1 ELSE 0 END) AS atrasados,
       round(100.0 * sum(CASE WHEN p.data_entrega::DATE <= p.data_entrega_prevista THEN 1 ELSE 0 END)
             / count(*), 1) AS pct_no_prazo
FROM refined.pedidos AS p
WHERE p.status = 'delivered'
  AND p.data_entrega IS NOT NULL
