# 20/10/2026 — Validação Docker Windows e checklist de entrega (v0.2.15)

## Evidências fornecidas pelo candidato

- Comando `docker compose ps`: serviço `app` no estado `Up ... (healthy)`, bind `127.0.0.1:8000->8000/tcp`.
- `check_docker_http.py`: 2 PASS, `/health` e `/`.
- `check_docker_http.py --chat`: 3 PASS, incluindo `/api/v1/chat` com handoff, ferramenta e fonte; trace real `trace_b2e0561bfccb4393a5630c2ce09b18c3`.
- As chamadas foram executadas pelo candidato no Windows. O ambiente de edição do assistente não executou Docker real nesta etapa.

## Decisão e alterações realizadas

- Preservar o código funcional v0.2.13 e o Compose da v0.2.14. Não alterar agentes, ferramentas, queries, retrieval, API nem frontend.
- Atualizar status real em README, AGENTS e checklist, sem exagerar cobertura: Docker local validado não implica deploy público.
- Entregar `.env.example` com placeholders e comentários, **nunca** o `.env` real. Verificar publicação Git e autorização das bases antes do envio.
- Permanecem como tarefas humanas: revisão da interface no navegador, pytest final no Windows, inspeção `git status`/histórico, criação ou confirmação de repo GitHub e apresentação.

## Testes

- Validação principal: evidências Windows enviadas pelo candidato (3/3, healthy).
- Patch documental: testes offline locais devem ser executados após montagem; não afirmar teste ao vivo adicional do SDK.

## Limitações

- O usuário pode ter um `.env` existente com segredo, e este não deve ser sobrescrito ou adicionado ao patch.
- A pasta sincronizada consultada não mostrou `.env.example`; incluí-lo como arquivo novo garante a reprodução das instruções de instalação.
- A validação não inclui testes de concorrência, autenticação, deploy em nuvem ou proteção universal contra perguntas desconhecidas; esses itens continuam fora do escopo e no roadmap.
