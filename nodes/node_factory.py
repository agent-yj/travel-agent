from typing import TypedDict, Literal, Annotated, Sequence, List

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import add_messages, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


def create_agent(llm, tools, system_message=None):
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: AgentState):
        messages = [{"role": "system", "content": system_message}] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", chatbot)

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
    )
    graph_builder.add_edge("tools", "agent")
    graph_builder.set_entry_point("agent")
    return graph_builder.compile()


def create_node(name: str, llm, tools, system_message=None):
    agent_graph = create_agent(llm, tools, system_message)

    def node_fn(state: MessagesState) -> Command[Literal["supervisor"]]:
        result = agent_graph.invoke(state)
        return Command(
            update={
                "messages": [
                    HumanMessage(content=result["messages"][-1].content, name=name)
                ]
            },
            goto="supervisor"
        )

    return node_fn
