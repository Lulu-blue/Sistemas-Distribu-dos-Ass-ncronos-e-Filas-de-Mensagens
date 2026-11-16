# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-BD-003` |
| **Nome** | Um boleto por pedido |
| **Tipo** | Confiabilidade |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 2 |

---

## Descrição

### Texto do Requisito

> A tabela `boletos` deve referenciar um pedido existente por `pedido_id` e rejeitar a inserção de um segundo boleto para o mesmo `pedido_id`.

### Condições de Aplicação

- Condição 1: Reentrega de mensagem pelo RabbitMQ após queda de um worker antes do `ack`.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Decisão técnica do grupo (ack manual, CLAUDE.md) |
| **Requisito Pai** | REQ-BD-001 |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Teste de falha (Pessoa 8) |

---

## Justificativa (Rationale)

Com `ack` manual, uma mensagem pode ser entregue duas vezes (o worker salvou e caiu antes de confirmar). A regra de unicidade garante que isso não gere boleto duplicado.

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
Funcionalidade: Unicidade do boleto
  Cenário: Segunda inserção para o mesmo pedido
    Dado que o pedido 1 já tem boleto
    Quando um worker insere outro boleto com pedido_id 1
    Então o banco retorna o erro "duplicate key value violates unique constraint boletos_pedido_id_key"
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-BD-003 | Dois `INSERT` em `boletos` com o mesmo `pedido_id` | O segundo falha com `boletos_pedido_id_key` |

**Resultado:** Verificado em 20/10/2026.

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
- O worker de boletos (Pessoa 4) deve usar `INSERT ... ON CONFLICT (pedido_id) DO NOTHING` ou tratar o erro e dar `ack`, senão a mensagem fica voltando para a fila.

### Notas e Suposições
- `ON DELETE CASCADE`: apagar um pedido apaga o boleto dele.

### Anexos / Referências
- `banco/init.sql` — tabela `boletos`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
