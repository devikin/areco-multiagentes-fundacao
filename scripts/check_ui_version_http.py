"""Verifica os arquivos de UI efetivamente servidos pelo Docker, sem consumir tokens."""
from __future__ import annotations
import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

VERSION = '0.2.35'
GREETING = 'Olá, como posso te ajudar hoje?'
OLD_GREETING = 'Olá! Consulte lançamentos financeiros'
OLD_LOADING = 'Consultando base de conhecimento'


def fetch(url: str) -> str:
    with urlopen(url, timeout=12) as response:
        assert response.status == 200, f'HTTP {response.status}: {url}'
        return response.read().decode('utf-8-sig')


def check(base_url: str) -> None:
    base = base_url.rstrip('/')
    html = fetch(base+'/')
    assert GREETING in html, 'HTML antigo: a saudação não foi atualizada.'
    assert OLD_GREETING not in html, 'HTML antigo detectado.'
    assert '>v'+VERSION+'</span>' in html and 'MVP de avaliação' in html, 'Versão/MVP não aparecem no cabeçalho.'
    assert '/static/app.js?v='+VERSION in html, 'JS sem identificação de versão.'
    assert '/static/styles.css?v='+VERSION in html, 'CSS sem identificação de versão.'
    print('PASS | HTML | saudação correta + versão v'+VERSION+' acima do MVP')

    js = fetch(base+'/static/app.js?v='+VERSION)
    assert "renderMessage('...', 'bot')" in js, 'Indicador de carregamento ainda não é ...'
    assert OLD_LOADING not in js, 'JS antigo detectado.'
    assert 'session_id: sessionId' in js, 'Session ID não está sendo transmitido.'
    assert 'new AbortController()' in js, 'Controle de timeout ausente.'
    assert 'input.value = text' in js, 'Restauração de texto não encontrada.'
    assert "fetch('/health'" in js, 'Preflight /health ausente.'
    assert 'await waitForServer()' in js, 'Reconexão ausente.'
    assert 'RECONNECT_CANCELLED' in js, 'Cancelamento ausente.'
    assert html.find('id="reconnectOverlay"') >= 0, 'Overlay de reconexão ausente.'
    print('PASS | JavaScript | sessão + preflight + reconexão segura')

    css = fetch(base+'/static/styles.css?v='+VERSION)
    assert '.release-version{' in css, 'Estilo da versão não encontrado.'
    assert '.reconnect-overlay' in css and 'backdrop-filter:blur(' in css, 'Blur de reconexão ausente.'
    print('PASS | CSS | versão + overlay com blur')

    metadata = json.loads(fetch(base+'/openapi.json'))
    assert metadata.get('info',{}).get('version') == VERSION, 'API está rodando uma versão anterior.'
    print('PASS | FastAPI | versão '+VERSION+' servida pelo container')


def main() -> int:
    parser=argparse.ArgumentParser(description='Verifica versão efetiva da UI Docker; 0 tokens OpenAI.')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args=parser.parse_args()
    try:
        check(args.base_url)
    except (AssertionError, HTTPError, URLError, OSError, ValueError) as exc:
        print(f'FAIL | UI desatualizada ou indisponível | {exc}')
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
