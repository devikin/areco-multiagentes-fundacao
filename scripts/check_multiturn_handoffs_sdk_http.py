"""Teste real de continuidade e handoffs do Areco Multiagentes v0.2.27.

Seis turnos na MESMA sessão. Nenhuma alteração na aplicação ou banco.
- Sem parâmetros: 6 interações reais com OpenAI via FastAPI (consome tokens).
- --reassess-report: reavalia relatório salvo SEM acessar API (zero tokens).

Atenção: resposta do histórico não comprova consulta nova. O relatório registra
explicitamente se a fundamentação vem de ferramenta atual ou turno anterior.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000'
VERSION = '0.2.27'

SCENARIOS = [
    ('C01', 'Qual o status do protocolo OUV-0002?', 'Busca inicial na Ouvidoria'),
    ('C02', 'E qual é a prioridade dele?', 'Memória do mesmo protocolo'),
    ('C03', 'Como solicito férias?', 'Handoff da Ouvidoria para Internas'),
    ('C04', 'E com quantos dias de antecedência?', 'Memória da política de férias'),
    ('C05', 'Qual departamento tem maior orçamento em janeiro de 2026?', 'Handoff para Financeiro'),
    ('C06', 'E em fevereiro de 2026?', 'Memória e mudança de mês no Financeiro'),
]


def normalized(value: object) -> str:
    text = unicodedata.normalize('NFKD', str(value).casefold())
    return ''.join(ch for ch in text if not unicodedata.combining(ch))


def ask(message: str, session_id: str) -> dict:
    data = json.dumps({'message': message, 'session_id': session_id}, ensure_ascii=False).encode('utf-8')
    req = Request(BASE + '/api/v1/chat', data=data,
                  headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
    with urlopen(req, timeout=120) as response:
        return json.load(response)


def source_names(response: dict) -> set[str]:
    return {x.get('source', '') for x in response.get('sources', []) if isinstance(x, dict)}


def generic_checks(data: dict, session: str, *, from_saved_report: bool = False) -> list[str]:
    errors = []
    # O arquivo antigo guardava somente resumo de cada resposta. A auditoria
    # anterior já executou os checks de engine, generation_method e session_id.
    # Não fingir que a reavaliação offline tem esses campos ausentes.
    if not from_saved_report:
        if data.get('engine') != 'sdk':
            errors.append('motor diferente de Agents SDK')
        if data.get('generation_method') != 'agents_sdk_llm':
            errors.append('resposta não atribuída à LLM')
        if data.get('session_id') != session:
            errors.append('session_id alterado entre os turnos')
    if not str(data.get('trace_id') or '').startswith('trace_'):
        errors.append('trace ausente')
    if not str(data.get('answer') or '').strip():
        errors.append('resposta vazia')
    if '*' in str(data.get('answer') or ''):
        errors.append('asterisco na resposta')
    return errors


def prior_tool_evidence(history: dict[str, dict], case: str, tool: str,
                        source: str, detail: str | None = None) -> dict | None:
    """Vincula resposta à consulta anterior da MESMA sessão, não a um palpite."""
    previous = history.get(case)
    if not previous or previous.get('status') != 'PASS':
        return None
    if tool not in (previous.get('tools_used') or []):
        return None
    if not any(isinstance(item, dict) and item.get('source') == source and
               (detail is None or item.get('detail') == detail)
               for item in (previous.get('sources') or [])):
        return None
    if not str(previous.get('trace_id') or '').startswith('trace_'):
        return None
    return {'turn': case, 'source': source, 'tool': tool, 'trace_id': previous['trace_id']}


def check(case: str, data: dict, history: dict[str, dict]) -> tuple[list[str], str, list[dict]]:
    """Verifica conteúdo + cadeia de evidência, sem exigir handoff redundante."""
    errors = []
    answer = normalized(data.get('answer', ''))
    sources = source_names(data)
    tools = set(data.get('tools_used') or [])
    domain = data.get('domain')
    evidence_origin = 'current_tool' if tools else 'none'
    historical_evidence: list[dict] = []

    if case == 'C01':
        if domain != 'ouvidoria':
            errors.append(f'domínio incorreto na consulta inicial: {domain}')
        if 'manifestacoes.csv' not in sources or 'buscar_protocolo' not in tools:
            errors.append('não consultou o protocolo na fonte da Ouvidoria')
        if not any(isinstance(x, dict) and x.get('source') == 'manifestacoes.csv'
                   and x.get('detail') == 'OUV-0002' for x in data.get('sources', [])):
            errors.append('não confirmou a identidade do protocolo OUV-0002 na fonte')
        if 'aguardando' not in answer or 'responsavel' not in answer:
            errors.append('status do OUV-0002 incorreto ou ausente')

    elif case == 'C02':
        if domain not in ('ouvidoria', 'conversa'):
            errors.append(f'domínio incoerente com acompanhamento do protocolo: {domain}')
        if 'baixa' not in answer or 'ouv-0002' not in answer:
            errors.append('não recuperou a prioridade Baixa do protocolo OUV-0002')
        if 'buscar_protocolo' in tools and 'manifestacoes.csv' in sources:
            if not any(isinstance(x, dict) and x.get('detail') == 'OUV-0002'
                       for x in data.get('sources', [])):
                errors.append('nova consulta não comprovou o protocolo correto')
            evidence_origin = 'current_tool'
        elif not tools and not sources:
            reference = prior_tool_evidence(history, 'C01', 'buscar_protocolo',
                                            'manifestacoes.csv', 'OUV-0002')
            if reference is None:
                errors.append('resposta sem fonte atual e sem consulta anterior validada de OUV-0002')
            else:
                historical_evidence.append(reference)
                evidence_origin = 'prior_tool_record'
        else:
            errors.append('ferramenta/fonte incompatível com a prioridade do protocolo')

    elif case == 'C03':
        if domain != 'informacoes_internas':
            errors.append(f'domínio incorreto para política de férias: {domain}')
        if '30 dias' not in answer:
            errors.append('não informou antecedência correta de 30 dias')
        if '01_politica_ferias.md' not in sources or 'buscar_documentos' not in tools:
            errors.append('não consultou a política de férias')

    elif case == 'C04':
        if domain not in ('informacoes_internas', 'conversa'):
            errors.append(f'domínio incoerente com acompanhamento de férias: {domain}')
        if '30 dias' not in answer or 'ferias' not in answer:
            errors.append('não recuperou os 30 dias de antecedência das férias')
        if 'buscar_documentos' in tools and '01_politica_ferias.md' in sources:
            evidence_origin = 'current_tool'
        elif not tools and not sources:
            reference = prior_tool_evidence(history, 'C03', 'buscar_documentos',
                                            '01_politica_ferias.md')
            prior_answer = normalized(history.get('C03', {}).get('answer', ''))
            if reference is None or '30 dias' not in prior_answer or 'ferias' not in prior_answer:
                errors.append('resposta sem fonte atual e sem antecedência fundamentada em C03')
            else:
                historical_evidence.append(reference)
                evidence_origin = 'prior_answer'
        else:
            errors.append('ferramenta/fonte incompatível com a política de férias')

    elif case in ('C05', 'C06'):
        if domain != 'financeiro':
            errors.append(f'Financeiro não assumiu/manteve a conversa (domínio={domain})')
        if 'consultar_financeiro' not in tools or 'orcamento_mensal.csv' not in sources:
            errors.append('não executou consulta de orçamento com fonte')
        if 'tecnologia' not in answer:
            errors.append('não identificou o departamento Tecnologia')
        expected = '43.229,05' if case == 'C05' else '48.243,24'
        if expected not in str(data.get('answer', '')):
            errors.append(f'valor incorreto: esperado R$ {expected}')
        if case == 'C06':
            details = ' '.join(str(x.get('detail') or '') for x in data.get('sources', [])
                               if isinstance(x, dict))
            if not re.search(r'2026\s+meses\s+02\s*[–—-]\s*02', details):
                errors.append('período consultado não foi fevereiro de 2026')

    return errors, evidence_origin, historical_evidence


def evaluate(code: str, objective: str, question: str, response: dict,
             session: str, history: dict[str, dict], *, saved: bool = False) -> dict:
    generic = generic_checks(response, session, from_saved_report=saved)
    check_errors, origin, history_sources = check(code, response, history)
    errors = generic + check_errors
    return {
        'id': code, 'objective': objective, 'question': question,
        'answer': response.get('answer'), 'domain': response.get('domain'),
        'sources': response.get('sources'), 'tools_used': response.get('tools_used'),
        'handoffs': response.get('handoffs'), 'trace_id': response.get('trace_id'),
        'token_usage': response.get('token_usage'),
        'evidence_origin': origin, 'historical_evidence': history_sources,
        'status': 'FAIL' if errors else 'PASS', 'errors': errors,
    }


def print_result(result: dict) -> None:
    print(f'{result["id"]} | {result["status"]} | {result.get("objective", "")}', flush=True)
    print(f'Pergunta: {result.get("question", "")}', flush=True)
    print(f'Domínio: {result.get("domain", "-")}; ferramentas: {result.get("tools_used", [])}', flush=True)
    print(f'Resposta: {result.get("answer", "-")}', flush=True)
    print(f'Evidência: {result.get("evidence_origin", "none")}', flush=True)
    for ref in result.get('historical_evidence') or []:
        print(f'  Reutilizou {ref["turn"]}: {ref["source"]} | trace={ref["trace_id"]}', flush=True)
    print(f'Trace: {result.get("trace_id", "-")}', flush=True)
    if result.get('errors'):
        print('Erros: ' + '; '.join(result['errors']), flush=True)
    print(flush=True)


def save_report(report: dict, output: Path) -> None:
    report['summary'] = {
        'PASS': sum(item['status'] == 'PASS' for item in report['results']),
        'FAIL': sum(item['status'] == 'FAIL' for item in report['results']),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Resumo: {report["summary"]} | Relatório: {output}', flush=True)


def real_test() -> int:
    with urlopen(BASE + '/openapi.json', timeout=10) as response:
        version = json.load(response)['info']['version']
    if version != VERSION:
        print(f'ERRO: Docker está na versão {version}; este teste é para v{VERSION}.')
        return 2

    session = str(uuid4())
    report = {'suite': 'multiturn_handoffs', 'version': version,
              'created_at': datetime.now(timezone.utc).isoformat(),
              'session_id': session, 'results': [], 'evaluator_revision': 'context-aware-v2'}
    history: dict[str, dict] = {}
    print('TESTE REAL | 6 turnos na mesma sessão | Consome tokens OpenAI.\n', flush=True)

    for code, question, objective in SCENARIOS:
        try:
            response = ask(question, session)
            result = evaluate(code, objective, question, response, session, history)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
            result = {'id': code, 'objective': objective, 'question': question,
                      'status': 'FAIL', 'errors': [f'{type(exc).__name__}: {exc}'],
                      'evidence_origin': 'none', 'historical_evidence': []}
        report['results'].append(result)
        history[code] = result
        print_result(result)

    output = ROOT / 'docs' / 'evidence' / f'multiturn_handoffs_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json'
    save_report(report, output)
    return 0 if report['summary']['FAIL'] == 0 else 1


def reassess(saved_path: str) -> int:
    folder = ROOT / 'docs' / 'evidence'
    if saved_path == 'latest':
        matches = sorted(folder.glob('multiturn_handoffs_*.json'), reverse=True)
        if not matches:
            print(f'ERRO: Nenhum relatório anterior encontrado em {folder}')
            return 2
        source = matches[0]
    else:
        source = Path(saved_path).expanduser().resolve()
    original = json.loads(source.read_text(encoding='utf-8'))
    if original.get('suite') != 'multiturn_handoffs':
        print('ERRO: Arquivo não é um relatório de multiturn_handoffs.')
        return 2
    items = original.get('results', [])
    if [x.get('id') for x in items] != [x[0] for x in SCENARIOS]:
        print('ERRO: Relatório anterior não contém os seis cenários esperados, na ordem.')
        return 2

    history: dict[str, dict] = {}
    report = {'suite': 'multiturn_handoffs', 'version': original.get('version'),
              'created_at': datetime.now(timezone.utc).isoformat(),
              'session_id': original.get('session_id'), 'results': [],
              'evaluator_revision': 'context-aware-v2',
              'reassessed_from': str(source),
              'original_summary': original.get('summary'),
              'limitations': 'Modo offline: engine, generation_method e session_id por turno não constavam do JSON anterior; checks originais foram previamente executados e não são repetidos.',
              'api_calls': 0}
    print(f'REAVALIAÇÃO OFFLINE | {source.name} | ZERO tokens OpenAI.\n', flush=True)
    for (code, question, objective), old in zip(SCENARIOS, items):
        result = evaluate(code, objective, question, old, str(original.get('session_id')),
                          history, saved=True)
        # Conservar falhas antigas não relacionadas aos critérios semânticos do script.
        old_errors = old.get('errors') or []
        non_scoring = [e for e in old_errors if e.startswith(('HTTPError:', 'URLError:',
                        'TimeoutError:', 'OSError:', 'ValueError:', 'KeyError:',
                        'motor diferente', 'resposta não atribuída', 'session_id alterado'))]
        for error in non_scoring:
            if error not in result['errors']:
                result['errors'].append(error)
        if result['errors']:
            result['status'] = 'FAIL'
        result['previous_status'] = old.get('status')
        result['previous_errors'] = old_errors
        report['results'].append(result)
        history[code] = result
        print_result(result)
    output = source.with_name('multiturn_reassessed_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.json')
    save_report(report, output)
    return 0 if report['summary']['FAIL'] == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description='Teste de continuidade multiagente v0.2.27')
    parser.add_argument('--reassess-report', nargs='?', const='latest', default=None,
                        metavar='ARQUIVO', help='Reavaliar JSON salvo, ou o mais recente, sem chamadas OpenAI')
    args = parser.parse_args()
    if args.reassess_report is not None:
        return reassess(args.reassess_report)
    return real_test()


if __name__ == '__main__':
    sys.exit(main())
