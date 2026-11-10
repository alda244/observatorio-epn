"""Selección reproducible del universo 2025 y del piloto de 500 empresas.

Entrada: ranking oficial SCVS 2025 (``etl/datos/crudo/2025/ranking_2025.xlsx``),
descargado sin modificar desde
https://appscvsmovil.supercias.gob.ec/ranking/reporte.html.

Salidas en ``etl/datos/universo/2025/``:

- ``universo_2025.csv``: 14.042 empresas (núcleo tecnológico completo +
  medianas y grandes de G, C, M y K).
- ``piloto_500.csv``: 300 tecnológicas medianas y grandes + top 50 por ventas
  de G, C, M y K.
- ``top50_<grupo>.csv``: las cinco listas top 50 por ventas (TEC, G, C, M, K).
- ``calidad_2025.json``: conteos y alertas de calidad del archivo crudo.

Uso (desde la raíz del repositorio)::

    python etl/universo/seleccionar_universo.py

Reglas (documentadas en docs/investigacion/12 y 13):

- Tamaño derivado por ventas (COPCI): mediana > USD 1 M y <= USD 5 M;
  grande > USD 5 M. La columna ``Tamaño`` del ranking 2025 viene vacía.
- Núcleo tecnológico: CIIU Rev. 4 J61, J62, J63 y J582.
- Se eliminan expedientes duplicados (copias exactas en el archivo crudo).
- En K se excluyen del top 50 las sociedades de cartera (CIIU K642 o
  "HOLDING" en la razón social), porque no ofrecen productos ni servicios al
  público. Siguen en el universo.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
CRUDO = RAIZ / "etl" / "datos" / "crudo" / "2025" / "ranking_2025.xlsx"
SALIDA = RAIZ / "etl" / "datos" / "universo" / "2025"
URL_FUENTE = "https://appscvsmovil.supercias.gob.ec/ranking/recursos/archivos/ranking_2025.xlsx"

UMBRAL_MEDIANA = 1_000_000
UMBRAL_GRANDE = 5_000_000
TOP_N = 50
PREFIJOS_TEC = ("J61", "J62", "J63", "J582")
GRUPOS = {
    "TEC": "Tecnológicas (J61, J62, J63, J582)",
    "G": "G Comercio",
    "C": "C Manufactura",
    "M": "M Actividades profesionales, científicas y técnicas",
    "K": "K Actividades financieras y de seguros",
}

RENOMBRE = {
    "Expediente": "expediente",
    "Nombre": "nombre",
    "Tipo Compañia": "tipo_compania",
    "Región": "region",
    "Provincia": "provincia",
    "Ciudad": "ciudad",
    "Sector": "sector_scvs",
    "Cant. Empleados": "empleados",
    "Activio\n2025": "activo",
    "Patrimonio\n2025": "patrimonio",
    "Ingreso por ventas\n2025": "ventas",
    "Utilidad neta\n2025": "utilidad_neta",
    "Ingreso Total\n2025": "ingreso_total",
}


def grupo_de(ciiu: str) -> str | None:
    """Devuelve el grupo del universo para un código CIIU, o None si no entra."""
    if ciiu.startswith(PREFIJOS_TEC):
        return "TEC"
    if ciiu[:1] in ("G", "C", "M", "K"):
        return ciiu[:1]
    return None


def tamano_de(ventas: float) -> str:
    """Tamaño derivado por ventas anuales (COPCI)."""
    if ventas > UMBRAL_GRANDE:
        return "grande"
    if ventas > UMBRAL_MEDIANA:
        return "mediana"
    return "micro_pequena"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_ranking(ruta: Path) -> tuple[pd.DataFrame, str]:
    """Lee el ranking crudo (encabezado en la segunda fila) y la fecha de corte."""
    corte = str(pd.read_excel(ruta, header=None, nrows=1).iloc[0, 0])
    df = pd.read_excel(ruta, header=1)
    return df, corte.replace("Fecha de corte - ", "").strip()


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    actividad = df["Actividad económica"].astype(str)
    out = df.rename(columns=RENOMBRE)[list(RENOMBRE.values())].copy()
    out["anio"] = df["Año"]
    out["ciiu"] = actividad.str.split(" - ", n=1).str[0].str.strip()
    out["ciiu_descripcion"] = actividad.str.split(" - ", n=1).str[1].str.strip()
    out["seccion_ciiu"] = out["ciiu"].str[:1]
    out["division_ciiu"] = out["ciiu"].str[:3]
    for col in ("nombre", "provincia", "ciudad", "region", "tipo_compania"):
        out[col] = out[col].astype(str).str.strip()
    out["grupo"] = out["ciiu"].map(grupo_de)
    out["tamano_derivado"] = out["ventas"].map(tamano_de)
    # Sociedades de cartera: CIIU K642 o "HOLDING" en la razón social.
    out["es_holding"] = out["ciiu"].str.startswith("K642") | out["nombre"].str.upper().str.contains(
        "HOLDING", regex=False
    )
    # Alerta del caso señalado por el director (Tiendas Tuti: 8 empleados y
    # más de USD 1.000 millones en ventas): grande por ventas con < 10 empleados.
    out["alerta_empleados"] = (out["tamano_derivado"] == "grande") & (out["empleados"] < 10)
    return out


def main() -> int:
    if not CRUDO.exists():
        print(f"No existe {CRUDO}. Descárguelo desde {URL_FUENTE}", file=sys.stderr)
        return 1
    SALIDA.mkdir(parents=True, exist_ok=True)

    crudo, corte = leer_ranking(CRUDO)
    filas_crudo = len(crudo)
    df = preparar(crudo)

    duplicados = int(df.duplicated("expediente").sum())
    df = df.drop_duplicates("expediente", keep="first")
    anio_cero = int((df["anio"] == 0).sum())

    en_grupo = df[df["grupo"].notna()]
    universo = en_grupo[
        (en_grupo["grupo"] == "TEC") | (en_grupo["tamano_derivado"] != "micro_pequena")
    ].copy()
    universo = universo.sort_values(["grupo", "ventas"], ascending=[True, False])
    universo["rank_grupo"] = universo.groupby("grupo")["ventas"].rank(
        ascending=False, method="first"
    ).astype(int)

    columnas = [
        "expediente", "nombre", "grupo", "ciiu", "ciiu_descripcion", "seccion_ciiu",
        "division_ciiu", "tamano_derivado", "tipo_compania", "region", "provincia",
        "ciudad", "empleados", "activo", "patrimonio", "ventas", "utilidad_neta",
        "ingreso_total", "es_holding", "alerta_empleados", "rank_grupo",
    ]
    universo[columnas].to_csv(SALIDA / "universo_2025.csv", index=False, encoding="utf-8")

    # Listas top 50 por grupo.
    tops: dict[str, pd.DataFrame] = {}
    for g in GRUPOS:
        cand = universo[universo["grupo"] == g]
        if g == "K":
            cand = cand[~cand["es_holding"]]
        top = cand.nlargest(TOP_N, "ventas").copy()
        top.insert(0, "posicion", range(1, len(top) + 1))
        tops[g] = top
        top[["posicion", *columnas]].to_csv(
            SALIDA / f"top50_{g.lower()}.csv", index=False, encoding="utf-8"
        )

    # Piloto: 300 tecnológicas medianas y grandes + top 50 de G, C, M, K.
    tec = universo[(universo["grupo"] == "TEC") & (universo["tamano_derivado"] != "micro_pequena")].copy()
    tec["criterio_piloto"] = "tecnologica_mediana_grande"
    partes = [tec]
    for g in ("G", "C", "M", "K"):
        t = tops[g].drop(columns="posicion").copy()
        t["criterio_piloto"] = f"top50_{g.lower()}"
        partes.append(t)
    piloto = pd.concat(partes, ignore_index=True)
    piloto["en_top50_tec"] = piloto["expediente"].isin(tops["TEC"]["expediente"])
    piloto[[*columnas, "criterio_piloto", "en_top50_tec"]].to_csv(
        SALIDA / "piloto_500.csv", index=False, encoding="utf-8"
    )

    conteo = (
        en_grupo.groupby(["grupo", "tamano_derivado"]).size().unstack(fill_value=0).to_dict("index")
    )
    calidad = {
        "fuente_url": URL_FUENTE,
        "archivo": str(CRUDO.relative_to(RAIZ)).replace("\\", "/"),
        "sha256": sha256(CRUDO),
        "fecha_corte": corte,
        "filas_crudo": filas_crudo,
        "expedientes_duplicados_eliminados": duplicados,
        "filas_con_anio_cero": anio_cero,
        "filas_con_ventas_cero": int((df["ventas"] == 0).sum()),
        "columna_tamano_vacia": bool(crudo["Tamaño"].isna().all()),
        "grandes_con_menos_de_10_empleados": int(df["alerta_empleados"].sum()),
        "grandes_total": int((df["tamano_derivado"] == "grande").sum()),
        "empleados_maximo_declarado": int(df["empleados"].max()),
        "conteo_por_grupo_y_tamano": conteo,
        "universo_por_grupo": universo["grupo"].value_counts().to_dict(),
        "universo_total": len(universo),
        "holdings_en_universo": int(universo["es_holding"].sum()),
        "piloto_total": len(piloto),
        "piloto_por_criterio": piloto["criterio_piloto"].value_counts().to_dict(),
        "piloto_con_alerta_empleados": int(piloto["alerta_empleados"].sum()),
    }
    (SALIDA / "calidad_2025.json").write_text(
        json.dumps(calidad, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(calidad, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
