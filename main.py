import asyncio
import os
from pathlib import Path

from agent.agent import BrowserAgent
from agent.planner import Planner
from browser.controller import BrowserController
from browser.executor import ActionExecutor
from llm.groq_provider import GroqProvider


def load_groq_api_key() -> str:

    api_key = os.environ.get("GROQ_API_KEY")

    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parent / ".env"

    if env_path.exists():

        for line in env_path.read_text().splitlines():

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError(
        "GROQ_API_KEY not found."
    )


async def main():

    api_key = load_groq_api_key()

    llm = GroqProvider(
        api_key=api_key,
        model="openai/gpt-oss-20b",
    )

    browser = BrowserController()

    planner = Planner(
        llm=llm,
    )

    executor = ActionExecutor(browser)

    agent = BrowserAgent(
        planner=planner,
        executor=executor,
        browser=browser,
        verifier=None,
        max_retries=2,
    )

    await browser.open()

    try:

        result = await agent.run(
            "Go to quotes.toscrape.com and find the quote "
            "written by Albert Einstein. Extract the text "
            "of the quote."
        )

        print("\nFinal result:")
        print(result.get("result"))

    finally:

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())