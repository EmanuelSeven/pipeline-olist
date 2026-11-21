-- Pergunta: quantos clientes voltaram a comprar?
-- Grão do resultado: um número de pedidos por cliente (1, 2, 3...).
-- Cliente = a pessoa (cliente_unico_id), nunca cliente_id (que muda a cada pedido).
WITH pedidos_por_pessoa AS (  -- grão: uma pessoa com pedido válido
    SELECT c.cliente_unico_id, count(*) AS pedidos
    FROM refined.pedidos AS p
    JOIN refined.clientes AS c ON c.cliente_id = p.cliente_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY c.cliente_unico_id
)
SELECT pedidos AS pedidos_por_cliente,
       count(*) AS clientes,
       round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct_clientes
FROM pedidos_por_pessoa
GROUP BY pedidos
ORDER BY pedidos
