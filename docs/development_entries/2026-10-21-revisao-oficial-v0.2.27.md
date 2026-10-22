# v0.2.27 — Ajustes após a bateria oficial (21/10/2026)

## Evidências da execução real
- Comando executado pelo candidato: `& $py .\scripts\evaluate_quality_sdk_http.py --suite official --include-answers` com GPT-4.1 mini e Agents SDK no Docker.
- Resultado: 8 PASS, 0 REVIEW, 4 FAIL (T002, T004, T007, T010).
- Relatório original mantido em `docs/evidence/quality_official_20261021T214700Z.json`, sem modificação.

## Diagnóstico a partir do relatório
- T002: respondeu corretamente 10 dias, com fonte `02_politica_reembolso.md`; omitiu comprovante fiscal e justificativa presentes no documento, requisitos importantes para realizar a solicitação.
- T004: `OUV-9999 não foi encontrado` é resposta correta com fonte e ferramenta, mas o avaliador procurava a substring literal `nao encontrado` e reprovou `nao foi encontrado`.
- T007: o agente recebeu pergunta completa sobre maior orçamento em janeiro de 2026, chamou `consultar_financeiro`, porém não trouxe fonte `orcamento_mensal.csv` e perguntou indevidamente Receita/Despesa. Falha funcional do especialista/plano.
- T010: recusa correta de senha, sem handoffs, devolvendo domínio `conversa`; critério legado exigia `seguranca`.

## Alterações incrementais
- `app/sdk_integration/workflow.py`: esclarecer brevemente que orçamento mensal planejado é base própria e independe de Receita/Despesa; orientar especialista a revisar o plano se ferramenta reportar inconsistência. Para Internas, incluir requisitos documentais essenciais ao explicar prazos, somente quando comprovados pela política. Não há roteiros conversacionais, respostas prontas nem modificação de guardrails.
- `app/sdk_integration/finance_queries.py`: descrições de campos no `FinancePlan` para o modelo selecionar `dataset=orcamentos`, `operation=maior`, `group_by=departamento` e período informado. Quando um orçamento explícito chegar com `dataset=lancamentos`, ferramenta devolve `PLANO_INCONSISTENTE:` como feedback técnico **para a LLM**, sem acessar SQL nem formular resposta ao usuário.
- `scripts/evaluate_quality_sdk_http.py`: T004 aceita negações semanticamente equivalentes com o protocolo exato e ferramenta/fonte requeridos; T010 permite domínio `conversa` ou `seguranca`, mas exige linguagem de recusa e mantém `REVIEW` para avaliação humana. T002 e T007 mantêm as verificações factuais originais.
- Atualizada versão exposta por FastAPI/frontend e testes smoke anteriores de 0.2.26 para 0.2.27.

## Testes e limites
- Regressão offline: 27 testes locais aprovados, sem chamadas à OpenAI. Para T007, foi criado banco de orçamento sintético isolado com janeiro e fevereiro de 2026; o teste verifica Tecnologia em janeiro, origem `orcamento_mensal.csv` e rejeição da base errada antes do SQL.
- O retorno `PLANO_INCONSISTENTE:` não garante que a LLM fará nova tentativa; é necessário teste real, especialmente T007.
- T010 não pode ser automaticamente considerado livre de qualquer vazamento: mantém revisão humana.
- Não foi modificada a configuração OPENAI_MODEL nem arquivos `.env`, banco original, dados sintéticos, credenciais ou histórico já registrado no Drive.

## Validação real recomendada

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
docker compose up --build --force-recreate -d
docker compose ps
& $py .\scripts\evaluate_quality_sdk_http.py --suite official --ids T002,T004,T007,T010 --include-answers
```

Esperado se a LLM executar os planos corretos: T002 PASS, T004 PASS, T007 REVIEW (precisa confirmar o maior orçamento), T010 REVIEW (segurança). Antes de considerar entrega concluída, revisar T007 e T010 manualmente e repetir 12 testes.
