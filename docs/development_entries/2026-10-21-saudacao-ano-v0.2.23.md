# Desenvolvimento — v0.2.23 — 21/10/2026

## Contexto
O usuário mostrou dois problemas no navegador: (1) `ola td berm` e `ola td bem` retornava uma solicitação de especificação de domínio; (2) após `despesas por departamento` → pedido de ano → `205` → `2025`, o Financeiro retornava resposta sem evidências.

## Causa-raiz
- Reconhecedor de intenções sociais não continha abreviações comuns como `td bem`.
- Mesmo com intenção guardada, ao receber apenas `2025` o serviço enviava o valor isolado como a mensagem mais recente do `Runner`. Havia casos em que a LLM fazia handoff para Financeiro sem executar a ferramenta, e a proteção de grounding descartava a resposta.

## Correção
- Reconhecimento restrito de saudações abreviadas quando a mensagem inteira é social; solicitações compostas continuam indo ao orquestrador.
- Quando existe consulta financeira pendente, o último esclarecimento pedia explicitamente o ano e chegou um ano válido com 4 dígitos, o `Runner` recebe a pergunta anterior com o ano informado. Nada é inferido sobre departamentos, categorias ou status.
- No agente Financeiro, `ModelSettings(tool_choice='required')`, com reset automático depois da chamada, exige ao menos uma ferramenta. A ferramenta decide se pode consultar ou se faltam parâmetros.
- Mantidas as verificações de fonte no backend; nenhuma resposta financeira sem ferramenta passa para o usuário.
- Identificação v0.2.23 no Docker e no frontend para reduzir confusão com cache.

## Validação
- Suíte de `pytest` offline com Runner simulado e banco de dados sintético; inclui casos da conversa reportada, barreira contra erro `205`, contexto completo enviado ao Runner e soma filtrada.
- Teste real `scripts/check_social_year_followup_sdk_http.py`: 3 chamadas ao SDK/OpenAI mais 1 turno local; deve ser executado no Docker do usuário.
- Limite: `tool_choice='required'` reforça a chamada da ferramenta, mas não garante plano correto em todos os casos; avaliação com OpenAI real e regressão oficial continuam necessárias.
