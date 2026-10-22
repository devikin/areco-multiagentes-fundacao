# Auditoria da suíte de testes — Areco v0.2.35

**Motivo:** `pytest` era interrompido durante a coleta porque testes de v0.2.10–v0.2.23 importavam funções descontinuadas (`_orchestrator_response`, `SOCIAL_ANSWERS`, `_social_intent`, `OUT_OF_SCOPE_ANSWER`) ou assumiam o estado de sessão legado (`record`, `pending_questions`). Essas APIs não pertencem ao contrato do OpenAI Agents SDK adotado atualmente.

## Decisão

- **Não** reintroduzir funções legadas apenas para satisfazer testes antigos.
- Preservar os arquivos integrais em `docs/tests_historicos/` com um manifesto contendo hash SHA-256 e caminho original, usando `scripts/archive_legacy_tests.py --apply`.
- Os testes arquivados **não contam como testes aprovados da versão atual**. Este arquivamento não corrige falhas funcionais eventualmente descobertas na suíte remanescente.
- Adicionar testes de sessão atuais em `tests/test_session_contract_current_v035.py` para isolamento, reentrada de protocolo, pendências financeiras e limite de histórico.
- Preservar testes contemporâneos de v0.2.24–v0.2.35 e testes de ferramentas/dados enquanto forem compatíveis; investigar qualquer falha remanescente individualmente, sem ignorá-la silenciosamente.
- Versão funcional da aplicação **permanece 0.2.35**; nenhum endpoint, especialista, ferramenta, prompt, arquivo de dados ou banco foi modificado.

## Instruções

Na raiz do projeto:

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
& $py .\scripts\archive_legacy_tests.py            # inspeção sem alterar
& $py .\scripts\archive_legacy_tests.py --apply    # arquiva sem apagar
& $py -m pytest -q
```

`--restore` desfaz os movimentos verificando os hashes e recusando sobrescrever originais.

**Cuidado:** pytest em execução após essa migração pode identificar problemas adicionais não visíveis enquanto a coleta estava bloqueada. Só declarar a suíte aprovada quando a saída do Windows indicar zero falhas e erros.
