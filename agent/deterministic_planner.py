from browser.actions import BrowserAction


class DeterministicPlanner:

    def __init__(
        self,
        target_author="Albert Einstein",
        failure_mode=None,
    ):
        self.target_author = target_author
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
        # 4. Handle navigation task
        # --------------------------------------------------

        if "navigate to the login page" in goal.lower():

            for element in state.elements:

                element_text = (
                    element.text or ""
                ).lower()

                if "login" in element_text:

                    return BrowserAction(
                        action="click",
                        element_id=element.id,
                    )

            # If already on login page
            if "login" in state.page_text.lower():

                return BrowserAction(
                    action="done",
                    text="Login",
                )

        # --------------------------------------------------
        # 5. Find target quote
        # --------------------------------------------------

        for element in state.elements:

            element_text = element.text or ""

            if self.target_author.lower() in element_text.lower():

                return BrowserAction(
                    action="extract_text",
                    element_id=element.id,
                )

        # --------------------------------------------------
        # 6. Handle first-quote / tags task
        # --------------------------------------------------

        if "tags associated with the first quote" in goal.lower():

            for element in state.elements:

                element_text = element.text or ""

                if "Tags" in element_text:

                    return BrowserAction(
                        action="extract_text",
                        element_id=element.id,
                    )

        # --------------------------------------------------
        # 7. Fallback
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