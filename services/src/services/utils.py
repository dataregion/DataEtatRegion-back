import functools


def wrap_all_ex_to(exception_to_raise):
    """Catch all exception and wraps it into ex"""
    return convert_exception(Exception, exception_to_raise)


def convert_exception(exception_to_transform, exception_to_raise):
    """Catch all exception and wraps it into ex"""

    if not issubclass(exception_to_raise, BaseException) or not issubclass(
        exception_to_transform, BaseException
    ):
        raise ValueError(
            "Mauvaise utilisation du décorateur. ( e.g: @convert_exception(Err, Err) )"
        )

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_to_raise as e:
                raise e
            except exception_to_transform as e:
                raise exception_to_raise from e

        return wrapper

    return decorator
