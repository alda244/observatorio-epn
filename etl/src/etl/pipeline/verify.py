"""Paso `verificar`: comprueba que todo lo que produjo el ETL cuadra.

No transforma nada: lee lo que hay en disco y comprueba las condiciones que
deben cumplirse siempre. Es la red de seguridad del pipeline, y responde una
pregunta concreta: ¿se puede confiar en estos datos?

Qué comprueba, por capa:

| Capa | Comprobación |
| --- | --- |
| Crudo | Cada archivo del MANIFEST coincide con su hash SHA-256 |
| Crudo | Cada HTML capturado está en disco y su contenido da el hash del manifiesto |
| Plata | Expediente único y filas que cuadran contra el archivo crudo |
| Plata | CIIU con formato válido, cifras no negativas y ventas ≤ ingreso donde se reportó |
| Oro | El universo sale de plata y todos tienen grupo |
| Oro | El piloto y los top 50 son subconjuntos del universo |
| Consolidado | Claves únicas, cero filas huérfanas y el piloto con las 500 |

Devuelve una lista de resultados y termina con código 1 si alguna falla, así
sirve igual en la terminal y en CI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import pandas as pd

from etl import config
from etl.common import leer_jsonl, log, sha256_archivo

OK = "ok"
AVISO = "aviso"
FALLA = "falla"
ESTADOS_URL = {"si", "manual", "revisar", "no_encontrada"}
ESTADOS_FICHA = {"completo", "parcial", "pendiente"}
MOTIVOS_ALERTA = {"imposible", "grande_menos_10", "fuera_de_rango_division"}


@dataclass
class Resultado:
    capa: str
    comprobacion: str
    estado: str
    detalle: str = ""


@dataclass
class Informe:
    resultados: list[Resultado] = field(default_factory=list)

    def anotar(self, capa: str, comprobacion: str, condicion: bool, detalle: str = "") -> None:
        self.resultados.append(Resultado(capa, comprobacion, OK if condicion else FALLA, detalle))

    def avisar(self, capa: str, comprobacion: str, detalle: str = "") -> None:
        self.resultados.append(Resultado(capa, comprobacion, AVISO, detalle))

    @property
    def fallas(self) -> list[Resultado]:
        return [r for r in self.resultados if r.estado == FALLA]

    @property
    def avisos(self) -> list[Resultado]:
        return [r for r in self.resultados if r.estado == AVISO]

    def tabla(self) -> pd.DataFrame:
        return pd.DataFrame([vars(r) for r in self.resultados])


def anios_con_plata() -> list[int]:
    if not config.PLATA.exists():
        return []
    return sorted(
        int(c.name)
        for c in config.PLATA.iterdir()
        if c.is_dir() and c.name.isdigit() and (c / "ranking.parquet").exists()
    )


def _crudo(informe: Informe) -> None:
    manifiesto = config.CRUDO / "MANIFEST.csv"
    if not manifiesto.exists():
        informe.anotar("crudo", "MANIFEST.csv existe", False, str(manifiesto))
        return
    registro = pd.read_csv(manifiesto)
    presentes, cambiados, ausentes = 0, [], []
    for fila in registro.itertuples():
        ruta = config.CRUDO / fila.archivo
        if not ruta.exists():
            ausentes.append(fila.archivo)
            continue
        presentes += 1
        if sha256_archivo(ruta) != fila.sha256:
            cambiados.append(fila.archivo)
    informe.anotar(
        "crudo",
        "los archivos presentes coinciden con su hash",
        not cambiados,
        f"{presentes} verificados" + (f"; cambiaron: {cambiados}" if cambiados else ""),
    )
    if ausentes:
        informe.avisar(
            "crudo",
            "archivos del MANIFEST que no están en disco",
            f"{len(ausentes)}: se recuperan con su url_origen",
        )
    sin_url = registro["url_origen"].isna().sum() if "url_origen" in registro else 0
    if sin_url:
        informe.avisar("crudo", "filas del MANIFEST sin url_origen", str(int(sin_url)))


def _html_capturado(informe: Informe, anio: int) -> None:
    carpeta = config.ruta_web(anio)
    registros = leer_jsonl(carpeta / "manifest.jsonl")
    if not registros:
        return
    guardadas = [r for r in registros if str(r.get("sha256", "")) != ""]
    faltan, distinto = [], []
    for r in guardadas:
        archivo = carpeta / f"{r['expediente']}_{r['sha256']}.html"
        if not archivo.exists():
            faltan.append(archivo.name)
        elif sha256_archivo(archivo) != r["sha256"]:
            distinto.append(archivo.name)
    informe.anotar(
        f"crudo {anio}",
        "cada página del manifiesto está en disco con su hash",
        not faltan and not distinto,
        f"{len(guardadas)} páginas"
        + (f"; faltan {len(faltan)}" if faltan else "")
        + (f"; hash distinto {distinto}" if distinto else ""),
    )
    omitidas = len(registros) - len(guardadas)
    if omitidas:
        informe.avisar(
            f"crudo {anio}", "páginas registradas sin guardar", f"{omitidas} (meta robots o error)"
        )


def _plata(informe: Informe, anio: int) -> pd.DataFrame:
    capa = f"plata {anio}"
    plata = pd.read_parquet(config.ruta_plata(anio) / "ranking.parquet")
    informe.anotar(capa, "el expediente es único", plata["expediente"].is_unique)

    calidad_ruta = config.ruta_plata(anio) / "calidad_ranking.json"
    if calidad_ruta.exists():
        calidad = json.loads(calidad_ruta.read_text())
        informe.anotar(
            capa,
            "el reporte de calidad coincide con el archivo",
            calidad["filas_plata"] == len(plata),
            f"reporte {calidad['filas_plata']:,} · archivo {len(plata):,}",
        )
        # crudo = idénticas + expedientes en conflicto + cuarentena + plata
        esperado = (
            calidad["filas_crudo"]
            - calidad["filas_identicas_quitadas"]
            - len(calidad["expedientes_con_conflicto"])
            - calidad["filas_descartadas"]
        )
        informe.anotar(
            capa,
            "las filas cuadran contra el archivo crudo",
            esperado == len(plata),
            f"crudo {calidad['filas_crudo']:,} − idénticas {calidad['filas_identicas_quitadas']}"
            f" − conflictos {len(calidad['expedientes_con_conflicto'])}"
            f" − cuarentena {calidad['filas_descartadas']} = {esperado:,}",
        )

    mal_ciiu = (~plata["ciiu"].str.match(r"^[A-U]\d{4}", na=False)).sum()
    informe.anotar(capa, "el CIIU tiene formato válido", mal_ciiu == 0, f"{mal_ciiu} inválidos")
    negativas = sum(int((plata[c] < 0).sum()) for c in ["empleados", "activo", "ventas"])
    informe.anotar(capa, "no hay cifras negativas donde no pueden serlo", negativas == 0)
    reportado = plata["ingreso_total"] > 0
    incoherentes = int((reportado & (plata["ventas"] > plata["ingreso_total"] + 1)).sum())
    informe.anotar(
        capa,
        "las ventas no superan el ingreso total reportado",
        incoherentes == 0,
        f"{incoherentes} filas",
    )
    cobertura = float((plata["ventas"] > 0).mean() * 100)
    if cobertura < config.COBERTURA_MINIMA_VENTAS:
        informe.avisar(
            capa,
            "cobertura de ventas insuficiente para delimitar",
            f"{cobertura:.1f} % — año no comparable",
        )
    return plata


def _oro(informe: Informe, anio: int, plata: pd.DataFrame) -> None:
    capa = f"oro {anio}"
    ruta = config.ruta_oro(anio) / "universo.parquet"
    if not ruta.exists():
        informe.avisar(capa, "sin capa oro", "ejecute `etl universo`")
        return
    universo = pd.read_parquet(ruta)
    informe.anotar(capa, "el expediente es único", universo["expediente"].is_unique)
    informe.anotar(
        capa,
        "el universo sale de la capa plata",
        universo["expediente"].isin(plata["expediente"]).all(),
    )
    informe.anotar(capa, "todas tienen grupo", universo["grupo"].notna().all())

    piloto_ruta = config.ruta_oro(anio) / "piloto.csv"
    if piloto_ruta.exists():
        piloto = pd.read_csv(piloto_ruta)
        informe.anotar(
            capa,
            "el piloto es subconjunto del universo",
            piloto["expediente"].isin(universo["expediente"]).all(),
            f"{piloto['expediente'].nunique()} empresas",
        )
    for grupo in config.GRUPOS:
        top_ruta = config.ruta_oro(anio) / f"top50_{grupo.lower()}.csv"
        if not top_ruta.exists():
            continue
        top = pd.read_csv(top_ruta)
        informe.anotar(
            capa,
            f"top 50 de {grupo} válido",
            len(top) <= config.TOP_N and top["expediente"].isin(universo["expediente"]).all(),
            f"{len(top)} filas",
        )


def _urls_y_ficha(informe: Informe, anio: int) -> None:
    capa = f"plata {anio}"
    urls_ruta = config.ruta_plata(anio) / "urls_piloto.csv"
    piloto_ruta = config.ruta_oro(anio) / "piloto.csv"
    if urls_ruta.exists() and piloto_ruta.exists():
        urls = pd.read_csv(urls_ruta)
        piloto = pd.read_csv(piloto_ruta)
        informe.anotar(
            capa,
            "las URL corresponden a empresas del piloto",
            urls["expediente"].isin(piloto["expediente"]).all(),
        )
        informe.anotar(capa, "una fila por empresa", urls["expediente"].is_unique)
        malos = set(urls["url_verificada"].dropna()) - ESTADOS_URL
        informe.anotar(capa, "los estados de URL son válidos", not malos, str(malos or ""))
        verificadas = urls[urls["url_verificada"].isin(("si", "manual"))]
        informe.anotar(
            capa,
            "toda URL verificada tiene dirección",
            verificadas["url_oficial"].notna().all(),
        )
        informe.avisar(
            capa,
            "avance de la búsqueda de webs",
            f"{len(urls)} de {piloto['expediente'].nunique()} del piloto; "
            f"verificadas {len(verificadas)}",
        )

    ficha_ruta = config.ruta_plata(anio) / "ficha_company_profile.csv"
    if ficha_ruta.exists():
        ficha = pd.read_csv(ficha_ruta)
        informe.anotar(capa, "la ficha tiene una fila por empresa", ficha["expediente"].is_unique)
        malos = set(ficha["estado"].dropna()) - ESTADOS_FICHA
        informe.anotar(capa, "los estados de la ficha son válidos", not malos, str(malos or ""))
        largo = ficha["tagline"].dropna().str.len()
        informe.anotar(
            capa,
            "el tagline no pasa de 150 caracteres",
            bool((largo <= 150).all()) if len(largo) else True,
        )
        personales = ficha["correo_corporativo"].dropna()
        genericos = (
            personales.str.split("; ")
            .explode()
            .str.match(
                r"^(info|ventas|contacto|comercial|servicioalcliente|atencionalcliente|hola|hello"
                r"|soporte|marketing|rrhh|talentohumano|recursoshumanos|administracion|gerencia"
                r"|secretaria)@"
            )
        )
        informe.anotar(
            capa,
            "solo hay correos corporativos (LOPDP)",
            bool(genericos.all()) if len(genericos) else True,
        )


def _consolidado(informe: Informe, requiere_consolidado: bool) -> None:
    capa = "consolidado"
    rutas = {
        "empresa": config.ORO / "empresa.parquet",
        "cifras": config.ORO / "cifras_anuales.parquet",
    }
    faltan = [ruta.name for ruta in rutas.values() if not ruta.exists()]
    if faltan:
        detalle = f"faltan {', '.join(faltan)}: ejecute `etl consolidar`"
        if requiere_consolidado or len(faltan) < len(rutas):
            informe.anotar(capa, "archivos del consolidado disponibles", False, detalle)
        else:
            informe.avisar(capa, "sin consolidar", detalle)
        return
    empresa = pd.read_parquet(rutas["empresa"])
    cifras = pd.read_parquet(rutas["cifras"])
    faltan_columnas = (
        {"expediente", "grupo", "en_piloto", "criterio_piloto", "en_top50_tec"} - set(empresa)
    ) | (
        {"expediente", "anio", "en_universo_ese_anio", "tiene_alerta", "motivo_alerta"}
        - set(cifras)
    )
    if faltan_columnas:
        informe.anotar(capa, "columnas del consolidado", False, ", ".join(sorted(faltan_columnas)))
        return

    clave = empresa["expediente"]
    informe.anotar(
        capa, "empresa: expediente único y no nulo", clave.is_unique and clave.notna().all()
    )
    informe.anotar(
        capa,
        "cifras_anuales: (expediente, anio) único",
        not cifras.duplicated(["expediente", "anio"]).any(),
    )
    informe.anotar(
        capa,
        "cifras_anuales no tiene filas huérfanas",
        cifras["expediente"].isin(empresa["expediente"]).all(),
    )

    universo_ruta = config.ruta_oro(config.ANIO_UNIVERSO) / "universo.parquet"
    if universo_ruta.exists():
        referencia = pd.read_parquet(universo_ruta, columns=["expediente"])
        informe.anotar(
            capa,
            f"empresa es el universo fijado en {config.ANIO_UNIVERSO}",
            set(empresa["expediente"]) == set(referencia["expediente"]),
            f"{len(empresa):,} empresas",
        )
    piloto = empresa["en_piloto"]
    top50 = empresa["en_top50_tec"]
    en_piloto = empresa.loc[piloto.eq(True), "expediente"].nunique()
    informe.anotar(capa, "el piloto tiene 500 empresas", en_piloto == 500, f"{en_piloto} empresas")
    informe.anotar(
        capa,
        "empresa: grupo, criterio del piloto y top 50 coherentes",
        empresa["grupo"].isin(config.GRUPOS).all()
        and _booleanos(piloto)
        and _booleanos(top50)
        and piloto.eq(empresa["criterio_piloto"].notna()).all()
        and piloto[top50.eq(True)].all(),
    )
    anios = cifras["anio"]
    anios_validos = (
        not cifras.empty
        and anios.isin(range(config.ANIO_MINIMO_COMPARABLE, config.ANIO_UNIVERSO + 1)).all()
    )
    informe.anotar(
        capa,
        "cifras_anuales: ejercicios fiscales válidos",
        anios_validos,
        f"{anios.min()}–{anios.max()}",
    )
    pertenencia = cifras["en_universo_ese_anio"]
    informe.anotar(capa, "pertenencia anual booleana y no nula", _booleanos(pertenencia))
    if anios_validos and _booleanos(pertenencia):
        for anio, filas in cifras.groupby("anio"):
            ruta = config.ruta_oro(int(anio)) / "universo.parquet"
            if not ruta.exists():
                informe.anotar(capa, f"universo anual disponible para {anio}", False)
                continue
            expedientes = pd.read_parquet(ruta, columns=["expediente"])["expediente"]
            esperada = filas["expediente"].isin(expedientes)
            informe.anotar(
                capa,
                f"pertenencia anual coincide con oro {anio}",
                filas["en_universo_ese_anio"].eq(esperada).all(),
            )
    alerta = cifras["tiene_alerta"]
    motivo = cifras["motivo_alerta"]
    informe.anotar(
        capa,
        "alerta de empleados y motivo coherentes",
        _booleanos(alerta)
        and motivo.dropna().isin(MOTIVOS_ALERTA).all()
        and alerta.eq(motivo.notna()).all(),
    )

    ficha_ruta = config.ORO / "ficha.csv"
    if ficha_ruta.exists():
        ficha = pd.read_csv(ficha_ruta)
        informe.anotar(
            capa,
            "la ficha corresponde a empresas del universo",
            ficha["expediente"].isin(empresa["expediente"]).all(),
            f"{len(ficha)} fichas",
        )


def _booleanos(valores: pd.Series) -> bool:
    return pd.api.types.is_bool_dtype(valores) and valores.notna().all()


def ejecutar(anio: int | None = None) -> Informe:
    informe = Informe()
    anios = [anio] if anio else anios_con_plata()
    if not anios:
        raise FileNotFoundError("No hay capa plata que verificar: ejecute antes `etl ranking`")

    _crudo(informe)
    for a in anios:
        plata = _plata(informe, a)
        _oro(informe, a, plata)
        _urls_y_ficha(informe, a)
        _html_capturado(informe, a)
    _consolidado(informe, requiere_consolidado=anio is None)

    tabla = informe.tabla()
    config.DATOS.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(config.DATOS / "verificacion.csv", index=False)
    conteo = tabla["estado"].value_counts().to_dict()
    log.info("Verificación: %s comprobaciones %s", len(tabla), conteo)
    for r in informe.fallas:
        log.error("FALLA  %s · %s · %s", r.capa, r.comprobacion, r.detalle)
    for r in informe.avisos:
        log.warning("aviso  %s · %s · %s", r.capa, r.comprobacion, r.detalle)
    return informe
