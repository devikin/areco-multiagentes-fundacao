"""Smoke test real da nova ferramenta Ouvidoria pelo FastAPI; gera custos na API OpenAI."""
from __future__ import annotations

import json
import urllib.request

BASE = 'http://127.0.0.1:8000'


def request(question: str) -> dict:
    payload = json.dumps({'message': question}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE + '/api/v1/chat', data=payload, method='POST',
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        assert response.status == 200
        return json.load(response)


def main() -> None:
    cases = [
        ('Quantas manifestações de prioridade Alta existem?', '38'),
        ('Distribua as manifestações da Ouvidoria por prioridade.', '79'),
    ]
    for question, expected in cases:
        reply = request(question)
        assert reply.get('engine') == 'sdk', reply
        assert reply.get('domain') == 'ouvidoria', reply
        assert reply.get('handoffs'), reply
        assert 'consultar_manifestacoes' in reply.get('tools_used', []), reply
        assert any(c['source'] == 'manifestacoes.csv' for c in reply.get('sources', [])), reply
        assert expected in reply.get('answer', ''), reply
        assert reply.get('trace_id', '').startswith('trace_'), reply
        print(f"OK: {question} | trace={reply['trace_id']} | "
              f"latência={reply['latency_ms']}ms")
    print('2/2 consultas avançadas Ouvidoria verificadas com Agents SDK real.')


if __name__ == '__main__':
    main()
