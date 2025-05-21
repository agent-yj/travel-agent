from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, START, StateGraph

from nodes.node_factory import create_node
from nodes.supervisor import create_supervisor_node
from prompts import chat_prompt
from tools import web_search_tools, notion_tools, calendar_tools

load_dotenv()
MODEL_GPT_4O = "gpt-4o"
llm = ChatOpenAI(model_name=MODEL_GPT_4O)

supervisor_node = create_supervisor_node(llm)

web_search_node = create_node(
    name="web_searcher",
    llm=llm,
    tools=web_search_tools
)

notion_node = create_node(
    name="notion_assistant",
    llm=llm,
    tools=notion_tools
)

calendar_node = create_node(
    name="calendar_assistant",
    llm=llm,
    tools=calendar_tools
)

chat_node = create_node(
    name="chat_assistant",
    llm=llm,
    tools=[],
    system_message=chat_prompt
)

builder = StateGraph(MessagesState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("web_searcher", web_search_node)
builder.add_node("notion_assistant", notion_node)
builder.add_node("calendar_assistant", calendar_node)
builder.add_node("chat_assistant", chat_node)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break

    for event in graph.stream({"messages": [("user", user_input)]}, config):
        for value in event.values():
            if value is None:
                continue

            latest_message = value["messages"][-1]
            if isinstance(latest_message, AIMessage):
                print("AI:", latest_message.content)
            elif isinstance(latest_message, HumanMessage):
                print(f"{latest_message.name}:", latest_message.content)
            else:
                print("Info:", latest_message.content)
