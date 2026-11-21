-- Grão do resultado: uma UF do cliente.
-- Pergunta: qual o ticket médio por estado?
-- Ticket médio = receita de cada pedido válido somada primeiro, média por pedido depois.
WITH receita_pedido AS (      -- grão: um pedido válido com item
    SELECT p.pedido_id, p.cliente_id, sum(i.preco) AS receita
    FROM refined.pedidos AS p
    JOIN refined.itens_pedido AS i ON i.pedido_id = p.pedido_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY p.pedido_id, p.cliente_id
)
SELECT c.uf,
       count(*)                AS pedidos,
       round(avg(r.receita), 2) AS ticket_medio
FROM receita_pedido AS r
JOIN refined.clientes AS c ON c.cliente_id = r.cliente_id   -- 1:1, não muda o grão
GROUP BY c.uf
ORDER BY ticket_medio DESC
