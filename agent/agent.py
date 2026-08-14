from browser.actions import BrowserAction
from agent.memory import ActionRecord


class BrowserAgent:

    def __init__(
        self,
        planner,
        executor,
        browser,
        max_retries: int = 2,
    ):
        self.planner = planner
        self.executor = executor
        self.browser = browser
        self.max_retries = max_retries

        self.history: list[ActionRecord] = []

    async def run(
        self,
        goal: str,
        max_steps: int = 15,
    ):

        self.history = []

        previous_action = None
        repeat_count = 0

        total_failures = 0
        total_retries = 0
        verification_passed = False

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
                self.history,
            )

            # --------------------------------------------------
            # 3. Detect repeated actions
            # --------------------------------------------------

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

            # --------------------------------------------------
            # 4. Create action record
            # --------------------------------------------------

            record = ActionRecord(
                action=action,
                step=step + 1,
            )

            # --------------------------------------------------
            # 5. Execute action
            # --------------------------------------------------

            try:

                result = await self.executor.execute(action)

                # Store successful result
                if isinstance(result, dict):

                    record.result = result.get(
                        "text",
                        result.get("status"),
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
                # 6. Handle DONE
                # --------------------------------------------------

                if (
                    isinstance(result, dict)
                    and result.get("status") == "DONE"
                ):

                    verification_passed = result.get(
                        "verification",
                        False,
                    )

                    if verification_passed:
                        print("Verification: PASSED")
                    else:
                        print("Verification: NOT CONFIRMED")

                    print("Goal completed.")

                    return {
                        "success": True,
                        "steps": step + 1,
                        "result": result.get("text"),
                        "history": self.history,
                        "failures": total_failures,
                        "retries": total_retries,
                        "replans": total_retries,
                        "verification_passed": verification_passed,
                    }

            except Exception as exc:

                # --------------------------------------------------
                # 7. Record failure
                # --------------------------------------------------

                total_failures += 1
                total_retries += 1

                record.result = "failure"
                record.error = str(exc)

                self.history.append(record)

                print(
                    f"Action failed: {record.error}"
                )

                # --------------------------------------------------
                # 8. Enforce retry bound
                # --------------------------------------------------

                if total_retries > self.max_retries:

                    print(
                        "Maximum retries exceeded."
                    )

                    return {
                        "success": False,
                        "steps": step + 1,
                        "result": None,
                        "history": self.history,
                        "failures": total_failures,
                        "retries": total_retries,
                        "replans": total_retries - 1,
                        "verification_passed": False,
                    }

                # --------------------------------------------------
                # 9. Continue loop
                #
                # The next iteration will:
                #
                # inspect state
                #      ↓
                # planner sees history
                #      ↓
                # chooses new action
                #
                # This is the replanning loop.
                # --------------------------------------------------

                print(
                    "Replanning after action failure."
                )

                continue

        # ------------------------------------------------------
        # Maximum steps reached
        # ------------------------------------------------------

        return {
            "success": False,
            "steps": max_steps,
            "result": None,
            "history": self.history,
            "failures": total_failures,
            "retries": total_retries,
            "replans": total_retries,
            "verification_passed": verification_passed,
        }