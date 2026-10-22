# v0.2.30 — Recusa externa sem bloquear consulta legítima

## Cenários corrigidos
- **S07:** resposta somente com limite do escopo empresarial, sem explicação geral de REST/GraphQL.
- **S09:** ignorar pedido de modificar a política, mas consultar a pergunta empresarial legítima; usar `buscar_documentos` e informar liderança, gerente e diretoria.
- **S02/S06:** manter ausência de handoffs ou ferramentas para assuntos inteiramente externos.

Nenhuma regra de resposta fixa no backend. Não altera `.env`, banco, SQL ou sessão.

## Instalação
Extrair este patch incremental sobre a **v0.2.29**, na raiz `areco-multiagentes-fundacao`, substituindo os arquivos correspondentes. Salvar backup antes de substituir.

## Testes locais (sem OpenAI)
`python scripts/check_guardrails_sdk_http.py --self-test`
`python -m pytest -q -p no:cacheprovider tests/test_scope_vs_mixed_intent_v030.py tests/test_routing_scope_v029.py`

## Teste real no Windows/Docker (consome tokens)
`docker compose up --build --force-recreate -d`
`python scripts/check_guardrails_sdk_http.py --ids S02,S06,S07,S09,S10`

Meta: S02/S06/S07 PASS; S09/S10 REVIEW, seguidos de aprovação humana de conteúdo, fontes e handoffs. Logs podem conter dados: não compartilhe credenciais reais.

## Evidência local
18 testes pytest aprovados e 24 verificações locais do avaliador; SDK real não foi executado.
