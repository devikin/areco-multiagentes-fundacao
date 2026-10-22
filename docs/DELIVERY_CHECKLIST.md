# Checklist final — entrega Areco v0.2.35

## Já confirmado pelo candidato

- [x] Agents SDK como motor único, 1 Orquestrador e 3 especialistas.
- [x] Docker executou no Windows com container healthy e backend FastAPI acessível.
- [x] Suíte oficial: 12 casos aprovados após revisão humana dos 2 REVIEW.
- [x] Continuidade do frontend: 8/8; alternância de domínios: 4/4; continuidade financeira: 3/3.
- [x] Saudação natural: 4/4 com GPT-4.1 mini real + inspeção manual no frontend (v0.2.32).

## Pendente na v0.2.34

- [ ] Instalar patch, reconstruir container e verificar `healthy`.
- [ ] Executar `python -m pytest -q` com o projeto completo.
- [ ] Inspecionar frontend após atualização: sucesso normal, erro 503, timeout e pergunta restaurada sem retry automático.
- [ ] Confirmar HTML e FastAPI exibem a mesma versão v0.2.34; atualizar a página com Ctrl+F5.
- [ ] Validar consulta sem dados sensíveis após o patch. Não é necessário repetir toda a bateria paga sem regressão.
- [ ] Auditar `git status`, `.gitignore`, `.dockerignore`, arquivos `.env`, banco runtime, logs e histórico de commits.
- [ ] Registrar `pip freeze` do Python usado na validação e revisar resolução de dependências; não trocar por versões inventadas.
- [ ] Conferir que a documentação, scripts usados e as evidências têm nomes e caminhos existentes no pacote.
- [ ] Decidir se o repositório deve permanecer privado e confirmar autorização para compartilhar bases fictícias recebidas.

## Demonstração recomendada (3 minutos)

1. `docker compose up --build -d` e `docker compose ps`.
2. Abrir http://127.0.0.1:8000/ e mostrar três domínios.
3. Exibir uma consulta à Ouvidoria `OUV-0016` com fonte e trace.
4. Mostrar resposta sobre política de férias e orçamento por departamento.
5. Apresentar README, arquitetura e resultados reais de teste.

**Limite:** demonstração local sem autenticação; nunca exponha a PoC diretamente na internet. Timeout no browser não comprova que a execução foi cancelada no servidor.


## Validação de falha de rede — v0.2.34
- [ ] Com a aba aberta, parar container e enviar pergunta: texto permanece visível no campo.
- [ ] Tentar enviar novamente ainda sem servidor: texto continua visível, sem retry automático.
- [ ] Iniciar o container e clicar Enviar manualmente: resposta confirmada limpa o campo.
- [ ] Recarregar página inicia sessão nova, sem recuperação automática de histórico/resposta; comportamento documentado.


## v0.2.35 — Reconexão antes do envio

- [x] Testes locais da lógica de reconexão (sem OpenAI): servidor online, espera offline, cancelamento e POST incerto.
- [x] Candidato validou manualmente o fluxo de reconexão no frontend com captura visual do overlay/blur em 22/10/2026. Evidência: `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`.
- [ ] Se necessário para auditoria de entrega, confirmar nos logs que a reconexão causou **somente um POST**; a captura não comprova essa quantidade.
- [ ] Testar Cancelar espera sem POST automático, com pergunta preservada no input.
- [ ] Confirmar que falha de POST já iniciado **não** produz reenvio automático.
- [ ] Executar `python -m pytest -q` no projeto completo e revisar saída antes da entrega.

**Limitação deliberada:** fila por aba, sem persistência após reload e sem recuperação de histórico após reinício do backend.


### Registro visual de validação — 22/10/2026

- [x] Print original anexado em `docs/assets/reconexao_backend_offline_v0.2.35.png`.
- [x] Procedimento e limites documentados em `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`.
- [x] Teste manual de reconexão aprovado pelo candidato.
- [ ] Reexecutar o pytest final no Windows e auditar o estado real do repositório Git antes da publicação.
