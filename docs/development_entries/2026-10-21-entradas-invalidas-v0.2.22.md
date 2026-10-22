# Entrada — 21/10/2026 — v0.2.22: correção de erros de digitação e intenção pendente

## Evidência e decisão
Após a versão visual v0.2.21, o usuário relatou que o cache da aba antiga era a causa de exibir arquivos estáticos desatualizados; confirmou a interface em janela anônima. Aprovou prosseguir com o tratamento de erros de digitação antes do handoff, especialmente `205` seguido de `2025` em uma consulta de despesas por departamento. Também pediu incluir a definição de `$py` em todos os comandos futuros.

## Mudanças
- Criado `app/sdk_integration/input_guard.py`: somente checagens sintáticas e de parâmetros solicitados; não roteia assuntos e não cria novo agente.
- Respostas locais para anos com menos de quatro dígitos, protocolos incompletos, mês acima de 12, intervalo com ordem invertida e valores numéricos ambíguos em esclarecimento.
- Departamento com erro ortográfico: compara com os valores existentes no SQLite usando similaridade conservadora, apresenta sugestão e aguarda confirmação explícita, sem substituição silenciosa.
- `SessionState.pending_confirmation` guarda a sugestão somente na sessão; entrada inválida não é adicionada aos fragmentos pendentes para a próxima consulta; quando o usuário corrige, a consulta retoma o contexto original.
- `SdkChatService` responde localmente ao erro, com `trace_id=None` e zero tokens; requisições efetivas continuam pelo Runner e handoffs nativos.
- Versão FastAPI e selo visual atualizados para v0.2.22. O cache-busting acompanha a versão.
- Novos testes offline com Runner simulado e smoke HTTP com OpenAI real, sem alterações nos dados, ferramentas SQL, RAG, segredos ou Dockerfile.

## Testes e limites
- Testes offline locais: ver saída registrada na preparação do patch.
- Não foi possível executar OpenAI/Docker no Windows do usuário neste ambiente; smoke real `scripts/check_input_corrections_sdk_http.py` pendente.
- O processamento de intenção é probabilístico; a validação cobre apenas erros objetivos e não garante todos os casos de linguagem natural.
- Uma resposta local intencionalmente não aparece no tracing da OpenAI porque não ocorreu chamada ao modelo. A API fornece classificação e metadata explícitas para auditoria.
