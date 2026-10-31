"""Lien du dépôt réel : celui où le deck est publié, pas celui que `cours.yml` laisse supposer.

Déduire une URL d'un nom supposé est fragile (un dépôt renommé, un témoin qui ne porte pas le nom
de son bloc). L'ordre, du plus fiable au moins fiable :

1. `GITHUB_REPOSITORY` (« organisation/dépôt »), que GitHub Actions pose sur le runner : il fait autorité ;
2. le `remote` `origin` du dépôt git local, s'il pointe sur github.com (les identifiants éventuels
   de l'adresse ne sont jamais repris) ;
3. en dernier recours, le nom déduit de `cours.yml` (`Cours.url_depot`).
"""

import re
import subprocess
from collections.abc import Mapping
from pathlib import Path

from cielircours.config import Cours

_DEPOT = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
_REMOTE = re.compile(
    r"(?:https?://(?:[^@/]+@)?github\.com/|ssh://git@github\.com/|git@github\.com:)"
    r"(?P<depot>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?\Z"
)


def _depuis_remote(racine: Path) -> str | None:
    try:
        sortie = subprocess.run(
            ["git", "-C", str(racine), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10, check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    m = _REMOTE.fullmatch(sortie)
    return m.group("depot") if m else None


def url_du_depot(racine: Path, cours: Cours, env: Mapping[str, str]) -> str:
    """Le lien `https://github.com/<organisation>/<dépôt>` ; `racine` est le dossier de `cours.yml`."""
    depot = env.get("GITHUB_REPOSITORY", "").strip()
    if not _DEPOT.fullmatch(depot):
        depot = _depuis_remote(racine) or ""
    return f"https://github.com/{depot}" if depot else cours.url_depot
