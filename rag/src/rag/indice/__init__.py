"""Índice: fragmentación, embeddings y almacén vectorial.

El prototipo guarda el índice en archivos (``vectores.npy`` +
``fragmentos.jsonl``). La interfaz ``Almacen`` es la misma que implementará
el almacén pgvector del esquema ``asistente`` (ADR 0002), de modo que el
motor no cambia al migrar.
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


class AlmacenLocal:
    """Almacén en archivos; equivalente funcional de la tabla ``asistente.fragmento``."""

    def __init__(self, carpeta: Path, modelo: str) -> None:
        self.carpeta = Path(carpeta)
        self.modelo = modelo
        self._frag: list[Fragmento] = []
        self._vec = np.zeros((0, 0), dtype=np.float32)
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
