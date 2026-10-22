"""Validação HTTP real do novo RAG; invoca a API OpenAI e gera custos."""
import json
import urllib.request

BASE = 'http://127.0.0.1:8000'


def ask(question: str) -> dict:
    payload = json.dumps({'message': question}, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE + '/api/v1/chat', data=payload, method='POST',
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as response:
        assert response.status == 200
        return json.load(response)


def main():
    cases = [
        ('Como solicito férias?', '01_politica_ferias.md'),
        ('Posso trabalhar de casa?', '06_politica_home_office.md'),
        ('Qual o prazo para pedir reembolso?', '02_politica_reembolso.md'),
    ]
    for question, source in cases:
        reply = ask(question)
        assert reply.get('domain') == 'informacoes_internas', reply
        assert reply.get('engine') == 'sdk', reply
        assert 'buscar_documentos' in reply.get('tools_used', []), reply
        assert 'transfer_to_informacoes_internas' in reply.get('handoffs', []), reply
        assert any(item.get('source') == source for item in reply.get('sources', [])), reply
        assert any('versão' in item.get('detail', '').lower() for item in reply.get('sources', [])), reply
        assert reply.get('trace_id', '').startswith('trace_'), reply
        assert reply.get('answer'), reply
        print(f"OK: {source} | trace={reply['trace_id']} | {reply['latency_ms']} ms")
    print('3/3 consultas internas com fontes validadas no Agents SDK real.')


if __name__ == '__main__':
    main()
