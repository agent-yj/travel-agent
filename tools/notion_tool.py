import json
import os
from typing import Annotated, Type

import requests
from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv()
NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_PARENT_PAGE_ID = os.environ["NOTION_PARENT_PAGE_ID"]

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


@tool
async def create_notion_page(
        title: Annotated[str, "생성할 페이지의 타이틀"],
        content: Annotated[str, "생성할 페이지의 내용"]
) -> str:
    """Create Notion Page with title, content."""
    data = {
        "parent": {"page_id": f"{NOTION_PARENT_PAGE_ID}"},
        "properties": {
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))
    return res.json()['url']


class CreatePageInput(BaseModel):
    title: str = Field(..., description="생성할 페이지의 타이틀")
    content: str = Field(..., description="생성할 페이지의 내용")


class CreatePageTool(BaseTool):
    """설정된 Parent Page 아래에 노션 페이지를 생성하는 툴"""

    name: str = "create_page"
    description: str = (
        "Use this tool to create Notion Page."
        "The input must include the title, content."
        "Return value is page url link created."
    )
    args_schema: Type[CreatePageInput] = CreatePageInput

    def _run(self, title: str, content: str, **kwargs) -> str:
        import asyncio
        return asyncio.run(self._arun(title=title, content=content))

    async def _arun(self, title: str, content: str, **kwargs) -> str:
        """Create Notion Page with title, content."""

        data = {
            "parent": {"page_id": f"{NOTION_PARENT_PAGE_ID}"},
            "properties": {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]
        }

        res = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))
        return res.json()['url']


