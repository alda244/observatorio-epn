# 0005. Widget alineado con FragUI

| Campo | Valor |
| --- | --- |
| Estado | Aceptado |
| Fecha | 2026-11-17 |
| Componente | A |

## Contexto

El widget se embebe en el portal del Observatorio. En proyectos anteriores del grupo, cada equipo usó una tecnología distinta y la integración falló. [FragUI](https://github.com/RodraHa/FragUI) es la librería de componentes ya construida en el mismo grupo.

## Decisión

El widget usa el mismo stack y las mismas convenciones que FragUI:

| Aspecto | Elección |
| --- | --- |
| Lenguaje | React + TypeScript |
| Estilos | En línea, desde tokens |
| Empaquetado | tsup, ESM y CJS |
| Documentación | Storybook |
| Pruebas | Vitest, Testing Library, axe-core (WCAG 2.1 AA) |
| Lint | ESLint 9, Prettier |
| Paquetes | npm |

## Consecuencias

| Tipo | Detalle |
| --- | --- |
| Positiva | Se reutilizan los componentes de formulario de FragUI |
| Negativa | Las versiones del widget siguen a las de FragUI |
