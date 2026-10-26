# Especificação de Requisitos de Software (SRS)

> **Norma de referência:** ISO/IEC/IEEE 29148:2018  
> **Projeto:** `Delivery Assíncrono — Geração de Boletos com Fila de Mensagens`  
> **Versão:** `1.0`  
> **Data:** `20/10/2026`  
> **Autor:** `Luiza (Pessoas 1 e 2 — orquestração, banco de dados e configurações)`

---

## Histórico de Revisões

| Versão | Data | Autor | Alterações |
|--------|------|-------|------------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Rascunho inicial. Requisitos de infraestrutura e banco detalhados e verificados; requisitos de API, workers e painel em nível de resumo, para as Pessoas 3 a 6 completarem. |

---

## 1. Introdução

### 1.1 Propósito (Purpose)
Este documento especifica os requisitos do sistema **Delivery Assíncrono**. O sistema recebe uma grande quantidade de pedidos de delivery simultâneos e gera, para cada pedido, um boleto fictício, sem travar quando chegam milhares de pedidos de uma vez.

O público deste documento é: os 8 integrantes do grupo (para saber o que cada parte precisa cumprir e como as partes se encaixam), o professor da disciplina (para avaliar a configuração do orquestrador) e a Pessoa 7 (que usa este material no relatório em LaTeX).

### 1.2 Escopo (Scope)
- **a) Produto:** *Delivery Assíncrono*, composto por 6 serviços em containers Docker: `api`, `rabbitmq`, `worker-boletos`, `worker-envios`, `agendador` e `postgres`.
- **b) O que o produto fará:** receber pedidos e colocá-los em uma fila. Workers retiram os pedidos da fila, geram um boleto fictício (linha digitável e vencimento) e gravam o resultado no banco. Depois da aprovação do pagamento, outro worker agenda o envio. Boletos vencidos e não pagos são cancelados automaticamente.
- **c) Benefícios e objetivos:** demonstrar na prática o padrão **Produtor-Consumidor** com uma fila como *buffer*. A API responde assim que publica o pedido, e os workers consomem no próprio ritmo; a vazão aumenta adicionando réplicas (`--scale worker-boletos=4`).
- **d) Consistência com especificações superiores:** este SRS atende à **Prática 4** do enunciado `pratica.pdf` (Prof. Michel Pires da Silva, CEFET-MG). Os boletos são fictícios: nada é registrado em banco ou sistema financeiro real.

**Fora do escopo:** pagamento real, autenticação de clientes, envio de e-mail, implantação em nuvem ou em cluster.

### 1.3 Referências (References)

| Referência | Título | Versão | Data | Fonte |
|------------|--------|--------|------|-------|
| [REF-001] | Trabalho Prático: Orquestração de Serviços, Sistemas Distribuídos e Monitoramento com Containers | — | 2026 | `pratica.pdf` (DECOM / CEFET-MG) |
| [REF-002] | ISO/IEC/IEEE 29148:2018 — Requirements engineering | 2018 | 2018 | ISO |
| [REF-003] | Compose Specification | v2 | — | https://docs.docker.com/compose/ |
| [REF-004] | RabbitMQ Documentation — Consumer Prefetch, Acknowledgements | 3.13 | — | https://www.rabbitmq.com/docs |
| [REF-005] | PostgreSQL 16 Documentation | 16 | — | https://www.postgresql.org/docs/16/ |
| [REF-006] | Docker Official Image `postgres` — Initialization scripts | — | — | https://hub.docker.com/_/postgres |
| [REF-007] | Fichas de requisito do projeto | 1.0 | 20/10/2026 | `template-so/requisitos/` |

### 1.4 Termos (Terms)

