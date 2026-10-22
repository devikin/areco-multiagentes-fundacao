# Checklist final — entrega Areco v0.2.35

## Já confirmado pelo candidato

- [x] Agents SDK como motor único, 1 Orquestrador e 3 especialistas.
- [x] Docker executou no Windows com container healthy e backend FastAPI acessível.
- [x] Suíte oficial: 12 casos aprovados após revisão humana dos 2 REVIEW.
- [x] Continuidade do frontend: 8/8; alternância de domínios: 4/4; continuidade financeira: 3/3.
- [x] Saudação natural: 4/4 com GPT-4.1 mini real + inspeção manual no frontend (v0.2.32).

## Verificações finais — estado de 22/10/2026

- [x] Testes completos no Windows: **137 passed in 6.74s**, `python -m pytest -q` (saída compartilhada pelo candidato).
- [x] Git inicializado, commit criado e `main` publicada no GitHub.
- [x] Repositório `devikin/areco-multiagentes-fundacao` confirmado como **private** pela API GitHub.
- [x] `.env` ignorado localmente e ausente da branch principal remota; `.env.example` contém chave vazia.
- [x] Os arquivos essenciais do backend, frontend, testes, Docker e avaliação oficial foram localizados no GitHub.
- [x] A reconexão v0.2.35 foi validada manualmente no navegador com captura anexada.
- [ ] Confirmar qual canal de entrega a Areco aceita e compartilhar apenas com avaliadores autorizados (convite GitHub ou arquivo compactado).
- [ ] Confirmar autorização para compartilhamento do pacote sintético recebido, mantendo-o em repositório privado até lá.
- [ ] Se for exigida reprodução estrita, registrar as versões instaladas do Python/SDK e verificar um build novo; `requirements.txt` contém intervalos.

## Demonstração recomendada (3 minutos)

1. `docker compose up --build -d` e `docker compose ps`.
2. Abrir http://127.0.0.1:8000/ e mostrar três domínios.
3. Exibir uma consulta à Ouvidoria `OUV-0016` com fonte e trace.
4. Mostrar resposta sobre política de férias e orçamento por departamento.
5. Apresentar README, arquitetura e resultados reais de teste.

**Limite:** demonstração local sem autenticação; nunca exponha a PoC diretamente na internet. Timeout no browser não comprova que a execução foi cancelada no servidor.


## v0.2.35 — Reconexão antes do envio

- [x] Testes locais da lógica de reconexão (sem OpenAI): servidor online, espera offline, cancelamento e POST incerto.
- [x] Candidato validou manualmente o fluxo de reconexão no frontend com captura visual do overlay/blur em 22/10/2026. Evidência: `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`.
- [ ] Se necessário para auditoria de entrega, confirmar nos logs que a reconexão causou **somente um POST**; a captura não comprova essa quantidade.
- [ ] Testar Cancelar espera sem POST automático, com pergunta preservada no input.
- [ ] Confirmar que falha de POST já iniciado **não** produz reenvio automático.
- [x] Executar `python -m pytest -q` no projeto completo: **137 passed in 6.74s** em 22/10/2026.

**Limitação deliberada:** fila por aba, sem persistência após reload e sem recuperação de histórico após reinício do backend.


### Registro visual de validação — 22/10/2026

- [x] Print original anexado em `docs/assets/reconexao_backend_offline_v0.2.35.png`.
- [x] Procedimento e limites documentados em `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`.
- [x] Teste manual de reconexão aprovado pelo candidato.
- [x] Pytest concluído no Windows e repositório privado/branch principal verificados após publicação.

### Observação de evidências

As 137 aprovações são de testes locais/offline (não equivalem a 137 chamadas reais ao SDK). A quantidade exata de POSTs após reconexão e os cenários de cancelamento/queda durante POST não foram comprovados por logs enviados nesta conversa; manter essas verificações separadas.
