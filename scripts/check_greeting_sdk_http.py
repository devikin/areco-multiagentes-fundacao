"""Smoke HTTP de saudação da v0.2.34. Consome tokens OpenAI em --run.

G01: saudação isolada (sessão nova)
G02: saudação + intenção (sessão nova)
G03/G04: consulta direta à Ouvidoria e acompanhamento (mesma sessão)
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.34'
CASES = (
    ('G01', 'oi, tudo bem?', 'saudacao'),
    ('G02', 'ola td bem? quero saber sobre protocolo', 'mista'),
    ('G03', 'Qual e a situacao do protocolo OUV-0016?', 'protocolo'),
    ('G04', 'e qual e a prioridade dele?', 'protocolo'),
)


def norm(txt):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(txt).casefold())
                   if not unicodedata.combining(c))


def issues(code, data, history):
    answer = str(data.get('answer') or '').strip()
    a = norm(answer)
    tools = data.get('tools_used') or []
    srcs = data.get('sources') or []
    errors=[]
    if not answer: errors.append('resposta vazia')
    if not str(data.get('trace_id','')).startswith('trace_'): errors.append('trace ausente')
    if data.get('generation_method') != 'agents_sdk_llm': errors.append('geracao nao atribuida a LLM')
    if re.search(r'^ola\s*,?\s*como posso te ajudar hoje\s*\?',a):
        errors.append('repetiu a mensagem inicial do frontend')
    if code in ('G01','G02'):
        if tools or srcs: errors.append('consulta ou ferramenta inesperada')
        if data.get('domain') != 'conversa': errors.append('esperado orquestrador em saudacao sem protocolo')
    if code == 'G02' and not any(x in a for x in ('ouv-', 'numero do protocolo','codigo do protocolo','qual protocolo','informe o protocolo','numero do seu protocolo')):
        errors.append('nao pediu o identificador do protocolo')
    if code == 'G03':
        if data.get('domain') != 'ouvidoria':errors.append('nao encaminhou para Ouvidoria')
        if 'buscar_protocolo' not in tools:errors.append('nao chamou buscar_protocolo')
        if not any(x.get('source')=='manifestacoes.csv' and x.get('detail')=='OUV-0016' for x in srcs if isinstance(x,dict)):
            errors.append('fonte de OUV-0016 ausente')
        if 'aguardando' not in a or 'responsavel' not in a:errors.append('status incorreto')
    if code == 'G04':
        if not history.get('G03') or history['G03']['status']!='PASS':errors.append('consulta anterior nao validada')
        if 'prioridade' not in a or 'media' not in a:errors.append('prioridade nao confirmada')
    return errors


def self_test():
    base={'answer':'Tudo bem! Como posso ajudar?', 'domain':'conversa', 'tools_used':[],
          'sources':[], 'trace_id':'trace_test', 'generation_method':'agents_sdk_llm'}
    assert not issues('G01',base,{})
    assert issues('G01',{**base,'answer':'Olá, como posso te ajudar hoje?'},{})
    assert not issues('G02',{**base,'answer':'Claro! Qual o número do protocolo OUV-NNNN?'},{})
    assert issues('G02',{**base,'answer':'Tudo bem!'},{})
    prot={**base,'answer':'OUV-0016 está Aguardando área responsável.', 'domain':'ouvidoria',
          'tools_used':['buscar_protocolo'],
          'sources':[{'source':'manifestacoes.csv','detail':'OUV-0016'}]}
    assert not issues('G03',prot,{})
    assert issues('G03',{**prot,'tools_used':[]},{})
    assert not issues('G04',{**base,'answer':'A prioridade é média.'},{'G03':{'status':'PASS'}})
    assert issues('G04',{**base,'answer':'A prioridade é média.'},{})
    print('PASS | 8 verificacoes locais; sem OpenAI.')


def main():
    p=argparse.ArgumentParser(description='v0.2.34 smoke greeting + protocolo')
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test', action='store_true')
    mode.add_argument('--run', action='store_true')
    p.add_argument('--url', default='http://127.0.0.1:8000')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    if args.self_test:
        self_test();return
    with urlopen(args.url.rstrip('/')+'/openapi.json',timeout=10) as r:
        version=json.load(r)['info']['version']
    if version!=VERSION:raise RuntimeError(f'Versao inesperada: {version}, esperada {VERSION}')
    sessions={t:str(uuid4()) for t in ('saudacao','mista','protocolo')}
    results=[]
    history={}
    for code,query,group in CASES:
        payload=json.dumps({'message':query,'session_id':sessions[group]}).encode('utf-8')
        req=Request(args.url.rstrip('/')+'/api/v1/chat',data=payload,
                    headers={'Content-Type':'application/json; charset=utf-8'},method='POST')
        with urlopen(req,timeout=120) as r:data=json.load(r)
        errors=issues(code,data,history)
        record={'id':code,'question':query,'answer':data.get('answer'),
                'status':'FAIL' if errors else 'PASS','errors':errors,
                'domain':data.get('domain'),'sources':data.get('sources'),
                'tools_used':data.get('tools_used'),'handoffs':data.get('handoffs'),
                'trace_id':data.get('trace_id'),'session_id':data.get('session_id')}
        results.append(record); history[code]=record
        print(f'{code} | {record["status"]} | {query}')
        print('  Resposta:',record['answer'])
        print('  Dominio:',record['domain'],'| Ferramentas:',record['tools_used'])
        if errors:print('  Erros:', '; '.join(errors))
        print('  Trace:', record['trace_id'])
    report={'suite':'greeting_v033','version':version,'created_at':datetime.now(timezone.utc).isoformat(),
            'results':results,'summary':dict(Counter(x['status'] for x in results))}
    path=args.output or ROOT/'docs/evidence'/('greeting_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Resumo:',report['summary'],'| Relatorio:',path)
if __name__=='__main__':main()
