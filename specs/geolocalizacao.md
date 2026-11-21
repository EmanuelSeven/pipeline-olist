# SPEC — raw.geolocalizacao → refined.geolocalizacao (desafio 2)

Só a spec. Nada de código, nada gravado no banco. Todo número abaixo foi
contado no olist.duckdb (raw), não estimado.

## O que é uma linha

- Em raw: um ponto (lat/lng) observado para um prefixo de CEP, como veio.
  1.000.163 linhas, 19.015 CEPs distintos — mediana de 29 pontos por CEP,
  máximo de 1.146 num CEP só.
- Em refined: **um ponto distinto** (a linha inteira sem cópia exata).
- A tabela **não tem chave**: nem o CEP, nem (CEP, lat, lng) identificam uma
  linha de forma única por regra de negócio. A unidade é a linha inteira.

## 1. Escopo

Lê raw.geolocalizacao, escreve refined.geolocalizacao. Nunca escreve em raw.
Não agrega por CEP. Motivo: reduzir 52 pontos a um por CEP exige escolher
média, mediana ou primeiro ponto, uma cidade e uma UF — isso responde a
pergunta "onde fica este CEP?" e é trabalho de mart
(ex.: marts.geolocalizacao_por_cep), não de refined.

## 2. Nomes

| original | novo |
|---|---|
| geolocation_zip_code_prefix | cep_prefixo |
| geolocation_lat | lat |
| geolocation_lng | lng |
| geolocation_city | cidade |
| geolocation_state | uf |

Motivo: `cep_prefixo`, `cidade` e `uf` são os mesmos nomes de
refined.clientes e refined.vendedores.

## 3. Tipos

- cep_prefixo: VARCHAR. Motivo: 245.733 linhas têm CEP começando com '0';
  todos os 1.000.163 têm 5 caracteres. Identificador, nunca somado.
- lat, lng: DOUBLE. Motivo: coordenada é medida aproximada, não dinheiro;
  nenhuma conta exige centavo exato. 0 valores falham na conversão.
- cidade, uf: VARCHAR, como vieram (sem normalizar grafia — ver 6).

## 4. Conversão que falha

Para tudo (igual à etapa 2): conta, antes de gravar, os valores não nulos de
lat/lng que não convertem para DOUBLE. 1 ou mais → mostra a contagem e
sys.exit(1). Medido hoje: 0 em lat, 0 em lng.

## 5. Duplicatas

- Linha repetida inteira (mesmo CEP, lat, lng, cidade, uf): **sai**, fica uma
  cópia. São 261.831 cópias exatas (1.000.163 → 738.332). Motivo: a cópia não
  traz informação nenhuma; tirá-la não muda o significado de nenhuma linha.
- Mesmo CEP com pontos diferentes: **fica tudo**. Não é duplicata, é o grão
  da tabela.

## 6. Nulos e anomalias

- Nulos: 0 em todas as 5 colunas. Regra geral mantida: nulo continua nulo.
- Pontos fora do Brasil (caixa lat −33,75 a 5,27 e lng −73,99 a −34,79):
  42 linhas em raw, 33 depois de tirar as cópias. **Ficam**, anotados como
  anomalia. Motivo: filtrar é decisão de quem calcula distância (mart), e
  a caixa é uma aproximação.
- 8.556 CEPs têm mais de uma grafia de cidade; 8 CEPs têm mais de uma UF;
  8.011 grafias de cidade distintas. **Ficam como vieram.** Motivo: escolher
  a cidade "certa" de um CEP é agregação (mart); normalizar grafia
  é inventar dado.

## 7. Saída na tela

    ✓ refined.geolocalizacao   1.000.163 -> 738.332 linhas  (261.831 duplicatas)
        anomalias mantidas: 33 pontos fora do Brasil, 8 CEPs com 2 UFs

## Aviso para quem for usar (JOIN)

Ligar clientes à geolocalização direto pelo CEP **multiplica linhas**:
refined.clientes (99.441) ⋈ raw.geolocalizacao = 15.083.455 linhas, porque
cep_prefixo não é chave de nenhum dos lados. Qualquer soma depois desse JOIN
sai inflada. Para cruzar com cliente/vendedor, use antes um mart com um ponto
por CEP.

Cobertura: 157 CEPs de cliente (278 clientes) e 7 CEPs de vendedor
(7 vendedores) não existem na geolocalização — um JOIN comum os perde.

## Reexecução e erro

CREATE OR REPLACE, nunca acrescenta. Faltando raw.geolocalizacao: manda rodar
a ingestão e sys.exit(1).

## Critérios de aceite

- 1.000.163 entram, 738.332 saem, 261.831 cópias removidas.
- 19.015 CEPs distintos antes e depois (a deduplicação não apaga CEP).
- 0 falhas de conversão em lat e lng; DESCRIBE mostra DOUBLE em lat/lng e
  VARCHAR em cep_prefixo.
- Todo cep_prefixo com 5 caracteres; os que começam com '0' continuam com '0'.
- Rodar duas vezes imprime exatamente a mesma coisa.
