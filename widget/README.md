# widget · Componente A

Dueña: Alicia Pereira. Widget embebible del asistente para el portal del Observatorio. Sigue el stack y las convenciones de [FragUI](https://github.com/RodraHa/FragUI) (ADR 0005).

| Carpeta / archivo | Propósito |
| --- | --- |
| `src/index.ts` | Punto de entrada único del paquete |
| `src/AsistenteWidget.tsx` | Componente raíz (hola mundo) |
| `src/tokens.ts` | Tokens provisionales, a sustituir por los de FragUI |
| `src/*.stories.tsx` | Historias de Storybook |
| `.storybook/` | Storybook con addon-a11y (WCAG 2.1 AA) y Chromatic |
| `tests/` | Vitest + Testing Library + axe-core |

## Alineación con FragUI

| Aspecto | FragUI | Widget |
| --- | --- | --- |
| Lenguaje | React + TypeScript | Igual (mismas versiones mayores) |
| Estilos | En línea, desde tokens | Igual |
| Empaquetado | tsup, ESM + CJS | Igual |
| Documentación | Storybook 10 | Igual |
| Pruebas | Vitest + Testing Library | Igual + axe-core en pruebas unitarias |
| Accesibilidad | addon-a11y, `test: 'error'` | Igual |
| Regresión visual | Chromatic | Igual (requiere `CHROMATIC_PROJECT_TOKEN`) |
| Lint / formato | ESLint 9 + Prettier | Igual configuración |
| Paquetes | npm | npm |

## Uso (PowerShell, desde la raíz)

```powershell
.\scripts\dev.ps1 -Modulo widget    # Storybook en http://localhost:6006
.\scripts\test.ps1 -Modulo widget   # lint + tipos + pruebas
npm --prefix widget run build       # paquete en widget\dist
```
