# Roadmap — evolução após a prova de conceito

**Status:** conceitual, não implementado. **Decisão do candidato (20/10/2026):** os dados e cenários do desafio são sintéticos; não consumir tempo de implementação para atingir cobertura universal de perguntas, que não é possível garantir. Priorizar documentação, Docker e entrega reproduzível.

## O que o MVP já realiza

Orquestrador com handoffs nativos do OpenAI Agents SDK; três especialistas; ferramentas SQLite/Decimal e busca BM25 com fontes; respostas controladas para pedidos fora de escopo e credenciais, protocolos ausentes e especialistas sem evidência; logs de execução e traces. **Não confundir essas proteções pontuais com garantia de grounding de toda afirmação ou segurança de produção.**

## Melhorias propostas para um ambiente real

| Prioridade futura | Evolução conceitual | Finalidade / critério de avaliação futuro |
|---|---|---|
| P1 | **Validação sistemática de evidências antes de exibir resposta** | Conferir afirmações factuais contra trechos/linhas de fonte; responder apenas com evidência, ou declarar informação insuficiente. Para números, comparar com valores da ferramenta; para políticas, validar cobertura e versão. |
| P1 | **Tratamento de incerteza e ambiguidades** | Pedir esclarecimento quando o domínio, parâmetros ou elegibilidade individual não puderem ser determinados; evitar respostas fabricadas e encaminhamento arbitrário. |
| P1 | **Conjunto ampliado de testes** | Variar paráfrases, perguntas de múltiplos domínios, falta de fontes, dados conflitantes, erros de ferramenta e tentativas de prompt injection; avaliar roteamento, recuperação e resposta separadamente. |
| P2 | **Validação pós-geração proporcional ao risco** | Regras determinísticas para montantes, datas, status e fontes; revisão adicional de afirmações textuais críticas apenas quando necessário. Avaliar latência e custo. |
| P2 | **Monitoramento de qualidade e feedback** | Registrar erros, perguntas não atendidas, revisão humana e métricas de cobertura sem capturar dados sensíveis indevidamente; transformar incidentes em regressões reproduzíveis. |
| P1 se produção | **Autenticação, autorização e privacidade** | Identidade do colaborador, restrição de documentos/registros por permissão, proteção de dados, tratamento seguro de logs e rate limits. |
| P2 | **Atualização e governança da base** | Fontes aprovadas, versão, responsável, data de validade, política para documentos contraditórios e testes de reingestão. |

**Critério de evolução:** não medir “100% das perguntas possíveis”; medir cobertura de uma amostra representativa, precisão/fidelidade de respostas, taxa de recusa apropriada, vazamento de dados, erros de roteamento, latência e custo. Definir metas com stakeholders após observar uso real.

**Fora do escopo do desafio atual:** implementar estas melhorias; banco vetorial, memória conversacional, gerenciamento de usuários e infraestrutura de produção. O MVP com dados fictícios serve para demonstrar arquitetura e resultados auditáveis.
