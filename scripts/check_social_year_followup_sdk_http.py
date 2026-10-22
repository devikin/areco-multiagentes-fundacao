"""Teste v0.2.23 no Docker real: saudação informal + correção de ano.

São três chamadas ao Agents SDK/OpenAI e uma validação local sem tokens.
A saída expõe trace, domínio e evidência para investigação sem fingir PASS.
"""
from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8000'


def ask(message: str, session_id: str) -> dict:
    payload = json.dumps({'message': message, 'session_id': session_id}, ensure_ascii=False).encode('utf-8')
    req = Request(BASE + '/api/v1/chat', data=payload, method='POST',
                  headers={'Content-Type': 'application/json; charset=utf-8'})
    with urlopen(req, timeout=90) as res:
        data = json.load(res)
    print(f'{message!r} -> {data.get("domain")} | {data.get("answer")}\n'
          f'  ferramentas={data.get("tools_used")} fontes={data.get("sources")} trace={data.get("trace_id")}',
          flush=True)
    assert data['session_id'] == session_id, 'Sessão não preservada'
    return data


def main() -> int:
    with urlopen(BASE + '/openapi.json', timeout=10) as res:
        info = json.load(res)['info']
    assert info['version'] == '0.2.23', 'Docker ainda não executa v0.2.23; reconstrua o container.'
    print('Versão v0.2.23 identificada. 3 chamadas REAIS à OpenAI + 1 local (205).', flush=True)
    sid = str(uuid4())
    social = ask('ola td berm', sid)
    assert social['domain'] == 'conversa', 'Saudação abreviada deveria receber uma saudação natural'
    assert 'Como posso te ajudar hoje?' in social['answer']
    print('PASS | saudação informal\n', flush=True)

    opening = ask('Quero consultar o total de despesas do departamento de Tecnologia', sid)
    assert opening['domain'] == 'esclarecimento' and 'ano' in opening['answer'].casefold(), \
        'Consulta incompleta deveria solicitar o ano antes do handoff'
    print('PASS | intenção financeira preservada e ano solicitado\n', flush=True)

    invalid = ask('205', sid)
    assert invalid['domain'] == 'esclarecimento'
    assert invalid['classification_method'] == 'validacao_entrada_local'
    assert invalid['token_usage']['requests'] == 0
    print('PASS | ano 205 rejeitado sem OpenAI\n', flush=True)

    result = ask('2025', sid)
    assert result['domain'] == 'financeiro', 'Ano corrigido não chegou ao Financeiro'
    assert 'transfer_to_financeiro' in result['handoffs'], 'Handoff financeiro ausente'
    assert 'consultar_financeiro' in result['tools_used'], 'Financeiro não consultou a ferramenta'
    assert 'lancamentos_financeiros.csv' in {c['source'] for c in result['sources']}, 'Fonte financeira ausente'
    assert '234.196,14' in result['answer'], 'Total filtrado de Tecnologia em 2025 divergente'
    print('PASS | 2025 retomado + consulta real a despesas de Tecnologia\n4/4 turnos verificados.', flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'FAIL | {type(exc).__name__}: {exc}', flush=True)
        raise
