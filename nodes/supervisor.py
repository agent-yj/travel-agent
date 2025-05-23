from typing import Literal, TypedDict, List

from langgraph.constants import END
from langgraph.graph import MessagesState
from langgraph.types import Command

from prompts import supervisor_system_prompt


class Router(TypedDict):
    """The agent to route to next. If no further action is needed, route to FINISH."""
    next: List[Literal["web_searcher", "notion_assistant", "calendar_assistant", "chat_assistant", "FINISH"]]


def create_supervisor_node(llm):
    def supervisor_node(state: MessagesState) -> Command[
        Literal["web_searcher", "notion_assistant", "calendar_assistant", "chat_assistant", "__end__"]
    ]:
        messages = [{"role": "system", "content": supervisor_system_prompt}] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)

        nexts = response["next"]
        next_agent = nexts.pop(0)
        print(f"next agent: {next_agent}, remaining: {nexts}")

        if next_agent == "FINISH":
            goto = END
        else:
            goto = next_agent

        return Command(goto=goto)

    return supervisor_node

