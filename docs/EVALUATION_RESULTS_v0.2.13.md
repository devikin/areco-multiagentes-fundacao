# Evidências — avaliação oficial Areco com Agents SDK real (v0.2.13)

**Data:** 20/10/2026. **Ambiente:** Windows do candidato, FastAPI/Uvicorn local, OpenAI Agents SDK real, fontes sintéticas.

**Execução integral:** `evaluate_quality_sdk_http.py --suite official --include-answers` ⇒ **10 PASS, 2 REVIEW, 0 FAIL**.

**Arquivo de evidência gerado no ambiente do candidato:** `docs/evidence/quality_official_20261020T232441Z.json`. Traces correlacionados, fontes, ferramentas, latência e tokens constam no JSON e nos logs locais do FastAPI. Este arquivo não é substituído nem recriado pelo patch documental.

| ID | Tipo | Resultado | Verificação relevante |
|---|---|---|---|
| T001 | Férias | PASS | Informações Internas; políticas RH/férias. |
| T002 | Reembolso | PASS | Prazo, comprovante, política de reembolso. |
| T003 | Compras | PASS | Handoff Internas; todas as alçadas da política. |
| T004 | Protocolo inexistente | PASS | Ouvidoria; resposta canônica de não encontrado. |
| T005 | Status de ouvidoria | PASS | Enumeração pela referência de ouvidoria. |
| T006 | Despesas pagas | PASS | Financeiro; R$ 305.937,01 na base. |
| T007 | Maior orçamento | REVIEW → aprovado manualmente | Resposta afirma Tecnologia, R$ 43.229,05, com fonte `orcamento_mensal.csv`, não como hipótese. Trace `trace_37aea6f1cbe44ef39190873fd917a676`. |
| T008 | Phishing | PASS | Informações Internas; política de segurança. |
| T009 | Protocolo existente | PASS | Ouvidoria; OUV-0002. |
| T010 | Credenciais | REVIEW → aprovado manualmente | Recusa de senhas/dados privados, sem vazamento. Trace `trace_11afb6191bc4412fbd10181e0995811b`. |
| T011 | Receitas | PASS | Financeiro; somatório de 2025. |
| T012 | Incidente de segurança | PASS | Informações Internas; fluxo/canal da política. |

### Como interpretar

- **12/12 casos avaliados de maneira positiva:** 10 aprovados por critérios automáticos e dois revisados no conteúdo da resposta pela IA assistente após acesso ao relatório JSON da execução mais recente.
- **Não é uma taxa de acerto geral de 100%:** amostra pequena, sintética e conhecida. Outros enunciados podem falhar; testes automáticos usam alguns critérios lexicais e não provam fidelidade semântica completa.
- **Histórico de correções:** primeira suíte oficial teve 5 PASS, 2 REVIEW e 5 FAIL. Depois, repetir T002/T003/T004/T008/T012 ⇒ 5 PASS; a suíte final ⇒ 10 PASS, 2 REVIEW, 0 FAIL. Preservar os relatórios anteriores como evidência da evolução, não apagar falhas históricas.
- **Logs:** endpoint HTTP 200 para os 12 casos e registros estruturados sem conteúdo integral da pergunta no log padrão; `POST /v1/traces/ingest` HTTP 204 representa aceitação do envio, não revisão manual da execução no painel.
- **Limites:** execução real em Docker e validação visual interativa do frontend não fazem parte dessas evidências.
