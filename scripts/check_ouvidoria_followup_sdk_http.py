"""Teste LIVE opcional do caso OUV-0013: duas chamadas reais ao SDK.

Executar após docker compose up --build -d, sem expor a chave OpenAI.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen
from uuid import uuid4

BASE = 'http://127.0.0.1:8000/api/v1/chat'


def ask(message: str, sid: str) -> dict:
    body = json.dumps({'message':message,'session_id':sid},ensure_ascii=False).encode('utf-8')
    req = Request(BASE,data=body,headers={'Content-Type':'application/json; charset=utf-8'},method='POST')
    with urlopen(req,timeout=120) as res:
        data=json.load(res)
    assert data.get('trace_id','').startswith('trace_'),data
    assert data.get('session_id')==sid,data
    print(f"{message} => {data['domain']} | {data['answer']} | fonte={data['sources']} | "
          f"método={data['generation_method']} | trace={data['trace_id']}",flush=True)
    return data


def main():
    print('2 consultas REAIS à OpenAI; haverá consumo de tokens.',flush=True)
    sid=str(uuid4())
    initial=ask('Qual o status do protocolo OUV-0013?',sid)
    assert initial['domain']=='ouvidoria',initial
    assert any(s['source']=='manifestacoes.csv' for s in initial['sources']), initial
    assert 'buscar_protocolo' in initial['tools_used'], initial
    after=ask('mas já foi reembolsado?',sid)
    assert after['domain']=='ouvidoria',after
    assert 'OUV-0013' in after['answer'],after
    assert 'não comprova' in after['answer'] or 'não confirma' in after['answer'] or 'não é possível confirmar' in after['answer'],after
    assert any(s['source']=='manifestacoes.csv' for s in after['sources']),after
    assert 'buscar_protocolo' in after['tools_used'],after
    assert 'sdk_sem_evidencia' != after['generation_method'],after
    assert '*' not in after['answer'],after
    print('2/2 | Contexto + resposta verificável da Ouvidoria no Docker.',flush=True)

if __name__=='__main__':
    main()
