# Ficha de Requisito

> **Norma de referência:** ISO/IEC/IEEE 29148:2018 (Seções 5.2.5 e 5.2.8)

---

## Identificação

| Campo | Valor |
|-------|-------|
| **ID** | `REQ-CONF-001` |
| **Nome** | Configuração externa e segredos fora do repositório |
| **Tipo** | Segurança |
| **Prioridade** | Essencial |
| **Status** | Verificado |
| **Versão** | `1.0` |
| **Responsável** | Pessoa 2 |

---

## Descrição

### Texto do Requisito

> As credenciais do Postgres e do RabbitMQ, os nomes das filas e os parâmetros de tempo (`TEMPO_PROCESSAMENTO_SEGUNDOS`, `PRAZO_PAGAMENTO_MINUTOS`, `INTERVALO_AGENDADOR_SEGUNDOS`, `PRAZO_ENVIO_MINUTOS`) devem ser lidos do arquivo `.env`; o repositório deve conter o arquivo `.env.exemplo` com as mesmas chaves e senhas substituídas por `troque_aqui`, e o `.gitignore` deve excluir o `.env`.

### Condições de Aplicação

- Condição 1: Clonagem do repositório por um integrante novo.
- Condição 2: Alteração de tempos para a demo.

---

## Rastreabilidade

| Campo | Valor |
|-------|-------|
| **Fonte (Source)** | Enunciado (variáveis de ambiente, critério 1); CHECKLIST.md, Receita 2, Etapa 1 |
| **Requisito Pai** | — |
| **Requisitos Filhos** | — |
| **Casos de Uso / Histórias Relacionadas** | Arguição: professor pede para alterar o tempo de sleep ao vivo |

---

## Justificativa (Rationale)

Trocar um tempo ou uma senha não exige mexer no código. Isso é útil se o professor pedir uma alteração ao vivo. Além disso, a senha real não vai parar no GitHub.

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
Funcionalidade: Configuração externa
  Cenário: Senha ausente impede a subida
    Dado que o .env não define POSTGRES_PASSWORD
    Quando o operador executa "docker compose config"
    Então o comando falha com a mensagem "defina POSTGRES_PASSWORD no .env"
```

### Casos de Teste Associados
| ID do Teste | Descrição | Resultado Esperado |
|-------------|-----------|--------------------|
| TEST-CONF-001a | `diff .env .env.exemplo` | Diferença só nas linhas de senha e no comentário de cabeçalho |
| TEST-CONF-001b | `git check-ignore .env` | Imprime `.env` |
| TEST-CONF-001c | Alterar `TEMPO_PROCESSAMENTO_SEGUNDOS` e rodar `docker compose up -d` | Worker recriado com o novo valor em `docker compose exec worker-boletos env` |

**Resultado:** Verificado em 20/10/2026 (TEST-CONF-001a).

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
- Os nomes das variáveis são um contrato com as Pessoas 3, 4 e 5. Renomear uma variável exige avisar os três.

### Notas e Suposições
- O compose usa `${VAR:?mensagem}` nas senhas para falhar cedo, com mensagem clara, se elas faltarem.

### Anexos / Referências
- `.env.exemplo`
- `.gitignore`
- SRS seção 3.1, tabela de variáveis

---

## Histórico de Alterações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| 1.0 | 20/10/2026 | Luiza (Pessoas 1 e 2) | Criação inicial |
