from typing import Any, Optional


class APIError(Exception):
    """Exception raised for errors during API calls."""

    def __init__(
        self,
        status_code: int,
        message: str = "Error occurred in API call",
        params: Optional[dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.params = params or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.params:
            params_str = ", ".join(
                f"{key}={value}" for key, value in self.params.items()
            )
            return f"[{self.status_code}] {self.message} - [{params_str}]"
        else:
            return f"[{self.status_code}] {self.message}"
