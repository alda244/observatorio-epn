from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Group = Literal["TEC", "G", "C", "M", "K"]
Size = Literal["micro_pequena", "mediana", "grande"]
ProfileStatus = Literal["completa", "parcial", "sin_ficha"]
AlertReason = Literal["imposible", "grande_menos_10", "fuera_de_rango_division"]


class CompanyFilters(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group: Group | None = Field(default=None, alias="grupo")
    industry_section: str | None = Field(default=None, alias="seccion_ciiu", pattern=r"^[A-U]$")
    province: str | None = Field(default=None, alias="provincia")
    size: Size | None = Field(default=None, alias="tamano")
    name: str | None = Field(default=None, alias="nombre", min_length=2)
    in_pilot: bool | None = Field(default=None, alias="en_piloto")
    profile_status: ProfileStatus | None = Field(default=None, alias="estado_ficha")
    has_alert: bool | None = Field(default=None, alias="tiene_alerta")
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: Literal["ventas", "nombre", "empleados"] = Field(default="ventas", alias="orden")


class CompanySummary(BaseModel):
    company_id: int = Field(alias="expediente")
    tax_id: str | None = Field(default=None, alias="ruc", pattern=r"^\d{13}$")
    name: str = Field(alias="nombre")
    trade_name: str | None = Field(default=None, alias="nombre_comercial")
    industry_code: str = Field(alias="ciiu")
    industry_description: str | None = Field(alias="ciiu_descripcion")
    industry_section: str | None = Field(alias="seccion_ciiu")
    group: Group = Field(alias="grupo")
    province: str | None = Field(alias="provincia")
    city: str | None = Field(alias="ciudad")
    sales: float | None = Field(alias="ventas")
    employees: int | None = Field(alias="empleados")
    size: Size | None = Field(alias="tamano")
    has_alert: bool = Field(alias="tiene_alerta")
    alert_reason: AlertReason | None = Field(alias="motivo_alerta")
    in_pilot: bool = Field(alias="en_piloto")
    profile_status: ProfileStatus = Field(alias="estado_ficha")


class CompanyPage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    limit: int
    offset: int
    items: list[CompanySummary] = Field(alias="datos")


class Provenance(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    source_type: Literal["scvs_ranking"] = Field(default="scvs_ranking", alias="fuente_tipo")
    source_url: str = Field(alias="fuente_url")
    cutoff_date: date = Field(alias="fecha_corte")


class AnnualFigures(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fiscal_year: int = Field(alias="anio")
    provenance: Provenance = Field(alias="procedencia")
    employees: int | None = Field(alias="empleados")
    assets: float | None = Field(alias="activo")
    equity: float | None = Field(alias="patrimonio")
    sales: float | None = Field(alias="ventas")
    net_income: float | None = Field(alias="utilidad_neta")
    total_income: float | None = Field(alias="ingreso_total")
    size: Size | None = Field(alias="tamano")
    has_alert: bool = Field(alias="tiene_alerta")
    alert_reason: AlertReason | None = Field(alias="motivo_alerta")
    income_not_reported: bool = Field(alias="ingreso_total_no_reportado")
    profit_not_reported: bool = Field(alias="utilidad_no_reportada")
    group_rank: int | None = Field(alias="rank_grupo")
    qualified_this_year: bool = Field(alias="en_universo_ese_anio")


class CompanyProfile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    official_url: str | None = Field(alias="url_oficial")
    tagline: str | None = Field(max_length=150)
    description: str | None = Field(alias="descripcion")
    products_and_services: str | None = Field(alias="productos_servicios")
    corporate_email: str | None = Field(alias="correo_corporativo")
    phone: str | None = Field(alias="telefono")
    social_links: list[str] = Field(alias="redes")
    logo_url: str | None
    address: str | None = Field(alias="direccion")
    source_type: Literal["web_oficial", "informe_anual_oficial", "catalogo_oficial", "prensa"] = (
        Field(alias="fuente_tipo")
    )
    captured_on: date = Field(alias="fecha_captura")
    status: Literal["completo", "parcial", "pendiente"] = Field(alias="estado")
    sources: dict[str, str] = Field(alias="fuentes")


class CompanyDetail(CompanySummary):
    model_config = ConfigDict(populate_by_name=True)

    industry_division: str | None = Field(alias="division_ciiu")
    company_type: str | None = Field(alias="tipo_compania")
    region: str | None
    is_holding: bool | None = Field(alias="es_holding")
    annual_figures: list[AnnualFigures] = Field(alias="cifras")
    profile: CompanyProfile | None = Field(alias="ficha")
