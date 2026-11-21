-- Pergunta: o atraso derruba a nota?
-- Grão do resultado: uma situação de entrega ('no_prazo' ou 'atrasado').
-- Mesmo denominador do mart 03 (delivered com data de entrega), com o ::DATE.
WITH nota_pedido AS (          -- grão: um pedido (média das avaliações dele)
    SELECT pedido_id, avg(nota) AS nota
    FROM refined.avaliacoes
    GROUP BY pedido_id
),
situacao_pedido AS (           -- grão: um pedido entregue
    SELECT pedido_id,
           CASE WHEN data_entrega::DATE <= data_entrega_prevista THEN 'no_prazo'
                ELSE 'atrasado' END AS situacao
    FROM refined.pedidos
    WHERE status = 'delivered' AND data_entrega IS NOT NULL
)
SELECT s.situacao,
       count(*)                AS pedidos_avaliados,
       round(avg(n.nota), 2)   AS nota_media,
       round(100.0 * count(*) FILTER (WHERE n.nota <= 2) / count(*), 1) AS pct_nota_baixa
FROM situacao_pedido AS s
JOIN nota_pedido AS n ON n.pedido_id = s.pedido_id
GROUP BY s.situacao
ORDER BY s.situacao DESC
