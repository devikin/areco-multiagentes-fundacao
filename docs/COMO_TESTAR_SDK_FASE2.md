> **ARQUIVO HISTÓRICO:** não descreve a arquitetura SDK-only v0.2.6. Consulte README.md.

# Fase 2 — Agents SDK no FastAPI (implementado, teste real pendente)

## Pré-requisitos
- Aplicar patch sobre a **v0.2.3 ou v0.2.4**; o patch inclui
  `app/agents/finance_tools.py`, mas não sobrescreve `finance.py` legado.
- Parar o servidor antigo (CTRL+C); não executar duas instâncias na mesma porta.
- `.env` com OPENAI_API_KEY válida e OPENAI_MODEL=gpt-4o-mini.
- O `poc_agents_sdk` da Fase 1 pode continuar no repositório; não é importado pelo backend.

## Instalação segura (Windows PowerShell)

Na pasta `H:\Meu Drive\Desafio IA Areco\areco-multiagentes-fundacao`:

```powershell
$venv = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv"
$py = Join-Path $venv 'Scripts\python.exe'
& $py -m pip install -r .\requirements-sdk.txt
```

Essa é a venv criada na Fase 1. Ela contém Agents SDK, mas pode não conter
FastAPI/Uvicorn; `requirements-sdk.txt` instala as duas camadas na venv isolada.
Não execute esta instalação na `.venv` antiga.

No `.env` existente, **adicione**:

```ini
AGENT_ENGINE=sdk
```

Mantenha `.env` fora do Git, nunca compartilhe a chave. Inicie com:

```powershell
& $py -m uvicorn app.main:app --reload
```

Acesse `http://127.0.0.1:8000/health`; procure `"engine": "sdk"` e três agentes.
O frontend continua em `http://127.0.0.1:8000/`.

## Teste HTTP real (3 perguntas)

Em **outro** PowerShell, no mesmo diretório, rode:

```powershell
$py = Join-Path "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv" 'Scripts\python.exe'
& $py .\scripts\check_sdk_http.py
```

O script envia três perguntas reais. Critérios: handoff nativo, ferramenta,
fonte, resposta e trace_id em cada chamada. O resultado financeiro esperado é
R$ 305.937,01. **Não declare validado antes de executá-lo no Windows.**

Os registros do FastAPI incluem `engine`, `trace_id`, `handoffs`, `tools_used`,
`token_usage`, `classification_method` e `generation_method`. Não gravam a
pergunta completa por padrão. No painel da OpenAI, busque o workflow
`Areco | FastAPI Agents SDK - Fase 2`.

## Reversão imediata

Pare o Uvicorn, altere `.env` para `AGENT_ENGINE=legacy` e reinicie com a
venv anterior:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

O arquivo SQLite, a interface, as bases e o serviço legado são preservados.
**Não há fallback silencioso entre arquiteturas**: erros de API/SDK devolvem
HTTP 503 para investigação, mantendo a rastreabilidade.

## Limitações e riscos

- Testes locais desta alteração utilizaram SDK SIMULADO; a PoC real da
  Fase 1 foi validada pelo usuário (três traces fornecidos), mas esta
  integração FastAPI ainda precisa ser validada com OpenAI ao vivo.
- `FinancePlan` da v0.2.4 é reutilizado, não SQL livre.
- Informações Internas usa BM25; sem banco vetorial externo.
- Ouvidoria aceita protocolos exatos, lista de status e contagem total;
  filtros avançados ficam para uma etapa seguinte.
- A API é stateless; session_id permanece sem armazenamento multi-turno.
- O `confidence=0.0` no SDK significa **sem escore calibrado disponível**,
  não confiança calculada como zero.
- O Dockerfile atual instala só requirements.txt e inicia no modo `legacy`;
  imagem Docker com SDK será configurada/validada na Fase 3.
- Traces omitem entrada/saída sensível dos spans. Ainda são exportados
  metadados para OpenAI; dados originais do desafio são sintéticos.
- SDK depende de chamadas pagas à OpenAI. Mantenha baixo volume de testes.
