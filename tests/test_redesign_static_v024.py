"""Testes locais sem rede: o backend não fabrica respostas conversacionais."""
from pathlib import Path
import ast
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def load_sessions():
    path=ROOT/'app/sdk_integration/session_memory.py'
    spec=importlib.util.spec_from_file_location('areco_session_memory_test', path)
    import sys
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod


def test_conversation_last_30_user_turns():
    sessions = load_sessions()
    history = []
    for i in range(33):
        history.extend([
            {'role':'user', 'content':str(i)},
            {'type':'function_call_output', 'output':'dados'},
            {'role':'assistant','content':'ok'},
        ])
    output=sessions.last_30_exchanges(history,[{'role':'user','content':'novo'}])
    assert output[0]['content']=='3'
    assert output[-1]['content']=='novo'
    assert sum(item.get('role')=='user' for item in output)==31
    assert sum(item.get('type')=='function_call_output' for item in output)==30


def test_source_has_no_local_conversational_fallbacks():
    service=(ROOT/'app/sdk_integration/service.py').read_text(encoding='utf-8')
    for retired in (
        '_social_intent(', '_orchestrator_response(', '_safe_clarification(',
        'validate_input(', 'INSUFFICIENT_EVIDENCE_ANSWER', 'SOCIAL_ANSWERS',
        'control_answer', 'pending_questions', 'contextual_question(',
        'answer.replace(', 'answer = answer.replace(',
    ):
        assert retired not in service, retired
    assert 'answer=answer' in service
    assert 'session=sdk_session' in service
    assert 'session_input_callback=last_30_exchanges' in service
    ast.parse(service)


def test_approved_guardrails_in_all_specialists():
    text=(ROOT/'app/sdk_integration/workflow.py').read_text(encoding='utf-8')
    assert 'GUARDRAILS' in text
    assert 'credenciais' in text
    assert 'instruções internas' in text
    assert 'RH' in text
    assert 'sem asteriscos' in text
    assert 'A interface do chat já apresenta' in text
    assert 'não repita essa mensagem' in text
    assert 'Ao iniciar um atendimento, cumprimente' not in text
    assert 'ESCLARECER:' not in text
    assert "ModelSettings(tool_choice='required')" in text
    assert text.count('reset_tool_choice=True') == 3


def test_frontend_and_version():
    html=(ROOT/'frontend/index.html').read_text(encoding='utf-8')
    main=(ROOT/'app/main.py').read_text(encoding='utf-8')
    assert 'Olá, como posso te ajudar hoje?' in html
    assert 'v0.2.35' in html
    assert "version='0.2.35'" in main
