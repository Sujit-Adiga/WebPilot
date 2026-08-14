from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class BenchmarkTask:
    name: str
    goal: str
    expected_text: Optional[str] = None


TASKS = [
    BenchmarkTask(
        name="Einstein quote",
        goal=(
            "Go to quotes.toscrape.com and find the quote "
            "written by Albert Einstein. Extract the text of the quote."
        ),
        expected_text=(
            "The world as we have created it is a process of our thinking. "
            "It cannot be changed without changing our thinking."
        ),
    ),

    BenchmarkTask(
        name="Oscar Wilde quote",
        goal=(
            "Go to quotes.toscrape.com and find the quote "
            "written by Oscar Wilde. Extract the text of the quote."
        ),
        expected_text=(
            "It is better to be hated for what you are than to be loved "
            "for what you are not."
        ),
    ),

    BenchmarkTask(
        name="George Bernard Shaw quote",
        goal=(
            "Go to quotes.toscrape.com and find the quote "
            "written by George Bernard Shaw. Extract the text of the quote."
        ),
        expected_text=(
            "Life isn't about finding yourself. Life is about creating yourself."
        ),
    ),

    BenchmarkTask(
        name="Navigate to login",
        goal=(
            "Go to quotes.toscrape.com and navigate to the login page."
        ),
        expected_text="Login",
    ),

    BenchmarkTask(
        name="Find tags",
        goal=(
            "Go to quotes.toscrape.com and find the tags associated "
            "with the first quote."
        ),
        expected_text="Tags",
    ),
]