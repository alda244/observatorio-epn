"""Índice: fragmentación, embeddings y almacén vectorial.

Hay dos almacenes con la misma interfaz ``Almacen``:

- ``AlmacenLocal``: archivos (``vectores.npy`` + ``fragmentos.jsonl``), para
  desarrollo sin base de datos.
- ``AlmacenPgvector``: tabla ``asistente.fragmento`` en PostgreSQL con
  pgvector (ADR 0002). Se elige con ``RAG_ALMACEN=pgvector``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from rag.ingesta import Documento


@dataclass
class Fragmento:
    frag_id: str
    doc_id: str
    orden: int
    titulo: str
    texto: str
    fuente_url: str
    fuente_tipo: str
    fecha: str
    origen: str
    sha256_doc: str
    metadatos: dict


def fragmentar(doc: Documento, palabras: int = 350, solape: int = 50) -> list[Fragmento]:
    """Ventanas de ``palabras`` con ``solape``; respeta párrafos cuando caben."""
    if solape >= palabras:
        raise ValueError("el solape debe ser menor que el tamaño del fragmento")
    tokens = doc.texto.split()
    if not tokens:
        return []
    ventanas: list[str] = []
    inicio = 0
    while inicio < len(tokens):
        fin = min(inicio + palabras, len(tokens))
        ventanas.append(" ".join(tokens[inicio:fin]))
        if fin == len(tokens):
            break
        inicio = fin - solape
    # Una ficha corta conserva sus saltos de línea (más legible al citar).
    if len(ventanas) == 1:
        ventanas = [doc.texto]
    sha = doc.sha256
    return [
        Fragmento(
            frag_id=f"{doc.doc_id}#{i}",
            doc_id=doc.doc_id,
            orden=i,
            titulo=doc.titulo,
            texto=t,
            fuente_url=doc.fuente_url,
            fuente_tipo=doc.fuente_tipo,
            fecha=doc.fecha,
            origen=doc.origen,
            sha256_doc=sha,
            metadatos=doc.metadatos,
        )
        for i, t in enumerate(ventanas)
    ]


# ---------------------------------------------------------------- embeddings


class Embedder(Protocol):
    nombre: str
    dimension: int

    def codificar(self, textos: list[str]) -> np.ndarray: ...


class EmbedderHash:
    """Embedding determinista por hashing de palabras y trigramas.

    No captura significado; sirve para pruebas automáticas sin descargar
    modelos y como línea base léxica en la evaluación.
    """

    def __init__(self, dimension: int = 512) -> None:
        self.nombre = f"hash-{dimension}"
        self.dimension = dimension

    def _rasgos(self, texto: str) -> list[str]:
        palabras = re.findall(r"\w+", texto.lower())
        tri = [p[i : i + 3] for p in palabras for i in range(max(1, len(p) - 2))]
        return palabras + tri

    def codificar(self, textos: list[str]) -> np.ndarray:
        m = np.zeros((len(textos), self.dimension), dtype=np.float32)
        for i, t in enumerate(textos):
            for r in self._rasgos(t):
                h = int.from_bytes(hashlib.md5(r.encode()).digest()[:4], "little")
                m[i, h % self.dimension] += 1.0
        normas = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.where(normas == 0, 1, normas)


class EmbedderST:
    """Modelo de sentence-transformers (BGE-M3 en producción)."""

    def __init__(self, modelo: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.nombre = modelo
        self._m = SentenceTransformer(modelo, device="cpu")
        self.dimension = int(self._m.get_sentence_embedding_dimension())

    def codificar(self, textos: list[str]) -> np.ndarray:
        v = self._m.encode(textos, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(v, dtype=np.float32)


def crear_embedder(nombre: str) -> Embedder:
    if nombre.startswith("hash"):
        partes = nombre.split("-")
        return EmbedderHash(int(partes[1]) if len(partes) > 1 else 512)
    return EmbedderST(nombre)


# ------------------------------------------------------------------- almacén


class Almacen(Protocol):
    def hashes(self) -> dict[str, str]: ...

    def reemplazar(self, doc_ids: set[str], fragmentos: list[Fragmento], vectores: np.ndarray) -> None: ...

    def eliminar(self, doc_ids: set[str]) -> None: ...

    def todo(self) -> tuple[list[Fragmento], np.ndarray]: ...

    def guardar(self) -> None: ...

    def vaciar(self) -> None: ...


class AlmacenLocal:
    """Almacén en archivos; equivalente funcional de la tabla ``asistente.fragmento``."""

    def __init__(self, carpeta: Path, modelo: str, vaciar: bool = False) -> None:
        self.carpeta = Path(carpeta)
        self.modelo = modelo
        self._frag: list[Fragmento] = []
        self._vec = np.zeros((0, 0), dtype=np.float32)
        if vaciar:
            self.vaciar()
        meta = self.carpeta / "indice.json"
        if meta.exists():
            info = json.loads(meta.read_text(encoding="utf-8"))
            if info.get("modelo") != modelo:
                raise ValueError(
                    f"El índice se construyó con '{info.get('modelo')}' y se pidió '{modelo}'. "
                    "Use --reconstruir."
                )
            with (self.carpeta / "fragmentos.jsonl").open(encoding="utf-8") as f:
                self._frag = [Fragmento(**json.loads(linea)) for linea in f]
            self._vec = np.load(self.carpeta / "vectores.npy")

    def hashes(self) -> dict[str, str]:
        return {f.doc_id: f.sha256_doc for f in self._frag}

    def eliminar(self, doc_ids: set[str]) -> None:
        if not doc_ids or not self._frag:
            return
        keep = [i for i, f in enumerate(self._frag) if f.doc_id not in doc_ids]
        self._frag = [self._frag[i] for i in keep]
        self._vec = self._vec[keep] if keep else np.zeros((0, self._vec.shape[1]), dtype=np.float32)

    def reemplazar(self, doc_ids: set[str], fragmentos: list[Fragmento], vectores: np.ndarray) -> None:
        self.eliminar(doc_ids)
        if not fragmentos:
            return
        self._frag.extend(fragmentos)
        self._vec = vectores if self._vec.size == 0 else np.vstack([self._vec, vectores])

    def todo(self) -> tuple[list[Fragmento], np.ndarray]:
        return self._frag, self._vec

    def vaciar(self) -> None:
        for nombre in ("indice.json", "fragmentos.jsonl", "vectores.npy"):
            (self.carpeta / nombre).unlink(missing_ok=True)
        self._frag, self._vec = [], np.zeros((0, 0), dtype=np.float32)

    def guardar(self) -> None:
        self.carpeta.mkdir(parents=True, exist_ok=True)
        with (self.carpeta / "fragmentos.jsonl").open("w", encoding="utf-8") as f:
            for fr in self._frag:
                f.write(json.dumps(asdict(fr), ensure_ascii=False) + "\n")
        np.save(self.carpeta / "vectores.npy", self._vec)
        (self.carpeta / "indice.json").write_text(
            json.dumps(
                {"modelo": self.modelo, "fragmentos": len(self._frag), "documentos": len(self.hashes())},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


ESQUEMA_SQL = Path(__file__).resolve().parents[3] / "migraciones" / "001_asistente.sql"
_COLUMNAS = ("frag_id", "doc_id", "orden", "titulo", "texto", "fuente_url", "fuente_tipo", "fecha",
             "origen", "sha256_doc", "metadatos")


def _vector_sql(v: np.ndarray) -> str:
    return "[" + ",".join(f"{x:.7g}" for x in v) + "]"


class AlmacenPgvector:
    """Almacén en ``asistente.fragmento`` (PostgreSQL + pgvector).

    Las tablas se crean en la primera ingesta, con la dimensión del modelo.
    Los cambios quedan en una transacción hasta ``guardar()``.
    """

    def __init__(self, dsn: str, modelo: str, vaciar: bool = False) -> None:
        import psycopg

        self.modelo = modelo
        self.con = psycopg.connect(dsn)
        self.dimension: int | None = None
        if vaciar:
            self.vaciar()
        existe = self.con.execute("SELECT to_regclass('asistente.indice') IS NOT NULL").fetchone()[0]
        if existe:
            fila = self.con.execute("SELECT modelo, dimension FROM asistente.indice").fetchone()
            if fila:
                if fila[0] != modelo:
                    raise ValueError(
                        f"El índice se construyó con '{fila[0]}' y se pidió '{modelo}'. Use --reconstruir."
                    )
                self.dimension = fila[1]

    def _crear(self, dimension: int) -> None:
        if not self.con.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone():
            raise RuntimeError("La base no tiene la extensión pgvector. Un administrador debe ejecutar: "
                               "CREATE EXTENSION vector;")
        self.con.execute(ESQUEMA_SQL.read_text(encoding="utf-8").replace("{dim}", str(dimension)))
        self.con.execute(
            "INSERT INTO asistente.indice (modelo, dimension) VALUES (%s, %s) "
            "ON CONFLICT (id) DO UPDATE SET modelo = EXCLUDED.modelo, dimension = EXCLUDED.dimension",
            (self.modelo, dimension),
        )
        self.dimension = dimension

    def hashes(self) -> dict[str, str]:
        if self.dimension is None:
            return {}
        return dict(self.con.execute("SELECT DISTINCT doc_id, sha256_doc FROM asistente.fragmento").fetchall())

    def eliminar(self, doc_ids: set[str]) -> None:
        if doc_ids and self.dimension is not None:
            self.con.execute("DELETE FROM asistente.fragmento WHERE doc_id = ANY(%s)", (list(doc_ids),))

    def reemplazar(self, doc_ids: set[str], fragmentos: list[Fragmento], vectores: np.ndarray) -> None:
        if not fragmentos:
            self.eliminar(doc_ids)
            return
        if self.dimension is None:
            self._crear(int(vectores.shape[1]))
        self.eliminar(doc_ids)
        with self.con.cursor() as cur:
            cur.executemany(
                f"INSERT INTO asistente.fragmento ({', '.join(_COLUMNAS)}, embedding) "
                f"VALUES ({', '.join(['%s'] * len(_COLUMNAS))}, %s::vector)",
                [
                    (*(json.dumps(v, ensure_ascii=False) if k == "metadatos" else v
                       for k, v in asdict(f).items()), _vector_sql(vec))
                    for f, vec in zip(fragmentos, vectores, strict=True)
                ],
            )

    def todo(self) -> tuple[list[Fragmento], np.ndarray]:
        if self.dimension is None:
            return [], np.zeros((0, 0), dtype=np.float32)
        filas = self.con.execute(
            f"SELECT {', '.join(_COLUMNAS)}, embedding::real[] FROM asistente.fragmento ORDER BY doc_id, orden"
        ).fetchall()
        frag = [Fragmento(*f[:-1]) for f in filas]
        return frag, np.array([f[-1] for f in filas], dtype=np.float32).reshape(len(filas), self.dimension)

    def buscar(self, vector: np.ndarray, k: int = 5) -> list[tuple[str, float]]:
        """Vecinos más cercanos con el índice HNSW: (frag_id, coseno)."""
        return self.con.execute(
            "SELECT frag_id, 1 - (embedding <=> %s::vector) FROM asistente.fragmento "
            "ORDER BY embedding <=> %s::vector LIMIT %s",
            (_vector_sql(vector), _vector_sql(vector), k),
        ).fetchall()

    def registrar_traza(self, t: dict) -> None:
        self.con.execute(
            "INSERT INTO asistente.traza (traza_id, fecha, pregunta, filtros, modelo_embeddings, modelo_llm, "
            "modo, recuperados, advertencias, latencia_ms, tokens_entrada, tokens_salida, respuesta) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (t["traza_id"], t["fecha"], t["pregunta"], json.dumps(t["filtros"], ensure_ascii=False),
             t["modelo_embeddings"], t["modelo_llm"], t["modo"],
             json.dumps(t["recuperados"], ensure_ascii=False), json.dumps(t["advertencias"], ensure_ascii=False),
             t["latencia_ms"], t.get("tokens_entrada"), t.get("tokens_salida"), t["respuesta"]),
        )
        self.con.commit()

    def vaciar(self) -> None:
        self.con.execute("DROP TABLE IF EXISTS asistente.fragmento, asistente.indice")
        self.con.commit()
        self.dimension = None

    def guardar(self) -> None:
        self.con.commit()


def crear_almacen(cfg, vaciar: bool = False) -> Almacen:
    """Almacén según ``cfg.almacen``; ``vaciar`` borra el índice antes de abrirlo."""
    if cfg.almacen == "pgvector":
        if not cfg.pg_dsn:
            raise ValueError("RAG_ALMACEN=pgvector requiere RAG_PG_DSN")
        return AlmacenPgvector(cfg.pg_dsn, cfg.modelo_embeddings, vaciar)
    return AlmacenLocal(cfg.indice, cfg.modelo_embeddings, vaciar)
