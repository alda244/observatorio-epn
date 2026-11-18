-- Esquema del Componente A. {dim} es la dimensión del modelo de embeddings
-- (1024 para BGE-M3); la ingesta la reemplaza al crear las tablas.

CREATE SCHEMA IF NOT EXISTS asistente;

CREATE TABLE IF NOT EXISTS asistente.indice (
    id        boolean PRIMARY KEY DEFAULT true CHECK (id),
    modelo    text    NOT NULL,
    dimension integer NOT NULL
);

CREATE TABLE IF NOT EXISTS asistente.fragmento (
    frag_id     text PRIMARY KEY,
    doc_id      text    NOT NULL,
    orden       integer NOT NULL,
    titulo      text    NOT NULL,
    texto       text    NOT NULL,
    fuente_url  text    NOT NULL,
    fuente_tipo text    NOT NULL,
    fecha       text    NOT NULL,
    origen      text    NOT NULL CHECK (origen IN ('literal', 'derivado')),
    sha256_doc  char(64) NOT NULL,
    metadatos   jsonb   NOT NULL DEFAULT '{}',
    embedding   vector({dim}) NOT NULL
);

CREATE INDEX IF NOT EXISTS fragmento_doc_id ON asistente.fragmento (doc_id);
CREATE INDEX IF NOT EXISTS fragmento_embedding ON asistente.fragmento
    USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS asistente.traza (
    traza_id          text PRIMARY KEY,
    fecha             timestamptz NOT NULL,
    pregunta          text NOT NULL,
    filtros           jsonb NOT NULL DEFAULT '{}',
    modelo_embeddings text NOT NULL,
    modelo_llm        text,
    modo              text NOT NULL CHECK (modo IN ('llm', 'extractivo', 'rechazo')),
    recuperados       jsonb NOT NULL,
    advertencias      jsonb NOT NULL DEFAULT '[]',
    latencia_ms       integer NOT NULL,
    tokens_entrada    integer,
    tokens_salida     integer,
    respuesta         text NOT NULL
);
