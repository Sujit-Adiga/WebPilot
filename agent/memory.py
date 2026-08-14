from dataclasses import dataclass
from typing import Optional

from browser.actions import BrowserAction


@dataclass
class ActionRecord:
    step: int
    action: BrowserAction
    result: Optional[str] = None
    error: Optional[str] = None