"""Teste real v0.2.22: ano incorreto preserva intenção e consulta posterior.

Executa duas consultas reais ao SDK e uma validação local sem tokens.
O estado de LLM é probabilístico: falhas retornam trace para diagnóstico.
"""
from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8000'


def ask(message: str, session: str) -> dict:
    body = json.dumps({'message': message, 'session_id': session}, ensure_ascii=False).encode('utf-8')
    request = Request(BASE + '/api/v1/chat', data=body, method='POST',
                      headers={'Content-Type': 'application/json; charset=utf-8'})
    with urlopen(request, timeout=120) as response:
        data = json.load(response)
    assert data['session_id'] == session
    print(f'{message!r} | {data["domain"]} | {data["answer"]} | trace={data.get("trace_id")}',
          flush=True)
    return data


def main() -> int:
    print('Teste: 2 chamadas REAIS à OpenAI e 1 validação local sem tokens.', flush=True)
    sid = str(uuid4())
    first = ask('Quero consultar o total de despesas do departamento de Tecnologia', sid)
    if first['domain'] != 'esclarecimento' or 'ano' not in first['answer'].casefold():
        print('FAIL: o primeiro turno deveria solicitar o ano; revise seu trace.', flush=True)
        return 1
    print('PASS | intenção financeira e ano pendente', flush=True)

    invalid = ask('205', sid)
    if (invalid['domain'] != 'esclarecimento'
            or invalid['classification_method'] != 'validacao_entrada_local'
            or invalid['token_usage']['requests'] != 0
            or 'quatro dígitos' not in invalid['answer']):
        print('FAIL: entrada incompleta não foi contida pelo validador local.', flush=True)
        return 1
    print('PASS | ano incompleto rejeitado sem handoff nem consumo de tokens', flush=True)

    final = ask('2025', sid)
    if (final['domain'] != 'financeiro'
            or 'consultar_financeiro' not in final['tools_used']
            or 'lancamentos_financeiros.csv' not in {x['source'] for x in final['sources']}):
        print('FAIL: correção não retomou consulta financeira com fonte; revise trace.', flush=True)
        return 1
    print('PASS | correção do ano e consulta fundamentada em fonte real', flush=True)
    print('3/3 turnos validados (2 SDK + 1 validação local).', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'FAIL | {type(exc).__name__}: {exc}', flush=True)
        raise
