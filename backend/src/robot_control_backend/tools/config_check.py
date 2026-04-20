from __future__ import annotations

from robot_control_backend.bootstrap.settings import (
    SettingsError,
    get_settings,
    run_configuration_preflight,
)


def main() -> None:
    """Validate configuration, print a safe summary, and run optional preflight checks."""
    try:
        settings = get_settings()
        preflight_results = run_configuration_preflight(settings)
    except SettingsError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    print("Configuration valid:")
    for key, value in settings.safe_summary().items():
        print(f"  - {key}: {value}")

    print("Preflight results:")
    for line in preflight_results:
        print(f"  - {line}")
