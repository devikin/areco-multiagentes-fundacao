# Plano de três dias úteis — orientação pelo MVP

> Dias são relativos à data real de início/recebimento; não foram presumidas datas de entrega.

| Fase | Prioridade | Entregável comprovável | Critério de saída |
|---|---|---|---|
| Dia 1 — fundação | P0 | Arquivos reais classificados por domínio, arquitetura revisada, AGENTS.md, logs de trabalho, FastAPI mínimo e contratos | Endpoints de saúde/chat e teste isolado de roteamento executados |
| Dia 2 — integração | P0 | 3 agentes, recuperação de dados, citações, frontend e tratamento de ausência de evidências | Cada domínio responde casos positivos e negativos usando dados dos anexos |
| Dia 3 — validação | P0 | Testes integrados/negativos, Docker, README, logs, evidências e revisão do Git | Projeto clonado/rodado conforme documentação, evidências registradas |

## Backlog priorizado
1. **P0:** inventariar arquivos e estruturar fontes; confirmar permissões de uso e upload a um provedor de LLM.
2. **P0:** contrato Pydantic de classificação e saída; roteamento independente, injetável para testes.
3. **P0:** recuperadores por domínio; tratamento robusto de nenhuma evidência e conteúdo malicioso.
4. **P0:** testes unitários de classificação e recuperação; integração de chat.
5. **P0:** Docker, health check, logs por ID, README e demonstração guiada.
6. **P1:** histórico curto de conversas se necessário para perguntas de seguimento.
7. **P1:** métricas de tokens/custos; melhorias de ranking se a recuperação falhar nos testes.
8. **P2:** busca semântica, persistência sofisticada, dashboards de observabilidade, orquestração de workflows.

## Critério de corte de escopo
Se o prazo ficar apertado, manter os 3 agentes, roteamento, respostas fundamentadas, API, UI mínima, Docker e testes negativos. Adiar animações, embeddings hospedados, sessões persistentes e instrumentação avançada.

## Riscos principais
- **Bases não disponíveis:** bloqueia decisões de extração/retrieval e testes reais. Mitigação: prototipar contratos, sem fingir uso de dados da Areco.
- **Documento complexo/tabela:** RAG puramente textual pode gerar números incorretos. Mitigação: extrair estrutura e usar cálculo determinístico.
- **Rota equivocada:** agente responde com fonte do domínio errado. Mitigação: dataset rotulado e testes por domínio.
- **Alucinação:** modelo responde sem evidência. Mitigação: gate de relevância, citações verificáveis e status `insufficient_evidence`.
- **API indisponível ou custo:** testes reprodutíveis precisam de mocks; prever timeout e erro amigável.
- **Docker não testado:** documentação não prova execução. Mitigação: smoke test em ambiente real com evidência.
- **Histórico de IA incompleto:** preservar prompts/revisões conforme ocorrem.
