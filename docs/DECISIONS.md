# Registro de decisões arquiteturais (ADR simplificado)

## ADR-0001 — Implementação de orquestração direta
- **Data:** 20/10/2026.
- **Situação:** PROPOSTA pela IA; não validada por implementação ou testes.
- **Problema:** implementar quatro papéis distintos em três dias úteis de forma explicável.
- **Decisão proposta:** classes Python com interfaces claras, FastAPI, roteador tipado via LLM e agentes de domínio com recuperação própria. Não utilizar LangGraph/LangChain/CrewAI inicialmente.
- **Alternativas:** frameworks de agentes; único prompt com múltiplas personas.
- **Justificativa:** controle, simplicidade, testes independentes e menor curva de aprendizagem. Prompt único foi rejeitado como evidência insuficiente de handover; frameworks podem introduzir overhead para este caso.
- **Reavaliar se:** houver workflow com múltiplos ciclos de ferramentas, estado persistente complexo ou exigência formal do teste.

## ADR-0002 — Recuperação de conhecimento dependente do formato
- **Data:** 20/10/2026.
- **Situação:** HIPÓTESE, aguardando bases da Areco.
- **Decisão proposta:** documentos pequenos textuais: indexação local com chunks + metadados e BM25; dados tabulares: acesso estruturado e cálculos determinísticos. Embeddings só se os testes mostrarem ganho necessário.
- **Alternativas:** vector DB, file search hospedado, embeddings locais, recuperação via LLM sem índice.
- **Riscos:** correspondência lexical limitada por sinônimos, especialmente em português; desempenho precisa ser verificado com perguntas reais.

## ADR-0003 — Rastreabilidade e registro de IA
- **Data:** 20/10/2026.
- **Situação:** proposta operacional adotada como padrão para criação desta documentação; funcionamento da aplicação ainda pendente.
- **Decisão:** separar `docs/DEVELOPMENT_LOG.md` (desenvolvimento assistido por IA) de logs JSON da aplicação; registrar status/certeza/evidências; preservar prompt original, sem credenciais.

## ADR-0004 — SQLite no MVP, com consultas por domínio
- **Data:** 20/10/2026.
- **Estado:** IMPLEMENTADO e testado localmente. Seleção técnica proposta pela IA para avançar no MVP; usuário ainda poderá revisá-la.
- **Decisão:** importar CSVs/Markdown/FAQ de origem para SQLite local, mantendo os CSVs sintéticos no pacote e os campos financeiros como texto decimal.
- **Alternativas:** PostgreSQL disponibilizado no esquema original do pacote, banco vetorial gerenciado, execução direto sobre CSV a cada requisição.
- **Justificativa:** dispensa credenciais e serviço adicional, acelera testes locais, suporta índices, rastreabilidade e consultas parametrizadas.
- **Limitação:** PostgreSQL seria mais apropriado para produção e concorrência intensa; não é necessário para a carga demonstrativa atual.

## ADR-0005 — Duplo modo local/LLM
- **Data:** 20/10/2026.
- **Estado:** modo local implementado/testado; modo LLM implementado mas não testado com provedor real.
- **Decisão:** classificação LLM por JSON validado quando a chave existir; fallback documentado com regras. Consultas financeiras/de protocolos executam ferramentas determinísticas.
- **Risco:** demonstrar apenas o modo local não comprova integração efetiva de IA; teste com chave é pendência prioritária.

## Atualização de status dos ADRs anteriores
- **ADR-0001:** classes e handover implementados, testes locais aprovados; classificação LLM pendente de teste real.
- **ADR-0002:** BM25 + SQLite + `Decimal` efetivamente implementados e testados com os casos fornecidos.
- **ADR-0003:** logs da aplicação e diário de desenvolvimento mantidos separados.

