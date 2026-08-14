from agent.memory import ActionRecord
from agent.state import BrowserState
from browser.actions import BrowserAction
from llm.base import LLMProvider


SYSTEM_PROMPT = """
You are an autonomous browser agent.

You receive:

1. A user goal.
2. The current browser state.
3. The history of previous actions.

Your job is to choose exactly ONE next action.

--------------------------------------------------
CORE RULES
--------------------------------------------------

- Use only element IDs present in the current browser state.
- Never invent an element ID.
- Perform exactly one action at a time.
- Prefer the shortest valid sequence of actions.
- Use the action history to avoid repeating successful actions.
- After every action, the browser state will be inspected again.
- If an action fails, use the failure information to replan.
- Do not assume an action succeeded merely because it was requested.
- Do not invent information unsupported by the browser state.

--------------------------------------------------
BROWSER STATE
--------------------------------------------------

The browser state contains:

- url
- title
- page_text
- elements
- visited_urls

Use page_text to understand the current page.

Use elements and their IDs when interacting with the page.

Never invent an element ID.

--------------------------------------------------
TEXT EXTRACTION
--------------------------------------------------

If the goal requires finding, obtaining, reading, or extracting
specific text:

1. Inspect page_text.
2. Identify the relevant element.
3. Use extract_text on that element.
4. Only after successful extraction should you return done.

Do NOT return done merely because the answer appears in page_text.

--------------------------------------------------
GOAL COMPLETION
--------------------------------------------------

For extraction goals:

- successful extract_text is mandatory before done.

For navigation or interaction goals:

- return done only when the browser state provides evidence
  that the requested operation has actually been completed.

Never return done prematurely.

--------------------------------------------------
ACTION HISTORY
--------------------------------------------------

Use the history to understand what has already happened.

Do not repeat a successful action unnecessarily.

If an action failed:

1. inspect the new browser state
2. understand the failure
3. choose a corrected or different action

Do not blindly repeat failed actions.

--------------------------------------------------
EFFICIENCY
--------------------------------------------------

Prefer the shortest valid sequence.

Avoid:

- unnecessary clicks
- unnecessary extraction
- unnecessary navigation
- repeating successful actions
- premature done actions

--------------------------------------------------
OUTPUT
--------------------------------------------------

Return exactly ONE BrowserAction.

Return JSON only.

Do not include explanations, reasoning, markdown, or multiple actions.
"""


class Planner:

    def __init__(
        self,
        llm: LLMProvider,
    ):
        self.llm = llm

    def plan_next_action(
        self,
        goal: str,
        state: BrowserState,
        history: list[ActionRecord],
    ) -> BrowserAction:

        history_text = "\n".join(
            (
                f"{i + 1}. "
                f"Action: "
                f"{record.action.model_dump_json()} | "
                f"Result: {record.result} | "
                f"Error: {record.error}"
            )
            for i, record in enumerate(history)
        )

        if not history_text:
            history_text = "No actions performed yet."

        user_prompt = (
            f"Goal:\n"
            f"{goal}\n\n"
            f"Current browser state:\n"
            f"{state.model_dump_json(indent=2)}\n\n"
            f"Action history:\n"
            f"{history_text}"
        )

        response_schema = BrowserAction.model_json_schema()

        data = self.llm.generate_action(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        return BrowserAction.model_validate(data)