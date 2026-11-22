# Processamento Assíncrono de Boletos com Filas de Mensagens

Trabalho prático de Sistemas Operacionais Modernos (CEFET-MG), Prática 4: Sistemas Distribuídos Assíncronos e Filas de Mensagens.

O sistema simula uma loja que recebe um pico de pedidos e gera os boletos de forma assíncrona, usando o padrão produtor-consumidor:

- a **API** recebe os pedidos, salva no banco e coloca uma mensagem na fila;
- o **RabbitMQ** guarda as mensagens (o *buffer*);
- os **workers** retiram uma mensagem por vez, simulam o processamento (1 s) e salvam o boleto no **PostgreSQL**.

Tudo roda em containers orquestrados pelo Docker Compose.

## Estrutura do repositório

```
.
├── docker-compose.yml   # os 6 serviços, a rede interna e os volumes
├── .env.exemplo         # modelo das variáveis de ambiente (senhas, filas, tempos)
├── banco/
│   ├── init.sql         # cria as tabelas pedidos e boletos na primeira subida
│   └── consultas.sql    # consultas usadas para conferir os testes
├── api/                 # produtor (FastAPI) e painel administrativo (admin.html)
├── worker-boletos/      # consumidor da fila.boletos: gera os boletos
├── worker-envios/       # consumidor da fila.envios: agenda o envio dos pedidos pagos
└── agendador/           # cancela, a cada 30 s, os pedidos com boleto vencido
```

Cada serviço tem seu próprio `Dockerfile`, `main.py` e `requirements.txt`. Os workers e o agendador também têm uma pasta `tests/`.

| Serviço | Porta no navegador | Função |
|---|---|---|
| `api` | 8000 | produtor e painel administrativo |
| `rabbitmq` | 15672 | fila de mensagens e painel de gerenciamento |
| `postgres` | não exposta | banco de dados |
| `worker-boletos` | não exposta | consumidor principal (pode ter várias réplicas) |
| `worker-envios` | não exposta | consumidor de envios |
| `agendador` | não exposta | tarefa periódica |

## Como executar

Pré-requisito: Docker com o Docker Compose.

```bash
cp .env.exemplo .env          # depois, troque as senhas no .env
docker compose up -d --build  # sobe os 6 serviços
```

- Painel da aplicação: http://localhost:8000/admin
- Painel do RabbitMQ: http://localhost:15672 (usuário e senha definidos no `.env`)

## Demonstração

1. No painel da aplicação, clique em **Simular pico de pedidos**: 5.000 pedidos entram na fila.
2. No painel do RabbitMQ, aba *Queues*, acompanhe a `fila.boletos` esvaziando a cerca de 1 mensagem por segundo.
3. Suba mais três consumidores e veja a fila esvaziar cerca de 4 vezes mais rápido:

```bash
docker compose up -d --scale worker-boletos=4
```

Para encerrar, use `docker compose down`. Para encerrar e apagar os dados dos volumes, use `docker compose down -v`.

## Testes

Os testes de cada serviço não precisam do Docker nem de dependências instaladas:

```bash
python3 -m unittest discover -s worker-boletos/tests
python3 -m unittest discover -s worker-envios/tests
python3 -m unittest discover -s agendador/tests
```

No Windows (fora do WSL), troque `python3` por `python` ou `py`.
