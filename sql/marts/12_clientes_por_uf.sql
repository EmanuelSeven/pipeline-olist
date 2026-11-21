-- Pergunta: quantas pessoas compram de cada UF?
-- Grão do resultado: uma UF do cliente.
-- Cliente = a pessoa (cliente_unico_id).
-- ATENÇÃO: a coluna clientes NÃO soma para o total — soma 96.136, não 96.096:
-- 39 pessoas têm pedidos em mais de uma UF (uma delas em três) e contam em cada UF.
SELECT uf, count(DISTINCT cliente_unico_id) AS clientes
FROM refined.clientes
GROUP BY uf
ORDER BY clientes DESC
