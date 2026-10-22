"""Plano tipado e ferramentas seguras para consultas financeiras.

O LLM *somente* escolhe parâmetros de um conjunto permitido: nunca fornece SQL.
Agregações monetárias são realizadas com Decimal, não SQLite REAL/float.
"""
from __future__ import annotations

from collections import defaultdict
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from typing import Literal
import re
import sqlite3

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dataclasses import dataclass, field
from app.schemas import Citation

@dataclass
class FinanceQueryResult:
    text: str
    sources: list[Citation] = field(default_factory=list)
    generation_method: str = "sql_decimal"

from app.knowledge.retrieval import normalize
from app.schemas import Citation

Dataset = Literal['lancamentos', 'orcamentos']
Operation = Literal['soma', 'contagem', 'agrupar', 'maior', 'nao_suportada']
Group = Literal['departamento', 'categoria', 'centro_custo', 'status', 'mes']


class FinancePlan(BaseModel):
    """Contrato obrigatório da seleção de ferramenta feita pela LLM."""
    model_config = ConfigDict(extra='forbid')

    dataset: Dataset = Field(description=(
        'orcamentos: valores planejados por mês/departamento, sem tipo Receita/Despesa; '
        'lancamentos: receitas e despesas efetivamente registradas.'))
    operation: Operation = Field(description=(
        'maior: grupo com maior total; agrupar: totais de todos os grupos; '
        'soma: total geral; contagem: número de registros.'))
    year: int | None = Field(default=None, ge=2000, le=2099)
    start_month: int | None = Field(default=None, ge=1, le=12)
    end_month: int | None = Field(default=None, ge=1, le=12)
    transaction_type: Literal['Receita', 'Despesa'] | None = None
    status: Literal['Pago', 'Pendente', 'Atrasado'] | None = None
    group_by: Group | None = Field(default=None,
        description='Grupo usado em maior/agrupar; departamento quando comparar departamentos.')
    departamento: str | None = Field(default=None, max_length=80)
    categoria: str | None = Field(default=None, max_length=80)
    centro_custo: str | None = Field(default=None, max_length=10)

    @model_validator(mode='after')
    def check_plan(self):
        if (self.start_month is None) != (self.end_month is None):
            raise ValueError('Intervalo mensal incompleto')
        if self.start_month is not None and self.start_month > self.end_month:
            raise ValueError('Intervalo mensal invertido')
        if self.operation in {'maior', 'agrupar'} and self.group_by is None:
            raise ValueError('Agrupamento obrigatório')
        if self.operation in {'contagem', 'soma'} and self.group_by is not None:
            raise ValueError('Agrupamento incompatível com a operação escolhida')
        if self.dataset == 'orcamentos':
            if self.transaction_type is not None or self.status is not None or self.categoria is not None:
                raise ValueError('Filtro inexistente na tabela de orçamentos')
            if self.group_by not in (None, 'departamento', 'centro_custo', 'mes'):
                raise ValueError('Agrupamento não permitido para orçamento')
        return self



def _brl(amount: Decimal) -> str:
    value = f'{amount:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
    return f'R$ {value}'


def _lookup_value(conn: sqlite3.Connection, table: str, column: str, raw: str | None) -> str | None:
    if not raw:
        return None
    # Identificadores de tabela e coluna são EXCLUSIVAMENTE constantes neste código.
    allowed = {
        'lancamentos_financeiros': {'departamento', 'categoria', 'centro_custo'},
        'orcamento_mensal': {'departamento', 'centro_custo'},
    }
    if column not in allowed.get(table, set()):
        raise ValueError('Filtro não permitido')
    rows = conn.execute(f'SELECT DISTINCT {column} FROM {table}').fetchall()
    names = [row[0] for row in rows]
    return next((v for v in names if normalize(v) == normalize(raw)), None)


