# v0.2.8 — Regressão real em escolha de ferramenta da Ouvidoria

## Origem / evidência
Em 20/10/2026 o usuário reportou `check_sdk_http.py: 3/3` aprovado e
`check_ouvidoria_sdk_http.py` falhando no caso de prioridade Alta:
`tools_used=["contar_manifestacoes"]`; resposta total geral=180;
esperado apenas prioridade Alta=38. Handoff para Ouvidoria ocorreu corretamente.

## Solução proposta pela IA
Remover do agente a ferramenta sem filtros `contar_manifestacoes` e
centralizar contagem total e filtrada, agrupamentos e listagens em
`consultar_manifestacoes(OuvidoriaPlan)`; reforçar instruções e validar
no executor que uma pergunta de distribuição “por X” não use operação
`contagem` nem agrupe por Y.

## Testes realizados
Teste local com fixture SQL da base real: `45 passed, 1 skipped`.
Não houve chamadas à OpenAI nem teste Windows desta correção ainda.

## Decisão humana pendente
Aplicar patch e testar 2/2 consultas avançadas reais. Preservar traces
para comparação e não afirmar conclusão sem essa evidência.
