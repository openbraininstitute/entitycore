import pytest

import app.schemas.types as test_module
from app.config import settings


@pytest.mark.parametrize(
    ("page", "page_size", "expected_offset"),
    [
        (1, 10, 0),
        (2, 10, 10),
        (3, 10, 20),
        (1000, settings.PAGINATION_DEFAULT_PAGE_SIZE, settings.PAGINATION_DEFAULT_PAGE_SIZE * 999),
        (1000, settings.PAGINATION_MAX_PAGE_SIZE, settings.PAGINATION_MAX_PAGE_SIZE * 999),
    ],
)
def test_pagination_request_success(page, page_size, expected_offset):
    result = test_module.PaginationRequest(page=page, page_size=page_size)
    assert result.offset == expected_offset


@pytest.mark.parametrize(
    ("page", "page_size", "expected_message"),
    [
        (0, 10, r"page\W+Input should be greater than or equal to 1"),
        (1, 0, r"page_size\W+Input should be greater than or equal to 1"),
        (
            1,
            settings.PAGINATION_MAX_PAGE_SIZE + 1,
            (
                rf"page_size\W+Input should be less than or equal "
                rf"to {settings.PAGINATION_MAX_PAGE_SIZE}"
            ),
        ),
    ],
)
def test_pagination_request_raises(page, page_size, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        test_module.PaginationRequest(page=page, page_size=page_size)
