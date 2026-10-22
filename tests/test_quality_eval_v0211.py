"""Testes OFFLINE das regras do avaliador; não invocam LLM nem geram custos."""
from __future__ import annotations
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'evaluate_quality_sdk_http.py'
spec = importlib.util.spec_from_file_location('quality_eval_0211', SCRIPT)
from sys import modules
quality = importlib.util.module_from_spec(spec)
modules[spec.name] = quality
spec.loader.exec_module(quality)


def reply(**kwargs):
    base = {'engine':'sdk', 'domain':'informacoes_internas',
            'handoffs':['transfer_to_informacoes_internas'], 'tools_used':['buscar_documentos'],
            'sources':[{'source':'01_politica_ferias.md'}],
            'trace_id':'trace_abcd1234', 'answer':'Solicite pelo portal com 30 dias de antecedência.'}
    base.update(kwargs)
    return base


def test_all_official_cases_loaded():
    assert len(quality.OFFICIAL) == 12
    assert {c.id for c in quality.OFFICIAL} == {f'T{i:03d}' for i in range(1, 13)}
    assert len(quality.collect_cases('smoke')) == 6
    assert len(quality.collect_cases('full')) == 17


def test_valid_grounded_answer_passes():
    case = quality.OFFICIAL[0]
    assert quality.assess(case, reply())['status'] == 'PASS'


def test_wrong_route_or_missing_source_fails():
    case = quality.OFFICIAL[0]
    result = quality.assess(case, reply(domain='financeiro', sources=[]))
    assert result['status'] == 'FAIL'
    assert any('domínio' in error for error in result['errors'])
    assert any('fonte' in error for error in result['errors'])


def test_security_cannot_handoff():
    case = next(c for c in quality.OFFICIAL if c.id == 'T010')
    assert quality.assess(case, reply(domain='seguranca'))['status'] == 'FAIL'
    safe = reply(domain='seguranca', handoffs=[], tools_used=[], answer='Não posso informar a senha.')
    assert quality.assess(case, safe)['status'] == 'REVIEW'


def test_human_review_not_misreported_as_pass():
    case = next(c for c in quality.EXTRA if c.id == 'E001')
    good = reply(sources=[{'source':'06_politica_home_office.md'}], answer='Política define regime no contrato e requer acordo.')
    assert quality.assess(case, good)['status'] == 'REVIEW'


def test_unicode_and_numeric_content():
    case = quality.OFFICIAL[5]  # T006
    good = reply(domain='financeiro', handoffs=['transfer_to_financeiro'],
                 tools_used=['consultar_financeiro'], sources=[{'source':'lancamentos_financeiros.csv'}],
                 answer='O total foi R$ 305.937,01.')
    assert quality.assess(case, good)['status'] == 'PASS'
    assert quality.assess(case, dict(good, answer='R$ 305.937,00'))['status'] == 'FAIL'
