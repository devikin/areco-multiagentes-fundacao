# Inventário inicial das bases de conhecimento (20/10/2026)

## Origem observada
- Pasta Google Drive de Meu Drive: `Desafio IA Areco`, ID `1tzcub9pbTBC0uoF3slm8e5fHTAHyJEbm`.
- Caminho usado no computador do usuário: `H:\Meu Drive\Desafio IA Areco` (mapeamento local; não é um endereço de API do Google Drive).
- Também foi identificada uma pasta homônima compartilhada; a análise aqui se refere à pasta de Meu Drive.
- Empresa descrita nos anexos: **Aurora Serviços Digitais S.A.** (fictícia); dados declaradamente sintéticos.

## Inventário observado
| Domínio | Arquivos | Quantidades declaradas no manifesto | Abordagem recomendada |
|---|---|---|---|
| Financeiro | `lancamentos_financeiros.csv`, `orcamento_mensal.csv`, `indicadores_e_regras.json` | 300 lançamentos; 144 orçamentos | Importação tabular; agregações SQL/Python determinísticas e `Decimal`/`NUMERIC` |
| Informações internas | 10 políticas/procedimentos `.md`; `faq_interno.json` | 10 documentos; 7 itens FAQ | Recuperação textual por FAQ, seções e fontes (`RAG` leve) |
| Ouvidoria | `manifestacoes.csv`, `referencia_ouvidoria.json` | 180 manifestações | Consulta exata por protocolo, filtros tipados e agregações seguras |
| Complementar | `sql/schema.sql`, `documentacao/dicionario_de_dados.md`, `documentacao/ingestao_e_uso.md`, `testes/perguntas_avaliacao.json`, `manifesto_pacote.json` | 12 perguntas de avaliação | Contratos de banco, parâmetros de ingestão e testes manuais |

## Evidências das fontes lidas
- `documentacao/dicionario_de_dados.md`: nomes e significados das colunas e limites dos domínios.
- `documentacao/ingestao_e_uso.md`: recomenda PostgreSQL para CSV, NUMERIC(14,2), recuperação por seção nos Markdown e consultas estruturadas na ouvidoria.
- `sql/schema.sql`: DDL para 3 tabelas com índices e restrições de integridade.
- `financeiro/indicadores_e_regras.json`: distingue despesas pagas de incorridas; diferencia competência de vencimento; obriga conversão decimal.
- `ouvidoria/referencia_ouvidoria.json`: não inventar protocolos; `Respondido` não significa `Concluído`; prazo de 10 dias é fictício.
- `testes/perguntas_avaliacao.json`: 12 cenários esperados, incluindo roteamento, cálculo financeiro, protocolo ausente, protocolo conhecido e segurança.
- CSVs: cabeçalhos e primeiras linhas efetivamente inspecionados pela integração com Google Drive, mas contagem total, consistência e valores agregados **não foram verificados independentemente**.
- Um Markdown de férias e o FAQ interno foram lidos como amostra: férias via portal com 30 dias de antecedência.

## Recomendação de engenharia (proposta da IA, ainda não implementada)
1. **Orquestrador:** LLM com classificação para `financeiro`, `informacoes_internas`, `ouvidoria`, `ambigua`, `fora_escopo` ou `seguranca`; saída validada por Pydantic.
2. **Financeiro:** catálogo fechado de operações, filtros tipados; cálculos no banco com `NUMERIC` (evitar texto→SQL arbitrário).
3. **Informações internas:** buscar fragmentos ou seções do FAQ e dos Markdown com fonte e versão; bloquear respostas sem evidência.
4. **Ouvidoria:** lookup por protocolo e filtros autorizados; não inventar identidades, protocolos ou prazos legais.
5. **Testes:** usar `perguntas_avaliacao.json` como suíte inicial de aceitação e verificar erros e casos ambíguos adicionais.
6. **Persistência:** PostgreSQL consta nas instruções do pacote e no esquema SQL, mas requer decisão de custo/simplicidade para rodar em Docker. A adoção no MVP permanece **proposta**, não implementação.

## Pontos pendentes
- Não foi executada ingestão, contagem automática independente nem validação integral dos CSVs.
- Não há backend, frontend, orquestrador ou agentes executados.
- Não foi feita auditoria de cada documento Markdown, apenas inventário e amostras.
- Nenhum teste da aplicação foi executado.

## Atualização de auditoria — após implementação (20/10/2026)
- Contagens **confirmadas por leitura integral dos CSV e ingestão SQLite**: 300 lançamentos, 144 orçamentos, 180 manifestações, 10 Markdown, 7 FAQ (17 chunks).
- Fonte: arquivos obtidos da pasta Drive `Desafio IA Areco` em Meu Drive; cópias verificadas sob `data/knowledge/`.
- Recuperação implementada: consultas SQL parametrizadas para tabelas, `Decimal` para valores, BM25 para documentação.
- Todos os 12 casos oficiais passaram em verificação automatizada de **domínio e fonte esperada** (testes `test_official_12_evaluation_cases`). As verificações de conteúdo foram ampliadas nos testes de FAQ, segurança, financeiro e protocolo.
- Limite: a suíte não prova cobertura completa de perguntas abertas; uso de LLM e Docker seguem pendentes de validação real.
