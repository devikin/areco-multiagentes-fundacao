# Decisões e observações pessoais do candidato — Desafio Areco

**Fonte:** anotações próprias transcritas pelo candidato em 22/10/2026, posteriormente ao desenvolvimento. Este documento apresenta os relatos em **ordem das etapas do projeto**, relacionando-os a registros técnicos existentes. **Não é uma transcrição contemporânea de cada interação nem presume que cada decisão tenha sido tomada exatamente na data do patch correspondente.** As datas e versões indicam apenas a etapa técnica corroborada pela documentação.

As observações entre aspas preservam a voz pessoal, com ajustes mínimos de ortografia. Os vínculos técnicos são contextualizações documentais, não novas afirmações do candidato.

## 20/10/2026 — Preparação e primeiros testes

### P01 — Apresentação do desafio e definição das responsabilidades

> Informei o contexto e a complexidade do desafio à IA para me ajudar a decidir partes técnicas.

- **Intervenção humana:** apresentei as condições do teste e orientei a IA na análise da solução.
- **Registro técnico associado:** `docs/DEVELOPMENT_LOG.md`, entrada 001; `docs/PLAN.md`; `docs/ai_interactions/2026-10-20-prompt-inicial.txt`.
- **Aprendizado evidenciado:** partir do problema e do prazo, não de uma tecnologia previamente escolhida.

### P02 — Falha no primeiro deploy local / inicialização do SQLite

> No primeiro deploy da aplicação houve uma falha no banco SQLite, e nós a corrigimos.

- **Intervenção humana:** executei a aplicação, observei a falha real no Windows e trouxe o erro para diagnóstico.
- **Registro técnico associado:** `docs/DEVELOPMENT_LOG.md`, entrada 004; `docs/DECISIONS.md`, ADR-0006.
- **Resultado documentado:** conexão encerrada explicitamente antes da substituição do banco temporário; SQLite passou a usar diretório local fora da pasta sincronizada do Google Drive.

### P03 — Conferência manual de respostas contra as bases

> Na primeira validação das respostas dos agentes, verifiquei manualmente as bases de conhecimento para garantir que as respostas fornecidas pelo modelo durante o chat estavam corretas.

- **Intervenção humana:** conferi afirmações da IA nas fontes, em vez de aceitar respostas plausíveis apenas pelo texto.
- **Registro técnico associado:** `docs/KNOWLEDGE_AUDIT.md`, `docs/DEVELOPMENT_LOG.md`, entradas 010–012, `docs/EVALUATION_RESULTS_v0.2.13.md` e `docs/evidence/`.
- **Limite:** esta anotação descreve validação manual de respostas observadas, não auditoria de todas as respostas possíveis.

### P04 — Respostas pouco naturais e determinísticas

> Durante a avaliação da qualidade das respostas humanizadas, percebi que estavam muito determinísticas e sem fluidez de uma conversa natural. Decidi revisar para identificar o motivo.

- **Intervenção humana:** avaliei a experiência do chat para além dos critérios de classificação e exatidão factual.
- **Registro técnico associado:** `docs/development_entries/2026-10-20-conversacional-v0.2.16.md`, `docs/DEVELOPMENT_LOG.md`, entrada 015.

### P05 — Recuperação textual excessivamente literal

> Decidi melhorar a recuperação textual para evitar erros de não encontrar informações na base de conhecimento; o agente estava muito literal e não identificava a semântica de algumas palavras.

- **Intervenção humana:** identifiquei perguntas naturais que tinham resposta documental, mas não recuperavam a fonte.
- **Registro técnico associado:** `docs/development_entries/2026-10-20-conversacional-v0.2.16.md` (caso de férias com termos introdutórios) e `docs/development_entries/2026-10-21-guardrails-v0.2.28.md` (normalização e melhoria da recuperação BM25).
- **Limite técnico:** o recuperador continua lexical/BM25 com normalizações; não se tornou busca vetorial semântica.

### P06 — Primeira estrutura de agentes conversacionais

> Conseguimos ajustar uma primeira versão de agentes conversacionais e toda a sua estrutura.

- **Intervenção humana:** acompanhei a primeira evolução para conversação mais natural e avaliei seu comportamento.
- **Registro técnico associado:** `docs/DEVELOPMENT_LOG.md`, entradas das versões v0.2.16 a v0.2.18, e `docs/DECISIONS.md`, ADR-0013/0014.

## 20–21/10/2026 — Continuidade, entrada e redesenho conversacional

### P07 — Loops, memória e perda de contexto

> Depois de alguns testes de chat com o agente orquestrador, percebi a conversa ainda muito engessada, pouco humanizada, truncada, com loops, falta de coerência em alguns casos e comportamento estranho de memória. Iniciei uma otimização considerando essas demandas.

