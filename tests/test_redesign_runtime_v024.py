"""Teste offline v0.2.24: respostas da LLM chegam intactas ao frontend."""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from app.sdk_integration.service import SdkChatService
from app.sdk_integration.session_memory import SessionMemory
import app.sdk_integration.service as service_module


class FakeSession:
    def __init__(self, session_id):
        self.session_id = session_id


class FakeContext:
    def __init__(self, **kwargs):
        self.question = kwargs['question']
        self.sources=[]
        self.tools_used=[]


class FakeRunner:
    calls=[]

    @classmethod
    async def run(cls, agent, text, *, context, session, run_config, max_turns):
        cls.calls.append((text, context.question, session, run_config.session_input_callback))
        assert isinstance(text, str)
        assert text == context.question
        assert max_turns == 10
        return SimpleNamespace(
            final_output='Não tenho certeza do ano. Pode informar os quatro dígitos?',
            last_agent=SimpleNamespace(name='Orquestrador'),
            new_items=[],
            context_wrapper=SimpleNamespace(usage=SimpleNamespace(
                requests=1,input_tokens=27,output_tokens=15,total_tokens=42)),
        )


def test_all_dialogue_turns_reach_llm_and_are_returned_unchanged(monkeypatch, tmp_path):
    monkeypatch.setattr(service_module, 'ExecutionContext', FakeContext)
    FakeRunner.calls=[]
    service=SdkChatService.__new__(SdkChatService)
    service.runner=FakeRunner
    service.orchestrator=SimpleNamespace(name='Orquestrador')
    service.run_config_type=lambda **kwargs: SimpleNamespace(**kwargs)
    service.sdk_session_type=FakeSession
    service.sessions=SessionMemory(max_exchanges=30)
    service.database=tmp_path/'knowledge.sqlite'
    service.knowledge_dir=tmp_path

    async def run():
        for text in ('oi td berm', '205', 'quero falar com alguém', 'quem ganhou a Copa?'):
            result=await service.chat(text,'sessao-A')
            assert result.answer == 'Não tenho certeza do ano. Pode informar os quatro dígitos?'
            assert result.generation_method == 'agents_sdk_llm'
            assert result.trace_id and result.token_usage['requests']==1
        await service.chat('Olá', 'sessao-B')
    asyncio.run(run())
    assert len(FakeRunner.calls)==5
    assert [r[0] for r in FakeRunner.calls]==[
        'oi td berm','205','quero falar com alguém','quem ganhou a Copa?','Olá'
    ]
    assert FakeRunner.calls[0][2] is FakeRunner.calls[1][2]
    assert FakeRunner.calls[0][2] is not FakeRunner.calls[4][2]
    assert callable(FakeRunner.calls[0][3])
