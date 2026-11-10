"""Motor RAG: recuperación híbrida, salvaguardas, generación con cita y traza.

Flujo de ``Motor.responder``:

1. Recuperación densa (coseno sobre embeddings), léxica (BM25 sobre el texto)
   y por nombre (BM25 sobre la razón social), fusionadas con *Reciprocal Rank
   Fusion*. Filtros por metadatos: explícitos o implícitos (una ciudad o
   provincia del corpus mencionada en la pregunta).
2. Salvaguarda de respaldo: se responde solo si el mejor coseno supera
   ``umbral_fuerte``, o si supera ``umbral_similitud`` y además algún
   término de la pregunta aparece en los fragmentos recuperados. Si no, se
   responde "no hay dato publicado".
3. Generación: con LLM configurado, se le entrega solo el contexto numerado y
   se exige citar ``[n]``; si la respuesta no cita o cita fuera de rango, se
   descarta y se usa la respuesta extractiva. Sin LLM, la respuesta es
   extractiva (lista de fichas con su cita).
4. Cifras: se toman de la API de B (nunca del texto indexado), con la
   advertencia de calidad del dato de empleados cuando corresponde.
5. Traza: cada respuesta se registra en ``trazas.jsonl``.
"""

from __future__ import annotations

import json
import math
import re
import time
import unicodedata
import urllib.request
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np

from rag.cliente_b import ClienteB, ClienteBArchivo
from rag.config import Config
from rag.indice import AlmacenLocal, Embedder, Fragmento, crear_embedder

SIN_DATO = "No hay dato publicado en las fuentes del Observatorio para responder esa pregunta."
RE_CIFRAS = re.compile(r"vend|venta|factur|ingres|utilidad|ganan|patrimonio|activo|emplead|trabajador", re.I)
RE_EMPLEADOS = re.compile(r"emplead|trabajador|personal", re.I)
STOP = set(
    "a al de del el la las los lo un una unos unas y o en por para con sin que qué cual cuál "
    "cuales cuáles es son hay se su sus como cómo donde dónde quien quién quienes me mi "
    "empresa empresas compañía compañías".split()
)


def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def tokens(texto: str) -> list[str]:
    return [p for p in re.findall(r"\w+", _sin_tildes(texto.lower())) if p not in STOP and len(p) > 1]


