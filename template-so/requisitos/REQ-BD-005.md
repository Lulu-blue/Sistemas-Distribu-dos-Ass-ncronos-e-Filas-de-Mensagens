# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-BD-005` |
| **Nome** | Consultas de acompanhamento do processamento |
| **Tipo** | Funcional |
| **Prioridade** | Desejável |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 2 |

---

## Descrição

### Texto do Requisito

> O arquivo `banco/consultas.sql` deve fornecer consultas que retornem: (a) a quantidade de pedidos por status; (b) a quantidade de boletos gerados por minuto; (c) o total de boletos gerados; (d) a quantidade de boletos por container gerador.

### Condições de Aplicação

- Condição 1: Durante e após o processamento do pico de 5.000 pedidos.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | CLAUDE.md, "Pessoa 2"; CHECKLIST.md, Receita 2, Etapa 3 |
| **Requisito Pai** | — |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Painel admin (Pessoa 6); medição 1 vs 4 workers (Pessoa 8) |

---

## Justificativa (Rationale)

Os números do banco provam a validação: com 1 worker saem cerca de 60 boletos por minuto e com 4 workers cerca de 240. Também mostram que os 4 containers dividem o trabalho.

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
Funcionalidade: Consultas
  Cenário: Boletos por minuto
    Dado que o worker-boletos gerou boletos nos últimos 2 minutos
    Quando o operador executa a consulta 2 de consultas.sql
    Então o resultado lista um registro por minuto com a contagem de boletos daquele minuto
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-BD-005 | `psql < banco/consultas.sql` | As 7 consultas executam sem erro |

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
- A consulta (d) depende de o worker preencher `boletos.gerado_por` com `socket.gethostname()` (Pessoa 4).

### Notas e Suposições
- Os índices em `pedidos(status)` e `boletos(gerado_em)` mantêm essas consultas rápidas com milhares de linhas.

### Anexos / Referências
- `banco/consultas.sql`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
