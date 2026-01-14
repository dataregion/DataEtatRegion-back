from datetime import datetime
from prefect import task
from prefect.cache_policies import NO_CACHE


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def is_second_day_of_week_in_month(day_of_week: int) -> bool:
    today = datetime.today()
    return today.weekday() == day_of_week and 8 <= today.day <= 15