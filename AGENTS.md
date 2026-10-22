# AGENTS.md — Diretrizes vigentes para desenvolvimento assistido por IA

> Documento de instruções criado desde a preparação inicial do desafio, em 20/10/2026. Esta edição consolida as diretrizes **vigentes da v0.2.35**. O conteúdo anterior, inclusive regras substituídas, é preservado em `docs/AGENTS_HISTORY.md` e no histórico Git.

## Objetivo e limites

Construir e manter uma prova de conceito de assistente multiagente para o desafio Areco, compreensível, reproduzível, testável e orientada por evidências. Não tratar a PoC como sistema de produção: não há autenticação por usuário, controle de permissões nem garantia absoluta contra alucinações.

## Arquitetura atual (fonte de verdade)

- Backend Python 3.12 + FastAPI (`app/main.py`); frontend HTML/CSS/JS em `frontend/`.
- `app/sdk_integration/workflow.py`: **OpenAI Agents SDK**, com um Orquestrador e handoffs nativos para Financeiro, Informações Internas e Ouvidoria; respostas ao usuário geradas pela LLM, sem substituir seu conteúdo com templates locais legados.
- `app/sdk_integration/tools.py`, `finance_queries.py` e `ouvidoria_queries.py`: ferramentas de leitura controlada, filtros tipados e SQL parametrizado; cálculos monetários com `Decimal`. Nunca executar SQL livre sugerido pelo modelo.
- `app/knowledge/ingest.py` e `retrieval.py`: ingestão de bases sintéticas, SQLite e recuperação BM25 com identificação de fontes/documentos.
- `app/sdk_integration/service.py` e `session_memory.py`: memória de sessão volátil, isolamento entre abas, limites de sessão e rastreabilidade de handoffs, ferramentas e traces. Não afirmar persistência após reinício.
- `frontend/app.js`: preflight `/health`, modal de espera quando servidor indisponível e envio automático **somente enquanto não houve POST**; após POST incerto, o reenvio é exclusivamente manual.
- `docs/ARCHITECTURE.md` contém o desenho detalhado e os trade-offs. Versões antigas registradas em documentação histórica **não são instruções vigentes**.

## Protocolo obrigatório de trabalho e registro

1. Antes de implementar, identificar problema, requisito, evidência disponível, limitações e arquivos potencialmente afetados.
2. Registrar a **solicitação humana ou referência de conversa**, a proposta da IA e as alternativas. Diferenciar explicitamente escolha do candidato de decisão sugerida ou executada pela IA.
3. Documentar a razão da escolha, implicações e alternativas rejeitadas, sem atribuir ao candidato decisões não confirmadas.
4. Preservar as mudanças pequenas e reversíveis. Evitar modificar agentes/serviço/testes aprovados para atender somente questões documentais.
5. Registrar **após cada etapa realmente executada** em `docs/DEVELOPMENT_LOG.md`: data/etapa, comportamento observado, prompt ou referência, arquivos, testes/comandos e resultados, problemas, correções e pendências.
6. Para decisões relevantes, registrar um ADR único em `docs/DECISIONS.md`. Para reflexões do candidato, consultar e atualizar cronologicamente `docs/DECISOES_PESSOAIS.md`; declarações retrospectivas devem ser identificadas como tal.
7. Manter `docs/AI_USAGE.md` como índice dos casos demonstrativos e `docs/ai_interactions/` como referência de prompts e transcrições/exportações verificadas. Não transformar resumo em citação literal de chat.
8. Distinguir testes offline/mockados, execução HTTP/Docker, testes com OpenAI real e inspeção manual. Nunca declarar PASS sem saída/evidência; registrar `REVIEW` como revisão humana, não aprovação automática.
9. Preservar `request_id`, `trace_id`, agente, ferramentas, handoffs, fontes e uso de tokens quando presentes, sem capturar respostas ou dados sensíveis desnecessariamente. Usar `trace_include_sensitive_data=False`.
10. Verificar o README como se o avaliador fosse clonar do zero. Manter `.env` fora do Git, usar `.env.example` sem segredo e não publicar o MVP em endereço público.

## Checklist mínimo por alteração

- Contexto e intenção documentados; fonte e domínio corretos.
- Handoff e resposta baseados na ferramenta apropriada; não inventar valores, protocolos, direitos ou políticas.
- Erros de entrada, falhas de OpenAI, falta de fontes e conexão indisponível têm respostas controladas.
- `python -m pytest -q` executado quando código/testes forem alterados, com resultado real registrado. Para alteração documental exclusiva, verificar links/caminhos e `git diff --check`.
- README, arquitetura, decisões e diário sincronizados; nenhuma chave ou arquivo de runtime versionado.

## Evidências de referência

- Histórico técnico: [`docs/DEVELOPMENT_LOG.md`](docs/DEVELOPMENT_LOG.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/AGENTS_HISTORY.md`](docs/AGENTS_HISTORY.md).
- Decisões pessoais: [`docs/DECISOES_PESSOAIS.md`](docs/DECISOES_PESSOAIS.md).
- Casos de interação com IA: [`docs/AI_USAGE.md`](docs/AI_USAGE.md).
- Validação e limitações: [`docs/RELEASE_VALIDATION_v0.2.35.md`](docs/RELEASE_VALIDATION_v0.2.35.md), [`docs/DELIVERY_CHECKLIST.md`](docs/DELIVERY_CHECKLIST.md).
