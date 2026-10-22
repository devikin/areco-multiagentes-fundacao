# v0.2.30 — Limite de escopo e intenção mista

Evidência: execução real do usuário na v0.2.29, com S02 PASS, S06 PASS, S07 FAIL (exposição de informação técnica externa) e S09 FAIL (não encaminhou compra à base de políticas); S10 REVIEW semanticamente correto.

Decisão: tratar primeiro a intenção factual e separar dela instruções para alterar papel/regras. Pedido puramente externo deve ser recusado diretamente; pedido empresarial legítimo misturado a instrução maliciosa deve ser encaminhado ao especialista relevante, desprezando só a instrução indevida.

Prompt atualizado com dois exemplos curtos contrastantes; o avaliador detecta explicações externas parciais e preserva exigência de `buscar_documentos` para S09. Sem fallbacks, regex de roteamento no backend, mudança de modelo ou alteração de credenciais.

Validação local: 18 testes pytest aprovados (incluindo regressões v0.2.28/v0.2.29) e 24 verificações do self-test do avaliador, com cópias atuais de service/session_memory e retrieval usadas apenas na preparação da suíte. Execução real em Docker/OpenAI pendente.
