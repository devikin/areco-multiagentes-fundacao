"""Smoke de 3 turnos com GPT-4.1 mini no Docker.

Valida: esclarecimento inicial -> ano digitado errado -> consulta confirmada.
Faz chamadas reais à OpenAI e consome tokens; não simula a LLM.
"""
from __future__ import annotations

import json
import sys
import unicodedata
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8000'


def norm(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold())
                   if not unicodedata.combining(c))


def ask(message: str, session: str) -> dict:
    request = Request(BASE + '/api/v1/chat',
                      data=json.dumps({'message': message, 'session_id': session}, ensure_ascii=False).encode(),
                      headers={'Content-Type': 'application/json'}, method='POST')
    with urlopen(request, timeout=120) as response:
        answer = json.load(response)
    print(f'Pergunta: {message}\nDomínio: {answer["domain"]}\nResposta: {answer["answer"]}\n'
          f'Fontes: {answer["sources"]} | ferramentas: {answer["tools_used"]} | '
          f'trace: {answer["trace_id"]}\n', flush=True)
    assert answer['generation_method'] == 'agents_sdk_llm', 'Backend substituiu resposta da LLM'
    assert answer['session_id'] == session
    assert answer['trace_id'], 'Chamada à OpenAI sem trace'
    return answer


def main() -> None:
    with urlopen(BASE + '/openapi.json', timeout=10) as response:
        version = json.load(response)['info']['version']
    assert version == '0.2.27', f'Docker desatualizado: API {version}; esperado 0.2.27'
    session = str(uuid4())

    opening = ask('Quero consultar minhas despesas por departamento', session)
    assert opening['domain'] == 'financeiro'
    assert not opening['sources'], 'Não pode executar consulta antes de obter o ano'
    assert any(x in norm(opening['answer']) for x in ('ano', 'periodo')), 'Agente não pediu o período'
    print('PASS 1/3 | Solicitou o ano', flush=True)

    invalid = ask('205', session)
    assert invalid['domain'] == 'financeiro', 'Perdeu a continuidade do Financeiro'
    assert not invalid['sources'], 'Falha crítica: consultou dados após ano incompleto'
    assert '?' in invalid['answer'] and any(x in norm(invalid['answer']) for x in ('ano', 'digito')), \
        'Agente deveria perguntar naturalmente o ano completo'
    print('PASS 2/3 | 205 não gerou consulta nem citação', flush=True)

    correct = ask('2025', session)
    assert correct['domain'] == 'financeiro'
    assert 'consultar_financeiro' in correct['tools_used']
    assert 'lancamentos_financeiros.csv' in {item['source'] for item in correct['sources']}
    assert '2025' in correct['answer'] and 'departamento' in norm(correct['answer'])
    assert 'R$' in correct['answer']
    print('PASS 3/3 | 2025 confirmado, ferramenta executada, resposta fundamentada', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'FAIL: {type(exc).__name__}: {exc}', flush=True)
        sys.exit(1)
