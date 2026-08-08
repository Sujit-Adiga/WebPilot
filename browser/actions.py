from typing import Literal
from pydantic import BaseModel


class BrowserAction(BaseModel):
    action: Literal[
        "navigate",
        "click",
        "fill",
        "extract_text",
        "wait",
        "press",
        "done"
    ]

    element_id: int | None = None
    text: str | None = None
    url: str | None = None
    key: str | None = None
