# v0.2.4 — Plano LLM + SQL financeiro seguro

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