def _validate_against_question(question: str, plan: FinancePlan) -> str | None:
    """Impede respostas quantitativas fabricadas por perda de filtros explícitos."""
    q = normalize(question)
    has_budget = bool(re.search(r'\borcamentos?\b', q))
    has_transaction = bool(re.search(r'\b(receitas?|despesas?|lancamentos?|faturamento)\b', q))
    if has_budget and has_transaction:
        return 'Para comparar orçamento e lançamentos, especifique primeiro qual base deseja consultar.'
    if has_budget and plan.dataset != 'orcamentos':
        # Erro de contrato para o agente, NAO e uma resposta ao usuario.
        # A intenção já era suficiente: não inventar pedido de Receita/Despesa.
        return ('PLANO_INCONSISTENTE: a pergunta pede orçamento mensal, '
                'que possui base própria (dataset=orcamentos), independente '
                'de receitas/despesas. Ajuste o plano e tente novamente '
                'antes de pedir esclarecimentos ao usuário.')
    if has_transaction and plan.dataset != 'lancamentos':
        return 'Não consegui confirmar que a pergunta se refere a lançamentos. Reformule a pergunta.'
    months = {'janeiro':1, 'fevereiro':2, 'marco':3, 'abril':4, 'maio':5, 'junho':6,
              'julho':7, 'agosto':8, 'setembro':9, 'outubro':10, 'novembro':11, 'dezembro':12}
    explicit = [value for name,value in months.items() if re.search(r'\b'+name+r'\b', q)]
    if explicit and (plan.start_month != min(explicit) or plan.end_month != max(explicit)):
        return 'Não consegui confirmar os meses da consulta. Reformule indicando o período.'
    mentioned_years = set(re.findall(r'\b20\d{2}\b', q))
    # Contrato de integridade: o plano não pode criar um ano que o usuário não informou.
    # O contexto pode incluir 'Pergunta original | Complemento: resposta curta'.
    # Se a resposta atual for '205', mesmo um ano antigo na pergunta original
    # NÃO autoriza a execução: solicite a confirmação do complemento.
    latest = question.rsplit(' | Complemento: ', 1)[-1].strip()
    if re.fullmatch(r'\d{1,3}', latest):
        return ('ANO_NAO_CONFIRMADO: a última mensagem informou "' + latest +
                '", que não é um ano com quatro dígitos. NÃO consulte o banco nem '
                'complete o número (por exemplo, 205 não é 2050). '
                'Peça ao usuário para confirmar o ano completo com uma pergunta natural.')
    if len(mentioned_years) > 1:
        return 'ANO_NAO_CONFIRMADO: há vários anos na solicitação; solicite esclarecimento.'
    if plan.year is not None and str(plan.year) not in mentioned_years:
        return ('ANO_NAO_CONFIRMADO: o ano ' + str(plan.year) +
                ' não foi informado pelo usuário em quatro dígitos. '
                'Não execute consulta com datas deduzidas; pergunte o ano correto.')
    if mentioned_years and plan.year is None:
        return 'ANO_NAO_CONFIRMADO: o ano mencionado não foi incluído no plano. Confirme os parâmetros.'
    # Intervalos mensais específicos só podem ser montados a partir do pedido.
    # Janeiro-dezembro pode representar o ano completo explicitamente solicitado.
    months_in_plan = (plan.start_month, plan.end_month)
    if months_in_plan not in ((None, None), (1, 12)) and not explicit:
        first_half = bool(re.search(r'\b(primeiro|1o|1) semestre\b', q))
        second_half = bool(re.search(r'\b(segundo|2o|2) semestre\b', q))
        if not ((first_half and months_in_plan == (1, 6)) or
                (second_half and months_in_plan == (7, 12))):
            return ('PERIODO_NAO_CONFIRMADO: os meses escolhidos não estão confirmados '
                    'na pergunta. Solicite o intervalo correto; não invente datas.')
    # Filtros com identificadores textuais devem estar presentes no texto do usuário.
    # Isto impede que a LLM acrescente nomes de departamento, categorias ou centros.
    for field in ('departamento', 'categoria', 'centro_custo'):
        selected = getattr(plan, field)
        if selected and normalize(selected) not in q:
            return ('FILTRO_NAO_CONFIRMADO: o valor de ' + field + ' ("' + selected +
                    '") não foi informado pelo usuário. Solicite confirmação do filtro.')
    if re.search(r'\bpor\s+departamento\b', q) and plan.group_by != 'departamento':
        return ('AGRUPAMENTO_NAO_CONFIRMADO: o usuário solicitou despesas por '
                'departamento; preserve esse agrupamento em vez de calcular um total geral.')
    if plan.dataset == 'lancamentos':
        if re.search(r'\b(receitas?|faturamento)\b', q) and plan.transaction_type != 'Receita':
            return 'Não consegui confirmar o tipo Receita. Reformule a pergunta.'
        if re.search(r'\b(despesas?)\b', q) and plan.transaction_type != 'Despesa':
            return 'Não consegui confirmar o tipo Despesa. Reformule a pergunta.'
        if re.search(r'\b(pagas?|pagos?|quitadas?|quitados?)\b', q) and plan.status != 'Pago':
            return 'Não consegui confirmar o filtro de pagamentos realizados. Reformule a pergunta.'
    return None


