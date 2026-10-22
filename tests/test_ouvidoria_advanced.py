"""Validação offline das ferramentas Ouvidoria v0.2.7; sem rede ou LLM."""
from pathlib import Path
import sqlite3
from pydantic import ValidationError
import pytest

from app.sdk_integration.ouvidoria_queries import OuvidoriaPlan
from app.sdk_integration.tools import ExecutionContext, consultar_manifestacoes, buscar_protocolo

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'data' / 'knowledge'


@pytest.fixture
def ctx(prepared):
    _, _, db = prepared
    return ExecutionContext(db, KB, 'Quantas manifestações de prioridade Alta existem?')


def test_count_high_priority_real_data(ctx):
    response = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem', prioridade='Alta'))
    assert '38' in response
    assert ctx.tools_used == ['consultar_manifestacoes']
    assert ctx.sources[0].source == 'manifestacoes.csv'


def test_group_by_priority_matches_base(ctx):
    ctx.question = 'Distribua as manifestações por prioridade.'
    response = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='agrupar', agrupar_por='prioridade'))
    for expected in ('Média: 79', 'Baixa: 55', 'Alta: 38', 'Crítica: 8'):
        assert expected in response
    assert '(180 registros)' in response


def test_group_status_exact_sum(ctx):
    ctx.question = 'Quantas manifestações há por status?'
    response = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='agrupar', agrupar_por='status'))
    assert 'Em análise: 47' in response
    assert '(180 registros)' in response


def test_filtered_list_limited_to_three_and_source(ctx):
    ctx.question = 'Liste manifestações da categoria Privacidade em 2026'
    plan = OuvidoriaPlan(operacao='listar', categoria='Privacidade',
                         data_inicio='2026-01-01', data_fim='2026-12-31', limite=3)
    result = consultar_manifestacoes(ctx, plan)
    assert result.count('protocolo: OUV-') == 3
    assert 'Exibindo 3 de 22' in result
    assert 'FONTE: manifestacoes.csv' in result


def test_filters_by_area_without_sql_injection(ctx):
    ctx.question = 'Mostre os casos da área Encarregado de Dados'
    response = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='listar',
                                   area_responsavel='encarregado de dados', limite=2))
    assert 'Encarregado de Dados' in response
    assert 'Exibindo 2 de 22' in response
    ctx2 = ExecutionContext(ctx.database, KB, 'Mostre os casos da área abc\' OR 1=1 --')
    blocked = consultar_manifestacoes(ctx2, OuvidoriaPlan(operacao='listar',
                                             area_responsavel="abc' OR 1=1 --"))
    assert 'Área responsável não encontrada' in blocked
    assert 'Exibindo 2' not in blocked


def test_empty_result_has_source_and_no_invented_protocols(ctx):
    ctx.question = 'Liste manifestações Abertas em janeiro de 2025'
    response = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='listar',
        status='Aberto', data_inicio='2025-01-01', data_fim='2025-01-31'))
    assert 'Nenhuma manifestação' in response
    assert 'OUV-' not in response
    assert ctx.sources and ctx.sources[0].source == 'manifestacoes.csv'


def test_invalid_schema_and_extra_sql_rejected():
    for fields in [
        {'operacao':'agrupar'},
        {'operacao':'contagem', 'agrupar_por':'status'},
        {'operacao':'listar','limite':10000},
        {'operacao':'contagem','sql':'DELETE FROM manifestacoes_ouvidoria'},
        {'operacao':'listar','status':'Arquivado'},
        {'operacao':'listar','data_inicio':'2026-12-31','data_fim':'2026-01-01'},
    ]:
        with pytest.raises(ValidationError):
            OuvidoriaPlan.model_validate(fields)


def test_no_dropped_explicit_priority_filter(ctx):
    response = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem'))
    assert 'Não consegui confirmar o filtro' in response
    assert not ctx.sources
    assert ctx.control_answer == response


def test_no_dropped_year_month_or_category(ctx):
    ctx.question = 'Quantas manifestações de categoria Privacidade em setembro de 2026?'
    result = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem'))
    assert 'Não consegui confirmar' in result
    assert not ctx.sources
    ctx.question = 'Quantas manifestações de categoria Privacidade em setembro de 2026?'
    result = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem',
        categoria='Privacidade', data_inicio='2026-09-01',data_fim='2026-09-30'))
    assert 'FONTE: manifestacoes.csv' in result


def test_relative_dates_require_explicit_range(ctx):
    ctx.question = 'Quantas manifestações tivemos ontem?'
    result = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem'))
    assert 'datas de início e fim' in result
    assert not ctx.sources


def test_date_field_response_works(ctx):
    ctx.question = 'Quantas manifestações tiveram data de resposta em setembro de 2026?'
    plan = OuvidoriaPlan(operacao='contagem', campo_data='data_resposta',
                         data_inicio='2026-09-01',data_fim='2026-09-30')
    response = consultar_manifestacoes(ctx, plan)
    assert 'Total de manifestações' in response
    assert ctx.sources[0].source == 'manifestacoes.csv'


def test_existing_exact_protocol_still_works(ctx):
    response = buscar_protocolo(ctx, 'OUV-0002')
    assert 'Aguardando área responsável' in response
    assert ctx.sources[-1].detail == 'OUV-0002'


def test_no_sql_mutation(ctx):
    plan = OuvidoriaPlan(operacao='contagem')
    consultar_manifestacoes(ctx, plan)
    with sqlite3.connect(ctx.database) as conn:
        assert conn.execute('SELECT COUNT(*) FROM manifestacoes_ouvidoria').fetchone()[0] == 180


def test_unfiltered_count_still_works_with_unified_tool(ctx):
    ctx.question = 'Quantas manifestações existem no total?'
    output = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem'))
    assert '180' in output
    assert ctx.tools_used == ['consultar_manifestacoes']
    assert ctx.sources[0].source == 'manifestacoes.csv'


def test_priority_distribution_cannot_be_replaced_by_total(ctx):
    ctx.question = 'Distribua as manifestações da Ouvidoria por prioridade.'
    output = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='contagem'))
    assert 'Não consegui confirmar o agrupamento' in output
    assert not ctx.sources
    assert ctx.control_answer == output


def test_priority_distribution_must_match_group(ctx):
    ctx.question = 'Distribua as manifestações da Ouvidoria por prioridade.'
    output = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='agrupar', agrupar_por='status'))
    assert 'Não consegui confirmar o agrupamento' in output
    assert not ctx.sources


def test_priority_distribution_from_database(ctx):
    ctx.question = 'Distribua as manifestações da Ouvidoria por prioridade.'
    output = consultar_manifestacoes(ctx, OuvidoriaPlan(operacao='agrupar', agrupar_por='prioridade'))
    assert 'Média: 79' in output
    assert 'Baixa: 55' in output
    assert 'Alta: 38' in output
    assert 'Crítica: 8' in output
    assert ctx.sources
