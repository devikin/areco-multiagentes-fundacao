# v0.2.12 — Correção de resposta fora de escopo

**Contexto:** o usuário conferiu o teste E003. A API devolveu `domain=fora_de_escopo`, mas a resposta incluiu fato externo sobre futebol. O teste E002 de esclarecimento foi adequado.

**Mudança:** reforçar instruções do Orquestrador e criar sanitização determinística do texto no serviço antes da resposta HTTP. A função `_orchestrator_response` ignora integralmente o texto livre depois de `FORA_DE_ESCOPO:` ou `SEGURANCA:`. Sem marcador, mantém resposta genérica ambígua.

**Escolha:** não usar um classificador paralelo nem reescrever orquestração. Preserva SDK-only e handoffs nativos.

**Testes:** 77 passaram, 1 ignorado (offline); simulação cobre vazamento factual, segurança, ambiguidades, serviço e instruções. Não foi feita uma execução real à OpenAI nesta etapa.

**Verificação pendente:** `python scripts/check_scope_sdk_http.py` com Uvicorn no Windows.
