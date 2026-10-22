# v0.2.11 — Avaliação da qualidade dos quatro agentes

**Escopo:** somente script de avaliação, testes offline do avaliador e registro do desenvolvimento. **Não altera** prompts, FastAPI, SQLite, ferramentas, Docker ou frontend.

## Evidência já recebida (20/10/2026)
O usuário executou no Windows: `check_internas_sdk_http.py` **3/3** (férias, trabalho remoto, reembolso) e `check_sdk_http.py` **3/3 handoffs** (Internas, Financeiro, Ouvidoria), com IDs de traces informados na conversa. Essa evidência confirma smoke tests, **não** equivale à bateria completa abaixo.

## Executar testes offline (sem custo de API)

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
& $py -m pytest -q tests\test_quality_eval_v0211.py
```

## Executar testes reais (gera custos de API)
**Deixe o Uvicorn aberto em outro terminal.** A execução é sequencial e cada caso pode utilizar várias requisições LLM.

```powershell
& $py .\scripts\evaluate_quality_sdk_http.py --suite smoke     # 6 perguntas
& $py .\scripts\evaluate_quality_sdk_http.py --suite official  # 12 casos do pacote Areco
& $py .\scripts\evaluate_quality_sdk_http.py --suite full      # 12 oficiais + 5 extras
```

- `PASS`: critérios automáticos objetivos atendidos.
- `REVIEW`: sem falhas automáticas, **mas exige revisão manual** do texto, sobretudo recusa, elegibilidade, prompt injection e semântica.
- `FAIL`: falha no domínio, tool, handoff, fonte, trace ou conteúdo literal essencial.
- O resultado `PASS` de uma verificação automática **não assegura ausência de alucinação**.
- Pode haver falsos negativos por paráfrase, números formatados de outro modo, variação estocástica da LLM ou versões da fonte. Verifique o trace e a resposta real antes de ajustar o teste.
- O relatório JSON é salvo em `docs/evidence/quality_<suite>_<timestamp>.json`. Por padrão **não inclui pergunta nem resposta**, apenas hashes, domínio, fontes, tools, latência, tokens e trace. Para inspecionar o texto, execute com `--include-answers` somente com dados sintéticos.
- O script não executa operações de escrita nas bases de conhecimento.

### Os 12 casos oficiais
Cobrem férias, reembolso, compras, protocolo inexistente, status, despesas 2025, orçamento, phishing, protocolo existente, segurança de senhas, receitas 2025 e incidentes de segurança. Fontes: `data/reference/perguntas_avaliacao.json` e bases fornecidas pela Areco.

### Os 5 casos complementares
Trabalho remoto (sem permissão pessoal inventada), ambiguidade real, fora de escopo, tentativa de sobrepor política por prompt e saldo individual de férias. A leitura humana é obrigatória para confirmar segurança e qualidade.

### Critérios de aceite desta fase
1. Sem falhas nos 12 testes oficiais após inspeção humana dos casos marcados REVIEW.
2. Casos de segurança e fora de escopo sem transferência indevida e sem divulgação de dados privados.
3. Traces e fontes recuperadas para cada resposta factual.
4. Registrar casos reprovados, mensagens/erros relevantes, alteração proposta e reexecução — sem fabricar aprovações.

**Pendente:** testes reais dessa suíte no Windows e Docker. Esta etapa valida o avaliador offline, não a qualidade do modelo no ambiente real.
