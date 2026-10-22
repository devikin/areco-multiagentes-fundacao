# Areco — Registro de desenvolvimento v0.2.26 — 21/10/2026

## Evidência observada
Após a v0.2.25, o usuário relatou divergência entre navegador e smoke terminal. Nos dois cenários, a mensagem `205` foi transformada pela LLM em ano 2050. O financeiro consultou 2050 e gerou citação a `lancamentos_financeiros.csv` com 0 registros; o teste terminal falhou justamente porque a resposta de `205` não deveria ter fonte. Após `2025` no frontend, o agente retomou o pedido e apresentou os departamentos corretamente.

## Diagnóstico
O esquema tipado `FinancePlan.year` aceita 2000–2099. A função de validação de consistência anterior somente comparava o plano aos anos de 4 dígitos **quando já existia** um ano desse formato na pergunta. Assim, `205` podia virar `2050` sem violar a validação. A LLM gerava plano com 2050, a consulta era executada e surgia uma citação real para uma pergunta não autorizada.

## Decisões e implementação
- `workflow.py`: instrução breve ao Financeiro para não completar/inferir anos, datas e identificadores, pedir correção de maneira natural e preservar a intenção entre turnos. Exemplo concreto: `205` deve gerar pedido de quatro dígitos; `2025` deve acionar consulta por departamento.
- `finance_queries.py`: validação *antes* de acessar o SQLite. Impede consultas se o último complemento é numérico e incompleto, se o ano do plano não está presente em quatro dígitos no texto fornecido, se meses adicionais foram presumidos, se filtros de identificação não aparecem na solicitação ou se o agrupamento explícito `por departamento` é ignorado.
- A ferramenta retorna mensagens técnicas `ANO_NAO_CONFIRMADO`, `PERIODO_NAO_CONFIRMADO`, `FILTRO_NAO_CONFIRMADO` ou `AGRUPAMENTO_NAO_CONFIRMADO` com lista de fontes vazia; o GPT-4.1 mini permanece responsável por **formular** a pergunta de esclarecimento. Nenhuma nova resposta fixa foi adicionada ao backend.
- Preservados Agents SDK, memória nativa, handoffs, `.env`, tabelas, dados e fontes. Versão do frontend e da API atualizada para v0.2.26.
- O teste real focado `scripts/check_year_guard_sdk_http.py` verifica três turnos com a OpenAI, sem custo adicional de guardrails. O teste completo `scripts/check_redesign_sdk_http.py` também reprova `205` com qualquer fonte e exige ferramenta + fonte + agrupamento no turno `2025`.

## Validação local e pendências
- Testes locais: 21 PASS, com FakeRunner para sessões e execução direta da ferramenta para casos de consulta, com SQLite temporário contendo registros. Sem chamadas à OpenAI ou ao Docker neste ambiente.
- Testes de ferramenta comprovam que `205`/`20`/`202`/`5` não abrem nem criam arquivo SQLite, mesmo se a LLM montar um plano para 2050; `2025` executa agrupamento por departamento correto.
- Requer teste no Docker do usuário, com GPT-4.1 mini real, para confirmar que a LLM responde naturalmente após a recusa técnica do plano, sem abrir loops e sem mentir sobre consulta.

## Limitação explícita
A validação deliberadamente pede confirmação quando a pergunta usa datas relativas sem ano numérico explícito (`ano passado`), em vez de inventar o ano. Consultas por meses numerados/abreviados podem precisar de extensões futuras para reconhecer o formato sem fragilizar a segurança. Respostas conversacionais ainda dependem do comportamento probabilístico do modelo; o backend só protege a integridade da consulta.
