import pytest

# Enable assertion rewriting in specific modules. See:
# https://docs.pytest.org/en/stable/how-to/writing_plugins.html#assertion-rewriting
pytest.register_assert_rewrite("tests.utils")
