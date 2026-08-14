import asyncio

from agent.agent import BrowserAgent
from agent.deterministic_planner import (
    DeterministicPlanner,
    AlwaysFailPlanner,
)
from agent.verifier import GoalVerifier
from browser.controller import BrowserController
from browser.executor import ActionExecutor


GOAL = (
    "Go to quotes.toscrape.com and find the quote "
    "written by Albert Einstein. Extract the text of the quote."
)


async def run_test(name, planner):

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    browser = BrowserController()

    executor = ActionExecutor(browser)

    agent = BrowserAgent(
        planner=planner,
        executor=executor,
        browser=browser,
        verifier=GoalVerifier(),
        max_retries=2,
    )

    await browser.open()

    try:

        result = await agent.run(
            GOAL,
            max_steps=10,
        )

        print("\nTEST RESULT")
        print("-" * 60)

        print(
            f"Success:      {result['success']}"
        )

        print(
            f"Steps:        {result['steps']}"
        )

        print(
            f"Failures:     {result['failures']}"
        )

        print(
            f"Retries:      {result['retries']}"
        )

        print(
            f"Replans:      {result['replans']}"
        )

        print(
            f"Verification: {result['verification']}"
        )

        if result.get("failure_type"):
            print(
                f"Failure type: {result['failure_type']}"
            )

        return result

    finally:

        await browser.close()


async def main():

    # --------------------------------------------------
    # Test 1: Normal execution
    # --------------------------------------------------

    await run_test(
        "TEST 1 — Normal execution",
        DeterministicPlanner(),
    )

    # --------------------------------------------------
    # Test 2: One action failure + recovery
    # --------------------------------------------------

    await run_test(
        "TEST 2 — Failure recovery + replanning",
        DeterministicPlanner(
            failure_mode="invalid_element"
        ),
    )

    # --------------------------------------------------
    # Test 3: Repeated failure + bounded retries
    # --------------------------------------------------

    await run_test(
        "TEST 3 — Bounded retries",
        AlwaysFailPlanner(),
    )


if __name__ == "__main__":
    asyncio.run(main())