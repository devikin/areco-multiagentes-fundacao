"""Smoke REAL v0.2.18: esclarecimento e continuidade por sessão no Docker.

São 5 chamadas reais à API OpenAI. Exige docker compose up --build -d.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8000'


def ask(question: str, session_id: str) -> dict:
    payload = json.dumps({'message': question, 'session_id': session_id}, ensure_ascii=False).encode('utf-8')
    req = Request(BASE+'/api/v1/chat', data=payload, method='POST',
                  headers={'Content-Type':'application/json; charset=utf-8'})
    with urlopen(req, timeout=120) as res:
        assert res.status == 200, res.status
        data = json.load(res)
    print(f"{question!r} => {data.get('domain')} | {data.get('answer')} | trace={data.get('trace_id')}", flush=True)
    assert data.get('engine') == 'sdk', data
    assert data.get('trace_id','').startswith('trace_'), data
    assert '*' not in data.get('answer',''), data
    assert data.get('session_id') == session_id, data
    return data


def main():
    print('5 consultas REAIS à OpenAI; haverá consumo de tokens.', flush=True)
    sid = str(uuid4())
    greeting = ask('Olá', sid)
    assert greeting['domain'] == 'conversa', greeting
    assert greeting['answer'] == 'Olá! Seja bem-vindo(a). Como posso te ajudar hoje?', greeting
    print('PASS | Saudação natural')

    ambiguous = ask('Gostaria de saber sobre algumas despesas', sid)
    assert ambiguous['domain'] == 'esclarecimento', ambiguous
    assert '?' in ambiguous['answer'], ambiguous
    assert not ambiguous.get('sources') and not ambiguous.get('handoffs'), ambiguous
    print('PASS | Esclarecimento sem handoff prematuro')

    finance = ask('O total de 2025', sid)
    assert finance['domain'] == 'financeiro', finance
    assert 'transfer_to_financeiro' in finance['handoffs'], finance
    assert 'consultar_financeiro' in finance['tools_used'], finance
    assert 'lancamentos_financeiros.csv' in {x['source'] for x in finance['sources']}, finance
    assert 'R$' in finance['answer'], finance
    print('PASS | Memória curta + handoff financeiro fundamentado')

    holidays = ask('Como solicito férias?', sid)
    assert holidays['domain'] == 'informacoes_internas', holidays
    assert '01_politica_ferias.md' in {x['source'] for x in holidays['sources']}, holidays
    assert 'buscar_documentos' in holidays['tools_used'], holidays
    print('PASS | Handoff direto para política de férias')

    outsider = ask('Quem venceu a Copa do Mundo de 2018?', str(uuid4()))
    assert outsider['domain'] == 'fora_de_escopo', outsider
    assert not outsider['handoffs'] and not outsider['tools_used'], outsider
    assert 'frança' not in outsider['answer'].lower(), outsider
    print('PASS | Fora de escopo sem vazamento factual')
    print('5/5 diálogos validados no Agents SDK real.')


if __name__ == '__main__':
    main()
