# Etapa v0.2.9 — Recuperação documental de Informações Internas

**Data:** 20/10/2026
**Solicitação:** depois de validar 3/3 handoffs e as consultas avançadas de Ouvidoria v0.2.8 em FastAPI com SDK real, prosseguir com a melhoria do RAG documental. O usuário também mostrou um trace onde o painel de tool `consultar_manifestacoes` indicava `No output`.

## Problema observado na implementação anterior
- `retrieve()` retornava diferentes chunks da mesma fonte, fazendo FAQ e documento competirem por espaço nos 3 resultados.
- `Como reporto um incidente de segurança?` podia privilegiar uma fonte genérica de segurança em vez de fluxo de incidentes.
- `Posso trabalhar de casa?` não localizava o documento **Trabalho remoto e híbrido**, porque a busca era estritamente lexical.
- Fontes não traziam explicitamente a versão na resposta da ferramenta.
- Correspondências fracas ocasionavam documentos de outro tema no contexto do modelo.

## Solução proposta/implementada pela IA
1. Manter BM25 local, sem vetores/serviço externo, apropriado para 10 documentos curtos.
2. Normalizar acentos/plurais comuns, empregar conjunto **restrito e explícito** de aliases de vocabulário da base, sem caracterizar como embedding/semantic search.
3. Usar FAQ na pontuação, mas devolver cada documento principal uma só vez com seu texto completo e versão.
4. Filtrar combinações com baixa sobreposição e pontuação relativa; não preencher lacunas com fatos externos.
5. Ajustar instruções do especialista para citar os documentos realmente usados e as versões disponíveis.
6. Preservar interfaces: FastAPI, SDK Runner, handoffs, campos `sources`, SQLite e dados de origem permanecem intactos.

## Alternativas
- Embeddings e banco vetorial: rejeitados nesta etapa pelo volume limitado (10 documentos), custo, dependências e prazo.
- Usar LLM como indexador único: rejeitado por falta de recuperação auditável.
- Reindexar em fragmentos pequenos: desnecessário para documentos curtos, com risco de perder condições e limitações.

## Arquivos alterados
- `app/knowledge/retrieval.py`
- `app/sdk_integration/tools.py`
- `app/sdk_integration/workflow.py`
- `tests/test_rag_v029.py` (novo)
- `scripts/check_internas_sdk_http.py` (novo)
- `README.md`, `docs/DEVELOPMENT_LOG.md`, este registro.

## Testes observados
- Execução local (Linux, sem chamada OpenAI): `python -m pytest -q -p no:cacheprovider` => **61 passed, 1 skipped**.
- Testes de ranking, fontes únicas, texto completo, versão, consulta multifonte, ausência de evidência e senha sensível.
- Primeiro teste de regressão de senha falhou porque a política de segurança foi corretamente recuperada; ajustado o critério de teste para exigir política de segurança e recusa pelo especialista, sem excluir fontes de orientação.
- Testes offline antigos (45 aprovados, 1 pulado na v0.2.8) seguem aprovados.
- **Não testado aqui:** execução real com Agents SDK/OpenAI no Windows, nem Docker; validar com `scripts/check_internas_sdk_http.py` após aplicação.

## Tracing
- `app/sdk_integration/service.py` configura `trace_include_sensitive_data=False`. Isso pode explicar tool spans que apresentam `No output` apesar de a ferramenta ser usada. A ausência de payload no painel, isoladamente, não invalida uma resposta verificada pelo endpoint. Não alteramos essa opção de privacidade nesta etapa.

## Limitações conhecidas
- BM25 com aliases **não cobre sinônimos não previstos**; futuro upgrade semântico seria opcional.
- O modelo ainda deve ser auditado por perguntas reais para garantir que use somente fontes devolvidas.
- Documentos sintéticos sem acesso individual; não garantir políticas reais ou dados pessoais.
- A aprovação de 3/3 handoffs e Ouvidoria v0.2.8 foi informada pelo usuário, não refeita nesta revisão com OpenAI ao vivo.
