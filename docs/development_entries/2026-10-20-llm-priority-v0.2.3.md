# Entrada de desenvolvimento — v0.2.3 — Prioridade LLM nos agentes

Data: 20/10/2026. Continuação cronológica do projeto; registrar no diário principal na próxima consolidação, preservando quaisquer edições locais.

## Evidência observada no ambiente do usuário
- O usuário executou uma pergunta sobre aprovações para compra de R$ 12.000 e forneceu screenshot da interface e log do terminal.
- Log real informado: `classification_method="llm"`, `generation_method="llm_contexto"`, `classification_error=null`, `generation_error=null`, fontes `03_aprovacao_de_compras.md`, resposta HTTP 200, latência observada `179848 ms` (aproximadamente 3 minutos).
- A resposta foi considerada correta pelo usuário. Não inferir que esta latência representa a performance típica.
- Decisão explícita do usuário: **usar fallback apenas quando a LLM falhar** e seguir com o desenvolvimento dos agentes.

## Problema inspecionado
- Na v0.2.2, `InternalAgent.respond()` retornava um texto de FAQ ANTES de tentar `LLMAdapter.complete`. Assim, mesmo com IA configurada e disponível, o especialista às vezes usava `generation_method=faq_extrativa` sem falha da IA. Esse comportamento não correspondia à prioridade LLM solicitada.

## Decisão técnica e alteração proposta pela IA
- Com `OPENAI_API_KEY` presente e `USE_LLM_ANSWERS=true`, o agente interno chama a LLM primeiro com o trecho recuperado e citação. A FAQ é evidência, nunca atalho para evitar IA.
- Se a LLM falhar por exceção ou devolver conteúdo vazio, usar resposta direta da FAQ, rotulada `faq_fallback`, ou extração, rotulada `extrativo_fallback`, e registrar `generation_error` seguro.
- Em modo offline ou com geração de IA explicitamente desabilitada, responder por extração local SEM rotular falsamente como fallback.
- **Roteamento já cumpria a regra**: LLM classifica primeiro quando está configurada, e `regras_fallback` só ocorre após exceção/saída inválida. Classificação de baixa confiança/ambígua válida continua `method=llm`.
- **Exceção deliberada de segurança**: perguntas explícitas solicitando credenciais de terceiros podem ser bloqueadas localmente antes do provedor, por minimização de dados e proteção. Isso é um guardrail, não é fallback.
- **Financeiro e Ouvidoria**: SQL/Decimal e protocolo exato são ferramentas de consulta e cálculo, não fallback; continuam determinísticos por integridade numérica. A extensão destes especialistas com interpretação de comandos via LLM terá fase própria e validação de plano estruturado.

## Alterações realizadas
- `app/agents/internal.py`: inversão do atalho de FAQ e a chamada à LLM; novos estados `faq_fallback`/`EmptyLLMResponse`.
- `tests/test_llm_priority.py`: sete novos cenários sem chamadas reais ao provedor.
- Este registro e guia rápido. Sem alteração de `.env`, consultas SQL, configuração Docker ou fonte de dados.

## Evidência de teste do ambiente do assistente
- Execução em Linux/Python 3.13.5: `python -m pytest -q --disable-warnings --maxfail=1` => **27 passed in 1.11s** (20 regressões antigas + 7 novas).
- Novos testes: FAQ com LLM bem-sucedida; FAQ com erro e fallback; saída vazia e fallback; LLM ambígua válida sem fallback; saída JSON inválida no classificador e fallback; modo offline explícito; integridade dos agentes tabulares.
- Chamada real à OpenAI **não executada nesta etapa**; testes de LLM foram simulados. Compatibilidade desta correção no Windows **ainda precisa de confirmação do usuário**.

## Próximas ações propostas, ainda não implementadas
1. Testar pergunta de FAQ com LLM no Windows: `Como solicito férias?`, verificar `classification_method=llm`, `generation_method=llm_contexto`, erros null, e fonte da política.
2. Evoluir o **Financeiro** com plano estruturado de intenção/consulta e SQL parametrizado, sem SQL gerado livremente pelo modelo; manter Decimal e fontes.
3. Evoluir **Ouvidoria** com filtros validados e consultas exatas ao banco; sem inventar status/protocolos.
4. Aperfeiçoar **Informações Internas** com múltiplos trechos e fontes, preservando citações e regras anti-alucinação.
5. Investigar latência de aproximadamente 180s: confirmar na prática os limites por etapa, sem assumir diagnóstico apenas do log.
