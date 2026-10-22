# v0.2.25 — Continuidade do especialista após esclarecimento (21/10/2026)

## Evidência trazida pelo usuário
O smoke v0.2.24 retornou respostas adequadas de saudação, políticas, Ouvidoria, segurança, fora de escopo e atendimento humano. O caso Financeiro não concluiu: após a pergunta sobre despesas por departamento, o especialista solicitou período; em seguida `205` foi interpretado pelo orquestrador como possível departamento e `2025` não originou consulta financeira. As duas respostas eram LLM, sem fontes/ferramentas. O smoke v0.2.24 tinha asserts apenas de resposta não-vazia nesses turnos, portanto era insuficiente para indicar a falha.

## Diagnóstico técnico
`service.py` sempre iniciava cada `Runner.run` com `self.orchestrator`. O Agents SDK mantinha mensagens anteriores em `SQLiteSession`, mas o agente inicial, novamente Orquestrador, podia ignorar o esclarecimento aberto e reinterpretar uma resposta curta. O Agents SDK oferece `RunResult.last_agent` para dar continuidade ao especialista entre turnos. O rastreamento de traces não foi inspecionado diretamente aqui, então a análise da decisão da LLM é baseada nas respostas/logs fornecidos e no código.

## Alterações
- `SessionState` retém temporariamente `pending_agent` e `pending_question` quando especialista finaliza sem fonte. Históricos, turnos do usuário e respostas continuam sob gerenciamento do SDK; não há fallback conversacional.
- No próximo turno, `Runner.run` começa com o último especialista, preservando a sessão. Quando a consulta retorna fonte, libera o especialista; o próximo assunto começa pelo Orquestrador.
- A ferramenta Financeiro recebe a pergunta empresarial pendente e o complemento na variável `ExecutionContext.question` para validar que o plano respeitou os filtros originais. A mensagem enviada à LLM permanece exatamente como digitada; isto NÃO gera resposta nem classifica intenção.
- Se o usuário mudar de domínio enquanto há um esclarecimento aberto, os três especialistas possuem handoff nativo para o Orquestrador, que pode redistribuir o assunto.
- Instrução curta adicional no Financeiro: compreender resposta numérica como possível período quando este foi pedido, solicitar ano completo se inválido e preservar agrupamento por departamento.
- O smoke `scripts/check_redesign_sdk_http.py` agora exige consulta financeira final com ferramenta, fonte, ano e agrupamento. Não marca simples presença de texto como sucesso.
- Versão da aplicação v0.2.25.

## Segurança, limites e validação
- Não alterou `.env`, bases, contratos tipados do Financeiro, Dockerfile ou API key.
- Não gerou respostas locais ou fallback; respostas sempre da LLM após chamada OpenAI, salvo erro técnico.
- A ausência de `context.sources` é apenas sinal técnico de esclarecimento pendente, podendo também significar ausência definitiva de dados; o próximo turno ainda pode ser roteado ao Orquestrador pela LLM.
- `tool_choice='required'` segue ativo nos especialistas. A combinação de handoff de retorno e tool_choice deve ser validada com SDK real.
- Testes offline feitos com FakeRunner e SDK simulado: fluxo inicial, ano inválido, correção válida, alternância de assunto e janela de memória. Não confundir com execução real.
- É necessária validação no Docker do usuário, especialmente o novo assert de `2025` e a troca de assunto enquanto o especialista pede período.