## ADR-0006 — Fechamento explícito e armazenamento local para SQLite em Windows
- **Data:** 20/10/2026.
- **Estado:** CORREÇÃO IMPLEMENTADA; confirmação no Windows do usuário pendente.
- **Causa:** o context manager padrão de sqlite3 não fecha a conexão. Substituir arquivo de banco ainda aberto no Windows falha com `WinError 32`. Pastas sincronizadas podem manter handles externos.
- **Decisão:** fechar connection antes de substituir arquivo temporário e armazenar o SQLite por padrão em `%LOCALAPPDATA%` no Windows. Arquivos-fonte de conhecimento permanecem no Google Drive; `.env` permite customizar o destino.
- **Alternativas:** desativar sincronização, retries de rename, usar PostgreSQL imediatamente. Preferiu-se a correção de ciclo de vida e isolamento do estado mutável para não aumentar a complexidade do MVP.

## ADR-0007 — Planejamento financeiro tipado por LLM; execução determinística
- **Data:** 20/10/2026.
- **Estado:** implementado/testado localmente com LLM simulada; aguarda teste real Windows/OpenAI.
- **Decisão:** o agente Financeiro pede à LLM somente um `FinancePlan` validado por Pydantic; SQLite consulta exclusivamente tabelas/colunas permitidas com valores em placeholders SQL. As agregações monetárias usam `Decimal` Python.
- **Resiliência:** fallback apenas por falha da LLM ou resposta/plano inválido; falta de ano ou intenção não suportada retorna esclarecimento sem fallback. Erro de banco permanece erro técnico.
- **Alternativas rejeitadas:** execução de SQL livre fornecido pelo modelo; somas de valores feitas pela LLM.
- **Limitações:** máximo de somas por grupo, não operação entre orçamentos e despesas; uma competência anual por consulta.

## ADR-0008 — Agents SDK como único motor do projeto
- **Data:** 20/10/2026.
- **Solicitação/decisão do usuário:** remover a implementação anterior e manter apenas OpenAI Agents SDK após validar 3/3 handoffs HTTP reais e tracing.
- **Alternativas:** manter flag `AGENT_ENGINE` com dois motores ou reescrever aplicação inteira.
- **Decisão implementada pela IA nesta etapa:** retirar código legado, mover mecanismo financeiro de SQL/Decimal para `app/sdk_integration/finance_queries.py`, preservar `/api/v1/chat`, frontend, dados, ingestão, documentação histórica e testes aplicáveis.
- **Riscos:** regressão no startup do Windows, dependência obrigatória de OpenAI, perda do modo offline de atendimento; backup e testes HTTP de regressão necessários.
- **Fallback:** nenhum fallback para o motor legado. A ausência de fontes é tratada com resposta controlada; erros técnicos não devem ser escondidos.
- **Validações:** testes offline realizados no ambiente desta execução; smoke test real pós-limpeza no Windows pendente.

## ADR-0009 — Consultas estruturadas da Ouvidoria via Agents SDK (v0.2.7)
- **Data:** 20/10/2026.
- **Estado:** implementado e testado offline; validação real via SDK no Windows pendente.
- **Decisão:** LLM fornece somente `OuvidoriaPlan` tipado. SQLite executa SELECTs parametrizados e agregações verificáveis, sem SQL livre.
- **Alternativas descartadas:** escrever SQL gerado pelo modelo; puxar todos os registros da Ouvidoria para contexto do modelo; interpretar quantidades pela LLM sem ferramentas.
- **Segurança:** enums explícitos para status, prioridade, categoria e canal; agrupamento em allowlist; área conferida com valores reais; máximo dez linhas por listagem. Datas relativas não são inferidas.
- **Compatibilidade:** 3 handoffs, `/api/v1/chat`, ferramentas antigas, respostas e tracing preservados.


## ADR-0010 — Uma ferramenta para consulta agregada de Ouvidoria (v0.2.8)
- **Contexto:** no teste real da v0.2.7, o especialista escolheu `contar_manifestacoes` (total geral) mesmo quando o usuário pediu filtro de prioridade Alta.
- **Decisão proposta pela IA:** remover ferramenta redundante da lista do agente e centralizar agregações em `consultar_manifestacoes` com plano Pydantic validado; bloquear agrupamento divergente.
- **Benefício:** reduz confusão de escolha e respostas numéricas sem filtro; preserva handoff, SQLite e API.
- **Trade-off:** o modelo ainda precisa preencher corretamente o plano; falhas de planejamento permanecem visíveis e não devem virar respostas fabricadas.
- **Validação:** 45 testes locais passaram; teste SDK real está pendente.

