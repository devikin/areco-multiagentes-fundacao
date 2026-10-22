# v0.2.17 — Correção de saudações sem marcador na saída do SDK

**Evidência real enviada pelo usuário:** `scripts/check_conversational_sdk_http.py` (v0.2.16) falhou na primeira consulta `Olá`. Resposta `domain=ambiguo`, texto "Você quer consultar Financeiro, Informações Internas ou Ouvidoria?", sem handoff/tool, com trace `trace_5e3dc05f41b04096a905705a670c288a`.

**Causa:** `_orchestrator_response` só reconhecia conteúdo social quando o LLM emitia um prefixo exato (`SAUDACAO:` / `AGRADECIMENTO:` / `DESPEDIDA:`). Em uma saudação real o modelo retornou texto livre sem marcador, provocando o fallback `ambiguo`. A falha não prova ausência de documentos nem erro do SDK; é uma fragilidade do contrato de saída entre LLM e backend.

**Alteração:** acrescentar verificação determinística de **mensagens inteiras e exclusivamente sociais** dentro do `SdkChatService`, após a chamada ao SDK (mantendo trace/uso/observabilidade). Quando não houve handoff e a mensagem do usuário é um cumprimento, agradecimento ou despedida isolado, padronizar `domain=conversa` e a resposta autorizada, mesmo se a LLM não enviou o marcador. O reconhecimento compara frases completas, não substrings. Consultas como "Olá, gostaria de saber sobre férias" não são capturadas; mantêm a prioridade do handoff. Mantidos controles para credenciais, fora de escopo e perguntas ambíguas. Reforçado prompt do Orquestrador e adicionados testes de regressão com Runner simulado.

**Limitação:** o modelo continua probabilístico na seleção de handoffs; a regra cobre casos estritamente sociais sem handoff, não toda linguagem conversacional. Sem novas dependências, sem memória persistente e sem camada geral de roteamento baseada em palavras-chave.

**Validações:** executar testes offline e smoke HTTP no Docker. A confirmação do comportamento real exige o próximo teste no Windows (não declarar como validado antecipadamente).
