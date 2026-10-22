# Atualização incremental v0.2.26 — Ano confirmado e recuperação natural

Aplicar sobre a v0.2.25, extraindo na pasta que contém `areco-multiagentes-fundacao`. Não inclui nem altera `.env`, dados, credenciais ou banco SQLite.

## Correção
`205` não é um ano válido em quatro dígitos. Antes o agente podia inventar `2050` e fazer consulta real; agora o plano financeiro é rejeitado **antes de abrir o banco** caso não corresponda a um ano confirmado no texto do usuário. O retorno técnico é enviado ao especialista, que faz a pergunta de correção usando a LLM. Após `2025`, o especialista deve continuar a intenção original e chamar a ferramenta para agrupar por departamento, com fonte.

Também são rejeitados meses/intervalos e filtros acrescentados sem confirmação, além da troca indevida de agrupamento por departamento por uma soma geral. Datas relativas exigem confirmação explícita de ano de quatro dígitos nesta versão.

## PowerShell — reconstrução e teste real

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"

docker compose up --build --force-recreate -d
docker compose ps
& $py .\scripts\check_year_guard_sdk_http.py
```

O teste recomendado executa apenas três turnos com a OpenAI: intenção financeira, `205` e `2025`. Para executar a regressão mais ampla (nove turnos, maior custo), use `& $py .\scripts\check_redesign_sdk_http.py`. É esperado que **205 não produza nenhuma citação**. A execução no Docker do candidato permanece pendente. Testes offline nesta preparação: 21 aprovados.
