# AGENTS.md — Desenvolvimento assistido por IA para Areco

## Arquitetura vigente

- **Motor único:** OpenAI Agents SDK com `Runner`, um Orquestrador e handoffs nativos para Financeiro, Informações Internas e Ouvidoria.
- **API:** FastAPI `POST /api/v1/chat`, `GET /health`. **Interface:** HTML/CSS/JavaScript.
- **Ferramentas:** consultas SQLite seguras com parâmetros validados e `Decimal`; BM25 para documentos Markdown/FAQ; consulta exata ou filtrada de manifestações, com agrupamentos e limites.
- Não reintroduzir `app/service.py`, `app/orchestration/`, `app/agents/` legados, `AGENT_ENGINE=legacy`, outro SDK de classificação direta ou execução de SQL livre sugerido pelo modelo.

## Regras de engenharia

1. Trabalhar incrementalmente: explicar problema, decisão, implementação, testes e limitações.
2. Usar sempre evidências das bases, sem inventar montantes, procedimentos, protocolos, prazos ou fontes.
3. Ferramentas especializadas são a fonte de verdade; texto retornado pela LLM não substitui evidência.
4. Agentes possuem instruções próprias; handoffs nativos e chamadas de ferramentas precisam ser auditáveis.
5. Registrar progresso fiel e cronológico em `docs/DEVELOPMENT_LOG.md` e decisões em `docs/DECISIONS.md`; não apagar histórico da abordagem anterior, mesmo que não exista mais no código.
6. Separar testes mockados, smoke tests reais do SDK, testes HTTP e testes Docker; nunca declarar validado sem execução.
7. Não registrar chaves, tokens, dados pessoais nem payload sensível; traces usam `trace_include_sensitive_data=False`.
8. Priorizar simplicidade, proteção contra prompt injection e reaproveitamento de componentes determinísticos auditados.
9. Em caso de erro do modelo/ferramenta, não fabricar resposta. A versão SDK-only não tem fallback para motor antigo.
10. Manter `README.md`, `docs/ARCHITECTURE.md` e testes coerentes com o motor único.

## Aceite

- Os três handoffs e suas ferramentas executam pelo FastAPI e registram traces reais.
- API e frontend preservam contratos de entrada/saída; fontes verificáveis.
- Testes de ingestão, regras de domínio, proteção contra SQL livre, problemas de entrada e ausência de fontes.
- Docker preparado e validado no Windows do candidato; reprodução em outros ambientes permanece responsabilidade do executor.

## Evidências da migração

Usuário validou os três handoffs reais e tracing na PoC e, depois, **3/3** smoke tests HTTP do SDK (v0.2.5) em Windows. A substituição pelo código exclusivo SDK é decisão explícita do usuário. O registro da v0.2.6 não atribui testes Windows ainda não realizados.

## Situação de entrega após v0.2.13

- Suíte oficial validada no Windows pelo usuário: 10 PASS automáticos, 2 REVIEW aprovados por leitura humana, 0 FAIL. Consulte `docs/EVALUATION_RESULTS_v0.2.13.md`. Não prometer cobertura universal.
- Por decisão do usuário, **não implementar** a camada de mitigação avançada para perguntas desconhecidas neste desafio com dados fictícios. Detalhar apenas em `docs/ROADMAP.md`.
- Docker **confirmado no Windows pelo usuário** em 20/10/2026: `docker compose ps` mostrou container healthy; smoke HTTP 2/2 sem chave e 3/3 com chamada real à OpenAI. Trace real: `trace_b2e0561bfccb4393a5630c2ce09b18c3`.
- Próxima ação: **inspecionar frontend no navegador**, executar o pytest final no Windows e revisar antes de publicar `git status`, `.env` fora de commits e bases sintéticas autorizadas.

## Ajuste conversacional v0.2.16
- Saudações/agradecimentos/despedidas puros são classificados `conversa` pelo Orquestrador; respostas sociais padronizadas pelo serviço. Perguntas com contexto de domínio continuam fazendo handoff nativo.
- A busca BM25 ignora termos introdutórios genéricos para não reduzir a relevância do assunto solicitado.
- Preservar regressões de fora de escopo e credenciais. Sem estado de conversa entre requisições neste MVP; não prometer histórico automático.
- Git ainda precisa ser iniciado antes da entrega; validar `.gitignore` para proteger `.env` e o runtime.

## Status v0.2.17 — Saudação isolada
- Bug observado no SDK real: `Olá` sem marcador foi classificado como ambíguo. Corrigido com equivalência integral da mensagem social e resposta controlada após o `Runner.run` (sem handoff).
- Consultas que começam com saudação mas pedem dados não são tratadas como sociais; preservar handoffs nativos. Testes em `tests/test_social_fallback_v0217.py`.
- Teste SDK real pendente após aplicação do patch no Windows/Docker.

