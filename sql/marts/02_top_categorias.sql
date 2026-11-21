-- Grão do resultado: uma categoria.
-- Pergunta: quais categorias mais vendem?
-- Grão do JOIN: um item. LEFT JOIN na tradução e no produto sem categoria:
-- sem eles, R$ 183.813,13 somem sem aviso.
-- ATENÇÃO: a coluna pedidos NÃO soma — um pedido com itens de duas categorias
-- conta nas duas (soma 99.002 > 98.199). Não use para totais.
-- categoria_pt é só o rótulo de tela (mart 00); categoria continua em inglês.
SELECT coalesce(t.categoria_ingles, pr.categoria, 'sem_categoria') AS categoria,
       coalesce(pt.categoria_pt, 'Sem categoria')                  AS categoria_pt,
       count(DISTINCT p.pedido_id) AS pedidos,
       count(*)                    AS itens,
       sum(i.preco)                AS receita
FROM refined.itens_pedido AS i
JOIN refined.pedidos  AS p  ON p.pedido_id = i.pedido_id
JOIN refined.produtos AS pr ON pr.produto_id = i.produto_id
LEFT JOIN refined.traducao_categorias AS t ON t.categoria = pr.categoria
LEFT JOIN marts.categorias_pt AS pt ON pt.categoria = pr.categoria
WHERE p.status NOT IN ('canceled', 'unavailable')
GROUP BY 1, 2
ORDER BY receita DESC
