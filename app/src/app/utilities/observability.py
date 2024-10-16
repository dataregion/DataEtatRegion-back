"""
Module pour l'observabilité. ie. prometheus
"""

from contextlib import contextmanager
from functools import wraps
from prometheus_client import Gauge, Summary
import time


def get_full_func_name(func):
    return func.__module__ + "." + func.__qualname__


def sanitize_prom_metric_name(name):
    transformed = name
    transformed = transformed.replace(".", "_")
    transformed = transformed.replace("<", "_")
    transformed = transformed.replace(">", "_")
    return transformed


_SUMMARY_CACHE = {}


def _get_summary_of_time_or_default(name) -> Summary:
    if name not in _SUMMARY_CACHE:
        summary = Summary(f"{name}_latency_seconds", f"Performance for {name}")
        _SUMMARY_CACHE[name] = summary
    return _SUMMARY_CACHE[name]


__GAUGE_CACHE = {}


def _get_gauge_of_currently_executing_or_default(name) -> Gauge:
    if name not in __GAUGE_CACHE:
        gauge = Gauge(f"{name}_inprogress", f"Currently executing {name}")
        __GAUGE_CACHE[name] = gauge
    return __GAUGE_CACHE[name]


def summary_of_time():
    """Expose une métrique prometheus concernant le temps d'execution de la fonction sous forme de summary"""

    def wrapper(func):
        name = get_full_func_name(func)
        name = sanitize_prom_metric_name(name)

        summary = _get_summary_of_time_or_default(name)

        @wraps(func)
        @summary.time()
        def inner_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return inner_wrapper

    return wrapper


class SummaryOfTimePerfCounter:
    """
    Performance counter allowing to instruct a prometheus summary representing
    execution time of the code section
    """

    def __init__(self, name) -> None:
        self._summary = _get_summary_of_time_or_default(name)
        self._start = None
        self._end = None

    def start(self):
        if self._start is not None:
            raise RuntimeError("Ne démarrez pas deux fois un PerfCounter")
        self._start = time.perf_counter()

    def observe(self):
        if self._start is None:
            raise RuntimeError("Démarrez le PerfCounter avant d'appeler observe")
        self._end = time.perf_counter()

        diff = self._end - self._start
        self._summary.observe(diff)

    @staticmethod
    @contextmanager
    def cm(name: str):
        pc = SummaryOfTimePerfCounter(name)
        pc.start()
        try:
            yield
        finally:
            pc.observe()


def gauge_of_currently_executing():
    """Expose une métrique prometheus qui traque le nombre d'execution courante sous forme de jauge"""

    def wrapper(func):
        name = get_full_func_name(func)
        name = sanitize_prom_metric_name(name)

        gauge = _get_gauge_of_currently_executing_or_default(name)

        @wraps(func)
        @gauge.track_inprogress()
        def inner_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return inner_wrapper

    return wrapper