## ADR-0011 — Encaminhar pelo assunto, esclarecer no especialista (v0.2.10)
- **Contexto:** modelo do Orquestrador classificou "Posso trabalhar de casa?" como ambígua, apesar da existência de política interna específica. Não executou handoff nem recuperação documental.
- **Decisão:** privilegiar handoff ao especialista quando o domínio já é identificável. A ausência de informação suficiente para responder não transforma o domínio em ambíguo. O especialista consulta evidências e pode negar confirmação individual. Manter ambiguidade quando nenhum domínio puder ser inferido e preservar recusa de credenciais.
- **Alternativa descartada:** introduzir router de palavras-chave ou regra específica em Python; contradiz a arquitetura SDK-only e criaria camada paralela de classificação.
- **Risco residual:** prompt mais explícito melhora a orientação, mas não garante 100% de handoffs em LLM não determinística. Testes HTTP reais continuam necessários.

## ADR-0012 — Proteções de robustez avançada no roadmap, sem implementação no MVP (v0.2.14)
- **Data:** 20/10/2026. **Status:** decisão expressa do usuário.
- **Contexto:** foi discutida a impossibilidade de cobrir todas as perguntas desconhecidas; validação aprofundada de evidências, incerteza, testes adversariais, monitoramento e permissões demandaria esforço adicional.
- **Decisão:** por se tratar de teste técnico com dados fictícios, não implementar essas proteções além dos controles que já existem; descrevê-las conceitualmente em `docs/ROADMAP.md`.
- **Prioridade imediata:** Docker reproduzível, README consistente com v0.2.13, evidências, checklist e entrega.
- **Limite declarado:** aprovação em 12 casos conhecidos não é garantia de segurança ou qualidade para perguntas nunca testadas.

## ADR-0013 — Camada conversacional leve, preservando handoffs (v0.2.16)
- **Contexto:** saudação simples era incorretamente fora de escopo; a formulação informal de férias falhou no BM25 apesar de documento válido.
- **Decisão:** manter roteamento nativo no Agents SDK e introduzir marcadores sociais apenas para mensagens exclusivamente sociais, com respostas padronizadas para não abrir geração factual arbitrária. Solicitações de domínio mesmo acompanhadas de saudação continuam encaminhadas ao especialista.
- **Recuperação:** remover termos introdutórios de pouco significado dos tokens de consulta para BM25 e testar variações de linguagem natural; não aumentar escopo para busca semântica geral.
- **Limite:** sem memória conversacional persistente ou acesso a informação fora dos três domínios.

## ADR-0014 — Mensagens sociais isoladas com pós-validação de domínio (v0.2.17)
- **Contexto:** a LLM classificou uma saudação simples como ambígua porque não emitiu o prefixo `SAUDACAO:` pedido nas instruções.
- **Decisão:** verificação determinística em lista restrita de mensagens integralmente sociais apenas após `Runner.run`, sem handoff, preservando a chamada ao SDK e trace.
- **Não fazer:** classificar temas substantivos por palavras-chave; transformar cumprimento que precede pergunta em resposta social.
- **Trade-off:** consome uma chamada ao modelo mesmo em saudações simples; preferível nesta PoC para demonstrar o SDK.

## ADR-0015 — Pedidos externos e intenção empresarial mista (v0.2.30)
- **Contexto:** S07 forneceu conhecimento técnico externo parcial; S09 classificou como conversa uma pergunta legítima sobre política de compras misturada a tentativa de manipulação. S02/S06 passaram sem handoff na v0.2.29.
- **Decisão:** isolar a solicitação factual dos comandos maliciosos. Apenas o comando que tenta alterar regras deve ser ignorado; o pedido legítimo permanece e segue por handoff. Pedido inteiramente externo recebe recusa natural, sem ferramenta, definição parcial ou transferência fictícia.
- **Alternativa rejeitada:** respostas pré-programadas, regex de roteamento no backend e bloqueio integral de qualquer pergunta que mencione 'ignore'.
- **Validação:** testes offline e self-test do avaliador; execução GPT-4.1 mini real no Docker pendente.

