from rest_framework.views import exception_handler

_CODE_BY_STATUS = {
    400: "VALIDATION_ERROR",
    401: "AUTHENTICATION_ERROR",
    403: "PERMISSION_DENIED",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "THROTTLED",
}


def custom_exception_handler(exc, context):
    """Normalize every DRF error into the response shape from spec §41:

        {"success": false, "error": {"code": ..., "message": ..., "field": ...}}

    Unhandled (non-APIException) exceptions return None here and fall through
    to Django/DRF's default 500 handling, which never leaks a stack trace to
    the client.
    """

    response = exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    field = None
    message = detail

    if isinstance(detail, dict):
        # Field-level validation errors, e.g. {"amount": ["This field is required."]}
        field = next(iter(detail), None)
        first_value = detail.get(field) if field else None
        if isinstance(first_value, list) and first_value:
            message = str(first_value[0])
        else:
            message = str(first_value) if first_value is not None else "Invalid request."
    elif isinstance(detail, list) and detail:
        message = str(detail[0])
    else:
        message = str(detail)

    response.data = {
        "success": False,
        "error": {
            "code": _CODE_BY_STATUS.get(response.status_code, "ERROR"),
            "message": message,
            "field": field,
        },
    }
    return response
