# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-BD-002` |
| **Nome** | Restrição dos estados do pedido |
| **Tipo** | Funcional |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 2 |

---

## Descrição

### Texto do Requisito

> A coluna `pedidos.status` deve aceitar exclusivamente os valores `CRIADO`, `AGUARDANDO_PAGAMENTO`, `PAGO`, `ENVIO_AGENDADO`, `ENVIADO` e `CANCELADO`, assumir `CRIADO` quando nenhum valor for informado na inserção, e o banco deve rejeitar com erro qualquer outro valor.

### Condições de Aplicação

- Condição 1: Inserção de pedido pela API.
- Condição 2: Atualização de status por workers, agendador ou API.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | CLAUDE.md, "Estados do pedido"; CHECKLIST.md, Receita 2, Etapa 2 |
| **Requisito Pai** | REQ-BD-001 |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Ciclo de vida do pedido (SRS seção 2.2) |

---

## Justificativa (Rationale)

A coluna é escrita por cinco serviços diferentes. Validar no banco faz um valor como `pago` ou `PAGADO` falhar no momento da escrita, e não só quando o painel ou o agendador lerem o dado.

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
Funcionalidade: Estados válidos
  Cenário: Status inválido é rejeitado
    Dado que existe o pedido de id 1
    Quando um serviço executa "UPDATE pedidos SET status='PAGADO' WHERE id=1"
    Então o banco retorna o erro "violates check constraint pedidos_status_valido" e o status não muda
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-BD-002a | `INSERT` sem status | Pedido criado com `status = 'CRIADO'` |
| TEST-BD-002b | `UPDATE ... SET status='PAGADO'` | Erro `pedidos_status_valido` |

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
- O banco valida o valor do estado, não a ordem das transições (ex.: `ENVIADO → CRIADO`). A ordem é responsabilidade do código que muda o status.

### Notas e Suposições
- Optou-se por `CHECK` em vez de `ENUM` porque é mais simples de alterar caso surja um estado novo.

### Anexos / Referências
- `banco/init.sql` — constraint `pedidos_status_valido`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
