import json
from google import genai
from google.genai import types

from browser.actions import BrowserAction
from agent.state import BrowserState

SYSTEM_PROMPT = """
You are an autonomous browser agent.

You receive:
1. A user goal.
2. The current browser state.

Choose exactly ONE next action.

Rules:
- Use only element IDs present in the current browser state.
- Never invent an element ID.
- Perform exactly one action at a time.
- Do not repeat an action that has already succeeded.
- Prefer the shortest sequence of actions necessary to complete the goal.
- Before choosing an action, determine whether the user's goal is already complete.
- If the goal has been achieved, immediately return {"action": "done"}.
- Do not use extract_text merely to verify that an action succeeded.
- Use extract_text only when the user's goal requires obtaining text from the page.


Action requirements:
- navigate requires url.
- click requires element_id.
- fill requires element_id and text.
- extract_text requires element_id.
- wait requires element_id.
- press requires element_id and key.
- done requires no element_id.

Return JSON only.
"""

class Planner:

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)


    def plan_next_action(self, goal: str, state: BrowserState) -> BrowserAction:
        """Ask Gemini for the next single BrowserAction given a goal and state."""

        user_content = (
            f"Goal: {goal}\n\n"
            f"Current browser state:\n{state.model_dump_json(indent=2)}"
        )

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=BrowserAction,
            ),
        )

        response_text = response.text
        if response_text is None:
            raise ValueError("Empty response text from model")

        data = json.loads(response_text)
        return BrowserAction.model_validate(data)