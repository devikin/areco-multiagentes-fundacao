# Como a IA foi utilizada no desenvolvimento — roteiro para a avaliação da Areco

## 1. Papel humano e papel da IA

A IA apoiou análise dos requisitos, propostas de arquitetura, escrita e revisão de código, produção de testes, interpretação de logs e geração de documentação. **O candidato** trouxe problemas encontrados no Windows, testou o frontend e o chat real, conferiu respostas nas bases, questionou comportamentos, escolheu mudanças de escopo e aprovou ou rejeitou abordagens. Uma sugestão escrita pela IA não deve ser atribuída automaticamente ao candidato.

O projeto foi iterativo, não uma geração única de código. Mudanças foram avaliadas com testes offline, chamadas HTTP/Docker, execução com OpenAI real, revisão manual de respostas e, por fim, 137 testes Pytest aprovados no Windows.

## 2. Por onde começar a auditoria

| O que avaliar | Evidência navegável |
|---|---|
| Anotações pessoais, em ordem histórica | [`DECISOES_PESSOAIS.md`](DECISOES_PESSOAIS.md) |
| Diário técnico, problemas e correções | [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md) |
| Decisões e alternativas | [`DECISIONS.md`](DECISIONS.md) |
| Instruções fornecidas ao agente desde o início | [`../AGENTS.md`](../AGENTS.md) e [`AGENTS_HISTORY.md`](AGENTS_HISTORY.md) |
| Prompt inicial preservado | [`ai_interactions/2026-10-20-prompt-inicial.txt`](ai_interactions/2026-10-20-prompt-inicial.txt) |
| Transcrições integrais da sessão | [`ai_interactions/README.md`](ai_interactions/README.md) |
| Arquitetura e ferramentas vigentes | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Testes e publicação | [`RELEASE_VALIDATION_v0.2.35.md`](RELEASE_VALIDATION_v0.2.35.md), [`evidence/`](evidence/) |

## 3. Estudos de caso: colaboração humano–IA

### Caso A — Ambiente real revelou falha no SQLite
- **Observação do candidato:** falha de inicialização em pasta sincronizada no Windows.
- **Análise da IA:** a conexão SQLite não era explicitamente fechada antes de substituir o arquivo temporário; armazenamento em pasta sincronizada agravava o problema.
- **Correção efetiva:** fechamento explícito e caminho local em `%LOCALAPPDATA%`.
- **Evidências:** diário, entrada 004; ADR-0006; testes de ingestão e API.

### Caso B — Roteamento correto não garantiu cálculo correto
- **Observação do candidato:** uma pergunta sobre quantidade de manifestações Alta retornou 180 em vez de 38.
- **Análise da IA:** duas ferramentas concorriam, e o agente escolhia a contagem total sem filtros.
- **Correção efetiva:** unificação das agregações filtradas em ferramenta adequada e validação de plano.
- **Evidências:** `development_entries/2026-10-20-ouvidoria-tools-v0.2.8.md` e diário, entrada 009.

### Caso C — O problema conversacional não era apenas o prompt
- **Observações do candidato:** resposta determinística, linguagem técnica, perda de contexto e repetição de menus/loops em múltiplos turnos.
- **Decisão humana:** revisar o quanto o backend moldava ou substituía a conversação.
- **Redesenho:** prompt mais conciso; a LLM produz o texto visível; o backend conserva ferramentas, guardrails e isolamento da sessão.
- **Evidências:** `development_entries/2026-10-21-redesign-v0.2.24.md`, diário e anotações pessoais P04, P06–P10.

### Caso D — Correção do entendimento de linguagem natural nas bases
- **Observação do candidato:** consulta informal sobre férias retornava ausência de fonte apesar de o documento existir.
- **Diagnóstico:** a estratégia BM25 penalizava termos introdutórios da pergunta; depois foi reforçada com normalizações documentais.
- **Evidências:** `development_entries/2026-10-20-conversacional-v0.2.16.md`, `development_entries/2026-10-21-guardrails-v0.2.28.md`, anotações P05.

### Caso E — Continuidade, segurança e tolerância a falhas
- **Observações do candidato:** erro de ano `205`, respostas técnicas, mudança de assunto, tentativa de pedir credenciais/prompts e perda de conexão com backend.
- **Respostas do processo:** validação e correção contextual de parâmetros; ajustes nos handoffs/guardrails; reconexão visual com pré-checagem `/health`, sem retry automático de POST incerto.
- **Evidências:** `development_entries/2026-10-21-entradas-invalidas-v0.2.22.md`, `development_entries/2026-10-21-guardrails-v0.2.28.md`, `EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md`, anotações P08, P11, P12.

## 4. Regra de honestidade das evidências

- `docs/DECISOES_PESSOAIS.md` foi consolidado retrospectivamente a partir de notas do candidato. **Não** equivale à transcrição literal de interações passadas.
- Logs técnicos podem conter propostas preliminares substituídas. A arquitetura **vigente** está em `AGENTS.md`, `ARCHITECTURE.md` e código.
- Teste mockado não é chamada ao GPT-4.1 mini; `REVIEW` demanda inspeção humana; captura visual não prova quantidade de POSTs.
- As duas exportações integrais da mesma sessão, em Markdown e TXT, foram adicionadas sem modificação ao diretório `docs/ai_interactions/`. O índice da pasta fornece links e hashes SHA-256; os relatos retrospectivos em `DECISOES_PESSOAIS.md` continuam distintos da transcrição literal.
- Não versionar `.env`, tokens, senhas ou banco runtime. Esta aplicação permanece demonstrativa e local.

## 5. Formato recomendado de novos registros

**Etapa/data → solicitação/prompt (ou referência verificável) → proposta da IA → intervenção/decisão humana → arquivos alterados → validação efetivamente executada → resultado/limitações → referência ao relatório ou commit.**

Documente o resultado que aconteceu, mesmo quando houve erro ou mudança de hipótese. Essas correções são parte central da avaliação de uso responsável da IA.
