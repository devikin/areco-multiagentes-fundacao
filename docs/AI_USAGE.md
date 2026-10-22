# Uso de IA no desenvolvimento — evidências e boas práticas

O avaliador deve conseguir distinguir propostas geradas com auxílio de IA, decisões humanas, mudanças realmente realizadas e testes reais.

## Registro mínimo por mudança
1. Guardar prompt relevante ou referência ao histórico original.
2. Resumir fielmente a sugestão da IA e indicar a ferramenta usada.
3. Registrar opção aceita, adaptada ou rejeitada e o motivo.
4. Identificar arquivos/commits efetivos.
5. Documentar execução de testes com comandos e resultados reais.
6. Atualizar limitações pendentes.

## Histórico inicial
- `docs/ai_interactions/2026-10-20-prompt-inicial.txt`: texto original das instruções do usuário.
- `docs/DEVELOPMENT_LOG.md`: resumo da primeira etapa e acompanhamento cronológico.
- **Importante:** o arquivo acima não contém o histórico integral da conversa de ChatGPT. Preservar/exportar conversas relevantes separadamente, mediante disponibilidade do recurso do produto, antes da entrega. Nunca apresentar um resumo como transcrição integral.

## Proteção de dados
- Não incluir `.env`, tokens, emails privados, PII, bases confidenciais ou requisições sensíveis nos logs de IA, prints ou commits.
- Não publicar as bases fornecidas pela Areco no GitHub sem confirmar autorização de divulgação.
