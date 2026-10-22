"""Regressão v0.2.26: ferramenta não consulta anos, meses ou filtros inventados.

Testes offline não substituem integração com GPT-4.1 mini via Docker.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.sdk_integration.finance_queries import FinancePlan, execute_plan, _validate_against_question


def plan(year=2050, **kwargs) -> FinancePlan:
    return FinancePlan(dataset='lancamentos', operation='agrupar',
                       group_by='departamento', transaction_type='Despesa',
                       year=year, **kwargs)


@pytest.mark.parametrize('latest', ['205', '20', '5', '202'])
def test_incomplete_year_is_rejected_without_sql_even_if_llm_invents_2050(tmp_path, latest):
    nonexistent = tmp_path / 'never-opened.sqlite'
    result = execute_plan(nonexistent,
                          f'Quero despesas por departamento | Complemento: {latest}',
                          plan())
    assert not nonexistent.exists(), 'Nunca abrir banco em consulta com ano inferido'
    assert result.sources == []
    assert 'ANO_NAO_CONFIRMADO:' in result.text
    assert 'quatro dígitos' in result.text
    assert 'consulte o banco' in result.text


def test_year_not_present_even_if_request_says_last_year(tmp_path):
    db = tmp_path / 'never-opened.sqlite'
    result = execute_plan(db, 'Quero despesas por departamento do ano passado', plan(year=2025))
    assert not db.exists()
    assert not result.sources
    assert 'ANO_NAO_CONFIRMADO:' in result.text


def test_year_is_rejected_even_when_previous_context_contains_2025_but_latest_205(tmp_path):
    db = tmp_path / 'never-opened.sqlite'
    result = execute_plan(db, 'Quero despesas de 2025 por departamento | Complemento: 205', plan(year=2025))
    assert not db.exists()
    assert not result.sources
    assert 'ANO_NAO_CONFIRMADO:' in result.text


def test_different_year_than_user_confirmed_rejected_without_source(tmp_path):
    db = tmp_path / 'never-opened.sqlite'
    result = execute_plan(db, 'Despesas por departamento | Complemento: 2025', plan(year=2050))
    assert not db.exists()
    assert not result.sources
    assert 'ANO_NAO_CONFIRMADO:' in result.text


def test_extra_months_without_explicit_user_period_rejected():
    message = _validate_against_question('Despesas por departamento no ano 2025',
                 plan(year=2025, start_month=3, end_month=7))
    assert message and 'PERIODO_NAO_CONFIRMADO:' in message


def test_invented_department_filter_rejected():
    message = _validate_against_question('Despesas por departamento no ano 2025',
                 plan(year=2025, departamento='Tecnologia'))
    assert message and 'FILTRO_NAO_CONFIRMADO:' in message


def test_mentioned_department_and_month_range_are_allowed():
    assert _validate_against_question('Despesas de Tecnologia de fevereiro a maio de 2025',
              plan(year=2025, departamento='Tecnologia',start_month=2,end_month=5)) is None


def test_2050_is_valid_when_user_explicitly_says_2050():
    assert _validate_against_question('Despesas por departamento no ano 2050', plan(year=2050)) is None


def test_2025_runs_real_grouping_only_after_explicit_confirmation(tmp_path):
    db = tmp_path / 'financial.sqlite'
    with sqlite3.connect(db) as con:
        con.execute('''CREATE TABLE lancamentos_financeiros
              (data_competencia TEXT,tipo TEXT,status TEXT,valor_brl TEXT,
               departamento TEXT,centro_custo TEXT,categoria TEXT)''')
        con.executemany('''INSERT INTO lancamentos_financeiros
              VALUES (?,?,?,?,?,?,?)''', [
            ('2025-03-02','Despesa','Pago','100.00','Tecnologia','TI01','Serviços'),
            ('2025-04-02','Despesa','Pago','250.50','Comercial','CO01','Serviços'),
            ('2050-02-01','Despesa','Pago','999.00','Marketing','MA01','Serviços'),
        ])
    result=execute_plan(db,'Quero despesas por departamento | Complemento: 2025',plan(year=2025))
    assert result.sources and result.sources[0].source == 'lancamentos_financeiros.csv'
    assert 'Tecnologia: R$ 100,00' in result.text
    assert 'Comercial: R$ 250,50' in result.text
    assert 'Marketing' not in result.text
    assert '2025' in result.text


def test_department_grouping_cannot_be_dropped():
    incorrect = FinancePlan(dataset='lancamentos',operation='soma',year=2025,transaction_type='Despesa')
    msg = _validate_against_question('Despesas por departamento no ano 2025', incorrect)
    assert 'AGRUPAMENTO_NAO_CONFIRMADO:' in msg
