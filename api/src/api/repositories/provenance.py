import csv
import re
from datetime import date

from api.config import ranking_manifest
from api.schemas.companies import Provenance


def ranking_sources() -> dict[int, Provenance]:
    sources = {}
    with ranking_manifest().open(encoding="utf-8", newline="") as manifest:
        for entry in csv.DictReader(manifest):
            path = re.fullmatch(r"(\d{4})/ranking_\1\.xlsx", entry["archivo"])
            if path is None:
                continue
            sources[int(path.group(1))] = Provenance(
                source_url=entry["url_origen"], cutoff_date=date.fromisoformat(entry["fecha_corte"])
            )
    return sources
