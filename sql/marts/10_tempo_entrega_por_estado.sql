-- Grão do resultado: uma UF do cliente.
-- Pergunta: quantos dias da compra até a entrega, por UF do cliente?
-- Mesmo denominador do mart 03. Parte de data_compra (o tempo da loja),
-- não de data_envio (que seria o tempo da transportadora).
WITH dias_pedido AS (          -- grão: um pedido entregue
    SELECT c.uf, date_diff('day', p.data_compra, p.data_entrega) AS dias
    FROM refined.pedidos AS p
    JOIN refined.clientes AS c ON c.cliente_id = p.cliente_id
    WHERE p.status = 'delivered' AND p.data_entrega IS NOT NULL
)
SELECT uf,
       count(*)              AS entregues,
       round(avg(dias), 1)   AS dias_medio,
       median(dias)          AS dias_mediana
FROM dias_pedido
GROUP BY uf
ORDER BY dias_medio
