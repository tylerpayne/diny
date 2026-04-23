import pytest

from diny import provide


@pytest.fixture
def di():
    """Open a clean DI scope for each test."""
    with provide():
        yield
