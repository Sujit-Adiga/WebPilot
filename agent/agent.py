from browser.actions import BrowserAction
from agent.memory import ActionRecord


class BrowserAgent:

    def __init__(self, planner, executor, browser):
        self.planner = planner
        self.executor = executor
        self.browser = browser
        self.history: list[ActionRecord] = []

    async def run(
        self,
        goal: str,
        max_steps: int = 15,
        max_retries: int = 3
    ):

        previous_action = None
        repeat_count = 0
        retry_count = 0

        for step in range(max_steps):

            print(f"\n--- Step {step + 1} ---")

            # 1. Inspect the current browser state
            state = await self.browser.inspect_page()

            # 2. Ask the planner for the next action
            action = self.planner.plan_next_action(
                goal,
                state,
                self.history
            )

            # 3. Detect repeated actions
            if action == previous_action:
                repeat_count += 1
            else:
                repeat_count = 0

            previous_action = action

            if repeat_count >= 2:
                raise RuntimeError(
                    "Agent appears to be repeating the same action."
                )

            print(f"Action: {action}")

            # 4. Record the action
            record = ActionRecord(
                action=action,
                step=step + 1
            )

            try:

                # 5. Execute the action
                result = await self.executor.execute(action)

                # 6. Record successful result
                if isinstance(result, dict):
                    record.result = result.get(
                        "text",
                        result.get("status")
                    )
                else:
                    record.result = (
                        str(result)
                        if result is not None
                        else "success"
                    )

                self.history.append(record)

                print(f"Result: {result}")

                # 7. Successful action → reset retry counter
                retry_count = 0

                # 8. Check whether the agent has completed the goal
                if (
                    isinstance(result, dict)
                    and result.get("status") == "DONE"
                ):
                    final_text = result.get("text")

                    print("Goal completed.")

                    return {
                        "success": True,
                        "steps": step + 1,
                        "result": final_text,
                        "history": self.history,
                    }

            except Exception as exc:

                # 9. Record the failed action
                record.result = "failure"
                record.error = str(exc)

                self.history.append(record)

                retry_count += 1

                print(f"Action failed: {record.error}")
                print(
                    f"Retry {retry_count}/{max_retries}"
                )

                # 10. Stop after bounded number of consecutive failures
                if retry_count >= max_retries:

                    print("Maximum retries exceeded.")

                    return {
                        "success": False,
                        "steps": step + 1,
                        "result": None,
                        "history": self.history,
                        "error": "Maximum retries exceeded",
                    }

                # 11. Otherwise continue:
                #     inspect → replan → execute
                continue

        # 12. Maximum total steps reached
        return {
            "success": False,
            "steps": max_steps,
            "result": None,
            "history": self.history,
            "error": "Maximum steps reached",
        }