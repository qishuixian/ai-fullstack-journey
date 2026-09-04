from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph


class MyState(TypedDict):
    """共享状态，类似全局 state。"""

    input_text: str
    step_count: int
    final_output: str


def node_process_input(state: MyState) -> dict:
    """节点1：处理输入，将文本转为大写。"""
    print(f"[Node: process_input] 收到: {state['input_text']}")
    return {
        "input_text": state["input_text"].upper(),
        "step_count": state["step_count"] + 1,
    }


def node_check_length(state: MyState) -> dict:
    """节点2：判断文本长度，决定下一步。"""
    length = len(state["input_text"])
    print(f"[Node: check_length] 文本长度: {length}")
    return {
        "step_count": state["step_count"] + 1,
        "final_output": f"文本长度是 {length}",
    }


def router_after_process(state: MyState) -> Literal["check_length", "end"]:
    """如果 step_count 小于 3，继续；否则结束。"""
    if state["step_count"] < 3:
        return "check_length"
    return "end"


builder = StateGraph(MyState)

builder.add_node("process_input", node_process_input)
builder.add_node("check_length", node_check_length)

builder.set_entry_point("process_input")

builder.add_conditional_edges(
    "process_input",
    router_after_process,
    {
        "check_length": "check_length",
        "end": END,
    },
)

builder.add_edge("check_length", "process_input")

app = builder.compile()

initial_state: MyState = {
    "input_text": "Hello LangGraph!",
    "step_count": 0,
    "final_output": "",
}

print("=== 开始运行 LangGraph ===")
result = app.invoke(initial_state)
print("\n=== 最终结果 ===")
print(result)
