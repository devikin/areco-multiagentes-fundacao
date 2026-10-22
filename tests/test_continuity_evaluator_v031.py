"""Evita falso FAIL para respostas de continuidade respaldadas pelo turno anterior."""
from pathlib import Path
import importlib.util
import sys

ROOT=Path(__file__).resolve().parents[1]


def evaluator():
    spec=importlib.util.spec_from_file_location('areco_continuity_http_v031',
         ROOT/'scripts/check_frontend_continuity_sdk_http.py')
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod


def test_reused_verified_protocol_does_not_require_tool_again():
    mod=evaluator()
    prior={'F06':{'status':'PASS','sources':[{'source':'manifestacoes.csv','detail':'OUV-0016'}]}}
    response={'answer':'O protocolo OUV-0016 está aguardando área responsável.',
              'domain':'conversa','tools_used':[],'sources':[],
              'generation_method':'agents_sdk_llm','trace_id':'trace_test'}
    assert not mod.check('F07',response,prior)
    assert mod.check('F07',response,{})


def test_new_protocol_must_use_exact_ouvidoria_source_and_tool():
    mod=evaluator()
    response={'answer':'O protocolo OUV-0016 está aguardando área responsável.',
              'domain':'informacoes_internas','tools_used':['buscar_documentos'],
              'sources':[{'source':'01_politica_ferias.md','detail':'x'}],
              'generation_method':'agents_sdk_llm','trace_id':'trace_test'}
    assert len(mod.check('F06',response,{})) >= 3
    response.update(domain='ouvidoria',tools_used=['buscar_protocolo'],
                    sources=[{'source':'manifestacoes.csv','detail':'OUV-0016'}])
    assert not mod.check('F06',response,{})


def test_finance_pending_year_is_checked_separately():
    mod=evaluator()
    invalid={'answer':'Qual é o ano?', 'domain':'financeiro',
             'tools_used':[],'sources':[], 'generation_method':'agents_sdk_llm','trace_id':'trace_test'}
    assert not mod.check('Y01',invalid,{})
    invalid['sources']=[{'source':'lancamentos_financeiros.csv','detail':'2050'}]
    assert mod.check('Y01',invalid,{})
