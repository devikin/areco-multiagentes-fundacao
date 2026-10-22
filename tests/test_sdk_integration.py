"""Contratos e ferramentas offline da Fase 2; não usa chave nem rede.

O Runner é SIMULADO nos testes HTTP. O handoff real foi validado pelo
usuário na PoC e precisa ser repetido nesta nova versão após instalar patch.
"""
from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
import sys

from app.sdk_integration.finance_queries import FinancePlan
from app.sdk_integration.ouvidoria_queries import OuvidoriaPlan
from app.knowledge.ingest import bootstrap
from app.sdk_integration.tools import (
    ExecutionContext, buscar_documentos, buscar_protocolo, consultar_financeiro,
    listar_status_ouvidoria, consultar_manifestacoes,
)

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'data' / 'knowledge'


@pytest.fixture
def context(tmp_path):
    db = tmp_path / 'sdk.sqlite'
    bootstrap(KB, db)
    return ExecutionContext(db, KB, 'Quanto foi gasto em despesas pagas de janeiro a março de 2025?')


def test_sql_finance_preserves_exact_decimal_and_source(context):
    plan = FinancePlan(dataset='lancamentos', operation='soma', year=2025,
                       start_month=1, end_month=3, transaction_type='Despesa', status='Pago')
    response = consultar_financeiro(context, plan)
    assert '305.937,01' in response
    assert context.sources[0].source == 'lancamentos_financeiros.csv'
    assert context.tools_used == ['consultar_financeiro']


def test_finance_does_not_invent_year(context):
    context.question = 'Quanto foi gasto em despesas pagas?'
    response = consultar_financeiro(context, FinancePlan(
        dataset='lancamentos', operation='soma', transaction_type='Despesa', status='Pago'))
    assert 'Informe o ano' in response
    assert context.control_answer == 'Informe o ano para realizar uma consulta financeira sem presumir o período.'
    assert not context.sources


def test_finance_rejects_extraneous_sql():
    with pytest.raises(ValidationError):
        FinancePlan.model_validate({'dataset':'lancamentos','operation':'soma', 'sql':'DROP TABLE clientes'})


def test_documents_cite_true_chunks(context):
    question = 'Como solicito férias?'
    output = buscar_documentos(context, question)
    assert '30 dias corridos' in output
    assert any('ferias.md' in source.source for source in context.sources)


def test_documents_without_support_do_not_create_sources(context):
    output = buscar_documentos(context, 'zzzzzzzz qwertyuiop')
    assert 'SEM_EVIDENCIA' in output
    assert not context.sources
    assert context.control_answer is not None


def test_ombudsman_protocol_and_missing_record(context):
    output = buscar_protocolo(context, 'ouv-0002')
    assert 'Aguardando área responsável' in output
    assert context.sources[0].source == 'manifestacoes.csv'
    assert context.sources[0].detail == 'OUV-0002'
    output = buscar_protocolo(context, 'OUV-9999')
    assert 'não encontrado' in output


def test_ombudsman_invalid_protocol_never_queries_guess(context):
    output = buscar_protocolo(context, 'ouvidoria do fulano')
    assert 'inválido' in output
    assert not context.sources
    assert context.control_answer is not None


def test_ombudsman_reference_and_total(context):
    assert 'Status permitidos' in listar_status_ouvidoria(context)
    context.question = 'Quantas manifestações existem no total?'
    assert '180' in consultar_manifestacoes(context, OuvidoriaPlan(operacao='contagem'))
    assert {source.source for source in context.sources} == {'referencia_ouvidoria.json', 'manifestacoes.csv'}


def fake_sdk_module(monkeypatch):
    module = ModuleType('agents')

    class FakeAgent:
        def __init__(self, name, model, instructions, tools=None, handoffs=None,
                     handoff_description=None, model_settings=None, reset_tool_choice=True):
            self.name, self.model = name, model
            self.instructions, self.tools = instructions, tools or []
            self.handoffs = handoffs or []
            self.model_settings, self.reset_tool_choice = model_settings, reset_tool_choice
        @classmethod
        def __class_getitem__(cls, _):
            return cls

    class FakeRunContextWrapper:
        @classmethod
        def __class_getitem__(cls, _):
            return cls

    class FakeRunConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeRunner:
        calls = []
        @staticmethod
        async def run(orchestrator, message, *, context, max_turns, run_config, session=None):
            FakeRunner.calls.append((orchestrator, message, max_turns, run_config))
            assert not run_config.trace_include_sensitive_data
            assert run_config.trace_id.startswith('trace_')
            assert len(orchestrator.handoffs) == 3
            if 'férias' in message:
                selected = 'Informacoes_Internas'
                output = buscar_documentos(context, message)
                answer = 'Solicite no portal interno com antecedência de 30 dias. Fonte: 01_politica_ferias.md'
                tool_name = 'buscar_documentos'
            elif 'OUV-' in message:
                selected = 'Ouvidoria'
                output = buscar_protocolo(context, 'OUV-0002')
                answer = 'O protocolo OUV-0002 está Aguardando área responsável. Fonte: manifestacoes.csv'
                tool_name = 'buscar_protocolo'
            elif 'despesas pagas' in message:
                selected = 'Financeiro'
                plan = FinancePlan(dataset='lancamentos', operation='soma', year=2025,
                                   start_month=1, end_month=3, transaction_type='Despesa', status='Pago')
                output = consultar_financeiro(context, plan)
                answer = output
                tool_name = 'consultar_financeiro'
            else:
                selected = 'Orquestrador'
                answer = 'Posso ajudar com perguntas relacionadas à empresa.'
                tool_name = None
            new_items = []
            if tool_name:
                new_items = [SimpleNamespace(type='handoff_call_item', raw_item=SimpleNamespace(name='transfer_to_'+selected.lower())),
                             SimpleNamespace(type='tool_call_item', raw_item=SimpleNamespace(name=tool_name))]
            return SimpleNamespace(
                new_items=new_items, last_agent=SimpleNamespace(name=selected), final_output=answer,
                context_wrapper=SimpleNamespace(usage=SimpleNamespace(requests=3,
                    input_tokens=100,output_tokens=50,total_tokens=150)),
            )

    module.Agent = FakeAgent
    module.ModelSettings = lambda **kwargs: SimpleNamespace(**kwargs)
    module.RunContextWrapper = FakeRunContextWrapper
    module.Runner = FakeRunner
    module.RunConfig = FakeRunConfig
    module.SQLiteSession = lambda session_id: SimpleNamespace(session_id=session_id)
    module.function_tool = lambda function: function
    module.handoff = lambda a: SimpleNamespace(agent_name=a.name, tool_name='transfer_to_'+a.name.lower())
    monkeypatch.setitem(sys.modules, 'agents', module)
    monkeypatch.delitem(sys.modules, 'app.sdk_integration.workflow', raising=False)
    return FakeRunner


