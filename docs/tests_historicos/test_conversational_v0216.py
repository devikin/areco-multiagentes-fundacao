"""Ajustes conversacionais sem SDK real: proteção de escopo, BM25 e handoffs."""
from __future__ import annotations

import ast
import asyncio
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
import sqlite3

import pytest

from app.knowledge.retrieval import retrieve, tokens
from app.sdk_integration.service import (
    SdkChatService, OUT_OF_SCOPE_ANSWER, SECURITY_ANSWER, SOCIAL_ANSWERS,
    _orchestrator_response,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('question', [
    'gostaria de saber sobre as férias',
    'Pode me explicar como funcionam as férias?',
    'Me conte sobre a política de férias',
    'Oi, queria entender as férias',
])
def test_busca_internas_com_linguagem_natural(prepared, question):
    _, _, database = prepared
    with closing(sqlite3.connect(database)) as conn:
        conn.row_factory = sqlite3.Row
        hits = retrieve(conn, question)
    assert hits, (question, tokens(question))
    assert hits[0]['source'] == '01_politica_ferias.md', hits
    assert '30 dias corridos' in hits[0]['content']


@pytest.mark.parametrize('question', [
    'Quantos dias de licença maternidade?', 'Qual o nome do CEO?',
    'Gostaria de saber sobre a Copa do Mundo de 2018',
])
def test_ignora_introducoes_sem_fabricar_fontes(prepared, question):
    _, _, database = prepared
    with closing(sqlite3.connect(database)) as conn:
        conn.row_factory = sqlite3.Row
        assert retrieve(conn, question) == []


@pytest.mark.parametrize('marker,expected', list(SOCIAL_ANSWERS.items()))
def test_respostas_sociais_sao_controladas(marker, expected):
    domain, text = _orchestrator_response(marker + ' TEXTO FALSO NÃO AUTORIZADO')
    assert domain == 'conversa'
    assert text == expected
    assert 'TEXTO FALSO' not in text


def test_escopo_e_senha_preservados():
    assert _orchestrator_response('FORA_DE_ESCOPO: França 2018') == ('fora_de_escopo', OUT_OF_SCOPE_ANSWER)
    assert _orchestrator_response('SEGURANCA: senha=abc') == ('seguranca', SECURITY_ANSWER)
    assert _orchestrator_response('AMBIGUO: Qual prazo?') == ('ambiguo', 'Qual prazo?')


def test_instrucoes_diferenciam_social_de_handoff():
    tree = ast.parse((ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf-8'))
    builder = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'construir_orquestrador')
    return_call = next(x.value for x in builder.body if isinstance(x, ast.Return))
    instructions = next(ast.literal_eval(x.value) for x in return_call.keywords if x.arg == 'instructions')
    for text in ('SAUDACAO:', 'AGRADECIMENTO:', 'DESPEDIDA:', 'handoff nativo',
                 'Olá, gostaria de saber sobre férias', 'FORA_DE_ESCOPO:', 'SEGURANCA:'):
        assert text in instructions


def test_sdk_response_social_sem_handoff_ou_fonte(tmp_path):
    class FakeRunner:
        @staticmethod
        async def run(*_, **__):
            return SimpleNamespace(
                last_agent=SimpleNamespace(name='Orquestrador'),
                final_output='SAUDACAO: mensagem inventada qualquer',
                new_items=[],
                context_wrapper=SimpleNamespace(usage=SimpleNamespace(
                    requests=1,input_tokens=22,output_tokens=12,total_tokens=34)),
            )
    service = SdkChatService.__new__(SdkChatService)
    service.runner = FakeRunner
    service.run_config_type = lambda **kwargs: SimpleNamespace(**kwargs)
    service.orchestrator = SimpleNamespace(name='Orquestrador')
    service.database = tmp_path/'fake.sqlite'
    service.knowledge_dir = tmp_path
    response = asyncio.run(service.chat('Olá!'))
    assert response.domain == 'conversa'
    assert response.answer == SOCIAL_ANSWERS['SAUDACAO:']
    assert response.agent is None
    assert response.sources == response.handoffs == response.tools_used == []
    assert response.generation_method == 'sdk_resposta_controle'
    assert response.engine == 'sdk'
