-- Grão do resultado: a operação inteira, uma linha.
-- Pergunta: os números dos cartões do painel.
-- Cada CTE tem UMA linha; o SELECT final junta com vírgula (sem ON): 1 x 1 x 1 = 1.
-- Se alguma CTE voltar com duas linhas, o mart dobra calado — cada uma agrega tudo.
WITH receita_pedido AS (      -- grão: um pedido válido com item
    SELECT p.pedido_id, sum(i.preco) AS receita
    FROM refined.pedidos AS p
    JOIN refined.itens_pedido AS i ON i.pedido_id = p.pedido_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY p.pedido_id
),
ticket AS (                   -- grão: uma linha
    SELECT round(avg(receita), 2) AS ticket_medio,
           round(median(receita), 2) AS ticket_mediana
    FROM receita_pedido
),
frete AS (                    -- grão: uma linha. Frete sobre o que o cliente pagou em item: preco + frete
    SELECT round(100.0 * sum(i.frete) / (sum(i.preco) + sum(i.frete)), 1) AS pct_frete
    FROM refined.itens_pedido AS i
    JOIN refined.pedidos AS p ON p.pedido_id = i.pedido_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
),
cancelados AS (               -- grão: uma linha. canceled sobre TODOS os pedidos
    SELECT round(100.0 * count(*) FILTER (WHERE status = 'canceled') / count(*), 2) AS pct_cancelados
    FROM refined.pedidos
),
entrega AS (                  -- grão: uma linha. Mesmo denominador do mart 03
    SELECT round(avg(date_diff('day', data_compra, data_entrega)), 1) AS dias_entrega,
           median(date_diff('day', data_compra, data_entrega))       AS dias_entrega_mediana
    FROM refined.pedidos
    WHERE status = 'delivered' AND data_entrega IS NOT NULL
),
nota AS (                     -- grão: uma linha. Média em todas as avaliações
    SELECT round(avg(nota), 2) AS nota_media
    FROM refined.avaliacoes
)
SELECT ticket.ticket_medio, ticket.ticket_mediana, frete.pct_frete,
       cancelados.pct_cancelados, entrega.dias_entrega, entrega.dias_entrega_mediana,
       nota.nota_media
FROM ticket, frete, cancelados, entrega, nota
