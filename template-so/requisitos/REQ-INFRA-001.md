# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-INFRA-001` |
| **Nome** | Subida do ambiente com um único comando |
| **Tipo** | Restrição de Design |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 1 |

---

## Descrição

### Texto do Requisito

> O arquivo `docker-compose.yml` deve declarar os serviços `rabbitmq`, `postgres`, `api`, `worker-boletos`, `worker-envios` e `agendador`, de forma que o comando `docker compose up -d`, executado na raiz do repositório, coloque os 6 serviços no estado `running` sem intervenção manual adicional.

### Condições de Aplicação

- Condição 1: Docker Engine ≥ 24 e Docker Compose v2 instalados no computador da apresentação.
- Condição 2: Arquivo `.env` presente na raiz (criado a partir de `.env.exemplo`).

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Enunciado `pratica.pdf`, Prática 4, item 1; critério de avaliação 1 (3,0 pts) |
| **Requisito Pai** | — |
| **Requisitos Filhos** | REQ-INFRA-002, REQ-INFRA-003, REQ-INFRA-004, REQ-INFRA-005 |
| **Casos de Uso / Histórias Relacionadas** | Demonstração ao vivo — etapa "Subida do Ambiente" |

---

## Justificativa (Rationale)

O enunciado exige um manifesto de orquestração e a execução ao vivo do comando de inicialização. Um único comando reduz o risco de erro durante a apresentação de 40 minutos.

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
Funcionalidade: Subida do ambiente
  Cenário: Ambiente sobe do zero
    Dado que o volume do banco está vazio e o arquivo .env existe
    Quando o operador executa "docker compose up -d"
    Então "docker compose ps" lista os 6 serviços com status "Up" em até 120 segundos
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-INFRA-001a | `docker compose config --quiet` | Saída vazia, código de retorno 0 |
| TEST-INFRA-001b | `docker compose up -d` seguido de `docker compose ps` | 6 serviços com status `Up` |

**Resultado:** Verificado em 20/10/2026: 6 serviços `Up`.

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
- Depende de os Dockerfiles das pastas `api/`, `worker-boletos/`, `worker-envios/` e `agendador/` existirem (provisórios até as Pessoas 3, 4 e 5 entregarem).

### Notas e Suposições
- As imagens `rabbitmq:3.13-management`, `postgres:16` e `python:3.12-slim` são baixadas antes da apresentação, para não depender da internet ao vivo.

### Anexos / Referências
- `docker-compose.yml`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
