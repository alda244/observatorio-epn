"""Estados financieros: la identidad del balance y la cuarentena."""

import pandas as pd
import pandera.errors as pe
import pytest

from etl.pipeline import financials


def balance(expediente: int, activo=1000.0, pasivo=400.0, patrimonio=600.0, **extra) -> dict:
    base = {
        "expediente": expediente,
        "anio": 2025,
        "nombre": f"EMPRESA {expediente} S.A.",
        "ruc": "1790000000001",
        "activo": activo,
        "pasivo": pasivo,
        "patrimonio": patrimonio,
        "gasto_personal": 100.0,
    }
    return base | extra


def test_el_activo_es_igual_al_pasivo_mas_el_patrimonio():
    df = pd.DataFrame([balance(1), balance(2, activo=2000.0, pasivo=500.0, patrimonio=1500.0)])
    assert financials.ESQUEMA.validate(df, lazy=True) is not None


def test_un_balance_descuadrado_no_pasa_la_validacion():
    df = pd.DataFrame([balance(1, activo=1000.0, pasivo=400.0, patrimonio=100.0)])
    with pytest.raises(pe.SchemaErrors):
        financials.ESQUEMA.validate(df, lazy=True)


def test_la_tolerancia_absorbe_el_redondeo_pero_no_un_error():
    apenas = pd.DataFrame([balance(1, activo=1000.5, pasivo=400.0, patrimonio=600.0)])
    assert financials.ESQUEMA.validate(apenas, lazy=True) is not None
    df = pd.DataFrame([balance(1, activo=1002.0, pasivo=400.0, patrimonio=600.0)])
    with pytest.raises(pe.SchemaErrors):
        financials.ESQUEMA.validate(df, lazy=True)


def test_la_cuarentena_aparta_el_descuadre_y_la_cifra_negativa():
    df = pd.DataFrame(
        [
            balance(1),
            balance(2, activo=1000.0, pasivo=400.0, patrimonio=100.0),
            balance(3, activo=-5.0, pasivo=0.0, patrimonio=-5.0),
        ]
    )
    buenas, descartes = financials.separar_descartes(df)
    assert set(buenas["expediente"]) == {1}
    assert dict(zip(descartes["expediente"], descartes["motivo_descarte"], strict=True)) == {
        2: "balance_descuadrado",
        3: "cifra_negativa",
    }


@pytest.mark.parametrize(
    ("crudo", "valido"),
    [("1790000000001", True), ("179000000000", False), ("O1790000000001", False), (" ", False)],
)
def test_solo_se_acepta_el_ruc_de_trece_digitos(crudo, valido):
    df = financials.normalizar_ruc(pd.DataFrame([balance(1, ruc=crudo) | {"ruc": crudo}]))
    assert bool(df["ruc_valido"].iloc[0]) is valido
    assert df["ruc_original"].iloc[0] == crudo
    if not valido:
        assert pd.isna(df["ruc"].iloc[0])


def test_el_gasto_en_personal_suma_las_cuentas_de_nomina():
    assert "sueldos_salarios_remuneraciones" in financials.CUENTAS_PERSONAL
    assert len(financials.CUENTAS_PERSONAL) == 5
    assert all(c in financials.CUENTAS.values() for c in financials.CUENTAS_PERSONAL)
