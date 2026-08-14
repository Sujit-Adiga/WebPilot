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
            "press",
        }:
            if action.element_id is None:
                raise ValueError(
                    f"Element ID required for {action.action}"
                )

            if not self.controller.has_element(action.element_id):
                raise ValueError(
                    f"Invalid element ID: {action.element_id}"
                )

        if action.action == "fill":
            if action.text is None:
                raise ValueError(
                    "Text must be provided for fill action."
                )

        if action.action == "press":
            if action.key is None:
                raise ValueError(
                    "Key must be provided for press action."
                )

    async def execute(self, action: BrowserAction):

        # Validate before executing the action
        self.validate(action)

        if action.action in {"click", "fill", "extract_text", "wait", "press"}:
            assert action.element_id is not None

        if action.action == "fill":
            assert action.text is not None

        if action.action == "press":
            assert action.key is not None

        if action.action == "navigate":

            if action.url is None:
                raise ValueError(
                    "URL must be provided for navigate action."
                )

            await self.controller.goto(action.url)
            return "success"

        elif action.action == "click":

            assert action.element_id is not None
            await self.controller.click(action.element_id)
            return "success"

        elif action.action == "fill":

            assert action.element_id is not None
            assert action.text is not None
            await self.controller.fill(
                action.element_id,
                action.text
            )
            return "success"

        elif action.action == "extract_text":

            assert action.element_id is not None
            return await self.controller.extract_text(
                action.element_id
            )

        elif action.action == "wait":

            assert action.element_id is not None
            await self.controller.wait(
                action.element_id
            )
            return "success"

        elif action.action == "press":

            assert action.element_id is not None
            assert action.key is not None
            await self.controller.press(
                action.element_id,
                action.key
            )
            return "success"

        elif action.action == "done":

            return {
                "status": "DONE",
                "text": action.text
            }

        else:
            raise ValueError(
                f"Unsupported action: {action.action}"
            )