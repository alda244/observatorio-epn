"""Configuración del Componente A, leída de variables de entorno.

Toda decisión que cambia entre el prototipo y producción vive aquí, para que
cambiar de modelo o de proveedor sea cambiar una variable y no el código
(ADR 0004).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[3]


def _env(nombre: str, defecto: str) -> str:
    return os.environ.get(nombre, defecto)


@dataclass(frozen=True)
class Config:
    # Fuente de empresas: mientras no exista la API de B se usa su exportación
    # publicada (piloto_500.csv), con la misma forma que GET /empresas.
    fuente_empresas: Path = field(
        default_factory=lambda: Path(
            _env("RAG_FUENTE_EMPRESAS", str(RAIZ_REPO / "etl/datos/universo/2025/piloto_500.csv"))
        )
    )
    catalogo_ciiu: Path = field(
        default_factory=lambda: Path(
            _env("RAG_CATALOGO_CIIU", str(RAIZ_REPO / "etl/datos/crudo/2025/bi_ciiu.csv"))
        )
    )
    documentos: Path = field(
        default_factory=lambda: Path(_env("RAG_DOCUMENTOS", str(RAIZ_REPO / "rag/datos/documentos")))
    )
    indice: Path = field(
        default_factory=lambda: Path(_env("RAG_INDICE", str(RAIZ_REPO / "rag/datos/indice")))
    )
    trazas: Path = field(
        default_factory=lambda: Path(_env("RAG_TRAZAS", str(RAIZ_REPO / "rag/datos/trazas.jsonl")))
    )
    # Embeddings: "hash" es determinista y sin descargas (pruebas); cualquier
    # otro valor es un modelo de sentence-transformers.
    modelo_embeddings: str = field(
        default_factory=lambda: _env(
            "RAG_EMBEDDINGS", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    )
    palabras_por_fragmento: int = field(
        default_factory=lambda: int(_env("RAG_PALABRAS_FRAGMENTO", "350"))
    )
    solape_palabras: int = field(default_factory=lambda: int(_env("RAG_SOLAPE", "50")))
    top_k: int = field(default_factory=lambda: int(_env("RAG_TOP_K", "5")))
    # Salvaguarda de respaldo (calibrada con rag/evaluacion para el modelo del
    # prototipo; se recalibra con BGE-M3):
    # - umbral_similitud: coseno mínimo si hay coincidencia léxica;
    # - umbral_fuerte: coseno que basta sin coincidencia léxica.
    umbral_similitud: float = field(
        default_factory=lambda: float(_env("RAG_UMBRAL_SIMILITUD", "0.30"))
    )
    umbral_fuerte: float = field(default_factory=lambda: float(_env("RAG_UMBRAL_FUERTE", "0.65")))
    # LLM opcional, compatible con la API de OpenAI (Bedrock, OpenAI, Gemini, Ollama).
    llm_base_url: str = field(default_factory=lambda: _env("RAG_LLM_BASE_URL", ""))
    llm_modelo: str = field(default_factory=lambda: _env("RAG_LLM_MODELO", ""))
    llm_api_key: str = field(default_factory=lambda: _env("RAG_LLM_API_KEY", ""))

    @property
    def llm_activo(self) -> bool:
        return bool(self.llm_base_url and self.llm_modelo)
