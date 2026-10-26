# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-INFRA-004` |
| **Nome** | Escalabilidade horizontal do worker de boletos |
| **Tipo** | Performance |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 1 |

---

## Descrição

### Texto do Requisito

> O serviço `worker-boletos` deve iniciar com 1 réplica e aceitar o comando `docker compose up -d --scale worker-boletos=4`, que deve resultar em 4 containers `worker-boletos` em execução simultânea, sem interromper os demais serviços.

### Condições de Aplicação

- Condição 1: Ambiente em execução.
- Condição 2: Fila `fila.boletos` com ou sem mensagens pendentes.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Enunciado, Prática 4, validação: "--scale consumer=4" |
| **Requisito Pai** | REQ-INFRA-001 |
| **Requisitos Filhos** | REQ-PERF-001 (vazão 4x — Pessoas 4 e 8) |
| **Casos de Uso / Histórias Relacionadas** | Demonstração ao vivo — etapa 4 da validação |

---

## Justificativa (Rationale)

É o item central da validação: com mais consumidores na mesma fila, a vazão aumenta proporcionalmente.

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
Funcionalidade: Escalabilidade
  Cenário: Escalar de 1 para 4 workers
    Dado que o ambiente está em execução com 1 worker-boletos
    Quando o operador executa "docker compose up -d --scale worker-boletos=4"
    Então "docker compose ps worker-boletos" lista 4 containers com status "Up"
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-INFRA-004a | `docker compose up -d --scale worker-boletos=4` | Comando termina sem erro |
| TEST-INFRA-004b | `docker compose ps worker-boletos` | `delivery-worker-boletos-1` a `-4` com status `Up` |

**Resultado:** Verificado em 20/10/2026: 4 réplicas `Up`.

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
- O serviço não pode ter `container_name` (cada réplica precisa de um nome próprio) nem `ports` (4 containers não podem usar a mesma porta do hospedeiro).
- A divisão justa das mensagens entre os 4 depende de `prefetch_count=1` no código do worker (Pessoa 4).

### Notas e Suposições
- `deploy.replicas: 1` define o valor inicial; o `--scale` sobrescreve esse valor.

### Anexos / Referências
- `docker-compose.yml` — serviço `worker-boletos`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
