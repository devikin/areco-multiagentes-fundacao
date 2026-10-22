"""v0.2.31: regressões offline da continuidade e handoffs.
Simula respostas do SDK somente para testar a seleção do agente inicial;
NÃO valida o roteamento nem as respostas de um modelo real.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]


def service_module(monkeypatch):
    # Stubs de fronteira: nenhum modelo ou API externa é chamado.
    class Response:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
    @dataclass
    class Context:
        database: Path
        knowledge_dir: Path
        question: str
        sources: list = field(default_factory=list)
        tools_used: list = field(default_factory=list)
    spec = importlib.util.spec_from_file_location('v031_sessions', ROOT/'app/sdk_integration/session_memory.py')
    sessions = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, sessions)
    spec.loader.exec_module(sessions)
    for name, attrs in {
        'app.schemas': {'ChatResponse': Response},
        'app.sdk_integration.tools': {'ExecutionContext': Context},
        'app.sdk_integration.session_memory': {
            'SessionMemory': sessions.SessionMemory, 'SessionState': sessions.SessionState,
            'last_30_exchanges': sessions.last_30_exchanges},
    }.items():
        mod = types.ModuleType(name)
        for k,v in attrs.items(): setattr(mod,k,v)
        monkeypatch.setitem(sys.modules, name, mod)
    sp = importlib.util.spec_from_file_location('v031_service', ROOT/'app/sdk_integration/service.py')
    svc = importlib.util.module_from_spec(sp)
    monkeypatch.setitem(sys.modules, sp.name, svc)
    sp.loader.exec_module(svc)
    return svc, sessions, Context


def test_token_recognized_only_when_formally_valid(monkeypatch):
    svc, _, _ = service_module(monkeypatch)
    agent = types.SimpleNamespace(name='Informacoes_Internas')
    for message in ('OUV-0016','O protocolo ouV-0016?', 'Agora OUV-0002', 'nao localizou OUV-0016?'):
        assert svc.requires_orchestrator_recheck(message,agent)
    for message in ('OUV-016','A-OUV-0016', 'OUV-00163', '205', '2025', 'reembolso'):
        assert not svc.requires_orchestrator_recheck(message,agent)
    assert not svc.requires_orchestrator_recheck('OUV-0016', types.SimpleNamespace(name='Ouvidoria'))
    assert not svc.requires_orchestrator_recheck('OUV-0016',None)


def test_no_source_not_always_a_pending_clarification(monkeypatch):
    svc, _, _ = service_module(monkeypatch)
    assert not svc.keep_specialist_pending('Informacoes_Internas',[])
    assert not svc.keep_specialist_pending('Ouvidoria',[])
    assert svc.keep_specialist_pending('Financeiro',[])
    assert not svc.keep_specialist_pending('Financeiro',[object()])


def test_frontend_replay_and_switch_without_sticky_internas(monkeypatch):
    svc, sessions, Context = service_module(monkeypatch)
    router = types.SimpleNamespace(name='Orquestrador')
    internal = types.SimpleNamespace(name='Informacoes_Internas')
    finance = types.SimpleNamespace(name='Financeiro')
    ouvidoria = types.SimpleNamespace(name='Ouvidoria')
    observed = []
    class FakeRunConfig:
        def __init__(self, **kwargs):pass
    class FakeSdkSession:
        def __init__(self, session_id):self.id=session_id
    class FakeRunner:
        async def run(self, agent, message, *, context, session, **kwargs):
            observed.append((agent.name,message,context.question))
            if message=='reembolso':
                last,answer=internal,'Não encontrei documento para consultar situação de protocolo.'
            elif 'OUV-0016' in message:
                assert agent is router, 'Novo protocolo não foi reavaliado pelo Orquestrador'
                assert 'Complemento' not in context.question, 'Contexto anterior contaminou consulta nova'
                last,answer=ouvidoria,'O status do OUV-0016 é Aguardando área responsável.'
                context.sources.append(types.SimpleNamespace(source='manifestacoes.csv',detail='OUV-0016'))
                context.tools_used.append('buscar_protocolo')
            elif message=='Preciso ver despesas por departamento':
                last,answer=finance,'Para qual ano deseja consultar?'
            elif message=='205':
                assert agent is finance
                last,answer=finance,'Informe ano de quatro dígitos.'
            elif message=='2025':
                assert agent is finance
                assert context.question=='Preciso ver despesas por departamento | Complemento: 2025'
                last,answer=finance,'Em 2025 há despesas por departamento.'
                context.sources.append(types.SimpleNamespace(source='lancamentos_financeiros.csv',detail='2025'))
                context.tools_used.append('consultar_financeiro')
            else:
                raise AssertionError(message)
            usage=types.SimpleNamespace(requests=1,input_tokens=10,output_tokens=10,total_tokens=20)
            return types.SimpleNamespace(last_agent=last,final_output=answer,new_items=[],
                                         context_wrapper=types.SimpleNamespace(usage=usage))

    x=svc.SdkChatService.__new__(svc.SdkChatService)
    x.orchestrator=router
    x.runner=FakeRunner()
    x.run_config_type=FakeRunConfig
    x.sdk_session_type=FakeSdkSession
    x.sessions=sessions.SessionMemory()
    x.database=Path('/tmp/knowledge.sqlite')
    x.knowledge_dir=Path('/tmp/knowledge')

    async def scenario():
        sid='web-session'
        bad = await x.chat('reembolso',sid)
        assert bad.domain=='informacoes_internas'
        assert x.sessions.get(sid).pending_agent is None, 'Sem evidências não é esclarecimento pendente'
        good = await x.chat('OUV-0016',sid)
        assert good.domain=='ouvidoria'
        assert good.tools_used==['buscar_protocolo']
        assert x.sessions.get(sid).pending_agent is None
        sid2='finance-session'
        for msg in ('Preciso ver despesas por departamento','205','2025'):
            await x.chat(msg,sid2)
        assert observed[-1][0]=='Financeiro'
        assert x.sessions.get(sid2).pending_agent is None
        # protocolo inesperado durante uma pendência financeira -> reavaliação.
        sid3='finance-switch'
        await x.chat('Preciso ver despesas por departamento',sid3)
        assert x.sessions.get(sid3).pending_agent is finance
        await x.chat('OUV-0016',sid3)
        assert observed[-1][0]=='Orquestrador'
        assert x.sessions.get(sid3).pending_agent is None
    asyncio.run(scenario())


def test_context_prompt_preserves_intent_and_requires_real_protocol():
    source=(ROOT/'app/sdk_integration/workflow.py').read_text('utf-8')
    assert 'intenção ao longo de toda a conversa' in source
    assert 'NÃO confunda com pedido de política de reembolso' in source
    assert 'não prometa localizar uma manifestação individual' in source
    assert 'encaminhe à Ouvidoria para buscar_protocolo' in source
    assert 'se o usuário fornecer OUV-NNNN' in source or 'se o usuário informar OUV-NNNN' in source
    assert 'OUV-NNNN ou pedir situação individual' in source
