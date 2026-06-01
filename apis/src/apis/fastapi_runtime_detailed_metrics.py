from fastapi_runtime_details_collector import setup_lag_monitor

__all__ = ["setup_metrics"]


def setup_metrics():
    return setup_lag_monitor()
