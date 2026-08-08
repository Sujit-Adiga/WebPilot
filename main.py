import asyncio
from agent.agent import BrowserAgent
from agent.planner import Planner
from browser.controller import BrowserController
from browser.executor import ActionExecutor
import os
from pathlib import Path


def load_gemini_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with env_path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip()

    raise EnvironmentError(
        "GEMINI_API_KEY is not set. Add it to your environment or to a .env file in the project root."
    )


async def main():

    browser = BrowserController()

    planner = Planner(load_gemini_api_key())

    executor = ActionExecutor(browser)

    agent = BrowserAgent(
        planner,
        executor,
        browser
    )

    await browser.open()

    try:
        await agent.run(
            "Go to quotes.toscrape.com and find the quote "
            "written by Albert Einstein. Extract the text of the quote."
        )
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())