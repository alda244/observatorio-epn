# 9. Antecedentes del mismo director: Reinoso y Data Hub EPN

Dos trabajos dirigidos por Andrés Larco sirven de base: la tesis de maestría de Paúl Reinoso (fuentes y ETL de la SCVS y el BCE) y el proyecto Data Hub EPN (método de trabajo, estructura de la memoria y stack).

## Reinoso (2025): clasificación de empresas por rentabilidad

Reinoso Almeida, P. A. (2025). *Modelo de clasificación de empresas según su rentabilidad y rama económica utilizando técnicas de aprendizaje de máquina en el sector societario del Ecuador* [Tesis de maestría, EPN]. [bibdigital.epn.edu.ec/handle/15000/26730](https://bibdigital.epn.edu.ec/handle/15000/26730)

| Aspecto | Hallazgo | Implicación para el proyecto | Componente |
| --- | --- | --- | --- |
| Fuente SCVS | Estados financieros por ramo, archivos anuales `Balances_AAAA_n` + `catalogo_AAAA_n` en el Portal de Información ([SCVS](https://appscvsgen.supercias.gob.ec/consultaCompanias/societario/estadosFinancierosPorRamo.jsf)) | Ruta de descarga probada; complementa el ranking de [01](01-fuente-scvs.md) | B |
| Periodo | 2017–2023; 688.549 registros tras unificar | Cifra de referencia para validar la carga de B | B |
| Formatos cambiantes | 6 archivos con 622–925 columnas en 2017; solo 2 en 2023. Las columnas traen el código contable, no el nombre | El ETL necesita un mapeo de cuentas por año; confirma el riesgo de 2022 anotado en [03](03-periodo-de-analisis.md) | B |
| Variables | 7 de identificación (año, RUC, razón social, expediente, rama, descripción, CIIU) y 23 financieras (activo, pasivo, patrimonio, ingresos, costos, utilidad, impuesto) | Base para el contrato `/empresas/{expediente}` e `/indicadores` | A + B |
| Fuente BCE | Cuentas Nacionales Trimestrales: VAB por industria, variación anual, 20 sectores ([BCE](https://contenido.bce.fin.ec/documentos/informacioneconomica/cuentasnacionales/ix_cuentasnacionalestrimestrales.html)) | Contexto macro por sector para las respuestas del asistente | B |
| Límite BCE | Algunas industrias vienen agregadas sin nota que aclare qué incluyen | Tabla de correspondencia CIIU ↔ industria BCE, con advertencia en lo ambiguo | B |
| Modelos | Altman Z'' y un coeficiente propio (CAR); redes neuronales superan a SVC y árbol de decisión | Altman está sesgado para Ecuador; si B lo expone, el asistente debe citarlo con esa advertencia | A + B |
| Despliegue | Prototipo local en Streamlit | El Observatorio es su "trabajo futuro": monitoreo sectorial visible a interesados | — |
| Recomendación | Filtrar por rama, ubicación o empleados para no perder registros | Coincide con delimitar por sector ([02](02-sectores-y-tamanos.md)) | A + B |

Insumos a pedir: notebooks `Modelo Altman Zpr.ipynb`, `Modelo CAR.ipynb`, `Rentabilidad_Altman_Zpr.py` y las tablas anuales unificadas.

## Data Hub EPN (2026): plataforma de datos públicos

Proyecto "Plataforma web inteligente para la visualización interactiva, análisis predictivo y prescriptivo de datos públicos del Ecuador" (EPN, jul-2026). Repositorio: [github.com/datahubepn/datahub-epn](https://github.com/datahubepn/datahub-epn).

| Componente | Autor | Enfoque |
| --- | --- | --- |
| Frontend UX/UI y visualización | Luis Caiza | React |
| Lakehouse, pipelines ELT y backend de microservicios | Joel Defaz | FastAPI, Airflow, PostgreSQL, Docker, AWS |
| Modelos predictivos contenerizados | Alex Escobar | scikit-learn, JAX, FastAPI, Docker |
| Análisis prescriptivo | Jorge Rojas | Módulos de apoyo a la decisión |

| Patrón | Detalle | Cómo se adopta |
| --- | --- | --- |
| Metodología | Scrum con Sprint 0 + 5 sprints | Mismo esquema en `docs/sprints/A` |
| Capítulo de cada sprint | Introducción · Requerimientos (historias de usuario) · Tratamiento de datos · Implementación · Pruebas y validación · Resultados | Plantilla del informe de sprint |
| Niveles de analítica | Descriptivo → diagnóstico → predictivo → prescriptivo | B cubre los niveles; A los hace consultables en lenguaje natural |
| Declaración de uso de IA | En certificaciones: herramienta, para qué se usó y que el contenido fue revisado por el autor | Incluirla en la memoria de A |
| Stack | FastAPI + PostgreSQL + React, igual que este repositorio | Reduce el riesgo de integración que señaló el director |
