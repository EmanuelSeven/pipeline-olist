# Desafio 1 — O que esse dado é capaz de responder

1. Tempo médio de entrega (em dias) — pedidos (order_purchase_timestamp, order_delivered_customer_date) — mede quanto tempo o cliente espera pelo pedido
2. % de pedidos entregues no prazo — pedidos (order_delivered_customer_date, order_estimated_delivery_date) — mede se a loja cumpre o que promete
3. Pedidos entregues por mês — pedidos (order_status, order_delivered_customer_date) — mede o volume que a operação consegue entregar
4. Tempo médio de entrega por estado — pedidos (order_purchase_timestamp, order_delivered_customer_date) + clientes (customer_state) — mostra quais estados demoram mais e ajuda a planejar veículos e rotas
5. Frete médio por estado — itens_pedido (freight_value) + pedidos (order_id, customer_id) + clientes (customer_state) — mostra onde o frete pesa mais e pode estar atrapalhando as vendas
6. Pedidos com atraso grave ou nota ruim — pedidos (order_delivered_customer_date, order_estimated_delivery_date) + avaliacoes (order_id, review_score) — conta pedidos com mais de 7 dias de atraso OU nota 1 ou 2; aponta onde a operação está falhando
7. Nota média: no prazo × atrasado — pedidos (order_delivered_customer_date, order_estimated_delivery_date) + avaliacoes (review_score) — mostra quanto o atraso derruba a satisfação do cliente
8. Ranking das formas de pagamento — pagamentos (payment_type, payment_value) — mostra quais formas os clientes preferem, em quantidade e em valor
9. Itens vendidos e receita por categoria — itens_pedido (product_id, price) + produtos (product_category_name) — mostra quais categorias mais vendem, em quantidade e em dinheiro
10. Vendas por estado do vendedor — itens_pedido (seller_id, price) + vendedores (seller_state) — mostra de onde sai a maior parte das vendas

## Não dá

- ✗ Custo da entrega (combustível, pedágio, hotel) — não existe coluna de custo da transportadora, só o frete cobrado do cliente
