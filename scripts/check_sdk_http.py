"""Smoke test ao vivo do FastAPI integrado ao Agents SDK (3 handoffs reais).

Rodar com servidor SDK iniciado; três chamadas à OpenAI geram custos.
"""
from __future__ import annotations
import json
import urllib.request

URL = 'http://127.0.0.1:8000'


def get_json(path: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload else None
    request = urllib.request.Request(
        URL + path, data=body,
        headers={'Content-Type': 'application/json'} if body else {},
        method='POST' if body else 'GET',
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        assert response.status == 200
        return json.load(response)


def main() -> None:
    health = get_json('/health')
    assert health['status'] == 'ok', health
    assert health['engine'] == 'sdk', f"Modo atual: {health['engine']}. Esta versão exige SDK."
    cases = [
        ('Como solicito férias?', 'informacoes_internas', '01_politica_ferias.md', '30 dias'),
        ('Quanto foi gasto em despesas pagas de janeiro a março de 2025?',
         'financeiro', 'lancamentos_financeiros.csv', '305.937,01'),
        ('Qual o status do protocolo OUV-0002?',
         'ouvidoria', 'manifestacoes.csv', 'Aguardando área responsável'),
    ]
    for question, domain, source, expected_text in cases:
        response = get_json('/api/v1/chat', {'message': question})
        assert response['engine'] == 'sdk', response
        assert response['domain'] == domain, response
        assert response['classification_method'] == 'agents_sdk_handoff', response
        assert response['handoffs'], response
        assert response['tools_used'], response
        assert any(x['source'] == source for x in response['sources']), response
        assert expected_text.lower() in response['answer'].lower(), response
        print(f"OK: {domain} | fonte: {source} | latência: {response['latency_ms']}ms "
              f"| trace: {response['trace_id']}")
    print('3/3 handoffs via FastAPI verificados no ambiente em execução.')


if __name__ == '__main__':
    main()
