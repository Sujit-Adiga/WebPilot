from agent.state import BrowserState


class GoalVerifier:

    def verify(
        self,
        goal: str,
        state: BrowserState,
        result: str | None = None,
    ) -> bool:
        """
        Verify whether the observed browser state and latest result
        provide sufficient evidence that the goal has been completed.

        This is intentionally conservative:
        - A non-empty extraction result can satisfy extraction goals.
        - Otherwise, the agent should continue planning.
        """

        if result is None:
            return False

        result = result.strip()

        if not result:
            return False

        extraction_keywords = [
            "extract",
            "find",
            "quote",
            "text",
            "written by",
        ]

        goal_lower = goal.lower()

        if any(keyword in goal_lower for keyword in extraction_keywords):
            return True

        return False