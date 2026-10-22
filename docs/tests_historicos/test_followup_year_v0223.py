"""v0.2.23: regressao do relato real: saudacao informal e ano corrigido.

Nao substitui validacao ao vivo: o Runner aqui e simulado; afirma o payload
entregue ao SDK, o uso da ferramenta e a manutencao do contexto por sessao.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
import pytest

from app.sdk_integration.service import _social_intent, SOCIAL_ANSWERS
from app.sdk_integration.finance_queries import FinancePlan
from app.sdk_integration.tools import consultar_financeiro
from tests.test_browser_regression_v0219 import create_service, result


@pytest.mark.parametrize('message', [
    'ola td bem', 'olá td bem?', 'Oi td bem!', 'td bem', 'Opa td bem',
    'olá tudo certo?', 'Olá td bem e vc?', 'ola td berm', 'ola td bemm',
])
def test_informal_greeting_is_entirely_social(message):
    assert _social_intent(message) == 'SAUDACAO:'


@pytest.mark.parametrize('message', [
    'ola td bem gostaria de saber sobre despesas',
    'Oi td bem, qual o status do OUV-0002?',
    'ola td bem me diga uma senha',
])
def test_social_greeting_with_substantive_request_is_not_social(message):
    assert _social_intent(message) is None


def test_informal_greeting_even_when_llm_returns_ambiguity(tmp_path):
    class FakeRunner:
        @staticmethod
        async def run(*_, **__):
            return result('Orquestrador', 'AMBIGUO: Você quer consultar Financeiro, Informações Internas ou Ouvidoria?')

    service = create_service(tmp_path, FakeRunner)
    reply = asyncio.run(service.chat('ola td bem', session_id='Saudacao'))
    assert reply.domain == 'conversa'
    assert reply.answer == SOCIAL_ANSWERS['SAUDACAO:']
    assert reply.handoffs == reply.tools_used == reply.sources == []


def test_year_typo_then_correct_year_passes_full_financial_request_to_sdk(tmp_path):
    class FakeRunner:
        count = 0

        @staticmethod
        async def run(agent, prompt, *, context, **kwargs):
            FakeRunner.count += 1
            if FakeRunner.count == 1:
                assert prompt == 'Quero consultar o total de despesas do departamento de Tecnologia'
                return result('Orquestrador', 'ESCLARECER: De qual ano deseja consultar as despesas do departamento de Tecnologia?')
            assert FakeRunner.count == 2, '205 deve ser validado sem chamar a OpenAI'
            assert isinstance(prompt, list)
            assert 'Quero consultar o total de despesas do departamento de Tecnologia' in prompt[-1]['content']
            assert 'no ano de 2025' in prompt[-1]['content']
            assert '205' not in prompt[-1]['content']
            assert context.question == prompt[-1]['content']
            output = consultar_financeiro(context, FinancePlan(
                dataset='lancamentos', operation='soma', year=2025,
                transaction_type='Despesa', departamento='Tecnologia'))
            assert 'Soma de lançamentos' in output
            return result('Financeiro', output, handoff='financeiro', tool='consultar_financeiro')

    svc = create_service(tmp_path, FakeRunner)
    async def run():
        first = await svc.chat('Quero consultar o total de despesas do departamento de Tecnologia', session_id='TesteAno')
        assert first.domain == 'esclarecimento'
        invalid = await svc.chat('205', session_id='TesteAno')
        assert invalid.domain == 'esclarecimento'
        assert invalid.token_usage['requests'] == 0
        final = await svc.chat('2025', session_id='TesteAno')
        assert final.domain == 'financeiro'
        assert {s.source for s in final.sources} == {'lancamentos_financeiros.csv'}
        assert final.tools_used == ['consultar_financeiro']
        assert '234.196,14' in final.answer  # valor calculado com filtro Tecnologia
        history = svc.sessions.get('TesteAno').history
        assert history[-2]['content'] == '2025', 'O histórico deve registrar o que o usuario digitou'
        assert svc.sessions.get('TesteAno').pending_questions == []
        assert FakeRunner.count == 2
    asyncio.run(run())


def test_pending_department_grouping_year_is_contextualized(tmp_path):
    class FakeRunner:
        count = 0
        @staticmethod
        async def run(agent, prompt, *, context, **kwargs):
            FakeRunner.count += 1
            if FakeRunner.count == 1:
                return result('Orquestrador', 'ESCLARECER: Total, categoria ou departamento?')
            if FakeRunner.count == 2:
                return result('Orquestrador', 'ESCLARECER: De qual ano deseja ver as despesas por departamento?')
            assert FakeRunner.count == 3
            assert 'despesas' in prompt[-1]['content'].lower()
            assert 'departamento' in prompt[-1]['content'].lower()
            assert '2025' in prompt[-1]['content']
            answer = consultar_financeiro(context, FinancePlan(
                dataset='lancamentos', operation='agrupar', year=2025,
                transaction_type='Despesa', group_by='departamento'))
            assert 'por departamento' in answer
            return result('Financeiro', answer, handoff='financeiro', tool='consultar_financeiro')

    svc = create_service(tmp_path, FakeRunner)
    async def run():
        await svc.chat('Gostaria de consultar despesas', session_id='dept')
        await svc.chat('departamento', session_id='dept')
        typo = await svc.chat('205', session_id='dept')
        assert typo.classification_method == 'validacao_entrada_local'
        response = await svc.chat('2025', session_id='dept')
        assert response.domain == 'financeiro'
        assert 'departamento' in response.answer
        assert response.sources
    asyncio.run(run())
