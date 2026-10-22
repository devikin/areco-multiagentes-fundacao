"""Regressões motivadas pela bateria oficial REAL: 5 FAIL, 2 REVIEW."""
from __future__ import annotations
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import pytest

from app.sdk_integration.tools import ExecutionContext, buscar_protocolo
from app.knowledge.ingest import bootstrap
from app.sdk_integration.service import SdkChatService

ROOT = Path(__file__).resolve().parents[1]


def _instructions():
    tree = ast.parse((ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf8'))
    builder = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'construir_orquestrador')
    agents = {}
    for statement in builder.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    agents[target.id] = next(ast.literal_eval(kw.value) for kw in statement.value.keywords if kw.arg == 'instructions')
        if isinstance(statement, ast.Return):
            agents['orquestrador'] = next(ast.literal_eval(kw.value) for kw in statement.value.keywords if kw.arg == 'instructions')
    return agents


def test_routing_policy_distinguishes_approval_vs_financial_analysis():
    agents = _instructions()
    router = agents['orquestrador']
    assert 'R$ 12.000' in router
    assert 'aprovação de compras' in router
    assert 'NÃO significa' in router


def test_routing_policy_protects_legitimate_phishing_incident_questions():
    router = _instructions()['orquestrador']
    for phrase in ('Como reporto um e-mail de phishing?', 'O que fazer se houver incidente de segurança?', 'NÃO fora de escopo', 'SEGURANCA:'):
        assert phrase in router


def test_internal_agent_mentions_proof_and_deadline_requirements():
    instructions = _instructions()['internas']
    assert 'comprovantes' in instructions
    assert 'reembolso' in instructions
    assert 'buscar_documentos' in instructions


def test_missing_protocol_sets_canonical_control_answer(tmp_path):
    path = tmp_path/'kb.sqlite'
    bootstrap(ROOT/'data'/'knowledge', path)
    ctx = ExecutionContext(path, ROOT/'data'/'knowledge', 'Existe o protocolo OUV-9999?')
    value = buscar_protocolo(ctx, 'OUV-9999')
    assert ctx.control_answer == 'Protocolo OUV-9999 não encontrado na base de Ouvidoria.'
    assert ctx.control_answer in value
    assert ctx.sources[0].source == 'manifestacoes.csv'


def test_answer_of_missing_protocol_not_rephrased_by_llm(tmp_path):
    # Simula Runner que inventa resposta diferente após receber resultado real da ferramenta.
    database = tmp_path/'kb.sqlite'
    bootstrap(ROOT/'data'/'knowledge', database)

    class Runner:
        @staticmethod
        async def run(*_, **kwargs):
            ctx = kwargs['context']
            buscar_protocolo(ctx, 'OUV-9999')
            return SimpleNamespace(
                last_agent=SimpleNamespace(name='Ouvidoria'),
                final_output='Não há dados para apresentar.',
                new_items=[SimpleNamespace(type='handoff_call_item', raw_item=SimpleNamespace(name='transfer_to_ouvidoria')),
                           SimpleNamespace(type='tool_call_item', raw_item=SimpleNamespace(name='buscar_protocolo'))],
                context_wrapper=SimpleNamespace(usage=SimpleNamespace(requests=3,input_tokens=20,output_tokens=5,total_tokens=25)),
            )

    service = SdkChatService.__new__(SdkChatService)
    service.runner=Runner
    service.run_config_type=lambda **kwargs: SimpleNamespace(**kwargs)
    service.orchestrator=SimpleNamespace(name='Orquestrador')
    service.database=database
    service.knowledge_dir=ROOT/'data'/'knowledge'
    result = asyncio.run(service.chat('Existe o protocolo OUV-9999?'))
    assert result.domain == 'ouvidoria'
    assert result.answer == 'Protocolo OUV-9999 não encontrado na base de Ouvidoria.'
    assert result.generation_method == 'sdk_resposta_controle'
    assert result.sources[0].source == 'manifestacoes.csv'


def test_retest_tool_supports_selection_of_official_failures():
    import importlib.util, sys
    module_name='quality_evaluator_official_v0213'
    spec=importlib.util.spec_from_file_location(module_name, ROOT/'scripts/evaluate_quality_sdk_http.py')
    module=importlib.util.module_from_spec(spec)
    sys.modules[module_name]=module
    spec.loader.exec_module(module)
    assert len(module.collect_cases('official')) == 12
    assert {x.id for x in module.collect_cases('official')} >= {'T002','T003','T004','T008','T012'}


def test_evaluator_retests_only_requested_ids(monkeypatch, tmp_path):
    import importlib.util, json, sys
    module_name='quality_evaluator_select_0213'
    spec=importlib.util.spec_from_file_location(module_name, ROOT/'scripts/evaluate_quality_sdk_http.py')
    module=importlib.util.module_from_spec(spec)
    sys.modules[module_name]=module
    spec.loader.exec_module(module)
    seen=[]
    def fake_call_api(_, question, __):
        seen.append(question)
        return {'engine':'sdk','domain':'ambiguo','answer':'Pode esclarecer?', 'trace_id':'trace_mock',
                'handoffs':[], 'tools_used':[], 'sources':[], 'token_usage':{}}
    monkeypatch.setattr(module,'call_api',fake_call_api)
    output=tmp_path/'partial.json'
    exit_code=module.main(['--suite','official','--ids','T002,T003,T004,T008,T012','--output',str(output)])
    report=json.loads(output.read_text(encoding='utf8'))
    assert exit_code == 1  # mock propositalmente não satisfaz critérios, não é PASS falso
    assert len(seen) == 5
    assert [x['id'] for x in report['results']] == ['T002','T003','T004','T008','T012']
