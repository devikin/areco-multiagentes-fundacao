# Checklist final de entrega — Areco v0.2.35

> Esta é a visão **atual** de entrega. Pendências de versões intermediárias são históricas e permanecem nos diários/commits, não como tarefas ainda abertas. As validações se referem às evidências fornecidas pelo candidato, incluindo execução independente em clone limpo no Windows em 22/10/2026; não são garantia universal de reprodução.

## Confirmado

- [x] Backend FastAPI, frontend HTML/CSS/JS e OpenAI Agents SDK como motor único com Orquestrador e três especialistas.
- [x] Bases sintéticas importadas para SQLite; consultas SQL parametrizadas, `Decimal` e recuperação documental BM25 com fontes.
- [x] Docker/Windows executado pelo candidato com container `healthy` e testes HTTP reais dos três domínios.
- [x] Avaliação oficial v0.2.27: 10 PASS automáticos, 2 REVIEW posteriormente analisados/aceitos manualmente (12/12); os relatórios brutos preservam sua classificação original.
- [x] Continuidade frontend v0.2.31: 8/8; alternância de domínios: 4/4; esclarecimentos financeiros: 3/3; saudação natural v0.2.32: 4/4.
- [x] Reconexão v0.2.35 validada manualmente no navegador, com imagem e procedimento. Testes automatizados da lógica também presentes.
- [x] Suíte Pytest completa executada pelo candidato em Windows: **137 passed in 6.74s**.
- [x] Git inicializado, `.env` ignorado e ausente no GitHub; commit inicial publicado no repositório **privado** `devikin/areco-multiagentes-fundacao` (branch `main`).
- [x] Estrutura de rastreabilidade: `request_id`, `trace_id`, fontes, handoffs, ferramentas e tokens em resposta/logs.
- [x] Anotações pessoais transcritas em 22/10/2026 e vinculadas cronologicamente aos registros técnicos (sem inventar datas de cada decisão).
- [x] Índice de uso da IA e instruções do agente organizados para revisão dos avaliadores.

## Ainda precisa de confirmação antes de entregar

- [x] **Clone limpo (22/10/2026):** execução independente no Windows/Docker validada pelo candidato, container `healthy`, `/health` com três agentes SDK e consultas pelo chat às três bases; detalhes em `docs/CLONE_VALIDATION.md`.
- [ ] **Reprodutibilidade:** identificar e validar resolução das versões de dependências num build novo; `requirements.txt` tem intervalos amplos, sem arquivo lock. Não inventar versões nem prometer instalação idêntica em todos os ambientes.
- [ ] **Rastreabilidade conversacional:** obter a exportação ZIP da sessão, selecionar o chat correto, conferir dados antes de publicar e produzir referência legível em `docs/ai_interactions/`.
- [ ] **Evidências específicas:** se a avaliação exigir confirmação empírica de um único POST após reconexão, verificar logs/DevTools; screenshot não prova a quantidade de requisições.
- [ ] **Compartilhamento:** confirmar se as bases fictícias podem ser compartilhadas e definir como conceder acesso à Areco ao repo privado ou fornecer pacote aprovado.
- [ ] **Versão final:** revisar `git diff`, validar caminhos/links e ausência de segredos, realizar último commit e **somente então** criar/publicar a tag anotada `v0.2.35`.

## Demonstração recomendada (3–5 minutos)

1. Mostrar execução no Docker e `/health`.
2. Realizar uma pergunta em Financeiro (montante/orçamento com período), uma sobre política interna e outra sobre protocolo `OUV-0016`.
3. Mostrar `request_id`, `trace_id`, handoffs, ferramentas e fontes; explicar que o modelo decide o direcionamento e ferramentas garantem o dado recuperado.
4. Abrir `docs/AI_USAGE.md` → `docs/DECISOES_PESSOAIS.md` → diário técnico → ADRs → testes; mostrar ao menos um bug encontrado e corrigido com auxílio de IA.
5. Expor honestamente limites: aplicação local sem autenticação; estado de conversa volátil; sem idempotência de POST já iniciado.

## Documentos principais

- Entrada de avaliadores: [`../README.md`](../README.md)
- Instruções atuais do agente: [`../AGENTS.md`](../AGENTS.md)
- Decisões do candidato: [`DECISOES_PESSOAIS.md`](DECISOES_PESSOAIS.md)
- Uso responsável da IA: [`AI_USAGE.md`](AI_USAGE.md)
- Diário e decisões: [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md), [`DECISIONS.md`](DECISIONS.md)
- Validação e clone: [`RELEASE_VALIDATION_v0.2.35.md`](RELEASE_VALIDATION_v0.2.35.md), [`CLONE_VALIDATION.md`](CLONE_VALIDATION.md)