| Termo | Definição |
|-------|-----------|
| Container | Processo isolado com sistema de arquivos, rede e dependências próprios, criado a partir de uma imagem. |
| Orquestrador | Ferramenta que cria e gerencia um conjunto de containers a partir de um manifesto (Docker Compose). |
| Broker | Serviço que armazena mensagens em filas até que um consumidor as retire (RabbitMQ). |
| Fila | Lista de mensagens em ordem de chegada (primeiro a entrar, primeiro a sair). |
| Produtor | Quem coloca mensagens na fila (serviço `api`). |
| Consumidor / Worker | Quem retira mensagens da fila e faz o trabalho (`worker-boletos`, `worker-envios`). |
| Ack (acknowledgement) | Confirmação do consumidor de que a mensagem foi processada; sem ela, o broker reentrega a mensagem. |
| Prefetch | Número máximo de mensagens entregues a um consumidor sem ack. |
| Réplica | Cópia idêntica de um mesmo serviço rodando em paralelo. |
| Escalabilidade horizontal | Aumentar a capacidade colocando mais cópias, em vez de uma máquina mais forte. |
| Healthcheck | Comando executado periodicamente pelo Docker para marcar o container como `healthy` ou `unhealthy`. |
| Volume | Armazenamento gerenciado pelo Docker, independente do ciclo de vida do container. |
| Rede Docker | Rede virtual privada onde os containers se enxergam pelo nome (ex.: `postgres`). |
| Linha digitável | Sequência numérica de um boleto (fictícia neste sistema). |
| Pico | Chegada de 5.000 pedidos de uma só vez (botão "Simular pico"). |

### 1.5 Abreviações (Abbreviations)

| Abreviação | Significado |
|------------|-------------|
| SRS | Software Requirements Specification |
| API | Application Programming Interface |
| AMQP | Advanced Message Queuing Protocol (protocolo do RabbitMQ, porta 5672) |
| SQL | Structured Query Language |
| HTTP | HyperText Transfer Protocol |
| JSON | JavaScript Object Notation |
| DNS | Domain Name System |
| TBD | To Be Defined (a definir) |

---

## 2. Visão Geral do Produto (Product Overview)

### 2.1 Perspectiva do Produto (Product Perspective)
O produto é independente: não faz parte de um sistema maior. A arquitetura está no diagrama de blocos abaixo. Todos os containers ficam na rede `rede_interna`, e só duas portas aparecem para o computador hospedeiro.

```
                    Navegador (computador hospedeiro)
                     │ :8000                 │ :15672
═════════════════════╪═══════════════════════╪══════════ rede_interna (bridge)
                     ▼                       ▼
              ┌─────────────┐  publica  ┌──────────────┐   consome   ┌──────────────────┐
              │     api     │──────────►│   rabbitmq   │────────────►│ worker-boletos×N │
              │ (Produtor)  │  AMQP     │ fila.boletos │  AMQP       │  (N = 1 ou 4)    │
              │ painel admin│  :5672    │ fila.envios  │             └────────┬─────────┘
              └──────┬──────┘           └──────┬───────┘                      │
                     │                         │ consome               grava boleto
                     │                         ▼                              │
                     │                  ┌──────────────┐                      │
                     │                  │ worker-envios│──── agenda envio ──┐ │
                     │                  └──────────────┘                    │ │
                     │ SQL :5432                                            ▼ ▼
                     └─────────────────────────────────────────────►┌──────────────┐
                                        ┌──────────────┐  cancela   │   postgres   │
                                        │  agendador   │───────────►│ pedidos      │
                                        │ (a cada 30 s)│  vencidos  │ boletos      │
                                        └──────────────┘            └──────┬───────┘
                                                                           │
                       volume dados_rabbitmq ◄── rabbitmq    postgres ──► volume dados_postgres
```

#### 2.1.1 Interfaces de Sistema (System Interfaces)

| Interface | Entre | Funcionalidade |
|-----------|-------|----------------|
| Publicação de pedido | `api` → `rabbitmq` (`fila.boletos`) | Coloca um pedido novo na fila para gerar boleto |
| Consumo de pedido | `rabbitmq` → `worker-boletos` | Entrega um pedido por vez a cada worker |
| Publicação de pagamento | `api` → `rabbitmq` (`fila.envios`) | Avisa que um pedido foi pago |
| Consumo de pagamento | `rabbitmq` → `worker-envios` | Entrega o pedido pago para agendar o envio |
| Persistência | `api`, workers e `agendador` → `postgres` | Lê e grava pedidos e boletos |

