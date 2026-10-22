# v0.2.16 — Ajuste conversacional e recuperação de férias

**Evidência:** Print do usuário com interação `olá` -> resposta de fora de escopo, e `gostaria de saber sobre as férias` -> ausência de fonte. O Git retornou `fatal: not a git repository` na pasta do projeto.

**Diagnóstico reproduzido offline:** a política `01_politica_ferias.md` existe e contém regras sobre portal, antecedência de 30 dias, aprovação pela liderança e contato de RH. A busca BM25 falhou porque as palavras introdutórias `gostaria` e `saber` reduziam a cobertura do termo `ferias` para 1/3, abaixo do mínimo 0,5. A mesma limitação ocorria em perguntas com `explicar` e `funcionam`.

**Decisão:** preserve o Agents SDK e os 3 handoffs nativos. O orquestrador trata saudações, agradecimentos e despedidas sem handoff, com marcador e resposta segura controlada pelo backend; mensagens com consulta substantiva, ainda que com saudação, continuam com handoff. Fora de escopo, credenciais e ambiguidade continuam com controles atuais. Melhoramos a lista de palavras conversacionais ignoradas pelo BM25, sem embeddings e sem nova dependência.

**Escopo:** `workflow.py`, `service.py`, `schemas.py`, `retrieval.py`, teste de regressão, smoke SDK HTTP, documentação. Não alterar dados sintéticos, SQL, FastAPI, frontend ou Dockerfile.

**Limites:** o endpoint recebe cada mensagem de forma isolada (histórico conversacional não é passado ao SDK); anáforas como "e o prazo?" ainda podem exigir esclarecimento. O SDK real precisa de validação no Windows com os novos prompts. O projeto ainda não está inicializado como repositório Git — instruções de inicialização serão executadas apenas depois de conferir as exclusões de segredos.
