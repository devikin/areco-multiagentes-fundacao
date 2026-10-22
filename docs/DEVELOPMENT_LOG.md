# Diário de desenvolvimento assistido por IA

> Registro contínuo. Não reconstruir retrospectivamente conversas, testes ou decisões. Atualizar após cada etapa efetiva.

## Entrada 001 — 20/10/2026 — Análise inicial e preparação documental
- **Contexto:** desafio técnico de Analista de IA da Areco, com orquestrador e agentes Financeiro, Informações Internas e Ouvidoria.
- **Solicitação original:** adotar os papéis e seguir as instruções do prompt anexado pelo usuário nesta conversa.
- **Prompt preservado:** `docs/ai_interactions/2026-10-20-prompt-inicial.txt` (cópia textual do anexo fornecido; não é transcrição de todo o chat).
- **Proposta da IA:** arquitetura modular sem framework de agentes na versão inicial; FastAPI/Pydantic; classificação tipada; recuperadores segregados; fontes verificáveis; testes com mocks e arquivos reais; Docker.
- **Alternativas consideradas:** LangChain, LangGraph, CrewAI, busca vetorial hospedada, BM25, dados estruturados. Escolhas de recuperação e modelo são provisórias enquanto não há anexos de conhecimento.
- **Justificativa:** limite de três dias úteis e necessidade de demonstrar handover, grounding, rastreabilidade e qualidade.
- **Artefatos criados nesta etapa:** `AGENTS.md`, `README.md`, `.env.example`, `.gitignore`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/PLAN.md`, `docs/TEST_PLAN.md`, `docs/AI_USAGE.md`, este diário e diretórios vazios de conhecimento.
- **Estado de decisão:** proposta técnica da IA; ainda não houve confirmação humana individual de opções de modelagem.
- **Implementação de aplicação:** não iniciada.
- **Testes funcionais/Docker:** não executados.
- **Validação de artefatos:** presença e leitura dos arquivos locais podem ser verificadas por inspeção do pacote. Isso **não** valida o aplicativo.
- **Bloqueios:** bases da Areco não disponíveis; enunciado completo e eventuais restrições de API/compartilhamento não foram inspecionados.
- **Próxima ação:** receber e inventariar as bases, classificar formatos/domínios e escolher abordagem de recuperação antes de escrever o código dos agentes.

## Entrada 002 — 20/10/2026 — Acesso ao Drive e análise inicial das bases
- **Solicitação do usuário:** respostas futuras concisas; consultar os anexos na pasta de Meu Drive que corresponde a `H:\Meu Drive\Desafio IA Areco` no computador dele.
- **Ação efetivamente realizada:** localização de pasta `Desafio IA Areco` no Google Drive conectado; listagem de pastas/arquivos; leitura do manifesto, dicionário de dados, instruções de ingestão, SQL, regras financeiras/ouvidoria, FAQ, perguntas de avaliação, uma política Markdown e amostras de cabeçalhos/linhas CSV.
- **Resultados observados:** três domínios com CSV, JSON e Markdown; dados sintéticos; esquema PostgreSQL fornecido; conjunto de 12 perguntas de avaliação; totais declarados de 300 lançamentos, 144 orçamentos, 180 manifestações, 10 documentos internos e 7 FAQ. Contagens declaradas não validadas por ingestão automática.
- **Proposta da IA:** recuperação híbrida por domínio: operações estruturadas e determinísticas para Financeiro e Ouvidoria; RAG leve com fontes para Informações Internas; roteamento tipado.
- **Justificativa:** tipos de dados distintos requerem estratégias distintas, sobretudo para valores exatos e identificadores.
- **Artefato criado:** `docs/KNOWLEDGE_AUDIT.md`; este diário atualizado.
- **Decisões do usuário:** preferência por concisão e fonte dos anexos; stack complementar e persistência ainda sujeitas à implementação e validação.
- **Testes:** nenhum teste funcional, Docker ou de integração executado nesta etapa; apenas inspeção documental.
- **Próxima ação:** preparar ingestão reproduzível, implementar contratos do orquestrador e testar casos fornecidos.

## Modelo para próxima entrada
- Data / etapa / objetivo:
- Prompt ou referência da conversa:
- Sugestão da IA:
- Decisão do usuário (quando houver):
- Alternativas e justificativas:
- Arquivos efetivamente criados/alterados:
- Comandos/testes realmente executados e saídas:
- Bugs, erros e correções:
- Limitações, riscos e próximo passo:


## Entrada 003 — 20/10/2026 — Ingestão, agentes, API, frontend e testes locais
- **Pedido do usuário:** “vamos avançar” após pactuarmos analisar a ingestão e contratos do orquestrador. Preferência por respostas curtas mantida.
- **Ação observada da IA:** consultou arquivos reais do Google Drive, obteve cópias binárias, revisou políticas/FAQs/dicionário, implementou código da API, classes de agentes, orquestrador, adapter LLM, consultas estruturadas, BM25, frontend, Dockerfile/Compose, configuração e testes. A escolha de SQLite foi **proposta e aplicada pela IA** para o MVP, sem atribuir ao usuário uma decisão que não foi formalmente dada.
- **Arquivos criados/atualizados:** `app/`, `frontend/`, `tests/`, `requirements*.txt`, `Dockerfile`, `compose.yaml`, `.dockerignore`, `data/knowledge/` com anexos sintéticos, `data/reference/` com documentação e testes de origem, `.env.example`, `README.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/KNOWLEDGE_AUDIT.md`, `docs/TEST_PLAN.md`, `docs/SOURCE_MANIFEST.md`, `AGENTS.md` e este registro.
- **Contagens verificadas dos arquivos:** 300 lançamentos financeiros, 144 orçamentos, 180 manifestações, 10 Markdown e 7 itens FAQ; a ingestão gravou 17 chunks textuais.
- **Testes realmente executados:** `python -m pytest -q` passou inicialmente 7, depois 9, e na execução mais recente **10 passed in 0.47s**. Um teste percorreu as 12 perguntas entregues pela Areco, verificando domínio/fonte/resposta não vazia; testes adicionais cobriram valores exatos, recuperação, segurança, falha simulada de provedor, API, ausência de bases e formato de input.
- **Validação HTTP real:** Uvicorn iniciado em 127.0.0.1:8439; `GET /health` retornou HTTP 200 e três agentes. `POST /api/v1/chat` para `OUV-0002` retornou HTTP 200, `ouvidoria`, status `Aguardando área responsável` e `manifestacoes.csv`, com request_id e log JSON. Os testes foram executados novamente após introdução de adapter LLM.
- **Bugs identificados/corrigidos:** (1) detecção de `maio` dentro da palavra `maior` fazia orçamento de janeiro abranger janeiro–maio; corrigida com limites de palavra e teste do valor exato de janeiro. (2) buscas de FAQ devolviam a pergunta da FAQ em vez da resposta; corrigida seleção da resposta, com testes de prazo e férias.
- **Validações NÃO realizadas:** Docker/Compose não disponível no ambiente; integração OpenAI real não chamada por ausência de chave; frontend não inspecionado num navegador interativo; compatibilidade Windows não executada; modelos e custos não medidos.
- **Riscos/limites:** modo offline não é inferência LLM; roteamento heurístico e perguntas financeiras abertas têm escopo limitado; contexto multi-turnos não persistido; sem autenticação, não publicar publicamente. Bases sintéticas incluídas no ZIP para demonstração; confirmar permissão antes de publicar no GitHub.
- **Próxima prioridade:** testar em Windows com Docker e uma chave autorizada; expandir a matriz de perguntas adversariais e técnicas de grounding; preparar repositório privado e checklist de avaliação.
- **Histórico integral:** esta entrada é resumo honesto do trabalho, não transcrição do histórico completo da conversa. Preservar/exportar as interações originais quando possível.

## Entrada 004 — 20/10/2026 — Correção de inicialização SQLite no Windows
- **Problema real reportado pelo usuário:** Uvicorn falhou no startup com `WinError 32` ao fazer `temporary.replace(database_path)` em `H:\Meu Drive\Desafio IA Areco\...\knowledge.sqlite.building`, seguido de erro também no cleanup de `.building`.
- **Diagnóstico via código:** `with sqlite3.connect(...)` gerenciava somente transação; a conexão não era explicitamente fechada antes de `Path.replace`. Além disso, o banco temporário residia numa pasta sincronizada pelo Drive, sujeita a bloqueios externos.
- **Decisão técnica da IA:** usar `contextlib.closing` juntamente com context manager transacional; escolher `%LOCALAPPDATA%/ArecoMultiagentes/knowledge.sqlite` como padrão Windows; preservar override `DATABASE_PATH` via `.env`; não mascarar a exceção original se remoção do arquivo de build falhar.
- **Arquivos alterados:** `app/knowledge/ingest.py`, `app/main.py`, `.env.example`, `README.md`, `tests/test_ingest.py`, `tests/test_api.py`, `docs/DEVELOPMENT_LOG.md`, `docs/DECISIONS.md`.
- **Evidência real neste ambiente (Linux):** `PYTHONPATH=/opt/pyvenv/lib/python3.13/site-packages python -S -m pytest -q -p no:cacheprovider` => **14 passed in 0.86s**. Regressão adicionada verificou fechamento antes de `Path.replace`, duas ingestões seguidas e localização padrão de banco no Windows. Uvicorn v0.2.1 iniciou e `GET /health`, `GET /`, `POST /api/v1/chat` responderam HTTP 200; consulta ao protocolo OUV-0002 retornou `Aguardando área responsável`. O teste final no Windows do usuário continua pendente.
- **Próximo passo:** descompactar versão corrigida; testar `uvicorn --reload` no Windows; validar `/health` e uma pergunta do chat.

## Entrada 005 — 20/10/2026 — Agente Financeiro com planejamento LLM e ferramentas SQL seguras (v0.2.4)
- **Pedido do usuário:** “avance” após aprovação da prioridade da LLM e do fallback restrito a falhas.
- **Proposta/implementação da IA:** manter a v0.2.3 e acrescentar uma etapa de planejamento via LLM no agente Financeiro: resposta JSON tipada por Pydantic (`FinancePlan`) para escolher conjunto de dados, operação, ano, intervalo, agrupamento e filtros. Somente o código Python monta SELECTs parametrizados e calcula valores com `Decimal`; nenhum SQL do modelo é executado.
- **Alternativas rejeitadas:** permitir SQL livre gerado por LLM (risco de segurança e inexatidão); delegar somas ao LLM (inconsistência numérica); substituir o modo offline validado (risco de regressão).
- **Arquivos de aplicação alterados:** `app/agents/finance.py` (envoltório do planejador, modo local e fallback), `app/agents/finance_tools.py` (novo contrato e executor); criados `tests/test_finance_llm_tools.py`, `docs/COMO_TESTAR_v0.2.4.md` e este registro.
- **Tratamento de falhas:** erro ou JSON/plano inválido do LLM -> `deterministico_fallback` e código do erro; solicitação sem ano/fora das operações suportadas -> esclarecimento, sem fallback; erros reais de banco/SQL propagam sem fallback. Com LLM desativada, comportamento v0.2.3 permanece.
- **Verificação real:** `PYTHONPATH=. python -m pytest -q -p no:cacheprovider` retornou **45 passed** em Linux, incluindo 27 testes anteriores, 17 novos testes de ferramenta e um teste HTTP adicional. Incluídos casos de total financeiro, agrupamento, orçamento, filtros, ausência de dados, ano desconhecido, proteção SQL, divergência de status e falha simulada do provedor.
- **Limitações:** LLM de planejamento foi SIMULADA nos testes, sem chamada à OpenAI real; não houve teste no Windows/Docker nesta etapa. Planejador suporta somas, contagens, agrupamentos e maior soma por grupo de um único ano, não percentuais, comparações intertabelas ou SQL livre. Agrupamentos são somas, não contagens agrupadas.
- **Validação humana pendente:** aplicar patch v0.2.4 sobre v0.2.3 e conferir o novo fluxo na API real; depois avançar com consultas flexíveis na Ouvidoria.
- **Histórico original:** solicitação e devolutivas estão neste chat; esta entrada é resumo, não transcrição completa.


## Entrada 006 — 20/10/2026 — Integração Agents SDK / FastAPI (Fase 2)
- O usuário apresentou 3 traces reais da PoC e autorizou a Fase 2.
- Decisão da IA: motor SDK opcional via `AGENT_ENGINE=sdk`, preservando `legacy` como padrão e rollback sem mudança de banco.
- Camada em `app/sdk_integration`, handoffs nativos, fontes registradas por ferramentas, traces sem payload sensível, contrato HTTP compatível.
- O motor financeiro reutiliza FinancePlan/execute_plan; cálculos permanecem determinísticos.
- Evidências detalhadas, testes e pendências: `docs/development_entries/2026-10-20-agents-sdk-fastapi-fase2.md`.
- Teste real no Windows do novo endpoint FastAPI é **pendente**; os 3 traces recebidos cobrem apenas a PoC da Fase 1.

## Entrada 007 — 20/10/2026 — Consolidação em Agents SDK-only (v0.2.6)
- **Evidência enviada pelo usuário:** resultado 3/3 smoke tests FastAPI no Windows (Informações Internas, Financeiro e Ouvidoria), com IDs de trace; usuário solicitou eliminar a implementação antiga.
- **Decisão humana:** manter somente OpenAI Agents SDK.
- **Ação da IA:** preparar código consolidado; remover módulos legados de orquestração/serviços/agentes, preservar consultas monetárias com Decimal movendo-as para componente SDK, atualizar dependencies, Dockerfile (via requirements), startup, documentação e testes. Preparar migração com cópia de segurança para preservar .env e .git.
- **Motivo:** reduzir duplicidade de lógica e explicar melhor a arquitetura durante a avaliação.
- **Limitação:** código resultante inicialmente validado por testes offline, não por chamada real pós-limpeza; Docker não validado. Traces anteriores evidenciam a Fase 2 antes da limpeza.
- **Histórico:** entradas anteriores registram etapas legadas de forma fiel e são mantidas como auditoria, não como código vigente.

## Entrada 008 — 20/10/2026 — Ouvidoria avançada no Agents SDK (v0.2.7)
- **Pedido e contexto:** usuário declarou “validado 100%” a migração SDK-only; seguimos ao incremento de ferramentas de Ouvidoria prometido. A confirmação Windows é do usuário; ele não enviou novo log técnico nesta mensagem.
- **Solução da IA:** adicionar plano estrito Pydantic para filtros por status, prioridade, categoria, canal, área e datas, além de contagem/agrupamento/listagem, preservando ferramenta de protocolo exato.
- **Decisão técnica:** LLM decide o plano, código constrói somente SQL SELECT parametrizado. Nenhum banco, frontend, handoff ou rota da API alterado. Limite de 10 protocolos e validação de filtros explícitos.
- **Implementado:** `ouvidoria_queries.py`, atualização de `tools.py`/`workflow.py`, testes offline, novo smoke HTTP e documentação.
- **Testes observados:** `python -m pytest -q` => 41 passed, 1 skipped (SDK real indisponível no assistente); consultas reais ao SQLite sintético validaram 38 Alta e 79 Média, 55 Baixa, 38 Alta, 8 Crítica na distribuição. **Não houve teste OpenAI ao vivo desta extensão**.
- **Limitações:** datas relativas solicitam período explícito; não há edição de protocolos, autenticação, estado conversacional nem Docker validado. A LLM ainda pode selecionar parâmetros inadequados que exigirão avaliação pelo usuário.
- **Próximo passo:** testar SDK real no Windows e registrar logs/traces sem segredos.


## Entrada 009 — 20/10/2026 — Ajuste seleção de ferramentas da Ouvidoria (v0.2.8)
- **Evidência do usuário:** após instalar v0.2.7 no Windows, `check_sdk_http.py` retornou 3/3 handoffs; `check_ouvidoria_sdk_http.py` falhou no primeiro caso. Para a pergunta “Quantas manifestações de prioridade Alta existem?”, a LLM acionou `contar_manifestacoes` em vez de `consultar_manifestacoes`. Resposta incorreta: 180 (total geral), enquanto a base registra 38 de prioridade Alta. Log incluía `tools_used: ["contar_manifestacoes"]`, domínio Ouvidoria e trace real.
- **Diagnóstico da IA:** sobreposição de ferramentas; `contar_manifestacoes` nunca aceita filtros e, escolhida indevidamente, compromete a resposta mesmo com handoff correto e HTTP 200.
- **Proposta e implementação pela IA:** expor apenas `consultar_manifestacoes` para *todas* as contagens, agrupamentos e listagens; manter `buscar_protocolo` e `listar_status_ouvidoria` para suas funções próprias. Remover função redundante e alterar instruções do agente. Adicionar validação de agrupamento pedido na pergunta (por prioridade/status/etc.) antes do SQL, evitando devolver total geral como resposta a distribuição.
- **Testes executados localmente:** `python -m pytest -q` em v0.2.8 retornou **45 passed, 1 skipped** (SDK real indisponível no ambiente de desenvolvimento); inclui total geral, filtro Alta=38, distribuição exata e rejeição de plano que ignora agrupamento. Nenhuma chamada real à OpenAI foi feita nesta correção.
- **Próximo passo humano:** aplicar patch sem alterar `.env`; reiniciar Uvicorn, executar smoke 3/3 e o smoke da Ouvidoria; compartilhar saída e traces. **Não marcar v0.2.8 validada em Windows até evidência.**

## Entrada 010 — 20/10/2026 — RAG documental v0.2.9
- **Contexto:** após validação humana dos 3/3 handoffs e de duas consultas avançadas da Ouvidoria v0.2.8, iniciamos melhorias de Informações Internas.
- **Solução aplicada pela IA:** deduplicação por documento principal, ranking BM25 local com aliases controlados e cortes de relevância, recuperação de política integral, rastreio de versão por fonte e prompt de geração mais estrito.
- **Verificações executadas:** `python -m pytest -q -p no:cacheprovider` => 61 passed, 1 skipped, offline. Um teste de senha inicialmente esperava zero fontes e foi corrigido porque retornar a política de segurança é apropriado para orientar uma recusa; nenhuma chave nem dado pessoal foi extraído.
- **Testes pendentes:** chamadas reais à OpenAI em Windows na versão v0.2.9; Docker.
- **Evidências detalhadas, trade-offs e próximos passos:** `docs/development_entries/2026-10-20-rag-internas-v0.2.9.md`.

## Entrada 011 — 20/10/2026 — Falha de roteamento de trabalho remoto (v0.2.10)
- **Evidência real enviada pelo usuário:** após o patch documental v0.2.9, `check_sdk_http.py` confirmou 3/3 handoffs; `check_internas_sdk_http.py` passou o primeiro caso de férias, mas falhou na pergunta **“Posso trabalhar de casa?”**. A API respondeu `domain=ambiguo`, `agent=None`, `handoffs=[]`, `tools_used=[]`; portanto, a consulta nem chegou ao RAG. Não há evidência de falha do recuperador documental nesta execução.
- **Hipótese da IA:** instruções do orquestrador não exemplificavam home office e o modelo confundiu uma dúvida de elegibilidade individual (que requer política e limites) com ausência de domínio. Como o modelo é probabilístico, um caso falho não demonstra taxa de erro geral.
- **Alteração implementada:** reforçar o roteamento **pelo assunto** com exemplos de home office/trabalho remoto e esclarecer que é o especialista quem verifica evidências e limites de elegibilidade. Atualizar `handoff_description` de Informações Internas e instrução de não afirmar permissão individual sem fundamento. Preservados os marcadores `AMBIGUO:`, `FORA_DE_ESCOPO:`, `SEGURANCA:` e os três handoffs nativos.
- **Arquivos:** `app/sdk_integration/workflow.py`, `tests/test_orchestrator_policy_v0210.py`, README e registro cronológico.
- **Limites da validação:** testes estáticos verificam as instruções e testes de recuperação verificam o documento correto; **não comprovam a classificação de uma LLM real**. Smoke test da v0.2.10 no Windows ainda pendente. Não houve mudança de banco, frontend, FastAPI nem SDK Runner.
- **Próximo passo:** executar smoke `check_internas_sdk_http.py` no Windows com OpenAI real e confirmar handoff + `buscar_documentos` + `06_politica_home_office.md` para “Posso trabalhar de casa?”.

## Entrada 012 — 20/10/2026 — Evidências reais da avaliação oficial v0.2.13
- **Usuário validou no Windows:** repetição seletiva de T002/T003/T004/T008/T012 retornou 5 PASS; suíte oficial completa `--suite official --include-answers` retornou **10 PASS, 2 REVIEW, 0 FAIL**. Os 12 POSTs no log FastAPI retornaram HTTP 200, com fontes/handoffs/tools e traces.
- **Revisão semântica dos dois REVIEW:** T007 respondeu Tecnologia, R$ 43.229,05, fonte `orcamento_mensal.csv`; T010 recusou credenciais. Ambos revisados com respostas do JSON `docs/evidence/quality_official_20261020T232441Z.json` acessível via Drive conectado.
- **Limitação:** 12 casos conhecidos com dados sintéticos, não cobertura universal. Docker ainda não foi executado; não transferir validade do Windows/Uvicorn para container.

## Entrada 013 — 20/10/2026 — Decisão de escopo e preparação de entrega (v0.2.14)
- **Decisão humana:** registrar no roadmap proteções avançadas para perguntas desconhecidas, sem implementá-las no desafio fictício.
- **Ação proposta e realizada pela IA:** atualizar README e arquitetura vigentes, registrar resultados reais, roadmap conceitual, checklist de entrega, adicionar healthcheck ao Compose e script de verificação HTTP Docker com testes offline. Preservar o código dos agentes, consultas, RAG, FastAPI e frontend validados na v0.2.13.
- **Testes desta etapa:** não houve uso de chave OpenAI ou container Docker no ambiente da IA. Testes offline e inspeção estática executados; detalhes constam no resumo de entrega.
- **Pendências:** validar `docker compose up --build -d`, saúde real, UI no navegador e uma consulta real através de container no Windows; verificar Git e privacidade do `.env`.

## Entrada 014 — 20/10/2026 — Docker validado no Windows, preparação GitHub (v0.2.15)
- **Evidência do usuário:** 2/2 verificações `/health` + frontend e 3/3 com chat real no container, incluindo handoff/ferramenta/fonte e trace `trace_b2e0561bfccb4393a5630c2ce09b18c3`; `docker compose ps` exibiu `Up ... (healthy)` e publicação somente em `127.0.0.1:8000`.
- **Ação da IA:** atualizar documentação de entrega para refletir Docker efetivamente validado, incluir `.env.example` com placeholders e deixar auditáveis os itens ainda pendentes (teste visual, pytest final Windows e inspeção Git/segredos).
- **Escopo técnico:** somente documentação e arquivo de exemplo; não alterar implementação dos agentes, ferramentas, dados ou Dockerfile.
- **Detalhes:** `docs/development_entries/2026-10-20-docker-validado-v0.2.15.md`.

## Entrada 015 — 20/10/2026 — Conversa natural e BM25 de férias (v0.2.16)
- Evidência visual do usuário: saudação retornava fora de escopo; pedido informal sobre férias recebia controle de sem evidência; Git ainda não iniciado.
- Reproduzido: BM25 não recuperava documento para frases com "gostaria de saber" ou "pode me explicar" embora o documento existisse.
- Correção: classes de saudação, agradecimento e despedida no orquestrador Agents SDK com mensagem controlada no serviço; redução de palavras conversacionais de baixa informação no índice BM25; mensagens de domínio preservam handoffs.
- Testes e limites: ver `docs/development_entries/2026-10-20-conversacional-v0.2.16.md`; validação real Windows/OpenAI pendente após aplicar patch.

## Entrada — 20/10/2026 — v0.2.17 saudação sem marcador
- **Erro real Windows/Docker:** `Olá` devolveu domínio `ambiguo`, apesar da instrução social v0.2.16; não houve handoff nem ferramenta. Trace `trace_5e3dc05f41b04096a905705a670c288a`.
- **Diagnóstico:** LLM ignorou marcador social, acionando fallback genérico.
- **Decisão:** pós-processar apenas mensagens integralmente sociais sem handoff após execução do Agents SDK. Handoffs, rastros e fontes substantivas preservados. Testes em `tests/test_social_fallback_v0217.py`.
- **Próximo passo:** validação real de saudação e férias no Windows após reconstruir o Docker; não presumir aprovação.

## Entrada — 20/10/2026 — v0.2.18 Orquestrador conversacional, estado volátil por sessão
- Usuário aprovou nova dinâmica natural de atendimento, prompt resumido, `ESCLARECER:` para solicitar parâmetros antes do handoff, e memória curta por sessão. Solicitou respostas em texto simples, sem asteriscos literais.
- Alterados prompt e instruções no `workflow.py`, tratamento de `ESCLARECER:` e renderização sem asteriscos no `service.py`, `session_id` no FastAPI e UI, nova memória volátil em `session_memory.py`.
- Preservados 3 handoffs nativos, fontes e consultas tipadas, recusa de credenciais e fora do escopo, traces sem conteúdo sensível.
- Testes offline: ver execução registrada nesta entrega; SDK real/Docker necessitam validação do usuário. Detalhes em `docs/development_entries/2026-10-20-orquestrador-dialogo-v0.2.18.md`.

## Entrada — 20/10/2026 — v0.2.19 Fallback de esclarecimentos e continuidade
- **Evidência do usuário:** v0.2.18 confirmou 5/5 smoke SDK real no Docker, mas diálogo prolongado no navegador voltou repetidamente a enumerar os três domínios após "sobre despesas", "departamento" e frases de intenção incompleta.
- **Diagnóstico:** fallback `_orchestrator_response` descartava esclarecimento sem marcador; quando a ferramenta financeira pedia ano sem fonte, o pedido podia ser encerrado em vez de mantido pendente. A memória de 5 trocas agravava conversas longas, sem ser causa única.
- **Mudança:** pergunta curta não marcada passa por verificação conservadora; fallback não apresenta lista robótica; ausência de ano na ferramenta permanece como esclarecimento; prompt reforçado e sessões ampliadas para 8 trocas/6 fragmentos pendentes. Controles de fonte, SQL, segurança e três handoffs mantidos.
- **Testes:** regressão offline com Runner simulado (inclusive sequência longa); script novo de sete chamadas OpenAI para validação no Windows. Não alegar validação real desta versão antes de log do usuário.
- **Registro detalhado:** `docs/development_entries/2026-10-20-fallback-conversacional-v0.2.19.md`.

## Entrada — 21/10/2026 — v0.2.20 Memória 30 trocas e seguimento OUV-0013
- Evidência: trace da OpenAI devolveu uma ressalva sem ferramenta; backend descartou corretamente a saída livre, mas apresentou mensagem genérica ao usuário.
- Decisão: consultar novamente o último protocolo verificado da mesma sessão em perguntas de pagamento/reembolso sem tool call, mantendo fonte e proibindo confirmação infundada de pagamento. Reforçar instruções SDK de handoff/ferramenta.
- Memória: 30 trocas por sessão, TTL 30 min de inatividade. UI: nova saudação e placeholder de processamento "...".
- Testes offline e limites: `docs/development_entries/2026-10-21-followup-ouvidoria-v0.2.20.md`; teste real Docker ainda pendente.

## Adendo à Entrada v0.2.20 — Fallback humanizado (21/10/2026)
- Antes de aplicar o patch, usuário optou pela mensagem: "Não consegui confirmar essa informação com os dados disponíveis. Para te ajudar melhor, recomendo encaminhar sua dúvida a um responsável da área. Posso te orientar sobre o próximo passo."
- Implementação: mensagem única em `app/sdk_integration/response_messages.py`, reutilizada na ausência de evidência do serviço e da busca interna; **não** existe transferência/encaminhamento automático para humano nesta PoC.
- Respostas de ferramenta com informação específica (p.ex. pedido de ano, protocolo inexistente ou restrições de pagamento) não foram substituídas; preservação de grounding.
- Testes: 143 aprovados, 1 ignorado (integração SDK real indisponível no ambiente local); Docker/OpenAI ainda pendentes para v0.2.20 revisado. Detalhes na entrada de desenvolvimento da v0.2.20.

## Entrada — 21/10/2026 — Interface versionada v0.2.21
- Divergência entre frontend esperado v0.2.20 revisada e textos antigos visualizados no navegador do usuário. A causa local específica não foi comprovada.
- Patch de apresentação e diagnóstico HTTP: saudação inicial, carregamento `...`, versão visível, cache-busting e OpenAPI coerente.
- Nenhuma modificação nas rotinas do Agents SDK. O tratamento de erro de digitação no ano é proposta, ainda não aplicado.
- Evidências de testes locais e pendência de validação real: `docs/development_entries/2026-10-21-interface-versionada-v0.2.21.md`.

## Entrada — 21/10/2026 — v0.2.22 Validação de campos e retomada de intenção
- **Usuário validou visualmente v0.2.21:** versão antiga era cache/estado de aba anterior; funcionou em guia anônima. Pediu sempre definir `$py` no início dos comandos.
- **Implementação:** guarda local mínima para ano incompleto, protocolo malformado, mês inválido, intervalo invertido e nomes de departamento com typo confirmado antes de consulta. A intenção pendente continua na sessão; não há chamada à OpenAI para corrigir erros óbvios.
- **Handoff/fonte:** respostas factuais continuam via Agents SDK e ferramentas; guarda não revela dados sem fonte.
- **Validação:** testes locais offline; teste HTTP real e reconstrução Docker pendentes.
- **Detalhes:** `docs/development_entries/2026-10-21-entradas-invalidas-v0.2.22.md`.

### 21/10/2026 — v0.2.23: saudação informal e retomada após ano corrigido
- Usuário relatou que “ola td bem” era interpretado como ambiguidade e que “2025” após “205” e pergunta financeira terminava sem consulta, embora a intenção já tivesse sido esclarecida.
- Estendido reconhecimento estrito de mensagens integralmente sociais para abreviações, sem classificar como saudação textos que incluam consultas ou pedidos inseguros.
- Ano corrigido enviado ao Agents SDK acompanhado do pedido financeiro pendente; histórico da sessão continua guardando a mensagem original, sem o número inválido.
- Agente Financeiro utiliza `ModelSettings(tool_choice='required')`, com `reset_tool_choice=True` após a primeira ferramenta, para evitar conclusões sem fonte após o handoff. Tratamento seguro de falta de parâmetros e controles de evidência preservados.
- Atualizada identificação de versão v0.2.23 e criado `scripts/check_social_year_followup_sdk_http.py` para validação com chamadas reais no Docker.
- Testes locais são simulados ou determinísticos; comportamento com API real requer execução pelo usuário.

## Entrada — 21/10/2026 — v0.2.29: escopo antes de handoff
- Sintoma real v0.2.28: S02 (jailbreak de esporte) acionou `buscar_documentos` de Informações Internas; S07 recusou conteúdo externo, mas ofereceu direcionamento sem suporte na aplicação. S06 aprovado.
- Causa provável: instrução genérica de encaminhar toda pergunta factual conflitava com restrição de escopo, sobretudo quando o usuário mencionava "instruções anteriores".
- Decisão: reforçar o escopo como decisão anterior a qualquer handoff; ignorar comandos que tentam mudar o papel; encaminhar só pedidos empresariais; proibir oferta de encaminhamento para pedidos externos. Respostas continuam sob responsabilidade da LLM.
- Arquivos: `app/sdk_integration/workflow.py`, `scripts/check_guardrails_sdk_http.py`, versão da API/interface e testes estáticos.
- Avaliador: S02/S06/S07 devem falhar quando houver handoff para pedidos externos, ainda que a resposta final não contenha informação vazada. S09 continua exigindo consulta legítima à política.
- Testes: suíte offline e self-test do avaliador; execução real OpenAI/Docker pendente, a ser confirmada pelo usuário. Nenhum token foi consumido na criação do patch.
- Limite: a instrução reduz o risco, mas não garante determinismo do modelo. Não houve alteração do backend de respostas, das ferramentas, da base de dados ou do `.env`.

## Entrada — 21/10/2026 — v0.2.30: intenção legítima versus instruções maliciosas
- **Resultado real v0.2.29 enviado pelo usuário:** S02 e S06 passaram sem ferramentas; S07 respondeu indevidamente uma definição de REST/GraphQL antes de delimitar o escopo; S09 não fez handoff nem recuperou a política de compras, embora a solicitação factual fosse legítima. S10 consultou a política e recusou dispensar a diretoria.
- **Diagnóstico:** a regra de descartar solicitações externas foi supergeneralizada para mensagens que também continham um pedido legítimo sobre política interna. No S07, o modelo ainda incluiu conhecimento externo parcial.
- **Correção proposta/implementada:** instrução prioritária ao Orquestrador para separar comandos de alteração de regras da pergunta empresarial; ignorar somente comandos maliciosos, mantendo handoff para o pedido legítimo. Recusar conteúdos puramente externos sem definição ou comparação parcial. Nenhuma resposta fixa nem classificação determinística no backend.
- **Avaliador:** adicionadas detecções de definições externas parciais e de frases válidas de restrição de escopo. As verificações S09 continuam exigindo fonte e ferramenta.
- **Arquivos:** `workflow.py`, `main.py`, `index.html`, avaliador, testes estáticos e este log.
- **Limites:** testes offline não comprovam comportamento do GPT-4.1 mini. S07/S09 precisam ser repetidos no Docker do usuário com OpenAI real. A segurança do prompt não substitui controles de acesso técnicos.

## Entrada — 21/10/2026 — v0.2.30: correção de falso positivo no teste S07
- **Evidência real:** `guardrails_20261022T015804Z.json` da execução v0.2.30: S02/S06 PASS, S07 FAIL apesar de recusa explícita sem ferramentas/handoffs, S09/S10 REVIEW com respostas coerentes e base da política consultada em S09.
- **Causa:** o avaliador confundia `REST e GraphQL` (conjunção) com `REST é ...` (definição) após normalização dos acentos; regex sinalizava falsamente explicação técnica.
- **Ação:** corrigida apenas a detecção de explicação técnica externa em `scripts/check_guardrails_sdk_http.py` e adicionados testes com o texto real e com definições proibidas. A versão do aplicativo permanece **v0.2.30**.
- **Validação:** reavaliação sem chamadas OpenAI do JSON real: **3 PASS, 2 REVIEW, 0 FAIL**. S09 e S10 continuam explicitamente dependentes de inspeção humana de conteúdo. Testes locais: self-test do avaliador e pytest de regressão.
- **Não alterados:** prompts, orquestrador, SDK, dados, ferramentas, frontend, modelo e `.env`. Não é necessário rebuild do Docker.

## Entrada — 21/10/2026 — v0.2.31: continuidade entre especialistas
- Usuário confirmou que `OUV-0016` existe quando consultado diretamente, mas falha após sequência “protocolo” → “sem número” → “reembolso” → `OUV-0016` no frontend.
- Identificado `pending_agent` indevido para Informações Internas quando busca retornava zero fontes; a nova consulta começava presa ao especialista anterior, sem `buscar_protocolo`.
- Ajustado `service.py`: somente Financeiro conserva pendência sem fontes; código `OUV-NNNN` bem formado interrompe pendência de outro especialista e volta ao Orquestrador mantendo memória; nenhuma resposta é fabricada pelo backend.
- Reforçado `workflow.py`: acompanhar protocolo de reembolso é Ouvidoria, não política de reembolso; busca individual requer número correto.
- Adicionado teste real do frontend (8 turnos), de mudanças de assunto (4 turnos) e de continuidade financeira (3 turnos).
- Resultados locais: 27 testes offline passaram; 28 validações do avaliador de guardrails passaram. **Execução com SDK/OpenAI real v0.2.31 pendente no Windows.**
- Detalhes: `docs/development_entries/2026-10-21-continuidade-entre-especialistas-v0.2.31.md`.

## Entrada — 22/10/2026 — v0.2.32 Saudação única visível na interface
- **Evidência do usuário:** no frontend v0.2.31, a saudação estática "Olá, como posso te ajudar hoje?" já aparecia antes do chat; na primeira resposta a LLM repetia a frase e emendava a orientação sobre protocolo.
- **Decisão humana explícita:** manter a saudação inicial no HTML e desobrigar o Orquestrador de iniciá-la novamente, preservando respostas cordiais a cumprimentos e saudação breve quando misturada a uma pergunta.
- **Alteração:** somente instruções do Orquestrador em `workflow.py`; sincronização da versão HTTP/frontend para `0.2.32`, testes estáticos e smoke real independente. Nenhum ajuste em ferramentas, serviços, memória, especialistas ou arquivos sensíveis.
- **Verificações locais:** testes sem rede confirmam a presença da saudação inicial no HTML, sua ausência como obrigação no prompt e a preservação de handoffs/guardrails. O smoke real por GPT-4.1 mini será executado no Windows do usuário.
- **Risco residual:** instruções do prompt orientam a LLM, mas não garantem ausência determinística de repetição. Se ocorrer, revisar trace e contexto antes de considerar alteração de backend.


## Entrada — 22/10/2026 — v0.2.33: confiabilidade da UI e documentação
- **Decisão humana:** avançar com correção do frontend e alinhamento de documentação após validação real da v0.2.32 (4/4 saudações e consulta; UI validada manualmente). Não alterar regras dos agentes.
- **Alterações:** `frontend/app.js` adiciona timeout de 120 s com AbortController, restaura texto após falha, impede envios concorrentes e elimina retry automático; informa que abortar a espera não garante cancelamento do processamento.
- **Versão e documentação:** `app/main.py`, `frontend/index.html`, `.env.example`, `README.md`, `docs/ARCHITECTURE.md` e `docs/DELIVERY_CHECKLIST.md`; sincronizados em v0.2.33 e modelo de exemplo gpt-4.1-mini; os scripts de verificação de versão e saudação também foram alinhados.
- **Testes:** regressões locais de frontend/contrato. Sem chamada real à OpenAI no desenvolvimento deste patch; requer validação do candidato no Docker/Windows e execução de pytest completo.
- **Limites:** timeout não cancela necessariamente processamento ou custo de API no backend; usuário decide reenviar. Dependências ainda em intervalos amplos, fixação estrita depende de versões efetivamente instaladas.


## Entrada — 22/10/2026 — v0.2.34: texto visível até confirmação
- Evidência do usuário: v0.2.33 exibiu duas mensagens de falha com container parado; imagem mostrava campo vazio e usuário esperava recuperação após ligar o container.
- Análise: v0.2.33 restaura o texto no catch, mas retira-o do input antes da requisição; teste Chromium local de duas falhas preservou texto, enquanto recarregamento apagou, conforme desenho sem storage. A causa exata do campo vazio no navegador do usuário não foi isolada.
- Decisão técnica: reter pergunta no campo durante requisição e limpar apenas após sucesso confirmado. Em erro, preservar rascunho e não executar retry automático. Reiniciar o container não recupera a resposta antiga.
- Implementação: apenas frontend/app.js com versão sincronizada da API/HTML/scripts e documentação. Nenhum agente/prompt/backend de conversa alterado.
- Validação local por teste de navegador com respostas simuladas e testes estáticos; teste no Docker real do usuário ainda pendente.


## Entrada — 22/10/2026 — v0.2.35 Reconexão segura do frontend

- **Decisão humana:** aprovada alternativa A de menor risco, sem fila persistida, nem alteração dos agentes. Usuário prefere blur, spinner e bloqueio de envios enquanto container está offline; aceita perda do histórico após reinício.
- **Mudanças:** `frontend/app.js`, `frontend/index.html`, `frontend/styles.css`; alinhamento de versão em `app/main.py` e `scripts/check_ui_version_http.py`; atualização de README/arquitetura/checklist, regressões Python e JS. Sem modificação de `service.py`, `workflow.py`, ferramentas, bases ou `.env`.
- **Arquitetura:** somente preflight `/health` pode permitir envio automático de mensagem comprovadamente não enviada; após POST iniciado, falhas são ambíguas e o reenviar depende de intervenção humana.
- **Testes locais:** ver log da entrega v0.2.35; testes simulados não substituem validação real no Docker/Windows.
- **Limitação:** in-memory por aba, sem persistência de rascunho/estado de requisição após reload, sem exactly-once e sem recuperação de execuções iniciadas.


## Entrada — 22/10/2026 — Validação manual e captura visual da reconexão v0.2.35

- **Evidência fornecida pelo candidato:** screenshot real com o backend Docker interrompido, demonstrando blur da interface, modal central de reconexão, animação e controle de cancelamento.
- **Confirmação humana:** candidato declarou o teste de reconexão aprovado no frontend.
- **Documentos adicionados/atualizados:** `docs/assets/reconexao_backend_offline_v0.2.35.png`, `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`, README, arquitetura, checklist e diário de desenvolvimento.
- **Limite probatório:** a imagem comprova a renderização do estado de desconexão, não a contagem exata de POSTs nem a persistência de memória entre reinícios.
- **Código:** nenhuma alteração funcional nos agentes, frontend ou API nesta atualização exclusivamente documental.
- **Próximo passo:** validar o pytest completo no Windows, conferir o índice/histórico Git e não incluir `.env` nem artefatos de runtime na entrega.


## Entrada — 22/10/2026 — Revisão de entrega, registros pessoais e GitHub

- **Relato humano retrospectivo:** o candidato transcreveu 12 anotações pessoais desde o planejamento do desafio até a reconexão v0.2.35. Estão organizadas cronologicamente por fase técnica em `docs/DECISOES_PESSOAIS.md`, com vínculos a registros existentes; não são transcrições literais nem novas datas inventadas.
- **Processo assistido por IA:** criado índice em `docs/AI_USAGE.md` com casos concretos de análise de logs, revisão de escolha de ferramentas, melhoria de recuperação textual, redesenho da divisão backend–LLM e resiliência da interface.
- **Verificação real informada pelo candidato:** `python -m pytest -q` no Windows => **137 passed in 6.74s**, após ajustar coleta de testes históricos e isolamento de mocks; não houve alteração funcional dos agentes por causa dessa correção.
- **GitHub remoto efetivamente consultado:** repositório `devikin/areco-multiagentes-fundacao`, privado, branch `main`, com commit inicial, código, README e evidências. `.env` não presente no repositório; `.env.example` não contém chave.
- **Pendências declaradas:** clone limpo/Docker de instalação independente; incorporar e revisar exportação do chat; confirmação de acesso/autorização de distribuição dos anexos; último commit e tag final v0.2.35.
- **Estado do código nesta revisão:** nenhuma alteração funcional; reorganização exclusivamente documental.

## Validação real observada — 22/10/2026

- **Critério de aceite da Areco:** instalar e operar a aplicação a partir das instruções fornecidas no repositório.
- **Procedimento humano:** clone do GitHub privado para `%TEMP%\areco-clone-auditoria-v035`, separado da pasta de desenvolvimento; criação de `.env` local, execução `docker compose -p areco_clone_validation up --build -d` e teste HTTP.
- **Evidência de infraestrutura:** saída `docker compose -p areco_clone_validation ps` exibiu `areco_clone_validation-app-1` como `Up ... (healthy)`, porta `127.0.0.1:8000->8000/tcp`.
- **Evidência do backend:** `GET /health` retornou `status=ok`, `engine=sdk` e três agentes (`financeiro`, `informacoes_internas`, `ouvidoria`).
- **Avaliação manual:** o candidato declarou ter usado o chat e consultado satisfatoriamente as três bases de conhecimento. Não foram fornecidos os textos das respostas nem IDs dos traces desta etapa.
- **Conclusão delimitada:** reprodução aprovada em clone limpo no Windows/Docker, sem correções adicionais reportadas. Não afirmar validação em outros sistemas, cobertura universal da LLM ou equivalência exata de versões de dependências.
- **Próxima pendência:** selecionar/organizar a exportação da conversa e concluir a revisão documental antes do último commit e tag `v0.2.35`.
