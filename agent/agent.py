from browser.actions import BrowserAction
from agent.memory import ActionRecord


class BrowserAgent:

    def __init__(
        self,
        planner,
        executor,
        browser,
        max_retries: int = 2
    ):
        self.planner = planner
        self.executor = executor
        self.browser = browser

        self.history: list[ActionRecord] = []

        # Maximum number of consecutive failures allowed
        self.max_retries = max_retries

    async def run(
        self,
        goal: str,
        max_steps: int = 15
    ):

        previous_action = None
        repeat_count = 0
        consecutive_failures = 0

        for step in range(max_steps):

            print(f"\n--- Step {step + 1} ---")

            # -------------------------------------------------
            # 1. OBSERVE
            # -------------------------------------------------

            state = await self.browser.inspect_page()

            # -------------------------------------------------
            # 2. PLAN
            # -------------------------------------------------

            action = self.planner.plan_next_action(
                goal,
                state,
                self.history
            )

            print(f"Action: {action}")

            # -------------------------------------------------
            # 3. DETECT REPETITION
            # -------------------------------------------------

            if action == previous_action:
                repeat_count += 1
            else:
                repeat_count = 0

            previous_action = action

            if repeat_count >= 2:
                print("Planner is repeating the same action.")

                self.history.append(
                    ActionRecord(
                        action=action,
                        result="failure",
                        error="Repeated action detected"
                    )
                )

                # Give planner another chance with updated history
                continue

            # -------------------------------------------------
            # 4. EXECUTE
            # -------------------------------------------------

            record = ActionRecord(action=action)

            try:

                result = await self.executor.execute(action)

                record.result = (
                    str(result)
                    if result is not None
                    else "success"
                )

                self.history.append(record)

                print(f"Result: {record.result}")

                # Successful action resets failure counter
                consecutive_failures = 0

                # -------------------------------------------------
                # 5. GOAL COMPLETION
                # -------------------------------------------------

                if result == "DONE":

                    print("Goal completed.")

                    return {
                        "success": True,
                        "steps": step + 1,
                        "history": self.history
                    }

            except Exception as exc:

                consecutive_failures += 1

                record.result = "failure"
                record.error = str(exc)

                self.history.append(record)

                print(f"Action failed: {record.error}")

                # -------------------------------------------------
                # BOUNDED RETRIES
                # -------------------------------------------------

                if consecutive_failures >= self.max_retries:

                    print(
                        f"Maximum retries ({self.max_retries}) "
                        "reached."
                    )

                    return {
                        "success": False,
                        "steps": step + 1,
                        "history": self.history,
                        "error": "Maximum retries exceeded"
                    }

                # -------------------------------------------------
                # FAILURE REPLANNING
                # -------------------------------------------------

                print(
                    "Replanning from updated browser state..."
                )

                continue

        print("Maximum number of steps reached.")

        return {
            "success": False,
            "steps": max_steps,
            "history": self.history,
            "error": "Maximum steps exceeded"
        }