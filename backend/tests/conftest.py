from __future__ import annotations

import pytest

from robot_control_backend.bootstrap.settings import reset_settings_cache


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    reset_settings_cache()
    yield
    reset_settings_cache()
