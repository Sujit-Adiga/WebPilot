import argparse
import asyncio
import time

from agent.agent import BrowserAgent
from agent.planner import Planner
from browser.controller import BrowserController
from browser.executor import ActionExecutor


TASKS = [
    {
        "name": "Einstein quote",
        "goal": (
            "Go to quotes.toscrape.com and find the quote "
            "written by Albert Einstein. Extract the text of the quote."
        ),
    },
    {
        "name": "Oscar Wilde quote",
        "goal": (
            "Go to quotes.toscrape.com and find the quote "
            "written by Oscar Wilde. Extract the text of the quote."
        ),
    },
    {
        "name": "George Bernard Shaw quote",
        "goal": (
            "Go to quotes.toscrape.com and find the quote "
            "written by George Bernard Shaw. Extract the text of the quote."
        ),
    },
    {
        "name": "Navigate to login",
        "goal": (
            "Go to quotes.toscrape.com and navigate to the login page."
        ),
    },
    {
        "name": "Find tags",
        "goal": (
            "Go to quotes.toscrape.com and find the tags associated "
            "with the quote written by Albert Einstein."
        ),
    },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run WebPilot benchmark tasks."
    )

    parser.add_argument(
        "--task",
        type=int,
        help="Run only the specified task number (1-based).",
    )

    return parser.parse_args()


async def run_task(task, api_key):

    print(f"\n[{task['name']}]")
    print("-" * 60)

    browser = BrowserController()
    planner = Planner(api_key)
    executor = ActionExecutor(browser)
    verifier = None

    agent = BrowserAgent(
        planner=planner,
        executor=executor,
        browser=browser,
        verifier=verifier,
        max_retries=2,
    )

    start = time.perf_counter()

    try:
        await browser.open()

        result = await agent.run(
            task["goal"]
        )

        elapsed = time.perf_counter() - start

        return {
            "name": task["name"],
            "success": result["success"],
            "steps": result["steps"],
            "time": elapsed,
            "result": result.get("result"),
            "history": result.get("history", []),
        }

    except Exception as exc:

        elapsed = time.perf_counter() - start

        return {
            "name": task["name"],
            "success": False,
            "steps": 0,
            "time": elapsed,
            "result": None,
            "error": str(exc),
            "history": [],
        }

    finally:
        await browser.close()


async def main():

    args = parse_args()

    api_key = load_gemini_api_key()

    if args.task is not None:

        if args.task < 1 or args.task > len(TASKS):
            raise ValueError(
                f"Task must be between 1 and {len(TASKS)}."
            )

        tasks = [TASKS[args.task - 1]]

    else:
        tasks = TASKS

    print("=" * 60)
    print("WebPilot Benchmark")
    print("=" * 60)

    results = []

    for i, task in enumerate(tasks, 1):

        print(
            f"\n[{i}/{len(tasks)}] {task['name']}"
        )

        result = await run_task(
            task,
            api_key
        )

        results.append(result)

        if result["success"]:
            print("  ✓ SUCCESS")
        else:
            print("  ✗ FAILED")

            if "error" in result:
                print(
                    f"  Error: {result['error']}"
                )

        print(
            f"  Steps: {result['steps']}"
        )

        print(
            f"  Time: {result['time']:.2f}s"
        )

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    successful = sum(
        r["success"] for r in results
    )

    total = len(results)

    print(
        f"Total tasks:        {total}"
    )

    print(
        f"Successful tasks:   {successful}"
    )

    print(
        f"Failed tasks:       {total - successful}"
    )

    print(
        f"Completion rate:    "
        f"{successful / total * 100:.1f}%"
    )

    print("\nPer-task results:")

    for result in results:

        status = (
            "PASS"
            if result["success"]
            else "FAIL"
        )

        print(
            f"{status} | "
            f"{result['name']:<30} | "
            f"{result['steps']:2d} steps | "
            f"{result['time']:.2f}s"
        )


def load_gemini_api_key() -> str:
    import os
    from pathlib import Path

    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parents[1] / ".env"

    if env_path.exists():

        for line in env_path.read_text().splitlines():

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError(
        "GEMINI_API_KEY not found."
    )


if __name__ == "__main__":
    asyncio.run(main())