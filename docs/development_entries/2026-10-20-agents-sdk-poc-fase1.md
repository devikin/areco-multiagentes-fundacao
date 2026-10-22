# 2026-10-20 — PoC isolada do OpenAI Agents SDK (fase 1)

## Solicitação
Migrar a arquitetura por partes: primeiro provar handoffs nativos e tracing,
sem comprometer a v0.2.4 validada anteriormente.

## Proposta técnica produzida com ajuda de IA
- PoC isolada em `poc_agents_sdk/` (sem tocar em `app/main.py`, `app/service.py`).
- Ambiente virtual SEPARADO em `%LOCALAPPDATA%` para não alterar o `.venv` atual.
- 1 orquestrador `Agent` + 3 especialistas `Agent`; `handoff(...)` nativo.
- 3 ferramentas de leitura sintética, usadas como adaptadores temporários.
- Execução por `Runner.run_sync`; auditoria pelos `new_items` (handoff/tool calls).
- Tracing ativo com `trace_include_sensitive_data=False`.
- Plano para futura adaptação das ferramentas existentes sem reescrever SQL.

## Decisão/estado
A proposta foi implementada somente na PoC local. Aprovação do usuário e
validação na API real ainda pendentes. Não substituir o serviço atual nesta fase.

## Evidências
- Ver testes locais em `tests/test_sdk_poc_tools.py` e
  `tests/test_sdk_poc_contract.py`.
- A instalação `openai-agents` não foi possível no ambiente de desenvolvimento
  desta sessão por indisponibilidade de rede. Portanto **nenhum handoff real
  foi executado aqui**. Necessária verificação com o SDK no Windows do usuário.

## Riscos e mitigação
- SDK não instalado: testes de montagem reais dependem da instalação na máquina.
- Custo e latência: `Runner` faz múltiplas chamadas por handoff/ferramenta.
- Privacidade: não registrar entradas/saídas brutas em spans de tracing.
- Limite funcional da PoC: ferramentas simples sobre CSV/Markdown; migração das
  ferramentas SQL/BM25 atuais somente na fase 2.
