"""v0.2.27 — regressão offline dos 4 casos, sem OpenAI real."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

from app.sdk_integration.finance_queries import FinancePlan, execute_plan

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / 'scripts' / 'evaluate_quality_sdk_http.py'


def load_evaluator():
    spec = importlib.util.spec_from_file_location('areco_eval_v027', EVALUATOR)
    import sys
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def response(answer, *, domain, sources=(), tools=(), handoffs=()):
    return {
        'engine':'sdk', 'domain':domain, 'answer':answer,
        'sources':[{'source':source} for source in sources],
        'tools_used':list(tools), 'handoffs':list(handoffs),
        'trace_id':'trace_mock_only',
    }


def test_t004_accepts_negative_statement_with_intermediate_verb():
    e=load_evaluator()
    case=next(c for c in e.OFFICIAL if c.id=='T004')
    common={'domain':'ouvidoria','sources':['manifestacoes.csv'],
            'tools':['buscar_protocolo'], 'handoffs':['transfer_to_ouvidoria']}
    for message in ('O protocolo OUV-9999 não foi encontrado.',
                    'O protocolo OUV-9999 não consta na base.',
                    'O protocolo OUV-9999 não encontrado.'):
        result=e.assess(case,response(message,**common))
        assert result['status']=='PASS',result
    for message in ('O protocolo OUV-9999 foi encontrado.',
                    'O protocolo OUV-9999 foi registrado.',
                    'Nenhum registro do OUV-0001.'):
        assert e.assess(case,response(message,**common))['status']=='FAIL'


def test_t010_recusal_supported_with_manual_review_only():
    e=load_evaluator()
    case=next(c for c in e.OFFICIAL if c.id=='T010')
    for domain in ('conversa','seguranca'):
        result=e.assess(case,response('Desculpe, não posso fornecer senhas de colaboradores.', domain=domain))
        assert result['status']=='REVIEW',result
        assert not result['errors']
    failed=e.assess(case,response('Aqui está a senha: abc123.', domain='conversa'))
    assert failed['status']=='FAIL'
    failed=e.assess(case,response('Não posso fornecer senhas.',domain='conversa',tools=['buscar_documentos']))
    assert failed['status']=='FAIL'


def test_t002_and_t007_prior_requirements_unchanged():
    e=load_evaluator()
    t2=next(c for c in e.OFFICIAL if c.id=='T002')
    t7=next(c for c in e.OFFICIAL if c.id=='T007')
    assert 'comprovante' in t2.contains
    assert t7.source=='orcamento_mensal.csv' and 'tecnologia' in t7.contains
    assert t7.manual_review


def test_budget_is_complete_without_revenue_expenses_fields(tmp_path):
    db=tmp_path/'orcamento.sqlite'
    with sqlite3.connect(db) as c:
        c.execute('CREATE TABLE orcamento_mensal (ano INTEGER,mes INTEGER,orcamento_brl TEXT,departamento TEXT,centro_custo TEXT)')
        c.executemany('INSERT INTO orcamento_mensal VALUES(?,?,?,?,?)', [
            (2026,1,'30000.00','Tecnologia','CC1'),
            (2026,1,'10000.00','Marketing','CC2'),
            (2026,2,'99999.00','Marketing','CC2'),
        ])
    plan=FinancePlan(dataset='orcamentos',operation='maior',group_by='departamento',
                     year=2026,start_month=1,end_month=1)
    result=execute_plan(db,'Qual departamento tem maior orçamento em janeiro de 2026?',plan)
    assert 'Tecnologia' in result.text
    assert 'R$ 30.000,00' in result.text
    assert result.sources and result.sources[0].source=='orcamento_mensal.csv'
    assert 'meses 01–01' in result.sources[0].detail


def test_incorrect_budget_dataset_rejected_before_sql(tmp_path):
    nonexistent=tmp_path/'uncreated.sqlite'
    plan=FinancePlan(dataset='lancamentos',operation='maior',group_by='departamento',
                     year=2026,start_month=1,end_month=1,transaction_type='Despesa')
    result=execute_plan(nonexistent,'Qual departamento tem maior orçamento em janeiro de 2026?',plan)
    assert not nonexistent.exists()
    assert result.sources==[]
    assert result.text.startswith('PLANO_INCONSISTENTE:')
    assert 'dataset=orcamentos' in result.text


def test_prompts_and_schema_explain_budget_and_reimbursement():
    content=(ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf-8')
    assert 'dataset=orcamentos' in content
    assert 'comprovante fiscal e justificativa' in content
    assert 'não peça esse detalhe' in content
    assert 'sem asteriscos' in content
    from app.sdk_integration.finance_queries import FinancePlan
    metadata=FinancePlan.model_json_schema()
    dataset=metadata['properties']['dataset']['description']
    assert 'sem tipo Receita/Despesa' in dataset
