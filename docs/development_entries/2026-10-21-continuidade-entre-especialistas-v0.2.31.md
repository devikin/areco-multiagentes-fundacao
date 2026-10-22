# v0.2.31 — Continuidade e troca de especialista

## Falha reproduzida pelo usuário
Na sessão de frontend: “quero saber a situação de um protocolo” → “não tenho o número” → “reembolso” → `OUV-0016`, o código ficou em `Informacoes_Internas` e buscou políticas internas, sem chamar `buscar_protocolo`. Consulta direta em sessão nova ao mesmo código funcionou. `manifestacoes.csv` registra OUV-0016, categoria Reembolso, prioridade Média e status Aguardando área responsável. Portanto a base existe; a falha observada foi de roteamento e estado pendente.

## Causa e solução
- A versão anterior mantinha `pending_agent` sempre que o especialista não registrava fontes. Isso confundia uma busca documental sem evidências com um esclarecimento solicitado e deixava o atendimento preso em Informações Internas.
- Agora somente o `Financeiro` mantém `pending_agent`/`pending_question` quando faltam dados para uma consulta tipada; preserva a sequência “despesas por departamento” → “205” → “2025”. Após consulta documental sem evidência, o próximo turno retorna ao Orquestrador com o histórico da sessão.
- Se o usuário fornecer um identificador formal `OUV-0000` e houver um especialista pendente diferente da Ouvidoria, o backend retoma pelo Orquestrador, limpando a influência da pergunta pendente na validação da nova consulta. O identificador é reconhecido para liberar a rota, não para redigir respostas, consultar banco ou introduzir segundo classificador de domínio.
- As instruções dos agentes agora distinguem consulta de política de reembolso de consulta à situação de uma manifestação de reembolso. Em busca individual sem código, não prometer encontrar protocolo por data, assunto ou departamento. Com identificador explícito, usar a ferramenta de Ouvidoria.

## Testes / evidências
- 27 testes locais pytest aprovados na cópia incremental disponível neste ambiente (inclusive simulação da rota e preservação de esclarecimento financeiro); 28 verificações do avaliador de guardrails aprovadas; `compileall` e integridade ZIP a conferir na entrega.
- O ambiente local NÃO faz chamadas à OpenAI nem executa Docker; as respostas reais devem ser verificadas no Windows do usuário.
- Criado `scripts/check_frontend_continuity_sdk_http.py` com cenários `frontend` (8 turnos), `switch` (4 turnos) e `finance` (3 turnos), cada um em sessão distinta, com evidências e traces gravados em `docs/evidence/`.
- `F07` admite resposta derivada do histórico do F06, se houver fonte correta e status correto, sem exigir consulta redundante.

## Não alterado
Ferramentas e SQL, banco sintético, `.env`, modelo, limites de 30 trocas e geração exclusiva de respostas pela LLM. O aplicativo continua usando somente Agents SDK nativo.

## Limites
Prompt e reentrada pelo Orquestrador reduzem, mas não eliminam a variabilidade do GPT-4.1 mini. Verificar casos reais de trocas de domínio com o script antes de aprovar.
