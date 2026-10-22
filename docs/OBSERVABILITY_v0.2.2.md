> **ARQUIVO HISTÓRICO:** não descreve a arquitetura SDK-only v0.2.6. Consulte README.md.

# Registro de desenvolvimento — Observabilidade v0.2.2 (20/10/2026)

## Evidência real do usuário
- Versão base confirmada: **v0.2.1**, funcional no Windows em `H:\Meu Drive\Desafio IA Areco`.
- O usuário testou o caso de aprovações para compra de R$ 12.000. A resposta e a fonte estavam corretas.
- A execução real teve duas mensagens de retry e uma resposta `HTTP/1.1 200 OK` da API OpenAI, mas o chat registrou `method=regras_fallback` e 162970 ms. **Não havia no log da v0.2.1 informação suficiente para concluir se a geração também usou LLM.**
- Hipóteses ainda em aberto: falha de rede/timeout durante a classificação, formato JSON inválido, validação de campos inválida ou erro do SDK. O HTTP 200 registrado pode ser de outra tentativa/etapa; não estabelece a causa por si só.

## Alteração proposta pela IA, ainda pendente de validação pelo usuário no Windows
- Separar `classification_method` de `generation_method` no resultado e nos logs.
- Registrar `classification_error` e `generation_error` como **nomes de exceções e, quando houver, código HTTP**, sem expor mensagens brutas, chaves ou prompts.
- Preservar o campo legado de log `method` com o mesmo valor de `classification_method`.
- Não modificar as regras de roteamento, os cálculos SQL nem o extrator textual da v0.2.1.
- Limitar tentativas implícitas da OpenAI SDK por padrão a 0 (`OPENAI_MAX_RETRIES=0`) e explicitar o timeout por tentativa (`OPENAI_TIMEOUT_SECONDS=12`). Ambos são configuráveis no ambiente; isso **não é garantia de duração máxima total**.
- Incluir na interface a origem da classificação e da resposta.

## Estados esperados

| Cenário | `classification_method` | `generation_method` |
|---|---|---|
| LLM classifica e redige | `llm` | `llm_contexto` |
| Classificação falha, geração LLM funciona | `regras_fallback` | `llm_contexto` |
| Classificação funciona, geração falha | `llm` | `extrativo_fallback` |
| Sem chave, documento extraído | `regras` | `extrativo` |
| FAQ retorna a resposta direta, antes da LLM | `llm` ou `regras` | `faq_extrativa` |
| Financeiro/Ouvidoria: resposta tabular | `llm` ou `regras` | `deterministico` |

`classification_error` e `generation_error` serão `null` se não houve falha capturada naquele estágio. `method` legado permanece sinônimo da classificação, não da geração.

## Testes executados neste ambiente
- Comando: `python -m pytest -q`.
- Resultado: **20 passed** (14 testes existentes e 6 adicionais).
- Seis casos novos: dois estágios LLM funcionando; fallback só do classificador; HTTP 200 simulado com JSON inválido; fallback só do gerador; contrato JSON/log e proteção contra segredo; modo sem LLM.
- **Os testes novos usam mocks, não chamadas reais pagas à API.**
- Não executado: teste com chave real da OpenAI nem reteste em Windows; solicitar evidências ao usuário.

## Instruções para aplicar o patch
1. Pare o Uvicorn (CTRL+C).
2. Extraia o arquivo ZIP do patch **na pasta-pai** `H:\Meu Drive\Desafio IA Areco`, permitindo mesclar/substituir os arquivos dentro de `areco-multiagentes-fundacao\`. Se estiver dentro da pasta do projeto, extraia o conteúdo *interno* `areco-multiagentes-fundacao/` para a pasta atual, evitando uma pasta duplicada.
3. **Não substitua o `.env`**, que não faz parte deste patch. As configurações atuais `OPENAI_API_KEY`, `OPENAI_MODEL`, `USE_LLM_ANSWERS=true` permanecem.
4. Opcional no `.env`: `OPENAI_TIMEOUT_SECONDS=12` e `OPENAI_MAX_RETRIES=0` (já são os padrões).
5. Rode `\.venv\Scripts\python.exe -m pytest -q` e `\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`.
6. Pergunte: “Quais são as aprovações para uma compra de R$ 12.000?”. Compare `classification_method`, `generation_method`, `classification_error` e `generation_error` no evento `chat` do log. Mantenha `OPENAI_API_KEY` fora de screenshots.
7. Opcional: “Como solicito férias?” passa por FAQ direta no código v0.2.1; portanto, geração sem LLM (`faq_extrativa`) pode ser **comportamento esperado**, não falha da API.

## Limitações e próximos passos
- Futuros refinamentos de RAG e síntese documental ficam fora deste patch; nenhuma melhoria do v0.3.0 foi aplicada.
- Se houver `classification_error`, investigar o tipo de exceção registrado antes de alterar arquitetura ou prompts.
- Realizar teste real no Windows e registrar o resultado em `docs/DEVELOPMENT_LOG.md`. Este arquivo documenta o passo de forma cronológica e pode ser anexado ao log principal, sem sobrescrever edições locais do usuário.
