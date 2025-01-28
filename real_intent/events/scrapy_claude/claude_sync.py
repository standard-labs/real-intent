"""Synchronous implementation of tools for the Anthropic API."""

from scrapybara.client import UbuntuInstance
from scrapybara.anthropic.base import ToolResult, ToolError, CLIResult
from scrapybara.tools import Tool

from playwright.sync_api import sync_playwright

from pydantic import BaseModel, Field
from typing import Literal, Any
import base64

from real_intent.internal_logging import log


class SearchParameters(BaseModel):
    command: Literal["search_for"] = Field(
        description=(
            "The browser command to execute. Required parameters per command:\n"
            "- search_for: requires 'query'"
        )
    )
    query: str = Field(
        ..., 
        description="The search query to enter in the Google's search bar (required for search_for)"
    )


class SearchTool(Tool):
    _instance: UbuntuInstance

    def __init__(self, instance: UbuntuInstance) -> None:
        super().__init__(
            name="search",
            description="Custom tool used to search for a query on Google.",
            parameters=SearchParameters,
        )
        self._instance = instance

    def __call__(self, **kwargs: Any) -> Any:
        query = kwargs.get("query")
        if not query:
            raise ToolError("Missing required 'query' parameter.")

        return self.perform_search(query)

    def perform_search(self, query: str) -> ToolResult:
        url = f"https://www.google.com/search?q={query}"
        cdp_url = self._instance.browser.start().cdp_url
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(cdp_url)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_load_state("load")    
            result = {"output": f"Successfully searched for {query}."}
            ss = page.screenshot(full_page=True)      
            result['base64_image'] = base64.b64encode(ss).decode("utf-8")

        return CLIResult(
            output=result.get("output") if result else "",
            error=result.get("error") if result else None,
            base64_image=result.get("base64_image") if result else None,
            system=result.get("system") if result else None,
        )

