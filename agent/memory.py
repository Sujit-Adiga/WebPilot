from dataclasses import dataclass
from typing import Optional

from browser.actions import BrowserAction


@dataclass
class ActionRecord:
    action: BrowserAction
    result: Optional[str] = None
    error: Optional[str] = None