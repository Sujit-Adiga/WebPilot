import asyncio

from agent.agent import BrowserAgent
from agent.planner import Planner
from browser.controller import BrowserController
from browser.executor import ActionExecutor


API_KEY = "YOUR_GEMINI_API_KEY"


async def main():

    browser = BrowserController()

    planner = Planner(API_KEY)

    executor = ActionExecutor(
        browser
    )

    agent = BrowserAgent(
        planner=planner,
        executor=executor,
        browser=browser,
        max_retries=2
    )

    await browser.open()

    try:

        result = await agent.run(
            goal=(
                "Go to quotes.toscrape.com "
                "and extract the quote written "
                "by Albert Einstein."
            ),
            max_steps=10
        )

        print("\nFinal result:")
        print(result)

    finally:

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())