- **Intervenção humana:** testei conversas com vários turnos e mudanças de assunto; identifiquei problemas não revelados por perguntas isoladas.
- **Registro técnico associado:** `docs/DEVELOPMENT_LOG.md`, versões v0.2.18–v0.2.20; `docs/DECISIONS.md` e `docs/development_entries/` correspondentes.
- **Aprendizado:** boa classificação de uma pergunta isolada não garante continuidade de uma conversa.

### P08 — Erros de digitação e parâmetros incompletos

> Durante alguns testes, a IA não identificava erros de digitação e não sabia trabalhar esse contexto. Por exemplo, quando eu dizia ano 205, ela não entendia e não tratava isso como erro de digitação. Otimizei para incluir esse tratamento.

- **Intervenção humana:** reproduzi entradas inválidas e solicitei tratamento sem inventar o parâmetro correto.
- **Registro técnico associado:** `docs/development_entries/2026-10-21-entradas-invalidas-v0.2.22.md`, `docs/DEVELOPMENT_LOG.md` v0.2.22.
- **Evolução importante:** o redesenho posterior removeu respostas rígidas do backend; validação de parâmetros precisa ser distinguida de geração de respostas pelo modelo.

### P09 — Linguagem excessivamente técnica

> Após alguns testes com mensagens no chat, o agente ainda respondia de forma muito técnica algumas vezes. Foi necessário revisar as instruções no prompt.

- **Intervenção humana:** avaliei clareza e naturalidade da linguagem e solicitei ajustes de instruções.
- **Registro técnico associado:** `docs/development_entries/2026-10-21-redesign-v0.2.24.md` (revisão aprovada de comunicação natural e instruções mais curtas).

### P10 — Redefinição das responsabilidades entre backend e LLM

> Após diversos ajustes em prompts, o agente ainda não conversava do jeito a que eu estava acostumado, comparado a outros agentes que desenvolvi. A conversa continuava com loops, engessada e perdendo partes do contexto nas trocas de assunto. Decidi revisar quanto o backend influenciava a conversa natural com a LLM. Identifiquei influência excessiva e resolvi refazer a arquitetura de prompt e backend, com mínima interferência do backend e mais responsabilidade da LLM na condução da conversa humanizada.

- **Intervenção humana:** questionei a arquitetura, em vez de insistir apenas na redação de prompts.
- **Registro técnico associado:** `docs/development_entries/2026-10-21-redesign-v0.2.24.md`, `docs/DEVELOPMENT_LOG.md`, evolução v0.2.24–v0.2.31.
- **Decisão arquitetural resultante:** respostas visíveis redigidas pela LLM com evidências das ferramentas; backend preserva validações e segurança, não substitui a conversa por respostas fixas.

### P11 — Reforço de segurança e escopo

> Decidi reforçar a segurança do agente para não expor credenciais de colaboradores, não conversar sobre outros assuntos, não revelar o prompt e aplicar outros guardrails.

- **Intervenção humana:** priorizei riscos de exposição de informação e de desvio de escopo nas conversas.
- **Registro técnico associado:** `docs/development_entries/2026-10-21-redesign-v0.2.24.md`, `docs/development_entries/2026-10-21-guardrails-v0.2.28.md`, `docs/DEVELOPMENT_LOG.md`, v0.2.28–v0.2.30.
- **Limite:** testes e instruções de segurança reduzem risco, mas não demonstram proteção absoluta nem equivalem a controles de autenticação.

## 22/10/2026 — Resiliência da interface

### P12 — Perda de conexão entre frontend e backend

> Decidi tratar falhas em que o frontend perdesse a conexão com o backend, informando ao usuário que deveria aguardar a reconexão para continuar usando o agente.

- **Intervenção humana:** defini experiência de espera e reconexão e validei o modal no navegador após interromper/reiniciar o Docker.
- **Registro técnico associado:** `docs/DECISIONS.md` (v0.2.33–v0.2.35), `docs/EVIDENCIA_RECONECTAR_BACKEND_v0.2.35.md` e `docs/RELEASE_VALIDATION_v0.2.35.md`.
- **Trade-off aceito:** aguardar sem envio enquanto `/health` estiver fora; não tentar reenviar automaticamente um POST de resultado incerto.

## Como estas anotações se relacionam ao histórico com IA

- **Perspectiva pessoal:** este arquivo relata observações e intervenções que o candidato apresentou retrospectivamente.
- **Histórico técnico:** `docs/DEVELOPMENT_LOG.md` registra implementações, evidências e erros por etapa; `docs/DECISIONS.md` descreve escolhas arquiteturais.
- **Interações originais:** `docs/ai_interactions/` e uma exportação organizada da conversa poderão permitir auditoria direta dos prompts, correções e resultados. A exportação **ainda não foi incorporada** ao repositório neste momento.
- Não confundir relato humano, sugestão da IA, testes automatizados, testes reais no Docker e avaliação manual.
