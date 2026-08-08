from browser.actions import BrowserAction
from browser.controller import BrowserController


class ActionExecutor:

    def __init__(self, controller: BrowserController):
        self.controller = controller

    def validate(self, action: BrowserAction):
        if action.action in {
            "click",
            "fill",
            "extract_text",
            "wait",
            "press"
        }:
            if action.element_id is None:
                raise ValueError(
                    f"Element ID required for {action.action}"
                )

            if not self.controller.has_element(action.element_id):
                raise ValueError(
                    f"Invalid element ID: {action.element_id}"
                )

    async def execute(self, action: BrowserAction):
        self.validate(action)

        if action.action == "navigate":
            if action.url is None:
                raise ValueError("URL must be provided for navigate action.")
            await self.controller.goto(action.url)

        elif action.action == "click":
            if action.element_id is None:
                raise ValueError("Element ID must be provided for click action.")
            await self.controller.click(action.element_id)

        elif action.action == "fill":
            if action.element_id is None or action.text is None:
                raise ValueError("Element ID and text must be provided for fill action.")
            await self.controller.fill(action.element_id, action.text)

        elif action.action == "extract_text":
            if action.element_id is None:
                raise ValueError("Element ID must be provided for extract_text action.")
            return await self.controller.extract_text(action.element_id)

        elif action.action == "wait":
            if action.element_id is None:
                raise ValueError("Element ID must be provided for wait action.")
            await self.controller.wait(action.element_id)

        elif action.action == "press":
            if action.element_id is None:
                raise ValueError(
                    "Element ID must be provided for press action."
                )

            if action.key is None:
                raise ValueError(
                    "Key must be provided for press action."
                )

            await self.controller.press(
                action.element_id,
                action.key
            )

        elif action.action == "done":
            return "DONE"