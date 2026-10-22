# Consolidação — Agents SDK-only (v0.2.6)

- **Pedido do usuário:** após validar 3/3 requisições FastAPI com handoff real e traces na OpenAI, manter apenas a nova arquitetura Agents SDK e remover a anterior.
- **Decisão técnica:** manter os contratos HTTP, ferramentas SQLite/Decimal, BM25, bases e frontend; remover `app/service.py`, `app/orchestration/`, `app/agents/`, `app/services/` e testes legados.
- **Implementação:** `app/main.py` instancia somente `SdkChatService`; motor financeiro compartilhado foi movido para `app/sdk_integration/finance_queries.py`; dependência `openai-agents` está em `requirements.txt`.
- **Segurança:** scripts de migração criam backup e preservam `.env`, `.git` e bases. Tracing reduz inputs/outputs sensíveis via `trace_include_sensitive_data=False`, mas saídas de ferramentas podem aparecer no painel; manter somente material sintético.
- **Testes:** 27 testes offline aprovados, 1 teste de SDK real ignorado por biblioteca ausente no ambiente local do assistente. A execução real em Windows pós-limpeza **ainda precisa ser comprovada**.
- **Rollback:** backup na pasta irmã externa ao projeto, criado pelo script de migração. Não apagar até repetir 3/3 smoke tests HTTP.
