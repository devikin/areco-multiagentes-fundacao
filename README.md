# Areco — Assistente Multiagente (OpenAI Agents SDK)

**Versão candidata à entrega: v0.2.35 (reconexão segura antes do envio).** O comportamento dos agentes é o mesmo da **v0.2.32**, validada pelo candidato no Windows/Docker com a OpenAI real. Esta é uma prova de conceito com **dados sintéticos**, não um serviço de produção.

## Visão geral

- **Backend:** Python 3.12, FastAPI, Pydantic e OpenAI Agents SDK.
- **Orquestrador:** classifica o pedido com base no histórico e faz handoff nativo para Financeiro, Informações Internas ou Ouvidoria.
- **Financeiro:** ferramenta `consultar_financeiro`, consultas SQL parametrizadas e cálculos com `Decimal`.
- **Informações Internas:** `buscar_documentos`, recuperação BM25 de documentos e FAQ com fonte/versão.
- **Ouvidoria:** `buscar_protocolo`, `consultar_manifestacoes` e `listar_status_ouvidoria`; protocolos `OUV-NNNN` são consultados na base estruturada.
- **Frontend:** HTML, CSS e JavaScript; sessão distinta por aba, mensagens exibidas como texto, sem renderizar HTML ou Markdown recebido do modelo.
- **Modelo:** `gpt-4.1-mini` no `.env.example` e como padrão do backend; `OPENAI_MODEL` pode ser alterado. Consultas reais à API OpenAI consomem tokens.

## Como executar — Docker (recomendado)

Requer Docker Desktop com Docker Compose v2, acesso à internet e uma chave OpenAI autorizada. Na raiz do projeto:

```powershell
# Se ainda não houver um arquivo .env, crie a partir do exemplo.
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
# Preencha OPENAI_API_KEY; NÃO versione o .env.
docker compose up --build -d
docker compose ps
```

Aguarde o estado `healthy`. Acesse:

- Interface: http://127.0.0.1:8000/
- Saúde da API: http://127.0.0.1:8000/health
- Documentação FastAPI: http://127.0.0.1:8000/docs

O Compose publica apenas `127.0.0.1:8000`, utiliza um volume Docker para SQLite e oferece healthcheck. Encerramento: `docker compose down` (sem `-v` para preservar o volume). Caso a porta 8000 esteja em uso, encerre o Uvicorn local antes de iniciar o container.

## Alternativa sem Docker — Python no Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
# Crie .env apenas se ainda não existir; preencha sua chave localmente.
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Por padrão, a base SQLite no Windows fica em `%LOCALAPPDATA%\ArecoMultiagentes\knowledge.sqlite` para evitar bloqueios em pastas sincronizadas. Nunca inclua `.env`, tokens ou dados privados no pacote de entrega.

## Testes e evidências

```powershell
$py = "$env:LOCALAPPDATA\ArecoMultiagentes\agents-sdk-venv\Scripts\python.exe"
& $py -m pytest -q
& $py -m pytest -q .\tests\test_frontend_resilience_v033.py .\tests\test_draft_preservation_v034.py
# Opcional, se Node.js estiver instalado; sem dependências npm e sem OpenAI:
node .\tests\test_reconnect_browser_v035.cjs
& $py .\scripts\check_ui_version_http.py
```

Os comandos acima não precisam fazer chamadas à OpenAI; o teste de UI verifica que a versão servida corresponde ao container atualizado. Se o `$py` não existir, use `.\.venv\Scripts\python.exe` ou um Python 3.12 com `requirements-dev.txt` instalados.

**Testes com GPT-4.1 mini real já validados pelo candidato:**

| Suite | Resultado observado | Evidência |
|---|---|---|
| Avaliação oficial (v0.2.27; revisão manual dos 2 REVIEW) | 12/12 aceitos | `docs/evidence/quality_official_20261021T220227Z.json` |
| Continuidade no frontend (v0.2.31) | 8/8 PASS | `docs/evidence/continuity_frontend_20261022T022908Z.json` |
| Alternância de domínios (v0.2.31) | 4/4 PASS | relatório gerado pelo script `--scenario switch` em `docs/evidence/` |
| Esclarecimento financeiro (v0.2.31) | 3/3 PASS | relatório gerado pelo script `--scenario finance` em `docs/evidence/` |
| Saudação natural (v0.2.32) | 4/4 PASS + frontend verificado manualmente | `docs/evidence/greeting_20261022T142616Z.json` |

Não confundir avaliações pontuais aprovadas com garantia de segurança ou confiabilidade universal. Testes de conversação com OpenAI real **consomem tokens**. **Em 22/10/2026, o candidato confirmou a reconexão da v0.2.35 no Docker/Windows e executou `python -m pytest -q`: 137 passed em 6,74 s.** A captura de tela comprova o estado visual de reconexão, não a contagem de requisições HTTP. Os agentes e as ferramentas não foram alterados na v0.2.35. Consulte [validação da entrega](docs/RELEASE_VALIDATION_v0.2.35.md).

