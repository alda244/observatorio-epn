from sqlalchemy import column, false, func, select, table, true
from sqlalchemy.engine import RowMapping

from api.db import engine
from api.schemas.companies import CompanyFilters

COMPANIES = table(
    "v_empresa",
    *(
        column(name)
        for name in (
            "expediente",
            "ruc",
            "nombre",
            "ciiu",
            "ciiu_descripcion",
            "seccion_ciiu",
            "grupo",
            "provincia",
            "ciudad",
            "en_piloto",
            "estado_ficha",
            "division_ciiu",
            "tipo_compania",
            "region",
            "es_holding",
        )
    ),
    schema="public",
)
FIGURES = table(
    "v_cifras_anuales",
    *(
        column(name)
        for name in (
            "expediente",
            "anio",
            "ventas",
            "empleados",
            "tamano_derivado",
            "tiene_alerta",
            "motivo_alerta",
            "activo",
            "patrimonio",
            "utilidad_neta",
            "ingreso_total",
            "ingreso_total_no_reportado",
            "utilidad_no_reportada",
            "rank_grupo",
            "en_universo_ese_anio",
        )
    ),
    schema="public",
)

PROFILES = table(
    "ficha_vigente",
    *(
        column(name)
        for name in (
            "expediente",
            "url_oficial",
            "tagline",
            "tagline_fuente",
            "descripcion",
            "descripcion_fuente",
            "productos_servicios",
            "productos_fuente",
            "correo_corporativo",
            "telefono",
            "redes",
            "logo_url",
            "direccion",
            "fuente_tipo",
            "fecha_captura",
            "estado",
        )
    ),
    schema="public",
)

LATEST = (
    select(
        FIGURES.c.ventas,
        FIGURES.c.empleados,
        FIGURES.c.tamano_derivado.label("tamano"),
        FIGURES.c.tiene_alerta,
        FIGURES.c.motivo_alerta,
    )
    .where(FIGURES.c.expediente == COMPANIES.c.expediente)
    .order_by(FIGURES.c.anio.desc())
    .limit(1)
    .lateral("latest")
)
ALERT = func.coalesce(LATEST.c.tiene_alerta, false())
SORTS = {
    "ventas": LATEST.c.ventas.desc().nulls_last(),
    "nombre": COMPANIES.c.nombre.asc(),
    "empleados": LATEST.c.empleados.desc().nulls_last(),
}


def company_summary():
    return select(
        *COMPANIES.c,
        LATEST.c.ventas,
        LATEST.c.empleados,
        LATEST.c.tamano,
        ALERT.label("tiene_alerta"),
        LATEST.c.motivo_alerta,
    )


def list_companies(filters: CompanyFilters) -> tuple[int, list[RowMapping]]:
    source = COMPANIES.outerjoin(LATEST, true())
    exact_filters = {
        COMPANIES.c.grupo: filters.group,
        COMPANIES.c.seccion_ciiu: filters.industry_section,
        COMPANIES.c.provincia: filters.province,
        COMPANIES.c.en_piloto: filters.in_pilot,
        COMPANIES.c.estado_ficha: filters.profile_status,
        LATEST.c.tamano: filters.size,
        ALERT: filters.has_alert,
    }
    conditions = [field == value for field, value in exact_filters.items() if value is not None]
    if filters.name is not None:
        conditions.append(COMPANIES.c.nombre.icontains(filters.name, autoescape=True))

    count = select(func.count()).select_from(source).where(*conditions)
    page = (
        company_summary()
        .select_from(source)
        .where(*conditions)
        .order_by(SORTS[filters.sort], COMPANIES.c.expediente)
        .limit(filters.limit)
        .offset(filters.offset)
    )
    with engine().connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        total = connection.execute(count).scalar_one()
        if filters.offset >= total:
            return total, []
        return total, list(connection.execute(page).mappings())


def get_company(company_id: int) -> tuple[RowMapping, list[RowMapping], RowMapping | None] | None:
    company_query = (
        company_summary()
        .select_from(COMPANIES.outerjoin(LATEST, true()))
        .where(COMPANIES.c.expediente == company_id)
    )
    figures_query = (
        select(
            *(field for field in FIGURES.c if field is not FIGURES.c.tamano_derivado),
            FIGURES.c.tamano_derivado.label("tamano"),
        )
        .where(FIGURES.c.expediente == company_id)
        .order_by(FIGURES.c.anio.desc())
    )
    profile_query = select(PROFILES).where(PROFILES.c.expediente == company_id)
    with engine().connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        company = connection.execute(company_query).mappings().one_or_none()
        if company is None:
            return None
        figures = list(connection.execute(figures_query).mappings())
        profile = None
        if company["en_piloto"]:
            profile = connection.execute(profile_query).mappings().one_or_none()
        return company, figures, profile
