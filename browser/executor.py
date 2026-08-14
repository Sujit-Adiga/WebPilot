from browser.actions import BrowserAction
from browser.controller import BrowserController


class ActionExecutor:

    def __init__(self, controller: BrowserController):
        self.controller = controller

    def validate(self, action: BrowserAction):

        # Actions that require an element
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

            if not self.controller.has_element(
                action.element_id
            ):
                raise ValueError(
                    f"Invalid element ID: "
                    f"{action.element_id}"
                )

        # Navigate validation
        if action.action == "navigate":

            if not action.url:
                raise ValueError(
                    "URL must be provided for navigate action."
                )

        # Fill validation
        if action.action == "fill":

            if action.text is None:
                raise ValueError(
                    "Text must be provided for fill action."
                )

        # Press validation
        if action.action == "press":

            if not action.key:
                raise ValueError(
                    "Key must be provided for press action."
                )

    async def execute(
        self,
        action: BrowserAction
    ):

        # Always validate before execution
        self.validate(action)

        if action.action == "navigate":

            url = action.url
            if url is None:
                raise ValueError(
                    "URL must be provided for navigate action."
                )

            await self.controller.goto(
                url
            )

            return "success"

        elif action.action == "click":

            element_id = action.element_id
            if element_id is None:
                raise ValueError(
                    "Element ID required for click action."
                )

            await self.controller.click(
                element_id
            )

            return "success"

        elif action.action == "fill":

            element_id = action.element_id
            if element_id is None:
                raise ValueError(
                    "Element ID required for fill action."
                )

            text = action.text
            if text is None:
                raise ValueError(
                    "Text must be provided for fill action."
                )

            await self.controller.fill(
                element_id,
                text
            )

            return "success"

        elif action.action == "extract_text":

            element_id = action.element_id
            if element_id is None:
                raise ValueError(
                    "Element ID required for extract_text action."
                )

            return await self.controller.extract_text(
                element_id
            )

        elif action.action == "wait":

            element_id = action.element_id
            if element_id is None:
                raise ValueError(
                    "Element ID required for wait action."
                )

            await self.controller.wait(
                element_id
            )

            return "success"

        elif action.action == "press":

            element_id = action.element_id
            if element_id is None:
                raise ValueError(
                    "Element ID required for press action."
                )

            key = action.key
            if key is None:
                raise ValueError(
                    "Key must be provided for press action."
                )

            await self.controller.press(
                element_id,
                key
            )

            return "success"

        elif action.action == "done":

            return "DONE"

        else:

            raise ValueError(
                f"Unknown action: {action.action}"
            )