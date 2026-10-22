# v0.2.19 — Continuidade e esclarecimento no Orquestrador

Data: 20/10/2026 (reprodução de conversa no navegador e investigação incremental).

## Evidências apresentadas pelo usuário
- Smoke real da v0.2.18 no Docker: 5/5 PASS, incluindo `Olá`, esclarecimento de despesas, `O total de 2025`, férias e fora de escopo; traces registrados pelo usuário.
- Conversa longa falhou: `queria tirar uma duvida`, `certo..tenho outra duvida`, `sobre despesas`, `departamento` e `despesas por departamento` desencadearam respostas genéricas `Você quer consultar Financeiro, Informações Internas ou Ouvidoria?` repetidas.
- O usuário suspeitou da memória curta. Investigação do código indicou causa primária no fallback `_orchestrator_response`, que descartava perguntas não marcadas, e outro problema no descarte de consulta pendente quando a ferramenta requisitava ano.

## Correção
- `service.py`: validação conservadora da forma de pergunta antes de aceitar esclarecimentos do LLM sem marcador; afirmações factuais ainda bloqueadas. Filtrar menus genéricos mesmo com marcador `AMBIGUO`/`ESCLARECER`.
- `service.py`: quando `consultar_financeiro` confirma que falta ano, retorno natural como `esclarecimento` e manutenção da intenção na sessão; não permitir fatos sem fonte.
- `session_memory.py`: oito interações e até seis fragmentos de pedido pendente; persistência, banco e autenticação não alterados.
- `workflow.py`: exemplos concisos de intenção incompleta e acompanhamento `departamento` → ano, sempre priorizando handoff quando pedido completo.
- Teste regressivo: `tests/test_browser_regression_v0219.py` simula a mesma sequência, regras anti-vazamento, ferramenta sem ano e isolamento de sessões.
- Smoke real novo: `scripts/check_browser_dialog_sdk_http.py` executa sete turnos no mesmo `session_id`; espera handoff documental e agrupamento por departamento.

## Limitações
- O Runner foi simulado na regressão local. Modelos reais ainda podem produzir desvios probabilísticos.
- Não se trata de memória persistente: reinício do container ou refresh da aba cria conversa nova.
- `max_turns=8` do Agents SDK se refere às etapas de execução interna de cada chamada; não limita a oito mensagens da sessão.
- Caso o modelo não mantenha a intenção na validação real, coletar domínio/resposta/trace e corrigir de maneira direcionada, sem modificar base sintética nem remover proteção contra alucinações.
