from typing import Literal, TypedDict
from langgraph.constants import END
from langgraph.graph import MessagesState
from langgraph.types import Command
from prompts import supervisor_system_prompt


class Router(TypedDict):
    """The agent to route to next. If no further action is needed, route to FINISH."""
    next: Literal["web_searcher", "notion_assistant", "calendar_assistant", "chat_assistant", "FINISH"]


def create_supervisor_node(llm):
    def supervisor_node(state: MessagesState) -> Command[
        Literal["web_searcher", "notion_assistant", "calendar_assistant", "chat_assistant", "__end__"]
    ]:
        messages = [{"role": "system", "content": supervisor_system_prompt}] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)

        goto = response["next"]
        print(f"Next Agent: {goto}")

        if goto == "FINISH":
            goto = END

        return Command(goto=goto)

    return supervisor_node
