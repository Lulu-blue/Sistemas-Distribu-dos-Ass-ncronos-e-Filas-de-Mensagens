# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-INFRA-003` |
| **Nome** | Ordem de inicialização por verificação de saúde |
| **Tipo** | Confiabilidade |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 1 |

---

## Descrição

### Texto do Requisito

> Os serviços `api`, `worker-boletos`, `worker-envios` e `agendador` devem iniciar somente depois que os serviços `rabbitmq` e `postgres` reportarem o estado `healthy`, conforme verificação de saúde (`healthcheck`) declarada no `docker-compose.yml`.

### Condições de Aplicação

- Condição 1: Primeira subida do ambiente.
- Condição 2: Subida após `docker compose down`.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Decisão técnica do grupo (CLAUDE.md, "Regras técnicas importantes"); critério 1 (dependências) |
| **Requisito Pai** | REQ-INFRA-001 |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Demonstração ao vivo — logs mostrando healthchecks |

---

## Justificativa (Rationale)

Um container em execução não está necessariamente pronto para conexões; o Postgres, por exemplo, ainda executa o `init.sql` nos primeiros segundos. Sem essa espera, a API e os workers tentariam conectar antes da hora e falhariam.

---

## Critérios de Verificação e Aceitação

### Método de Verificação
- [ ] Inspeção / Revisão
- [x] Teste
- [x] Demonstração
- [ ] Análise
- [ ] Simulação

### Critérios de Aceitação (Gherkin / BDD)
```gherkin
Funcionalidade: Ordem de inicialização
  Cenário: Workers esperam a infraestrutura
    Dado que o ambiente está desligado
    Quando o operador executa "docker compose up -d"
    Então o log do compose mostra "delivery-postgres-1 Healthy" e "delivery-rabbitmq-1 Healthy" antes de "delivery-api-1 Started"
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-INFRA-003a | `docker compose up -d` e leitura da saída | Linhas `Healthy` aparecem antes de `Started` dos 4 serviços de aplicação |
| TEST-INFRA-003b | `docker compose ps` após a subida | `rabbitmq` e `postgres` com `(healthy)` |

**Resultado:** Verificado em 20/10/2026: `Healthy` aparece antes de `Started`.

---

## Análise de Conformidade com a Norma

Verifique se o requisito atende às características da seção 5.2.5 da ISO/IEC/IEEE 29148:2018.

| Característica | Atende? | Observações |
|----------------|---------|-------------|
| **Necessary (Necessário)** | [x] Sim [ ] Não |  |
| **Appropriate (Apropriado)** | [x] Sim [ ] Não |  |
| **Unambiguous (Não ambíguo)** | [x] Sim [ ] Não |  |
| **Complete (Completo)** | [x] Sim [ ] Não |  |
| **Singular (Singular)** | [x] Sim [ ] Não |  |
| **Feasible (Factível)** | [x] Sim [ ] Não |  |
| **Verifiable (Verificável)** | [x] Sim [ ] Não |  |
| **Correct (Correto)** | [x] Sim [ ] Não |  |
| **Conforming (Conforme)** | [x] Sim [ ] Não |  |

---

## Informações Complementares

### Restrições e Dependências
- Healthcheck do RabbitMQ: `rabbitmq-diagnostics -q check_port_connectivity` (porta 5672 aceitando conexões).
- Healthcheck do Postgres: `pg_isready -h 127.0.0.1` (via TCP, para não reportar pronto durante a execução do `init.sql`).

### Notas e Suposições
- Os workers também tentam se reconectar ao RabbitMQ (responsabilidade das Pessoas 4 e 5), como segunda camada de proteção caso o broker reinicie depois da subida.

### Anexos / Referências
- `docker-compose.yml` — blocos `healthcheck` e âncora `x-depende-da-infra`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
