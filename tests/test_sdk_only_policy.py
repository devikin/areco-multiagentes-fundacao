"""Guardrails de regressão da migração: somente Agents SDK atende o chat."""
from pathlib import Path
from pydantic import ValidationError
import pytest
from app.sdk_integration.finance_queries import FinancePlan
from app.sdk_integration.tools import ExecutionContext, consultar_financeiro
from app.knowledge.ingest import bootstrap

ROOT = Path(__file__).resolve().parents[1]


def test_no_legacy_service_router_or_direct_llm_adapter():
    for obsolete in (
        'app/service.py', 'app/orchestration', 'app/agents',
        'app/services', 'poc_agents_sdk', 'requirements-sdk.txt'
    ):
        assert not (ROOT / obsolete).exists(), f'Módulo obsoleto: {obsolete}'
    code = (ROOT / 'app/main.py').read_text(encoding='utf-8')
    assert 'from app.sdk_integration.service import SdkChatService' in code
    assert 'run_in_threadpool' not in code
    assert 'app.state.chat_service = SdkChatService' in code


def test_agents_sdk_required_by_default():
    assert 'openai-agents' in (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    assert 'AGENT_ENGINE=legacy' not in (ROOT / '.env.example').read_text(encoding='utf-8')


def test_finance_plan_blocks_arbitrary_sql():
    with pytest.raises(ValidationError):
        FinancePlan(dataset='lancamentos', operation='soma', sql='DROP TABLE manifestacoes_ouvidoria')


def test_finance_plan_rejects_invalid_date_interval():
    with pytest.raises(ValidationError):
        FinancePlan(dataset='lancamentos', operation='soma', year=2025, start_month=6, end_month=2)


def test_finance_plan_rejects_invalid_budget_filters():
    with pytest.raises(ValidationError):
        FinancePlan(dataset='orcamentos', operation='soma', year=2026, status='Pago')


def test_finance_tool_without_year_requests_clarification(tmp_path):
    db = tmp_path / 'knowledge.sqlite'
    kb = ROOT / 'data/knowledge'
    bootstrap(kb, db)
    ctx = ExecutionContext(db, kb, 'Quanto foi gasto em despesas pagas?')
    result = consultar_financeiro(ctx, FinancePlan(dataset='lancamentos', operation='soma', transaction_type='Despesa', status='Pago'))
    assert 'Informe o ano' in result
    assert ctx.sources == []
    assert ctx.control_answer and 'Informe o ano' in ctx.control_answer


def test_finance_tool_query_exact_result_no_model_math(tmp_path):
    db = tmp_path / 'knowledge.sqlite'
    kb = ROOT / 'data/knowledge'
    bootstrap(kb, db)
    question = 'Quanto foi gasto em despesas pagas de janeiro a março de 2025?'
    ctx = ExecutionContext(db, kb, question)
    result = consultar_financeiro(ctx, FinancePlan(
        dataset='lancamentos', operation='soma', year=2025,
        start_month=1, end_month=3, status='Pago', transaction_type='Despesa'))
    assert 'R$ 305.937,01' in result
    assert 'lancamentos_financeiros.csv' in result
    assert ctx.tools_used == ['consultar_financeiro']
