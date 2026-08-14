import json

from groq import Groq

from llm.base import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-20b",
    ):
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate_action(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict,
    ) -> dict:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "browser_action",
                    "strict": True,
                    "schema": response_schema,
                },
            },
            temperature=0,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "LLM returned an empty response."
            )

        return json.loads(content)