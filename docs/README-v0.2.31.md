# Areco Multiagentes — Patch v0.2.31

**Objetivo:** corrigir a sessão do frontend que não localizava `OUV-0016` depois de perguntar sobre um protocolo de reembolso.

### Correções
- Impedir que busca documental sem evidências mantenha Informações Internas como agente pendente.
- Preservar explicitamente os esclarecimentos do Financeiro, inclusive ano digitado incompleto.
- Quando surgir identificador formal `OUV-NNNN` com outro especialista pendente, submeter a mensagem original ao Orquestrador com o histórico existente, sem concatenação de contexto financeiro/documents da intenção anterior.
- Separar consultas sobre procedimento de reembolso das consultas à situação de uma manifestação de reembolso; sem código, pedir número em vez de prometer pesquisa individual por descrições vagas.

### Instalação
O ZIP contém caminhos relativos à **raiz do projeto** (`app/`, `frontend/`, `scripts/`, `tests/`, `docs/`). Extraia-o em `H:\Meu Drive\Desafio IA Areco\areco-multiagentes-fundacao`, mantendo `.env` e `data/` existentes. Faça cópia de segurança se tiver alterações locais nos arquivos substituídos. Não extraia um nível acima da pasta do projeto.

### Validação no PowerShell
```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"

docker compose up --build --force-recreate -d
& $py .\scripts\check_frontend_continuity_sdk_http.py --scenario frontend
& $py .\scripts\check_frontend_continuity_sdk_http.py --scenario switch
& $py .\scripts\check_frontend_continuity_sdk_http.py --scenario finance
```
Cada cenário faz chamadas REAIS à API da OpenAI (8 + 4 + 3 turnos) e consome tokens. Recomenda-se rodar primeiro apenas `frontend` e avaliar o resultado antes de executar os outros.

### Cobertura e limites
27 testes locais offline e 28 testes do avaliador foram aprovados na cópia incremental. Não foi possível validar a LLM real/Docker aqui. `F06` deve consultar `OUV-0016` em `manifestacoes.csv` com status “Aguardando área responsável”; `F08` deve citar prioridade “Média”. As respostas devem ser revisadas semanticamente.
