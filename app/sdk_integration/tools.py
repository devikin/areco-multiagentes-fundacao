"""Ferramentas de domínio para o Agents SDK (dados locais confiáveis, somente leitura).

Não importa o pacote agents, portanto pode ser testado sem rede/chave/modelo.
Os argumentos fornecidos pelo modelo são sempre validados antes de consultar dados.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from contextlib import closing
import json
import re
import sqlite3

from app.sdk_integration.finance_queries import FinancePlan, execute_plan
from app.sdk_integration.ouvidoria_queries import OuvidoriaPlan, executar_consulta
from app.knowledge.retrieval import retrieve
from app.schemas import Citation
from app.sdk_integration.response_messages import INSUFFICIENT_EVIDENCE_ANSWER


@dataclass
class ExecutionContext:
    database: Path
    knowledge_dir: Path
    question: str
    sources: list[Citation] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    control_answer: str | None = None

    def record(self, tool: str, sources: list[Citation]) -> None:
        self.tools_used.append(tool)
        for citation in sources:
            if not any(old.source == citation.source and old.detail == citation.detail for old in self.sources):
                self.sources.append(citation)


def consultar_financeiro(ctx: ExecutionContext, plano: FinancePlan) -> str:
    """Executa a ferramenta FinancePlan da v0.2.4; nunca recebe SQL arbitrário."""
    answer = execute_plan(ctx.database, ctx.question, plano)
    ctx.record('consultar_financeiro', answer.sources)
    if not answer.sources:
        ctx.control_answer = answer.text
    return answer.text + ('\nFONTE(S): ' + ', '.join(c.source for c in answer.sources) if answer.sources else '')


def buscar_documentos(ctx: ExecutionContext, pergunta: str) -> str:
    """Busca até 3 políticas distintas com texto completo, fonte e versão."""
    if not pergunta.strip() or len(pergunta) > 1500:
        return 'Pergunta inválida para consulta documental.'
    with closing(sqlite3.connect(ctx.database)) as conn:
        conn.row_factory = sqlite3.Row
        hits = retrieve(conn, pergunta, top_k=3)
    hits = [hit for hit in hits if hit['score'] >= .8]
    if not hits:
        ctx.record('buscar_documentos', [])
        ctx.control_answer = INSUFFICIENT_EVIDENCE_ANSWER
        return 'SEM_EVIDENCIA: Não encontrei trecho suficiente na base de políticas internas.'
    citations = [Citation(source=hit['source'], detail=hit['section'] + (f" (versão {hit['document_version']})" if hit['document_version'] else '')) for hit in hits]
    ctx.record('buscar_documentos', citations)
    return '\n\n'.join(
        f"FONTE: {hit['source']} | DOCUMENTO: {hit['section']} | VERSÃO: {hit['document_version'] or 'não identificada'}\n{hit['content']}"
        for hit in hits
    )


def buscar_protocolo(ctx: ExecutionContext, protocolo: str) -> str:
    """Busca exata por OUV-NNNN; não consulta outros protocolos por suposição."""
    code = protocolo.strip().upper()
    if not re.fullmatch(r'OUV-\d{4}', code):
        ctx.record('buscar_protocolo', [])
        ctx.control_answer = 'Protocolo inválido: utilize exatamente OUV-0001.'
        return 'Protocolo inválido: utilize exatamente OUV-0001.'
    with closing(sqlite3.connect(ctx.database)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute('''SELECT protocolo,status,categoria,prioridade,data_abertura,
                          data_resposta,resposta_resumo,area_responsavel
                          FROM manifestacoes_ouvidoria WHERE protocolo=?''', (code,)).fetchone()
    ctx.record('buscar_protocolo', [Citation(source='manifestacoes.csv', detail=code)])
    if row is None:
        # O banco, não a paráfrase da LLM, determina a ausência do protocolo.
        ctx.control_answer = f'Protocolo {code} não encontrado na base de Ouvidoria.'
        return f'FONTE: manifestacoes.csv\n{ctx.control_answer}'
    return 'FONTE: manifestacoes.csv\n' + '; '.join(
        f'{key}={row[key]}' for key in row.keys() if row[key] is not None and row[key] != ''
    )


def listar_status_ouvidoria(ctx: ExecutionContext) -> str:
    reference = json.loads((ctx.knowledge_dir / 'ouvidoria' / 'referencia_ouvidoria.json').read_text(encoding='utf-8-sig'))
    ctx.record('listar_status_ouvidoria', [Citation(source='referencia_ouvidoria.json', detail='status_validos')])
    return 'FONTE: referencia_ouvidoria.json\nStatus permitidos: ' + ', '.join(reference['status_validos'])


def consultar_manifestacoes(ctx: ExecutionContext, plano: OuvidoriaPlan) -> str:
    """Consulta filtrada da Ouvidoria sem aceitar SQL livre nem inventar dados."""
    text, sources = executar_consulta(ctx.database, ctx.question, plano)
    ctx.record('consultar_manifestacoes', sources)
    if not sources:
        ctx.control_answer = text
    return text
