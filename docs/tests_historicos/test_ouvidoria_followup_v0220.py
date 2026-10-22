"""v0.2.20: 30 trocas, textos UI, e seguimento com evidência local."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.knowledge.ingest import bootstrap
from app.sdk_integration.grounded_followup import confirmar_limite_reembolso_ouvidoria
from app.sdk_integration.service import SdkChatService
from app.sdk_integration.session_memory import SessionMemory
from app.sdk_integration.tools import ExecutionContext, buscar_protocolo

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / 'data' / 'knowledge'


def response(agent, answer, *, handoff=None, tool=None):
    events = []
    if handoff:
        events.append(SimpleNamespace(type='handoff_call_item', raw_item=SimpleNamespace(name='transfer_to_'+handoff)))
    if tool:
        events.append(SimpleNamespace(type='tool_call_item', raw_item=SimpleNamespace(name=tool)))
    return SimpleNamespace(
        last_agent=SimpleNamespace(name=agent), final_output=answer, new_items=events,
        context_wrapper=SimpleNamespace(usage=SimpleNamespace(
            requests=2, input_tokens=400, output_tokens=30, total_tokens=430)))


def make_service(tmp_path, runner):
    db = tmp_path / 'knowledge.sqlite'
    bootstrap(KNOWLEDGE, db)
    svc = SdkChatService.__new__(SdkChatService)
    svc.runner = runner
    svc.run_config_type = lambda **kw: SimpleNamespace(**kw)
    svc.orchestrator = SimpleNamespace(name='Orquestrador')
    svc.database = db
    svc.knowledge_dir = KNOWLEDGE
    svc.sessions = SessionMemory(max_exchanges=30)
    return svc


def test_30_exchanges_preserved_and_31st_discards_first():
    memory = SessionMemory()
    assert memory.max_exchanges == 30
    s = memory.get('one-tab')
    for i in range(31):
        s.record(f'question {i}', f'answer {i}', needs_clarification=False,
                 reset_pending=True, max_exchanges=memory.max_exchanges)
    assert len(s.history) == 60
    assert s.history[0]['content'] == 'question 1'
    assert s.history[-1]['content'] == 'answer 30'
    assert len(s.input_for('next')) == 61
    assert memory.get('other-tab').history == []


def test_ouvidoria_followup_with_validated_protocol_and_no_tool_call(tmp_path):
    class Runner:
        calls = 0

        @staticmethod
        async def run(_, messages, *, context, **kwargs):
            Runner.calls += 1
            if Runner.calls == 1:
                result = buscar_protocolo(context, 'OUV-0013')
                assert 'Respondido' in result
                return response('Ouvidoria', 'O protocolo OUV-0013 está Respondido.',
                                handoff='ouvidoria', tool='buscar_protocolo')
            # O mesmo desvio real: a LLM responde sem executar nenhuma ferramenta.
            assert isinstance(messages, list)
            assert 'OUV-0013' in str(messages)
            return response('Ouvidoria', 'Sim, foi reembolsado!', handoff='ouvidoria')

    svc = make_service(tmp_path, Runner)

    async def scenario():
        first = await svc.chat('Qual o status do protocolo OUV-0013?', session_id='aba1')
        assert first.domain == 'ouvidoria'
        assert first.sources[0].detail == 'OUV-0013'
        assert svc.sessions.get('aba1').last_verified_protocol == 'OUV-0013'
        second = await svc.chat('mas já foi reembolsado?', session_id='aba1')
        assert second.domain == 'ouvidoria'
        assert second.generation_method == 'sdk_consulta_local_controle'
        assert 'OUV-0013' in second.answer
        assert 'Respondido' in second.answer
        assert 'não comprova' in second.answer
        assert 'foi reembolsado!' not in second.answer
        assert second.tools_used == ['buscar_protocolo']
        assert second.sources[0].source == 'manifestacoes.csv'
        assert second.handoffs == ['transfer_to_ouvidoria']
        assert second.trace_id.startswith('trace_')
    asyncio.run(scenario())


def test_without_verified_protocol_does_not_trust_llm(tmp_path):
    class Runner:
        @staticmethod
        async def run(*_, **__):
            return response('Ouvidoria', 'O reembolso foi pago', handoff='ouvidoria')
    svc = make_service(tmp_path, Runner)
    result = asyncio.run(svc.chat('mas já foi reembolsado?', session_id='new'))
    assert result.generation_method == 'sdk_sem_evidencia'
    assert not result.sources
    assert 'foi pago' not in result.answer


def test_no_protocol_crossover_after_other_specialist(tmp_path):
    class Runner:
        calls = 0
        @staticmethod
        async def run(_, messages, *, context, **kwargs):
            Runner.calls += 1
            if Runner.calls == 1:
                buscar_protocolo(context, 'OUV-0013')
                return response('Ouvidoria', 'Respondido', handoff='ouvidoria', tool='buscar_protocolo')
            if Runner.calls == 2:
                return response('Financeiro', 'Sem fonte', handoff='financeiro')
            return response('Ouvidoria', 'Foi pago!', handoff='ouvidoria')
    svc = make_service(tmp_path, Runner)
    async def scenario():
        await svc.chat('Qual é o status de OUV-0013?', session_id='tab')
        assert svc.sessions.get('tab').last_verified_protocol == 'OUV-0013'
        await svc.chat('Agora queria olhar despesas', session_id='tab')
        assert svc.sessions.get('tab').last_verified_protocol is None
        res = await svc.chat('mas já foi reembolsado?', session_id='tab')
        assert res.generation_method == 'sdk_sem_evidencia'
        assert not res.sources
    asyncio.run(scenario())


def test_lookup_fallback_rejects_other_protocol(tmp_path):
    db=tmp_path/'kb.sqlite';bootstrap(KNOWLEDGE,db)
    ctx=ExecutionContext(db,KNOWLEDGE,question='OUV-0014 foi pago?')
    assert confirmar_limite_reembolso_ouvidoria(ctx,'OUV-0014 foi pago?','OUV-0013') is None
    assert not ctx.tools_used
    assert confirmar_limite_reembolso_ouvidoria(ctx,'Qual o gerente da área?','OUV-0013') is None
    assert not ctx.tools_used


def test_frontend_strings():
    html=(ROOT/'frontend/index.html').read_text(encoding='utf-8')
    js=(ROOT/'frontend/app.js').read_text(encoding='utf-8')
    assert 'Olá, prezado(a). Como posso te ajudar hoje?' in html
    assert "renderMessage('...','bot')" in js
    assert 'Consultando base de conhecimento' not in js
