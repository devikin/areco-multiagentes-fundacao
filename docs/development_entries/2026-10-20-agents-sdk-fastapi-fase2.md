# 20/10/2026 — Fase 2, integração opcional com FastAPI

**Pedido do usuário:** após enviar três prints de trace (Financeiro, Informações
Internas e Ouvidoria), solicitou avançar para a Fase 2.

**Evidência fornecida pelo usuário:** screenshots do painel OpenAI mostrando,
para cada domínio, orquestrador, `Handoff`, ferramenta e resposta. Não foram
copiados para o repositório por conterem elementos da conta do usuário.

**Decisão técnica da IA:** criar camada opt-in `AGENT_ENGINE=sdk`, mantendo
`legacy` como padrão e rollback imediato. Adotar Runner assíncrono dentro do
FastAPI; preservar contrato `/api/v1/chat` com campos adicionais opcionais;
reutilizar FinancePlan e execute_plan (SELECT parametrizado e Decimal),
recuperação BM25 existente e SQLite para Ouvidoria. Capturar fontes no contexto
local da execução, não pela resposta livre do modelo. Tracing nativo com
`trace_include_sensitive_data=False`.

**Arquivos criados:** app/sdk_integration/{__init__,tools,workflow,service}.py,
requirements-sdk.txt, scripts/check_sdk_http.py, testes específicos,
docs/COMO_TESTAR_SDK_FASE2.md e esta entrada.

**Arquivos alterados:** app/main.py, app/schemas.py, frontend/app.js,
.env.example, README.md, docs/DEVELOPMENT_LOG.md e AGENTS.md.

**Alternativas rejeitadas:** reescrever SQL e ingestão (risco desnecessário),
substituir código legado imediatamente, engolir erros do SDK como `200 OK`,
atribuir fontes com base somente no texto que a LLM gerou.

**Verificação local concluída:** Pytest em Linux sobre base v0.2.4 retornou
**57 aprovados, 1 ignorado**. O teste ignorado depende de pacote openai-agents
real, indisponível neste ambiente. Foram executados testes de SQL/Decimal,
BM25, Ouvidoria, contrato FastAPI com Runner simulado e regressão legado.
Aplicação do mesmo patch sobre base v0.2.3 também foi testada: 39 aprovados.
O Runner nativo REAL no FastAPI não foi exercitado aqui.

**Pendente:** instalar a versão da integração no Windows e executar
`scripts/check_sdk_http.py` contra a OpenAI real, confirmar 3 traces, Docker,
tratamento de indisponibilidade e perguntas adversariais. Não afirmar
que o SDK real foi testado neste runtime de desenvolvimento.
