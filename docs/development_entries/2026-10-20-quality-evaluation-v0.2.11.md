# Registro de desenvolvimento — v0.2.11 — suíte de qualidade

**Data:** 2026-10-20. **Demanda:** após aprovação do roteador v0.2.10 pelo usuário, avançar com testes de qualidade, segurança e ambiguidade sem reescrever os agentes.

## Fatos observados
- O usuário validou 3/3 consultas internas com fontes (incluindo home office) e 3/3 handoffs com FastAPI real.
- A validação anterior não cobriu formalmente as 12 perguntas do pacote de avaliação nem cenários adicionais de robustez.

## Proposta/implementação da IA
- Script de avaliação via HTTP que executa 12 perguntas oficiais e 5 complementares.
- Verificação objetiva de domínio, handoff, ferramenta, fonte, trace, palavras/números críticos.
- Separação entre PASS, FAIL e REVIEW; jamais rotular segurança sem revisão humana como totalmente validada.
- JSON de evidências com hash da resposta, sem pergunta/resposta em claro por padrão.
- Testes offline próprios do script, sem chamadas ao provedor LLM.

## Limitações e próximos passos
- O reconhecimento semântico do resultado ainda requer avaliação humana; testes de palavras não substituem grounding.
- Falhas em testes reais podem refletir oscilação da LLM ou bug efetivo e devem ser analisadas pelo trace.
- Os 12+5 testes reais **não foram executados aqui** com a OpenAI.
- Próximo: usuário executar a suíte contra Uvicorn, compartilhar resumo e inspecionar casos FAIL/REVIEW.