def execute_plan(database: Path, question: str, plan: FinancePlan) -> FinanceQueryResult:
    """Executa apenas SELECTs parametrizados e monta o resultado sem LLM."""
    method = 'llm_plano_sql'
    if plan.operation == 'nao_suportada':
        return FinanceQueryResult('Esta operação ainda não é suportada. Posso somar, contar e agrupar lançamentos ou orçamentos por um período.',
                           generation_method=method)
    failed = _validate_against_question(question, plan)
    if failed:
        return FinanceQueryResult(failed, generation_method=method)
    if plan.year is None:
        return FinanceQueryResult('Informe o ano para realizar uma consulta financeira sem presumir o período.',generation_method=method)
    start, end = plan.start_month or 1, plan.end_month or 12
    table = 'lancamentos_financeiros' if plan.dataset == 'lancamentos' else 'orcamento_mensal'
    source = 'lancamentos_financeiros.csv' if plan.dataset == 'lancamentos' else 'orcamento_mensal.csv'
    price = 'valor_brl' if plan.dataset == 'lancamentos' else 'orcamento_brl'
    conditions = []
    args: list[str | int] = []
    if plan.dataset == 'lancamentos':
        conditions.extend(['substr(data_competencia,1,4)=?', 'CAST(substr(data_competencia,6,2) AS INTEGER) BETWEEN ? AND ?'])
        args.extend([str(plan.year), start, end])
        if plan.transaction_type:
            conditions.append('tipo=?');args.append(plan.transaction_type)
        if plan.status:
            conditions.append('status=?');args.append(plan.status)
    else:
        conditions.extend(['ano=?', 'CAST(mes AS INTEGER) BETWEEN ? AND ?'])
        args.extend([plan.year, start, end])
    # Filtros validados contra valores existentes (e parametrizados no SQL).
    with closing(sqlite3.connect(database)) as conn:
        for col, raw in [('departamento',plan.departamento), ('categoria',plan.categoria), ('centro_custo',plan.centro_custo)]:
            if raw is None:
                continue
            value = _lookup_value(conn, table, col, raw)
            if value is None:
                return FinanceQueryResult(f'Não encontrei {col.replace("_", " ")} = "{raw}" na base consultada.',
                                   [Citation(source=source)],generation_method=method)
            conditions.append(f'{col}=?');args.append(value)
        # Os nomes de colunas da projeção são constantes; o texto do usuário jamais é SQL.
        group_month = ('substr(data_competencia,6,2) AS mes' if plan.dataset == 'lancamentos' else 'mes')
        fixed_columns = (f'{price},departamento,centro_custo' +
                         (',categoria,status' if plan.dataset == 'lancamentos' else '') + ',' + group_month)
        sql = f'SELECT {fixed_columns} FROM {table} WHERE ' + ' AND '.join(conditions)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, args).fetchall()
    citation = Citation(source=source,detail=f'{len(rows)} registros; {plan.year} meses {start:02d}–{end:02d}')
    if not rows:
        return FinanceQueryResult('Não há registros correspondentes aos filtros solicitados.',[citation],generation_method=method)
    title = 'lançamentos' if plan.dataset == 'lancamentos' else 'orçamentos'
    if plan.operation == 'contagem':
        return FinanceQueryResult(f'Total de {title}: {len(rows)} registros no período {plan.year}, meses {start:02d}–{end:02d}.',
                           [citation],generation_method=method)
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal('0.00'))
    for r in rows:
        group = str(r[plan.group_by]) if plan.group_by else 'total'
        totals[group] += Decimal(r[price])
    if plan.operation == 'maior':
        k = sorted(totals, key=lambda item: (-totals[item], normalize(item)))[0]
        answer = f'Maior {title} por {plan.group_by.replace("_", " ")}: {k}, com {_brl(totals[k])}.'
    elif plan.operation == 'agrupar':
        detail = '; '.join(f'{key}: {_brl(total)}' for key,total in
                           sorted(totals.items(),key=lambda item:(-item[1],normalize(item[0]))))
        answer = f'{title.capitalize()} por {plan.group_by.replace("_", " ")}: {detail}.'
    else:
        answer = f'Soma de {title}: {_brl(totals["total"])} ({len(rows)} registros).'
    answer += f' Período: {plan.year}, meses {start:02d}–{end:02d}. Valores sintéticos.'
    return FinanceQueryResult(answer,[citation],generation_method=method)