#### 2.1.2 Interfaces de Usuário (User Interfaces)
- **Painel admin** (`http://localhost:8000`): página HTML servida pela API, com o botão "Simular pico", a contagem de pedidos por status e a ação "Aprovar pagamento". Responsável: Pessoa 6.
- **Painel do RabbitMQ** (`http://localhost:15672`): interface pronta do RabbitMQ. Mostra o tamanho das filas e a taxa de consumo. Login com `RABBITMQ_USER` / `RABBITMQ_PASSWORD` do `.env`.
- **Terminal**: comandos `docker compose` para subir, escalar e inspecionar o sistema.

#### 2.1.3 Interfaces de Hardware (Hardware Interfaces)
Não há interface direta com hardware. O sistema roda em um notebook comum com Docker.

#### 2.1.4 Interfaces de Software (Software Interfaces)

| Nome | Mnemônico | Versão | Fonte | Propósito |
|------|-----------|--------|-------|-----------|
| RabbitMQ com plugin de gerenciamento | `rabbitmq` | 3.13 (`rabbitmq:3.13-management`) | Docker Hub | Broker de mensagens e painel web |
| PostgreSQL | `postgres` | 16 (`postgres:16`) | Docker Hub | Banco relacional |
| Python | — | 3.12 (`python:3.12-slim`) | Docker Hub | Base das imagens de api, workers e agendador |
| Docker Compose | — | v2 (testado em v5.3.1) | Docker | Orquestrador |

**Formato da mensagem nas filas** (contrato entre produtor e workers), em JSON e UTF-8:
```json
{ "pedido_id": 123, "cliente": "Ana Souza", "valor": 89.90, "criado_em": "2026-11-23T14:30:00" }
```

#### 2.1.5 Interfaces de Comunicação (Communication Interfaces)

| Porta | Protocolo | Serviço | Visível no hospedeiro? |
|-------|-----------|---------|------------------------|
| 8000 | HTTP | `api` | Sim |
| 15672 | HTTP | `rabbitmq` (painel) | Sim |
| 5672 | AMQP 0-9-1 | `rabbitmq` | Não, só na `rede_interna` |
| 5432 | PostgreSQL wire protocol | `postgres` | Não, só na `rede_interna` |

Dentro da rede, os containers se acham pelo nome do serviço, graças ao DNS interno do Docker (ex.: `POSTGRES_HOST=postgres`).

#### 2.1.6 Restrições de Memória (Memory Constraints)
Não há limites rígidos de memória definidos. Referência: o ambiente completo, com 4 workers, deve rodar em um notebook com 8 GB de RAM. O armazenamento cresce cerca de 1 MB a cada 5.000 pedidos.

#### 2.1.7 Operações (Operations)
- **a) Modos de operação:** *normal* (pedidos avulsos) e *pico* (5.000 pedidos de uma vez).
- **b) Operação não assistida:** os workers e o agendador rodam sem intervenção humana.
- **c) Suporte:** consultas prontas em `banco/consultas.sql`.
- **d) Backup e recuperação:** os dados ficam nos volumes `dados_postgres` e `dados_rabbitmq`. `docker compose down` preserva os volumes; `docker compose down -v` apaga os volumes e recria o banco do zero.

#### 2.1.8 Requisitos de Adaptação de Site (Site Adaptation Requirements)
- **a)** Para instalar em outro computador: `cp .env.exemplo .env`, trocar as senhas e rodar `docker compose up -d`. As tabelas são criadas automaticamente pelo `banco/init.sql`.
- **b)** Itens ajustáveis por instalação, no `.env`: senhas, fuso horário (`TZ`), tempo de processamento, prazo de pagamento, intervalo do agendador, prazo de envio e quantidade de pedidos do pico.

#### 2.1.9 Interfaces com Serviços (Interfaces with Services)
Não há integração com serviços em nuvem. O único acesso externo acontece na preparação: baixar as imagens do Docker Hub antes da apresentação.

