from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper, CalendarToolkit

from tools.notion_tool import CreatePageTool

search = GoogleSearchAPIWrapper()
web_search_tools = [
    Tool(
        name="google_search",
        description="Provides up-to-date information in response to user requests using Google Search.",
        func=search.run,
    )
]
notion_tools = [CreatePageTool()]
calendar_toolkit = CalendarToolkit()
calendar_tools = calendar_toolkit.get_tools()
