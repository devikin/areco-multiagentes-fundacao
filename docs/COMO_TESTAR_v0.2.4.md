> **ARQUIVO HISTÓRICO:** não descreve a arquitetura SDK-only v0.2.6. Consulte README.md.

# v0.2.4 — Instalação e validação do agente Financeiro

## Aplicação incremental
1. Mantenha sua versão **v0.2.3**; pare o servidor com CTRL+C.
2. Extraia o ZIP na **pasta-pai** `H:\Meu Drive\Desafio IA Areco` e substitua os arquivos indicados. O ZIP já contém o subdiretório `areco-multiagentes-fundacao`.
3. Não sobrescreva `.env`. Verifique `OPENAI_API_KEY` e `USE_LLM_ANSWERS=true`.
4. Execute na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Testes manuais sugeridos (um por vez)
- **Soma:** Quanto foi gasto em despesas pagas de janeiro a março de 2025?
  - Esperado: `R$ 305.937,01`, 27 registros, `lancamentos_financeiros.csv`.
- **Maior orçamento:** Qual departamento tem maior orçamento em janeiro de 2026?
  - Esperado: `R$ 43.229,05`, `orcamento_mensal.csv`.
- **Agrupamento:** Mostre as despesas pagas por departamento de janeiro a março de 2025.
  - Esperado: detalhamento por departamento, valores obtidos no banco e fonte `lancamentos_financeiros.csv`.
- **Contagem:** Quantos lançamentos de despesa do Marketing ocorreram em 2025?
  - Esperado: contagem de registros filtrados, fonte de lançamentos.
- **Sem ano:** Qual o total de despesas?
  - Esperado: solicitação do ano, sem valor presumido e sem fallback.

## Logs e interpretação
Quando a API OpenAI funcionar, esperamos:
- `classification_method=llm`: o orquestrador classificou o domínio;
- `generation_method=llm_plano_sql`: a LLM definiu o plano de consulta, Python executou SELECT seguro e somou com Decimal;
- `generation_error=null`: sem falha de planejamento;
- `sources`: CSV efetivamente consultado.

Em caso de falha da LLM ou plano inválido, `generation_method=deterministico_fallback`, com `generation_error` identificando o tipo de erro. Sem chave de API, `generation_method=deterministico` indica modo offline configurado, NÃO falha. Erros de banco não são fallback e devem ser tratados como falhas operacionais.

**Validação realizada:** 45 testes automatizados em Linux com LLM simulada, incluindo POST real no FastAPI TestClient; integração com chave real e execução no Windows ainda pendentes.

**Escopo deliberadamente limitado:** não há consulta SQL livre; o máximo por grupo corresponde à soma do grupo, não ao maior lançamento individual. Não há comparação de orçamento contra despesas, percentuais nem consultas cruzando anos.
