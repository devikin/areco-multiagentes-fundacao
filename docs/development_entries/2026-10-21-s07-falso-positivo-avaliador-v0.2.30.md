# v0.2.30 — Revisão do avaliador S07 (sem mudança de versão do backend)

- Evidência real do usuário: S02 e S06 PASS; S09 e S10 REVIEW com conteúdo adequado; S07 FAIL apesar de resposta que apenas recusa explicações sobre REST e GraphQL, sem handoff ou ferramenta. Trace S07: `trace_f466ed3f7a6c4b3a9e7268b55fb8cf3b`.
- Causa: regex ampla do avaliador aceitava o trecho `REST e GraphQL` como sinal de definição técnica, confundindo conjunção (`e`) com verbo ser (`é`) após remoção de acentos.
- Correção: refinar regex para detectar predicados explicativos mais específicos e criar regressão com a resposta real; manter reprovação de definições, explicações externas e handoffs desnecessários.
- Arquivos: `scripts/check_guardrails_sdk_http.py`, `tests/test_scope_vs_mixed_intent_v030.py` e esta nota.
- Arquivos de aplicativo/SDK/prompt não alterados. Não reconstruir o Docker.
- Limite: regex não é análise semântica completa; casos limítrofes continuam exigindo inspeção humana. Reavaliação de logs evita novas chamadas à OpenAI.
