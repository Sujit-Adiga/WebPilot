from pydantic import BaseModel, Field


class PageElement(BaseModel):
    id: int
    tag: str
    text: str

    name: str | None = None
    placeholder: str | None = None
    aria_label: str | None = None
    type: str | None = None
    value: str | None = None
    href: str | None = None
    role: str | None = None


class BrowserState(BaseModel):
    url: str
    title: str

    # Visible textual content of the current page.
    # This gives the planner semantic information beyond
    # interactive elements.
    page_text: str = ""

    elements: list[PageElement]

    visited_urls: list[str] = Field(
        default_factory=list
    )