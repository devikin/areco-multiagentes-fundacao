# v0.2.21 — Interface versionada e diagnóstico de atualização (21/10/2026)

## Evidência e problema
O usuário mostrou, após patch v0.2.20, a saudação antiga e o texto antigo de carregamento. A cópia-fonte da v0.2.20 revisada já continha os textos novos. Logo, a divergência apontava para imagem Docker desatualizada, arquivo extraído em local incorreto, navegador em aba antiga ou cache de recursos. A causa específica no ambiente Windows não foi confirmada, pois não houve acesso ao container do usuário.

## Mudanças
- Versão `v0.2.21` visível acima de `MVP de avaliação`.
- `frontend/index.html`: saudação inicial aprovada `Olá, prezado(a). Como posso te ajudar hoje?`.
- `frontend/app.js`: indicador de processamento `...`, com session_id inalterado.
- `?v=0.2.21` no CSS/JS para evitar reutilização involuntária de cache de versões antigas.
- OpenAPI `version='0.2.21'` como marca verificável do backend.
- `scripts/check_ui_version_http.py`: quatro verificações reais HTTP sem consumo de tokens (HTML/JS/CSS/OpenAPI).

## Escopo não alterado
- Orquestrador, handoffs, SQL, RAG, memória curta e dados de conhecimento permanecem como na v0.2.20 revisada.
- Não houve implementação de correção de erros de digitação do ano; o usuário solicitou discussão prévia. Proposta: validar valores impossíveis/incompletos ANTES do handoff, pedir confirmação preservando intenção pendente, e apenas consultar ferramenta após validação.
- Ainda requer teste real com Docker Windows e atualização forçada do navegador após reconstrução.
