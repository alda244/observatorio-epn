from fastapi.responses import JSONResponse


def problem(status: int, title: str, detail: str, instance: str) -> JSONResponse:
    return JSONResponse(
        {
            "type": "about:blank",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
        },
        status_code=status,
        media_type="application/problem+json",
    )
