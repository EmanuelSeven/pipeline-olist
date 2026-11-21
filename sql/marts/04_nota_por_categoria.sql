-- Grão do resultado: uma categoria com 100 pedidos avaliados ou mais.
-- Pergunta: que nota cada categoria recebe?
-- A nota é do pedido e a categoria é do item: o grão é ajustado ANTES de juntar.
WITH nota_pedido AS (        -- grão: um pedido (média das avaliações do pedido; 547 têm mais de uma)
    SELECT pedido_id, avg(nota) AS nota
    FROM refined.avaliacoes
    GROUP BY pedido_id
),
categoria_pedido AS (        -- grão: um par (pedido, categoria)
    SELECT DISTINCT i.pedido_id,
           coalesce(t.categoria_ingles, pr.categoria, 'sem_categoria') AS categoria,
           coalesce(pt.categoria_pt, 'Sem categoria')                  AS categoria_pt
    FROM refined.itens_pedido AS i
    JOIN refined.produtos AS pr ON pr.produto_id = i.produto_id
    LEFT JOIN refined.traducao_categorias AS t ON t.categoria = pr.categoria
    LEFT JOIN marts.categorias_pt AS pt ON pt.categoria = pr.categoria
),
por_categoria AS (           -- grão: uma categoria
    SELECT c.categoria, c.categoria_pt,
           count(*)               AS pedidos_avaliados,
           round(avg(n.nota), 2)  AS nota_media
    FROM categoria_pedido AS c
    JOIN nota_pedido AS n ON n.pedido_id = c.pedido_id
    GROUP BY c.categoria, c.categoria_pt
    HAVING count(*) >= 100
)
SELECT rank() OVER (ORDER BY nota_media) AS posicao,
       categoria, categoria_pt, pedidos_avaliados, nota_media
FROM por_categoria
ORDER BY posicao, categoria
