from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.errors import problem
from api.routers import companies

app = FastAPI(title="Observatorio EPN")
app.include_router(companies.router)


@app.exception_handler(RequestValidationError)
async def invalid_parameter(request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = "; ".join(f"{error['loc'][-1]}: {error['msg']}" for error in exc.errors())
    return problem(400, "Parámetro inválido", detail, request.url.path)
