"""Las reglas de recolección web, en un solo lugar.

Los pasos `urls` y `web` salen a internet y deben hacerlo igual. Antes cada
uno tenía su propia copia de la configuración, que es justo la forma de que un
día dejen de coincidir. Aquí está una vez y los dos heredan de `Etico`.

Las reglas vienen de la guía de crawlers éticos de AWS y del borrador del IETF
sobre bots de recolección (sección 4 de [etl-guide.md](../../etl-guide.md)):

| Regla | Cómo se cumple |
| --- | --- |
| Respetar `robots.txt` | `robots_txt_obey = True` |
| Identificar el bot, con contacto | `USER_AGENT`, con la URL del repositorio |
| No suplantar un navegador | `impersonate=None`, `stealthy_headers=False` |
| Ritmo razonable | Una petición por dominio a la vez, pausa adaptativa |
| No insistir si el sitio bloquea | `max_blocked_retries = 0`, y 429 o 503 cortan el dominio |
"""

from __future__ import annotations

import logging

from scrapling.fetchers import FetcherSession
from scrapling.spiders import Spider

from etl.common import log

USER_AGENT = (
    "ObservatorioEPN-Bot/0.1 (+https://github.com/alda244/observatorio-epn; proyecto academico EPN)"
)
SEGUNDOS_ENTRE_PETICIONES = 5.0
RETRASO_MAXIMO = 60.0
PETICIONES_SIMULTANEAS_POR_DOMINIO = 1
TIEMPO_LIMITE = 20

# Códigos con los que el servidor pide que se baje el ritmo o que se pare.
BLOQUEO = (429, 503)
SIN_ENTRADA = 403


class Etico(Spider):
    """Base de los dos recolectores del proyecto.

    `autothrottle` ajusta la pausa según lo que tarda el servidor en responder
    y la alarga sola si el sitio se queja; `download_delay` es el piso.
    """

    robots_txt_obey = True
    concurrent_requests = 4
    concurrent_requests_per_domain = PETICIONES_SIMULTANEAS_POR_DOMINIO
    download_delay = SEGUNDOS_ENTRE_PETICIONES
    autothrottle_enabled = True
    autothrottle_start_delay = SEGUNDOS_ENTRE_PETICIONES
    autothrottle_max_delay = RETRASO_MAXIMO
    autothrottle_block_backoff = True
    max_blocked_retries = 0
    logging_level = logging.WARNING

    def configure_sessions(self, manager):
        manager.add(
            "etico",
            FetcherSession(
                impersonate=None,  # sin suplantar un navegador
                stealthy_headers=False,
                headers={"User-Agent": USER_AGENT},
                retries=1,
                timeout=TIEMPO_LIMITE,
            ),
        )

    def is_blocked(self, respuesta) -> bool:
        if respuesta.status in BLOQUEO:
            log.warning("%s respondió %s: se deja de pedir", respuesta.url, respuesta.status)
            return True
        return super().is_blocked(respuesta)

    @staticmethod
    def texto_de(respuesta) -> str:
        return respuesta.body.decode(respuesta.encoding or "utf-8", errors="replace")
