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
        # 3. Check whether extraction already succeeded
        # --------------------------------------------------

        for record in reversed(history):

            if (
                record.action.action == "extract_text"
                and record.result
                and record.result != "failure"
            ):

                return BrowserAction(
                    action="done",
                    text=record.result,
                )

        # --------------------------------------------------
        # 4. Find Einstein quote element
        # --------------------------------------------------

        for element in state.elements:

            if "Einstein" in element.text:

                return BrowserAction(
                    action="extract_text",
                    element_id=element.id,
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

        # --------------------------------------------------
        # 1. Navigate to test page
        # --------------------------------------------------

        if not history:

            return BrowserAction(
                action="navigate",
                url="http://quotes.toscrape.com",
            )

        # --------------------------------------------------
        # 2. Always produce an invalid action
        # --------------------------------------------------

        return BrowserAction(
            action="click",
            element_id=9999,
        )