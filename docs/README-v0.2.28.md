# Areco Agents SDK v0.2.28 — Guardrails e busca documental

Patch incremental sobre v0.2.27. Extraia mantendo a raiz `areco-multiagentes-fundacao/`.

## O que mudou
- Prompt: evitar handoffs fora do escopo; pedir referência ambígua diretamente; buscar fatos legítimos mesmo com texto malicioso misturado, usando pesquisa resumida.
- BM25: melhorar recall para aprovação de compras quando a pergunta contém distrações/adversarial; não responde por conta própria e não introduz fallback conversacional.
- Avaliador de segurança: diferenciar FAIL de REVIEW para recusas corretas e consultas improdutivas; revisão humana permanece necessária.
- API/UI: 0.2.28, sem alteração `.env`.

## Windows PowerShell
```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"

docker compose up --build --force-recreate -d
& $py .\scripts\check_guardrails_sdk_http.py --self-test
& $py .\scripts\check_guardrails_sdk_http.py --reassess-report .\docs\evidence\guardrails_20261021T223238Z.json
& $py .\scripts\check_guardrails_sdk_http.py --ids S02,S06,S07,S09,S10,S12
```

O último comando faz 7 chamadas reais à OpenAI; S10 e S12 incluem suas dependências S09/S11 automaticamente.
A reavaliação do JSON anterior não comprova mudanças na LLM, só corrige classificação anterior.
