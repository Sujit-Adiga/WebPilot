from agent.memory import ActionRecord
from agent.state import BrowserState
from browser.actions import BrowserAction
from llm.base import LLMProvider


SYSTEM_PROMPT = """
You are an autonomous browser agent.

Choose exactly ONE next BrowserAction based on:
- the user goal
- the current browser state
- recent action history

==================================================
CORE RULES
==================================================

1. Use only element IDs present in the current browser state.
2. Never invent an element ID.
3. Perform exactly one action.
4. Prefer the shortest valid action sequence.
5. Do not repeat successful actions unnecessarily.
6. If an action failed, replan using the new browser state.
7. Do not assume an action succeeded merely because it was requested.
8. Do not invent information unsupported by the browser state.

==================================================
PROGRESS AND LOOP PREVENTION
==================================================

Every action must make meaningful progress toward the goal.

Before selecting an action, inspect:

- the current browser state
- the previous action
- the result of the previous action
- the recent action history
- URLs that have already been visited
- actions that have already been attempted

A successful action does NOT necessarily mean useful progress.

Do NOT repeat an action merely because it succeeded.

In particular:

- Do not repeatedly navigate to the same URL.
- Do not repeatedly click the same element when the previous click
  did not produce useful progress.
- Do not repeatedly extract the same element after the extraction
  has already been performed.
- Do not repeat a sequence of actions that has already produced the
  same page or the same information.
- Do not return to an already visited page unless there is a clear
  reason that doing so is necessary for the goal.
- Do not restart a search from the beginning after making progress.
- When searching through multiple pages, prefer moving to a new page
  rather than returning to a page already visited.

For every proposed action, ask:

"Will this action provide new information or move me closer to
the user's goal?"

If the answer is no, choose another action.

==================================================
NAVIGATION RULES
==================================================

Do not navigate to a URL that has already been visited during the
current task unless:

1. the user explicitly requires revisiting it, or
2. the current browser state is meaningfully different and the
   navigation is necessary.

If the current URL already contains the information needed to
complete the goal, do not navigate elsewhere.

When searching paginated content:

- identify the current page
- inspect the available navigation controls
- move to a new page when necessary
- never repeatedly navigate to the same page

==================================================
ACTION HISTORY
==================================================

The action history records previous actions and their results.

Use it to determine:

- what URLs have already been visited
- what elements have already been clicked
- what text has already been extracted
- which actions failed
- which actions succeeded
- whether an action actually produced progress
- whether the agent is beginning to loop

A repeated successful action is still a problem if it produces
no new information.

For example, this is a loop:

navigate(page/1)
click(A)
click(B)
navigate(page/1)
click(A)
click(B)

Do not continue such a sequence.

If the same action appears repeatedly in the history and the
browser state has not provided meaningful new information, choose
a different strategy.

==================================================
TEXT EXTRACTION
==================================================

If the goal requires finding, obtaining, reading, or extracting
specific information:

1. Inspect page_text to identify relevant content.
2. Identify the element containing the requested information.
3. Use extract_text on that element.
4. After extract_text succeeds, inspect the extraction result.
5. Compare the extraction result directly against the user's goal.

If the extraction result satisfies the user's goal:

- immediately return done
- use the extracted information as the done text
- do NOT perform another extract_text action
- do NOT search for another item
- do NOT repeat the extraction

IMPORTANT:

A successful extraction is NOT automatically sufficient.

The extracted content must satisfy the requested target.

For example, if the goal is:

"Find the quote written by Albert Einstein"

and extract_text returns:

"The world as we have created it is a process of our thinking..."

by Albert Einstein

then the goal has been satisfied and the next action MUST be:

{
    "action": "done",
    "text": "The world as we have created it is a process of our thinking..."
}

Do not extract another quote from the page.

==================================================
GOAL COMPLETION
==================================================

Before selecting any new action, check whether the goal has already
been achieved.

Pay special attention to the result of the immediately preceding
action.

If the previous action was extract_text and its result contains the
requested information:

- return done immediately.

Never continue browsing after successfully obtaining the requested
information.

For extraction goals:

successful extraction + result satisfies goal = DONE

For navigation goals:

return done only when the current browser state proves that the
requested destination has been reached.

For interaction goals:

return done only when the browser state proves that the requested
interaction has occurred.

Never return done with empty or null text when the goal requires an
extracted answer.

==================================================
RECOVERY AFTER FAILURE
==================================================

If the previous action failed:

1. inspect the failure
2. inspect the new browser state
3. determine why the action failed
4. choose a different valid action when possible

Do not blindly repeat a failed action.

For example, if:

click(element_id=9999)

fails because the element does not exist, do not select
element_id=9999 again.

==================================================
OUTPUT
==================================================

Return exactly ONE BrowserAction.

Return JSON only.

Do not include:
- explanations
- reasoning
- markdown
- multiple actions
"""


