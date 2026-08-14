import asyncio
import time

from agent.agent import BrowserAgent
from agent.deterministic_planner import (
    DeterministicPlanner,
    AlwaysFailPlanner,
)
from agent.verifier import GoalVerifier
from browser.controller import BrowserController
from browser.executor import ActionExecutor
from benchmark.tasks import TASKS


def get_planner(task):

    if task.task_type == "bounded_retry":

        return AlwaysFailPlanner()

    if task.task_type == "failure_recovery":

        return DeterministicPlanner(
            target_author="Albert Einstein",
            failure_mode="invalid_element",
        )

    if "Oscar Wilde" in task.goal:

        return DeterministicPlanner(
            target_author="Oscar Wilde"
        )

    if "George Bernard Shaw" in task.goal:

        return DeterministicPlanner(
            target_author="George Bernard Shaw"
        )

    return DeterministicPlanner(
        target_author="Albert Einstein"
    )


async def run_task(task):

    print("\n" + "=" * 60)
    print(f"TASK — {task.name}")
    print("=" * 60)

    browser = BrowserController()

    executor = ActionExecutor(browser)

    planner = get_planner(task)

    agent = BrowserAgent(
        planner=planner,
        executor=executor,
        browser=browser,
        verifier=GoalVerifier(),
        max_retries=2,
    )

    await browser.open()

    start_time = time.perf_counter()

    try:

        result = await agent.run(
            task.goal,
            max_steps=10,
        )

        elapsed = time.perf_counter() - start_time

        result["time"] = elapsed

        print("\nTEST RESULT")
        print("-" * 60)

        print(f"Success:      {result['success']}")
        print(f"Steps:        {result['steps']}")
        print(f"Failures:     {result['failures']}")
        print(f"Retries:      {result['retries']}")
        print(f"Replans:      {result['replans']}")
        print(f"Verification: {result['verification']}")
        print(f"Time:         {elapsed:.2f}s")

        if result.get("failure_type"):
            print(
                f"Failure type: {result['failure_type']}"
            )

        return result

    finally:

        await browser.close()


def print_summary(results):

    print("\n")
    print("=" * 60)
    print("DETERMINISTIC BENCHMARK SUMMARY")
    print("=" * 60)

    total = len(results)

    # Normal successful tasks
    successful = sum(
        1
        for r in results
        if r["success"]
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
        1
        for r in results
        if r["verification"]
    )

    avg_steps = (
        sum(r["steps"] for r in results) / total
        if total
        else 0
    )

    avg_time = (
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
    print(
        f"Completion rate:    {completion_rate:.1f}%"
    )
    print(f"Verified tasks:     {verified}")
    print(f"Total failures:     {total_failures}")
    print(f"Total retries:      {total_retries}")
    print(f"Total replans:      {total_replans}")
    print(f"Average steps:      {avg_steps:.2f}")
    print(f"Average time:       {avg_time:.2f}s")

    # --------------------------------------------------
    # Bounded retry validation
    # --------------------------------------------------

    bounded_tasks = [
        r
        for r, task in zip(results, TASKS)
        if task.task_type == "bounded_retry"
    ]

    bounded_passed = sum(
        1
        for r in bounded_tasks
        if (
            r["failure_type"] == "max_retries"
            and r["retries"] == 2
        )
    )

    print(
        f"Bounded retry tests: "
        f"{bounded_passed}/{len(bounded_tasks)} passed"
    )

    # --------------------------------------------------
    # Failure recovery validation
    # --------------------------------------------------

    recovery_tasks = [
        r
        for r, task in zip(results, TASKS)
        if task.task_type == "failure_recovery"
    ]

    recovery_passed = sum(
        1
        for r in recovery_tasks
        if (
            r["success"]
            and r["failures"] >= 1
            and r["replans"] >= 1
        )
    )

    print(
        f"Failure recovery:   "
        f"{recovery_passed}/{len(recovery_tasks)} passed"
    )

    print("=" * 60)

    print("\nPer-task results:")

    for task, result in zip(TASKS, results):
        status = (
            "PASS"
            if result["success"]
            else "FAIL"
        )

        print(
            f"{status:4} | "
            f"{task.name:35} | "
            f"{result['steps']:2} steps | "
            f"{result['failures']} failures | "
            f"{result['retries']} retries"
        )


async def main():

    results = []

    for task in TASKS:

        result = await run_task(task)

        results.append(result)

    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())