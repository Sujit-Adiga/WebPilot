import json

from google import genai
from google.genai import types

from agent.memory import ActionRecord
from agent.state import BrowserState
from browser.actions import BrowserAction


SYSTEM_PROMPT = """
You are an autonomous browser automation agent.

You receive:

1. A user goal.
2. The current browser state.
3. The history of previous actions and their results.

Your task is to choose EXACTLY ONE next browser action.

Core strategy:

OBSERVE -> PLAN -> EXECUTE -> VERIFY -> REPLAN

Rules:

- Use only element IDs present in the CURRENT browser state.
- Never invent an element ID.
- Perform exactly one action at a time.
- Prefer the shortest sequence of actions necessary.
- Use action history to understand what has already happened.
- Never repeat an action that already succeeded unless the current state
  clearly requires it.
- If an action failed, reconsider the strategy before trying again.
- If an element ID from a previous state is no longer present, do not use it.
- After navigation or page-changing actions, rely on the new browser state.
- Determine whether the goal has already been achieved before selecting
  another action.
- If the goal has been achieved, return:
  {"action": "done"}
- Do not use extract_text merely to verify that a click or fill succeeded.
- Use extract_text when the user's goal explicitly requires obtaining
  information from the page.

Action requirements:

- navigate -> requires url
- click -> requires element_id
- fill -> requires element_id and text
- extract_text -> requires element_id
- wait -> requires element_id
- press -> requires element_id and key
- done -> requires no element_id

Return JSON only.
"""


class Planner:

    def __init__(
        self,
        api_key: str
    ):

        self.client = genai.Client(
            api_key=api_key
        )

    def plan_next_action(
        self,
        goal: str,
        state: BrowserState,
        history: list[ActionRecord]
    ) -> BrowserAction:

        if history:

            history_text = "\n".join(
                f"{i + 1}. "
                f"Action: {record.action.model_dump_json()} | "
                f"Result: {record.result} | "
                f"Error: {record.error}"
                for i, record in enumerate(history)
            )

        else:

            history_text = (
                "No actions performed yet."
            )

        user_content = (
            f"Goal:\n{goal}\n\n"
            f"Current browser state:\n"
            f"{state.model_dump_json(indent=2)}\n\n"
            f"Action history:\n"
            f"{history_text}"
        )

        response = (
            self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=BrowserAction,
                ),
            )
        )

        response_text = response.text

        if response_text is None:

            raise ValueError(
                "Empty response from planner."
            )

        data = json.loads(
            response_text
        )

        return BrowserAction.model_validate(
            data
        )