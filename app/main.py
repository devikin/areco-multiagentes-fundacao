"""Aplicação FastAPI. Request ID nos logs sem registrar dados sensíveis por padrão."""
from __future__ import annotations
from contextlib import asynccontextmanager
from pathlib import Path
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime,timezone
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.knowledge.ingest import bootstrap
from app.schemas import ChatRequest,ChatResponse
from app.sdk_integration.service import SdkChatService

ROOT=Path(__file__).resolve().parent.parent
load_dotenv(ROOT/'.env')
DATA_DIR=Path(os.getenv('KNOWLEDGE_DIR',str(ROOT/'data'/'knowledge')))


def default_database_path(root: Path, *, platform: str | None = None,
                          local_appdata: str | None = None) -> Path:
    """Evita manter SQLite na pasta sincronizada (Drive/OneDrive) no Windows."""
    platform = sys.platform if platform is None else platform
    if platform == 'win32':
        local = os.getenv('LOCALAPPDATA') if local_appdata is None else local_appdata
        if local:
            return Path(local) / 'ArecoMultiagentes' / 'knowledge.sqlite'
    return root / 'data' / 'runtime' / 'knowledge.sqlite'


# Um DATABASE_PATH explícito no .env continua tendo prioridade.
DB_PATH=Path(os.getenv('DATABASE_PATH') or default_database_path(ROOT))
logger=logging.getLogger('areco')
logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'),format='%(message)s')

@asynccontextmanager
async def lifespan(app:FastAPI):
    summary=bootstrap(DATA_DIR,DB_PATH)
    # SDK é o único mecanismo disponível. AGENT_ENGINE=sdk ainda é aceito
    # para compatibilidade com o .env já configurado na Fase 2.
    engine = os.getenv('AGENT_ENGINE', 'sdk').lower().strip()
    if engine != 'sdk':
        raise RuntimeError('Esta versão utiliza exclusivamente Agents SDK. Remova AGENT_ENGINE=legacy do .env.')
    app.state.chat_service = SdkChatService(DB_PATH, DATA_DIR)
    app.state.agent_engine = 'sdk'
    logger.info(json.dumps({'event':'startup','timestamp':datetime.now(timezone.utc).isoformat(),'ingestion':summary,'engine':engine},ensure_ascii=False))
    yield

app=FastAPI(title='Areco Multiagentes — Agents SDK',version='0.2.35',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'frontend'),name='static')

@app.get('/')
def index():
    return FileResponse(ROOT/'frontend'/'index.html')

@app.get('/health')
def health():
    return {'status':'ok','engine':app.state.agent_engine,'loaded_agents':list(app.state.chat_service.agents)}

@app.post('/api/v1/chat',response_model=ChatResponse)
async def chat(req:ChatRequest):
    start=time.perf_counter()
    try:
        result = await app.state.chat_service.chat(req.message, session_id=req.session_id)
        logger.info(json.dumps({
            'event':'chat','timestamp':datetime.now(timezone.utc).isoformat(),'request_id':result.request_id,'domain':result.domain,
            'agent':result.agent,'sources':[x.source for x in result.sources],
            'classification_method':result.classification_method,
            'generation_method':result.generation_method,
            'classification_error':result.classification_error,
            'generation_error':result.generation_error,
            'engine':result.engine,'trace_id':result.trace_id,
            'handoffs':result.handoffs,'tools_used':result.tools_used,
            'token_usage':result.token_usage,
            'status':'ok',
            'latency_ms':round((time.perf_counter()-start)*1000),
            'message_sha256':hashlib.sha256(req.message.encode()).hexdigest()[:12]
        },ensure_ascii=False))
        return result
    except Exception as exc:
        logger.exception('Falha de execução no agente')
        raise HTTPException(status_code=503,detail='Não foi possível concluir a consulta.') from exc