### 2.2 Funções do Produto (Product Functions)
1. **Receber pedidos** (avulsos ou pico de 5.000) e publicá-los em `fila.boletos`.
2. **Gerar boletos**: cada worker pega uma mensagem, gera a linha digitável e o vencimento, espera `TEMPO_PROCESSAMENTO_SEGUNDOS`, grava no banco e só então confirma (ack).
3. **Aprovar pagamento** (painel), publicando o pedido em `fila.envios`.
4. **Agendar envio**: calcula a previsão de envio do pedido pago.
5. **Cancelar boletos vencidos**: a cada `INTERVALO_AGENDADOR_SEGUNDOS`.
6. **Acompanhar** o processamento pelos dois painéis e pelas consultas SQL.
7. **Escalar** o worker de boletos de 1 para 4 réplicas com um comando.

**Ciclo de vida do pedido (diagrama de estados):**
```
CRIADO ──(worker-boletos)──► AGUARDANDO_PAGAMENTO ──(api: aprovar)──► PAGO ──(worker-envios)──► ENVIO_AGENDADO ──► ENVIADO
                                     │
                                     └──(agendador: venceu  |  cliente desistiu)──► CANCELADO
```

### 2.3 Características do Usuário (User Characteristics)
- **Operador da demonstração:** integrante do grupo, estudante de Computação, que conhece o terminal e o Docker em nível básico a intermediário. Por isso, os comandos de operação se limitam a `docker compose up`, `ps`, `logs`, `exec` e `--scale`.
- **Avaliador (professor):** conhece Docker a fundo e pode pedir alterações ao vivo. Por isso, as configurações ficam centralizadas no `.env`.
- **Cliente final (simulado):** não interage diretamente. Seus pedidos são gerados com dados fictícios (Faker).

### 2.4 Limitações (Limitations)
- **a) Regulatórias:** boletos fictícios, sem valor legal. Os dados de clientes são fictícios (Faker).
- **b) Hardware:** um único hospedeiro (Docker Compose, não cluster).
- **d) Operação paralela:** várias réplicas do `worker-boletos` acessam o mesmo banco ao mesmo tempo. A integridade é garantida por restrições no banco (REQ-BD-003).
- **g) Linguagem:** os serviços de aplicação são escritos em Python 3.12.
- **i) Qualidade:** a demonstração é cronometrada (40 minutos no total).
- **k) Segurança:** as senhas não podem ir para o repositório público (REQ-CONF-001).

### 2.5 Suposições e Dependências (Assumptions and Dependencies)
- O notebook da apresentação já tem o Docker instalado e as imagens baixadas.
- As portas 8000 e 15672 do hospedeiro estão livres.
- As Pessoas 3, 4 e 5 seguem os nomes de variáveis (seção 3.1) e de colunas (seção 3.5) definidos aqui.
- Os workers implementam `prefetch_count=1`, ack manual e reconexão ao RabbitMQ.

### 2.6 Distribuição de Requisitos (Apportioning of Requirements)

| Requisito | Serviço / artefato | Responsável |
|-----------|--------------------|-------------|
| REQ-INFRA-001 a 005 | `docker-compose.yml` | Pessoa 1 |
| REQ-CONF-001 | `.env`, `.env.exemplo`, `.gitignore` | Pessoa 2 |
| REQ-BD-001 a 004 | `banco/init.sql`, volumes | Pessoa 2 |
| REQ-BD-005 | `banco/consultas.sql` | Pessoa 2 |
| REQ-FUNC-001, 002, 004 | `api/` | Pessoa 3 |
| REQ-FUNC-003, REQ-PERF-001 | `worker-boletos/` | Pessoa 4 |
| REQ-FUNC-005, 006 | `worker-envios/`, `agendador/` | Pessoa 5 |
| REQ-FUNC-007 | painel HTML em `api/` | Pessoa 6 |

**Adiáveis para versões futuras:** transição `ENVIO_AGENDADO → ENVIADO` automática; cancelamento pelo cliente.

