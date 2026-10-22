# Validação de reprodução por clone limpo — Areco v0.2.35

**Situação:** VALIDADA pelo candidato em clone independente no Windows em 22/10/2026. O roteiro e o registro de evidência estão abaixo. Esta validação não garante execução em todos os sistemas operacionais.

## Pré-requisitos

- Conta GitHub com acesso ao repositório privado.
- Git, Docker Desktop/Compose v2, internet, porta `127.0.0.1:8000` disponível e chave OpenAI válida com créditos.
- Ambiente de trabalho separado da pasta anterior para não aproveitar bancos, cache, `.venv` ou `.env` do projeto existente.

## Passos (PowerShell em Windows)

```powershell
# Escolha uma pasta de teste fora da pasta original e fora do Google Drive.
New-Item -ItemType Directory -Force "$env:TEMP\areco-clone-validation" | Out-Null
Set-Location "$env:TEMP\areco-clone-validation"

git clone https://github.com/devikin/areco-multiagentes-fundacao.git
Set-Location .\areco-multiagentes-fundacao

git branch --show-current
# Antes de criar .env: validar que há somente o exemplo sem chave.
git ls-files -- .env
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
# Preencha OPENAI_API_KEY localmente, sem expor o valor em logs/screenshots.

# Parar a aplicação antiga se estiver ocupando 127.0.0.1:8000.
docker compose -p areco_clone_validation up --build -d
docker compose -p areco_clone_validation ps
Invoke-RestMethod http://127.0.0.1:8000/health
```

Abrir `http://127.0.0.1:8000/`, efetuar consultas dos três domínios, observar fonte/resultado e conferir console/logs sem divulgar segredos. **A execução real com OpenAI consome tokens.**

Ao terminar:

```powershell
docker compose -p areco_clone_validation down
# Não executar down -v se desejar preservar o banco do teste; a validação não exige removê-lo.
```

## Validação real observada — 22/10/2026

**Fonte da evidência:** execução PowerShell e testes manuais comunicados pelo candidato, na pasta temporária de auditoria (`%TEMP%\areco-clone-auditoria-v035`), fora da pasta original sincronizada.

- **Clone:** candidato confirmou que clonou o repositório privado e iniciou a aplicação a partir dessa cópia independente. O hash exato de `HEAD` no clone **não foi informado** nesta verificação; o commit remoto observado anteriormente era `88e42fa234a9e5b9997b368f05bee1ac6c1a0204`.
- **Inicialização:** `docker compose -p areco_clone_validation up --build -d`; o candidato confirmou sucesso. A saída enviada de `docker compose -p areco_clone_validation ps` mostrou o serviço `app` em estado **`Up ... (healthy)`**, com a porta exposta exclusivamente em `127.0.0.1:8000->8000/tcp`.
- **Saúde HTTP:** `Invoke-RestMethod http://127.0.0.1:8000/health` retornou `status=ok`, `engine=sdk`, `loaded_agents={financeiro, informacoes_internas, ouvidoria}`.
- **Validação funcional:** o candidato confirmou que realizou testes de conversação via navegador e consultas bem-sucedidas às **três** bases de conhecimento (Financeiro, Informações Internas e Ouvidoria).
- **Alterações exigidas para executar:** nenhuma correção de código ou documentação foi reportada pelo candidato durante este teste.
- **Resultado:** **APROVADO no ambiente Windows/Docker testado**. O procedimento documentado no `README.md` permitiu colocar a aplicação em funcionamento a partir de um clone limpo.

**Limites da evidência:** a saída do terminal comprova container saudável, bind local e os agentes listados; a validação das respostas nos três domínios foi comunicada pelo candidato, sem anexar nesta etapa o conteúdo de cada resposta nem os `trace_id`. Não inferir acurácia universal, tempos de resposta ou compatibilidade com outra máquina. A conversa usa API OpenAI e requer chave própria do avaliador.

## Evidências complementares opcionais

Caso seja solicitado pelo avaliador, podem ser acrescentados o SHA exato do clone (`git rev-parse HEAD`), versões do Docker/Compose, exemplos de consultas e seus `trace_id`, sem divulgar dados pessoais ou segredos. Esses detalhes **não foram fornecidos** na confirmação atual.

O registro acima preserva as evidências efetivamente comunicadas pelo candidato. Não substitui a inspeção dos traces detalhados, caso a avaliação os solicite.
