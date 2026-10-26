# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-BD-001` |
| **Nome** | Criação automática do esquema do banco |
| **Tipo** | Funcional |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 2 |

---

## Descrição

### Texto do Requisito

> Na primeira inicialização do serviço `postgres` com o volume `dados_postgres` vazio, o banco `delivery` deve conter as tabelas `pedidos` e `boletos`, com as colunas definidas na seção 3.5 do SRS, sem execução manual de comandos SQL.

### Condições de Aplicação

- Condição 1: Volume `dados_postgres` vazio (primeira subida ou após `docker compose down -v`).

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | CLAUDE.md, "Pessoa 2 — Pronto quando"; CHECKLIST.md, Receita 2, Etapas 2 e 5 |
| **Requisito Pai** | — |
| **Requisitos Filhos** | REQ-BD-002, REQ-BD-003 |
| **Casos de Uso / Histórias Relacionadas** | Demonstração ao vivo — subida do ambiente |

---

## Justificativa (Rationale)

Qualquer integrante consegue subir o projeto do zero no próprio notebook. Na apresentação, não existe um passo manual que alguém possa esquecer.

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
Funcionalidade: Esquema automático
  Cenário: Banco do zero
    Dado que o operador executou "docker compose down -v"
    Quando o operador executa "docker compose up -d" e depois "\dt" no psql
    Então a listagem mostra as tabelas "boletos" e "pedidos"
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-BD-001 | `docker compose down -v`, `up -d`, `psql -c '\dt'` | Tabelas `boletos` e `pedidos` listadas |

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
- O Postgres só executa os scripts de `/docker-entrypoint-initdb.d/` com o volume vazio. Uma mudança no `init.sql` só vale após `docker compose down -v`, que apaga os dados.

### Notas e Suposições
- O `init.sql` é montado como somente leitura (`:ro`).

### Anexos / Referências
- `banco/init.sql`

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
