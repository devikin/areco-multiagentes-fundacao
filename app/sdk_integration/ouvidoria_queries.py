"""Consultas da Ouvidoria: plano tipado, SQL parametrizado e projeções limitadas.

O modelo decide apenas filtros/agrupamento; jamais fornece SQL bruto.
A fonte é o CSV sintético importado para SQLite.
"""
from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Literal
import sqlite3
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.knowledge.retrieval import normalize
from app.schemas import Citation

Status = Literal['Aberto', 'Em análise', 'Aguardando área responsável', 'Respondido', 'Concluído']
Priority = Literal['Baixa', 'Média', 'Alta', 'Crítica']
Category = Literal['Cobrança', 'Atendimento', 'Produto ou serviço', 'Cancelamento',
                   'Reembolso', 'Privacidade', 'Elogio', 'Sugestão']
Channel = Literal['Portal', 'E-mail', 'Telefone', 'Chat']
Grouping = Literal['status', 'prioridade', 'categoria', 'area_responsavel', 'canal_entrada', 'mes']
Operation = Literal['contagem', 'agrupar', 'listar']
DateField = Literal['data_abertura', 'data_resposta']


class OuvidoriaPlan(BaseModel):
    """Contrato de tool call: somente operações/colunas explicitamente permitidas."""
    model_config = ConfigDict(extra='forbid')

    operacao: Operation = Field(description='contagem, agrupar ou listar protocolos')
    status: Status | None = None
    prioridade: Priority | None = None
    categoria: Category | None = None
    canal_entrada: Channel | None = None
    area_responsavel: str | None = Field(default=None, max_length=100)
    data_inicio: date | None = None
    data_fim: date | None = None
    campo_data: DateField = 'data_abertura'
    agrupar_por: Grouping | None = None
    limite: int = Field(default=5, ge=1, le=10)

    @model_validator(mode='after')
    def validate_operation(self):
        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError('O início do período não pode ser posterior ao fim.')
        if self.operacao == 'agrupar' and self.agrupar_por is None:
            raise ValueError('Informe agrupar_por para uma consulta agrupada.')
        if self.operacao != 'agrupar' and self.agrupar_por is not None:
            raise ValueError('agrupar_por somente é permitido em consultas agrupadas.')
        if self.operacao != 'listar' and self.limite != 5:
            raise ValueError('limite somente se aplica à listagem.')
        return self


def _area_canonica(conn: sqlite3.Connection, area: str | None) -> str | None:
    if area is None:
        return None
    choices = [r[0] for r in conn.execute('SELECT DISTINCT area_responsavel FROM manifestacoes_ouvidoria')]
    return next((v for v in choices if normalize(v) == normalize(area)), None)


