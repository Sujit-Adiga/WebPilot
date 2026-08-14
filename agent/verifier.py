from agent.state import BrowserState


class GoalVerifier:

    def verify(
        self,
        goal: str,
        state: BrowserState,
        result: str | None = None,
    ) -> bool:

        if result is None:
            return False

        result = result.strip()

        if not result:
            return False

        goal_lower = goal.lower()

        # --------------------------------------------------
        # Extraction-style goals
        # --------------------------------------------------

        extraction_keywords = [
            "extract",
            "quote",
            "text",
            "written by",
        ]

        if any(
            keyword in goal_lower
            for keyword in extraction_keywords
        ):

            return True

        # --------------------------------------------------
        # Navigation-style goals
        # --------------------------------------------------

        if "navigate" in goal_lower:

            return True

        return False