## ADR-0015 — Pendência de esclarecimento versus falta de evidências (v0.2.31)
- **Problema observado:** `pending_agent` era mantido para qualquer especialista que não retornasse fontes; isso prendia códigos OUV recebidos posteriormente em Informações Internas.
- **Decisão:** preservar a pendência apenas no Financeiro para parâmetros confirmáveis (ex.: ano), e permitir que o Orquestrador reavalie mensagens seguintes de outros especialistas. Reconhecer código formal OUV somente como guarda de reentrada ao Orquestrador, nunca como resposta ou SQL local.
- **Alternativa evitada:** introduzir um segundo classificador semântico em Python ou respostas hard-coded.
- **Risco:** a decisão semântica final de handoff ainda é probabilística; teste HTTP real necessário.

## ADR — v0.2.32 Saudação do frontend, sem obrigatoriedade no agente
- **Problema:** a mensagem inicial já existe no HTML, mas não integra o histórico SDK; um comando de saudação obrigatória no Orquestrador pode duplicá-la na primeira resposta.
- **Decisão aprovada:** manter a mensagem de boas-vindas no frontend, ensinar o Orquestrador a não repeti-la automaticamente, permitir cumprimento natural quando houver saudação do usuário e responder diretamente à pergunta substantiva.
- **Alternativas não adotadas:** remoção/reescrita da resposta LLM via JavaScript; mudança no histórico SDK para fingir uma mensagem anterior do usuário; desativar conversação social.
- **Trade-off:** resposta continua probabilística. Validação por teste HTTP real com sessão nova e casos de cumprimento, cumprimento+pergunta, consulta e acompanhamento.


## ADR — 22/10/2026 — v0.2.33: falha de rede e reenvio controlado
- **Contexto:** frontend removia texto ao enviar e não aplicava limite de espera. Usuário aprovou correção sem alterar os agentes.
- **Decisão:** 120 s de espera via AbortController; em erro, preservar texto no input, permitir novo envio manual e avisar que a consulta pode ter sido processada. Desabilitar envio e atalhos enquanto a requisição está pendente.
- **Alternativas rejeitadas:** retry automático, persistir conversas no browser e alterar serviço Python ou handoffs nesta etapa.
- **Risco residual:** sem chave de idempotência no servidor; o usuário pode gerar novos tokens caso reenvie após timeout.


## ADR — 22/10/2026 — v0.2.34: não apagar o input antes do sucesso
- Problema: requisição assíncrona limpa pergunta antes de receber confirmação; imagem de teste da falha mostrou input vazio em circunstância não reproduzida localmente.
- Decisão: conservar o texto visível até validação da resposta de API e só então limpar; em falha manter o texto e permitir reenvio manual após checar conectividade.
- Rejeitado: reenvio automático (pode duplicar cobrança e histórico) e armazenamento de pergunta em localStorage/sessionStorage sem aprovação explícita.
- Limite: reiniciar servidor não resgata respostas que não foram entregues; recarregar a aba perde o rascunho.


## ADR — v0.2.35 Reconexão segura de interface (alternativa A)

- **Contexto:** tentativa de recuperação de texto durante parada/reinício do container não atendia à experiência desejada. Proposta do usuário: overlay com blur e espera até recuperação do backend.
- **Decisão do usuário:** escolher alternativa A (risco estimado 3/10), aceitando perda da fila ao recarregar a aba e ausência de recuperação de processamento já iniciado.
- **Implementação:** checagem de `/health` antes do POST; caso offline, uma mensagem pendente em memória por aba, modal com spinner e cancelamento, polling de 3 segundos e envio único depois do retorno da API. Nenhuma mudança em backend ou Agents SDK além da string de versão.
- **Proibição:** nunca reenviar automaticamente solicitações após iniciar um POST cuja conclusão ficou incerta; idempotência/persistência end-to-end fica para possível evolução futura.
- **Verificação:** testes locais sem API; Docker/Windows ainda pendente após instalar o patch.
