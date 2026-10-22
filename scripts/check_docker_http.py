"""Smoke HTTP para a aplicação em Docker. Sem chat por padrão (custo zero de API)."""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED_AGENTS = {'financeiro', 'informacoes_internas', 'ouvidoria'}


def _fetch(url: str, *, payload: dict | None = None, timeout: int = 10) -> tuple[int, bytes]:
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None
    req = Request(url, data=body, headers={'Content-Type': 'application/json; charset=utf-8'} if body is not None else {})
    with urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def run(base_url: str, *, chat: bool = False) -> None:
    base_url = base_url.rstrip('/')
    code, data = _fetch(f'{base_url}/health')
    health = json.loads(data)
    assert code == 200, f'/health HTTP {code}'
    assert health.get('status') == 'ok' and health.get('engine') == 'sdk', health
    assert EXPECTED_AGENTS.issubset(set(health.get('loaded_agents', []))), health
    print('PASS | /health | Agents SDK + 3 especialistas')

    code, html = _fetch(f'{base_url}/')
    assert code == 200 and b'<html' in html.lower(), 'Frontend não disponível'
    print('PASS | / | Frontend HTML')

    if chat:
        # A chamada real não executa no modo padrão: é paga e depende de chave válida.
        code, data = _fetch(f'{base_url}/api/v1/chat', payload={'message':'Como solicito férias?'}, timeout=75)
        reply = json.loads(data)
        assert code == 200, f'Chat HTTP {code}'
        assert reply.get('domain') == 'informacoes_internas', reply
        assert 'transfer_to_informacoes_internas' in reply.get('handoffs', []), reply
        assert 'buscar_documentos' in reply.get('tools_used', []), reply
        assert any(item.get('source') == '01_politica_ferias.md' for item in reply.get('sources', [])), reply
        assert reply.get('trace_id', '').startswith('trace_'), reply
        print(f"PASS | /api/v1/chat | Handoff, ferramenta, fonte | {reply['trace_id']}")


def main() -> int:
    parser = argparse.ArgumentParser(description='Verifica a aplicação em Docker via HTTP')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--chat', action='store_true', help='Executa uma chamada real à OpenAI (consome tokens).')
    args = parser.parse_args()
    try:
        run(args.base_url, chat=args.chat)
    except (AssertionError, HTTPError, URLError, OSError, ValueError) as exc:
        print(f'FAIL | Docker smoke | {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
