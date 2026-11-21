-- Pergunta: quanto do dinheiro pago entra por cada forma de pagamento?
-- Grão do resultado: um tipo de pagamento. Grão da fonte: um pagamento (pedido_id, pagamento_seq).
-- valor soma 15.739.137,01, mais que a receita do mart 01 (13.494.400,74): o pagamento
-- inclui o FRETE e os juros de parcelamento; a receita é só sum(preco).
-- A soma de pedidos passa dos 98.206 válidos com pagamento: um pedido pago com cartão
-- e voucher conta nos dois tipos.
SELECT pg.tipo,
       count(*)                     AS pagamentos,
       count(DISTINCT pg.pedido_id) AS pedidos,
       sum(pg.valor)                AS valor,
       round(100.0 * sum(pg.valor) / sum(sum(pg.valor)) OVER (), 1) AS pct_valor
FROM refined.pagamentos AS pg
JOIN refined.pedidos AS p ON p.pedido_id = pg.pedido_id
WHERE p.status NOT IN ('canceled', 'unavailable')
GROUP BY pg.tipo
ORDER BY valor DESC
