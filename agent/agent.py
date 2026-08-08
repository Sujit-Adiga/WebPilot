class BrowserAgent:

    def __init__(self, planner, executor, browser):
        self.planner = planner
        self.executor = executor
        self.browser = browser

    async def run(self, goal: str, max_steps: int = 15):
        previous_action = None
        repeat_count = 0
        
        for step in range(max_steps):
            print(f"\n--- Step {step + 1} ---")

            state = await self.browser.inspect_page()

            action = self.planner.plan_next_action(goal, state)

            if action == previous_action:
                repeat_count += 1
            else:
                repeat_count = 0

            previous_action = action

            if repeat_count >= 2:
                raise RuntimeError(
                    "Agent appears to be repeating the same action."
                )

            print(action)

            result = await self.executor.execute(action)

            if result == "DONE":
                print("Goal completed.")
                return

        print("Maximum number of steps reached.")