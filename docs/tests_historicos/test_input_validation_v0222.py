"""Regressão v0.2.22: digitação inválida não apaga o assunto nem aciona LLM."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.sdk_integration.input_guard import evaluate
from app.sdk_integration.session_memory import SessionMemory
from app.sdk_integration.tools import consultar_financeiro, buscar_protocolo
from app.sdk_integration.finance_queries import FinancePlan
from tests.test_browser_regression_v0219 import create_service, result


def test_year_typo_then_corrected_year_queries_source(tmp_path):
    class FakeRunner:
        calls = 0

        @staticmethod
        async def run(agent, prompt, *, context, **kwargs):
            FakeRunner.calls += 1
            if FakeRunner.calls == 1:
                return result('Orquestrador', 'ESCLARECER: De qual ano deseja consultar as despesas da Tecnologia?')
            assert FakeRunner.calls == 2, 'Ano incompleto não deve chamar o SDK'
            assert '2025' in context.question and 'Tecnologia' in context.question
            assert '205' not in context.question
            answer = consultar_financeiro(context, FinancePlan(
                dataset='lancamentos', operation='soma', year=2025,
                transaction_type='Despesa', departamento='Tecnologia'))
            assert 'FONTE' in answer
            return result('Financeiro', answer, handoff='financeiro', tool='consultar_financeiro')

    service = create_service(tmp_path, FakeRunner)
    async def go():
        first = await service.chat('Quero o total de despesas da Tecnologia', session_id='A')
        assert first.domain == 'esclarecimento'
        before = list(service.sessions.get('A').pending_questions)
        typo = await service.chat('205', session_id='A')
        assert typo.domain == 'esclarecimento'
        assert typo.trace_id is None and typo.token_usage['requests'] == 0
        assert 'quatro dígitos' in typo.answer
        assert service.sessions.get('A').pending_questions == before
        good = await service.chat('2025', session_id='A')
        assert good.domain == 'financeiro'
        assert {s.source for s in good.sources} == {'lancamentos_financeiros.csv'}
        assert 'Soma de lançamentos' in good.answer
        assert service.sessions.get('A').pending_questions == []
        assert FakeRunner.calls == 2
    asyncio.run(go())


def test_protocol_format_never_guesses_or_queries_wrong_code(tmp_path):
    class FakeRunner:
        calls = 0
        @staticmethod
        async def run(agent, prompt, *, context, **kwargs):
            FakeRunner.calls += 1
            if FakeRunner.calls == 1:
                return result('Orquestrador', 'ESCLARECER: Qual é o número do protocolo?')
            assert FakeRunner.calls == 2
            answer = buscar_protocolo(context, 'OUV-0013')
            assert 'OUV-0013' in answer
            return result('Ouvidoria', answer, handoff='ouvidoria', tool='buscar_protocolo')

    service = create_service(tmp_path, FakeRunner)
    async def go():
        first = await service.chat('Quero consultar um protocolo da Ouvidoria', session_id='P')
        assert first.domain == 'esclarecimento'
        typo = await service.chat('OUV-013', session_id='P')
        assert typo.domain == 'esclarecimento' and typo.trace_id is None
        assert 'OUV-NNNN' in typo.answer and 'OUV-0013' not in typo.answer
        valid = await service.chat('OUV-0013', session_id='P')
        assert valid.domain == 'ouvidoria'
        assert 'manifestacoes.csv' in {s.source for s in valid.sources}
        assert FakeRunner.calls == 2
    asyncio.run(go())


def test_department_typo_requires_confirmation_and_isolated(tmp_path):
    class FakeRunner:
        calls = 0
        @staticmethod
        async def run(agent, prompt, *, context, **kwargs):
            FakeRunner.calls += 1
            if FakeRunner.calls == 1:
                return result('Orquestrador', 'ESCLARECER: De qual departamento você quer consultar as despesas?')
            assert FakeRunner.calls == 2
            assert 'Tecnologia' in context.question
            assert 'tecnolgia' not in context.question
            answer = consultar_financeiro(context, FinancePlan(dataset='lancamentos',
                  operation='soma', year=2025, departamento='Tecnologia', transaction_type='Despesa'))
            return result('Financeiro', answer, handoff='financeiro', tool='consultar_financeiro')
    service = create_service(tmp_path, FakeRunner)
    async def go():
        await service.chat('Quero consultar o total de despesas em 2025', session_id='A')
        reply = await service.chat('tecnolgia', session_id='A')
        assert reply.domain == 'esclarecimento'
        assert reply.answer == 'Você quis dizer o departamento Tecnologia?'
        assert service.sessions.get('B').pending_confirmation is None
        answer = await service.chat('sim', session_id='A')
        assert answer.domain == 'financeiro'
        assert answer.sources and 'Soma de lançamentos' in answer.answer
        assert service.sessions.get('A').pending_confirmation is None
        assert FakeRunner.calls == 2
    asyncio.run(go())


def test_invalid_fields_and_non_premature_corrections(tmp_path):
    service = create_service(tmp_path, SimpleNamespace())
    state = service.sessions.get('X')
    database = service.database
    state.record('Quero consultar despesas', 'Qual mês deseja consultar?',
                 needs_clarification=True, reset_pending=True, max_exchanges=30)
    assert 'mês 13' in evaluate('mês 13', state, database).answer
    assert 'mês 14' in evaluate('14', state, database).answer
    assert 'invertido' in evaluate('março a janeiro', state, database).answer
    assert evaluate('março a abril', state, database) is None
    assert evaluate('mês 12', state, database) is None
    assert evaluate('204', state, database) is None  # Não havia pedido de ano
    assert evaluate('OUV-013', state, database).answer.endswith('outro registro.')
    assert evaluate('OUV-0013', state, database) is None
    assert evaluate('tecnologia', state, database) is None
    assert evaluate('2025', state, database) is None
    # O guard não fabrica identificadores, valores ou casos financeiros.
    assert evaluate('quero saber como solicitar férias', state, database) is None


def test_department_confirmation_rejected_requires_new_value(tmp_path):
    service = create_service(tmp_path, SimpleNamespace())
    state = service.sessions.get('A')
    state.record('Quero despesas por departamento de 2025', 'Qual departamento deseja consultar?',
                 needs_clarification=True, reset_pending=True, max_exchanges=30)
    first = evaluate('tecnolgia', state, service.database)
    assert 'Tecnologia' in first.answer
    assert state.pending_confirmation == 'Tecnologia'
    rejection = evaluate('não', state, service.database)
    assert 'nome correto' in rejection.answer
    assert state.pending_confirmation is None
    assert evaluate('Comercial', state, service.database) is None


def test_ambiguous_ten_thousand_requires_unit(tmp_path):
    service = create_service(tmp_path, SimpleNamespace())
    state = service.sessions.get('A')
    state.record('quero saber sobre algumas despesas', 'Qual informação deseja consultar?',
                 needs_clarification=True, reset_pending=True, max_exchanges=30)
    answer = evaluate('10 mil', state, service.database)
    assert 'R$ 10 mil' in answer.answer and '10 mil registros' in answer.answer
