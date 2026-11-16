from collections.abc import Callable

from fastapi import Response


def cache_for(seconds: int) -> Callable[list[Response], None]:
    """
    Dependency to inject a Cache-Control header to a route response.

    Parameters
    ----------
    seconds : int
        Number of seconds to set for max-age
    """

    def _set(response: Response) -> None:
        response.headers["Cache-Control"] = f"public, max-age={seconds}"

    return _set
