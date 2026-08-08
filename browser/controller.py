from typing import Optional
from playwright.async_api import Locator, async_playwright

from agent.state import BrowserState, PageElement
from browser.actions import BrowserAction

class BrowserController:

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.element_map: dict[int, Locator] = {}
        self.visited_urls = []

    def _require_page(self):
        if self.page is None:
            raise RuntimeError("Browser is not open.")

        return self.page

    def has_element(self, element_id: int) -> bool:
        return element_id in self.element_map

    async def open(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def goto(self, url: str):
        page = self._require_page()
        await page.goto(url)
        actual_url = page.url
        if actual_url not in self.visited_urls:
            self.visited_urls.append(actual_url)
        print(f"Navigated to {actual_url}")

    async def get_title(self) -> str:
        page = self._require_page()
        return await page.title()

    async def click(self, element_id: int):
        locator = self.element_map[element_id]
        await locator.click()

    async def fill(self, element_id: int, text: str):
        locator = self.element_map[element_id]
        await locator.fill(text)

    async def extract_text(self, element_id: int) -> Optional[str]:
        locator = self.element_map[element_id]
        return await locator.text_content()

    async def wait(self, element_id: int):
        locator = self.element_map[element_id]
        await locator.wait_for()

    async def press(self, element_id: int, key: str):
        locator = self.element_map[element_id]
        await locator.press(key)

    async def inspect_page(self) -> BrowserState:
        page = self._require_page()
        locator = page.locator(
            "button, input, textarea, select, a[href], "
            "article, blockquote, p, span, small"
        )
        count = await locator.count()
        self.element_map.clear()
        elements = []
        element_id = 0

        for i in range(count):
            current = locator.nth(i)

            tag = await current.evaluate(
                "el => el.tagName.toLowerCase()"
            )

            text = (await current.text_content()) or ""
            if not text:
                text = (await current.get_attribute("value")) or ""

            placeholder = await current.get_attribute("placeholder")

            name = await current.get_attribute("name")

            aria_label = await current.get_attribute("aria-label")

            input_type = await current.get_attribute("type")
            if input_type == "hidden":
                continue

            value = None
            if tag in {"input", "textarea", "select"}:
                try:
                    value = await current.input_value()
                except:
                    value = None

            self.element_map[element_id] = current
            
            elements.append(
                PageElement(
                    id=element_id,
                    tag=tag,
                    text=text.strip(),
                    name=name,
                    placeholder=placeholder,
                    aria_label=aria_label,
                    type=input_type,
                    value=value
                )
            )
            element_id += 1

        return BrowserState(
            url=page.url,
            title=await page.title(),
            elements=elements,
            visited_urls=self.visited_urls.copy()
        )

    async def close(self):
        if self.browser is not None:
            await self.browser.close()
            
        if self.playwright is not None:
            await self.playwright.stop()

        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        