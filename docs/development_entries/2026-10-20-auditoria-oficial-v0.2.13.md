# v0.2.13 — Ajustes após primeira bateria oficial Areco (20/10/2026)

## Evidência real apresentada pelo candidato

Comando `evaluate_quality_sdk_http.py --suite official` no Windows, usando Agents SDK real:
- **PASS:** T001, T005, T006, T009, T011 (5)
- **REVIEW:** T007, T010 (2) — **ainda não aprovados semanticamente**
- **FAIL:** T002 (omissão de comprovante), T003 (roteamento incorreto para Financeiro), T004 (termo literal "não encontrado" ausente), T008 e T012 (indevidamente considerados fora de escopo).
- O relatório foi salvo pelo usuário em `docs/evidence/quality_official_20261020T230829Z.json`; ele não foi analisado integralmente neste ambiente. Apenas o resumo enviado no chat foi recebido.

## Diagnóstico e decisões

- T003, T008, T012 são erros no **orquestrador/seleção de handoff**; não são falhas de RAG nem da ferramenta SQL.
- T002 é problema de **completude da resposta**, não prova que o documento está incorreto.
- T004 pode ser diferença de formulação, pois a ferramenta local já devolve "não encontrado"; evitar transformar resultado factual do banco em paráfrase sem garantir a mensagem canônica.
- Manter Agents SDK como motor único e LLM como roteador; **não forçar roteamento por heurística determinística** após a chamada.
- Fortalecer instruções e descrições de handoff: aprovação de compras com valores em R$ pertence a Informações Internas; phishing e relato de incidentes também. `SEGURANCA:` para pedidos de segredos/credenciais, não para solicitações legítimas de orientação.
- Agente Internas deve mencionar requisitos documentais junto ao prazo de reembolso; não inventar documentos.
- Quando um protocolo exato está ausente, a ferramenta devolve evidência canônica. O serviço preserva `control_answer`, impedindo que o modelo transforme a ausência em afirmação inventada. Isso não é fallback de roteamento, é proteção de integridade de consulta.
- Introduzir opção `--ids` ao avaliador para repetir **apenas** os cinco FAIL; opcionalmente `--include-answers` registra as respostas de bases sintéticas para revisão humana.

## Implementação

- `app/sdk_integration/workflow.py`: reforço nas instruções e descrições de encaminhamento; exemplos dos casos que falharam.
- `app/sdk_integration/tools.py`: ausência de protocolo exato gera `control_answer` com número e mensagem padronizada.
- `app/sdk_integration/service.py`: prioriza o resultado de controle factual da ferramenta, mesmo quando o especialista foi acionado com fonte válida.
- `scripts/evaluate_quality_sdk_http.py`: argumento `--ids` para selecionar casos da suíte.
- `tests/test_official_regression_v0213.py`: testes de política, ferramenta, serviço e seleção de casos.

## Testes e limites

- Executado nesta cópia local: `python -m pytest -q -p no:cacheprovider` → **84 passed, 1 skipped**, usando testes offline e Runner simulado.
- Executado `python -m compileall -q app scripts tests` → sem erros.
- **Não houve novas chamadas reais à OpenAI** nesta correção; comportamento probabilístico do roteador depende de validação no Windows.
- **Docker não testado** nesta etapa.
- A falha de T004 não prova, sozinha, erro de conteúdo; o avaliador usa comparação lexical estrita. A resposta anterior completa não foi compartilhada. T007 e T010 ainda precisam de revisão humana.

## Próximo passo humano

1. Aplicar patch sobre v0.2.12 após backup; reiniciar o FastAPI.
2. `& $py .\scripts\evaluate_quality_sdk_http.py --suite official --ids T002,T003,T004,T008,T012 --include-answers`.
3. Inspecionar o arquivo JSON local; enviar IDs, resultados e as respostas em caso de FAIL. Depois revisar T007/T010 e executar suíte oficial completa de 12 casos.
