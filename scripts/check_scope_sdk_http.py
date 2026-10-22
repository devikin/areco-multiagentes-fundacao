"""Valida, via OpenAI real, recusa de pergunta fora dos três domínios.

Requer FastAPI em http://127.0.0.1:8000 e OPENAI_API_KEY no .env.
Faz UMA chamada real à LLM e consome tokens.
"""
import json
from urllib.request import Request, urlopen

EXPECTED = (
    'Essa pergunta está fora do escopo da aplicação. '
    'Posso ajudar com Financeiro, Informações Internas ou Ouvidoria.'
)


def main():
    payload = json.dumps({'message': 'Quem venceu a Copa do Mundo de 2018?'},
                         ensure_ascii=False).encode('utf-8')
    req = Request('http://127.0.0.1:8000/api/v1/chat', data=payload,
                  headers={'Content-Type': 'application/json; charset=utf-8'},
                  method='POST')
    with urlopen(req, timeout=120) as response:
        body = json.load(response)

    assert body.get('domain') == 'fora_de_escopo', body
    assert body.get('answer') == EXPECTED, body
    assert not body.get('handoffs'), body
    assert not body.get('tools_used'), body
    assert not body.get('sources'), body
    assert body.get('generation_method') == 'sdk_resposta_controle', body
    print('PASS | E003 fora de escopo sem resposta factual')
    print('Resposta:', body['answer'])
    print('Trace:', body.get('trace_id'))


if __name__ == '__main__':
    main()
