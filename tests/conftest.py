import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


_MISSING = object()


class MockScalars:
    def __init__(self, items: list[object]) -> None:
        self._items = items

    def all(self) -> list[object]:
        return self._items


class MockExecuteResult:
    def __init__(
        self,
        *,
        scalars: list[object] | None = None,
        scalar: object = _MISSING,
        rowcount: int = 0,
    ) -> None:
        self._scalars = scalars or []
        self._scalar = scalar
        self.rowcount = rowcount

    def scalars(self) -> MockScalars:
        return MockScalars(self._scalars)

    def scalar_one_or_none(self) -> object | None:
        if self._scalar is not _MISSING:
            return self._scalar
        if not self._scalars:
            return None
        return self._scalars[0]

    def scalar_one(self) -> object:
        if self._scalar is not _MISSING:
            return self._scalar
        return self._scalars[0]


class MockAsyncSession:
    def __init__(self, *execute_results: MockExecuteResult, get_result: object | None = None) -> None:
        self.add = Mock()
        self.execute = AsyncMock(side_effect=list(execute_results))
        self.get = AsyncMock(return_value=get_result)
        self.delete = AsyncMock()
        self.flush = AsyncMock()
        self.refresh = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.close = AsyncMock()

    def set_execute_results(self, *execute_results: MockExecuteResult) -> None:
        self.execute.side_effect = list(execute_results)


@pytest.fixture
def mock_session() -> MockAsyncSession:
    return MockAsyncSession()
