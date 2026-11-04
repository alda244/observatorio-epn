# 6. Recolección web ética con Scrapling

[Scrapling](https://github.com/d4vinci/Scrapling) (licencia BSD-3, v0.5) sirve para la capa Bronce, pero su configuración por defecto no cumple las reglas del proyecto: suplanta a Chrome y no obedece robots.txt. Se usa solo con la configuración de abajo.

## Configuración obligatoria

| Opción de Scrapling | Defecto | Valor en B | Regla ([`../investigacion/05`](../investigacion/05-adquisicion-de-datos.md)) |
| --- | --- | --- | --- |
| `robots_txt_obey` | `False` | `True` | Respetar robots.txt |
| `impersonate` | `"chrome"` | `None` | Bot identificado, sin suplantar |
| `stealthy_headers` | `True` | `False` | Bot identificado |
| `User-Agent` | Navegador | `ObservatorioEPN-Bot/0.1 (+repo; proyecto académico EPN)` | Trazabilidad |
| `concurrent_requests_per_domain` | `0` (sin límite) | `1` | No afectar el sitio |
| `download_delay` | `0` | `3` s | No afectar el sitio |
| Proxies, modos stealth, resolución de CAPTCHA | Disponibles | No se usan | Uso ético |
| Páginas por empresa | Sin tope | 4 (portada, nosotros, servicios/productos) | Solo texto institucional |

Comportamiento útil de la librería: si robots.txt responde 4xx, se asume permitido; si responde 5xx o falla, se asume todo bloqueado.

## Qué guarda (`spider_bloque2.py`)

| Salida | Contenido |
| --- | --- |
| `bronce/html/<expediente>/<sha256>.html` | HTML crudo, inmutable |
| `bronce/manifest.jsonl` | Expediente, URL, tipo de página, estado HTTP, fecha de captura, hash, `title`, `meta description`, `og:description`, `h1`, JSON-LD y PDF candidatos |

## Prueba local (03-nov-2026)

Sitio de prueba con robots.txt `Disallow: /privado/`, una página "nosotros", un enlace a `/privado/servicios.html`, un enlace externo y un PDF de informe.

| Verificación | Resultado |
| --- | --- |
| Pide robots.txt antes de rastrear | Sí |
| Respeta `Disallow: /privado/` | Sí, no lo visitó |
| No sigue enlaces a otro dominio | Sí |
| Espera entre peticiones | 3 s |
| Ignora filas sin URL | Sí |
| Extrae `meta description`, `og:description`, JSON-LD y `h1` | Sí |
| Detecta el PDF de informe | Sí |

Pendiente: probar contra webs reales desde la red de la EPN.

## Uso

```powershell
uv add "scrapling[fetchers]"
uv run python spider_bloque2.py universo_bloque2.csv --limite 10
```

## Datos personales

Solo texto institucional. No se guardan nombres de empleados, correos personales ni fotos de personas (Ley Orgánica de Protección de Datos Personales). Los cargos directivos, si aparecen, se excluyen en Plata.
