-- Grão do resultado: um mês de compra.
-- Pergunta: quanto vendemos por mês?
-- Pedido válido = status NOT IN ('canceled','unavailable'). Receita = sum(preco), sem frete.
-- O JOIN com itens muda o grão de pedido para item: pedidos se contam com count(DISTINCT).
-- 8 pedidos válidos sem nenhum item ficam fora (não venderam nada): 98.199, não 98.207.
SELECT date_trunc('month', p.data_compra)::DATE AS mes,
       count(DISTINCT p.pedido_id)              AS pedidos,
       sum(i.preco)                             AS receita
FROM refined.pedidos AS p
JOIN refined.itens_pedido AS i ON i.pedido_id = p.pedido_id
WHERE p.status NOT IN ('canceled', 'unavailable')
GROUP BY mes
ORDER BY mes