def _question_guard(question: str, plan: OuvidoriaPlan) -> str | None:
    """Evita executar consultas se o modelo eliminar filtro de status/prioridade explícito.

    Não exige presença literal de filtros na pergunta: o usuário pode usar sinônimos.
    """
    q = normalize(question)
    years = set(re.findall(r'\b20\d{2}\b', q))
    if years:
        selected_years = {str(d.year) for d in (plan.data_inicio, plan.data_fim) if d is not None}
        if not plan.data_inicio or not plan.data_fim or not years.issubset(selected_years):
            return 'Não consegui confirmar o período solicitado. Informe as datas ou reformule a pergunta.'
    months = {'janeiro':1,'fevereiro':2,'marco':3,'abril':4,'maio':5,'junho':6,
              'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
    mentioned_months = [value for name,value in months.items() if re.search(r'\b'+name+r'\b', q)]
    if mentioned_months:
        if not plan.data_inicio or not plan.data_fim:
            return 'Não consegui confirmar o período mensal. Informe datas exatas.'
        if plan.data_inicio.month != min(mentioned_months) or plan.data_fim.month != max(mentioned_months):
            return 'Não consegui confirmar os meses do período solicitado. Reformule a pergunta.'
    if re.search(r'\b(ultimos|ultimas|semana passada|mes passado|hoje|ontem)\b',q):
        # Datas relativas dependem do instante corrente, não disponível nesta ferramenta.
        return 'Para consultas por período relativo, informe as datas de início e fim no formato DD/MM/AAAA.'
    # Perguntas de distribuição exigem agrupamento; contar todos os registros
    # seria uma resposta tecnicamente válida para SQL, mas falsa para o usuário.
    expected_group = None
    aliases = {
        'prioridade': ('prioridade',),
        'status': ('status',),
        'categoria': ('categoria',),
        'area_responsavel': ('area', 'area responsavel'),
        'canal_entrada': ('canal', 'canal de entrada'),
        'mes': ('mes', 'mes de abertura'),
    }
    for group, labels in aliases.items():
        if any(re.search(r'\bpor\s+' + re.escape(label) + r'\b', q) for label in labels):
            expected_group = group
            break
    if expected_group and (plan.operacao != 'agrupar' or plan.agrupar_por != expected_group):
        return (f'Não consegui confirmar o agrupamento por {expected_group}. '
                'Reformule a pergunta para realizar a consulta corretamente.')

    if 'prioridade alta' in q or 'alta prioridade' in q:
        if plan.prioridade != 'Alta':
            return 'Não consegui confirmar o filtro de prioridade Alta. Reformule a pergunta.'
    if 'prioridade critica' in q or 'critica prioridade' in q:
        if plan.prioridade != 'Crítica':
            return 'Não consegui confirmar o filtro de prioridade Crítica. Reformule a pergunta.'
    for status in ('Em análise', 'Aguardando área responsável', 'Respondido', 'Concluído'):
        if normalize(status) in q and plan.status != status:
            # Se perguntou pela distribuição de status, não é filtro de um status.
            return f'Não consegui confirmar o filtro de status {status}. Reformule a pergunta.'
    for category in ('Cobrança','Atendimento','Produto ou serviço','Cancelamento',
                     'Reembolso','Privacidade','Elogio','Sugestão'):
        if normalize(category) in q and plan.categoria != category:
            return f'Não consegui confirmar a categoria {category}. Reformule a pergunta.'
    return None


def executar_consulta(database: Path, pergunta: str, plano: OuvidoriaPlan) -> tuple[str, list[Citation]]:
    """Apenas SELECT em tabela fixa, parâmetros SQL separados dos nomes de colunas."""
    aviso = _question_guard(pergunta, plano)
    if aviso:
        return aviso, []
    terms: list[str] = []
    params: list[str] = []
    for column, value in (
        ('status', plano.status), ('prioridade', plano.prioridade),
        ('categoria', plano.categoria), ('canal_entrada', plano.canal_entrada),
    ):
        if value is not None:
            terms.append(f'{column}=?')  # colunas constantes, não derivadas de texto livre
            params.append(value)
    for operator, value in (('>=', plano.data_inicio), ('<=', plano.data_fim)):
        if value is not None:
            terms.append(f'{plano.campo_data}{operator}?')  # Literal em campo_data
            params.append(value.isoformat())

    with closing(sqlite3.connect(database)) as conn:
        conn.row_factory = sqlite3.Row
        if plano.area_responsavel is not None:
            area = _area_canonica(conn, plano.area_responsavel)
            if area is None:
                return f'Área responsável não encontrada na base: {plano.area_responsavel}.', [Citation(source='manifestacoes.csv')]
            terms.append('area_responsavel=?')
            params.append(area)
        where = (' WHERE ' + ' AND '.join(terms)) if terms else ''
        base = ' FROM manifestacoes_ouvidoria' + where
        total = conn.execute('SELECT COUNT(*)' + base, params).fetchone()[0]
        citation = Citation(source='manifestacoes.csv', detail=f'{total} registros; consulta {plano.operacao}')
        if plano.operacao == 'contagem':
            return f'FONTE: manifestacoes.csv\nTotal de manifestações que atendem aos filtros: {total}. Dados sintéticos.', [citation]
        if plano.operacao == 'agrupar':
            column = ('substr(data_abertura,1,7)' if plano.agrupar_por == 'mes'
                      else plano.agrupar_por)  # Literal, nunca expressão do usuário
            rows = conn.execute(
                f'SELECT {column} AS grupo, COUNT(*) AS quantidade' + base
                + f' GROUP BY {column} ORDER BY quantidade DESC, grupo COLLATE NOCASE ASC', params
            ).fetchall()
            if not rows:
                return 'FONTE: manifestacoes.csv\nNenhuma manifestação encontrada para esses filtros.', [citation]
            groups = '; '.join(f'{row["grupo"]}: {row["quantidade"]}' for row in rows)
            return f'FONTE: manifestacoes.csv\nManifestações por {plano.agrupar_por} ({total} registros): {groups}.', [citation]
        # Limite Pydantic <=10 e ordenação estável, evitando vazar a base inteira ao modelo.
        rows = conn.execute('''SELECT protocolo, data_abertura, status, prioridade,
                              categoria, area_responsavel FROM manifestacoes_ouvidoria'''
                            + where + ' ORDER BY data_abertura DESC, protocolo ASC LIMIT ?',
                            [*params, plano.limite]).fetchall()
        if not rows:
            return 'FONTE: manifestacoes.csv\nNenhuma manifestação encontrada para esses filtros.', [citation]
        details = '\n'.join(' | '.join(f'{key}: {row[key]}' for key in row.keys()) for row in rows)
        tail = f' Exibindo {len(rows)} de {total} registros.'
        return 'FONTE: manifestacoes.csv\n' + details + '\n' + tail + ' Dados sintéticos.', [citation]