class BM25:
    def __init__(self, textos: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs = [Counter(tokens(t)) for t in textos]
        self.largos = np.array([sum(d.values()) for d in self.docs], dtype=np.float32)
        self.prom = float(self.largos.mean()) if len(self.docs) else 0.0
        df = Counter(t for d in self.docs for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def puntuar(self, consulta: str) -> np.ndarray:
        q = tokens(consulta)
        s = np.zeros(len(self.docs), dtype=np.float32)
        for i, d in enumerate(self.docs):
            norm = self.k1 * (1 - self.b + self.b * self.largos[i] / (self.prom or 1))
            for t in q:
                tf = d.get(t)
                if tf:
                    s[i] += self.idf[t] * tf * (self.k1 + 1) / (tf + norm)
        return s


@dataclass
class Resultado:
    fragmento: Fragmento
    coseno: float
    bm25: float
    rrf: float


@dataclass
class Respuesta:
    traza_id: str
    pregunta: str
    respuesta: str
    modo: str  # llm | extractivo | rechazo
    citas: list[dict] = field(default_factory=list)
    cifras: list[dict] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    latencia_ms: int = 0


def _usd(v: float) -> str:
    return f"USD {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Motor:
    def __init__(self, cfg: Config, embedder: Embedder | None = None, cliente_b: ClienteB | None = None) -> None:
        self.cfg = cfg
        self.almacen = AlmacenLocal(cfg.indice, cfg.modelo_embeddings)
        self.frag, self.vec = self.almacen.todo()
        if not self.frag:
            raise RuntimeError("El índice está vacío; ejecute primero la ingesta.")
        self.embedder = embedder or crear_embedder(cfg.modelo_embeddings)
        self.bm25 = BM25([f"{f.titulo} {f.texto}" for f in self.frag])
        self.bm25_nombre = BM25([f.titulo for f in self.frag])
        self.cliente_b = cliente_b or ClienteBArchivo(cfg.fuente_empresas)
        self.lugares = self._lugares()

    def _lugares(self) -> dict[str, tuple[str, str]]:
        """Nombre normalizado de ciudad/provincia -> (clave de metadato, valor)."""
        out: dict[str, tuple[str, str]] = {}
        for clave in ("provincia", "ciudad"):  # ciudad sobrescribe si coincide
            for f in self.frag:
                v = str(f.metadatos.get(clave, "")).strip()
                if len(v) > 3 and "(" not in v:
                    out[" ".join(tokens(v))] = (clave, v)
        return out

    def filtros_implicitos(self, pregunta: str) -> dict:
        q = " " + " ".join(tokens(pregunta)) + " "
        hallados = [(n, cv) for n, cv in self.lugares.items() if n and f" {n} " in q]
        if not hallados:
            return {}
        _, (clave, valor) = max(hallados, key=lambda x: len(x[0]))
        return {clave: valor}

    # ------------------------------------------------------------ recuperar
    def recuperar(self, pregunta: str, k: int | None = None, filtros: dict | None = None) -> list[Resultado]:
        k = k or self.cfg.top_k
        mask = np.ones(len(self.frag), dtype=bool)
        for clave, valor in (filtros or {}).items():
            v = _sin_tildes(str(valor).upper())
            mask &= np.array([_sin_tildes(str(f.metadatos.get(clave, "")).upper()) == v for f in self.frag])
        if not mask.any():
            return []
        q = self.embedder.codificar([pregunta])[0]
        cos = self.vec @ q
        lex = self.bm25.puntuar(pregunta)
        nom = self.bm25_nombre.puntuar(pregunta)
        idx = np.flatnonzero(mask)
        rrf: dict[int, float] = {}
        for puntaje, exigir_positivo in ((cos, False), (lex, True), (nom, True)):
            for rango, i in enumerate(idx[np.argsort(-puntaje[idx])][:50]):
                if exigir_positivo and puntaje[i] <= 0:
                    break
                rrf[int(i)] = rrf.get(int(i), 0) + 1 / (60 + rango)
        mejores = sorted(rrf, key=rrf.get, reverse=True)[:k]
        return [Resultado(self.frag[i], float(cos[i]), float(lex[i]), rrf[i]) for i in mejores]

    # ------------------------------------------------------------ responder
    def responder(self, pregunta: str, filtros: dict | None = None) -> Respuesta:
        t0 = time.perf_counter()
        traza_id = uuid.uuid4().hex[:12]
        if filtros is None:
            implicitos = self.filtros_implicitos(pregunta)
            if implicitos and self.recuperar(pregunta, k=1, filtros=implicitos):
                filtros = implicitos
        resultados = self.recuperar(pregunta, filtros=filtros)
        mejor = max((r.coseno for r in resultados), default=0.0)
        apoyo_lexico = any(r.bm25 > 0 for r in resultados)
        respaldada = mejor >= self.cfg.umbral_fuerte or (mejor >= self.cfg.umbral_similitud and apoyo_lexico)

        if not resultados or not respaldada:
            motivo = (f"sin respaldo: coseno máximo {mejor:.2f} (fuerte ≥ {self.cfg.umbral_fuerte:.2f}), "
                      f"coincidencia léxica: {'sí' if apoyo_lexico else 'no'}")
            r = Respuesta(traza_id, pregunta, SIN_DATO, "rechazo", advertencias=[motivo])
            return self._cerrar(r, resultados, t0, filtros)

        citas = [
            {
                "n": n,
                "titulo": r.fragmento.titulo,
                "fuente_url": r.fragmento.fuente_url,
                "fuente_tipo": r.fragmento.fuente_tipo,
                "fecha": r.fragmento.fecha,
                "origen": r.fragmento.origen,
                "frag_id": r.fragmento.frag_id,
            }
            for n, r in enumerate(resultados, 1)
        ]
        cifras, advertencias = self._cifras(pregunta, resultados)

        modo, texto = "extractivo", self._extractiva(resultados, cifras)
        if self.cfg.llm_activo:
            try:
                generado = self._llm(pregunta, resultados, cifras)
                if self._citas_validas(generado, len(resultados)):
                    modo, texto = "llm", generado
                else:
                    advertencias.append("respuesta del LLM descartada: sin citas válidas")
            except Exception as e:  # noqa: BLE001 - se degrada a extractivo
                advertencias.append(f"LLM no disponible: {type(e).__name__}")

        r = Respuesta(traza_id, pregunta, texto, modo, citas, cifras, advertencias)
        return self._cerrar(r, resultados, t0, filtros)

    def _cifras(self, pregunta: str, resultados: list[Resultado]) -> tuple[list[dict], list[str]]:
        if not RE_CIFRAS.search(pregunta):
            return [], []
        cifras, adv = [], []
        pide_empleados = bool(RE_EMPLEADOS.search(pregunta))
        vistos = set()
        for n, r in enumerate(resultados, 1):
            exp = r.fragmento.metadatos.get("expediente")
            if not exp or exp in vistos:
                continue
            vistos.add(exp)
            e = self.cliente_b.empresa(exp)
            if not e:
                continue
            c = {"n": n, "expediente": exp, "nombre": e["nombre"], "ventas_2025": e["ventas"],
                 "fuente": "API de B (ranking SCVS 2025)", "fecha_corte": e["fecha_corte"]}
            if pide_empleados:
                c["empleados_declarados"] = int(e["empleados"])
                if e.get("alerta_empleados"):
                    adv.append(
                        f"{e['nombre']}: declara {int(e['empleados'])} empleados con ventas de "
                        f"{_usd(e['ventas'])}; el dato de empleados de la SCVS es inconsistente en este caso."
                    )
            cifras.append(c)
        return cifras, adv

    def _extractiva(self, resultados: list[Resultado], cifras: list[dict]) -> str:
        por_n = {c["n"]: c for c in cifras}
        lineas = ["Según las fuentes del Observatorio:"]
        for n, r in enumerate(resultados, 1):
            act = next((ln for ln in r.fragmento.texto.splitlines() if ln.startswith("Actividad principal")), "")
            act = act.split(": ", 1)[-1].rstrip(".") if act else r.fragmento.texto[:160]
            ubic = r.fragmento.metadatos.get("ciudad", "")
            linea = f"- {r.fragmento.titulo}: {act}" + (f" ({ubic.title()})" if ubic else "") + f" [{n}]"
            if n in por_n:
                linea += f". Ventas 2025: {_usd(por_n[n]['ventas_2025'])}"
                if "empleados_declarados" in por_n[n]:
                    linea += f"; empleados declarados: {por_n[n]['empleados_declarados']}"
            lineas.append(linea)
        return "\n".join(lineas)

    def _llm(self, pregunta: str, resultados: list[Resultado], cifras: list[dict]) -> str:
        contexto = "\n\n".join(f"[{n}] {r.fragmento.titulo}\n{r.fragmento.texto}" for n, r in enumerate(resultados, 1))
        if cifras:
            contexto += "\n\nCifras oficiales (API de B, SCVS 2025):\n" + "\n".join(
                f"[{c['n']}] {c['nombre']}: ventas {_usd(c['ventas_2025'])}"
                + (f", empleados declarados {c['empleados_declarados']}" if "empleados_declarados" in c else "")
                for c in cifras
            )
        sistema = (
            "Eres el asistente del Observatorio EPN. Responde en español, solo con la información del "
            "contexto. Cada afirmación lleva su cita [n]. Si el contexto no responde la pregunta, di "
            f"exactamente: \"{SIN_DATO}\". No inventes cifras."
        )
        cuerpo = json.dumps({
            "model": self.cfg.llm_modelo,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"},
            ],
        }).encode()
        req = urllib.request.Request(
            self.cfg.llm_base_url.rstrip("/") + "/chat/completions",
            data=cuerpo,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.cfg.llm_api_key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _citas_validas(texto: str, n: int) -> bool:
        if texto.strip() == SIN_DATO:
            return True
        citas = {int(x) for x in re.findall(r"\[(\d+)\]", texto)}
        return bool(citas) and all(1 <= c <= n for c in citas)

    def _cerrar(self, r: Respuesta, resultados: list[Resultado], t0: float, filtros: dict | None) -> Respuesta:
        r.latencia_ms = int((time.perf_counter() - t0) * 1000)
        traza = {
            "traza_id": r.traza_id,
            "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pregunta": r.pregunta,
            "filtros": filtros or {},
            "modelo_embeddings": self.cfg.modelo_embeddings,
            "modelo_llm": self.cfg.llm_modelo if self.cfg.llm_activo else None,
            "modo": r.modo,
            "recuperados": [
                {"frag_id": x.fragmento.frag_id, "coseno": round(x.coseno, 4), "bm25": round(x.bm25, 3),
                 "rrf": round(x.rrf, 5)}
                for x in resultados
            ],
            "advertencias": r.advertencias,
            "latencia_ms": r.latencia_ms,
            "respuesta": r.respuesta,
        }
        self.cfg.trazas.parent.mkdir(parents=True, exist_ok=True)
        with self.cfg.trazas.open("a", encoding="utf-8") as f:
            f.write(json.dumps(traza, ensure_ascii=False) + "\n")
        return r


def a_dict(r: Respuesta) -> dict:
    return asdict(r)
