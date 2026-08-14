from browser.actions import BrowserAction
from agent.memory import ActionRecord


class BrowserAgent:

    def __init__(
        self,
        planner,
        executor,
        browser,
        verifier,
        max_retries: int = 2
    ):
        self.planner = planner
        self.executor = executor
        self.browser = browser
        self.max_retries = max_retries
        self.verifier = verifier

        self.history: list[ActionRecord] = []

    async def run(
        self,
        goal: str,
        max_steps: int = 15
    ):

        previous_action = None

        # Counts repeated successful actions.
        # Failed actions are handled separately as retries.
        repeat_count = 0

        # Whether the immediately preceding action failed.
        last_action_failed = False

        # Number of retries caused by action failures.
        retry_count = 0

        for step in range(max_steps):

            print(f"\n--- Step {step + 1} ---")

            # --------------------------------------------------
            # 1. Inspect current browser state
            # --------------------------------------------------

            state = await self.browser.inspect_page()

            # --------------------------------------------------
            # 2. Ask planner for next action
            # --------------------------------------------------

            action = self.planner.plan_next_action(
                goal,
                state,
                self.history
            )

            # --------------------------------------------------
            # 3. Detect repeated successful actions
            # --------------------------------------------------

            if (
                action == previous_action
                and not last_action_failed
            ):
                repeat_count += 1
            else:
                repeat_count = 0

            previous_action = action

            if repeat_count >= 2:
                print(
                    "Agent appears to be repeating "
                    "the same successful action."
                )

                return {
                    "success": False,
                    "steps": step + 1,
                    "result": None,
                    "history": self.history,
                    "failure_type": "repeated_action",
                    "failures": sum(
                        1
                        for record in self.history
                        if record.result == "failure"
                    ),
                    "retries": retry_count,
                    "replans": retry_count,
                    "verification": False,
                }

            print(f"Action: {action}")

            # --------------------------------------------------
            # 4. Create action record
            # --------------------------------------------------

            record = ActionRecord(
                action=action,
                step=step + 1
            )

            # --------------------------------------------------
            # 5. Execute action
            # --------------------------------------------------

            try:

                result = await self.executor.execute(action)

                # This action succeeded.
                last_action_failed = False

                # --------------------------------------------------
                # 6. Store successful result
                # --------------------------------------------------

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

                # --------------------------------------------------
                # 7. Handle successful completion
                # --------------------------------------------------

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
                        "failure_type": None,
                        "failures": sum(
                            1
                            for record in self.history
                            if record.result == "failure"
                        ),
                        "retries": retry_count,
                        "replans": retry_count,
                        "verification": True,
                    }

            # --------------------------------------------------
            # 8. Handle action failure
            # --------------------------------------------------

            except Exception as exc:

                last_action_failed = True

                retry_count += 1

                record.result = "failure"
                record.error = str(exc)

                self.history.append(record)

                print(
                    f"Action failed: {record.error}"
                )

                # --------------------------------------------------
                # 9. Enforce bounded retries
                # --------------------------------------------------

                if retry_count > self.max_retries:

                    print(
                        "Maximum retries reached."
                    )

                    return {
                        "success": False,
                        "steps": step + 1,
                        "result": None,
                        "history": self.history,
                        "failure_type": "max_retries",
                        "failures": retry_count,
                        "retries": self.max_retries,
                        "replans": self.max_retries,
                        "verification": False,
                    }

                # --------------------------------------------------
                # 10. Replan after failure
                # --------------------------------------------------

                print(
                    "Replanning after action failure."
                )

                continue

        # --------------------------------------------------
        # Maximum execution steps reached
        # --------------------------------------------------

        print(
            "Maximum number of steps reached."
        )

        return {
            "success": False,
            "steps": max_steps,
            "result": None,
            "history": self.history,
            "failure_type": "max_steps",
            "failures": sum(
                1
                for record in self.history
                if record.result == "failure"
            ),
            "retries": retry_count,
            "replans": retry_count,
            "verification": False,
        }