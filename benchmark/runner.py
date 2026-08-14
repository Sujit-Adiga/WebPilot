import argparse
import asyncio
import os
import time
from pathlib import Path

from agent.agent import BrowserAgent
from agent.planner import Planner
from browser.controller import BrowserController
from browser.executor import ActionExecutor
from llm.groq_provider import GroqProvider


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


def load_groq_api_key() -> str:
    """
    Load Groq API key from environment or local .env file.
    """

    api_key = os.environ.get("GROQ_API_KEY")

    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parents[1] / ".env"

    if env_path.exists():

        for line in env_path.read_text().splitlines():

            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip()

    raise RuntimeError(
        "GROQ_API_KEY not found. "
        "Set it in the environment or .env file."
    )


def parse_args():

    parser = argparse.ArgumentParser(
        description="Run WebPilot LLM benchmark tasks."
    )

    parser.add_argument(
        "--task",
        type=int,
        help="Run only one task (1-based index)."
    )

    return parser.parse_args()


async def run_task(task, api_key):

    print(f"\n[{task['name']}]")
    print("-" * 60)

    browser = BrowserController()

    llm = GroqProvider(
        api_key=api_key,
        model="openai/gpt-oss-20b",
    )

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
            "failures": result.get("failures", 0),
            "retries": result.get("retries", 0),
            "replans": result.get("replans", 0),
            "verification": result.get("verification", False),
            "failure_type": result.get("failure_type"),
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
            "failures": 0,
            "retries": 0,
            "replans": 0,
            "verification": False,
            "failure_type": "llm_error",
        }

    finally:

        await browser.close()


async def main():

    args = parse_args()

    api_key = load_groq_api_key()

    if args.task is not None:

        if args.task < 1 or args.task > len(TASKS):
            raise ValueError(
                f"Task must be between 1 and {len(TASKS)}."
            )

        tasks = [TASKS[args.task - 1]]

    else:

        tasks = TASKS

    print("=" * 60)
    print("WebPilot LLM Benchmark")
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
            f"  Steps:    {result['steps']}"
        )

        print(
            f"  Failures: {result['failures']}"
        )

        print(
            f"  Retries:  {result['retries']}"
        )

        print(
            f"  Replans:  {result['replans']}"
        )

        print(
            f"  Time:     {result['time']:.2f}s"
        )

    print("\n" + "=" * 60)
    print("LLM BENCHMARK RESULTS")
    print("=" * 60)

    total = len(results)

    successful = sum(
        r["success"]
        for r in results
    )

    total_failures = sum(
        r["failures"]
        for r in results
    )

    total_retries = sum(
        r["retries"]
        for r in results
    )

    total_replans = sum(
        r["replans"]
        for r in results
    )

    verified = sum(
        r["verification"]
        for r in results
    )

    average_steps = (
        sum(r["steps"] for r in results) / total
        if total
        else 0
    )

    average_time = (
        sum(r["time"] for r in results) / total
        if total
        else 0
    )

    completion_rate = (
        successful / total * 100
        if total
        else 0
    )

    print(f"Total tasks:        {total}")
    print(f"Successful tasks:   {successful}")
    print(f"Failed tasks:       {total - successful}")
    print(f"Completion rate:    {completion_rate:.1f}%")
    print(f"Verified tasks:     {verified}")
    print(f"Total failures:     {total_failures}")
    print(f"Total retries:      {total_retries}")
    print(f"Total replans:      {total_replans}")
    print(f"Average steps:      {average_steps:.2f}")
    print(f"Average time:       {average_time:.2f}s")

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
            f"{result['failures']} failures | "
            f"{result['retries']} retries | "
            f"{result['time']:.2f}s"
        )


if __name__ == "__main__":
    asyncio.run(main())