### 2.7 Requisitos Especificados (Specified Requirements)
Os requisitos estão nas seções 3 e 4. Cada um tem um identificador único `REQ-[CATEGORIA]-[NNN]`. Os de infraestrutura e banco têm ficha completa em `template-so/requisitos/`, com a análise de conformidade da seção 5.2.5 da norma.

---

## 3. Requisitos Específicos (Specific Requirements)

### 3.1 Interfaces Externas (External Interfaces)

**Variáveis de ambiente** (arquivo `.env`, lidas pelo `docker-compose.yml` e repassadas aos containers):

| Nome | Propósito | Usado por | Valor na demo | Unidade |
|------|-----------|-----------|---------------|---------|
| `TZ` | Fuso horário | todos | `America/Sao_Paulo` | — |
| `POSTGRES_DB` | Nome do banco | postgres, api, workers, agendador | `delivery` | — |
| `POSTGRES_USER` | Usuário do banco | idem | `delivery` | — |
| `POSTGRES_PASSWORD` | Senha do banco | idem | (secreta) | — |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Endereço do banco (definido no compose) | api, workers, agendador | `postgres` / `5432` | — |
| `RABBITMQ_USER` | Usuário do broker | rabbitmq, api, workers, agendador | `delivery` | — |
| `RABBITMQ_PASSWORD` | Senha do broker | idem | (secreta) | — |
| `RABBITMQ_HOST` / `RABBITMQ_PORT` | Endereço do broker (definido no compose) | api, workers, agendador | `rabbitmq` / `5672` | — |
| `FILA_BOLETOS` | Fila de pedidos novos | api, worker-boletos | `fila.boletos` | — |
| `FILA_ENVIOS` | Fila de pedidos pagos | api, worker-envios | `fila.envios` | — |
| `TEMPO_PROCESSAMENTO_SEGUNDOS` | Duração do `sleep` por mensagem | worker-boletos, worker-envios | `1` | segundos |
| `PRAZO_PAGAMENTO_MINUTOS` | Vencimento do boleto após geração | api, worker-boletos | `2` | minutos |
| `INTERVALO_AGENDADOR_SEGUNDOS` | Período da busca por vencidos | agendador | `30` | segundos |
| `PRAZO_ENVIO_MINUTOS` | Previsão de envio após pagamento | worker-envios | `5` | minutos |
| `QTD_PEDIDOS_PICO` | Pedidos do botão "Simular pico" | api | `5000` | pedidos |

**Mensagem na fila:** ver seção 2.1.4. Campos: `pedido_id` (inteiro > 0, igual a `pedidos.id`), `cliente` (texto ≤ 150 caracteres), `valor` (decimal > 0, 2 casas, em reais), `criado_em` (data e hora ISO 8601).

### 3.2 Funções (Functions)

| ID | Requisito | Responsável |
|----|-----------|-------------|
| REQ-FUNC-001 | A `api` deve gravar o pedido com status `CRIADO` e publicá-lo em `FILA_BOLETOS` no formato da seção 2.1.4. | Pessoa 3 |
| REQ-FUNC-002 | A ação "Simular pico" deve publicar `QTD_PEDIDOS_PICO` mensagens e responder ao navegador sem esperar o processamento. | Pessoa 3 |
| REQ-FUNC-003 | O `worker-boletos` deve gravar o boleto, mudar o pedido para `AGUARDANDO_PAGAMENTO` e só então enviar o ack. | Pessoa 4 |
| REQ-FUNC-004 | "Aprovar pagamento" deve mudar o pedido de `AGUARDANDO_PAGAMENTO` para `PAGO` e publicá-lo em `FILA_ENVIOS`. | Pessoa 3 |
| REQ-FUNC-005 | O `worker-envios` deve preencher `previsao_envio` e mudar o status para `ENVIO_AGENDADO`. | Pessoa 5 |
| REQ-FUNC-006 | O `agendador` deve mudar para `CANCELADO` os pedidos `AGUARDANDO_PAGAMENTO` com `boletos.vencimento` anterior ao horário atual. | Pessoa 5 |
| REQ-FUNC-007 | O painel deve exibir a quantidade de pedidos por status. | Pessoa 6 |
| REQ-BD-001 | Criação automática do esquema. [Ficha](requisitos/REQ-BD-001.md) | Pessoa 2 |
| REQ-BD-002 | Restrição dos 6 estados do pedido. [Ficha](requisitos/REQ-BD-002.md) | Pessoa 2 |
| REQ-BD-005 | Consultas de acompanhamento. [Ficha](requisitos/REQ-BD-005.md) | Pessoa 2 |

