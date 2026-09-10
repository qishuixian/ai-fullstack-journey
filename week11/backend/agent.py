"""Week 10 Day 7 react_agent 的异步版本；保留手写循环与 chunk 合并。"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).with_name('.env'))
MAX_STEPS = 5


@tool
async def get_weather(city: str) -> str:
    """查询城市天气（教学模拟数据，不是实时天气）。"""
    await asyncio.sleep(0.5)
    return {'北京': '晴，25度', '上海': '多云，28度', '广州': '雷阵雨，30度'}.get(city, f'未知城市：{city}')


@tool
async def calculator(a: int, b: int) -> int:
    """计算两个整数的乘积。"""
    return a * b


@tool
async def slow_tool() -> str:
    """模拟耗时十秒的外部工具，用于测试超时降级。"""
    await asyncio.sleep(10)
    return '慢工具执行成功'


@tool
async def send_email(to: str, subject: str, body: str) -> str:
    """模拟发送邮件，需要人工审核，不会真正发送邮件。"""
    return f'模拟邮件发送成功：收件人 {to}，主题 {subject}（未发送真实邮件）'


tools = [get_weather, calculator, slow_tool, send_email]
tool_map = {t.name: t for t in tools}


def create_model():
    if not os.getenv('DEEPSEEK_API_KEY'):
        raise ValueError('请先在 backend/.env 配置 DEEPSEEK_API_KEY')
    return ChatOpenAI(model=os.getenv('MODEL_NAME', 'deepseek-chat'),
                      api_key=os.environ['DEEPSEEK_API_KEY'],
                      base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
                      temperature=0, streaming=True, timeout=60, max_retries=1).bind_tools(tools)


async def react_agent(session_id, user_input, messages, approve, model=None):
    """yield 可序列化事件；messages 为本轮副本，仅成功时由服务原子保存。"""
    model = model if model is not None else create_model()
    if not messages:
        messages.append(SystemMessage(content='你是有帮助的助手，可调用工具。天气和邮件均为教学模拟。不要声称执行被拒绝或失败的操作。'))
    messages.append(HumanMessage(content=user_input))
    for step in range(1, MAX_STEPS + 1):
        yield {'type': 'step', 'step': step, 'content': '模型正在生成回复或选择工具'}
        full_response = None
        async for chunk in model.astream(messages):
            full_response = chunk if full_response is None else full_response + chunk
            if isinstance(chunk.content, str) and chunk.content:
                yield {'type': 'token', 'step': step, 'content': chunk.content}
        if full_response is None:
            raise ValueError('模型返回了空响应，请重试')
        if full_response.invalid_tool_calls:
            raise ValueError('模型返回了无效工具参数，请重试')
        calls = full_response.tool_calls
        messages.append(AIMessage(content=full_response.content or '', tool_calls=calls))
        if not calls:
            return
        for call in calls:
            name, args, call_id = call['name'], call['args'], call['id']
            yield {'type': 'tool_call', 'step': step, 'tool': name, 'args': args, 'call_id': call_id}
            allowed, reason = True, ''
            if name == 'send_email':
                async for event in approve(session_id, call):
                    if event['type'] == 'approval_result':
                        allowed, reason = event['approved'], event['content']
                    yield event
            status = 'success'
            if not allowed:
                result, status = reason, 'rejected'
            elif name not in tool_map:
                result, status = f'未知工具：{name}', 'error'
            else:
                try:
                    result = str(await asyncio.wait_for(tool_map[name].ainvoke(args),
                                      timeout=float(os.getenv('TOOL_TIMEOUT_SECONDS', '3'))))
                except asyncio.TimeoutError:
                    result, status = '工具暂时不可用（执行超时），请稍后再试。', 'timeout'
                except Exception as exc:
                    result, status = f'工具执行失败：{exc}', 'error'
            messages.append(ToolMessage(content=result, tool_call_id=call_id))
            yield {'type': 'tool_result', 'step': step, 'call_id': call_id, 'tool': name, 'content': result, 'status': status}
    content = '已达到最大推理轮数（5），请缩小问题范围后继续。'
    messages.append(AIMessage(content=content))
    yield {'type': 'token', 'step': MAX_STEPS, 'content': content}
