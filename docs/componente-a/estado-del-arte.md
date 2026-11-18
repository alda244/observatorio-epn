# Estado del arte

Base bibliográfica del asistente. Se usan trabajos de los últimos cinco años y, cuando definen una técnica, sus obras seminales.

## Ideas que sostienen el diseño

| Tema | Qué dice la literatura | Decisión en el asistente |
| --- | --- | --- |
| RAG | Recuperar documentos y generar a partir de ellos reduce respuestas sin fundamento y permite actualizar el conocimiento sin reentrenar el modelo [1], [9] | El LLM responde solo con los fragmentos recuperados |
| Recuperación densa | Los embeddings capturan significado más allá de las palabras exactas [2], [7] | Búsqueda por embeddings |
| Recuperación léxica | BM25 sigue siendo una base fuerte, sobre todo con nombres propios y términos raros [3], [6] | BM25 sobre el texto y sobre la razón social |
| Fusión | RRF combina rankings distintos sin calibrar sus puntajes [4] | Denso + BM25 + nombre con RRF |
| Embeddings multilingües | BGE-M3 cubre más de 100 idiomas y ofrece vectores densos y dispersos [8] | BGE-M3 en producción |
| Búsqueda vectorial | HNSW encuentra vecinos cercanos en tiempo sublineal con alta exhaustividad [5] | Índice HNSW en pgvector |
| Alucinaciones | Los LLM generan contenido plausible pero falso; el riesgo baja con recuperación y verificación [10] | Salvaguardas de respaldo y de campo pedido |
| Citas | Exigir y verificar citas mejora la trazabilidad de las respuestas [11], [12] | Respuesta descartada si no cita fuentes válidas |
| Contexto largo | Los modelos aprovechan peor la información en el medio de un contexto largo [13] | Solo 5 fragmentos por respuesta |
| Evaluación de RAG | RAGAS mide fidelidad, pertinencia y precisión del contexto sin respuestas de referencia escritas a mano [14] | RAGAS en el Sprint 3 |
| Usabilidad | SUS es una escala breve y validada; 68 es el promedio de referencia [15], [16] | SUS con al menos 30 usuarios |

## Referencias

[1] P. Lewis *et al.*, "Retrieval-augmented generation for knowledge-intensive NLP tasks," en *Proc. NeurIPS*, 2020. (Seminal)

[2] V. Karpukhin *et al.*, "Dense passage retrieval for open-domain question answering," en *Proc. EMNLP*, 2020. (Seminal)

[3] S. Robertson y H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Found. Trends Inf. Retr.*, vol. 3, no. 4, pp. 333–389, 2009. (Seminal)

[4] G. V. Cormack, C. L. A. Clarke y S. Büttcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," en *Proc. ACM SIGIR*, 2009. (Seminal)

[5] Y. A. Malkov y D. A. Yashunin, "Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 42, no. 4, pp. 824–836, 2020. (Seminal)

[6] N. Thakur *et al.*, "BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models," en *Proc. NeurIPS Datasets and Benchmarks*, 2021.

[7] N. Reimers e I. Gurevych, "Making monolingual sentence embeddings multilingual using knowledge distillation," en *Proc. EMNLP*, 2020. (Seminal)

[8] J. Chen *et al.*, "M3-Embedding: Multi-linguality, multi-functionality, multi-granularity text embeddings through self-knowledge distillation," en *Findings of ACL*, 2024.

[9] Y. Gao *et al.*, "Retrieval-augmented generation for large language models: A survey," arXiv:2312.10997, 2023.

[10] L. Huang *et al.*, "A survey on hallucination in large language models: Principles, taxonomy, challenges, and open questions," *ACM Trans. Inf. Syst.*, 2025.

[11] T. Gao, H. Yen, J. Yu y D. Chen, "Enabling large language models to generate text with citations," en *Proc. EMNLP*, 2023.

[12] A. Asai *et al.*, "Self-RAG: Learning to retrieve, generate, and critique through self-reflection," en *Proc. ICLR*, 2024.

[13] N. F. Liu *et al.*, "Lost in the middle: How language models use long contexts," *Trans. Assoc. Comput. Linguist.*, vol. 12, pp. 157–173, 2024.

[14] S. Es, J. James, L. Espinosa-Anke y S. Schockaert, "RAGAS: Automated evaluation of retrieval augmented generation," en *Proc. EACL: System Demonstrations*, 2024.

[15] J. Brooke, "SUS: A 'quick and dirty' usability scale," en *Usability Evaluation in Industry*, Taylor & Francis, 1996. (Seminal)

[16] A. Bangor, P. T. Kortum y J. T. Miller, "An empirical evaluation of the System Usability Scale," *Int. J. Hum.-Comput. Interact.*, vol. 24, no. 6, pp. 574–594, 2008. (Seminal)
