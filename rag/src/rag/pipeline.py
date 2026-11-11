"""Pipeline de ingesta: fuentes → documentos → fragmentos → embeddings → índice.

Es idempotente: un documento cuyo ``sha256`` no cambió no se vuelve a
procesar, y un documento que desapareció de las fuentes se elimina del
índice. Cada corrida deja un reporte en ``<indice>/corridas.jsonl``.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from rag.cliente_b import ClienteBArchivo
from rag.config import Config
from rag.indice import AlmacenLocal, crear_embedder, fragmentar
from rag.ingesta import Documento, cargar_catalogo_ciiu, cargar_documentos, ficha_identificacion


@dataclass
class ReporteIngesta:
    fecha: str
    modelo: str
    documentos_fuente: int
    nuevos: int
    actualizados: int
    sin_cambios: int
    eliminados: int
    fragmentos_indexados: int
    fragmentos_totales: int
    segundos: float


def recolectar(cfg: Config) -> list[Documento]:
    ciiu = cargar_catalogo_ciiu(cfg.catalogo_ciiu)
    docs = [ficha_identificacion(e, ciiu) for e in ClienteBArchivo(cfg.fuente_empresas).empresas()]
    docs += cargar_documentos(cfg.documentos)
    ids = [d.doc_id for d in docs]
    if len(ids) != len(set(ids)):
        raise ValueError("Hay doc_id repetidos en las fuentes")
    return docs


def ingerir(cfg: Config, reconstruir: bool = False) -> ReporteIngesta:
    t0 = time.perf_counter()
    if reconstruir:
        for nombre in ("indice.json", "fragmentos.jsonl", "vectores.npy"):
            (cfg.indice / nombre).unlink(missing_ok=True)
    almacen = AlmacenLocal(cfg.indice, cfg.modelo_embeddings)
    previos = almacen.hashes()
    docs = recolectar(cfg)

    actuales = {d.doc_id for d in docs}
    eliminados = set(previos) - actuales
    cambiados = [d for d in docs if previos.get(d.doc_id) != d.sha256]
    nuevos = sum(1 for d in cambiados if d.doc_id not in previos)

    fragmentos = [
        f for d in cambiados for f in fragmentar(d, cfg.palabras_por_fragmento, cfg.solape_palabras)
    ]
    almacen.eliminar(eliminados)
    if fragmentos:
        embedder = crear_embedder(cfg.modelo_embeddings)
        vectores = embedder.codificar([f"{f.titulo}\n{f.texto}" for f in fragmentos])
        almacen.reemplazar({d.doc_id for d in cambiados}, fragmentos, vectores)
    almacen.guardar()

    reporte = ReporteIngesta(
        fecha=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        modelo=cfg.modelo_embeddings,
        documentos_fuente=len(docs),
        nuevos=nuevos,
        actualizados=len(cambiados) - nuevos,
        sin_cambios=len(docs) - len(cambiados),
        eliminados=len(eliminados),
        fragmentos_indexados=len(fragmentos),
        fragmentos_totales=len(almacen.todo()[0]),
        segundos=round(time.perf_counter() - t0, 2),
    )
    with (cfg.indice / "corridas.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(reporte), ensure_ascii=False) + "\n")
    return reporte
