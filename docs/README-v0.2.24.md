# Patch v0.2.24 — Guia de aplicação (Areco)

Instale APENAS sobre a pasta da v0.2.23. O ZIP preserva `.env`, `.venv`, bases, Docker, documentação histórica e scripts anteriores. A variável `OPENAI_MODEL=gpt-4.1-mini` já configurada pelo candidato em `.env` será lida no próximo reinício.

No PowerShell, estando em `H:\Meu Drive\Desafio IA Areco\areco-multiagentes-fundacao`:

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
docker compose up --build --force-recreate -d
docker compose ps
& $py .\scripts\check_redesign_sdk_http.py
```

O script faz **nove** requisições reais ao endpoint e consome tokens. Observe o conteúdo de cada resposta, sobretudo naturalidade, escopo, ausência de asteriscos, handoffs e fontes. Use uma nova guia anônima, ou Ctrl+F5, para evitar cache anterior.

A regressão oficial antiga pressupõe marcadores/fallbacks e poderá requerer novos critérios; não interpretar esses testes legados como validação da arquitetura nova.
