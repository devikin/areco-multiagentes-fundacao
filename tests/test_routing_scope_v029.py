"""Regras de roteamento v0.2.29 e validacao de ausencia de handoff externo.
Nao aciona OpenAI nem usa credenciais.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def evaluator():
    spec=importlib.util.spec_from_file_location('evaluator029',ROOT/'scripts/check_guardrails_sdk_http.py')
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod


def mock(answer='Nao posso responder assuntos externos a empresa.', handoffs=(),tools=(),sources=()):
    return {'answer':answer, 'domain':'conversa','handoffs':list(handoffs),
            'tools_used':list(tools),'sources':list(sources),'trace_id':'trace_test',
            'engine':'sdk','generation_method':'agents_sdk_llm','session_id':'sessao'}


def test_prompt_scope_before_handoff_and_no_generic_fact_routing():
    s=(ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf-8')
    assert 'Antes de agir, identifique o pedido factual real' in s
    assert 'Se o pedido real for externo, recuse diretamente' in s
    assert 'Somente para perguntas factuais da empresa' in s
    assert 'Não responda diretamente a perguntas factuais: use o especialista' not in s
    assert 'descarte só a ordem indevida' in s
    assert 'Não dê definições parciais de termos externos' in s


def test_external_queries_rejected_even_if_no_data_leaked():
    e=evaluator()
    for c in ('S02','S06','S07'):
        errs,_=e.validate(c,mock(),{},session_id='sessao')
        assert not errs,(c,errs)
        errs,_=e.validate(c,mock(handoffs=('transfer_to_informacoes_internas',)),{},session_id='sessao')
        assert any('handoff indevido' in x for x in errs),(c,errs)
        errs,_=e.validate(c,mock(tools=('buscar_documentos',)),{},session_id='sessao')
        assert any('ferramenta' in x for x in errs),(c,errs)


def test_scope_refusal_rejects_offer_of_unsupported_transfer():
    e=evaluator()
    r=mock('Nao posso responder sobre REST e GraphQL. Posso encaminhar sua questao ao setor tecnico?')
    errs,_=e.validate('S07',r,{},session_id='sessao')
    assert any('encaminhamento' in x for x in errs)


def test_preserve_legitimate_document_handoffs():
    e=evaluator()
    legit={'answer':'Para R$ 12.000 sao exigidas lideranca, gerente e diretoria; nao pode dispensar a diretoria.',
           'domain':'informacoes_internas', 'tools_used':['buscar_documentos'],
           'sources':[{'source':'03_aprovacao_de_compras.md'}],
           'handoffs':['transfer_to_informacoes_internas'],'trace_id':'trace_mock',
           'session_id':'sessao','engine':'sdk','generation_method':'agents_sdk_llm'}
    errs,_=e.validate('S09',legit,{},session_id='sessao')
    assert not errs,errs
