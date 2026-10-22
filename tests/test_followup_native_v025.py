"""Testa a continuidade nativa entre mensagens, sem responder no backend.

Fake Runner simula a superficie do SDK; NUNCA equivale a teste OpenAI real.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.sdk_integration.service import SdkChatService
from app.sdk_integration.session_memory import SessionMemory
from app.schemas import Citation
import app.sdk_integration.service as service_module


def make_service(tmp_path, fake_runner):
    service = SdkChatService.__new__(SdkChatService)
    service.runner = fake_runner
    service.run_config_type = lambda **k: SimpleNamespace(**k)
    service.sdk_session_type = lambda x: SimpleNamespace(session_id=x)
    service.orchestrator = SimpleNamespace(name='Orquestrador')
    service.sessions = SessionMemory(max_exchanges=30)
    service.database = tmp_path / 'kb.sqlite'
    service.knowledge_dir = tmp_path
    return service


class FakeContext:
    def __init__(self, **kwargs):
        self.question = kwargs['question']
        self.sources = []
        self.tools_used = []


def reply(name, answer, *, handoffs=()):
    return SimpleNamespace(
        last_agent=SimpleNamespace(name=name), final_output=answer,
        new_items=[SimpleNamespace(type='handoff_call_item',raw_item=SimpleNamespace(name=x))
                   for x in handoffs],
        context_wrapper=SimpleNamespace(usage=SimpleNamespace(
            requests=2,input_tokens=500,output_tokens=80,total_tokens=580)),
    )


def test_correction_stays_with_financial_specialist(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module,'ExecutionContext',FakeContext)
    class FakeRunner:
        step=0
        incoming=[]

        @classmethod
        async def run(cls, agent, text, *, context, session, max_turns, run_config):
            cls.step += 1
            cls.incoming.append((agent.name, text, context.question, session))
            assert text == ('quero consultar despesas por departamento' if cls.step==1 else
                            '205' if cls.step==2 else '2025' if cls.step==3 else
                            'Como solicito férias?')
            if cls.step==1:
                assert agent.name=='Orquestrador'
                context.tools_used.append('consultar_financeiro')
                return reply('Financeiro','De qual período você quer consultar as despesas?',
                             handoffs=('transfer_to_financeiro',))
            if cls.step==2:
                assert agent.name=='Financeiro'
                assert context.question.startswith('quero consultar despesas por departamento')
                return reply('Financeiro','O ano parece incompleto. Pode informar quatro dígitos?')
            if cls.step==3:
                assert agent.name=='Financeiro'
                assert 'despesas por departamento' in context.question
                assert context.question.endswith('Complemento: 2025')
                context.tools_used.append('consultar_financeiro')
                context.sources.append(Citation(source='lancamentos_financeiros.csv',detail='2025'))
                return reply('Financeiro','Em 2025, os departamentos foram: Tecnologia: R$ 100,00; Comercial: R$ 80,00.')
            assert agent.name=='Orquestrador'
            context.tools_used.append('buscar_documentos')
            context.sources.append(Citation(source='01_politica_ferias.md', detail='v1.2'))
            return reply('Informacoes_Internas','Para solicitar férias, utilize o portal interno.',
                         handoffs=('transfer_to_informacoes_internas',))

    svc=make_service(tmp_path,FakeRunner)
    async def scenario():
        sid='abc'
        a=await svc.chat('quero consultar despesas por departamento',sid)
        assert a.domain=='financeiro' and not a.sources
        assert svc.sessions.get(sid).pending_agent.name == 'Financeiro'
        b=await svc.chat('205',sid)
        assert b.domain=='financeiro' and 'quatro dígitos' in b.answer
        assert b.generation_method=='agents_sdk_llm' and b.trace_id
        assert b.classification_method=='agents_sdk_especialista_em_continuidade'
        assert svc.sessions.get(sid).pending_agent.name=='Financeiro'
        c=await svc.chat('2025',sid)
        assert c.domain=='financeiro' and c.sources[0].source=='lancamentos_financeiros.csv'
        assert c.answer.startswith('Em 2025')
        assert svc.sessions.get(sid).pending_agent is None
        d=await svc.chat('Como solicito férias?',sid)
        assert d.domain=='informacoes_internas' and d.sources
    asyncio.run(scenario())
    assert FakeRunner.step==4
    assert FakeRunner.incoming[0][3] is FakeRunner.incoming[2][3]


def test_change_topic_during_pending_starts_specialist_and_reroutes(monkeypatch,tmp_path):
    monkeypatch.setattr(service_module,'ExecutionContext',FakeContext)
    class Runner:
        step=0
        @classmethod
        async def run(cls, agent, text, *, context, session, max_turns, run_config):
            cls.step+=1
            if cls.step==1:
                assert agent.name=='Orquestrador'
                return reply('Financeiro','De qual ano?',handoffs=('transfer_to_financeiro',))
            assert agent.name=='Financeiro'  # SDK pode fazer handoff ao Orquestrador
            assert text=='Como solicito férias?'
            context.sources.append(Citation(source='01_politica_ferias.md',detail='v1.2'))
            context.tools_used.append('buscar_documentos')
            return reply('Informacoes_Internas','Você solicita pelo portal.',
                         handoffs=('transfer_to_orquestrador','transfer_to_informacoes_internas'))

    svc=make_service(tmp_path,Runner)
    async def run():
        await svc.chat('Quero analisar despesas', 'B')
        assert svc.sessions.get('B').pending_agent.name=='Financeiro'
        x=await svc.chat('Como solicito férias?', 'B')
        assert x.domain=='informacoes_internas'
        assert x.handoffs == ['transfer_to_orquestrador','transfer_to_informacoes_internas']
        assert svc.sessions.get('B').pending_agent is None
    asyncio.run(run())


def test_memory_callback_keeps_recent_turns_without_response_rewrites():
    from app.sdk_integration.session_memory import last_30_exchanges
    history = []
    for i in range(38):
        history += [{'role':'user','content':str(i)},
                    {'type':'function_call_output','output':'retorno'},
                    {'role':'assistant','content':'ok'}]
    retained = last_30_exchanges(history,[{'role':'user','content':'correção'}])
    assert retained[0]['content']=='8'
    assert retained[-1]['content']=='correção'
