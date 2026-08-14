from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def generate_action(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict,
    ) -> dict:
        """
        Generate one structured BrowserAction.

        Implementations may use any underlying LLM provider.
        """

        raise NotImplementedError