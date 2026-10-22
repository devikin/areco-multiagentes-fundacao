# v0.2.20 — Memória de 30 trocas e seguimento ancorado na Ouvidoria

## Evidência apresentada pelo usuário

No navegador, após a consulta do protocolo OUV-0013 (`Respondido`, categoria Reembolso), a pergunta "mas já foi reembolsado?" gerou no trace da OpenAI uma resposta cautelosa, mas **sem chamada de ferramenta**. O backend exibiu "Não encontrei evidências suficientes...", porque bloqueia respostas factuais de especialistas sem fontes. A verificação foi correta; a mensagem era pouco útil.

## Decisão e implementação

- Preservar o controle de evidências; **não** exibir simplesmente a saída livre do modelo sem fonte.
- Quando a pergunta subsequente tratar de pagamento/reembolso, existir protocolo realmente consultado nesta sessão e o especialista fizer handoff sem ferramenta, o backend reconsulta o último protocolo verificado com `buscar_protocolo` e devolve resposta controlada. A geração é marcada `sdk_consulta_local_controle`, diferenciando consulta backend de tool span do SDK. Ao mudar de domínio, o protocolo validado é descartado. Sem protocolo verificado, continua bloqueado.
- Ressaltar que status `Respondido` demonstra tratamento da manifestação, **não comprova pagamento**. A base de Ouvidoria não equivale a sistema de liquidação; nunca afirmar que o reembolso foi pago. O protocolo é sintético.
- Instrução de Ouvidoria reforça consulta obrigatória à ferramenta mesmo em perguntas de seguimento. Prompt do Orquestrador mantém foco na Ouvidoria após referência a um protocolo.
- `SessionMemory` passa a guardar as **30 trocas mais recentes** por aba/sessão (antes 8). TTL de 30 minutos de inatividade e limite de 200 sessões inalterados. Não persiste entre reinicializações; maior histórico pode aumentar tokens e latência.
- Interface: saudação inicial passa a "Olá, prezado(a). Como posso te ajudar hoje?"; placeholder de processamento passa a "...".

## Verificações

- Testes offline simulados contemplam 30 trocas, isolamento, ausência de fonte, rejeição de protocolo diferente, mudança de domínio e texto da interface.
- Regressão integral local: ver saída registrada na entrega; SDK real/Windows e Docker da v0.2.20 **pendentes de verificação pelo usuário**.
- Smoke real opcional: `python scripts/check_ouvidoria_followup_sdk_http.py` (2 chamadas reais e pagas à OpenAI).

## Limites

- A recuperação pós-handoff é restrita à intenção de pagamento vinculada ao último protocolo realmente consultado. Outros especialistas sem fontes continuam sob o bloqueio anterior.
- Um trace do SDK pode exibir somente o handoff se a ferramenta foi acionada pelo backend após `Runner.run`; a fonte é registrada na resposta, e `generation_method` explica o caminho.
- A solução não consulta dados reais de pagamento nem comprova liquidação.

## Adendo — fallback humanizado antes de aplicar v0.2.20 (revisão)

O usuário aprovou a troca da mensagem técnica genérica de falta de evidência por uma orientação cordial para buscar um responsável humano. A aplicação **não possui** ferramenta de transferência real: não afirmar que a solicitação foi encaminhada, não criar protocolos nem prometer contato posterior.

- Nova constante centralizada `INSUFFICIENT_EVIDENCE_ANSWER` em `app/sdk_integration/response_messages.py`, compartilhada pelo serviço e recuperação documental.
- Mensagem exibida quando o especialista conclui sem ferramentas/fontes e não há resposta controlada específica; ou quando a busca documental não encontra suporte.
- Ficam preservadas solicitações de esclarecimento por falta de parâmetros, respostas verificadas, controles financeiros/ouvidoria, `OUV-0013`, proteção de credenciais e fora de escopo.
- Testes `tests/test_human_fallback_v0220.py` verificam ausência de promessas de handoff humano e bloqueio de afirmações sem evidência.
- Regressão offline do projeto revisado: **143 passed, 1 skipped**. Não houve validação adicional em SDK real/Docker nesta revisão.
