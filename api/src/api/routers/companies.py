from typing import Annotated

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.engine import RowMapping

from api.errors import problem
from api.repositories import companies
from api.repositories.provenance import ranking_sources
from api.schemas.companies import (
    AnnualFigures,
    CompanyDetail,
    CompanyFilters,
    CompanyPage,
    CompanyProfile,
    CompanySummary,
)

router = APIRouter(prefix="/v1", tags=["datos-abiertos"])


@router.get(
    "/empresas",
    operation_id="listarEmpresas",
    responses={
        400: {"content": {"application/problem+json": {}}, "description": "Parámetro inválido"}
    },
)
def list_companies(filters: Annotated[CompanyFilters, Query()]) -> CompanyPage:
    total, rows = companies.list_companies(filters)
    return CompanyPage(
        total=total,
        limit=filters.limit,
        offset=filters.offset,
        items=[CompanySummary.model_validate(row) for row in rows],
    )


@router.get(
    "/empresas/{expediente}",
    response_model=CompanyDetail,
    operation_id="obtenerEmpresa",
    responses={
        404: {"content": {"application/problem+json": {}}, "description": "Empresa no encontrada"},
        503: {
            "content": {"application/problem+json": {}},
            "description": "Procedencia no disponible",
        },
    },
)
def get_company(
    request: Request,
    company_id: Annotated[int, Path(alias="expediente", ge=1)],
) -> CompanyDetail | JSONResponse:
    record = companies.get_company(company_id)
    if record is None:
        return problem(
            404,
            "No encontrado",
            f"No existe una empresa con el expediente {company_id}",
            request.url.path,
        )
    company, figures, profile = record
    try:
        sources = ranking_sources() if figures else {}
        year_sources = [sources[row["anio"]] for row in figures]
    except (OSError, KeyError, ValueError):
        return problem(
            503,
            "Procedencia no disponible",
            "No se pudo obtener la fuente de uno de los ejercicios fiscales.",
            request.url.path,
        )
    series = [
        AnnualFigures.model_validate({**row, "provenance": source})
        for row, source in zip(figures, year_sources, strict=True)
    ]
    return CompanyDetail.model_validate(
        {**company, "annual_figures": series, "profile": current_profile(profile)}
    )


def current_profile(row: RowMapping | None) -> CompanyProfile | None:
    if row is None:
        return None
    sources = {
        field: row[column]
        for field, column in (
            ("tagline", "tagline_fuente"),
            ("descripcion", "descripcion_fuente"),
            ("productos_servicios", "productos_fuente"),
        )
        if row[column]
    }
    social_links = row["redes"].split("; ") if row["redes"] else []
    return CompanyProfile.model_validate({**row, "redes": social_links, "sources": sources})
