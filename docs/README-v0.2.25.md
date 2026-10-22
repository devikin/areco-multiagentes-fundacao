# Patch incremental v0.2.25 — Continuidade de esclarecimentos

Aplicar SOMENTE sobre a instalação v0.2.24 já funcional. O ZIP preserva `.env`, `.venv`, bases sintéticas, Docker e arquivos de outros módulos.

No PowerShell, estando em `H:\Meu Drive\Desafio IA Areco\areco-multiagentes-fundacao`:

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
docker compose up --build --force-recreate -d
docker compose ps
& $py .\scripts\check_redesign_sdk_http.py
```

O script usa o modelo `OPENAI_MODEL` já configurado no `.env` (gpt-4.1-mini no ambiente do usuário) e faz nove perguntas reais; algumas perguntas fazem múltiplas chamadas à OpenAI.

**O que considerar aprovado:** após `despesas por departamento` → `205` → `2025`, a resposta de `2025` deve ter `domain=financeiro`, ferramenta `consultar_financeiro`, fonte `lancamentos_financeiros.csv`, valores agrupados por departamento e ano 2025. O script agora falha explicitamente quando o agente retorna apenas um novo pedido de confirmação.

O backend não substitui a resposta do modelo, não trata anos com regex nem fornece textos fixos de fallback. A guarda e as operações de consulta permanecem no código tipado das ferramentas; o especialista controla o esclarecimento via continuidade nativa do Agents SDK. Novo assunto pode voltar ao Orquestrador por handoff.

Testes locais usam FakeRunner e só exercitam a lógica do serviço; resultados reais de OpenAI/Docker ainda não foram obtidos neste pacote.