**Situações anormais:**
- *Falha de comunicação com o broker:* os workers tentam se reconectar (Pessoas 4 e 5), e o Docker reinicia o container cujo processo terminar (REQ-INFRA-005).
- *Queda do worker no meio de uma mensagem:* sem ack, o RabbitMQ devolve a mensagem para a fila, e a regra de unicidade impede boleto duplicado (REQ-BD-003).
- *Dado inválido:* o banco rejeita status fora dos 6 valores e valor ≤ 0 (REQ-BD-002).

### 3.3 Requisitos de Usabilidade (Usability Requirements)
- REQ-USA-001: o operador deve conseguir executar a validação completa (subir, pico, 1 worker, 4 workers) usando somente os comandos listados no cabeçalho do `docker-compose.yml` e os botões do painel.

### 3.4 Requisitos de Desempenho (Performance Requirements)
**Estáticos:** até 4 réplicas simultâneas de `worker-boletos`; 5.000 pedidos por pico.

**Dinâmicos:**
- REQ-PERF-001: com `TEMPO_PROCESSAMENTO_SEGUNDOS=1`, a vazão de boletos com 4 réplicas deve ser de no mínimo 3,5 vezes a vazão com 1 réplica, medida pela consulta 2 de `consultas.sql` em uma janela de 2 minutos. (Responsáveis: Pessoas 4 e 8.)
- REQ-PERF-002: a publicação dos 5.000 pedidos do pico deve terminar em até 30 segundos. (Responsável: Pessoa 3.)
- REQ-INFRA-004: escalar de 1 para 4 workers com um comando. [Ficha](requisitos/REQ-INFRA-004.md)

> Valor de referência: com sleep de 1 s, 1 worker processa cerca de 60 boletos/min (5.000 em ~83 min) e 4 workers processam cerca de 240 boletos/min (~21 min).

### 3.5 Requisitos Lógicos de Banco de Dados (Logical Database Requirements)

**Entidades e relacionamento:** `pedidos 1 ──── 0..1 boletos` (um pedido tem no máximo um boleto).

**Tabela `pedidos`**

| Coluna | Tipo | Regra |
|--------|------|-------|
| `id` | BIGINT (identidade) | Chave primária; é o `pedido_id` da mensagem |
| `cliente` | VARCHAR(150) | Obrigatório |
| `valor` | NUMERIC(10,2) | Obrigatório, > 0 |
| `status` | VARCHAR(25) | Obrigatório, padrão `CRIADO`, só os 6 estados |
| `criado_em` | TIMESTAMPTZ | Padrão: agora |
| `atualizado_em` | TIMESTAMPTZ | Atualizado automaticamente em cada UPDATE (trigger) |
| `previsao_envio` | TIMESTAMPTZ | Opcional; preenchido pelo worker-envios |

**Tabela `boletos`**

| Coluna | Tipo | Regra |
|--------|------|-------|
| `id` | BIGINT (identidade) | Chave primária |
| `pedido_id` | BIGINT | Obrigatório, **único**, chave estrangeira para `pedidos(id)` com `ON DELETE CASCADE` |
| `linha_digitavel` | VARCHAR(60) | Obrigatório |
| `vencimento` | TIMESTAMPTZ | Obrigatório |
| `gerado_em` | TIMESTAMPTZ | Padrão: agora |
| `gerado_por` | VARCHAR(64) | Hostname do container worker que gerou o boleto |

