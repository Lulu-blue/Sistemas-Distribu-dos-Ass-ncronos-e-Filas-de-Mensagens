# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-INFRA-002` |
| **Nome** | Isolamento de rede e exposição mínima de portas |
| **Tipo** | Segurança |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 1 |

---

## Descrição

### Texto do Requisito

> Os 6 serviços devem se comunicar exclusivamente pela rede Docker `rede_interna`, e o computador hospedeiro deve ter acesso somente às portas 8000 (serviço `api`) e 15672 (painel web do `rabbitmq`); as portas 5432 (Postgres) e 5672 (AMQP) não devem ser publicadas no hospedeiro.

### Condições de Aplicação

- Condição 1: Ambiente em execução via `docker compose up -d`.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Enunciado (configuração de redes, critério 1); decisão de arquitetura do grupo (CLAUDE.md) |
| **Requisito Pai** | REQ-INFRA-001 |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Arguição: "por que o banco não tem porta?" |

---

## Justificativa (Rationale)

Expor só o necessário diminui a superfície de ataque: o banco e o broker ficam acessíveis apenas aos containers que precisam deles. Os containers se encontram pelo nome do serviço (DNS interno do Docker), por exemplo `postgres:5432`.

---

## Critérios de Verificação e Aceitação

### Método de Verificação
- [x] Inspeção / Revisão
- [x] Teste
- [ ] Demonstração
- [ ] Análise
- [ ] Simulação

### Critérios de Aceitação (Gherkin / BDD)
```gherkin
Funcionalidade: Isolamento de rede
  Cenário: Banco inacessível de fora
    Dado que o ambiente está em execução
    Quando o operador executa "docker compose ps"
    Então apenas api mostra "0.0.0.0:8000->8000/tcp", apenas rabbitmq mostra "0.0.0.0:15672->15672/tcp" e postgres mostra somente "5432/tcp" (sem mapeamento)
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-INFRA-002a | `curl localhost:8000` e `curl localhost:15672` | HTTP 200 nos dois |
| TEST-INFRA-002b | Conexão TCP em `localhost:5672` | Conexão recusada |
| TEST-INFRA-002c | Coluna PORTS de `docker compose ps` para `postgres` | `5432/tcp` sem `0.0.0.0:` |

**Resultado:** Verificado em 20/10/2026: 8000 e 15672 respondem; 5672 recusa conexão; postgres sem mapeamento.

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
- Se o hospedeiro tiver um PostgreSQL próprio instalado, a porta 5432 do hospedeiro aparece aberta por causa dele, não do container. A verificação correta é pela coluna PORTS do `docker compose ps`.

### Notas e Suposições
- A rede usa o driver `bridge` (rede virtual local de um único hospedeiro).

### Anexos / Referências
- `docker-compose.yml` — seções `ports` e `networks`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
