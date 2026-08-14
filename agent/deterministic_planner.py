from browser.actions import BrowserAction


class DeterministicPlanner:

    def __init__(self, failure_mode=None):
        self.failure_mode = failure_mode
        self.failed_once = False

    def plan_next_action(
        self,
        goal,
        state,
        history,
    ):

        # --------------------------------------------------
        # 1. Navigate to test page
        # --------------------------------------------------

        if not history:

            return BrowserAction(
                action="navigate",
                url="http://quotes.toscrape.com",
            )

        # --------------------------------------------------
        # 2. Inject one intentional failure
        # --------------------------------------------------

        if (
            self.failure_mode == "invalid_element"
            and not self.failed_once
        ):

            self.failed_once = True

            return BrowserAction(
                action="click",
                element_id=9999,
            )

        # --------------------------------------------------
        # 3. Find Einstein quote element
        # --------------------------------------------------

        for element in state.elements:

            if "Einstein" in element.text:

                return BrowserAction(
                    action="extract_text",
                    element_id=element.id,
                )

        # --------------------------------------------------
        # 4. After extraction, finish
        # --------------------------------------------------

        for record in reversed(history):

            if (
                record.action.action
                == "extract_text"
                and record.result
                and record.result != "failure"
            ):

                return BrowserAction(
                    action="done",
                    text=record.result,
                )

        # --------------------------------------------------
        # 5. Fallback
        # --------------------------------------------------

        return BrowserAction(
            action="done",
            text=None,
        )


class AlwaysFailPlanner:

    def plan_next_action(
        self,
        goal,
        state,
        history,
    ):

        if not history:

            return BrowserAction(
                action="navigate",
                url="http://quotes.toscrape.com",
            )

        return BrowserAction(
            action="click",
            element_id=9999,
        )