-- Grão do resultado: uma camada do pipeline (raw, refined, marts).
-- Pergunta: quantas tabelas e quantos registros tem cada camada?
-- Soma o mart 13; a página "Como foi feito" lê daqui, sem fazer conta na tela.
SELECT ordem, camada, count(*) AS tabelas, sum(linhas) AS registros
FROM marts.tabelas_por_camada
GROUP BY ordem, camada
ORDER BY ordem
