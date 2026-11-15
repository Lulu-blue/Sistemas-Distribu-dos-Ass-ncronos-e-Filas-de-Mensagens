# Validação real do Worker de Boletos

Data: 15/11/2026, horário de Brasília. Testes executados com Docker Compose no projeto local.

## Escalabilidade

Havia pedidos pendentes de uma carga anterior; não foi necessário gerar outro pico de 5.000 pedidos. As medições usaram o aumento do total de boletos confirmados no banco, com fila não vazia e atraso configurado em um segundo.

| Réplicas | Total inicial | Total final | Intervalo | Taxa |
|---|---:|---:|---:|---:|
| 1 | 4767 | 4787 | 20,002 s | 1,00 boleto/s |
| 4 | 4844 | 4924 | 20,002 s | 4,00 boletos/s |

Aceleração observada: aproximadamente 4 vezes. É uma medição curta nesta máquina, não uma garantia para qualquer carga ou ambiente. O comando rabbitmqctl list_consumers confirmou quatro consumidores com ack_required=true e prefetch_count=1.

## Recuperação

Inicialmente, o container RabbitMQ aparecia healthy, mas o broker recusava conexões AMQP e list_queues retornava erro de metadados do vhost. Um reinício do RabbitMQ restaurou o serviço; os workers reconectaram sem reinício manual. A causa original desse estado não foi determinada; o healthcheck atual verifica portas e não garante consumo funcional.

Para testes controlados, foram criados 80 pedidos fictícios pela API, IDs 5002 a 5081, com cliente “Teste recuperacao Codex 2026-11-15”. Esses registros foram mantidos no banco.

- RabbitMQ reiniciado durante consumo: interrupção registrada às 11:01:13; reconexão e consumo às 11:01:19; processamento retomado às 11:01:20.
- PostgreSQL reiniciado durante consumo: falha registrada às 11:01:33, com devolução de mensagens à fila; reconexão e consumo às 11:01:36; boletos voltaram a ser gravados às 11:01:37.
- Exemplo: pedido 5066 falhou no worker 1 durante a queda do banco e foi concluído pelo worker 4 às 11:01:37.
- Os logs também registraram reentrega do pedido 4646 reconhecida como boleto já existente, sem nova inserção.

## Consultas finais

| Verificação | Resultado |
|---|---:|
| Total de pedidos | 5081 |
| Total de boletos | 5081 |
| IDs de pedido com mais de um boleto | 0 |
| Pedidos AGUARDANDO_PAGAMENTO sem boleto | 0 |
| Pedidos CRIADO sem boleto | 0 |
| Pedidos de teste com boleto (5002 a 5081) | 80 |
| Mensagens Ready em fila.boletos | 0 |
| Mensagens Unacked em fila.boletos | 0 |
| Consumidores ativos | 4 |

Estado final: API e quatro workers rodando; PostgreSQL e RabbitMQ healthy. Nenhum volume foi removido e nenhum registro existente foi excluído. Não houve alteração no código durante estes testes.

## Evidências

O arquivo evidencias-validacao-2026-11-15.txt reúne trechos filtrados dos logs dos workers: reconexões, reentregas e processamento dos pedidos de teste. Linhas foram filtradas para reduzir ruído; não são o log completo nem uma captura de tela.

Conclusão: passaram os testes locais de escala 1→4, recuperação após reinício de RabbitMQ/PostgreSQL e verificações finais de consistência. Não foi executado teste de queda do host, remoção de volumes ou interrupção abrupta de um worker exatamente entre commit e ACK.

