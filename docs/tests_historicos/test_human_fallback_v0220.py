"""Apenas textos de controle, sem prometer handoff humano inexistente."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.knowledge.ingest import bootstrap
from app.sdk_integration.response_messages import INSUFFICIENT_EVIDENCE_ANSWER
from app.sdk_integration.service import SdkChatService
from app.sdk_integration.tools import ExecutionContext, buscar_documentos
from app.sdk_integration.session_memory import SessionMemory

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / 'data' / 'knowledge'


def service_with_runner(tmp_path, runner):
    db = tmp_path / 'kb.sqlite'
    bootstrap(KNOWLEDGE, db)
    svc = SdkChatService.__new__(SdkChatService)
    svc.runner = runner
    svc.run_config_type = lambda **kw: SimpleNamespace(**kw)
    svc.orchestrator = SimpleNamespace(name='Orquestrador')
    svc.database = db
    svc.knowledge_dir = KNOWLEDGE
    svc.sessions = SessionMemory(max_exchanges=30)
    return svc


def reply(agent, text, *, handoff=True):
    events = ([SimpleNamespace(type='handoff_call_item', raw_item=SimpleNamespace(name='transfer_to_financeiro'))]
              if handoff else [])
    return SimpleNamespace(last_agent=SimpleNamespace(name=agent), final_output=text,
        new_items=events, context_wrapper=SimpleNamespace(usage=SimpleNamespace(
            requests=1, input_tokens=10, output_tokens=10, total_tokens=20)))


def test_fallback_is_cordial_and_does_not_promise_unavailable_human_transfer():
    assert INSUFFICIENT_EVIDENCE_ANSWER.startswith('Não consegui confirmar essa informação')
    assert 'responsável da área' in INSUFFICIENT_EVIDENCE_ANSWER
    for unsupported in ('encaminhei', 'transferi', 'vou transferir', 'abrimos um chamado', 'um atendente entrará'):
        assert unsupported not in INSUFFICIENT_EVIDENCE_ANSWER.casefold()
    assert '*' not in INSUFFICIENT_EVIDENCE_ANSWER


def test_specialist_without_tool_returns_human_guidance_not_llm_claim(tmp_path):
    class Runner:
        @staticmethod
        async def run(*args, **kw):
            return reply('Financeiro', 'Foi pago ontem sem dúvida!')
    svc = service_with_runner(tmp_path, Runner)
    result = asyncio.run(svc.chat('Já foi pago?', session_id='teste'))
    assert result.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert result.generation_method == 'sdk_sem_evidencia'
    assert result.domain == 'financeiro'
    assert not result.sources
    assert not result.tools_used


def test_document_without_hits_sets_same_cordial_fallback(tmp_path):
    db = tmp_path/'knowledge.sqlite'; bootstrap(KNOWLEDGE, db)
    ctx=ExecutionContext(db, KNOWLEDGE, question='Qual é a política de viagens a Marte?')
    output = buscar_documentos(ctx, 'Qual é a política de viagens a Marte?')
    assert output.startswith('SEM_EVIDENCIA:')
    assert ctx.control_answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert ctx.tools_used == ['buscar_documentos']
    assert not ctx.sources
