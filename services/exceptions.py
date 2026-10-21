"""Exception domain. Di-handle terpusat di app.py menjadi response JSON."""

MAX_ERRORS_IN_RESPONSE = 50


class ServiceError(Exception):
    status_code = 500

    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []

    def to_dict(self) -> dict:
        payload = {"status": "error", "message": self.message}
        if self.errors:
            payload["errors"] = self.errors[:MAX_ERRORS_IN_RESPONSE]
            if len(self.errors) > MAX_ERRORS_IN_RESPONSE:
                payload["total_errors"] = len(self.errors)
        return payload


class ValidationError(ServiceError):
    status_code = 400


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409
