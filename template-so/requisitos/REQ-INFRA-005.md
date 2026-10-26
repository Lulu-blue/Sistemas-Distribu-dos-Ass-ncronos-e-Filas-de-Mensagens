# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-INFRA-005` |
| **Nome** | Reinício automático dos serviços |
| **Tipo** | Confiabilidade |
| **Prioridade** | Desejável |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 1 |

---

## Descrição

### Texto do Requisito

> Os serviços `rabbitmq`, `postgres`, `api`, `worker-boletos`, `worker-envios` e `agendador` devem usar a política de reinício `unless-stopped`, de forma que um container cujo processo principal termine sem parada manual seja reiniciado pelo Docker em até 10 segundos.

### Condições de Aplicação

- Condição 1: Container encerrado porque o processo principal terminou com erro (ex.: exceção no Python).
- Condição 2: Não se aplica a containers parados manualmente com `docker compose stop`, `docker stop` ou `docker kill`.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | CHECKLIST.md, Receita 1, Etapa 5 |
| **Requisito Pai** | REQ-INFRA-001 |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Teste de falha (Pessoa 8) |

---

## Justificativa (Rationale)

Se um worker cair durante a demo, ele volta sozinho. Junto com o `ack` manual, nenhuma mensagem se perde.

---

## Critérios de Verificação e Aceitação

### Método de Verificação
- [ ] Inspeção / Revisão
- [x] Teste
- [ ] Demonstração
- [ ] Análise
- [ ] Simulação

### Critérios de Aceitação (Gherkin / BDD)
```gherkin
Funcionalidade: Reinício automático
  Cenário: Worker volta após falha
    Dado que o worker-boletos está em execução
    Quando o processo principal do container é interrompido por dentro com "docker compose exec worker-boletos sh -c 'kill -INT 1'"
    Então "docker compose ps" mostra o container com status "Up" novamente em até 10 segundos e "docker inspect" mostra RestartCount maior que 0
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-INFRA-005a | `docker compose exec worker-boletos sh -c 'kill -INT 1'` e `docker compose ps` | Container volta para `Up`; `RestartCount` = 1 |
| TEST-INFRA-005b | `docker kill delivery-worker-boletos-1` | Container fica parado (parada manual não é desfeita) |

**Resultado:** Verificado em 20/10/2026: RestartCount = 1 após kill -INT 1; docker kill não reinicia (comportamento esperado).

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
- —

### Notas e Suposições
- `unless-stopped` respeita a parada manual: `docker compose stop`, `docker stop` e também `docker kill` contam como parada manual e não são desfeitos. Para o teste de falha da Pessoa 8, a queda precisa vir de dentro do processo.

### Anexos / Referências
- `docker-compose.yml` — chave `restart`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
