import asyncio
import json
import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, StrictBool

from agent import react_agent
import store

app = FastAPI(title='Week 11 · ReAct Studio')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:8003', 'http://127.0.0.1:8003'],
                   allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])
active = set()
pending = {}


@app.get('/health')
def health():
    return {'status': 'ok', 'model_configured': bool(os.getenv('DEEPSEEK_API_KEY'))}


@app.post('/sessions')
def create_session():
    session_id = str(uuid4())
    store.create(session_id)
    return {'id': session_id, 'title': '新会话'}


@app.get('/sessions/{session_id}')
def history(session_id: str):
    data = store.read(session_id)
    if data is None:
        raise HTTPException(404, '会话不存在')
    return {key: data[key] for key in ('id', 'title', 'turns')}


class Approval(BaseModel):
    session_id: str
    approval_id: str
    approved: StrictBool


@app.post('/approve')
async def approve(body: Approval):
    item = pending.get(body.approval_id)
    if not item or item[0] != body.session_id or item[1].done():
        raise HTTPException(409, '审核已结束或不属于此会话')
    item[1].set_result(body.approved)
    return {'ok': True}


async def wait_approval(session_id, call):
    approval_id = str(uuid4())
    future = asyncio.get_running_loop().create_future()
    pending[approval_id] = (session_id, future)
    try:
        yield {'type': 'approval_required', 'approval_id': approval_id, 'call_id': call['id'],
               'tool': call['name'], 'args': call['args']}
        try:
            approved = await asyncio.wait_for(future, float(os.getenv('APPROVAL_TIMEOUT_SECONDS', '120')))
            reason = '用户已批准' if approved else '用户拒绝了该操作'
        except asyncio.TimeoutError:
            approved, reason = False, '审核超时，已自动拒绝'
        yield {'type': 'approval_result', 'approval_id': approval_id, 'approved': approved, 'content': reason}
    finally:
        pending.pop(approval_id, None)
        if not future.done():
            future.cancel()


def encode(event):
    return f'data: {json.dumps(event, ensure_ascii=False)}\n\n'


@app.get('/chat')
async def chat(session_id: str, request_id: str = Query(min_length=1, max_length=100),
               message: str = Query(min_length=1, max_length=2000)):
    if not message.strip():
        raise HTTPException(422, '请输入问题')
    data = store.read(session_id)
    if data is None:
        raise HTTPException(404, '会话不存在')
    if session_id in active:
        raise HTTPException(409, '此会话正在生成回复')
    if any(t['id'] == request_id for t in data['turns']):
        raise HTTPException(409, '请求已完成，请读取会话历史')
    active.add(session_id)

    async def stream():
        events = []
        queue = asyncio.Queue()

        async def produce():
            try:
                async for event in react_agent(session_id, message, data['messages'], wait_approval):
                    events.append(event)
                    await queue.put(event)
                turns = data['turns'] + [{'id': request_id, 'user': message, 'events': events}]
                store.save(session_id, message[:24] if not data['turns'] else data['title'], data['messages'], turns)
                await queue.put({'type': 'done'})
            except Exception as exc:
                logging.exception('Agent run failed')
                await queue.put({'type': 'error', 'content': str(exc) if isinstance(exc, ValueError) else '模型服务请求失败，请检查后端日志与模型配置后重试。'})

        task = asyncio.create_task(produce())
        try:
            yield ': connected\n\n'
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), 15)
                except asyncio.TimeoutError:
                    yield ': heartbeat\n\n'
                    continue
                yield encode(event)
                if event['type'] in ('done', 'error'):
                    break
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            active.discard(session_id)

    return StreamingResponse(stream(), media_type='text/event-stream',
                             headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


static = Path(__file__).with_name('static')
if static.is_dir():
    app.mount('/', StaticFiles(directory=static, html=True), name='frontend')
