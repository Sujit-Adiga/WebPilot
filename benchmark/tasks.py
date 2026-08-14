from dataclasses import dataclass
from typing import Optional


@dataclass
class BenchmarkTask:
    name: str
    goal: str
    expected_text: Optional[str] = None
    task_type: str = "normal"


TASKS = [

    # --------------------------------------------------
    # Information extraction
    # --------------------------------------------------

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
        task_type="normal",
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
        task_type="normal",
    ),

    BenchmarkTask(
        name="George Bernard Shaw quote",
        goal=(
            "Go to quotes.toscrape.com and find the quote "
            "written by George Bernard Shaw. Extract the text of the quote."
        ),
        expected_text=(
            "Life isn't about finding yourself. "
            "Life is about creating yourself."
        ),
        task_type="normal",
    ),

    # --------------------------------------------------
    # Navigation / interaction
    # --------------------------------------------------

    BenchmarkTask(
        name="Navigate to login",
        goal=(
            "Go to quotes.toscrape.com and navigate to the login page."
        ),
        expected_text="Login",
        task_type="navigation",
    ),

    BenchmarkTask(
        name="Find tags",
        goal=(
            "Go to quotes.toscrape.com and find the tags associated "
            "with the first quote."
        ),
        expected_text="Tags",
        task_type="normal",
    ),

    # --------------------------------------------------
    # Failure recovery
    # --------------------------------------------------

    BenchmarkTask(
        name="Recover from invalid element",
        goal=(
            "Go to quotes.toscrape.com and find the quote "
            "written by Albert Einstein. Extract the text of the quote."
        ),
        expected_text=(
            "The world as we have created it is a process of our thinking. "
            "It cannot be changed without changing our thinking."
        ),
        task_type="failure_recovery",
    ),

    BenchmarkTask(
        name="Recover after failed click",
        goal=(
            "Go to quotes.toscrape.com and extract the quote "
            "written by Albert Einstein."
        ),
        expected_text=(
            "The world as we have created it is a process of our thinking. "
            "It cannot be changed without changing our thinking."
        ),
        task_type="failure_recovery",
    ),

    # --------------------------------------------------
    # Bounded retry tests
    # --------------------------------------------------

    BenchmarkTask(
        name="Bounded retry — invalid action",
        goal=(
            "Go to quotes.toscrape.com and extract the Einstein quote."
        ),
        task_type="bounded_retry",
    ),

    BenchmarkTask(
        name="Bounded retry — repeated failure",
        goal=(
            "Go to quotes.toscrape.com and extract the Einstein quote."
        ),
        task_type="bounded_retry",
    ),

    BenchmarkTask(
        name="Bounded retry — recovery budget",
        goal=(
            "Go to quotes.toscrape.com and extract the Einstein quote."
        ),
        task_type="bounded_retry",
    ),
]