class Planner:

    def __init__(
        self,
        llm: LLMProvider,
    ):
        self.llm = llm

    @staticmethod
    def _action_signature(action: BrowserAction) -> tuple:
        """
        Create a deterministic representation of an action so that
        repeated actions can be detected independently of JSON
        formatting.
        """

        return (
            action.action,
            action.element_id,
            action.text,
            action.url,
            action.key,
        )

    @staticmethod
    def _successful_history(history: list[ActionRecord]) -> list[ActionRecord]:
        """
        Return actions that completed successfully.

        We use the presence of an error as the failure signal because
        ActionRecord already stores the action result and error.
        """

        return [
            record
            for record in history
            if not record.error
        ]

    def _visited_urls(
        self,
        history: list[ActionRecord],
    ) -> set[str]:
        """
        Collect URLs that were successfully visited.
        """

        visited = set()

        for record in self._successful_history(history):

            action = record.action

            if action.action == "navigate" and action.url:
                visited.add(action.url.rstrip("/"))

        return visited

    def _repeated_action(
        self,
        action: BrowserAction,
        history: list[ActionRecord],
    ) -> bool:
        """
        Detect whether the proposed action is already present as a
        recent successful action.

        We only consider the recent history because repeating an
        action after substantial page progress can be legitimate.
        """

        successful = self._successful_history(history)

        if not successful:
            return False

        proposed = self._action_signature(action)

        # Compare against the most recent successful actions.
        recent_successful = successful[-3:]

        return any(
            self._action_signature(record.action) == proposed
            for record in recent_successful
        )

    def _repeated_navigation(
        self,
        action: BrowserAction,
        history: list[ActionRecord],
    ) -> bool:
        """
        Navigation to an already visited URL is usually a loop during
        a search task.
        """

        if action.action != "navigate" or not action.url:
            return False

        normalized_url = action.url.rstrip("/")

        return normalized_url in self._visited_urls(history)

    def _build_prompt(
        self,
        goal: str,
        state: BrowserState,
        history: list[ActionRecord],
        planning_warning: str | None = None,
    ) -> str:

        # Keep only recent history to control prompt size.
        recent_history = history[-6:]

        history_text = "\n".join(
            (
                f"Action: {record.action.model_dump_json()} | "
                f"Result: {record.result} | "
                f"Error: {record.error}"
            )
            for record in recent_history
        )

        if not history_text:
            history_text = "No previous actions."

        last_result = "No previous action result."

        if history:
            last_record = history[-1]

            last_result = (
                f"Action: {last_record.action.model_dump_json()}\n"
                f"Result: {last_record.result}\n"
                f"Error: {last_record.error}"
            )

        visited_urls = sorted(
            self._visited_urls(history)
        )

        visited_text = (
            "\n".join(visited_urls)
            if visited_urls
            else "No URLs visited yet."
        )

        # Bound page text so large pages do not exceed the LLM
        # token budget.
        page_text = state.page_text[:6000]

        warning_text = ""

        if planning_warning:
            warning_text = (
                "\n\nPLANNER WARNING:\n"
                f"{planning_warning}\n"
                "You MUST choose a different action that makes "
                "meaningful progress.\n"
            )

        return (
            f"Goal:\n"
            f"{goal}\n\n"

            f"Current URL:\n"
            f"{state.url}\n\n"

            f"Page text:\n"
            f"{page_text}\n\n"

            f"Interactive elements:\n"
            f"{state.elements}\n\n"

            f"LAST ACTION RESULT:\n"
            f"{last_result}\n\n"

            f"RECENT ACTION HISTORY:\n"
            f"{history_text}\n\n"

            f"ALREADY VISITED URLS:\n"
            f"{visited_text}\n"

            f"{warning_text}\n"

            f"IMPORTANT:\n"
            f"If the last action already produced the information "
            f"requested by the goal, return done immediately.\n"
            f"Do not perform another action.\n"
            f"If an action would repeat a previous unsuccessful "
            f"strategy without making progress, choose another "
            f"strategy."
        )

    def _generate_action(
        self,
        goal: str,
        state: BrowserState,
        history: list[ActionRecord],
        planning_warning: str | None = None,
    ) -> BrowserAction:

        print("\n=== CURRENT ELEMENTS ===")
        for element in state.elements:
            print(element)
        print("========================\n")

        user_prompt = self._build_prompt(
            goal=goal,
            state=state,
            history=history,
            planning_warning=planning_warning,
        )

        # Groq strict structured outputs require every property
        # to be required. Optional BrowserAction fields are therefore
        # represented as nullable values.
        response_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "navigate",
                        "click",
                        "fill",
                        "extract_text",
                        "wait",
                        "press",
                        "done",
                    ],
                },
                "element_id": {
                    "type": ["integer", "null"],
                },
                "text": {
                    "type": ["string", "null"],
                },
                "url": {
                    "type": ["string", "null"],
                },
                "key": {
                    "type": ["string", "null"],
                },
            },
            "required": [
                "action",
                "element_id",
                "text",
                "url",
                "key",
            ],
        }

        data = self.llm.generate_action(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        return BrowserAction.model_validate(data)

    def plan_next_action(
        self,
        goal: str,
        state: BrowserState,
        history: list[ActionRecord],
    ) -> BrowserAction:

        planning_warning = None

        # Allow a small number of replanning attempts inside the
        # planner if the LLM proposes an action that would obviously
        # repeat a recent successful action.
        #
        # This does NOT execute the action. It simply asks the LLM
        # for a better action.
        for _ in range(3):

            action = self._generate_action(
                goal=goal,
                state=state,
                history=history,
                planning_warning=planning_warning,
            )

            # A done action is always allowed to pass through here.
            # Goal correctness is handled by the agent/verification
            # layer.
            if action.action == "done":
                return action

            # Prevent returning to a URL that has already been visited.
            if self._repeated_navigation(
                action,
                history,
            ):
                planning_warning = (
                    f"You proposed navigating to "
                    f"'{action.url}', but this URL has already "
                    f"been visited during this task. "
                    f"Do not navigate there again. "
                    f"Choose an action that exposes new information "
                    f"or moves toward the requested target."
                )
                continue

            # Prevent immediate/recent repetition of a successful
            # action that has already failed to make progress.
            if self._repeated_action(
                action,
                history,
            ):
                planning_warning = (
                    "You proposed an action that was already "
                    "successfully executed recently. "
                    "It did not complete the goal. "
                    "Do not repeat that action. "
                    "Choose a different action that makes meaningful "
                    "progress toward the goal."
                )
                continue

            return action

        # If the model repeatedly proposes the same action despite
        # explicit warnings, return the last proposed action rather
        # than silently inventing a different browser action.
        #
        # The outer BrowserAgent can then apply its normal loop /
        # failure handling.
        return action