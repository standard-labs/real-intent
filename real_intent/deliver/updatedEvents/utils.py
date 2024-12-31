from anthropic.types.beta import BetaTextBlockParam, BetaImageBlockParam, BetaToolResultBlockParam
from scrapybara.anthropic import ToolResult
from typing import Any, Literal
from scrapybara.anthropic import ToolResult, CLIResult
from scrapybara.anthropic.base import BaseAnthropicTool, ToolError
from playwright.async_api import async_playwright
import base64

class ToolCollection:
    """A collection of anthropic-defined tools."""
    def __init__(self, *tools):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(self) -> list:
        return [tool.to_params() for tool in self.tools]

    async def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        tool = self.tool_map.get(name)
        if not tool:
            return None
        try:
            r = await tool(**tool_input)
            return r
        except Exception as e:
            print(f"Error running tool {name}: {e}")
            return None


def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> BetaToolResultBlockParam:
    tool_result_content: list[BetaTextBlockParam | BetaImageBlockParam] | str = []
    is_error = False
    if result.error:
        is_error = True
        tool_result_content = result.error
    else:
        if result.output:
            tool_result_content.append({
                "type": "text",
                "text": result.output,
            })
        if result.base64_image:
            tool_result_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,
                },
            })
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }


class SearchTool(BaseAnthropicTool):
    """ Custom tool used to search for a query on Google. Needed to create this as Claude won't correctly target and search for queries. """

    api_type: Literal["custom"] = "custom"
    name: Literal["search"] = "search"
    
    def __init__(self, instance):
        self.instance = instance
        super().__init__()

    def to_params(self) -> dict:
        return {
            "name": self.name,
            "type": self.api_type,
            "input_schema":{
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to enter in the Google's search bar.",
                    },
                },
                "required": ["query"],
            }
        }

    async def __call__(self, **kwargs: Any) -> Any:
        query = kwargs.get("query")
        
        if not query:
            return {"error": "Query parameter is required."}

        return await self.perform_search(query)

    async def perform_search(self, query: str):
        try:
            url = f"https://www.google.com/search?q={query}"
            cdp_url = self.instance.browser.start().cdp_url
            async with async_playwright() as playwright:
                browser = await playwright.chromium.connect_over_cdp(cdp_url)
                page = await browser.new_page()
                await page.goto(url)
                await page.wait_for_load_state("load")    
                result = {"output": f"Successfully searched for {query}."}
                ss = await page.screenshot(full_page=True)      # important, this screenshot is the only way Claude can see the results, the page closes instantly
                result['base64_image'] = base64.b64encode(ss).decode("utf-8")

            return CLIResult(
                output=result.get("output") if result else "",
                error=result.get("error") if result else None,
                base64_image=result.get("base64_image") if result else None,
                system=result.get("system") if result else None,
            )
        except Exception as e:
            raise ToolError(str(e)) from None

