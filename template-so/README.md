# Documentação de Requisitos — Delivery Assíncrono (ISO/IEC/IEEE 29148:2018)

Esta pasta é a versão **preenchida** dos templates da pasta [`../template/`](../template/), aplicada ao nosso projeto (Prática 4: sistema de delivery com fila de mensagens).

## Arquivos

| Arquivo | O que é |
|---------|---------|
| [`SRS_DELIVERY_FILAS_v1.0.md`](SRS_DELIVERY_FILAS_v1.0.md) | Especificação de Requisitos do sistema inteiro: arquitetura, portas, variáveis, tabelas, estados e plano de verificação |
| [`requisitos/`](requisitos/) | Uma ficha por requisito, com análise de conformidade com a norma e casos de teste |

## Fichas de requisito (Pessoas 1 e 2)

| ID | Nome | Responsável | Situação |
|----|------|-------------|----------|
| [REQ-INFRA-001](requisitos/REQ-INFRA-001.md) | Subida do ambiente com um único comando | Pessoa 1 | Verificado |
| [REQ-INFRA-002](requisitos/REQ-INFRA-002.md) | Isolamento de rede e exposição mínima de portas | Pessoa 1 | Verificado |
| [REQ-INFRA-003](requisitos/REQ-INFRA-003.md) | Ordem de inicialização por verificação de saúde | Pessoa 1 | Verificado |
| [REQ-INFRA-004](requisitos/REQ-INFRA-004.md) | Escalabilidade horizontal do worker de boletos | Pessoa 1 | Verificado |
| [REQ-INFRA-005](requisitos/REQ-INFRA-005.md) | Reinício automático dos serviços | Pessoa 1 | Verificado |
| [REQ-CONF-001](requisitos/REQ-CONF-001.md) | Configuração externa e segredos fora do repositório | Pessoa 2 | Verificado |
| [REQ-BD-001](requisitos/REQ-BD-001.md) | Criação automática do esquema do banco | Pessoa 2 | Verificado |
| [REQ-BD-002](requisitos/REQ-BD-002.md) | Restrição dos estados do pedido | Pessoa 2 | Verificado |
| [REQ-BD-003](requisitos/REQ-BD-003.md) | Um boleto por pedido | Pessoa 2 | Verificado |
| [REQ-BD-004](requisitos/REQ-BD-004.md) | Persistência dos dados entre reinícios | Pessoa 2 | Verificado |
| [REQ-BD-005](requisitos/REQ-BD-005.md) | Consultas de acompanhamento do processamento | Pessoa 2 | Verificado |

Os requisitos das outras pessoas (`REQ-FUNC-*`, `REQ-PERF-*`, `REQ-USA-*`) estão resumidos nas seções 3.2 a 3.4 do SRS. Para criar a ficha de um deles, copie [`../template/TEMPLATE_REQUISITO.md`](../template/TEMPLATE_REQUISITO.md) para `requisitos/REQ-FUNC-NNN.md`, preencha, e adicione uma linha na tabela acima.

## Integração (Pessoas 3 a 6)

- **Variáveis de ambiente:** tabela na seção 3.1 do SRS. Leia com `os.environ["NOME"]`.
- **Colunas do banco:** tabelas na seção 3.5 do SRS (e em [`../banco/init.sql`](../banco/init.sql)).
- **Status:** só os 6 valores em MAIÚSCULAS. Qualquer outro valor dá erro no banco.
- **Pessoa 4:** `boletos.pedido_id` é único. Use `INSERT ... ON CONFLICT (pedido_id) DO NOTHING` e dê `ack` mesmo assim. Preencha `gerado_por` com `socket.gethostname()`.
- **Pessoa 3:** declare as filas como `durable=True` e publique com `delivery_mode=2`, senão as mensagens se perdem num `docker compose stop`.
- **Pessoa 5:** o worker-envios grava a previsão em `pedidos.previsao_envio`.
- Os Dockerfiles em `api/`, `worker-boletos/`, `worker-envios/` e `agendador/` são **provisórios**: podem ser substituídos à vontade, mantendo o nome da pasta.

## Teste

```bash
cp .env.exemplo .env
docker compose up -d
docker compose ps
docker compose up -d --scale worker-boletos=4
docker compose ps worker-boletos
docker compose exec postgres psql -U delivery -d delivery -c '\dt'
docker compose exec -T postgres psql -U delivery -d delivery < banco/consultas.sql
```