def test_four_sdk_agents_and_three_handoffs(monkeypatch):
    fake_sdk_module(monkeypatch)
    from app.sdk_integration.workflow import construir_orquestrador
    root = construir_orquestrador('gpt-4o-mini')
    assert root.name == 'Orquestrador'
    assert {h.agent_name for h in root.handoffs} == {'Financeiro','Informacoes_Internas','Ouvidoria'}
    assert root.tools == []  # Orquestrador não executa ferramentas de domínio.
    assert len(root.handoffs) == 3


def test_http_contract_in_sdk_mode_with_fake_runner(monkeypatch, tmp_path):
    fake_runner = fake_sdk_module(monkeypatch)
    monkeypatch.delenv('AGENT_ENGINE', raising=False)
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key-not-real')
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path / 'knowledge.sqlite'))
    from app.main import app
    with TestClient(app) as client:
        assert client.get('/health').json() == {
            'status': 'ok', 'engine': 'sdk',
            'loaded_agents': ['financeiro', 'informacoes_internas', 'ouvidoria'],
        }
        for question, domain, source in [
            ('Como solicito férias?', 'informacoes_internas', '01_politica_ferias.md'),
            ('Qual o status do protocolo OUV-0002?', 'ouvidoria', 'manifestacoes.csv'),
            ('Quanto foi gasto em despesas pagas de janeiro a março de 2025?', 'financeiro', 'lancamentos_financeiros.csv'),
        ]:
            reply = client.post('/api/v1/chat', json={'message': question})
            assert reply.status_code == 200
            data = reply.json()
            assert data['domain'] == data['agent'] == domain
            assert any(c['source'] == source for c in data['sources'])
            assert data['classification_method'] == 'agents_sdk_handoff'
            assert data['generation_method'] == 'agents_sdk_llm'
            assert data['engine'] == 'sdk'
            assert data['trace_id'].startswith('trace_')
            assert data['token_usage']['total_tokens'] == 150
            assert data['handoffs'] and data['tools_used']
        out_scope = client.post('/api/v1/chat', json={'message':'Quem ganhou a Copa do Mundo de 2014?'}).json()
        assert out_scope['domain'] == 'conversa'
        assert not out_scope['sources']
        assert client.post('/api/v1/chat',json={'message':'a'}).status_code == 422
    assert len(fake_runner.calls) == 4


def test_sdk_mode_requires_key(monkeypatch, tmp_path):
    fake_sdk_module(monkeypatch)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    from app.sdk_integration.service import SdkChatService
    with pytest.raises(RuntimeError, match='OPENAI_API_KEY'):
        SdkChatService(tmp_path/'db.sqlite', KB)


def test_sdk_only_mode_rejects_invalid_engine(monkeypatch, tmp_path):
    monkeypatch.setenv('AGENT_ENGINE', 'accidental')
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path/'db.sqlite'))
    from app.main import app
    with pytest.raises(RuntimeError, match='exclusivamente Agents SDK'):
        with TestClient(app):
            pass


def test_ouvidoria_advanced_tool_is_available_on_sdk_agent(monkeypatch):
    """Verifica registro da ferramenta na árvore de agentes (sem rede)."""
    fake_sdk_module(monkeypatch)
    # Para inspecionar os agentes de destino, o stub de handoff devolve o objeto.
    sys.modules['agents'].handoff = lambda agent: agent
    from app.sdk_integration.workflow import construir_orquestrador
    root = construir_orquestrador('gpt-4o-mini')
    assert len(root.handoffs) == 3
    fin = next(agent for agent in root.handoffs if agent.name == 'Financeiro')
    assert fin.model_settings.tool_choice == 'required'
    assert fin.reset_tool_choice is True
    ouv = next(agent for agent in root.handoffs if agent.name == 'Ouvidoria')
    assert 'consultar_manifestacoes' in {tool.__name__ for tool in ouv.tools}
    assert 'buscar_protocolo' in {tool.__name__ for tool in ouv.tools}
    assert 'contar_manifestacoes' not in {tool.__name__ for tool in ouv.tools}
    assert len(ouv.tools) == 3
