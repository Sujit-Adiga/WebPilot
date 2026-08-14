import asyncio
import os
from pathlib import Path

from agent.agent import BrowserAgent
from agent.planner import Planner
from browser.controller import BrowserController
from browser.executor import ActionExecutor

from agent.verifier import GoalVerifier


def load_gemini_api_key() -> str:
    """
    Load Gemini API key from environment or local .env file.
    """

    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key:
        return api_key

    env_path = Path(__file__).parent / ".env"

    if env_path.exists():

        for line in env_path.read_text().splitlines():

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError(
        "GEMINI_API_KEY not found. "
        "Set it in the environment or .env file."
    )


async def main():

    api_key = load_gemini_api_key()

    browser = BrowserController()

    planner = Planner(api_key)

    executor = ActionExecutor(browser)

    agent = BrowserAgent(
        planner=planner,
        executor=executor,
        browser=browser,
        verifier=GoalVerifier()
    )

    await browser.open()

    try:

        result = await agent.run(
            "Go to quotes.toscrape.com and find the quote "
            "written by Albert Einstein. Extract the text of the quote.",
            max_steps=10,
            max_retries=2,
            max_planner_retries=1
        )

        print("\nFinal result:")
        print(result["result"])

    finally:

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())