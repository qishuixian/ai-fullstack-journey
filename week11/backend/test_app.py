"""不消耗 API 额度：用分片模型验证真实 ReAct 循环和 HTTP/SSE 协议。"""
import asyncio
import json
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk
import agent
import main
import store


class FakeModel:
    def __init__(self, name=None, args=None):
        self.name, self.args, self.round = name, args, 0

    async def astream(self, messages):
        self.round += 1
        if self.name and self.round == 1:
            raw = json.dumps(self.args or {})
            yield AIMessageChunk(content='', tool_call_chunks=[{'name': self.name, 'args': raw[:2], 'id': 'call-1', 'index': 0}])
            yield AIMessageChunk(content='', tool_call_chunks=[{'name': None, 'args': raw[2:], 'id': None, 'index': 0}])
        else:
            yield AIMessageChunk(content='测试')
            yield AIMessageChunk(content='完成')


class AppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = patch.object(store, 'DB_PATH', os.path.join(self.temp.name, 'test.db'))
        self.db.start()
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.sid = self.client.post('/sessions').json()['id']

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.db.stop()
        self.temp.cleanup()

    def chat(self, request_id='one'):
        return self.client.get('/chat', params={'session_id': self.sid, 'request_id': request_id, 'message': '测试任务'})

    def events(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/event-stream', response.headers['content-type'])
        return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]

    def test_chunk_merge_persistence_isolation_and_dedup(self):
        with patch.object(agent, 'create_model', return_value=FakeModel('calculator', {'a': 12, 'b': 8})):
            events = self.events(self.chat())
        self.assertEqual(next(e['content'] for e in events if e['type'] == 'tool_result'), '96')
        self.assertEqual(events[-1]['type'], 'done')
        self.assertEqual(len(store.read(self.sid)['turns']), 1)
        self.assertEqual(self.chat().status_code, 409)
        other = self.client.post('/sessions').json()['id']
        self.assertEqual(self.client.get(f'/sessions/{other}').json()['turns'], [])

    def test_approval_accept_and_reject(self):
        for allowed in (True, False):
            with self.subTest(allowed=allowed), patch.object(agent, 'create_model', return_value=FakeModel('send_email', {'to': 'demo@example.com', 'subject': '测试', 'body': '内容'})):
                with ThreadPoolExecutor() as executor:
                    run = executor.submit(self.chat, str(allowed))

                    async def find_approval():
                        for _ in range(200):
                            if main.pending:
                                return next(iter(main.pending))
                            await asyncio.sleep(.01)
                        raise AssertionError('未产生审核请求')

                    approval_id = self.client.portal.call(find_approval)
                    self.assertEqual(self.chat('busy').status_code, 409)
                    payload = {'session_id': 'wrong', 'approval_id': approval_id, 'approved': allowed}
                    self.assertEqual(self.client.post('/approve', json=payload).status_code, 409)
                    payload['session_id'] = self.sid
                    self.assertEqual(self.client.post('/approve', json=payload).status_code, 200)
                    events = self.events(run.result(timeout=5))
                    result = next(e for e in events if e['type'] == 'tool_result')
                    self.assertEqual(result['status'], 'success' if allowed else 'rejected')
                    self.assertEqual(self.client.post('/approve', json=payload).status_code, 409)
                    self.assertFalse(main.pending)

    def test_approval_timeout(self):
        with patch.dict(os.environ, {'APPROVAL_TIMEOUT_SECONDS': '.01'}), patch.object(agent, 'create_model', return_value=FakeModel('send_email', {'to': 'a', 'subject': 'b', 'body': 'c'})):
            events = self.events(self.chat())
        self.assertIn('审核超时', next(e['content'] for e in events if e['type'] == 'approval_result'))
        self.assertFalse(main.pending)

    def test_tool_timeout(self):
        with patch.dict(os.environ, {'TOOL_TIMEOUT_SECONDS': '.01'}), patch.object(agent, 'create_model', return_value=FakeModel('slow_tool')):
            events = self.events(self.chat())
        self.assertEqual(next(e['status'] for e in events if e['type'] == 'tool_result'), 'timeout')

    def test_failure_rolls_back_and_releases_session(self):
        with patch.object(agent, 'create_model', side_effect=ValueError('missing key')):
            self.assertEqual(self.events(self.chat())[-1]['type'], 'error')
        self.assertEqual(store.read(self.sid)['messages'], [])
        self.assertNotIn(self.sid, main.active)
        with patch.object(agent, 'create_model', return_value=FakeModel()):
            self.assertEqual(self.events(self.chat())[-1]['type'], 'done')

    def test_cancel_cleans_up_pending_approval(self):
        async def check():
            messages = []
            async def consume():
                async for _ in agent.react_agent(self.sid, 'test', messages, main.wait_approval,
                                                FakeModel('send_email', {'to': 'a', 'subject': 'b', 'body': 'c'})):
                    pass
            task = asyncio.create_task(consume())
            for _ in range(100):
                if main.pending:
                    break
                await asyncio.sleep(.01)
            self.assertTrue(main.pending)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            self.assertFalse(main.pending)
        asyncio.run(check())


if __name__ == '__main__':
    unittest.main()
