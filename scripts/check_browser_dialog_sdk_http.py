"""Smoke real da conversa reportada no navegador. 7 chamadas OpenAI, com custos.

Execução: python scripts/check_browser_dialog_sdk_http.py
Não valida a correção por mocks: usa o container vivo e a mesma session_id.
"""
from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8000'


def ask(message: str, sid: str) -> dict:
    body = json.dumps({'message': message, 'session_id': sid}, ensure_ascii=False).encode('utf-8')
    req = Request(BASE+'/api/v1/chat', data=body, method='POST',
                  headers={'Content-Type':'application/json; charset=utf-8'})
    with urlopen(req, timeout=120) as response:
        data = json.load(response)
    assert data['session_id'] == sid, data
    assert data['trace_id'].startswith('trace_'), data
    assert data['engine'] == 'sdk', data
    assert '*' not in data['answer'], data
    print(f"{message!r} => {data['domain']} | {data['answer']} | trace={data['trace_id']}", flush=True)
    return data


def main():
    print('7 chamadas REAIS ao Agents SDK/OpenAI, com consumo de tokens.',flush=True)
    sid = str(uuid4())
    cases = (
        ('ola', 'conversa'),
        ('queria tirar uma duvida', 'esclarecimento'),
        ('sobre as ferias', 'informacoes_internas'),
        ('certo..tenho outra duvida', 'esclarecimento'),
        ('sobre despesas', 'esclarecimento'),
        ('departamento', 'esclarecimento'),
        ('2025', 'financeiro'),
    )
    failures = []
    for question, expected in cases:
        reply = ask(question, sid)
        domain = reply['domain']
        if domain != expected:
            failures.append(f'{question!r}: domínio esperado={expected}; obtido={domain}')
        if 'Você quer consultar Financeiro, Informações Internas ou Ouvidoria?' in reply['answer']:
            failures.append(f'{question!r}: resposta robótica de domínio')
        if domain == 'informacoes_internas' and '01_politica_ferias.md' not in {s['source'] for s in reply['sources']}:
            failures.append(f'{question!r}: política de férias não recuperada')
        if domain == 'financeiro':
            if 'consultar_financeiro' not in reply['tools_used']:
                failures.append(f'{question!r}: ferramenta financeira ausente')
            if 'lancamentos_financeiros.csv' not in {s['source'] for s in reply['sources']}:
                failures.append(f'{question!r}: fonte financeira ausente')
            if 'departamento' not in reply['answer'].lower():
                failures.append(f'{question!r}: agrupamento por departamento ausente')
    if failures:
        print('FALHAS:', *failures, sep='\n - ', flush=True)
        sys.exit(1)
    print('7/7 turnos do diálogo do navegador validados com SDK real.',flush=True)


if __name__ == '__main__':
    main()
