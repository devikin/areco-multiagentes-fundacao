# Patch incremental v0.2.27 — Bateria oficial Areco

Aplicar somente sobre a v0.2.26 já validada, extraindo o conteúdo do ZIP na pasta `H:\Meu Drive\Desafio IA Areco`. O ZIP usa pasta-raiz `areco-multiagentes-fundacao`. Não inclui `.env`, banco, planilhas, dados, credenciais ou tokens.

## Ajustes
- T002: informações internas passam a priorizar prazo e requisitos essenciais de um procedimento, com base no documento recuperado. Não acrescentar informações sem evidência.
- T007: orçamento mensal é distinto dos lançamentos efetivos; o especialista recebe descrições de parâmetros e feedback técnico que permite corrigir plano incorreto sem pedir Receita/Despesa à toa. Cálculos e consultas permanecem no SQLite somente por planos validados.
- T004: avaliador aceita “não foi encontrado” como equivalente a “não encontrado”, desde que protocolo, fonte e ferramenta sejam corretos.
- T010: uma recusa no domínio `conversa` ou `seguranca` é aceitável, porém o caso fica em `REVIEW` para análise humana das credenciais.
- Interface e API exibem versão v0.2.27, evitando confusão com cache de versões anteriores.

## Instalação e execução — PowerShell

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"

docker compose up --build --force-recreate -d
docker compose ps

& $py .\scripts\evaluate_quality_sdk_http.py --suite official --ids T002,T004,T007,T010 --include-answers
```

As quatro perguntas geram chamadas reais à API OpenAI e consomem tokens. Resultados esperados **se a nova execução da LLM resolver T002/T007**: T002 PASS, T004 PASS, T007 REVIEW, T010 REVIEW. REVIEW não representa aprovação automática. Não declarar todos os 12 casos aprovados sem repetir a suíte completa.

Depois de validar semanticamente T007/T010 e resolver eventuais falhas, repetir os 12 casos:

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
& $py .\scripts\evaluate_quality_sdk_http.py --suite official --include-answers
```

O relatório fica em `docs/evidence/quality_official_YYYYMMDDTHHMMSSZ.json`.

## Histórico técnico
Ver `docs/development_entries/2026-10-21-revisao-oficial-v0.2.27.md`.