- **Frequência de uso:** durante o pico, cerca de 4 inserções por segundo em `boletos` e 4 atualizações por segundo em `pedidos` (4 workers); leitura do painel a cada poucos segundos.
- **Índices:** `pedidos(status)`, `boletos(gerado_em)`, `boletos(vencimento)`.
- **Integridade:** REQ-BD-002 (estados), REQ-BD-003 (unicidade).
- **Segurança:** acesso só pela `rede_interna`, com usuário e senha do `.env` (REQ-INFRA-002, REQ-CONF-001).
- **Retenção:** os dados persistem no volume `dados_postgres` até `docker compose down -v` (REQ-BD-004).

### 3.6 Restrições de Design (Design Constraints)
- Orquestração obrigatoriamente com Docker Compose ([REF-001]).
- O serviço que escala (`worker-boletos`) não pode ter `container_name` nem `ports` ([Ficha REQ-INFRA-004](requisitos/REQ-INFRA-004.md)).
- Os serviços de aplicação iniciam após o healthcheck do broker e do banco ([Ficha REQ-INFRA-003](requisitos/REQ-INFRA-003.md)).
- Subida com um único comando ([Ficha REQ-INFRA-001](requisitos/REQ-INFRA-001.md)).
- Os workers usam `prefetch_count=1` e ack manual após a gravação no banco.

### 3.7 Conformidade com Padrões (Standards Compliance)
- **Nomenclatura:** serviços, tabelas, colunas e variáveis em português, sem acento, em `snake_case` (tabelas e colunas), `kebab-case` (serviços) e `MAIÚSCULAS` (variáveis de ambiente).
- **Estados:** em MAIÚSCULAS, exatamente como na seção 2.2.
- **Documentação de requisitos:** ISO/IEC/IEEE 29148:2018 ([REF-002]).

### 3.8 Atributos do Sistema de Software (Software System Attributes)
- **a) Confiabilidade:** ack manual com unicidade no banco garante que cada pedido gere exatamente um boleto ([REQ-BD-003](requisitos/REQ-BD-003.md)).
- **b) Disponibilidade:** reinício automático ([REQ-INFRA-005](requisitos/REQ-INFRA-005.md)) e persistência em volumes ([REQ-BD-004](requisitos/REQ-BD-004.md)).
- **c) Segurança:** exposição mínima de portas ([REQ-INFRA-002](requisitos/REQ-INFRA-002.md)) e segredos fora do repositório ([REQ-CONF-001](requisitos/REQ-CONF-001.md)).
- **d) Manutenibilidade:** um serviço por pasta, cada um com seu Dockerfile; variáveis comuns declaradas uma única vez no compose (âncora `x-variaveis-app`).
- **e) Portabilidade:** roda em qualquer sistema com Docker (Linux, Windows com WSL2, macOS), sem instalar Python ou Postgres no hospedeiro.

---

## 4. Verificação (Verification)

| Requisito | Método | Como verificar | Situação em 20/10/2026 |
|-----------|--------|----------------|------------------------|
| REQ-INFRA-001 | Teste | `docker compose up -d` + `docker compose ps` → 6 serviços `Up` | Verificado |
| REQ-INFRA-002 | Teste / Inspeção | `curl` em 8000 e 15672 → 200; 5672 recusa conexão; `postgres` sem mapeamento de porta | Verificado |
| REQ-INFRA-003 | Demonstração | Saída do `up -d` mostra `Healthy` antes de `Started` | Verificado |
| REQ-INFRA-004 | Teste | `--scale worker-boletos=4` → 4 containers `Up` | Verificado |
| REQ-INFRA-005 | Teste | `kill -INT 1` dentro do worker → `RestartCount = 1` | Verificado |
| REQ-CONF-001 | Inspeção | `diff .env .env.exemplo` → só as senhas diferem | Verificado |
| REQ-BD-001 | Teste | `down -v`, `up -d`, `\dt` → 2 tabelas | Verificado |
| REQ-BD-002 | Teste | `UPDATE ... 'PAGADO'` → erro `pedidos_status_valido` | Verificado |
| REQ-BD-003 | Teste | Segundo boleto do mesmo pedido → erro `boletos_pedido_id_key` | Verificado |
| REQ-BD-004 | Teste | `stop`/`start` → pedido e mensagem da fila durável continuam lá | Verificado |
| REQ-BD-005 | Teste | `psql < banco/consultas.sql` → 7 consultas sem erro | Verificado |
| REQ-FUNC-001 a 007 | Teste / Demonstração | A definir pelas Pessoas 3 a 6 | Pendente (TBD-001) |
| REQ-PERF-001 | Análise | Consulta 2 com 1 e com 4 workers; razão ≥ 3,5 | Pendente (TBD-002) |
| REQ-PERF-002 | Teste | Cronometrar o pico | Pendente (TBD-001) |