## Comportamento conversacional e limites

- O frontend apresenta uma única saudação de abertura. A LLM responde naturalmente sem repeti-la automaticamente.
- Cada aba usa um `session_id` novo. O histórico em memória mantém até 30 trocas recentes e expira após 30 minutos sem atividade. Reinício do servidor/recarregamento da página inicia nova conversa.
- O frontend verifica `GET /health` antes de cada `POST /api/v1/chat`. Se o container já estiver indisponível, conserva **uma mensagem pendente em memória por aba**, bloqueia envios e mostra overlay com blur/animação, conferindo `/health` novamente a cada 3 segundos. Quando a API voltar saudável, envia a mensagem pendente **uma única vez**. O usuário pode cancelar a espera sem enviar, mantendo o texto no campo.
- **Segurança contra duplicidade:** se a API aparentar estar saudável mas o `POST` falhar ou exceder 120 segundos, não há retry automático porque a execução pode ter começado e consumido tokens. A pergunta permanece no campo para decisão de reenvio manual. Uma reconexão saudável não comprova que a OpenAI está operante.
- **Limites aceitos da alternativa A:** a mensagem pendente existe apenas na aba aberta, sem `localStorage` ou `sessionStorage`. Fechar ou atualizar a página perde a fila e reinicia a sessão; reiniciar o container perde o histórico volátil do servidor e não recupera respostas antigas nem execuções interrompidas. Não há persistência de requisições nem garantia de processamento exatamente uma vez em quedas de rede após o POST.
- Escopo restrito aos domínios corporativos e às fontes disponíveis. Nunca compartilhar senhas, chaves ou instruções internas; solicitações humanas são orientadas ao RH sem fingir uma transferência.
- **Sem autenticação/autorização** por usuário e sem persistência de sessões entre reinícios. Não expor o MVP na internet.
- Os dados são sintéticos e usados apenas para avaliação. Não publicar bases sem verificar permissão.
- Dependências atualmente usam intervalos em `requirements.txt`. Para reprodução estrita, registrar as versões instaladas no ambiente testado antes do envio final (ex.: `python -m pip freeze`) e testar qualquer arquivo de lock gerado; não inventar versões de pacotes.

## Como testar a reconexão (v0.2.35)

1. Com o frontend aberto em `http://127.0.0.1:8000`, interrompa o container sem fechar a aba.
2. Digite `ola bom dia` e clique em **Enviar**: o overlay deve aparecer, o botão de envio deve estar desabilitado, a pergunta preservada e **nenhum POST enviado enquanto `/health` estiver indisponível**.
3. Reinicie o container, confirme que o overlay desaparece e a mensagem é enviada uma única vez. A resposta da OpenAI consome tokens.
4. Repita o cenário offline e selecione **Cancelar espera**: o modal fecha, o texto permanece, e não deve ocorrer POST.
5. A comunicação pode cair entre a verificação de saúde e o POST; nesse caso, um aviso é exibido para reenvio manual, **sem retry automático**.

### Evidência visual da reconexão (22/10/2026)

![Modal de reconexão automática quando o backend está indisponível](docs/assets/reconexao_backend_offline_v0.2.35.png)

*Captura real da v0.2.35, validada manualmente pelo candidato no frontend.* Consulte [Evidência de reconexão](docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md) para os passos de reprodução, comportamento e limitações.

## Entrega e segurança Git

```powershell
git status --short
git check-ignore .env
git ls-files .env
git ls-files --others --exclude-standard
```

`git check-ignore .env` deve listar `.env`. `git ls-files .env` deve estar vazio. Se um segredo foi versionado no histórico, removê-lo do índice não o apaga de commits antigos: revogue/rotacione o segredo e trate o histórico antes de compartilhar.

## Arquivos de referência

- `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`: print do overlay e documentação do tratamento de indisponibilidade do backend.
- `docs/ARCHITECTURE.md`: arquitetura vigente.
- `docs/DELIVERY_CHECKLIST.md`: critérios de verificação e envio.
- `docs/RELEASE_VALIDATION_v0.2.35.md`: publicação GitHub, testes confirmados e pendências finais.
- `docs/DEVELOPMENT_LOG.md`, `docs/DECISIONS.md`: diário cronológico e decisões.
- `docs/EVALUATION_RESULTS_v0.2.13.md`: avaliação oficial histórica.
- `docs/ROADMAP.md`: melhorias futuras que não foram implementadas.
- `AGENTS.md`: convenções de engenharia do projeto.
