# v0.2.18 — Atendimento conversacional com memória curta

Data de registro: 20/10/2026. Decisão: usuário aprovou o novo orquestrador com tom natural, prompt resumido, esclarecimentos anteriores ao handoff e memória volátil por sessão. Incluiu requisito explícito: respostas sem asteriscos/Markdown literal na interface.

## Problema observado

- "Olá" tinha resposta rígida; pergunta vaga sobre despesas ia imediatamente ao especialista e devolvia mensagem genérica de ausência de evidência.
- O frontend não enviava `session_id`, mesmo existindo no request schema; cada mensagem era tratada isoladamente.
- Respostas documentais continham caracteres `**` visíveis, já que o frontend usa `textContent`.

## Alterações propostas/implementadas

1. Orquestrador recebeu prompt conciso, mantendo domínios, handoffs nativos, exemplos críticos de compras e segurança, marcadores e políticas de escopo. `ESCLARECER:` permite fazer pergunta antes do handoff quando o usuário não definiu o objetivo ou parâmetro essencial. Não exigir esclarecimento para perguntas gerais completas (ex.: férias).
2. `SessionMemory` em memória RAM, 5 trocas recentes, expiração após 30 minutos de inatividade, limite de 200 sessões, exclusão FIFO das mais antigas, isolamento e lock por sessão. Sessões são voláteis e perdidas no reinício. Nada gravado em SQLite/logs.
3. Backend recebe `session_id` opcional, repassa histórico de perguntas e respostas ao `Runner.run` somente quando informado, e combina pedidos ainda pendentes para validação das ferramentas. Clientes existentes sem `session_id` continuam isolados.
4. `ESCLARECER:` recebe resposta em texto livre limitada a pergunta curta, sem evidência; especialistas podem perguntar antes de consultar ferramenta, caso usem o marcador. Respostas factuais seguem bloqueadas sem ferramenta + fonte. Marcadores nunca são exibidos.
5. Mensagem de saudação exata: `Olá! Seja bem-vindo(a). Como posso te ajudar hoje?`. Respostas de todos os agentes passam por pós-processamento para remover `*` visíveis, além de instruções para não gerar Markdown.
6. Frontend gera `crypto.randomUUID()` por abertura de página e envia `session_id` em cada POST. Nenhuma persistência local/cookies. Após recarregar, a sessão é nova.
7. Testes offline com Runner simulado cobrem contexto, ferramenta, isolamento, limites, TTL, compatibilidade, renderização e segurança. Script `scripts/check_dialog_sdk_http.py` para 5 chamadas reais após reconstruir Docker.

## Limitações e evidências

A execução REAL do novo prompt/OpenAI no Windows ainda depende do usuário. Testes offline não garantem escolha do marcador pelo modelo. A memória é exclusivamente para demonstração local; não há autenticação, armazenamento persistente, nem garantia de funcionamento com múltiplos workers/instâncias.

Não reintroduzir router próprio ou módulos legados. Roadmap de salvaguardas avançadas permanece conceitual, por decisão do usuário.
