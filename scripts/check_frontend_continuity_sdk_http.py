"""Teste REAL de continuidade no OpenAI Agents SDK (v0.2.31).

Sem alterações na aplicação. Todos os turnos chamam a API e podem consumir tokens.
Cenários usam sessões distintas e respeitam o histórico de cada conversa.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unicodedata
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.2.31'
SEQUENCES={
 'frontend': [
  ('F01','com vai vc?'), ('F02','tenho duvidas'),
  ('F03','gostaria de saber a situacao de um protocolo'),
  ('F04','eu nao tenho o numero'), ('F05','reembolso'),
  ('F06','OUV-0016'), ('F07','n localizou o protocolo OUV-0016?'),
  ('F08','e qual e a prioridade dele?'),
 ],
 'switch': [
  ('X01','Qual o prazo para solicitar reembolso?'),
  ('X02','OUV-0016'),
  ('X03','Como solicito ferias?'),
  ('X04','OUV-0002'),
 ],
 'finance': [
  ('Y01','Quero consultar minhas despesas por departamento'),
  ('Y02','205'), ('Y03','2025'),
 ],
}


def norm(value):
    s=unicodedata.normalize('NFKD',str(value).casefold())
    return ''.join(c for c in s if not unicodedata.combining(c))


def call(base,message,sid,timeout):
    payload=json.dumps({'message':message,'session_id':sid},ensure_ascii=False).encode('utf-8')
    req=Request(base.rstrip('/')+'/api/v1/chat',data=payload,method='POST',
                headers={'Content-Type':'application/json; charset=utf-8'})
    with urlopen(req,timeout=timeout) as f:
        return json.load(f)


def check(case,d,history):
    errors=[]
    ans=str(d.get('answer',''))
    tools=d.get('tools_used') or []
    sources=d.get('sources') or []
    srcs={(x.get('source'),x.get('detail')) for x in sources if isinstance(x,dict)}
    txt=norm(ans)
    if d.get('generation_method')!='agents_sdk_llm': errors.append('resposta nao gerada pelo SDK/LLM')
    if not str(d.get('trace_id','')).startswith('trace_'): errors.append('trace ausente')
    if '*' in ans: errors.append('asteriscos proibidos')
    if case in ('F06','X02','X04'):
        pid='OUV-0002' if case=='X04' else 'OUV-0016'
        if d.get('domain')!='ouvidoria': errors.append('protocolo nao chegou a Ouvidoria')
        if 'buscar_protocolo' not in tools: errors.append('buscar_protocolo nao executada')
        if ('manifestacoes.csv',pid) not in srcs: errors.append('fonte do protocolo exato ausente')
        if 'aguardando area responsavel' not in txt: errors.append('status esperado ausente')
    elif case=='F07':
        # O mesmo status consultado no turno anterior pode ser reutilizado do histórico
        # sem nova ferramenta/handoff, assim como nos testes C02/C04 já aceitos.
        prior=history.get('F06',{})
        previous_citations={(x.get('source'),x.get('detail')) for x in (prior.get('sources') or []) if isinstance(x,dict)}
        if prior.get('status')!='PASS' or ('manifestacoes.csv','OUV-0016') not in previous_citations:
            errors.append('sem consulta anterior confiável para reutilizar a resposta')
        if 'aguardando area responsavel' not in txt or 'OUV-0016' not in ans.upper():
            errors.append('nao confirmou status correto do mesmo protocolo')
        if tools and ('buscar_protocolo' not in tools or ('manifestacoes.csv','OUV-0016') not in srcs):
            errors.append('nova consulta nao fundamentada na Ouvidoria')
    elif case=='F08':
        if 'media' not in txt: errors.append('prioridade media do OUV-0016 ausente')
        if 'OUV-0002' in ans: errors.append('memoria contaminada por outro protocolo')
    elif case=='X01':
        if d.get('domain')!='informacoes_internas': errors.append('politica de reembolso no agente errado')
        if 'buscar_documentos' not in tools: errors.append('busca documental nao executada')
        if '02_politica_reembolso.md' not in {x[0] for x in srcs}: errors.append('fonte reembolso ausente')
    elif case=='X03':
        if d.get('domain')!='informacoes_internas': errors.append('ferias no agente errado')
        if '01_politica_ferias.md' not in {x[0] for x in srcs}: errors.append('fonte ferias ausente')
    elif case=='Y01':
        if d.get('domain')!='financeiro': errors.append('financas nao encaminhadas')
        if sources: errors.append('ano nao informado mas retorno com fonte')
        if not any(w in txt for w in ('ano','periodo')): errors.append('nao pediu o ano')
    elif case=='Y02':
        if d.get('domain')!='financeiro': errors.append('perdeu contexto financeiro')
        if sources: errors.append('205 gerou fonte antes de confirmar ano')
    elif case=='Y03':
        if d.get('domain')!='financeiro': errors.append('ano nao retornou ao Financeiro')
        if 'consultar_financeiro' not in tools: errors.append('consulta financeira nao realizada')
        if 'lancamentos_financeiros.csv' not in {x[0] for x in srcs}: errors.append('fonte financeira ausente')
        if '2025' not in ans or 'departamento' not in txt: errors.append('nao retomou a intencao original')
    elif case in ('F03','F04','F05'):
        # Faltando código, o chatbot nao pode inventar situacao individual.
        if 'OUV-0016' in ans: errors.append('protocolo individual inventado antes de o usuario fornecer codigo')
    return errors


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--scenario',choices=['frontend','switch','finance','all'],default='frontend')
    ap.add_argument('--url',default='http://127.0.0.1:8000')
    ap.add_argument('--timeout',type=int,default=120)
    args=ap.parse_args()
    with urlopen(args.url.rstrip('/')+'/openapi.json',timeout=12) as f:
        version=json.load(f)['info']['version']
    if version!=VERSION:
        raise SystemExit(f'Versao Docker {version}; esperado {VERSION}. Rebuild necessario.')
    names=list(SEQUENCES) if args.scenario=='all' else [args.scenario]
    total=sum(len(SEQUENCES[n]) for n in names)
    print(f'TESTE REAL | {total} turnos com OpenAI; consome tokens.\n',flush=True)
    report={'suite':'continuity_frontend','version':version,'created_at':datetime.now(timezone.utc).isoformat(),'results':[]}
    for name in names:
        sid=str(uuid4())
        print('Sessao:',name,flush=True)
        session_history={}
        for code,message in SEQUENCES[name]:
            try:
                d=call(args.url,message,sid,args.timeout)
                errors=check(code,d,session_history)
                if d.get('session_id')!=sid: errors.append('sessao alterada')
                item={'id':code,'session_id':sid,'question':message,'answer':d.get('answer'),
                      'domain':d.get('domain'),'sources':d.get('sources',[]),
                      'tools_used':d.get('tools_used',[]),'handoffs':d.get('handoffs',[]),
                      'trace_id':d.get('trace_id'),'errors':errors,'status':'FAIL' if errors else 'PASS'}
            except Exception as e:
                item={'id':code,'session_id':sid,'question':message,'status':'FAIL',
                      'errors':[f'{type(e).__name__}: {e}']}
            report['results'].append(item)
            session_history[code]=item
            print(f'{code} | {item["status"]} | {message}',flush=True)
            print('  Dominio:',item.get('domain'),' Ferramentas:',item.get('tools_used',[]),flush=True)
            print('  Resposta:',item.get('answer','[nenhuma]'),flush=True)
            print('  Trace:',item.get('trace_id','-'),flush=True)
            if item['errors']:print('  Erros:', '; '.join(item['errors']),flush=True)
        print(flush=True)
    report['summary']=dict(Counter(x['status'] for x in report['results']))
    dest=ROOT/'docs'/'evidence';dest.mkdir(parents=True,exist_ok=True)
    fname='continuity_frontend_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json'
    path=dest/fname
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Resumo:',report['summary'],'| Relatorio:',path,flush=True)
    return 1 if report['summary'].get('FAIL',0) else 0

if __name__=='__main__':sys.exit(main())
