"""v0.2.18: conversação em sessão e proteções, com Runner SIMULADO/offline."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.knowledge.ingest import bootstrap
from app.sdk_integration.finance_queries import FinancePlan
from app.sdk_integration.session_memory import SessionMemory
from app.sdk_integration.service import (
    SdkChatService, _orchestrator_response, _plain_text, SOCIAL_ANSWERS,
)
from app.sdk_integration.tools import consultar_financeiro

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'data' / 'knowledge'


def response(name, text, *, handoff=False, tool=None):
    items = []
    if handoff:
        items.append(SimpleNamespace(type='handoff_call_item', raw_item=SimpleNamespace(
            name='transfer_to_' + name.lower())))
    if tool:
        items.append(SimpleNamespace(type='tool_call_item', raw_item=SimpleNamespace(name=tool)))
    return SimpleNamespace(last_agent=SimpleNamespace(name=name), final_output=text,
                           new_items=items, context_wrapper=SimpleNamespace(usage=SimpleNamespace(
                           requests=3, input_tokens=350, output_tokens=65, total_tokens=415)))


def make_service(tmp_path, runner):
    database = tmp_path / 'knowledge.sqlite'
    bootstrap(KB, database)
    svc = SdkChatService.__new__(SdkChatService)
    svc.runner = runner
    svc.run_config_type = lambda **kwargs: SimpleNamespace(**kwargs)
    svc.orchestrator = SimpleNamespace(name='Orquestrador')
    svc.database = database
    svc.knowledge_dir = KB
    svc.sessions = SessionMemory()
    return svc


def test_markers_allow_esclarecimento_without_factual_answer():
    domain, text = _orchestrator_response('ESCLARECER: Claro! Qual ano deseja consultar?')
    assert (domain, text) == ('esclarecimento', 'Claro! Qual ano deseja consultar?')
    assert _orchestrator_response('ESCLARECER: resposta sem pergunta') == (
        'esclarecimento', 'Claro! Pode me dar mais detalhes sobre o que você gostaria de consultar?')
    assert _plain_text('A **política** exige *30 dias*.') == 'A política exige 30 dias.'
    assert SOCIAL_ANSWERS['SAUDACAO:'] == 'Olá! Seja bem-vindo(a). Como posso te ajudar hoje?'


def test_memory_bounds_and_expiration():
    mem = SessionMemory(max_sessions=2, max_exchanges=2, ttl_seconds=1800)
    s = mem.get('a')
    for index in range(3):
        s.record(f'pergunta {index}', f'resposta {index}', needs_clarification=False,
                 reset_pending=True, max_exchanges=mem.max_exchanges)
    assert len(s.history) == 4
    assert s.history[0]['content'] == 'pergunta 1'
    mem.get('b')
    mem.get('c')
    assert 'a' not in mem._sessions
    mem._sessions['c'].updated -= 1801
    mem.get('d')
    assert 'c' not in mem._sessions


def test_clarifications_keep_pending_until_data_query():
    mem = SessionMemory()
    s = mem.get('same')
    s.record('Quero saber sobre despesas', 'Quais?', needs_clarification=True,
             reset_pending=True, max_exchanges=5)
    assert 'despesas' in s.contextual_question('O total de 2025')
    s.record('O total de 2025', 'R$ 1', needs_clarification=False,
             reset_pending=True, max_exchanges=5)
    assert s.contextual_question('E mais?') == 'E mais?'


def test_session_followup_handoff_carries_question_to_financial_plan(tmp_path):
    class Runner:
        inputs = []
        @staticmethod
        async def run(_, input_, *, context, **kwargs):
            Runner.inputs.append(input_)
            if len(Runner.inputs) == 1:
                return response('Orquestrador',
                                'ESCLARECER: Claro! Você quer consultar o total gasto ou por categoria?')
            assert isinstance(input_, list) and len(input_) == 3
            assert input_[0] == {'role':'user','content':'Gostaria de saber sobre algumas despesas'}
            assert 'despesas' in context.question and '2025' in context.question
            result = consultar_financeiro(context, FinancePlan(
                dataset='lancamentos', operation='soma', year=2025,
                transaction_type='Despesa'))
            assert 'Soma de lançamentos' in result
            return response('Financeiro', '**Soma de despesas:** ' + result,
                            handoff=True, tool='consultar_financeiro')
    svc = make_service(tmp_path, Runner)

    async def run():
        first = await svc.chat('Gostaria de saber sobre algumas despesas', session_id='aba-A')
        second = await svc.chat('O total de 2025', session_id='aba-A')
        assert first.domain == 'esclarecimento'
        assert not first.sources and not first.handoffs
        assert second.domain == 'financeiro'
        assert second.handoffs == ['transfer_to_financeiro']
        assert second.sources[0].source == 'lancamentos_financeiros.csv'
        assert '*' not in second.answer
        assert second.session_id == 'aba-A'
    asyncio.run(run())


def test_session_isolation_and_legacy_independence(tmp_path):
    class Runner:
        inputs = []
        @staticmethod
        async def run(_, input_, **kwargs):
            Runner.inputs.append(input_)
            return response('Orquestrador', 'AMBIGUO: Pode esclarecer?')
    svc = make_service(tmp_path, Runner)

    async def run():
        await svc.chat('Qual é o prazo?', session_id='first')
        await svc.chat('Sobre o processo', session_id='second')
        await svc.chat('De férias', session_id='first')
        await svc.chat('Qual é o prazo?')
    asyncio.run(run())
    assert isinstance(Runner.inputs[0], str)
    assert isinstance(Runner.inputs[1], str)
    assert isinstance(Runner.inputs[2], list)
    assert len(Runner.inputs[2]) == 3
    assert isinstance(Runner.inputs[3], str)


def test_specialist_can_ask_before_using_tool(tmp_path):
    class Runner:
        @staticmethod
        async def run(_, input_, **kwargs):
            return response('Ouvidoria', 'ESCLARECER: Qual é o número do protocolo?', handoff=True)
    svc = make_service(tmp_path, Runner)
    r = asyncio.run(svc.chat('Quero saber meu protocolo', session_id='c'))
    assert r.domain == 'esclarecimento'
    assert r.generation_method == 'agents_sdk_esclarecimento'
    assert r.sources == r.tools_used == []
    assert r.handoffs == ['transfer_to_ouvidoria']


def test_specialist_cannot_assert_fake_facts_without_sources(tmp_path):
    class Runner:
        @staticmethod
        async def run(_, input_, **kwargs):
            return response('Financeiro', 'Receita de **R$ 1 milhão**', handoff=True)
    svc = make_service(tmp_path, Runner)
    r = asyncio.run(svc.chat('Quanto foi a receita em 2025?', session_id='a'))
    assert r.domain == 'financeiro'
    assert '1 milhão' not in r.answer
    assert r.generation_method == 'sdk_sem_evidencia'


def test_backend_http_forwards_session_id(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.schemas import ChatResponse
    from app import main as main_module
    class FakeService:
        agents = {'financeiro':True,'informacoes_internas':True,'ouvidoria':True}
        async def chat(self, message, session_id=None):
            assert session_id == 'sessao-teste' and message == 'Olá'
            return ChatResponse(request_id='req', answer='Olá!', domain='conversa',
                session_id=session_id, agent=None, classification_method='agents_sdk_orquestrador',
                confidence=0.0, latency_ms=1)
    monkeypatch.setattr(main_module, 'bootstrap', lambda *_: {})
    monkeypatch.setattr(main_module, 'SdkChatService', lambda *_: FakeService())
    with TestClient(app) as client:
        body = client.post('/api/v1/chat', json={'message':'Olá','session_id':'sessao-teste'})
        assert body.status_code == 200
        assert body.json()['session_id'] == 'sessao-teste'


def test_frontend_uses_ephemeral_session_id():
    js = (ROOT / 'frontend' / 'app.js').read_text(encoding='utf-8')
    assert 'crypto.randomUUID()' in js
    assert 'session_id:sessionId' in js
    assert 'localStorage' not in js.replace('localStorage/cookies','')