Critérios de aceitação detalhados (Gherkin) e casos de teste estão em cada ficha em `requisitos/`.

---

## 5. Informações de Suporte (Supporting Information)
- **a) Exemplo de entrada/saída:** a mensagem `{"pedido_id": 1, "cliente": "Ana Souza", "valor": 89.90, ...}` gera em `boletos` uma linha com `pedido_id = 1`, `linha_digitavel` fictícia e `vencimento` = agora + `PRAZO_PAGAMENTO_MINUTOS`.
- **b) Roteiro da validação ao vivo:** (1) `docker compose up -d`; (2) `docker compose stop worker-boletos` para a fila encher; (3) "Simular pico" e mostrar a fila com 5.000 mensagens no painel 15672; (4) `docker compose up -d --scale worker-boletos=1` e mostrar a fila caindo devagar (~1 msg/s); (5) `docker compose up -d --scale worker-boletos=4` e mostrar a taxa ~4 msg/s e a consulta 4 com os 4 hostnames.
- **c) Problema resolvido:** sem fila, 5.000 requisições simultâneas tentariam gerar boletos ao mesmo tempo e derrubariam o servidor e o banco. Com a fila, a API apenas registra e publica o pedido, e os workers processam na vazão que suportam.
- **d) Empacotamento:** repositório GitHub com `docker-compose.yml`, `.env.exemplo`, `banco/` e uma pasta por serviço.

Os itens desta seção **não** são requisitos; são informação de apoio.

---

## Apêndice A — Índice (Index)

| Tema | Seção |
|------|-------|
| Arquitetura (diagrama) | 2.1 |
| Portas | 2.1.5 |
| Estados do pedido | 2.2 |
| Variáveis de ambiente | 3.1 |
| Tabelas do banco | 3.5 |
| Verificação | 4 |
| Fichas de requisito | `requisitos/` |

---

## Apêndice B — Modelos de Análise

**Diagrama ER**
```
┌───────────────────────────┐          ┌───────────────────────────┐
│ pedidos                   │          │ boletos                   │
├───────────────────────────┤          ├───────────────────────────┤
│ PK id             BIGINT  │1     0..1│ PK id             BIGINT  │
│    cliente        VARCHAR │◄─────────│ FK pedido_id (UQ) BIGINT  │
│    valor          NUMERIC │          │    linha_digitavel VARCHAR│
│    status         VARCHAR │          │    vencimento     TSTZ    │
│    criado_em      TSTZ    │          │    gerado_em      TSTZ    │
│    atualizado_em  TSTZ    │          │    gerado_por     VARCHAR │
│    previsao_envio TSTZ    │          └───────────────────────────┘
└───────────────────────────┘
```

O diagrama de estados está na seção 2.2 e o diagrama de blocos na seção 2.1.

---

## Apêndice C — Lista de Itens a Definir (TBD)

| ID | Localização | Descrição | Responsável | Prazo |
|----|-------------|-----------|-------------|-------|
| TBD-001 | 3.2, 3.4, 4 | Critérios de verificação de REQ-FUNC-001 a 007 e REQ-PERF-002 | Pessoas 3, 4, 5 e 6 | 01/11/2026 |
| TBD-002 | 3.4, 4 | Medição real de vazão 1 vs 4 workers (REQ-PERF-001) | Pessoas 4 e 8 | 15/11/2026 |
| TBD-003 | 2.4 | Quem e como dispara `ENVIO_AGENDADO → ENVIADO` | Pessoa 5 | 01/11/2026 |
