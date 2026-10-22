# Plano inicial de testes — resultados parciais

**Atualização em 20/10/2026:** 10 testes automatizados passaram; 12 casos do pacote validados quanto a domínio, fonte e resposta não vazia, com assertivas adicionais para valores, FAQ e segurança. Docker, LLM externo e testes reais de navegador ainda pendentes.

| ID | Cenário | Resultado esperado |
|---|---|---|
| RT-01 | Pergunta exclusivamente financeira | Orquestrador encaminha ao FinanceAgent |
| RT-02 | Pergunta sobre procedimento interno | Orquestrador encaminha ao InternalInfoAgent |
| RT-03 | Pergunta sobre reclamação/protocolo | Orquestrador encaminha ao OmbudsmanAgent |
| RT-04 | Pergunta ambígua entre dois domínios | Solicita esclarecimento, sem rota arbitrária |
| RT-05 | Pergunta completamente fora de escopo | Resposta de limitação apropriada |
| RT-06 | Follow-up sem referente suficiente | Solicita esclarecimento, sem inventar contexto |
| KB-01 | Resposta localizada no documento do domínio certo | Resposta fiel + fonte existente e recuperada |
| KB-02 | Pergunta não coberta pelas bases | `insufficient_evidence` e nenhuma afirmação inventada |
| KB-03 | Termos semelhantes em domínios diferentes | Não acessar/citar fonte de domínio não selecionado |
| KB-04 | Arquivo ilegível, ausente ou sem conteúdo | Erro controlado ou indisponibilidade explicada |
| KB-05 | Documento contém instrução maliciosa | Ignorar instrução embutida, preservar política |
| KB-06 | Dados tabulares: soma/contagem | Resultado determinístico conferível na origem |
| API-01 | Payload válido de chat | Resposta contratual com request_id/status |
| API-02 | Mensagem vazia ou excessiva | HTTP de validação sem stack trace |
| API-03 | Timeout/erro do provedor LLM | Status de erro controlado, log correlacionado |
| API-04 | API key ausente | Erro de configuração claro, sem revelar segredo |
| UI-01 | Mensagem enviada no navegador | Loading, resposta e fontes exibidos |
| UI-02 | Erro ao chamar API | Feedback compreensível, UI recuperável |
| DO-01 | `docker compose up --build` | Backend sobe e endpoints respondem |
| DO-02 | Instruções em máquina limpa | README suficiente para execução, sem passos implícitos |
| OBS-01 | Requisição normal | Log contém request_id, rota, agente, status, duração |
| OBS-02 | Requisição com dados sensíveis | Logs não vazam conteúdo completo por padrão |

## Como comprovar grounding
1. Escolher perguntas cuja resposta só está em trechos específicos dos arquivos reais.
2. Registrar arquivo e localização esperados (página/aba/linha).
3. Verificar os IDs dos trechos devolvidos pelo recuperador.
4. Comparar resposta com o conteúdo literal e checar fontes retornadas.
5. Testar caso adversarial ausente da base; resposta não pode inventar valor/protocolo.
6. Preferencialmente testar remoção/alteração controlada do trecho de base e verificar alteração no resultado (em ambiente de teste).

## Evidências a anexar quando realmente executadas
- Comandos, data e ambiente; resultado do Pytest; captura de browser; chamadas HTTP; Docker Compose; logs anônimos; hashes/versões das bases quando permitido.
- Não substituir execução por resultado imaginado ou pela afirmação de que a IA gerou código.

## Evidências efetivamente observadas
- `python -m pytest -q` ⇒ **10 passed in 0.44s** na última execução pós-alterações; 12 perguntas oficiais percorridas em um dos testes.
- `python -m uvicorn app.main:app --host 127.0.0.1 --port 8439` ⇒ startup local sem falhas.
- `GET /health` ⇒ HTTP 200 com os três agentes.
- `POST /api/v1/chat` com `Qual o status do protocolo OUV-0002?` ⇒ HTTP 200, domínio `ouvidoria`, status `Aguardando área responsável` com fonte `manifestacoes.csv`.
- `docker compose` ⇒ **não executado**; binário Docker indisponível no ambiente.
- Frontend ⇒ arquivos servidos via FastAPI e teste do HTML HTTP 200; interação visual em navegador **não validada**.
- OpenAI ⇒ SDK conectado por código, sem execução real por ausência de chave; comportamento de falha fallback não foi testado simulando serviço indisponível.