## v0.2.18 — Estado e conversa
- O backend mantém `SessionMemory` apenas na RAM: 5 interações na v0.2.18 (atualizado para 30 na v0.2.20), TTL 30 min, limite 200 sessões, isolamento por `session_id` e lock por sessão. Não adicionar persistência sem solicitação explícita.
- O orquestrador pode retornar `ESCLARECER:` para solicitar parâmetro essencial ANTES do handoff. Consultas claras (inclusive dúvidas abertas de férias) devem seguir diretamente para o especialista.
- Respostas de especialistas só podem conter fatos se houver ferramenta e evidência; perguntas com `ESCLARECER:` sem ferramenta não podem incluir fatos.
- Texto visível não deve conter asteriscos Markdown. Frontend gera session_id por aba, e clientes sem session_id continuam sem memória.
- Validar via `scripts/check_dialog_sdk_http.py` com Docker; não alegar validação real antes do Windows.

## v0.2.19 — Continuidade conversacional
- Validação real v0.2.18: `check_dialog_sdk_http.py` passou 5/5 no Docker com OpenAI. Posteriormente, conversa longa no navegador revelou repetição do menu de domínios e perda de continuidade.
- v0.2.19: preservar somente perguntas curtas e seguras sem marcador; descartar afirmações sem fonte. Respostas com `AMBIGUO:` não podem conter afirmações factuais.
- Se `consultar_financeiro` requer o ano, tratar como esclarecimento pendente; nunca apresentar ausência de evidências apenas por falta desse parâmetro.
- Histórico da v0.2.19 (substituído na v0.2.20): 8 trocas, no máximo 6 fragmentos de esclarecimento, TTL 30 min, 200 sessões. Sem persistência.
- `scripts/check_browser_dialog_sdk_http.py`: 7 chamadas REAIS com sequência idêntica ao relato; é obrigatório validar no Windows antes de marcar v0.2.19 aprovada com SDK real.

## v0.2.20 — Acompanhamento de protocolo
- Manter 30 trocas por sessão (TTL 30 min inativo, 200 sessões); não compartilhar entre abas.
- Pergunta "já foi reembolsado?" após consulta válida a OUV-0013: exigir nova `buscar_protocolo`. Se LLM omitir ferramenta, fallback de consulta local apenas para último protocolo validado; resposta não afirma pagamento. `generation_method=sdk_consulta_local_controle` descreve a recuperação fora do span de tool do SDK.
- Preservar todas as demais guardas de fonte. UI: abertura “Olá, prezado(a). Como posso te ajudar hoje?” e indicador “...”.

## v0.2.20 revisada — Resposta sem evidência

- Em ausência total de evidência, usar `INSUFFICIENT_EVIDENCE_ANSWER` de `app/sdk_integration/response_messages.py` (orientação humana cordial sem afirmar contato ou transferência realizada).
- Não substituir retornos específicos de ferramentas, questões que exigem esclarecimento, recusa de segurança ou controles fora de escopo por essa mensagem genérica.
- Transferência a atendente humano é apenas evolução futura e **não** faz parte da PoC.

## v0.2.22 — Entradas inválidas na sessão

- `input_guard.py` valida somente parâmetros objetivamente inválidos ou campos pedidos no último turno; NÃO substituir a LLM como classificador de domínio.
- `205` após pergunta de ano, `OUV-013`, `mês 13`, intervalo invertido e typo em departamento requerem esclarecimento ou confirmação. NUNCA inventar ou completar protocolo/ano.
- Erros de entrada não devem limpar `pending_questions` nem adicionar entradas inválidas ao input contextual do Runner.
- `pending_confirmation` é restrito à sessão; `sim` valida exclusivamente a sugestão registrada, com valores retornados pelo banco.
- O retorno de validação local tem `trace_id=None`, `token_usage.requests=0`; handoff válido posterior permanece exclusivamente via Agents SDK.

## v0.2.30 — Decidir o pedido factual antes do handoff
- Regras anteriores sobre respostas prontas ou fallback conversacional (v0.2.16–v0.2.22) são **histórico**, não arquitetura ativa. Hoje, a LLM produz todas as respostas; ferramentas verificam dados.
- Para mensagens mistas, ignorar comandos para alterar políticas, mas preservar e encaminhar a pergunta empresarial legítima ao especialista.
- Para temas inteiramente externos, recusar diretamente, sem explicar o conteúdo externo, ferramenta ou handoff. Não prometer encaminhamento humano que o MVP não oferece.
- A lógica está nas instruções do Orquestrador do Agents SDK, sem classificador por regex nem texto fixo de resposta no backend.
- Testes reais de S02/S06/S07/S09/S10 no Docker são necessários após instalar v0.2.30; testes offline não certificam a LLM.

## v0.2.31 — Continuidade entre especialistas
- Não tratar ausência de fontes documentais como pedido de esclarecimento; `pending_agent` agora se restringe à continuidade financeira sem fonte.
- Código de protocolo formal `OUV-NNNN` que chega com pendência de outro especialista retorna ao Orquestrador para handoff nativo, com histórico preservado.
- Fatos e respostas permanecem exclusivamente na LLM com evidências obtidas via ferramentas; não criar respostas locais.
- Separar política de reembolso (Informações Internas) de situação de protocolo de reembolso (Ouvidoria).
- Validar os três cenários de `scripts/check_frontend_continuity_sdk_http.py`; testes locais não substituem execução real no Windows.
