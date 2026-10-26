# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-BD-004` |
| **Nome** | Persistência dos dados entre reinícios |
| **Tipo** | Confiabilidade |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 2 |

---

## Descrição

### Texto do Requisito

> Os dados do Postgres devem ser armazenados no volume nomeado `dados_postgres` e os do RabbitMQ no volume nomeado `dados_rabbitmq`, de forma que pedidos, boletos, filas duráveis e mensagens persistentes registrados antes de `docker compose stop` estejam presentes após `docker compose start`.

### Condições de Aplicação

- Condição 1: Parada com `docker compose stop`, `docker stop` ou `docker compose down` (sem `-v`).

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Enunciado (volumes, critério 1); CHECKLIST.md, Receita 2, Etapa 4 |
| **Requisito Pai** | — |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Arguição: "o que acontece se o banco cair?" |

---

## Justificativa (Rationale)

Containers são recriados a cada `docker compose up` com alteração de configuração; os dados precisam ficar fora deles, em volumes nomeados.

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
Funcionalidade: Persistência
  Cenário: Pedido sobrevive ao stop/start
    Dado que existe 1 pedido no banco e 1 mensagem na fila durável fila.teste
    Quando o operador executa "docker compose stop" e depois "docker compose start"
    Então "SELECT count(*) FROM pedidos" retorna 1 e a fila.teste mostra 1 mensagem no painel
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-BD-004a | Inserir pedido, `stop`, `start`, contar pedidos | Contagem igual à de antes |
| TEST-BD-004b | Criar fila durável com 1 mensagem persistente, `stop`, `start` | Fila e mensagem continuam lá |

**Resultado:** Verificado em 20/10/2026 (Postgres e RabbitMQ).

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
- O RabbitMQ usa `hostname: rabbitmq` fixo, porque grava os dados em uma pasta com o nome do nó. Com um hostname aleatório, as filas se perderiam ao recriar o container.
- Mensagens só sobrevivem se a fila for `durable` e a mensagem for publicada com `delivery_mode=2` (responsabilidade da Pessoa 3).

### Notas e Suposições
- `docker compose down -v` apaga os volumes de propósito. Usado apenas no teste de banco vazio.

### Anexos / Referências
- `docker-compose.yml` — seção `volumes`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
