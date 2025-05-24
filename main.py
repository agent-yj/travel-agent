import asyncio
import os
import logging

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, START, StateGraph

from nodes.node_factory import create_node
from nodes.supervisor import create_supervisor_node
from prompts import chat_prompt, notion_prompt, web_search_prompt
from prompts.calendar import calendar_prompt
from tools import web_search_tools, notion_tools, calendar_tools

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

OPENAI_MODEL = os.environ["OPENAI_MODEL"]
GOOGLE_AI_MODEL = os.environ["GOOGLE_AI_MODEL"]

llm_openai = ChatOpenAI(model_name=OPENAI_MODEL, temperature=0.1)
llm_google_ai = ChatGoogleGenerativeAI(model=GOOGLE_AI_MODEL)

supervisor_node = create_supervisor_node(llm_openai)

web_search_node = create_node(
    name="web_searcher",
    llm=llm_openai,
    tools=web_search_tools,
    system_message=web_search_prompt
)

notion_node = create_node(
    name="notion_assistant",
    llm=llm_google_ai,
    tools=notion_tools,
    system_message=notion_prompt
)

calendar_node = create_node(
    name="calendar_assistant",
    llm=llm_openai,
    tools=calendar_tools,
    system_message=calendar_prompt
)

chat_node = create_node(
    name="chat_assistant",
    llm=llm_google_ai,
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

graph = builder.compile()

config = {"configurable": {"thread_id": "1"}}


async def process_user_message():
    state = {"messages": st.session_state.message_objects}

    async for event in graph.astream(state, config=config):
        for node_name, value in event.items():
            logging.info(f"value: {value}")

            if value is None:
                continue

            latest = value["messages"][-1]
            if latest:
                st.session_state.message_objects.append(latest)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": latest.content
                })

                with st.chat_message("assistant"):
                    st.markdown(latest.content)


def main():
    st.set_page_config(page_title="여행 에이전트", page_icon="✈️")

    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("message_objects", [])

    st.title("여행 에이전트")
    st.caption("여행 계획을 세워드립니다!")

    # 기존 대화 출력
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # 사용자 입력
    user_input = st.chat_input("대화를 입력해주세요!")

    if user_input:
        # 입력을 세션에 저장
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.message_objects.append(HumanMessage(content=user_input))

        with st.chat_message("user"):
            st.markdown(user_input)

        # 응답 처리
        with st.spinner("에이전트가 응답을 생성중입니다."):
            loop = asyncio.new_event_loop()

            try:
                asyncio.set_event_loop(loop)
                loop.run_until_complete(process_user_message())
            except Exception as e:
                st.error(f"에이전트 실행 중 오류가 발생했습니다: {str(e)}")

            loop.close()

        st.rerun()


if __name__ == "__main__":
    main()
