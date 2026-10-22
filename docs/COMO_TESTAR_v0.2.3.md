> **ARQUIVO HISTÓRICO:** não descreve a arquitetura SDK-only v0.2.6. Consulte README.md.

# v0.2.3 — Aplicação rápida e teste

## Instalar no Windows
1. Pare o Uvicorn com CTRL+C.
2. Extraia o patch na **pasta-pai** `H:\Meu Drive\Desafio IA Areco`, mesclando o diretório `areco-multiagentes-fundacao` e substituindo `app/agents/internal.py`.
3. Não altere `.env`; confirme `OPENAI_API_KEY` e `USE_LLM_ANSWERS=true` já configurados.
4. Na pasta do projeto execute ` .\.venv\Scripts\python.exe -m pytest -q `. Depois rode ` .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload `. (Os espaços externos são apenas formatação.)

## Testar no chat
**Pergunta:** Como solicito férias?

**Esperado com LLM funcionando:**
- `classification_method=llm` (a não ser que haja falha técnica);
- `generation_method=llm_contexto` mesmo se a recuperação devolver uma FAQ;
- `generation_error=null`;
- `sources=["01_politica_ferias.md"]`;
- texto baseado nos documentos, mencionando o portal e 30 dias corridos.

**Esperado quando somente a geração falha:** `generation_method=faq_fallback` ou `extrativo_fallback`, com `generation_error` preenchido. Classificação pode continuar `llm`.

**Observações:** `USE_LLM_ANSWERS=false` e ausência de chave significam modo local escolhido por configuração, não falha técnica; Financeiro e Ouvidoria executam consultas determinísticas por segurança. Solicitações explícitas de senhas de terceiros podem ser bloqueadas por regra de segurança antes da LLM. Os testes locais usam mocks e não cobrem a rede Windows/OpenAI.
